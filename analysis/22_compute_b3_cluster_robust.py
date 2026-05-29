#!/usr/bin/env python3
"""
B3 — Markets cluster-robust sensitivity (symmetric scenario grain).

Re-runs A3's cluster-aware bootstrap with cluster grain shifted from
segment-level (unit_id, n=54) to scenario-level (n=2 event clusters + 5
control scenarios = 7 total clusters).

Event composition (derived from unit_id parsing):
  volmageddon_2018_xiv:   8 segments
  covid_mwcb_2020_03_18:  8 segments

Control composition (derived from unit_id parsing):
  covid_noncollapse_2020_03_11:   8 segments
  volmageddon_control_2018_01_29: 8 segments
  volmageddon_control_2018_02_08: 8 segments
  covid_noncollapse_2020_03_13:   7 segments
  volmageddon_control_2018_01_25: 7 segments

Methodological notes:
  - At n=2 event clusters, the standard cluster bootstrap is in the
    small-cluster regime. Wild cluster bootstrap (Cameron, Gelbach &
    Miller 2008) is the methodologically appropriate response. Deferred
    to v2. This script reports the standard cluster bootstrap as a
    conservative UPPER BOUND on dependence-induced CI inflation.
  - Recsys cluster-robust strata sensitivity (item-popularity,
    time-period, activity) deferred to v2 with recsys-domain coauthor
    expertise on stratum definitions. At recsys n≈40K, A3's user-level
    clustering already captures dominant dependence; |BCa − percentile|
    < 0.01 on every endpoint (A3 finding), so further stratification
    expected to leave CIs essentially unchanged.

Reuses A3 (analysis/15_compute_effect_sizes.py) primitives:
  - BENCHMARK_SPECS[0] for markets spec
  - load_panel_for_spec for data loading
  - compute_cohens_d, compute_glasss_d, compute_rank_auc
  - bootstrap_ci, jackknife_clustered, compute_bca_correction

Outputs:
  results/calibrated/b3_markets_cluster_robust.csv
  results/calibrated/b3_markets_cluster_robust.md
"""

from __future__ import annotations
import argparse
import inspect
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add analysis dir to path so we can import the A3 module
sys.path.insert(0, str(Path(__file__).resolve().parent))
a3 = __import__("15_compute_effect_sizes")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "results" / "calibrated"

# Distinct seed from A3 (which uses 42) so the two analyses don't share a
# bootstrap RNG path.
RANDOM_SEED_B3: int = 43

# Expected cluster composition (sanity-check guard).
EXPECTED_EVENT_CLUSTERS = {
    "volmageddon_2018_xiv": 8,
    "covid_mwcb_2020_03_18": 8,
}
EXPECTED_CONTROL_CLUSTERS = {
    "covid_noncollapse_2020_03_11": 8,
    "volmageddon_control_2018_01_29": 8,
    "volmageddon_control_2018_02_08": 8,
    "covid_noncollapse_2020_03_13": 7,
    "volmageddon_control_2018_01_25": 7,
}


def derive_cluster_id(unit_id: str) -> str:
    """unit_id 'cfg_<config>__<scenario>__seg_<NN>' → '<scenario>'."""
    parts = unit_id.split("__")
    if len(parts) >= 3:
        return parts[1]
    raise ValueError(f"unit_id does not parse to scenario: {unit_id!r}")


