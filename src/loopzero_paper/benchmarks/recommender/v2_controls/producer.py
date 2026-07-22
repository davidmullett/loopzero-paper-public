"""Phase-3 real-engine SUMMARY PRODUCER — assembles RealArm / ControlArm objects
that feed the already-tested decision.verdict. BUILD + debug on synthetic/random
panels ONLY; running it on the real or real-control slate panels is the blind block
(separate step, decision.RATIFIED gate).

I-12 baseline handling: each family's v1 STRUCTURAL grid is swept (variance_ews/ac1
window {5,9,13}; cusum k {.02,.05,.10}; page_hinkley delta {.005,.01,.02};
matrix_profile window {4..8}; perm_entropy order{3,4}×delay{1,2}); the alarm
threshold is swept continuously per §8. At a matched control-alarm count a family's
TPR = max over its structural grid; best baseline = max over {six families ∪ PC1};
re-maxed WITHIN each bootstrap replicate (I-6).
"""
from __future__ import annotations
import json, gzip, csv
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np

from . import config as C
from . import decision as D
from . import indicators as I
from . import baselines as B
from . import sweep as SW
from . import covariate_model as CM
from .population import fold
from .bootstrap import bca_ci

csv.field_size_limit(1 << 24)

# I-12 structural grids + the scorer for each family
STRUCTURAL_GRID = {
    "variance_ews":        [{"window": w} for w in (5, 9, 13)],
    "ac1":                 [{"window": w} for w in (5, 9, 13)],
    "cusum":               [{"k": k} for k in (0.02, 0.05, 0.10)],
    "page_hinkley":        [{"delta": d} for d in (0.005, 0.01, 0.02)],
    "matrix_profile":      [{"window": w} for w in (4, 5, 6, 7, 8)],
    "permutation_entropy": [{"order": o, "delay": dl} for o, dl in [(3, 1), (3, 2), (4, 1), (4, 2)]],
}
STREAK = 8


@dataclass
class ArmUnits:
    """Per-unit label-side + indicator arrays for one arm's landmark population L2."""
    user_id: np.ndarray
    fold: np.ndarray           # 'cal'/'eval'
    is_event: np.ndarray       # bool
    clean_control: np.ndarray  # bool
    G: np.ndarray
    p: np.ndarray
    delta: np.ndarray
    mrf: np.ndarray            # (n, 20) miss_run_fraction series
    hit: np.ndarray            # (n, 20)


# ---------- panel -> per-unit arrays (touches slate panel; debugged on synthetic panels) ----------
FRONTIER_FLOOR = 10   # remaining_frontier_floor (frozen contract); clean control = never below it


