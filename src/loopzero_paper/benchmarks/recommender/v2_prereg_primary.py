"""V2 pre-registered primary analysis — Early Degradation Indicators under Matched Alert Budgets.

Implements the frozen pre-registration (OSF osf.io/7bvgz, frozen 2026-07-09).
Section numbers in docstrings refer to that document. The formulas in the
pre-registration GOVERN; where legacy code differs, the difference is reported
descriptively and the formulas are implemented as written (§6).

Deliberate two-stage design
---------------------------
`accounting` runs §4 population accounting, §5 folds, §6 indicators, and the §7
PC2 liveness gate. None of it compares indicators to labels.

`primary` runs §7 baselines and the §8 matched-budget comparison — i.e. it
produces ΔTPR. It refuses to run without --ratified, because two spec
interpretation points (see SPEC_INTERPRETATIONS) must be settled BEFORE the
primary statistic is observed. Choosing them afterwards would reintroduce
exactly the post-hoc contamination this pre-registration exists to prevent.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

# --- Frozen constants (§3) ---------------------------------------------------
BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
ENGINE_HASH_PREFIX = "56c1cff2"
PANEL_MD5 = "d486f59c97701c177e16c8eb0bde4a11"
COLLAPSE_STREAK_LEN = 8      # degradation rule: 8 consecutive frontier misses
SLATE_K = 10                 # slate size K
HORIZON_T = 50               # horizon
T_SPLIT = 20                 # landmark step (§4)
WINDOW_LEN = T_SPLIT         # |W| = 20
TOTAL_SLOTS = SLATE_K * WINDOW_LEN   # K·|W| = 200

BUDGETS = (0.01, 0.02, 0.05, 0.10)   # §8
PRIMARY_BUDGET = 0.05
BOOTSTRAP_ITERS = 10_000             # §8
BOOTSTRAP_SEED = 201                 # §8
DELTA_TPR_THRESHOLD = 0.05           # §11 crit 1 — may not be changed (§13)
INCREMENTAL_AUC_THRESHOLD = 0.02     # §11 crit 3 — may not be changed (§13)
MIN_EVAL_EVENTS_FOR_POWER = 200      # §11 power gate

PANEL_PATH = Path(
    "results/v2_prereg_slate_relog/"
    "movielens25m_recursive_frontier_public_v1__telemetry_panel__slate_v1.csv.gz"
)

# --- Spec interpretation points (MUST be ratified before `primary` runs) ------
SPEC_INTERPRETATIONS = {
    "baseline_structural_grid": (
        "§7 says the six v1 families are 'each fully threshold-swept' but does not say "
        "whether each family's STRUCTURAL hyperparameters (ews/ac1 window; cusum k; "
        "page-hinkley delta; matrix-profile window; perm-entropy order/delay) are also "
        "swept. DEFAULT IMPLEMENTED: sweep threshold at every structural setting in the "
        "v1 grid, and let 'best baseline' (§7) = max TPR over all (family, structural "
        "setting) pairs at the matched count. This is the BASELINE-FAVOURING reading: it "
        "makes SIGNAL SURVIVES strictly harder, so it cannot be attacked as hobbling the "
        "comparators. The alternative (pin one setting per family) would be weaker."
    ),
    "best_baseline_in_bootstrap": (
        "§8 asks for a cluster-aware BCa CI on the PAIRED difference ΔTPR = TPR(S) − "
        "TPR(best baseline). It does not say whether 'best baseline' is re-selected "
        "inside each bootstrap replicate. DEFAULT IMPLEMENTED: the identity of the best "
        "baseline is FIXED from the point estimate, and both TPRs are recomputed on each "
        "replicate. Re-selecting per replicate would fold baseline-selection noise into "
        "the paired difference and bias the CI."
    ),
}


# --- §5 Folds ----------------------------------------------------------------
def fold_of(user_id: int) -> str:
    """Deterministic, seedless 50/50 split by user (§5).

    SHA-256 of the ASCII decimal userId; calibration iff final hex digit in {0..7}.
    """
    digest = hashlib.sha256(str(int(user_id)).encode("ascii")).hexdigest()
    return "calibration" if digest[-1] in "01234567" else "evaluation"


# --- §6 Indicators (pure functions of {R_1..R_20}) ---------------------------
def indicators_from_slates(slates: List[List[int]]) -> Tuple[float, float, float]:
    """Return (G, delta, p) per §6. `slates` must be R_1..R_20 in step order."""
    if len(slates) != WINDOW_LEN:
        raise ValueError(f"expected {WINDOW_LEN} slates, got {len(slates)}")

    # G (churn/amplification): c_t = 1 − |R_t ∩ R_{t+1}| / |R_t ∪ R_{t+1}|, t = 1..19
    churns: List[float] = []
    for a, b in zip(slates[:-1], slates[1:]):
        sa, sb = set(a), set(b)
        union = sa | sb
        churns.append(1.0 - (len(sa & sb) / len(union)) if union else 0.0)
    g = float(np.mean(churns))

    # δ (coverage/breadth): |∪ R_t| / 200
    distinct = set()
    for s in slates:
        distinct.update(s)
    delta = len(distinct) / TOTAL_SLOTS

    # p (concentration/reinforcement): occupancy Herfindahl over 200 slots
    occupancy: Dict[int, int] = {}
    for s in slates:
        for item in s:
            occupancy[item] = occupancy.get(item, 0) + 1
    p = float(sum((n / TOTAL_SLOTS) ** 2 for n in occupancy.values()))

    return g, delta, p


# --- §7 Baseline family scores ------------------------------------------------
# Alarm predicate is `score >= threshold` for every family EXCEPT permutation
# entropy, whose v1 alarm is `score <= threshold` (low entropy = collapsed
# dynamics). We negate it so that "higher = more alarming" holds throughout and
# a single sweep direction is valid.
EPS = 1e-12


def _z_norm(x: np.ndarray) -> np.ndarray:
    mean = float(x.mean())
    std = float(x.std())
    if std <= EPS:
        return np.zeros_like(x, dtype=float)
    return (x - mean) / std


def variance_ews_score(series: np.ndarray, window: int) -> float:
    if len(series) < window:
        return float("nan")
    w = np.lib.stride_tricks.sliding_window_view(series, window_shape=window)
    return float(w.var(axis=1).max())


def _lag1_ac1(x: np.ndarray) -> float:
    if len(x) < 2:
        return 0.0
    x0, x1 = x[:-1], x[1:]
    if float(x0.std()) <= 1e-12 or float(x1.std()) <= 1e-12:
        return 0.0
    return float(np.corrcoef(x0, x1)[0, 1])


def ac1_score(series: np.ndarray, window: int) -> float:
    if len(series) < window:
        return float("nan")
    w = np.lib.stride_tricks.sliding_window_view(series, window_shape=window)
    return float(max(_lag1_ac1(np.asarray(win, dtype=float)) for win in w))


def cusum_score(series: np.ndarray, k: float) -> float:
    """Max CUSUM statistic — the v1 alarm is `g >= h`, so g's max is the score."""
    if len(series) < 2:
        return float("nan")
    baseline = float(np.mean(series[: min(5, len(series))]))
    g = 0.0
    peak = 0.0
    for x in series:
        g = max(0.0, g + (float(x) - baseline - k))
        peak = max(peak, g)
    return float(peak)


