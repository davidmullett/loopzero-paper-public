"""D-44 remedy (logged before this ran; DEVIATIONS v47). Pearson correlations among G, p, delta
on the 694 calibration-fold CLEAN controls — the standardization population where the z-parameters
are defined and z has unit variance by construction. Control-only, no label, no indicator x outcome
pairing; cannot bear on the verdict. Corrects the anchored item-4 matrix (D-7-class population
deviation: it was computed on the full eval arm n=12,606). Correlation is scale/shift invariant, so
r on raw G/p/delta equals r on z(G)/z(p)/z(delta).

Restores the §5.1 decomposition on the correct population:
  D = z(G) - z(delta);  Var(D) = 2(1 - r(G,delta));  Cov(D, z(p)) = r(G,p) - r(p,delta);
  Var(S) = Var(D) + 1 + 2 Cov(D, z(p));  occupancy variance share = 1 / Var(S).
"""
from __future__ import annotations
import json, sys
import numpy as np
sys.path.insert(0, "/Users/david/Dev/loopzero-paper-public/src")
from loopzero_paper.benchmarks.recommender.v2_controls import config as C
from loopzero_paper.benchmarks.recommender.phase4_execution import load_diag

OUT = C.OUT_DIR / "s2_exec2_calclean_correlation.json"


def main():
    rows = load_diag(C.PANEL, 20, 20)
    cc = [r for r in rows if r["fold"] == "cal" and r["clean"]]
    n = len(cc)
    print(f"cal-fold CLEAN controls (standardization population): n={n}", flush=True)
    assert n == 694, f"expected 694 cal-fold clean controls, got {n}"

    G = np.array([r["G"] for r in cc], float)
    p = np.array([r["p"] for r in cc], float)
    d = np.array([r["delta"] for r in cc], float)
    R = np.corrcoef(np.column_stack([G, p, d]), rowvar=False)
    r_Gp, r_Gd, r_pd = float(R[0, 1]), float(R[0, 2]), float(R[1, 2])

    var_D = 2 * (1 - r_Gd)
    cov_Dp = r_Gp - r_pd
    var_S = var_D + 1 + 2 * cov_Dp
    occ_share = 1.0 / var_S

    high = r_Gd >= 0.90
    reading = ("RESTORE — r(G,δ)≥0.90 (comparable to eval-arm 0.975); decomposition restored to §5.1 "
               "with correct population, D-43 reinstated with corrected figures"
               if high else
               "REVERT — r(G,δ)<0.90 (materially lower); geometric near-cancellation weakens/fails, "
               "§5.1 reverts to qualitative form permanently")

    out = {
        "population": "694 calibration-fold CLEAN controls (standardization population; z unit-variance by construction)",
        "n": n,
        "pearson_r": {"G_p": round(r_Gp, 5), "G_delta": round(r_Gd, 5), "p_delta": round(r_pd, 5)},
        "decomposition_on_correct_population": {
            "Var_D_=_2(1-r_Gdelta)": round(var_D, 5),
            "Cov_D_zp_=_rGp-rpdelta": round(cov_Dp, 5),
            "Var_S": round(var_S, 5),
            "occupancy_variance_share_=_1/Var_S": round(occ_share, 5),
        },
        "precommitted_reading": reading,
        "note": "D-44 remedy; corrects the eval-arm item-4 matrix. Control-only, no label; verdict untouched.",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"r(G,p)={r_Gp:.5f}  r(G,delta)={r_Gd:.5f}  r(p,delta)={r_pd:.5f}", flush=True)
    print(f"Var(D)={var_D:.5f}  Cov(D,z(p))={cov_Dp:.5f}  Var(S)={var_S:.5f}  occupancy share={occ_share:.5f}", flush=True)
    print(f"PRE-COMMITTED READING: {'RESTORE' if high else 'REVERT'}", flush=True)
    print("CALCLEAN_CORR_DONE", flush=True)


if __name__ == "__main__":
    main()