def load_arm_units(panel_path) -> ArmUnits:
    per: Dict[int, dict] = {}
    with gzip.open(panel_path, "rt", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            st = int(row["step"])
            u = int(row["user_id"])
            rec = per.get(u)
            if rec is None:
                cs = row["collapse_step"]
                rec = per[u] = {"label": row["label"],
                                "cs": None if cs in ("", "NA") else int(float(cs)),
                                "slate": {}, "mrf": {}, "hit": {}, "starved": False}
            if st <= C.WINDOW:
                rec["slate"][st] = [int(x) for x in json.loads(row["slate_json"])]
                rec["mrf"][st] = min(1.0, int(row["consecutive_misses_after_step"]) / STREAK)
                rec["hit"][st] = int(row["hit_this_step"])
            else:  # steps > 20: label-side frontier accounting for the clean-control flag
                if int(row["frontier_size_after"]) < FRONTIER_FLOOR:
                    rec["starved"] = True
    uids, folds, isev, clean, Gs, ps, ds, mrfs, hits = [], [], [], [], [], [], [], [], []
    steps = list(range(1, C.WINDOW + 1))
    for u, rec in per.items():
        cs, lab = rec["cs"], rec["label"]
        # D-7 fix (registered L2, wka72 §2): control admitted iff CLEAN (never starved). rec["starved"]
        # is set on frontier<floor for steps>20; by frontier monotonicity that also captures any
        # starvation at steps <=20 (a <=20 starver is <floor at all later steps, hence at >20 too, or
        # else its episode ends <20 and it fails the complete-window check below). So `not rec["starved"]`
        # == CLEAN == "no starvation at any step <=20 AND none in (20,50]". Verified against the anchored
        # census (6b6ac55) by the population-conformance assertion in the block (F).
        in_L2 = (lab == "control" and not rec["starved"]) or (lab == "event" and cs is not None and C.T_SPLIT < cs <= 50)
        if not in_L2 or any(s not in rec["slate"] for s in steps):
            continue
        slates = [rec["slate"][s] for s in steps]
        uids.append(u); folds.append(fold(u)); isev.append(lab == "event")
        clean.append(lab == "control" and not rec["starved"])   # every admitted control is now CLEAN
        Gs.append(I.churn_G(slates)); ps.append(I.occupancy_p(slates)); ds.append(I.coverage_delta(slates))
        mrfs.append([rec["mrf"][s] for s in steps]); hits.append([rec["hit"][s] for s in steps])
    return ArmUnits(np.array(uids), np.array(folds), np.array(isev, bool), np.array(clean, bool),
                    np.array(Gs), np.array(ps), np.array(ds), np.array(mrfs, float), np.array(hits, int))


# ---------- S composite (z on cal-fold CLEAN controls) + baseline score matrix (I-12) ----------
def s_scores(a: ArmUnits) -> np.ndarray:
    calc = (a.fold == "cal") & a.clean_control      # D-7: z-parameters on cal-fold CLEAN controls (wka72 §4)
    zp = I.ZParams(a.G[calc], a.p[calc], a.delta[calc])
    return I.composite_S(zp.z("G", a.G), zp.z("p", a.p), zp.z("delta", a.delta))


def pc1_scores(a: ArmUnits) -> np.ndarray:
    return (a.hit == 0).sum(axis=1) / C.WINDOW    # early miss rate (1..20)


def baseline_score_matrix(a: ArmUnits) -> Tuple[np.ndarray, List[str]]:
    """Per-unit score for every (family, structural config) in the I-12 grid, plus PC1.
    Returns (matrix [n, m], column names). Threshold is swept later (continuous, §8)."""
    cols, names = [], []
    for fam, grid in STRUCTURAL_GRID.items():
        scorer = B.FAMILY_SCORERS[fam]
        for cfg in grid:
            sc = np.array([scorer(a.mrf[i], **cfg) for i in range(len(a.mrf))], float)
            sc = np.nan_to_num(sc, nan=-np.inf)  # NaN (too-short series) never alarms
            cols.append(sc); names.append(f"{fam}{cfg}")
    cols.append(pc1_scores(a)); names.append("PC1")
    return np.vstack(cols).T, names


# ---------- ΔTPR at a matched budget with cluster BCa + I-6 re-max ----------
def _matched_count(is_event, budget):
    # D-7: matched control-alarm count = round(b · n_eval_CLEAN_controls). Post-population-fix the arm
    # contains only CLEAN controls, so (~is_event) IS the eval CLEAN-control mask (766 on the real arm,
    # wka72 §6). No non-clean control can enter this count.
    return SW.matched_count(budget, int((~is_event).sum()))


def delta_tpr_ci(S: np.ndarray, Bmat: np.ndarray, is_event: np.ndarray, user_id: np.ndarray,
                 budget: float, *, seed=C.BOOTSTRAP_SEED, n_boot=C.BOOTSTRAP_ITERS) -> Tuple[float, float, float]:
    def stat(idx):
        ie = is_event[idx]; uid = user_id[idx]
        cnt = _matched_count(ie, budget)
        tpr_s = SW.matched_tpr(S[idx], ie, uid, cnt)
        best = -np.inf
        for j in range(Bmat.shape[1]):          # I-6: re-max best baseline WITHIN the replicate
            best = max(best, SW.matched_tpr(Bmat[idx, j], ie, uid, cnt))
        return tpr_s - best
    return bca_ci(len(S), stat, n_boot=n_boot, seed=seed)


# ---------- gates ----------
def pc1_gate_ci(a: ArmUnits, *, seed=C.BOOTSTRAP_SEED, n_boot=C.BOOTSTRAP_ITERS) -> Tuple[float, float, float]:
    """I-7: (TPR_PC1 at b=0.05) - 0.05, cluster BCa."""
    ev = a.fold == "eval"
    pc1 = pc1_scores(a)[ev]; ie = a.is_event[ev]; uid = a.user_id[ev]
    def stat(idx):
        e = ie[idx]; cnt = _matched_count(e, C.PRIMARY_BUDGET)
        return SW.matched_tpr(pc1[idx], e, uid[idx], cnt) - C.PRIMARY_BUDGET
    return bca_ci(int(ev.sum()), stat, n_boot=n_boot, seed=seed)


def pc2_pass(a: ArmUnits) -> bool:
    d = a.delta
    q75, q25 = np.percentile(d, [75, 25])
    return int(np.unique(d).size) >= 20 and (q75 - q25) > 0


def measurability(a: ArmUnits) -> Tuple[int, int, int, float]:
    ev = a.fold == "eval"
    n_clean = int((ev & a.clean_control).sum())
    n_events = int((ev & a.is_event).sum())
    S = s_scores(a)[ev]
    q75, q25 = np.percentile(S, [75, 25])
    return n_clean, n_events, int(np.unique(S).size), float(q75 - q25)


# ---------- covariate incremental AUC (§9) ----------
def covariate_summary(a: ArmUnits, log_activity: np.ndarray, pop_affinity: np.ndarray,
                      *, seed=C.BOOTSTRAP_SEED, n_boot=C.BOOTSTRAP_ITERS):
    """On eval-fold L2: β signs of z(G),z(p),z(δ) each BCa CI; incremental AUC BCa CI."""
    ev = a.fold == "eval"
    calc = (a.fold == "cal") & (~a.is_event)
    zp = I.ZParams(a.G[calc], a.p[calc], a.delta[calc])
    zG, zP, zD = zp.z("G", a.G[ev]), zp.z("p", a.p[ev]), zp.z("delta", a.delta[ev])
    cov = np.column_stack([log_activity[ev], pop_affinity[ev]])
    ind = np.column_stack([zG, zP, zD])
    y = a.is_event[ev].astype(int)

    def coef_ci(col):
        def stat(idx):
            X = np.column_stack([np.ones(len(idx)), cov[idx], ind[idx]])
            b = CM.logistic_fit(X, y[idx])
            return b[3 + col]          # 0-intercept,1-2 cov, 3-5 indicators
        return bca_ci(len(y), stat, n_boot=n_boot, seed=seed)

    def incr_stat(idx):
        return CM.incremental_auc(cov[idx], ind[idx], y[idx])
    return coef_ci(0), coef_ci(1), coef_ci(2), bca_ci(len(y), incr_stat, n_boot=n_boot, seed=seed)


# ---------- arm summaries ----------
def real_arm(a: ArmUnits, log_activity: np.ndarray, pop_affinity: np.ndarray, **kw) -> D.RealArm:
    S = s_scores(a); Bmat, _ = baseline_score_matrix(a)
    ev = a.fold == "eval"
    delta_by_budget = {b: delta_tpr_ci(S[ev], Bmat[ev], a.is_event[ev], a.user_id[ev], b, **kw) for b in D.BUDGETS}
    bG, bP, bD, incr = covariate_summary(a, log_activity, pop_affinity, **kw)
    return D.RealArm(eval_events=int((ev & a.is_event).sum()), pc1_minus_b=pc1_gate_ci(a, **kw),
                     pc2_pass=pc2_pass(a), delta_by_budget=delta_by_budget,
                     cov_bG=bG, cov_bP=bP, cov_bD=bD, cov_incr_auc=incr)


def control_arm(name: str, a: ArmUnits, **kw) -> D.ControlArm:
    S = s_scores(a); Bmat, _ = baseline_score_matrix(a)
    ev = a.fold == "eval"
    d05 = delta_tpr_ci(S[ev], Bmat[ev], a.is_event[ev], a.user_id[ev], C.PRIMARY_BUDGET, **kw)
    ncc, nev, sd, siqr = measurability(a)
    return D.ControlArm(name=name, n_clean_controls=ncc, n_events=nev, s_distinct=sd, s_iqr=siqr, delta_b05=d05)