def surface_a3_signatures() -> None:
    """Print A3 function signatures so any mismatch is caught BEFORE the bootstrap."""
    print("=== A3 function signatures (dry-run check) ===")
    for fname in ["bootstrap_ci", "jackknife_clustered", "compute_bca_correction",
                  "compute_cohens_d", "compute_glasss_d", "compute_rank_auc",
                  "load_panel_for_spec"]:
        fn = getattr(a3, fname, None)
        if fn is None:
            print(f"  MISSING: {fname}")
            continue
        try:
            sig = inspect.signature(fn)
            print(f"  {fname}{sig}")
        except (ValueError, TypeError) as e:
            print(f"  {fname}: signature unavailable ({e})")
    print(f"  RANDOM_SEED in A3: {getattr(a3, 'RANDOM_SEED', 'MISSING')}")
    print(f"  CI_LEVEL in A3:    {getattr(a3, 'CI_LEVEL', 'MISSING')}")
    print(f"  BOOTSTRAP_ITERATIONS in A3: {getattr(a3, 'BOOTSTRAP_ITERATIONS', 'MISSING')}")
    print()


def robust_recompute_ci(
    point: float,
    bootstrap_dist: np.ndarray,
    jack: np.ndarray,
    ci_level: float,
) -> tuple[float, float, float, float, int]:
    """Filter non-finite bootstrap/jackknife iterations and recompute percentile + BCa CIs.

    Returns (lo_pct, hi_pct, lo_bca, hi_bca, n_degenerate).
    Small-cluster regime (n=2 event clusters; n=5 control scenarios) occasionally
    produces degenerate samples for Glass's d (control SD near zero); we filter
    those and report the count.
    """
    finite_boot_mask = np.isfinite(bootstrap_dist)
    n_degenerate = int(np.sum(~finite_boot_mask))
    finite_boot = bootstrap_dist[finite_boot_mask]
    if len(finite_boot) == 0:
        return (float("nan"), float("nan"), float("nan"), float("nan"), n_degenerate)
    alpha = 1.0 - ci_level
    lo_pct = float(np.percentile(finite_boot, alpha / 2.0 * 100.0))
    hi_pct = float(np.percentile(finite_boot, (1.0 - alpha / 2.0) * 100.0))
    finite_jack = jack[np.isfinite(jack)] if hasattr(jack, "__len__") else jack
    if (hasattr(finite_jack, "__len__") and len(finite_jack) > 0
            and np.isfinite(point)):
        lo_bca, hi_bca = a3.compute_bca_correction(
            point, finite_boot, finite_jack, ci_level=ci_level,
        )
    else:
        lo_bca, hi_bca = float("nan"), float("nan")
    return (lo_pct, hi_pct, lo_bca, hi_bca, n_degenerate)


