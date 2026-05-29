#!/usr/bin/env python3
"""
analysis/16_render_a3_effect_size_forest.py

Effect-size forest plot for A3 deliverable.

Reads:  results/rendered/effect_sizes/a3_effect_sizes_full.csv
Writes: results/figures/a3_effect_size_forest.{png,pdf}

Design vocabulary inherited from make_fig1_iconic_v13 (iconic claim ladder):
matplotlib hand-coded composition, explicit positioning at figure-fraction
coordinates, muted-academic palette, 300 dpi PNG + vector PDF.

Layout: single-panel forest plot, 12 rows = 4 benchmarks/horizons x 3 witnesses.
Each row shows Cohen's d point estimate (filled circle) with two overlaid
intervals: 95% BCa CI in front (full color) and 95% percentile CI behind
it (faint), so the BCa correction is visible as the shift between bars.

Canonical recsys h=50 group is anchored with subtle background tint and
bold benchmark label. Color coding: blue=canonical, green=predicted dir
with CI clear of 0, red=wrong dir with CI clear of 0, gray=CI spans 0.

Glass's d and Rank AUC are reported in Supplementary Table S2, not shown.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import numpy as np
import pandas as pd


# ============================================================================
# Palette (inherited from make_fig1_iconic_v13)
# ============================================================================
BLUE = "#3B5C8C"
GREEN = "#4F7B5C"
RED = "#C04C3F"
CANONICAL_BG = "#F0F4FA"

TEXT_DARK = "#1A1A1A"
TEXT_MID = "#444444"
TEXT_LIGHT = "#777777"


# ============================================================================
# Paths
# ============================================================================
REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "results" / "rendered" / "effect_sizes" / "a3_effect_sizes_full.csv"
OUT_DIR = REPO_ROOT / "results" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PNG = OUT_DIR / "a3_effect_size_forest.png"
OUT_PDF = OUT_DIR / "a3_effect_size_forest.pdf"


# ============================================================================
# Data ordering and labels
# ============================================================================
BENCH_ORDER = [
    "volmageddon_covid_public_v2",
    "movielens25m_recursive_frontier_public_v1__horizon_40",
    "movielens25m_recursive_frontier_public_v1__canonical_h50",
    "movielens25m_recursive_frontier_public_v1__horizon_60",
]
BENCH_LABEL = {
    "volmageddon_covid_public_v2": "Markets",
    "movielens25m_recursive_frontier_public_v1__horizon_40": "Recsys h=40",
    "movielens25m_recursive_frontier_public_v1__canonical_h50": "Recsys h=50\n(canonical)",
    "movielens25m_recursive_frontier_public_v1__horizon_60": "Recsys h=60",
}
CANONICAL_BENCH = "movielens25m_recursive_frontier_public_v1__canonical_h50"

WITNESS_ORDER = ["G", "p", "delta"]
WITNESS_LABEL = {"G": "G", "p": "p", "delta": "\u03b4"}
PREDICTED_SIGN = {"G": +1, "p": +1, "delta": -1}


def classify(row):
    """Color category: canonical / predicted / wrong / null."""
    if row.benchmark_id == CANONICAL_BENCH:
        return "canonical"
    lo, hi = row.ci_lower_bca, row.ci_upper_bca
    if lo <= 0 <= hi:
        return "null"
    expected = PREDICTED_SIGN[row.witness]
    if (row.point_estimate > 0 and expected > 0) or (row.point_estimate < 0 and expected < 0):
        return "predicted"
    return "wrong"


COLOR = {"canonical": BLUE, "predicted": GREEN, "wrong": RED, "null": TEXT_LIGHT}


# ============================================================================
# Load and filter to Cohen's d
# ============================================================================
df = pd.read_csv(CSV_PATH)
df = df[df.effect_measure == "cohens_d"].copy()


# ============================================================================
# Compute row y-positions
# ============================================================================
ROW_SPACING = 1.0
GROUP_GAP = 0.6

y_positions = []   # (bench, witness, y)
y = 0.0
for b_idx, bench in enumerate(BENCH_ORDER):
    if b_idx > 0:
        y -= GROUP_GAP
    for witness in WITNESS_ORDER:
        y_positions.append((bench, witness, y))
        y -= ROW_SPACING

y_data = [yv for (_, _, yv) in y_positions]
y_top = max(y_data) + 0.6
y_bot = min(y_data) - 0.6


# ============================================================================
# Figure composition
# ============================================================================
fig = plt.figure(figsize=(10.0, 7.5), dpi=300)
ax = fig.add_axes([0.32, 0.18, 0.60, 0.70])

# Canonical group background tint
canon_ys = [yv for (b, w, yv) in y_positions if b == CANONICAL_BENCH]
ax.axhspan(min(canon_ys) - 0.5, max(canon_ys) + 0.5, color=CANONICAL_BG, zorder=0)

# Zero reference line
ax.axvline(0, color=TEXT_MID, linewidth=0.8, zorder=2)

# Draw 12 rows
for (bench, witness, y_row) in y_positions:
    row = df[(df.benchmark_id == bench) & (df.witness == witness)].iloc[0]
    color = COLOR[classify(row)]

    # Percentile CI: fainter background bar
    ax.plot(
        [row.ci_lower_percentile, row.ci_upper_percentile],
        [y_row, y_row],
        color=color, alpha=0.18, linewidth=6.0, solid_capstyle="butt", zorder=3,
    )
    # BCa CI: foreground bar
    ax.plot(
        [row.ci_lower_bca, row.ci_upper_bca],
        [y_row, y_row],
        color=color, linewidth=2.5, solid_capstyle="butt", zorder=4,
    )
    # Point estimate
    ax.scatter(
        [row.point_estimate], [y_row],
        color=color, s=50, zorder=5, edgecolor="white", linewidth=0.8,
    )

    # Witness label
    ax.text(
        -0.02, y_row, WITNESS_LABEL[witness],
        ha="right", va="center", color=TEXT_DARK, fontsize=12, fontweight="semibold",
        transform=ax.get_yaxis_transform(),
    )

# Benchmark group labels (further left, vertically centered on each group)
for bench in BENCH_ORDER:
    group_ys = [yv for (b, w, yv) in y_positions if b == bench]
    label_y = (max(group_ys) + min(group_ys)) / 2
    is_canon = bench == CANONICAL_BENCH
    ax.text(
        -0.30, label_y, BENCH_LABEL[bench],
        ha="left", va="center",
        color=BLUE if is_canon else TEXT_DARK,
        fontsize=10, fontweight="bold" if is_canon else "normal",
        transform=ax.get_yaxis_transform(),
    )

# Axes formatting
ax.set_xlim(-0.7, 0.7)
ax.set_ylim(y_bot, y_top)
ax.set_xticks(np.arange(-0.6, 0.7, 0.2))
ax.set_yticks([])
ax.set_xlabel("Cohen's d", fontsize=10, color=TEXT_DARK, labelpad=14)
ax.tick_params(axis="x", labelsize=9, colors=TEXT_DARK, length=4)
for side in ["top", "right", "left"]:
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(TEXT_MID)

# Title + subtitle
fig.text(
    0.50, 0.945,
    "Effect sizes across witnesses, benchmarks, and recsys horizons",
    ha="center", va="center", fontsize=13, fontweight="bold", color=TEXT_DARK,
)
fig.text(
    0.50, 0.915,
    "Cohen's d, 95% BCa CI (front) and percentile CI (back, faint)",
    ha="center", va="center", fontsize=9.5, color=TEXT_MID,
)

# Footer note
fig.text(
    0.50, 0.030,
    "Predicted direction:  G > 0 (amplification),  p > 0 (concentration),  \u03b4 < 0 (contraction)",
    ha="center", va="center", fontsize=8.5, color=TEXT_MID,
)

# Color-category legend
legend_handles = [
    Line2D([], [], color=BLUE, marker="o", linestyle="-", linewidth=2.5,
           markersize=7, markeredgecolor="white", markeredgewidth=0.5,
           label="Canonical (h=50)"),
    Line2D([], [], color=GREEN, marker="o", linestyle="-", linewidth=2.5,
           markersize=7, markeredgecolor="white", markeredgewidth=0.5,
           label="Predicted direction"),
    Line2D([], [], color=RED, marker="o", linestyle="-", linewidth=2.5,
           markersize=7, markeredgecolor="white", markeredgewidth=0.5,
           label="Wrong direction"),
    Line2D([], [], color=TEXT_LIGHT, marker="o", linestyle="-", linewidth=2.5,
           markersize=7, markeredgecolor="white", markeredgewidth=0.5,
           label="CI spans 0"),
]
ax.legend(
    handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.10),
    ncol=4, frameon=False, fontsize=8.5, handlelength=2.0, columnspacing=2.0,
)

# Output
fig.savefig(OUT_PNG, dpi=300, facecolor="white", bbox_inches=None)
fig.savefig(OUT_PDF, facecolor="white", bbox_inches=None)
print(f"PNG: {OUT_PNG}")
print(f"PDF: {OUT_PDF}")
