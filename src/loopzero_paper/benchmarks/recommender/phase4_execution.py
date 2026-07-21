"""Phase-4 REQUIRED items (D-33), post-verdict, DIES route. Descriptive/robustness analyses on
the pre-registered set only (Route B / D-35 — no new composite, no threshold search, no feature
engineering against the purified label). Authored post-verdict (D-18/19/20 precedent class).

Items:
 1. Bounding diagnostic   — 4 indicators × {d_full, d_purified, d_starved_contrast, mechanical Δd
                            (cluster-bootstrap seed 42 / 10k CI), coupling type}.
 2. t_split {15,25}       — full primary form (ΔTPR by budget + criteria + PC1/PC2 gates); D-37 power rule.
 3. Frontier-headroom     — ΔTPR@0.05 for events with remaining frontier [10,15] vs >15.
 4. Correlation matrix    — Pearson r among the indicators on eval-L.
 5. I-5b absolute         — TPR_S − b (+CI) on each of the six severed control arms.
 6. Starvation-concurrence— label-side: events whose frontier crosses the floor in-window before collapse.
 + Not-run ledger         — three MOOT items with verbatim reasons.

RATIFIED set IN-PROCESS only (anchored source stays False; C*** unchanged).
"""
from __future__ import annotations
import gzip, csv, json, sys, os
from pathlib import Path
import numpy as np

sys.path.insert(0, "/Users/david/Dev/loopzero-paper-public/src")
from loopzero_paper.benchmarks.recommender.v2_controls import config as C
from loopzero_paper.benchmarks.recommender.v2_controls import decision as D
from loopzero_paper.benchmarks.recommender.v2_controls import producer as PR
from loopzero_paper.benchmarks.recommender.v2_controls import covariates as COV
from loopzero_paper.benchmarks.recommender.v2_controls import sweep as SW
from loopzero_paper.benchmarks.recommender.v2_controls import indicators as I
from loopzero_paper.benchmarks.recommender.v2_controls.population import fold
from loopzero_paper.benchmarks.recommender.v2_controls.bootstrap import bca_ci

csv.field_size_limit(1 << 24)
D.RATIFIED = True
OUT = C.OUT_DIR / "s2_exec2_phase4.json"
FLOOR = PR.FRONTIER_FLOOR   # 10
NB = int(os.environ.get("PHASE4_NBOOT", "10000"))   # 10k for the real run; small for smoke tests


