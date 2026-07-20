"""Canonical clean-control census generator (label-side only) — Study 2 (osf.io/wka72 §3).

DISCLOSURE (DEVIATIONS D-19): the ORIGINAL script that produced the census artifact anchored
at commit 6b6ac55 (preregistration/STUDY2_CENSUS.sha256) was never committed and is
unrecoverable. This module is the R4 re-derivation, committed as the canonical generator.
It REPRODUCES — and did not produce — the anchored artifact, verified byte-identical:
  study2_clean_control_census.csv          sha256 f286952cd7011bd562aee449d68f221aaa6d0cae6a52350e4c2df2f256188cfc
  study2_clean_control_census_summary.json sha256 994a2a5ab76894424e483436dec6d9c01e75a9918dfaeb1b1dfea0a64a1e8293

Contamination-safe by construction: reads ONLY label-side panel fields
(user_id, label, step, frontier_size_after) — never slate_json / G / p / delta / S / baseline.

Registered logic (wka72 §2/§3):
  * L2 candidate control  = control unstarved at the landmark t_split=20 (frontier >= floor=10).
  * CLEAN                 = candidate not starved in (20, 50]  (frontier never below floor).
  * starvation_time       = first step in (20, 50] with frontier below floor.
  * fold                  = anchored seedless SHA-256 split (§5), verbatim from v2_controls/population.py:16-18.
  * viability gate (§3)   = N(CLEAN,total) >= 1000 AND N(CLEAN,fold) >= 450 in both folds.

The panel input is content-verified (DEVIATIONS D-16/D-17; decompressed sha256 ea972e2e…,
manifest preregistration/PANEL_MANIFEST.json). decision.RATIFIED is irrelevant here (label-side).

Usage:
  python -m loopzero_paper.benchmarks.recommender.study2_clean_control_census \
      --out /tmp/census.csv [--verify results/v2_controls/study2_clean_control_census.csv]
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PANEL = REPO / "results/v2_prereg_slate_relog/movielens25m_recursive_frontier_public_v1__telemetry_panel__slate_v1.csv.gz"
FLOOR = 10          # remaining_frontier_floor (frozen contract)
T_SPLIT = 20        # §2 landmark
HORIZON = 50        # max_horizon_steps
VIA_TOTAL = 1000    # §3 viability gate
VIA_FOLD = 450      # §3 viability gate


def fold(user_id: int) -> str:
    """Verbatim reproduction of v2_controls/population.py:16-18 (anchored §5 fold rule)."""
    h = hashlib.sha256(str(int(user_id)).encode("ascii")).hexdigest()
    return "cal" if h[-1] in "01234567" else "eval"


def _linear_percentile(x_sorted, p):
    """numpy-default ('linear') percentile, dependency-free."""
    n = len(x_sorted)
    if n == 1:
        return float(x_sorted[0])
    rank = (p / 100.0) * (n - 1)
    lo = int(rank)
    frac = rank - lo
    if lo + 1 >= n:
        return float(x_sorted[-1])
    return float(x_sorted[lo] + frac * (x_sorted[lo + 1] - x_sorted[lo]))


def compute(panel_path: Path = PANEL):
    """Return (census_rows, summary_dict). Label-side read only."""
    ctrl = {}   # uid -> {step: frontier_size_after}
    with gzip.open(panel_path, "rt", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["label"] != "control":
                continue
            ctrl.setdefault(int(row["user_id"]), {})[int(row["step"])] = int(row["frontier_size_after"])

    rows = []
    starve_times = []
    for u in sorted(ctrl):
        fr = ctrl[u]
        f20 = fr.get(T_SPLIT)
        is_candidate = 1 if (f20 is not None and f20 >= FLOOR) else 0
        starved_2050, starve_time = "", ""
        if is_candidate:
            hits = [s for s in range(T_SPLIT + 1, HORIZON + 1) if s in fr and fr[s] < FLOOR]
            if hits:
                starved_2050, starve_time = 1, min(hits)
                starve_times.append(starve_time)
            else:
                starved_2050 = 0
        fd = "calibration" if fold(u) == "cal" else "evaluation"
        rows.append([u, fd, is_candidate, starved_2050, starve_time])

    n_cand = sum(1 for r in rows if r[2] == 1)
    clean = [r for r in rows if r[2] == 1 and r[3] == 0]
    n_clean = len(clean)
    cal = sum(1 for r in clean if r[1] == "calibration")
    eva = n_clean - cal
    st = sorted(starve_times)
    gate = {"cal_ge_450": cal >= VIA_FOLD, "eval_ge_450": eva >= VIA_FOLD,
            "total_ge_1000": n_clean >= VIA_TOTAL}
    gate["verdict"] = "PASS" if all(gate.values()) else "FAIL"
    summary = {
        "N_CLEAN_calibration": cal, "N_CLEAN_evaluation": eva, "N_CLEAN_total": n_clean,
        "candidate_controls_unstarved_at_20": n_cand,
        "fields_read": ["user_id", "label", "step", "frontier_size_after"],
        "frontier_floor": FLOOR, "gate": gate, "label_side_only": True,
        "route": "PROCEED-TO-EXECUTION-PROTOCOL" if gate["verdict"] == "PASS" else "NOT-VIABLE",
        "spec": "OSF osf.io/wka72 §3", "stage": "study2_clean_control_census",
        "starvation_time_distribution": {
            "max": max(st), "mean": round(sum(st) / len(st), 3),
            "median": _linear_percentile(st, 50), "min": min(st), "n": len(st),
            "p25": _linear_percentile(st, 25), "p75": _linear_percentile(st, 75)},
        "starve_window": "(20,50]", "starved_in_2050": len(st), "total_controls": len(ctrl),
    }
    return rows, summary


def serialize_csv(rows) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["user_id", "fold", "is_candidate", "starved_in_2050", "starvation_time"])
    for row in rows:
        w.writerow(row)
    return buf.getvalue().encode()


def serialize_summary(summary) -> bytes:
    return (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True, help="CSV output path (summary written alongside)")
    ap.add_argument("--panel", type=Path, default=PANEL)
    ap.add_argument("--verify", type=Path, default=None, help="anchored CSV to byte-compare against")
    args = ap.parse_args()
    rows, summary = compute(args.panel)
    csv_bytes = serialize_csv(rows)
    sum_bytes = serialize_summary(summary)
    args.out.write_bytes(csv_bytes)
    sum_path = args.out.with_name(args.out.stem + "_summary.json")
    sum_path.write_bytes(sum_bytes)
    print(f"census CSV     sha256 {hashlib.sha256(csv_bytes).hexdigest()}  bytes {len(csv_bytes)}  -> {args.out}")
    print(f"census summary sha256 {hashlib.sha256(sum_bytes).hexdigest()}  bytes {len(sum_bytes)}  -> {sum_path}")
    if args.verify is not None:
        anc = args.verify.read_bytes()
        anc_sum = args.verify.with_name(args.verify.stem + "_summary.json").read_bytes()
        print(f"CSV     byte-identity vs anchored: {'YES' if csv_bytes == anc else 'NO'}")
        print(f"summary byte-identity vs anchored: {'YES' if sum_bytes == anc_sum else 'NO'}")


if __name__ == "__main__":
    main()
