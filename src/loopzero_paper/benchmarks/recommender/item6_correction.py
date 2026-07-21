"""D-41 item-6 correction: split the starvation report into two DISTINCT control populations
defined by the anchored census (6b6ac55). Labeling/reporting split — no new population computation.
Indicators are the same per-unit values already produced in the Phase-4 run (deterministic reload).

  (a) H3-as-frozen:  STARVED-in-(20,50]  (candidate & starved_in_2050)  = 3   vs CLEAN 1,460 -> VACUOUS
  (b) concurrence:   STARVED-at-<=20     (not candidate, pre-landmark)  = 3,292 vs CLEAN 1,460 -> substantive
Partition: 3,292 + 1,460 + 3 = 4,755 (must close).
"""
from __future__ import annotations
import csv, json, sys
import numpy as np
sys.path.insert(0, "/Users/david/Dev/loopzero-paper-public/src")
from loopzero_paper.benchmarks.recommender.v2_controls import config as C
from loopzero_paper.benchmarks.recommender.v2_controls import indicators as I
from loopzero_paper.benchmarks.recommender.phase4_execution import load_diag, cohens_d, IND

CENSUS = C.OUT_DIR / "study2_clean_control_census.csv"
P4 = C.OUT_DIR / "s2_exec2_phase4.json"


def main():
    cen = list(csv.DictReader(open(CENSUS)))
    clean_ids, post_ids, pre_ids = set(), set(), set()
    for r in cen:
        u = int(r["user_id"])
        if r["is_candidate"] == "1":
            (post_ids if r["starved_in_2050"] == "1" else clean_ids).add(u)
        else:
            pre_ids.add(u)
    print(f"census partition: clean={len(clean_ids)} post_(20,50]={len(post_ids)} pre_<=20={len(pre_ids)} "
          f"sum={len(clean_ids)+len(post_ids)+len(pre_ids)}", flush=True)
    assert len(pre_ids) + len(clean_ids) + len(post_ids) == 4755, "partition does not close to 4,755"
    assert len(clean_ids) == 1460 and len(post_ids) == 3 and len(pre_ids) == 3292, "unexpected partition counts"

    rows = load_diag(C.PANEL, 20, 20)
    by = {r["u"]: r for r in rows}
    def vals(ids, key): return np.array([by[u][key] for u in ids if u in by], float)
    def present(ids): return sum(1 for u in ids if u in by)
    print(f"indicator join coverage: clean={present(clean_ids)}/{len(clean_ids)} "
          f"post={present(post_ids)}/{len(post_ids)} pre={present(pre_ids)}/{len(pre_ids)}", flush=True)

    # S composite: z-params on cal-fold CLEAN controls (registered basis)
    cal_clean = [u for u in clean_ids if u in by and by[u]["fold"] == "cal"]
    zp = I.ZParams(np.array([by[u]["G"] for u in cal_clean]), np.array([by[u]["p"] for u in cal_clean]),
                   np.array([by[u]["delta"] for u in cal_clean]))
    def S_of(ids):
        us = [u for u in ids if u in by]
        return I.composite_S(zp.z("G", np.array([by[u]["G"] for u in us])),
                             zp.z("p", np.array([by[u]["p"] for u in us])),
                             zp.z("delta", np.array([by[u]["delta"] for u in us])))

    # (a) H3-as-frozen: counts + vacuity, NO discrimination
    a = {"population_A_starved_in_(20,50]": len(post_ids), "population_CLEAN": len(clean_ids),
         "verdict": "VACUOUS by population fact",
         "note": "Only 3 candidate controls starve post-landmark; H3-as-frozen has no power and no "
                 "discrimination is computed. The CLEAN population excludes them; they never entered L2 as clean."}

    # (b) starvation-concurrence probe: does slate structure read PRE-landmark frontier depletion?
    names = {"G": "z(G) churn", "p": "z(p) occupancy", "delta": "z(δ) coverage", "mrf": "miss_run_fraction"}
    b_ind = {}
    for k in IND:
        d = cohens_d(vals(pre_ids, k), vals(clean_ids, k))
        b_ind[k] = round(float(d), 4)
        print(f"  (b) {names[k]}: d(pre-landmark vs clean) = {d:.4f}", flush=True)
    dS = cohens_d(S_of(pre_ids), S_of(clean_ids))
    print(f"  (b) S composite: d(pre-landmark vs clean) = {dS:.4f}", flush=True)
    slate_max = max(abs(b_ind["G"]), abs(b_ind["p"]), abs(b_ind["delta"]), abs(dS))
    reading = ("slate structure READS frontier depletion (|d|>=0.8) — S is in part a frontier-depletion "
               "detector; this is the contamination the CLEAN purification removes"
               if slate_max >= 0.8 else
               ("inconclusive (0.2<=|d|<0.8)" if slate_max >= 0.2 else
                "slate structure does NOT encode pre-landmark starvation (|d|<0.2)"))
    b = {"population_B_starved_at_<=20_prelandmark": len(pre_ids), "population_CLEAN": len(clean_ids),
         "cohens_d_pre_vs_clean": {**b_ind, "S_composite": round(float(dS), 4)},
         "precommitted_reading": reading, "max_slate_abs_d": round(float(slate_max), 4)}

    corrected = {
        "partition_check": {"pre_landmark_<=20": len(pre_ids), "clean": len(clean_ids),
                            "post_landmark_(20,50]": len(post_ids),
                            "sum": len(pre_ids) + len(clean_ids) + len(post_ids), "closes_to_4755": True},
        "a_H3_as_frozen": a,
        "b_starvation_concurrence_probe": b,
        "events_frontier_crossed_floor_before_collapse": 0,
        "note": "D-41 correction: (a) and (b) are DISTINCT control populations (census 6b6ac55), not one figure.",
    }
    p4 = json.loads(P4.read_text())
    p4["item6_starvation_concurrence"] = corrected
    P4.write_text(json.dumps(p4, indent=2, sort_keys=True) + "\n")
    print("ITEM6_CORRECTED", flush=True)
    print(json.dumps(corrected, indent=2))


if __name__ == "__main__":
    main()
