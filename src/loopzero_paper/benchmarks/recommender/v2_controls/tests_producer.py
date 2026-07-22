"""Producer known-answer tests on SYNTHETIC/constructed data ONLY (never the real or
real-control slate panels). Planted signal -> ΔTPR>0, correct covariate signs, incr
AUC>0; permuted labels -> chance (ΔTPR CI incl 0, incr AUC CI incl 0). Also debugs
load_arm_units on a tiny constructed slate panel. No real-engine decision quantity.
"""
from __future__ import annotations
import sys, json, gzip, tempfile
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "src"))
from loopzero_paper.benchmarks.recommender.v2_controls import producer as P
from loopzero_paper.benchmarks.recommender.v2_controls import config as C
from loopzero_paper.benchmarks.recommender.v2_controls.population import fold


def make_arm(planted: bool, n=1500, seed=0):
    rng = np.random.default_rng(seed)
    # ~80% events; assign folds by real SHA fold() on synthetic ids
    uid = np.arange(1, n + 1)
    fd = np.array([fold(int(u)) for u in uid])
    y = (rng.random(n) < 0.8)
    if planted:
        # events: higher G, higher p, lower delta (S separates); controls opposite
        G = np.where(y, rng.normal(0.55, 0.08, n), rng.normal(0.30, 0.08, n))
        p = np.where(y, rng.normal(0.10, 0.01, n), rng.normal(0.07, 0.01, n))
        dl = np.where(y, rng.normal(0.05, 0.01, n), rng.normal(0.11, 0.01, n))
    else:
        G = rng.normal(0.42, 0.12, n); p = rng.normal(0.085, 0.015, n); dl = rng.normal(0.08, 0.03, n)
    # ensure delta has >=20 distinct values / IQR>0 for PC2
    dl = np.round(dl, 4)
    mrf = np.clip(rng.random((n, 20)), 0, 1)      # miss series: chance (baselines at chance)
    hit = (rng.random((n, 20)) > 0.5).astype(int)
    clean = (~y)                                    # treat controls as clean for measurability test
    a = P.ArmUnits(uid, fd, y, clean, G, p, dl, mrf, hit)
    log_act = rng.normal(3, 1, n); pop_aff = rng.normal(2, 1, n)   # uninformative covariates
    return a, log_act, pop_aff


def run():
    out = {}
    # ---- planted: ΔTPR should be clearly positive at b=0.05, S separates ----
    a, la, pa = make_arm(planted=True, seed=1)
    S = P.s_scores(a); Bm, _ = P.baseline_score_matrix(a); ev = a.fold == "eval"
    dt = P.delta_tpr_ci(S[ev], Bm[ev], a.is_event[ev], a.user_id[ev], 0.05, n_boot=300)
    bG, bP, bD, incr = P.covariate_summary(a, la, pa, n_boot=200)
    planted_ok = (dt[0] > 0.05 and dt[1] > 0) and (bG[1] > 0 and bP[1] > 0 and bD[2] < 0) and (incr[0] > 0.02 and incr[1] > 0)
    out["planted"] = {"delta_tpr_b05": [round(x, 4) for x in dt], "bG": [round(x,3) for x in bG],
                      "bP": [round(x,3) for x in bP], "bD": [round(x,3) for x in bD],
                      "incr_auc": [round(x,4) for x in incr], "pass": bool(planted_ok)}

    # ---- permuted: chance -> ΔTPR CI incl 0, incr AUC CI incl 0 ----
    a2, la2, pa2 = make_arm(planted=False, seed=2)
    S2 = P.s_scores(a2); Bm2, _ = P.baseline_score_matrix(a2); ev2 = a2.fold == "eval"
    dt2 = P.delta_tpr_ci(S2[ev2], Bm2[ev2], a2.is_event[ev2], a2.user_id[ev2], 0.05, n_boot=300)
    _, _, _, incr2 = P.covariate_summary(a2, la2, pa2, n_boot=200)
    chance_ok = (dt2[1] <= 0 <= dt2[2]) and (incr2[1] <= 0 <= incr2[2])
    out["permuted"] = {"delta_tpr_b05": [round(x,4) for x in dt2], "incr_auc": [round(x,4) for x in incr2],
                       "pass": bool(chance_ok)}

    # ---- gates + measurability sane ----
    pc1 = P.pc1_gate_ci(a, n_boot=200); pc2 = P.pc2_pass(a); meas = P.measurability(a)
    out["gates"] = {"pc1_minus_b": [round(x,4) for x in pc1], "pc2_pass": bool(pc2),
                    "measurability(nclean,nev,sdistinct,siqr)": [meas[0], meas[1], meas[2], round(meas[3],4)]}

    # ---- load_arm_units on a tiny constructed slate panel (parse + clean-control debug) ----
    import csv as _csv
    d = Path(tempfile.mkdtemp()); pan = d / "synth_panel.csv.gz"
    hdr = ["user_id","label","step","collapse_step","hit_this_step","consecutive_misses_after_step",
           "slate_json","frontier_size_after"]
    rng = np.random.default_rng(3)
    # users 1..40 control (u%4==0 -> STARVED after 20 => EXCLUDED by the D-7 fix; else clean);
    # 41..80 events collapse_step=30. Post-fix, L2 admits only CLEAN controls.
    n_ctrl_clean_expected = 0
    with gzip.open(pan, "wt", newline="") as f:
        w = _csv.writer(f); w.writerow(hdr)
        for u in range(1, 41):
            starved = (u % 4 == 0)
            if not starved: n_ctrl_clean_expected += 1
            for st in range(1, 51):
                fr = 5 if (starved and st > 20) else 20   # starved controls drop below floor after 20
                slate = json.dumps([int(x) for x in rng.integers(1, 500, 10)])
                w.writerow([u, "control", st, "", int(rng.random() > 0.5), int(rng.integers(0, 8)), slate, fr])
        for u in range(41, 81):
            for st in range(1, 31):                        # event, collapse at 30 (in (20,50])
                slate = json.dumps([int(x) for x in rng.integers(1, 500, 10)])
                w.writerow([u, "event", st, 30, int(rng.random() > 0.5), int(rng.integers(0, 8)), slate, 20])
    au = P.load_arm_units(pan)
    n_clean = int(au.clean_control.sum()); n_ctrl = int((~au.is_event).sum())
    # D-7: starved controls are excluded from L2, so admitted controls == clean controls (30), not 40
    clean_ok = (n_clean == n_ctrl_clean_expected) and (n_ctrl == n_ctrl_clean_expected)
    out["load_arm_units"] = {"n_units": len(au.user_id), "n_controls": n_ctrl, "n_clean": n_clean,
                             "n_clean_expected": n_ctrl_clean_expected, "mrf_shape": list(au.mrf.shape),
                             "clean_determination_pass": bool(clean_ok)}

    out["all_pass"] = bool(planted_ok and chance_ok and clean_ok and len(au.user_id) > 0)
    return out


if __name__ == "__main__":
    import json as _j
    res = run()
    print(_j.dumps(res, indent=2))
    (C.OUT_DIR / "producer_test_results.json").write_text(_j.dumps(res, indent=2, sort_keys=True) + "\n")
    sys.exit(0 if res["all_pass"] else 1)