def page_hinkley_score(series: np.ndarray, delta: float) -> float:
    """Max (PH − PH_min) — the v1 alarm is `(ph - ph_min) >= threshold`."""
    if len(series) < 2:
        return float("nan")
    mean_t = 0.0
    ph = 0.0
    ph_min = 0.0
    peak = 0.0
    for t, x in enumerate(series, start=1):
        x = float(x)
        mean_t = mean_t + (x - mean_t) / t
        ph += x - mean_t - delta
        ph_min = min(ph_min, ph)
        peak = max(peak, ph - ph_min)
    return float(peak)


def matrix_profile_score(series: np.ndarray, window: int) -> float:
    n = len(series)
    if n < window + 1:
        return float("nan")
    windows = np.lib.stride_tricks.sliding_window_view(
        np.asarray(series, dtype=float), window_shape=window
    )
    m = windows.shape[0]
    if m < 2:
        return float("nan")
    subseqs = np.vstack([_z_norm(w) for w in windows])
    profile = np.full(m, np.inf, dtype=float)
    for i in range(m):
        for j in range(i + 1, m):
            dist = float(np.linalg.norm(subseqs[i] - subseqs[j])) / math.sqrt(window)
            if dist < profile[i]:
                profile[i] = dist
            if dist < profile[j]:
                profile[j] = dist
    finite = profile[np.isfinite(profile)]
    return float(finite.max()) if len(finite) else float("nan")


def _ordinal_pattern(window: np.ndarray, order: int) -> Tuple[int, ...]:
    idx = np.argsort(np.asarray(window, dtype=float), kind="mergesort")
    return tuple(int(i) for i in idx[:order])


def permutation_entropy_score(series: np.ndarray, order: int, delay: int) -> float:
    x = np.asarray(series, dtype=float)
    needed = (order - 1) * delay + 1
    if len(x) < needed + 1:
        return float("nan")
    patterns: Dict[Tuple[int, ...], int] = {}
    total = 0
    for start in range(0, len(x) - (order - 1) * delay):
        idx = start + np.arange(order) * delay
        pattern = _ordinal_pattern(x[idx], order=order)
        patterns[pattern] = patterns.get(pattern, 0) + 1
        total += 1
    if total == 0:
        return float("nan")
    probs = np.array([c / total for c in patterns.values()], dtype=float)
    entropy = float(-(probs * np.log(probs + EPS)).sum())
    max_entropy = math.log(math.factorial(order))
    if max_entropy <= EPS:
        return float("nan")
    return float(entropy / max_entropy)


