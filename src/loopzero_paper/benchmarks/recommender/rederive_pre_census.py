"""D-24 pre-census DERIVED-LAYER re-derivation under C** (registered budget grid).

The seeded-deterministic label-side rebuilds are NOT re-run (D-24 scope). Only the derived layer is
recomputed FROM the anchored per-arm counts in the prior artifact: the per-arm k table
(k = round(b · eval controls) over the registered grid config.BUDGETS) and the I-5a floor / route-cap
evaluation (>=100 CLEAN controls AND >=100 events per eval fold — grid-independent). The derived-layer
logic mirrors pre_census._arm_record / run() exactly; only D.BUDGETS changes (Study-1 -> registered).

Cap tripwire (D-24): route_cap MUST remain UNCONSTRAINED (the floor is a fixed count over untouched
populations). A changed cap => HALT (grid-entangled floor logic, R1-class). Contamination: label-side
counts + budget arithmetic only.

Usage: python -m ...rederive_pre_census --old <old.json> --out <new.json>
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
OLD_ANCHOR_SHA = "28a73b3aad983b201c275ae159d24e453ed4a069cde79cfd1b616b11d27e3ee9"  # PRE_CENSUS.sha256
FLOOR_CLEAN_CONTROLS = 100   # pre_census.FLOOR_CLEAN_CONTROLS (I-5a label-side)
FLOOR_EVENTS = 100           # pre_census.FLOOR_EVENTS


def rederive(old_path: Path, out_path: Path):
    from loopzero_paper.benchmarks.recommender.v2_controls import config as C
    from loopzero_paper.benchmarks.recommender.v2_controls import decision as D
    old_bytes = old_path.read_bytes()
    if hashlib.sha256(old_bytes).hexdigest() != OLD_ANCHOR_SHA:
        raise SystemExit(f"old artifact hash {hashlib.sha256(old_bytes).hexdigest()} != anchor {OLD_ANCHOR_SHA}")
    old = json.loads(old_bytes)
    budgets = tuple(D.BUDGETS)   # C** registered grid {0.02,0.05,0.10,0.20}

    arms = []
    for a in old["arms"]:                                 # anchored counts, grid-independent -> reused
        ev = a["by_fold"]["eval"]
        floor_pass = ev["clean_controls"] >= FLOOR_CLEAN_CONTROLS and ev["events"] >= FLOOR_EVENTS
        kb = {str(b): int(round(b * ev["clean_controls"])) for b in budgets}   # D-26: §6 matched k over eval CLEAN controls (mirrors _arm_record:51)
        arms.append({
            "arm": a["arm"],
            "by_fold": a["by_fold"],
            "eval_clean_controls": ev["clean_controls"],
            "eval_events": ev["events"],
            "i5a_labelside_floor_pass": bool(floor_pass),
            "k_of_b_eval_controls": kb,
        })
    all_clear = all(x["i5a_labelside_floor_pass"] for x in arms)
    report = {
        "stage": "phase25_labelside_pre_census",
        "epistemic_split": old["epistemic_split"],
        "i5a_labelside_floor": {"clean_controls_ge": FLOOR_CLEAN_CONTROLS, "events_ge": FLOOR_EVENTS},
        "arms": arms,
        "all_arms_clear_floor": bool(all_clear),
        "route_cap": ("UNCONSTRAINED" if all_clear else ["SIGNAL DIES", "UNINTERPRETABLE-BY-CONTROL-ARM"]),
        "decision_RATIFIED": D.RATIFIED,
    }
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report, budgets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    report, budgets = rederive(args.old, args.out)
    print(f"registered grid: {tuple(budgets)}")
    print("per-arm k(b) table (control counts) + floor:")
    for a in report["arms"]:
        print(f"  {a['arm']:<16} eval clean={a['eval_clean_controls']:<5} events={a['eval_events']:<6} "
              f"floor={'PASS' if a['i5a_labelside_floor_pass'] else 'FAIL'}  k={a['k_of_b_eval_controls']}")
    print(f"all_arms_clear_floor: {report['all_arms_clear_floor']}")
    print(f"ROUTE_CAP: {report['route_cap']}")
    # D-24 tripwire
    if report["route_cap"] != "UNCONSTRAINED":
        print("!!! CAP CHANGED — TRIPWIRE (D-24): HALT")
        sys.exit(2)
    print("cap == UNCONSTRAINED — matches the D-24 pre-committed expectation")


if __name__ == "__main__":
    main()