def run_markets_b3(n_iterations: int) -> pd.DataFrame:
    """Run B3 scenario-grain cluster bootstrap on markets."""
    markets_spec = a3.BENCHMARK_SPECS[0]
    assert markets_spec.domain == "markets", \
        f"Expected markets spec at index 0; got {markets_spec.domain}"

    event_rows, control_rows = a3.load_panel_for_spec(markets_spec)

    # Derive scenario-grain cluster_id on both panels
    event_rows = event_rows.assign(
        cluster_id=event_rows["unit_id"].map(derive_cluster_id)
    )
    control_rows = control_rows.assign(
        cluster_id=control_rows["unit_id"].map(derive_cluster_id)
    )

    # Sanity guard: cluster composition matches what the diagnostic showed
    event_composition = event_rows.groupby("cluster_id")["unit_id"].nunique().to_dict()
    control_composition = control_rows.groupby("cluster_id")["unit_id"].nunique().to_dict()
    print(f"Event cluster composition:   {event_composition}")
    print(f"Control cluster composition: {control_composition}")
    assert event_composition == EXPECTED_EVENT_CLUSTERS, \
        f"Event composition mismatch: got {event_composition}, expected {EXPECTED_EVENT_CLUSTERS}"
    assert control_composition == EXPECTED_CONTROL_CLUSTERS, \
        f"Control composition mismatch: got {control_composition}, expected {EXPECTED_CONTROL_CLUSTERS}"
    print(f"  n event clusters:   {len(event_composition)}")
    print(f"  n control clusters: {len(control_composition)}")
    print()

    statistic_fns = {
        "cohens_d": a3.compute_cohens_d,
        "glasss_d": a3.compute_glasss_d,
        "rank_auc": a3.compute_rank_auc,
    }

    rows = []
    for witness in ["G", "p", "delta"]:
        for measure_name, statistic_fn in statistic_fns.items():
            print(f"[{witness} | {measure_name}] scenario-grain bootstrap "
                  f"({n_iterations:,} iters)...")

            rng = np.random.default_rng(RANDOM_SEED_B3)
            point, lo_pct, hi_pct, bootstrap_dist = a3.bootstrap_ci(
                event_rows, control_rows,
                witness_col=witness,
                unit_col="cluster_id",
                statistic_fn=statistic_fn,
                n_iterations=n_iterations,
                rng=rng,
                method="percentile",
            )

            jack = a3.jackknife_clustered(
                event_rows, control_rows, witness, "cluster_id",
                statistic_fn,
            )

            # Robust recompute: filter non-finite iterations (small-cluster regime
            # can produce degenerate Glass's d samples when control SD ≈ 0).
            lo_pct, hi_pct, lo_bca, hi_bca, n_degenerate = robust_recompute_ci(
                point, bootstrap_dist, jack, ci_level=a3.CI_LEVEL,
            )

            degen_note = f"  (n_degenerate={n_degenerate}/{n_iterations})" if n_degenerate > 0 else ""
            print(f"  point={point:+8.4f}  "
                  f"pct=[{lo_pct:+8.4f}, {hi_pct:+8.4f}]  "
                  f"bca=[{lo_bca:+8.4f}, {hi_bca:+8.4f}]{degen_note}")

            rows.append({
                "benchmark_id": markets_spec.benchmark_id,
                "witness": witness,
                "effect_measure": measure_name,
                "cluster_grain": "scenario",
                "n_event_clusters": len(event_composition),
                "n_control_clusters": len(control_composition),
                "n_iterations": n_iterations,
                "n_degenerate_iterations": n_degenerate,
                "point_estimate": point,
                "ci_lower_percentile": lo_pct,
                "ci_upper_percentile": hi_pct,
                "ci_lower_bca": lo_bca,
                "ci_upper_bca": hi_bca,
            })

    return pd.DataFrame(rows)


def load_a3_baseline() -> pd.DataFrame:
    """Locate A3's canonical segment-grain CSV for side-by-side comparison."""
    candidates = [
        ROOT / "results" / "rendered" / "effect_sizes" / "a3_effect_sizes_full.csv",
        ROOT / "results" / "calibrated" / "a3_effect_sizes_full.csv",
        ROOT / "results" / "rendered" / "effect_sizes" / "supplementary_table_s2.csv",
    ]
    for path in candidates:
        if path.exists():
            df = pd.read_csv(path)
            if "benchmark_id" in df.columns:
                df = df[df["benchmark_id"] == "volmageddon_covid_public_v2"].copy()
            print(f"Loaded A3 baseline from: {path}  ({len(df)} markets rows)")
            return df
    print("WARN: A3 baseline CSV not found in expected locations; "
          "side-by-side comparison skipped.")
    return pd.DataFrame()