def baseline_structural_grid() -> Dict[str, List[Dict[str, Any]]]:
    """Structural hyperparameters from the v1 grids (thresholds are swept, not fixed)."""
    return {
        "variance_ews": [{"window": w} for w in (5, 9, 13)],
        "ac1": [{"window": w} for w in (5, 9, 13)],
        "cusum": [{"k": k} for k in (0.02, 0.05, 0.10)],
        "page_hinkley": [{"delta": d} for d in (0.005, 0.01, 0.02)],
        "matrix_profile": [{"window": w} for w in (4, 5, 6, 7, 8)],
        "permutation_entropy": [
            {"order": o, "delay": d} for o, d in itertools.product((3, 4), (1, 2))
        ],
    }


def baseline_score(series: np.ndarray, family: str, params: Dict[str, Any]) -> float:
    if family == "variance_ews":
        return variance_ews_score(series, int(params["window"]))
    if family == "ac1":
        return ac1_score(series, int(params["window"]))
    if family == "cusum":
        return cusum_score(series, float(params["k"]))
    if family == "page_hinkley":
        return page_hinkley_score(series, float(params["delta"]))
    if family == "matrix_profile":
        return matrix_profile_score(series, int(params["window"]))
    if family == "permutation_entropy":
        s = permutation_entropy_score(series, int(params["order"]), int(params["delay"]))
        # v1 alarm is score <= threshold; negate so higher = more alarming.
        return -s if not math.isnan(s) else float("nan")
    raise ValueError(f"unknown family: {family!r}")


# --- §8 Matched control-alarm operating point --------------------------------
def tpr_at_matched_count(
    scores: np.ndarray,
    labels: np.ndarray,      # 1 = event, 0 = control
    user_ids: np.ndarray,
    control_alarm_count: int,
) -> float:
    """TPR at the operating point that alarms exactly `control_alarm_count` controls.

    §8: full threshold sweep; ties in a detector score broken by ASCENDING userId.
    We induce a total order on evaluation-fold L by (-score, user_id) and cut
    immediately after the k-th control. Everything above the cut alarms.
    NaN scores never alarm (sorted to the bottom).
    """
    finite = np.isfinite(scores)
    order_key = np.where(finite, -scores, np.inf)
    order = np.lexsort((user_ids, order_key))   # primary: order_key asc; tie: userId asc

    ctrl_seen = 0
    events_above = 0
    for idx in order:
        if ctrl_seen >= control_alarm_count:
            break
        if labels[idx] == 1:
            events_above += 1
        else:
            ctrl_seen += 1

    n_events = int((labels == 1).sum())
    return events_above / n_events if n_events else float("nan")


# --- Loading -----------------------------------------------------------------
@dataclass
class Cohort:
    frame: pd.DataFrame          # one row per user in L
    excluded_early: int          # collapse_step <= 20
    n_input_units: int


def load_landmark_cohort(repo_root: Path) -> Cohort:
    """§4: build landmark population L and its per-user indicators + baseline series."""
    panel_path = repo_root / PANEL_PATH
    df = pd.read_csv(
        panel_path,
        usecols=[
            "user_id", "label", "step", "collapse_step",
            "hit_this_step", "consecutive_misses_after_step",
            "slate_json", "engine_hash",
        ],
    )

    engines = set(str(e)[:8] for e in df["engine_hash"].dropna().unique())
    if engines != {ENGINE_HASH_PREFIX}:
        raise ValueError(f"engine hash mismatch: {engines}")

    n_input_units = df["user_id"].nunique()

    # Landmark population L: no degradation declared at any step <= 20 (§4).
    cs = df.groupby("user_id")["collapse_step"].first()
    early = cs[(cs.notna()) & (cs <= T_SPLIT)].index
    excluded_early = len(early)
    in_L = cs.index.difference(early)

    df = df[df["user_id"].isin(in_L) & (df["step"] >= 1) & (df["step"] <= T_SPLIT)]
    df = df.sort_values(["user_id", "step"], kind="mergesort")

    rows = []
    for uid, g in df.groupby("user_id", sort=True):
        if len(g) != WINDOW_LEN:
            # §4: every unit in L has a complete 20-step window, by the degradation
            # rule. A short window means the panel disagrees with the spec.
            raise ValueError(f"user {uid}: expected {WINDOW_LEN} steps, got {len(g)}")

        slates = [json.loads(s) for s in g["slate_json"]]
        g_ind, delta, p = indicators_from_slates(slates)

        collapse_step = g["collapse_step"].iloc[0]
        is_event = bool(pd.notna(collapse_step) and T_SPLIT < collapse_step <= HORIZON_T)

        # §7 baseline input: the step-<=20 miss_run_fraction series.
        series = np.minimum(
            1.0,
            g["consecutive_misses_after_step"].to_numpy(dtype=float) / COLLAPSE_STREAK_LEN,
        )
        # PC1: early miss rate = (# frontier-miss steps in 1..20) / 20.
        pc1 = float((1 - g["hit_this_step"].to_numpy(dtype=float)).sum() / WINDOW_LEN)

        rows.append(
            {
                "user_id": int(uid),
                "fold": fold_of(int(uid)),
                "label": 1 if is_event else 0,
                "G": g_ind,
                "delta": delta,
                "p": p,
                "pc1": pc1,
                "series": series,
            }
        )

    return Cohort(pd.DataFrame(rows), excluded_early, n_input_units)


