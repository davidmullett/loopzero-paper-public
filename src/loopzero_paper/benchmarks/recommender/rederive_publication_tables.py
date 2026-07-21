"""Phase-5 §12 publication re-derivation (post-verdict, DIES route).

Re-derives the pre-registered quantities that §12 publishes but that the sealed payload
does NOT carry: the passed PC1 learnability-gate record (TPR + BCa CI over the CLEAN eval
population) and the per-detector operating tables (each registered family's matched TPR at
the four registered budgets, alongside S and PC1). Runs `real_arm` once over the CLEAN
population and VALUE-MATCHES the sealed payload by assertion (delta-by-budget + covariate):
any mismatch is a determinism failure -> HALT. This is NOT new analysis (Route B / D-35):
every quantity is a pre-registered §5/§6/§8 operating point re-derived for publication.

POST-HOC DISCLOSURE (D-18/D-19/D-20 precedent class). This module was AUTHORED AFTER the
verdict was sealed and anchored, and it is being executed post-verdict. Like the D-18/19/20
writers, it is committed as public source with its provenance stated plainly so the record is
self-describing: it does NOT compute any new quantity against the purified label (Route B /
D-35) — every quantity it emits is a pre-registered §5/§6/§7/§8 operating point that §12
publishes (the passed PC1 learnability gate; each registered detector family's matched TPR at
the four registered budgets). It re-derives them by re-running the already-anchored `real_arm`
over the CLEAN population, and it VALUE-MATCHES the sealed payload by assertion (ΔTPR-by-budget
+ covariate, tol 1e-9); a mismatch is a determinism failure and HALTS.

RATIFIED is set IN-PROCESS only (the anchored source stays False; C*** unchanged).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, "/Users/david/Dev/loopzero-paper-public/src")
from loopzero_paper.benchmarks.recommender.v2_controls import decision as D
from loopzero_paper.benchmarks.recommender.v2_controls import config as C
from loopzero_paper.benchmarks.recommender.v2_controls import conformance as CF
from loopzero_paper.benchmarks.recommender.v2_controls import producer as PR
from loopzero_paper.benchmarks.recommender.v2_controls import covariates as COV
from loopzero_paper.benchmarks.recommender.v2_controls import sweep as SW
from loopzero_paper.benchmarks.recommender.v2_controls import baselines as B

D.RATIFIED = True  # in-process only

PAYLOAD = C.OUT_DIR / "s2_verdict_payload.json"
OUT = C.OUT_DIR / "s2_exec2_gate_and_detector_tables.json"
TOL = 1e-9


def _close(a, b):
    return all(abs(float(x) - float(y)) <= TOL for x, y in zip(a, b))


def per_detector_tpr(a: PR.ArmUnits):
    """Point matched-TPR at each registered budget for S, PC1, and each family (max over its
    I-12 structural grid) — the operating table. Deterministic point estimates (no bootstrap)."""
    ev = a.fold == "eval"
    S = PR.s_scores(a)[ev]
    pc1 = PR.pc1_scores(a)[ev]
    ie = a.is_event[ev]
    uid = a.user_id[ev]
    n_ctrl = int((~ie).sum())
    rows = {}
    for b in D.BUDGETS:
        cnt = SW.matched_count(b, n_ctrl)
        col = {"S_composite": SW.matched_tpr(S, ie, uid, cnt),
               "PC1_early_miss": SW.matched_tpr(pc1, ie, uid, cnt)}
        for fam, grid in PR.STRUCTURAL_GRID.items():
            scorer = B.FAMILY_SCORERS[fam]
            best = -np.inf
            for cfg in grid:
                sc = np.array([scorer(a.mrf[i], **cfg) for i in np.where(ev)[0]], float)
                sc = np.nan_to_num(sc, nan=-np.inf)
                best = max(best, SW.matched_tpr(sc, ie, uid, cnt))
            col[fam] = float(best)
        rows[str(b)] = {"k": cnt, "tpr": {kk: round(float(vv), 6) for kk, vv in col.items()}}
    return rows, n_ctrl


def main():
    payload = json.loads(PAYLOAD.read_text())["decision_quantities"]
    print("[rederive] input gate + load real CLEAN population", flush=True)
    CF.input_gate()
    a = PR.load_arm_units(C.PANEL)
    CF.assert_population_conformance(a)
    cov = COV.load_real_covariates()
    la = np.array([cov[int(u)][0] for u in a.user_id], float)
    pa = np.array([cov[int(u)][1] for u in a.user_id], float)

    print("[rederive] real_arm (delta-by-budget + covariate + PC1 gate; 10k BCa)", flush=True)
    real = PR.real_arm(a, la, pa)

    # ---- VALUE-MATCH the sealed payload (determinism proof) ----
    for b in D.BUDGETS:
        got = real.delta_by_budget[b]
        exp = payload["real_delta_by_budget"][str(b)]
        assert _close(got, exp), f"HALT: delta@{b} re-derived {got} != payload {exp}"
    for name, got, exp in [("bG", real.cov_bG, payload["covariate"]["bG"]),
                           ("bP", real.cov_bP, payload["covariate"]["bP"]),
                           ("bD", real.cov_bD, payload["covariate"]["bD"]),
                           ("incr_auc", real.cov_incr_auc, payload["covariate"]["incr_auc"])]:
        assert _close(got, exp), f"HALT: covariate {name} re-derived {got} != payload {exp}"
    print("[rederive] VALUE-MATCH vs sealed payload: PASS (delta-by-budget + covariate identical)", flush=True)

    # PC1 gate record: pc1_minus_b = (TPR - 0.05); recover TPR + CI
    pm = real.pc1_minus_b
    pc1_tpr = [round(pm[0] + C.PRIMARY_BUDGET, 6), round(pm[1] + C.PRIMARY_BUDGET, 6), round(pm[2] + C.PRIMARY_BUDGET, 6)]
    pc1_pass = pm[1] > 0  # CI for (TPR - b) excludes 0 from above

    print("[rederive] per-detector operating tables (point TPR at 4 budgets)", flush=True)
    det, n_ctrl = per_detector_tpr(a)

    out = {
        "source": "post-verdict re-derivation; value-matched to sealed payload 472571471d94…",
        "pc1_learnability_gate": {
            "budget": C.PRIMARY_BUDGET,
            "TPR": pc1_tpr[0], "TPR_BCa95": [pc1_tpr[1], pc1_tpr[2]],
            "TPR_minus_b": [round(pm[0], 6), round(pm[1], 6), round(pm[2], 6)],
            "pass": bool(pc1_pass),
            "note": "clean-population PC1 gate (I-7); passed -> user-process signal is learnable (D-32b)",
        },
        "pc2_liveness_pass": bool(real.pc2_pass),
        "eval_clean_controls": n_ctrl,
        "eval_events": real.eval_events,
        "per_detector_operating_tables": det,
        "value_match": "delta_by_budget + covariate identical to sealed payload (tol 1e-9)",
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print("PC1_GATE_TPR::", pc1_tpr, "pass=", bool(pc1_pass), flush=True)
    print("PER_DETECTOR::", json.dumps(det), flush=True)
    print("REDERIVE_DONE", flush=True)


if __name__ == "__main__":
    main()