def write_outputs(b3_rows: pd.DataFrame, a3_baseline: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUT_DIR / "b3_markets_cluster_robust.csv"
    b3_rows.to_csv(csv_path, index=False)
    print(f"\nWrote: {csv_path}")

    md_lines = [
        "# B3 — Markets cluster-robust sensitivity (scenario grain)",
        "",
        "## Cluster composition",
        "",
        "Event-side scenario clusters (derived from `unit_id` parsing; n=2):",
        "",
        "| Cluster | Segments |",
        "|---------|----------|",
        f"| volmageddon_2018_xiv  | 8 |",
        f"| covid_mwcb_2020_03_18 | 8 |",
        "",
        "Control-side scenario clusters (n=5):",
        "",
        "| Cluster | Segments |",
        "|---------|----------|",
        f"| covid_noncollapse_2020_03_11   | 8 |",
        f"| volmageddon_control_2018_01_29 | 8 |",
        f"| volmageddon_control_2018_02_08 | 8 |",
        f"| covid_noncollapse_2020_03_13   | 7 |",
        f"| volmageddon_control_2018_01_25 | 7 |",
        "",
        "Total cluster units: 7 (2 event + 5 control), down from 54 segment units in A3.",
        "",
        "## Methodological framing",
        "",
        "Cluster-aware bootstrap (10,000 iterations) at scenario grain. Reported as a "
        "**conservative upper bound on dependence-induced CI inflation** under the "
        "matched-control experimental design. Wild cluster bootstrap "
        "(Cameron, Gelbach & Miller 2008) — the methodologically appropriate response "
        "to the small-cluster regime (n=2 event clusters) — is deferred to v2.",
        "",
        "## Effect sizes at scenario grain (B3)",
        "",
        "| Witness | Measure   | Point | Percentile 95% CI | BCa 95% CI |",
        "|---------|-----------|-------|-------------------|------------|",
    ]
    for _, r in b3_rows.iterrows():
        md_lines.append(
            f"| {r['witness']} | {r['effect_measure']} | "
            f"{r['point_estimate']:+.4f} | "
            f"[{r['ci_lower_percentile']:+.4f}, {r['ci_upper_percentile']:+.4f}] | "
            f"[{r['ci_lower_bca']:+.4f}, {r['ci_upper_bca']:+.4f}] |"
        )

    if not a3_baseline.empty and "ci_lower_bca" in a3_baseline.columns:
        md_lines += [
            "",
            "## Side-by-side: A3 segment grain vs B3 scenario grain (BCa 95% CI)",
            "",
            "| Witness | Measure | A3 segment grain (n=54) | B3 scenario grain (n=7) | CI width ratio |",
            "|---------|---------|--------------------------|--------------------------|----------------|",
        ]
        for _, r in b3_rows.iterrows():
            match = a3_baseline[
                (a3_baseline["witness"] == r["witness"])
                & (a3_baseline["effect_measure"] == r["effect_measure"])
            ]
            if match.empty:
                md_lines.append(
                    f"| {r['witness']} | {r['effect_measure']} | (not in A3 CSV) | "
                    f"[{r['ci_lower_bca']:+.4f}, {r['ci_upper_bca']:+.4f}] | – |"
                )
                continue
            a3_row = match.iloc[0]
            a3_lo = float(a3_row["ci_lower_bca"])
            a3_hi = float(a3_row["ci_upper_bca"])
            a3_width = a3_hi - a3_lo
            b3_width = float(r["ci_upper_bca"]) - float(r["ci_lower_bca"])
            ratio = b3_width / a3_width if a3_width > 0 else float("inf")
            md_lines.append(
                f"| {r['witness']} | {r['effect_measure']} | "
                f"[{a3_lo:+.4f}, {a3_hi:+.4f}] | "
                f"[{r['ci_lower_bca']:+.4f}, {r['ci_upper_bca']:+.4f}] | "
                f"{ratio:.2f}× |"
            )

    md_path = OUT_DIR / "b3_markets_cluster_robust.md"
    md_path.write_text("\n".join(md_lines) + "\n")
    print(f"Wrote: {md_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="B3 markets cluster-robust sensitivity at scenario grain."
    )
    parser.add_argument(
        "--n-iterations", type=int, default=10_000,
        help="Bootstrap iterations (default: 10000; matches A3).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Only print A3 function signatures; do not run bootstrap.",
    )
    args = parser.parse_args()

    surface_a3_signatures()
    if args.dry_run:
        return 0

    b3_rows = run_markets_b3(n_iterations=args.n_iterations)
    a3_baseline = load_a3_baseline()
    write_outputs(b3_rows, a3_baseline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