# --- Stage: accounting (§4, §5, §6, PC2) -------------------------------------
def run_accounting(repo_root: Path, out_dir: Path) -> Dict[str, Any]:
    cohort = load_landmark_cohort(repo_root)
    f = cohort.frame

    def counts(sub: pd.DataFrame) -> Dict[str, int]:
        return {
            "n": int(len(sub)),
            "events": int((sub["label"] == 1).sum()),
            "controls": int((sub["label"] == 0).sum()),
        }

    delta_vals = f["delta"].to_numpy(dtype=float)
    q75, q25 = np.percentile(delta_vals, [75, 25])
    pc2_distinct = int(len(np.unique(delta_vals)))
    pc2_iqr = float(q75 - q25)
    pc2_pass = bool(pc2_distinct >= 20 and pc2_iqr > 0)

    cal_ctrl = f[(f["fold"] == "calibration") & (f["label"] == 0)]
    z_params = {
        ind: {"mean": float(cal_ctrl[ind].mean()), "sd": float(cal_ctrl[ind].std(ddof=0))}
        for ind in ("G", "p", "delta")
    }

    # §6 pre-registered descriptive: indicator correlation matrix on calibration controls.
    corr = cal_ctrl[["G", "p", "delta"]].corr().round(4).to_dict()

    report = {
        "spec": "OSF osf.io/7bvgz (frozen 2026-07-09)",
        "panel_md5_expected": PANEL_MD5,
        "population_accounting": {
            "input_units_in_panel": cohort.n_input_units,
            "excluded_early_degraders_collapse_step_le_20": cohort.excluded_early,
            "landmark_population_L": counts(f),
            "by_fold": {
                "calibration": counts(f[f["fold"] == "calibration"]),
                "evaluation": counts(f[f["fold"] == "evaluation"]),
            },
        },
        "power_gate_§11": {
            "eval_events": int(((f["fold"] == "evaluation") & (f["label"] == 1)).sum()),
            "min_required": MIN_EVAL_EVENTS_FOR_POWER,
            "pass": bool(
                ((f["fold"] == "evaluation") & (f["label"] == 1)).sum()
                >= MIN_EVAL_EVENTS_FOR_POWER
            ),
        },
        "pc2_liveness_gate_§7": {
            "delta_distinct_values": pc2_distinct,
            "delta_iqr": pc2_iqr,
            "pass": pc2_pass,
        },
        "z_params_calibration_fold_controls_§6": z_params,
        "indicator_correlation_calibration_controls_§6": corr,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "v2_population_accounting.json").write_text(json.dumps(report, indent=2))
    f.drop(columns=["series"]).to_csv(out_dir / "v2_landmark_indicators.csv.gz", index=False)
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["accounting", "primary"])
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out-dir", type=Path, default=Path("results/v2_prereg_primary"))
    ap.add_argument(
        "--ratified",
        action="store_true",
        help="Confirm SPEC_INTERPRETATIONS are settled. Required for `primary`.",
    )
    args = ap.parse_args()

    if args.stage == "accounting":
        report = run_accounting(args.repo_root, args.out_dir)
        print(json.dumps(report, indent=2))
        return

    if not args.ratified:
        raise SystemExit(
            "REFUSING to run the primary comparison.\n\n"
            "Two spec-interpretation points must be settled BEFORE ΔTPR is observed;\n"
            "settling them afterwards is post-hoc contamination.\n\n"
            + "\n\n".join(f"[{k}]\n{v}" for k, v in SPEC_INTERPRETATIONS.items())
            + "\n\nRe-run with --ratified once these are confirmed."
        )
    raise SystemExit("primary stage: implement after ratification (see brief).")


if __name__ == "__main__":
    main()