def cohens_d(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return float("nan")
    sp = np.sqrt(((nx - 1) * x.var(ddof=1) + (ny - 1) * y.var(ddof=1)) / (nx + ny - 2))
    return float((x.mean() - y.mean()) / sp) if sp > 0 else float("nan")


# ---- diagnostic loader: admit ALL controls + events, keep starved flag, mrf mean, landmark frontier ----
def load_diag(panel_path, window=20, t_split=20):
    per = {}
    with gzip.open(panel_path, "rt", newline="") as f:
        for row in csv.DictReader(f):
            st = int(row["step"]); u = int(row["user_id"])
            rec = per.get(u)
            if rec is None:
                cs = row["collapse_step"]
                rec = per[u] = {"label": row["label"], "cs": None if cs in ("", "NA") else int(float(cs)),
                                "slate": {}, "mrf": {}, "hit": {}, "starved": False,
                                "front_lm": None, "crossed_before_cs": False, "starved_in_window": False}
            if st <= window:
                rec["slate"][st] = [int(x) for x in json.loads(row["slate_json"])]
                rec["mrf"][st] = min(1.0, int(row["consecutive_misses_after_step"]) / PR.STREAK)
                rec["hit"][st] = int(row["hit_this_step"])
            fs = row.get("frontier_size_after")
            if fs not in (None, "", "NA"):
                fsi = int(fs)
                if st == window:
                    rec["front_lm"] = fsi
                if st <= window and fsi < FLOOR:
                    rec["starved_in_window"] = True   # frontier below floor WITHIN the observation window
                if st > window and fsi < FLOOR:
                    rec["starved"] = True
                if rec["cs"] is not None and st <= rec["cs"] and fsi < FLOOR:
                    rec["crossed_before_cs"] = True
    steps = list(range(1, window + 1))
    rows = []
    for u, rec in per.items():
        cs, lab = rec["cs"], rec["label"]
        is_ev = (lab == "event" and cs is not None and t_split < cs <= 50)
        is_ct = (lab == "control")
        if not (is_ev or is_ct) or any(s not in rec["slate"] for s in steps):
            continue
        slates = [rec["slate"][s] for s in steps]
        mrf = np.array([rec["mrf"][s] for s in steps], float)
        rows.append({"u": u, "fold": fold(u), "event": is_ev,
                     "clean": (is_ct and not rec["starved"]), "starved": (is_ct and rec["starved"]),
                     "G": I.churn_G(slates), "p": I.occupancy_p(slates), "delta": I.coverage_delta(slates),
                     "mrf": float(mrf.mean()), "front_lm": rec["front_lm"], "crossed": rec["crossed_before_cs"],
                     "starved_in_window": rec["starved_in_window"]})
    return rows


IND = ["G", "p", "delta", "mrf"]
COUPLING = {"G": "slate-structure (engine-frontier-coupled)", "p": "slate-structure (engine-frontier-coupled)",
            "delta": "slate-structure (engine-frontier-coupled)", "mrf": "outcome-stream (behavioral/miss-coupled)"}


def item1_bounding(rows):
    ev = [r for r in rows if r["fold"] == "eval" and r["event"]]
    cl = [r for r in rows if r["fold"] == "eval" and r["clean"]]
    stv = [r for r in rows if r["fold"] == "eval" and r["starved"]]
    print(f"  [1] eval: events={len(ev)} clean={len(cl)} starved={len(stv)}", flush=True)
    pool = ev + cl + stv
    lab = np.array([0] * len(ev) + [1] * len(cl) + [2] * len(stv))  # 0 event,1 clean,2 starved
    table = {}
    for ind in IND:
        e = np.array([r[ind] for r in ev]); c = np.array([r[ind] for r in cl]); s = np.array([r[ind] for r in stv])
        allc = np.concatenate([c, s])
        d_full = cohens_d(e, allc)
        d_pur = cohens_d(e, c)
        d_stv = cohens_d(s, c)   # starved-vs-clean: the mechanical axis itself
        vals = np.array([r[ind] for r in pool])

        def stat(idx):
            li = lab[idx]; vi = vals[idx]
            ee = vi[li == 0]; cc = vi[li == 1]; ss = vi[li == 2]
            return cohens_d(ee, np.concatenate([cc, ss])) - cohens_d(ee, cc)
        dd, lo, hi = bca_ci(len(pool), stat, n_boot=NB, seed=42)
        table[ind] = {"d_full": round(d_full, 4), "d_purified": round(d_pur, 4),
                      "d_starved_contrast": round(d_stv, 4),
                      "mechanical_delta_d": [round(dd, 4), round(lo, 4), round(hi, 4)],
                      "coupling_type": COUPLING[ind]}
        print(f"  [1] {ind}: d_full={d_full:.3f} d_pur={d_pur:.3f} d_stv={d_stv:.3f} Δd={dd:.3f}[{lo:.3f},{hi:.3f}]", flush=True)
    return table


def item2_tsplit(cov, payload):
    res = {}
    for t in (15, 20, 25):   # t=20 is the KNOWN-ANSWER validation arm (must reproduce the sealed payload)
        C.WINDOW = t; C.T_SPLIT = t   # monkeypatch: run the registered primary at this landmark
        a = PR.load_arm_units(C.PANEL)
        ev_events = int(((a.fold == "eval") & a.is_event).sum())
        executable = ev_events >= C.POWER_MIN_EVAL_EVENTS
        covered = np.array([int(u) in cov for u in a.user_id])
        frac = float(covered.mean())
        # covariate-free core: ΔTPR by budget + PC1/PC2
        S = PR.s_scores(a); Bmat, _ = PR.baseline_score_matrix(a); ev = a.fold == "eval"
        dbb = {b: PR.delta_tpr_ci(S[ev], Bmat[ev], a.is_event[ev], a.user_id[ev], b) for b in D.BUDGETS}
        pc1 = PR.pc1_gate_ci(a); pc2 = PR.pc2_pass(a)
        c1 = D.bar_met(dbb[C.PRIMARY_BUDGET]); c2 = sum(1 for b in D.BUDGETS if dbb[b][0] > 0) >= 3
        if t == 20:   # KAT: identical code path must reproduce the sealed payload's registered analysis
            for b in D.BUDGETS:
                got = dbb[b]; exp = payload["real_delta_by_budget"][str(b)]
                assert abs(got[0] - exp[0]) < 1e-6, f"KAT HALT: t=20 ΔTPR@{b} point {got[0]} != payload {exp[0]}"
                if NB >= 10000:
                    assert all(abs(g - e) < 1e-9 for g, e in zip(got, exp)), \
                        f"KAT HALT: t=20 ΔTPR@{b} CI {got} != payload {exp} (NB={NB})"
            print(f"  [2] t=20 KAT: ΔTPR points match sealed payload (CI too @NB>=10k, NB={NB}) -> PASS", flush=True)
            res["_kat_t20"] = {"delta_by_budget": {str(b): [round(x, 6) for x in dbb[b]] for b in D.BUDGETS},
                               "matches_sealed_payload": True}
        entry = {"eval_events": ev_events, "executable": executable, "covariate_cache_coverage": round(frac, 4),
                 "delta_by_budget": {str(b): [round(x, 6) for x in dbb[b]] for b in D.BUDGETS},
                 "pc1_gate_TPR_minus_b": [round(x, 6) for x in pc1], "pc2_pass": bool(pc2),
                 "c1": bool(c1), "c2": bool(c2)}
        # c3 only if fully covered (t=25 ⊆ t=20 cache); else report subset coverage
        if frac >= 0.999:
            la = np.array([cov[int(u)][0] for u in a.user_id], float)
            pa = np.array([cov[int(u)][1] for u in a.user_id], float)
            bG, bP, bD, incr = PR.covariate_summary(a, la, pa)
            entry["c3"] = bool(D.covariate_pass(bG, bP, bD, incr))
            entry["covariate"] = {"bG": [round(x, 4) for x in bG], "bP": [round(x, 4) for x in bP],
                                  "bD": [round(x, 4) for x in bD], "incr_auc": [round(x, 4) for x in incr]}
        else:
            entry["c3"] = "NOT COMPUTED (covariate cache is t_split=20-scoped; %d%% of this landmark's units covered)" % round(frac * 100)
        res[str(t)] = entry
        print(f"  [2] t={t}: events={ev_events} exec={executable} c1={c1} c2={c2} ΔTPR@0.05={dbb[0.05][0]:.4f} cov={frac:.2f}", flush=True)
    C.WINDOW = 20; C.T_SPLIT = 20   # restore
    return res


def item3_frontier(arm, front_lm):
    """ΔTPR@0.05 (S − best baseline, matched, cluster BCa) for eval events split by remaining
    frontier at landmark: [floor,15] vs >15, each vs ALL eval clean controls. Uses the registered
    baseline matrix and z-params from the FULL arm (cal-fold clean), selecting subgroups by mask."""
    S = PR.s_scores(arm); Bmat, _ = PR.baseline_score_matrix(arm)
    ev = arm.fold == "eval"
    is_ev = arm.is_event & ev
    is_cl = arm.clean_control & ev
    flm = np.array([front_lm.get(int(u), -1) for u in arm.user_id])
    out = {}
    for name, lo, hi in [("headroom_10_15", FLOOR, 15), ("headroom_gt15", 16, 10**9)]:
        subm = is_ev & (flm >= lo) & (flm <= hi)
        n_sub = int(subm.sum())
        mask = subm | is_cl
        n_ctrl = int(is_cl.sum())
        if n_sub < 100:
            out[name] = {"n_events": n_sub, "note": "n<100; ΔTPR not reported"}
            print(f"  [3] {name}: n_events={n_sub} (<100, skipped)", flush=True)
            continue
        d = PR.delta_tpr_ci(S[mask], Bmat[mask], arm.is_event[mask], arm.user_id[mask], C.PRIMARY_BUDGET)
        out[name] = {"n_events": n_sub, "n_clean_controls": n_ctrl,
                     "k": SW.matched_count(C.PRIMARY_BUDGET, n_ctrl),
                     "delta_tpr_b05": [round(float(x), 6) for x in d]}
        print(f"  [3] {name}: n_events={n_sub} ΔTPR@0.05={d[0]:.4f}[{d[1]:.4f},{d[2]:.4f}]", flush=True)
    return out


def item4_corr(rows):
    L = [r for r in rows if r["fold"] == "eval" and (r["event"] or r["clean"] or r["starved"])]
    M = np.column_stack([np.array([r[k] for r in L]) for k in IND])
    R = np.corrcoef(M, rowvar=False)
    print("  [4] correlation matrix computed", flush=True)
    return {"indicators": IND, "pearson_r": [[round(float(R[i, j]), 4) for j in range(len(IND))] for i in range(len(IND))],
            "n": len(L)}


def item5_i5b():
    arms = {"popularity_only": C.OUT_DIR / "arm_popularity_only__slate_panel.csv.gz"}
    for i in range(5):
        arms[f"shuffled_ts_{102+i}"] = C.OUT_DIR / f"arm_shuffled_ts_{102+i}__slate_panel.csv.gz"
    out = {}
    for name, path in arms.items():
        a = PR.load_arm_units(path); ev = a.fold == "eval"
        S = PR.s_scores(a)[ev]; ie = a.is_event[ev]; uid = a.user_id[ev]
        def stat(idx):
            e = ie[idx]; cnt = PR._matched_count(e, C.PRIMARY_BUDGET)
            return SW.matched_tpr(S[idx], e, uid[idx], cnt) - C.PRIMARY_BUDGET
        pt, lo, hi = bca_ci(int(ev.sum()), stat, n_boot=NB, seed=C.BOOTSTRAP_SEED)
        beats = pt > 0 and lo > 0
        out[name] = {"TPR_S_minus_b": [round(pt, 6), round(lo, 6), round(hi, 6)], "beats_chance": bool(beats)}
        print(f"  [5] {name}: TPR_S-b={pt:.4f}[{lo:.4f},{hi:.4f}] beats_chance={beats}", flush=True)
    return out


def item6_starv_concurrence(rows):
    ev = [r for r in rows if r["event"]]
    ev_eval = [r for r in ev if r["fold"] == "eval"]
    conc = sum(1 for r in ev if r["crossed"])
    conc_eval = sum(1 for r in ev_eval if r["crossed"])
    # H3 numbers: units whose remaining frontier fell below the collapse floor WITHIN the window (1..20)
    winstarv_all = sum(1 for r in rows if r["starved_in_window"])
    winstarv_ev = sum(1 for r in ev if r["starved_in_window"])
    winstarv_ct = sum(1 for r in rows if r["starved_in_window"] and not r["event"])
    out = {"total_events": len(ev), "events_frontier_crossed_floor_before_collapse": conc,
           "eval_events": len(ev_eval), "eval_events_concurrent": conc_eval,
           "fraction_concurrent": round(conc / len(ev), 6) if ev else None,
           "within_window_starvers_total": winstarv_all,
           "within_window_starvers_events": winstarv_ev,
           "within_window_starvers_controls": winstarv_ct,
           "note": "H3-adjacent: (a) events whose remaining frontier fell below the collapse floor at/before "
                   "collapse — the in-window starvation-concurrence rate; and (b) the count of units that "
                   "starved (frontier<floor) WITHIN the observation window (1..20). By the degradation contract "
                   "(collapse fires only when frontier>=floor), events cannot cross the floor before collapse, "
                   "so H3's within-window-starvation mechanism is vacuous on the event class by construction."}
    print(f"  [6] concurrence {conc}/{len(ev)}; within-window starvers: total={winstarv_all} events={winstarv_ev} controls={winstarv_ct}", flush=True)
    return out


LEDGER = {
    "MF_sequential_engines": "MOOT — existed to test mechanism specificity of a DETECTED signal; none was detected (SIGNAL DIES on c1–c3); not run. Deferred as future characterization (D-33).",
    "random_arm_rerun": "MOOT — the random-arm degeneracy IS the result (D-3); a re-run adds nothing. Not run.",
    "H3_as_frozen": "MOOT — vacuous by population fact: by the degradation contract (collapse fires only when frontier>=floor) no event can cross the floor before collapse, and the CLEAN population excludes starvers by construction; the starvation-concurrence probe (item 6) reports the within-window-starver counts directly. Not run as a separate test.",
}


def main():
    print("[phase4] loading primary diagnostic population (window=20)", flush=True)
    rows = load_diag(C.PANEL, 20, 20)
    cov = COV.load_real_covariates()
    payload = json.loads((C.OUT_DIR / "s2_verdict_payload.json").read_text())["decision_quantities"]
    result = {"source": "post-verdict Phase-4 (D-33); descriptive/robustness on the pre-registered set only (Route B)"}
    front_lm = {r["u"]: r["front_lm"] for r in rows if r["front_lm"] is not None}
    print("[phase4] item 1 — bounding diagnostic", flush=True); result["item1_bounding_diagnostic"] = item1_bounding(rows)
    print("[phase4] item 4 — correlation matrix", flush=True); result["item4_indicator_correlation"] = item4_corr(rows)
    print("[phase4] item 6 — starvation-concurrence", flush=True); result["item6_starvation_concurrence"] = item6_starv_concurrence(rows)
    print("[phase4] loading primary analysis arm (clean, for items 3)", flush=True)
    arm = PR.load_arm_units(C.PANEL)
    print("[phase4] item 3 — frontier-headroom split", flush=True); result["item3_frontier_headroom_split"] = item3_frontier(arm, front_lm)
    print("[phase4] item 5 — I-5b absolute on control arms", flush=True); result["item5_i5b_absolute"] = item5_i5b()
    print("[phase4] item 2 — t_split sensitivity + t=20 KAT (heaviest)", flush=True); result["item2_tsplit_sensitivity"] = item2_tsplit(cov, payload)
    result["not_run_ledger"] = LEDGER
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PHASE4_DONE", flush=True)


if __name__ == "__main__":
    main()
