#!/usr/bin/env python3
"""
analysis/20_compute_a2_threshold_path.py

A2 — Threshold-path event detection rates (Path A+C v2, Option A locked).

Produces two output tables for Day 5 manuscript integration:

Table 1: Comparator threshold-path at canonical FPR sweep
  For the 4 bracketed (family, benchmark, horizon) cells where existing
  frozen calibration data brackets FPR=0.05:
    - variance_ews recsys h=40
    - variance_ews recsys h=60
    - matrix_profile recsys h=40 (FPR=0.01 below min, status=below_min_fp)
    - matrix_profile recsys h=60
  At each target FPR in {0.01, 0.025, 0.05, 0.075, 0.10}, linear
  interpolation of TPR between adjacent (fp, tpr) breakpoints. Breakpoints
  reported alongside for transparency.

Table 2: Envelope-boundary matched-FP comparison per panel
  For each panel at the canonical k=3:
    - markets (volmageddon_covid_public_v2)
    - recsys movielens25m h=40
    - recsys movielens25m h=50 canonical
    - recsys movielens25m h=60
  Loopzero is reported at the maximum control_fp achieved across the
  extended q-grid [50, 60, 70, 75, 80, 85, 90, 95, 99] (the envelope
  boundary). Each comparator family in the panel is then interpolated at
  the same FP where envelope overlap exists, or marked "no_overlap"
  otherwise. This is the matched-FP comparison contract operationalized
  at the envelope boundary.

Reads:
  results/rendered/a4_roc_lowfp/a4_roc_data.parquet
  results/rendered/bridge/a1_loopzero_operating_points.csv
  results/rendered/bridge/a1_loopzero_operating_points_h40_h60.csv

Writes:
  results/calibrated/a2_threshold_path_comparator_at_fpr_sweep.{csv,md}
  results/calibrated/a2_threshold_path_envelope_boundary.{csv,md}
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent

A4_PARQUET = REPO_ROOT / "results/rendered/a4_roc_lowfp/a4_roc_data.parquet"
LOOPZERO_MAIN_CSV = REPO_ROOT / "results/rendered/bridge/a1_loopzero_operating_points.csv"
LOOPZERO_H40_H60_CSV = REPO_ROOT / "results/rendered/bridge/a1_loopzero_operating_points_h40_h60.csv"

OUT_DIR = REPO_ROOT / "results/calibrated"
OUT_TABLE1_CSV = OUT_DIR / "a2_threshold_path_comparator_at_fpr_sweep.csv"
OUT_TABLE1_MD = OUT_DIR / "a2_threshold_path_comparator_at_fpr_sweep.md"
OUT_TABLE2_CSV = OUT_DIR / "a2_threshold_path_envelope_boundary.csv"
OUT_TABLE2_MD = OUT_DIR / "a2_threshold_path_envelope_boundary.md"

FPR_SWEEP_TARGETS = [0.01, 0.025, 0.05, 0.075, 0.10]

BRACKETED_CELLS = [
    ("variance_ews", "recsys", 40),
    ("variance_ews", "recsys", 60),
    ("matrix_profile", "recsys", 40),
    ("matrix_profile", "recsys", 60),
]

PANELS = [
    ("markets", "markets", None),
    ("recsys_h40", "recsys", 40),
    ("recsys_h50", "recsys", 50),
    ("recsys_h60", "recsys", 60),
]

PRIMARY_K = 3


# ---------------------------------------------------------------------------
# Linear interpolation with breakpoint reporting
# ---------------------------------------------------------------------------
def linear_interpolate_with_breakpoints(
    target_fp: float,
    fp_array: np.ndarray,
    tpr_array: np.ndarray,
) -> dict:
    """Linearly interpolate TPR at target_fp from sorted (fp, tpr) breakpoints.

    Returns dict with keys:
      interpolated_tpr: float or NaN
      status: 'interpolated' | 'at_observed_fp' | 'below_min_fp' |
              'above_max_fp' | 'insufficient_data'
      lower_fp, lower_tpr, upper_fp, upper_tpr: breakpoints used (NaN if
        not applicable)
      n_breakpoints: number of unique FPs available
    """
    order = np.argsort(fp_array)
    fps = np.asarray(fp_array)[order]
    tprs = np.asarray(tpr_array)[order]
    n = len(fps)

    base = {
        "interpolated_tpr": np.nan,
        "status": "insufficient_data",
        "lower_fp": np.nan,
        "lower_tpr": np.nan,
        "upper_fp": np.nan,
        "upper_tpr": np.nan,
        "n_breakpoints": n,
    }

    if n < 2:
        return base

    if target_fp < fps[0]:
        return {**base, "status": "below_min_fp",
                "upper_fp": float(fps[0]), "upper_tpr": float(tprs[0])}

    if target_fp > fps[-1]:
        return {**base, "status": "above_max_fp",
                "lower_fp": float(fps[-1]), "lower_tpr": float(tprs[-1])}

    for i in range(n - 1):
        if fps[i] <= target_fp <= fps[i + 1]:
            lower_fp, upper_fp = float(fps[i]), float(fps[i + 1])
            lower_tpr, upper_tpr = float(tprs[i]), float(tprs[i + 1])
            if lower_fp == target_fp:
                return {**base, "interpolated_tpr": lower_tpr,
                        "status": "at_observed_fp",
                        "lower_fp": lower_fp, "lower_tpr": lower_tpr,
                        "upper_fp": upper_fp, "upper_tpr": upper_tpr}
            if upper_fp == target_fp:
                return {**base, "interpolated_tpr": upper_tpr,
                        "status": "at_observed_fp",
                        "lower_fp": lower_fp, "lower_tpr": lower_tpr,
                        "upper_fp": upper_fp, "upper_tpr": upper_tpr}
            frac = (target_fp - lower_fp) / (upper_fp - lower_fp)
            interp_tpr = lower_tpr + frac * (upper_tpr - lower_tpr)
            return {**base, "interpolated_tpr": float(interp_tpr),
                    "status": "interpolated",
                    "lower_fp": lower_fp, "lower_tpr": lower_tpr,
                    "upper_fp": upper_fp, "upper_tpr": upper_tpr}
    return base


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_comparator_data() -> pd.DataFrame:
    """Load A4 canonical parquet, filter to curve_point, collapse duplicates."""
    df = pd.read_parquet(A4_PARQUET)
    df = df[df["source_type"] == "curve_point"].copy()
    df = (
        df.groupby(["family", "domain", "horizon", "fp"], dropna=False)["tpr"]
        .max()
        .reset_index()
    )
    return df


def get_comparator_breakpoints(
    df_comp: pd.DataFrame,
    family: str,
    domain: str,
    horizon: Optional[float],
) -> tuple[np.ndarray, np.ndarray]:
    if horizon is None:
        mask = (
            (df_comp["family"] == family)
            & (df_comp["domain"] == domain)
            & (df_comp["horizon"].isna())
        )
    else:
        mask = (
            (df_comp["family"] == family)
            & (df_comp["domain"] == domain)
            & (df_comp["horizon"] == horizon)
        )
    sub = df_comp[mask].sort_values("fp")
    return sub["fp"].to_numpy(), sub["tpr"].to_numpy()


def load_loopzero_at_k(k: int) -> pd.DataFrame:
    a = pd.read_csv(LOOPZERO_MAIN_CSV)
    b = pd.read_csv(LOOPZERO_H40_H60_CSV)
    df = pd.concat([a, b], ignore_index=True)
    df = df[df["k"] == k].copy()

    def parse_horizon(row):
        if row["domain"] == "markets":
            return None
        bm = str(row["benchmark"])
        if "__horizon_40" in bm: return 40
        if "__horizon_60" in bm: return 60
        if "__canonical_h50" in bm: return 50
        return None

    df["horizon"] = df.apply(parse_horizon, axis=1)
    return df


def get_loopzero_envelope_boundary(
    df_loop: pd.DataFrame,
    domain: str,
    horizon: Optional[int],
) -> dict:
    if horizon is None:
        mask = (df_loop["domain"] == domain) & (df_loop["horizon"].isna())
    else:
        mask = (df_loop["domain"] == domain) & (df_loop["horizon"] == horizon)
    sub = df_loop[mask].copy()
    if sub.empty:
        raise ValueError(f"No Loopzero rows for domain={domain} horizon={horizon}")
    max_fp = sub["control_fp"].max()
    boundary = (sub[sub["control_fp"] == max_fp]
                .sort_values("event_alarm_rate", ascending=False)
                .iloc[0])
    return {
        "loopzero_boundary_fp": float(boundary["control_fp"]),
        "loopzero_boundary_q": float(boundary["q_G_pct"]),
        "loopzero_boundary_k": int(boundary["k"]),
        "loopzero_boundary_tpr": float(boundary["event_alarm_rate"]),
    }


# ---------------------------------------------------------------------------
# Compute tables
# ---------------------------------------------------------------------------
def compute_table1(df_comp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family, domain, horizon in BRACKETED_CELLS:
        fps, tprs = get_comparator_breakpoints(df_comp, family, domain, horizon)
        for target_fpr in FPR_SWEEP_TARGETS:
            interp = linear_interpolate_with_breakpoints(target_fpr, fps, tprs)
            rows.append({"family": family, "domain": domain, "horizon": horizon,
                         "target_fpr": target_fpr, **interp})
    return pd.DataFrame(rows)


def compute_table2(df_loop: pd.DataFrame, df_comp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for panel_id, domain, horizon in PANELS:
        loop_boundary = get_loopzero_envelope_boundary(df_loop, domain, horizon)
        if horizon is None:
            comp_mask = (df_comp["domain"] == domain) & (df_comp["horizon"].isna())
        else:
            comp_mask = (df_comp["domain"] == domain) & (df_comp["horizon"] == horizon)
        families_in_panel = sorted(df_comp[comp_mask]["family"].unique())

        # Loopzero anchor row
        rows.append({
            "panel_id": panel_id, "panel_domain": domain, "panel_horizon": horizon,
            "method": "loopzero", "comparator_family": "loopzero",
            "loopzero_boundary_fp": loop_boundary["loopzero_boundary_fp"],
            "loopzero_boundary_q": loop_boundary["loopzero_boundary_q"],
            "loopzero_boundary_k": loop_boundary["loopzero_boundary_k"],
            "tpr_at_boundary_fp": loop_boundary["loopzero_boundary_tpr"],
            "status": "loopzero_envelope_boundary",
            "lower_fp": np.nan, "lower_tpr": np.nan,
            "upper_fp": np.nan, "upper_tpr": np.nan,
            "n_breakpoints": np.nan,
        })

        for family in families_in_panel:
            fps, tprs = get_comparator_breakpoints(df_comp, family, domain, horizon)
            interp = linear_interpolate_with_breakpoints(
                loop_boundary["loopzero_boundary_fp"], fps, tprs
            )
            status = interp["status"]
            if status == "below_min_fp":
                status = "no_overlap_comparator_above_loopzero_envelope"
            elif status == "above_max_fp":
                status = "no_overlap_comparator_below_loopzero_envelope"
            rows.append({
                "panel_id": panel_id, "panel_domain": domain, "panel_horizon": horizon,
                "method": "comparator", "comparator_family": family,
                "loopzero_boundary_fp": loop_boundary["loopzero_boundary_fp"],
                "loopzero_boundary_q": loop_boundary["loopzero_boundary_q"],
                "loopzero_boundary_k": loop_boundary["loopzero_boundary_k"],
                "tpr_at_boundary_fp": interp["interpolated_tpr"],
                "status": status,
                "lower_fp": interp["lower_fp"], "lower_tpr": interp["lower_tpr"],
                "upper_fp": interp["upper_fp"], "upper_tpr": interp["upper_tpr"],
                "n_breakpoints": interp["n_breakpoints"],
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def _fmt_pair(fp, tpr):
    if pd.isna(fp):
        return "—"
    return f"({fp:.4f}, {tpr:.4f})"


def render_table1_markdown(t1: pd.DataFrame) -> str:
    lines = ["# Table 1 — Comparator threshold-path at canonical FPR sweep",
             "",
             "Linear interpolation between adjacent (fp, tpr) breakpoints in the "
             "frozen calibration grid. Status legend: `interpolated` = target "
             "FPR within breakpoint range; `at_observed_fp` = target equals an "
             "observed breakpoint; `below_min_fp` = target below family's "
             "minimum achieved FP; `above_max_fp` = target above maximum. "
             "Breakpoints reported alongside for transparency.",
             ""]
    for (family, domain, horizon), sub in t1.groupby(
        ["family", "domain", "horizon"], dropna=False
    ):
        h_label = f"h={int(horizon)}" if pd.notna(horizon) else "no horizon"
        lines.append(f"## {family} | {domain} {h_label}")
        lines.append("")
        lines.append("| target FPR | TPR | status | lower (fp, tpr) | upper (fp, tpr) |")
        lines.append("|---|---|---|---|---|")
        for _, r in sub.sort_values("target_fpr").iterrows():
            tpr = f"{r['interpolated_tpr']:.4f}" if pd.notna(r["interpolated_tpr"]) else "—"
            lines.append(
                f"| {r['target_fpr']:.3f} | {tpr} | {r['status']} | "
                f"{_fmt_pair(r['lower_fp'], r['lower_tpr'])} | "
                f"{_fmt_pair(r['upper_fp'], r['upper_tpr'])} |"
            )
        lines.append("")
    return "\n".join(lines)


def render_table2_markdown(t2: pd.DataFrame) -> str:
    lines = ["# Table 2 — Envelope-boundary matched-FP comparison per panel",
             "",
             "Loopzero is reported at its envelope-boundary operating point per "
             "panel (maximum control_fp across the extended q-grid "
             "[50,60,70,75,80,85,90,95,99] at the canonical k=3). Comparator "
             "families are interpolated at the same FP where envelope overlap "
             "exists, or marked `no_overlap_*` otherwise. Status legend: "
             "`loopzero_envelope_boundary` = Loopzero's anchor at max FP; "
             "`interpolated` = comparator interpolated at Loopzero boundary FP; "
             "`no_overlap_comparator_above_loopzero_envelope` = comparator min "
             "FP exceeds Loopzero's boundary FP. Breakpoints reported alongside "
             "for transparency.",
             ""]
    for panel_id, sub in t2.groupby("panel_id", sort=False):
        lines.append(f"## Panel: {panel_id}")
        loop_row = sub[sub["method"] == "loopzero"].iloc[0]
        lines.append("")
        lines.append(
            f"Loopzero envelope boundary at k={int(loop_row['loopzero_boundary_k'])}: "
            f"FP={loop_row['loopzero_boundary_fp']:.6f} "
            f"(q={int(loop_row['loopzero_boundary_q'])}), "
            f"TPR={loop_row['tpr_at_boundary_fp']:.4f}"
        )
        lines.append("")
        lines.append("| family | TPR @ FP | status | lower (fp, tpr) | upper (fp, tpr) |")
        lines.append("|---|---|---|---|---|")
        for _, r in sub.iterrows():
            tpr = f"{r['tpr_at_boundary_fp']:.4f}" if pd.notna(r["tpr_at_boundary_fp"]) else "—"
            lines.append(
                f"| {r['comparator_family']} | {tpr} | {r['status']} | "
                f"{_fmt_pair(r['lower_fp'], r['lower_tpr'])} | "
                f"{_fmt_pair(r['upper_fp'], r['upper_tpr'])} |"
            )
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------
def self_check(t1: pd.DataFrame, t2: pd.DataFrame) -> None:
    assert len(t1) == len(BRACKETED_CELLS) * len(FPR_SWEEP_TARGETS), (
        f"Table 1 row count: expected "
        f"{len(BRACKETED_CELLS) * len(FPR_SWEEP_TARGETS)}, got {len(t1)}"
    )
    for horizon in (40, 60):
        ve = t1[(t1["family"] == "variance_ews") & (t1["horizon"] == horizon)]
        bracketed = (ve["status"].isin(["interpolated", "at_observed_fp"])).sum()
        assert bracketed == 5, (
            f"variance_ews h={horizon}: expected 5 bracketed FPRs, got {bracketed}"
        )
    mp40_low = t1[(t1["family"] == "matrix_profile")
                  & (t1["horizon"] == 40)
                  & (t1["target_fpr"] == 0.01)].iloc[0]
    assert mp40_low["status"] == "below_min_fp", (
        f"matrix_profile h=40 FPR=0.01: expected below_min_fp, got {mp40_low['status']}"
    )

    expected_panels = ["markets", "recsys_h40", "recsys_h50", "recsys_h60"]
    panel_ids = sorted(t2["panel_id"].unique().tolist())
    assert sorted(panel_ids) == sorted(expected_panels), (
        f"Table 2 panels: expected {expected_panels}, got {panel_ids}"
    )
    for panel_id in expected_panels:
        n_loop_rows = ((t2["panel_id"] == panel_id) & (t2["method"] == "loopzero")).sum()
        assert n_loop_rows == 1, (
            f"Panel {panel_id}: expected 1 loopzero anchor row, got {n_loop_rows}"
        )

    print("Self-check: OK")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading inputs...")
    df_comp = load_comparator_data()
    df_loop = load_loopzero_at_k(PRIMARY_K)
    print(f"  comparator points (collapsed): {len(df_comp)} rows")
    print(f"  loopzero at k={PRIMARY_K}: {len(df_loop)} rows across "
          f"{df_loop['benchmark'].nunique()} benchmarks")
    print()
    print("Computing Table 1 (comparator threshold-path at FPR sweep)...")
    t1 = compute_table1(df_comp)
    print(f"  Table 1: {len(t1)} rows")
    print()
    print("Computing Table 2 (envelope-boundary matched-FP comparison)...")
    t2 = compute_table2(df_loop, df_comp)
    print(f"  Table 2: {len(t2)} rows")
    print()
    print("Self-check...")
    self_check(t1, t2)
    print()
    print("Writing outputs...")
    t1.to_csv(OUT_TABLE1_CSV, index=False)
    OUT_TABLE1_MD.write_text(render_table1_markdown(t1))
    t2.to_csv(OUT_TABLE2_CSV, index=False)
    OUT_TABLE2_MD.write_text(render_table2_markdown(t2))
    print(f"  {OUT_TABLE1_CSV}")
    print(f"  {OUT_TABLE1_MD}")
    print(f"  {OUT_TABLE2_CSV}")
    print(f"  {OUT_TABLE2_MD}")
    print()
    print("=== Table 1 preview ===")
    print(t1.to_string(index=False))
    print()
    print("=== Table 2 preview ===")
    print(t2.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
