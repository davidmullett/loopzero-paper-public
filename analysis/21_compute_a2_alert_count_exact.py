#!/usr/bin/env python3
"""
analysis/21_compute_a2_alert_count_exact.py

A2 — Alert-count exact-matching sensitivity check (Path A+C v2, Option A).

Companion to analysis/20_compute_a2_threshold_path.py. Re-frames the
envelope-boundary comparison in integer alarm counts rather than rates.
Addresses two concerns from Day 3:

1. Discrete-FP-space coincidence on markets (Loopzero ≡ ac1_ews at
   FP=9/38) — by reporting in alarm counts, the coincidence becomes
   "both methods alarm on exactly 9 controls and detect 3 events"
   rather than a hidden artifact of discrete rate quantization.

2. Linear-interpolation dependency on recsys (variance_ews TPR
   estimates come from a linear fit between (FP=0, TPR=0) and
   (FP≈0.54, TPR=1.0)) — by reporting in alarm counts, the
   interpolation gap becomes "comparator has no calibration config
   between 0 alarms and ~3559 alarms; Loopzero sits at 97" rather
   than a hidden interpolative dependency.

Reads:
  results/rendered/a4_roc_lowfp/a4_roc_data.parquet
  results/rendered/bridge/a1_loopzero_operating_points.csv
  results/rendered/bridge/a1_loopzero_operating_points_h40_h60.csv

Writes:
  results/calibrated/a2_alert_count_exact_results.{csv,md}

Methodology:
- Loopzero envelope-boundary point: alarm counts read directly from
  n_control_alarmed / n_event_alarmed columns in the operating-point CSV.
- Comparator alarm counts: derived as round(fp_comp * panel.n_control_units)
  and round(tpr_comp * panel.n_event_units). Because the underlying
  fp/tpr values were originally integer ratios, rounding recovers
  exact alarm counts.
- Match status: exact_match | bounded_gap | no_overlap_above |
  no_overlap_below | insufficient_data.
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
OUT_CSV = OUT_DIR / "a2_alert_count_exact_results.csv"
OUT_MD = OUT_DIR / "a2_alert_count_exact_results.md"

PANELS = [
    ("markets", "markets", None),
    ("recsys_h40", "recsys", 40),
    ("recsys_h50", "recsys", 50),
    ("recsys_h60", "recsys", 60),
]

PRIMARY_K = 3


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
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
        "n_control_alarmed": int(boundary["n_control_alarmed"]),
        "n_event_alarmed": int(boundary["n_event_alarmed"]),
        "n_control_units": int(boundary["n_control_units"]),
        "n_event_units": int(boundary["n_event_units"]),
        "control_fp": float(boundary["control_fp"]),
        "event_alarm_rate": float(boundary["event_alarm_rate"]),
        "q_G_pct": float(boundary["q_G_pct"]),
        "k": int(boundary["k"]),
    }


def load_comparator_data() -> pd.DataFrame:
    df = pd.read_parquet(A4_PARQUET)
    df = df[df["source_type"] == "curve_point"].copy()
    df = (
        df.groupby(["family", "domain", "horizon", "fp"], dropna=False)["tpr"]
        .max()
        .reset_index()
    )
    return df


def get_comparator_breakpoints_with_counts(
    df_comp: pd.DataFrame,
    family: str,
    domain: str,
    horizon: Optional[float],
    n_control_units: int,
    n_event_units: int,
) -> pd.DataFrame:
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
    sub = df_comp[mask].sort_values("fp").reset_index(drop=True)
    sub["n_control_alarmed"] = np.round(sub["fp"] * n_control_units).astype(int)
    sub["n_event_alarmed"] = np.round(sub["tpr"] * n_event_units).astype(int)
    return sub


# ---------------------------------------------------------------------------
# Match classification
# ---------------------------------------------------------------------------
def determine_alarm_count_match(
    loop_n_control: int,
    comp_breakpoints: pd.DataFrame,
) -> dict:
    base = {
        "status": "insufficient_data",
        "comp_lower_n_control": np.nan,
        "comp_lower_n_event": np.nan,
        "comp_upper_n_control": np.nan,
        "comp_upper_n_event": np.nan,
        "gap_width_n_control": np.nan,
        "n_comparator_breakpoints": len(comp_breakpoints),
        "exact_match_n_event": np.nan,
    }
    n = len(comp_breakpoints)
    if n < 1:
        return base

    counts = comp_breakpoints["n_control_alarmed"].to_numpy()
    events = comp_breakpoints["n_event_alarmed"].to_numpy()

    matches = comp_breakpoints[comp_breakpoints["n_control_alarmed"] == loop_n_control]
    if not matches.empty:
        best = matches.loc[matches["n_event_alarmed"].idxmax()]
        return {
            **base,
            "status": "exact_match",
            "comp_lower_n_control": int(best["n_control_alarmed"]),
            "comp_lower_n_event": int(best["n_event_alarmed"]),
            "comp_upper_n_control": int(best["n_control_alarmed"]),
            "comp_upper_n_event": int(best["n_event_alarmed"]),
            "gap_width_n_control": 0,
            "exact_match_n_event": int(best["n_event_alarmed"]),
        }

    if n < 2:
        only = comp_breakpoints.iloc[0]
        if only["n_control_alarmed"] > loop_n_control:
            return {
                **base,
                "status": "no_overlap_above",
                "comp_upper_n_control": int(only["n_control_alarmed"]),
                "comp_upper_n_event": int(only["n_event_alarmed"]),
            }
        else:
            return {
                **base,
                "status": "no_overlap_below",
                "comp_lower_n_control": int(only["n_control_alarmed"]),
                "comp_lower_n_event": int(only["n_event_alarmed"]),
            }

    if loop_n_control < counts.min():
        return {
            **base,
            "status": "no_overlap_above",
            "comp_upper_n_control": int(counts.min()),
            "comp_upper_n_event": int(events[counts.argmin()]),
        }
    if loop_n_control > counts.max():
        return {
            **base,
            "status": "no_overlap_below",
            "comp_lower_n_control": int(counts.max()),
            "comp_lower_n_event": int(events[counts.argmax()]),
        }

    sorted_idx = np.argsort(counts)
    sorted_counts = counts[sorted_idx]
    sorted_events = events[sorted_idx]
    for i in range(len(sorted_counts) - 1):
        if sorted_counts[i] <= loop_n_control <= sorted_counts[i + 1]:
            return {
                **base,
                "status": "bounded_gap",
                "comp_lower_n_control": int(sorted_counts[i]),
                "comp_lower_n_event": int(sorted_events[i]),
                "comp_upper_n_control": int(sorted_counts[i + 1]),
                "comp_upper_n_event": int(sorted_events[i + 1]),
                "gap_width_n_control": int(sorted_counts[i + 1] - sorted_counts[i]),
            }
    return base


# ---------------------------------------------------------------------------
# Build table
# ---------------------------------------------------------------------------
def compute_alert_count_table(df_loop: pd.DataFrame, df_comp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for panel_id, domain, horizon in PANELS:
        loop = get_loopzero_envelope_boundary(df_loop, domain, horizon)
        loop_meta = {
            "panel_id": panel_id,
            "panel_domain": domain,
            "panel_horizon": horizon,
            "panel_n_control_units": loop["n_control_units"],
            "panel_n_event_units": loop["n_event_units"],
            "loop_n_control_alarmed": loop["n_control_alarmed"],
            "loop_n_event_alarmed": loop["n_event_alarmed"],
            "loop_control_fp": loop["control_fp"],
            "loop_event_alarm_rate": loop["event_alarm_rate"],
            "loop_q_G_pct": loop["q_G_pct"],
            "loop_k": loop["k"],
        }
        # Loopzero anchor
        rows.append({
            **loop_meta,
            "method": "loopzero",
            "comparator_family": "loopzero",
            "status": "loopzero_envelope_boundary",
            "comp_lower_n_control": np.nan,
            "comp_lower_n_event": np.nan,
            "comp_upper_n_control": np.nan,
            "comp_upper_n_event": np.nan,
            "gap_width_n_control": np.nan,
            "n_comparator_breakpoints": np.nan,
            "exact_match_n_event": np.nan,
        })

        if horizon is None:
            comp_mask = (df_comp["domain"] == domain) & (df_comp["horizon"].isna())
        else:
            comp_mask = (df_comp["domain"] == domain) & (df_comp["horizon"] == horizon)
        families = sorted(df_comp[comp_mask]["family"].unique())

        for family in families:
            comp_bps = get_comparator_breakpoints_with_counts(
                df_comp, family, domain, horizon,
                loop["n_control_units"], loop["n_event_units"],
            )
            match = determine_alarm_count_match(loop["n_control_alarmed"], comp_bps)
            rows.append({
                **loop_meta,
                "method": "comparator",
                "comparator_family": family,
                **match,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------
def render_markdown(df: pd.DataFrame) -> str:
    lines = [
        "# A2 — Alert-count exact-matching sensitivity check",
        "",
        "Companion to `a2_threshold_path_envelope_boundary.{csv,md}`. Re-frames "
        "the envelope-boundary comparison in integer alarm counts to surface "
        "(a) discrete-FP-space coincidences as exact alarm-count matches, and "
        "(b) linear-interpolation gaps as quantitative gap widths in alarm-count "
        "space.",
        "",
        "Comparator alarm counts derived from `round(fp_comp * panel.n_control_units)` "
        "and `round(tpr_comp * panel.n_event_units)`. Status legend:",
        "",
        "- `loopzero_envelope_boundary` — Loopzero's anchor at panel max FP, k=3",
        "- `exact_match` — comparator has a breakpoint at exactly Loopzero's alarm count",
        "- `bounded_gap` — Loopzero's alarm count falls strictly between two adjacent "
        "comparator breakpoints; `gap_width_n_control` records the gap size",
        "- `no_overlap_above` — all comparator breakpoints have higher alarm counts",
        "- `no_overlap_below` — all comparator breakpoints have lower alarm counts",
        "- `insufficient_data` — comparator has <1 useful breakpoint",
        "",
    ]
    for panel_id, sub in df.groupby("panel_id", sort=False):
        lines.append(f"## Panel: {panel_id}")
        lines.append("")
        loop_row = sub[sub["method"] == "loopzero"].iloc[0]
        lines.append(
            f"Panel n_control_units={int(loop_row['panel_n_control_units'])}, "
            f"n_event_units={int(loop_row['panel_n_event_units'])}. "
            f"Loopzero at envelope boundary (q={int(loop_row['loop_q_G_pct'])}, "
            f"k={int(loop_row['loop_k'])}): "
            f"**{int(loop_row['loop_n_control_alarmed'])} false alarms / "
            f"{int(loop_row['panel_n_control_units'])} controls** "
            f"(FP={loop_row['loop_control_fp']:.6f}), "
            f"**{int(loop_row['loop_n_event_alarmed'])} true detections / "
            f"{int(loop_row['panel_n_event_units'])} events** "
            f"(TPR={loop_row['loop_event_alarm_rate']:.4f})."
        )
        lines.append("")
        lines.append(
            "| family | status | comp_lower (n_control, n_event) | "
            "comp_upper (n_control, n_event) | gap_width_n_control | n_breakpoints |"
        )
        lines.append("|---|---|---|---|---|---|")
        for _, r in sub.iterrows():
            if r["method"] == "loopzero":
                continue
            lower = (
                f"({int(r['comp_lower_n_control'])}, {int(r['comp_lower_n_event'])})"
                if pd.notna(r["comp_lower_n_control"]) else "—"
            )
            upper = (
                f"({int(r['comp_upper_n_control'])}, {int(r['comp_upper_n_event'])})"
                if pd.notna(r["comp_upper_n_control"]) else "—"
            )
            gap = (
                f"{int(r['gap_width_n_control'])}"
                if pd.notna(r["gap_width_n_control"]) else "—"
            )
            nbp = (
                f"{int(r['n_comparator_breakpoints'])}"
                if pd.notna(r["n_comparator_breakpoints"]) else "—"
            )
            lines.append(
                f"| {r['comparator_family']} | {r['status']} | {lower} | {upper} | "
                f"{gap} | {nbp} |"
            )
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------
def self_check(df: pd.DataFrame) -> None:
    m_ac1 = df[(df["panel_id"] == "markets") & (df["comparator_family"] == "ac1_ews")]
    assert not m_ac1.empty, "markets ac1_ews missing"
    row = m_ac1.iloc[0]
    assert row["status"] == "exact_match", (
        f"markets ac1_ews: expected exact_match, got {row['status']}"
    )
    assert int(row["loop_n_control_alarmed"]) == 9, (
        f"markets Loopzero n_control_alarmed: expected 9, got "
        f"{row['loop_n_control_alarmed']}"
    )
    assert int(row["loop_n_event_alarmed"]) == 3, (
        f"markets Loopzero n_event_alarmed: expected 3, got "
        f"{row['loop_n_event_alarmed']}"
    )
    assert int(row["exact_match_n_event"]) == 3, (
        f"ac1_ews exact_match_n_event: expected 3, got {row['exact_match_n_event']}"
    )

    for fam in ("cusum", "page_hinkley", "variance_ews"):
        sub = df[(df["panel_id"] == "markets") & (df["comparator_family"] == fam)]
        if sub.empty:
            continue
        assert sub.iloc[0]["status"] == "no_overlap_above", (
            f"markets {fam}: expected no_overlap_above, got {sub.iloc[0]['status']}"
        )

    rec40_ve = df[
        (df["panel_id"] == "recsys_h40") & (df["comparator_family"] == "variance_ews")
    ].iloc[0]
    assert rec40_ve["status"] == "bounded_gap", (
        f"recsys h40 variance_ews: expected bounded_gap, got {rec40_ve['status']}"
    )
    assert rec40_ve["gap_width_n_control"] > 100, (
        f"recsys h40 variance_ews: expected gap_width > 100, got "
        f"{rec40_ve['gap_width_n_control']}"
    )

    print("Self-check: OK")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading inputs...")
    df_loop = load_loopzero_at_k(PRIMARY_K)
    df_comp = load_comparator_data()
    print(f"  loopzero at k={PRIMARY_K}: {len(df_loop)} rows")
    print(f"  comparator points (collapsed): {len(df_comp)} rows")
    print()
    print("Computing alert-count table...")
    df = compute_alert_count_table(df_loop, df_comp)
    print(f"  Table: {len(df)} rows")
    print()
    print("Self-check...")
    self_check(df)
    print()
    print("Writing outputs...")
    df.to_csv(OUT_CSV, index=False)
    OUT_MD.write_text(render_markdown(df))
    print(f"  {OUT_CSV}")
    print(f"  {OUT_MD}")
    print()
    print("=== Output preview ===")
    print(df[[
        "panel_id", "method", "comparator_family",
        "loop_n_control_alarmed", "loop_n_event_alarmed",
        "status", "comp_lower_n_control", "comp_lower_n_event",
        "comp_upper_n_control", "comp_upper_n_event",
        "gap_width_n_control",
    ]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
