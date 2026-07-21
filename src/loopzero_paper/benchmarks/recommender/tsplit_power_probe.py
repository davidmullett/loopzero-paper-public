"""D-37 power probe (label-side only). For t_split in {15,20,25}, count the complete-window
eval-fold EVENT population (collapse in (t,50] AND slate window 1..t complete) and the eval-fold
CLEAN control population (never frontier<floor across the horizon AND window 1..t complete).
Applies the D-37 rule: eval events < 200 -> that landmark's sensitivity is NOT EXECUTABLE.
Emits COUNTS ONLY (no indicator value, no slate content).
"""
from __future__ import annotations
import gzip, csv, json, sys
sys.path.insert(0, "/Users/david/Dev/loopzero-paper-public/src")
from loopzero_paper.benchmarks.recommender.v2_controls import config as C
from loopzero_paper.benchmarks.recommender.v2_controls.population import fold

csv.field_size_limit(1 << 24)
FLOOR = 10
LANDMARKS = (15, 20, 25)
MAXW = max(LANDMARKS)
POWER_FLOOR = C.POWER_MIN_EVAL_EVENTS  # 200


def main():
    per = {}
    with gzip.open(C.PANEL, "rt", newline="") as f:
        for row in csv.DictReader(f):
            u = int(row["user_id"]); st = int(row["step"])
            rec = per.get(u)
            if rec is None:
                cs = row["collapse_step"]
                rec = per[u] = {"label": row["label"],
                                "cs": None if cs in ("", "NA") else int(float(cs)),
                                "steps": set(), "minfront": 10**9}
            if st <= MAXW and row.get("slate_json") not in (None, "", "NA"):
                rec["steps"].add(st)
            fs = row.get("frontier_size_after")
            if fs not in (None, "", "NA"):
                rec["minfront"] = min(rec["minfront"], int(fs))

    report = {"power_floor": POWER_FLOOR, "landmarks": {}}
    for t in LANDMARKS:
        need = set(range(1, t + 1))
        ev = cc = 0
        for u, rec in per.items():
            if not need.issubset(rec["steps"]):
                continue
            fo = fold(u)
            if fo != "eval":
                continue
            lab, cs = rec["label"], rec["cs"]
            if lab == "event" and cs is not None and t < cs <= 50:
                ev += 1
            elif lab == "control" and rec["minfront"] >= FLOOR:
                cc += 1
        executable = ev >= POWER_FLOOR
        report["landmarks"][t] = {"eval_events": ev, "eval_clean_controls": cc,
                                  "executable": executable,
                                  "verdict": "EXECUTABLE" if executable else "NOT EXECUTABLE (below §11 power floor 200)"}
        print(f"t_split={t}: eval_events={ev} eval_clean_controls={cc} -> {report['landmarks'][t]['verdict']}", flush=True)
    (C.OUT_DIR / "s2_exec2_tsplit_power_probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("PROBE_DONE", flush=True)


if __name__ == "__main__":
    main()
