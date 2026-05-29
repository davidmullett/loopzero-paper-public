#!/usr/bin/env python3
"""
analysis/19_render_a4_roc_lowfp.py

A4 ROC + low-FP zoom figure renderer (v0, Day 2 morning).

Layout: two side-by-side panels (markets left, recsys right) sharing TPR axis.
Recsys panel has a corner inset for [0.0, 0.10] low-FP zoom.

Encoding:
- Family identity -> color (colorblind-safe palette, inherited from v13/a3)
- Recsys horizon -> line style (h=40 long-dashed, h=60 short-dashed,
  h=50 canonical -> star markers)
- Markets -> solid line per family (no horizon distinction; benchmark single)
- Acceptance band [0.03, 0.07] -> soft sand vertical fill on both panels + inset
- Loopzero pre-registered operating points -> large filled gold stars at FP=0.0

Outputs:
  results/figures/a4_roc_lowfp_main.{png,pdf}
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "results/rendered/a4_roc_lowfp/a4_roc_data.parquet"
# Loopzero canonical operating points (split across two files: markets+h50, h40+h60)
LOOPZERO_OPS_FILES = [
    REPO_ROOT / "results/rendered/bridge/a1_loopzero_operating_points.csv",
    REPO_ROOT / "results/rendered/bridge/a1_loopzero_operating_points_h40_h60.csv",
]

OUT_DIR = REPO_ROOT / "results/figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PNG = OUT_DIR / "a4_roc_lowfp_main.png"
OUT_PDF = OUT_DIR / "a4_roc_lowfp_main.pdf"


# ============================================================================
# Design vocabulary -- matches v13 iconic claim ladder + a3 forest plot
# ============================================================================
PALETTE = {
    "variance_ews":        "#3B5C8C",  # deep blue
    "cusum":               "#4F7B5C",  # forest green
    "page_hinkley":        "#B66B30",  # warm orange
    "ac1_ews":             "#C04C3F",  # red (markets only)
    "ac1":                 "#8B2418",  # deepened red (recsys sibling; L* gap widened post-review B2)
    "matrix_profile":      "#7A5C9C",  # muted purple
    "permutation_entropy": "#8C7D3B",  # olive
}

FAMILY_DISPLAY = {
    "variance_ews":        "Variance EWS",
    "cusum":               "CUSUM",
    "page_hinkley":        "Page-Hinkley",
    "ac1_ews":             "AC1-EWS (markets)",
    "ac1":                 "AC1 (recsys)",
    "matrix_profile":      "Matrix Profile (recsys)",
    "permutation_entropy": "Permutation Entropy (recsys)",
}

TEXT_DARK   = "#1A1A1A"
TEXT_MID    = "#444444"
TEXT_LIGHT  = "#777777"

BAND_FILL   = "#EFE9D6"   # soft sand
BAND_EDGE   = "#D8C99C"

LOOPZERO_GOLD = "#C9A227"

HORIZON_STYLE = {
    40: {"linestyle": (0, (5, 2)),   "linewidth": 1.5, "alpha": 0.85},  # long dash
    60: {"linestyle": (0, (1.5, 2)), "linewidth": 1.5, "alpha": 0.85},  # short dash
}

ACCEPTANCE_BAND = (0.03, 0.07)


# ============================================================================
# Data loading
# ============================================================================
def load_data():
    df = pd.read_parquet(DATA_PATH)
    return df.sort_values(["domain", "horizon", "family", "fp"]).reset_index(drop=True)


def load_loopzero_ops():
    """Load Loopzero pre-registered operating points (primary=True canonical config).

    Schema: combined CSV has columns [method, domain, benchmark, config, q_*, k,
    control_fp, event_alarm_rate, accepted, primary, ...]. Canonical pre-registered
    config is q=95, k=3 across all (domain, horizon) combinations, marked primary=True.

    Returns DataFrame with normalized columns: [domain, horizon, config, fp, tpr].
    Horizon parsed from benchmark string for recsys; None for markets.
    """
    parts = []
    for path in LOOPZERO_OPS_FILES:
        if not path.exists():
            print(f"WARNING: missing Loopzero ops file {path}")
            continue
        parts.append(pd.read_csv(path))
    if not parts:
        print("No Loopzero operating point files found; stars will be omitted.")
        return None

    df = pd.concat(parts, ignore_index=True)
    df_primary = df[df["primary"] == True].copy()

    if len(df_primary) == 0:
        print("WARNING: no primary=True Loopzero operating points found.")
        return None

    def parse_horizon(row):
        if row["domain"] == "markets":
            return None
        bm = str(row["benchmark"])
        if "__horizon_40" in bm:
            return 40
        if "__horizon_60" in bm:
            return 60
        if "__canonical_h50" in bm:
            return 50
        return None

    df_primary["horizon"] = df_primary.apply(parse_horizon, axis=1)
    df_primary = df_primary.rename(columns={"control_fp": "fp", "event_alarm_rate": "tpr"})

    print(f"Loaded {len(df_primary)} Loopzero primary operating points:")
    for _, row in df_primary.iterrows():
        hz_str = f"h={int(row.horizon)}" if pd.notna(row["horizon"]) else "(no horizon)"
        print(f"  {row['domain']:8} {hz_str:8}: fp={row['fp']:.4f}, tpr={row['tpr']:.4f}, config={row['config']}")

    return df_primary[["domain", "horizon", "config", "fp", "tpr"]]


# ============================================================================
# Plotting primitives
# ============================================================================
def style_axis(ax, *, title="", xlim=(0, 1), ylim=(0, 1.02),
               show_xlabel=True, show_ylabel=True):
    ax.set_facecolor("white")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.tick_params(axis="both", colors=TEXT_MID, labelsize=8.5,
                   length=3, width=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_linewidth(0.7)
        ax.spines[s].set_color(TEXT_MID)
    if show_xlabel:
        ax.set_xlabel("False-positive rate (FP)", fontsize=9.5,
                      color=TEXT_DARK, labelpad=6)
    if show_ylabel:
        ax.set_ylabel("True-positive rate (TPR)", fontsize=9.5,
                      color=TEXT_DARK, labelpad=6)
    if title:
        ax.set_title(title, fontsize=10, color=TEXT_DARK,
                     pad=8, loc="left", fontweight="semibold")


def draw_acceptance_band(ax):
    ax.axvspan(*ACCEPTANCE_BAND, color=BAND_FILL, alpha=0.5,
               zorder=0, linewidth=0)
    for x in ACCEPTANCE_BAND:
        ax.axvline(x, color=BAND_EDGE, linewidth=0.6, alpha=0.6, zorder=0.5)


def draw_diagonal(ax):
    ax.plot([0, 1], [0, 1], color=TEXT_LIGHT, linewidth=0.4,
            linestyle="-", alpha=0.3, zorder=0.3)


def _aggregate_roc(sub):
    """Collapse (fp) duplicates to max(tpr).

    Multiple comparator configs often resolve to the same achievable FP
    (especially slow families with small n_control_units that quantize
    achievable FPs to {0, 1/n, 2/n, ...}). For ROC plotting we want the
    best TPR achieved at each FP, not every config individually.
    """
    if len(sub) == 0:
        return sub
    agg = sub.groupby("fp", as_index=False).agg(tpr=("tpr", "max"))
    return agg.sort_values("fp")


def plot_markets_curves(ax, df):
    markets = df[df.domain == "markets"]
    for family in sorted(markets.family.unique()):
        sub = markets[markets.family == family]
        agg = _aggregate_roc(sub)
        if len(agg) < 1:
            continue
        color = PALETTE.get(family, "#666666")
        if len(agg) >= 2:
            ax.plot(agg.fp, agg.tpr, color=color, linewidth=1.8, alpha=0.95,
                    solid_capstyle="round", zorder=2)
        # Anchor dots at every operating point (also handles single-point families)
        ax.scatter(agg.fp, agg.tpr, color=color, s=14, zorder=2.2,
                   edgecolor="white", linewidth=0.4)


def plot_recsys_curves_and_markers(ax, df, *, plot_markers=True):
    recsys = df[df.domain == "recsys"]
    for family in sorted(recsys.family.unique()):
        color = PALETTE.get(family, "#666666")
        # h=40, h=60 curves (aggregated: max TPR per achievable FP)
        for horizon in (40, 60):
            sub = recsys[(recsys.family == family)
                         & (recsys.horizon == horizon)
                         & (recsys.source_type == "curve_point")]
            agg = _aggregate_roc(sub)
            if len(agg) >= 2:
                ax.plot(agg.fp, agg.tpr, color=color,
                        **HORIZON_STYLE[horizon], zorder=2)
            if len(agg) >= 1:
                # Faint dots at each achievable FP show where the steps land
                ax.scatter(agg.fp, agg.tpr, color=color, s=9,
                           edgecolor="none",
                           alpha=HORIZON_STYLE[horizon]["alpha"],
                           zorder=2.5)
        # h=50 canonical star markers (nearest only; nearest_nontrivial often duplicates)
        if plot_markers:
            ms = recsys[(recsys.family == family)
                        & (recsys.horizon == 50)
                        & (recsys.source_type == "selected_marker")
                        & (recsys.marker_category == "nearest")]
            if len(ms):
                ax.scatter(ms.fp, ms.tpr, marker="*", s=180, color=color,
                           edgecolor="white", linewidth=0.9, zorder=4)


def plot_loopzero_stars(ax, loopzero_ops, *, domain):
    if loopzero_ops is None or len(loopzero_ops) == 0:
        return
    if "domain" in loopzero_ops.columns:
        sub = loopzero_ops[loopzero_ops.domain == domain]
    else:
        # If schema doesn't include domain, assume the file is recsys-only
        sub = loopzero_ops if domain == "recsys" else loopzero_ops.iloc[:0]
    if len(sub) == 0:
        return
    ax.scatter(sub.fp, sub.tpr, marker="*", s=340, color=LOOPZERO_GOLD,
               edgecolor=TEXT_DARK, linewidth=1.0, zorder=6)


# ============================================================================
# Figure assembly
# ============================================================================
def main():
    df = load_data()
    loopzero_ops = load_loopzero_ops()

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": False,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    })

    fig = plt.figure(figsize=(11.5, 5.4), dpi=300)

    # Manual axis placement (figure-fraction coords)
    ax_markets = fig.add_axes([0.065, 0.20, 0.36, 0.68])
    ax_recsys  = fig.add_axes([0.555, 0.20, 0.36, 0.68])

    # --- Markets panel ---
    draw_acceptance_band(ax_markets)
    draw_diagonal(ax_markets)
    plot_markets_curves(ax_markets, df)
    plot_loopzero_stars(ax_markets, loopzero_ops, domain="markets")
    style_axis(
        ax_markets,
        title="A. Markets — Volmageddon + COVID, late-30min window",
        show_xlabel=True, show_ylabel=True,
    )

    # --- Recsys panel ---
    draw_acceptance_band(ax_recsys)
    draw_diagonal(ax_recsys)
    plot_recsys_curves_and_markers(ax_recsys, df)
    plot_loopzero_stars(ax_recsys, loopzero_ops, domain="recsys")
    style_axis(
        ax_recsys,
        title="B. Recommender — MovieLens-25M, horizons h=40/50/60",
        show_xlabel=True, show_ylabel=False,
    )

    # --- Inset: low-FP zoom on recsys ---
    ax_inset = ax_recsys.inset_axes(
        bounds=[0.43, 0.05, 0.55, 0.50],  # (x0, y0, w, h) — enlarged post-review B3
        zorder=10,
    )
    draw_acceptance_band(ax_inset)
    plot_recsys_curves_and_markers(ax_inset, df, plot_markers=True)
    plot_loopzero_stars(ax_inset, loopzero_ops, domain="recsys")
    ax_inset.set_xlim(0.0, 0.10)
    ax_inset.set_ylim(0.0, 1.02)
    ax_inset.set_xticks([0.0, 0.03, 0.07, 0.10])
    ax_inset.set_yticks([0.0, 0.5, 1.0])
    ax_inset.tick_params(axis="both", colors=TEXT_MID, labelsize=7.5,
                          length=2.5, width=0.5)
    for s in ("top", "right"):
        ax_inset.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax_inset.spines[s].set_linewidth(0.6)
        ax_inset.spines[s].set_color(TEXT_MID)
    ax_inset.set_facecolor("white")

    # Zoom-region rectangle on main recsys axis (strengthened post-review B4)
    ax_recsys.indicate_inset_zoom(
        ax_inset, edgecolor=TEXT_MID, alpha=0.75, linewidth=0.9,
    )

    ax_inset.text(
        0.5, 1.04, "Low-FP zoom, FP ∈ [0.00, 0.10]",
        transform=ax_inset.transAxes, fontsize=8, color=TEXT_MID,
        ha="center", va="bottom",
    )

    # --- Composite legend below the figure ---
    families_in_data = sorted(set(df.family.unique()))
    family_handles = [
        Line2D([0], [0], color=PALETTE[f], linewidth=1.8,
               label=FAMILY_DISPLAY.get(f, f))
        for f in families_in_data
    ]
    horizon_handles = [
        Line2D([0], [0], color=TEXT_MID, linewidth=1.5,
               linestyle=HORIZON_STYLE[40]["linestyle"],
               label="h=40 (curve)"),
        Line2D([0], [0], color=TEXT_MID, linewidth=1.5,
               linestyle=HORIZON_STYLE[60]["linestyle"],
               label="h=60 (curve)"),
        Line2D([0], [0], marker="*", color="white",
               markerfacecolor=TEXT_MID, markeredgecolor="white",
               markersize=11, linewidth=0,
               label="h=50 canonical (★, colored by family)"),
    ]
    band_handle = mpatches.Patch(
        facecolor=BAND_FILL, edgecolor=BAND_EDGE, linewidth=0.6,
        label="Acceptance band [0.03, 0.07]",
    )
    loopzero_handle = Line2D(
        [0], [0], marker="*", color="white",
        markerfacecolor=LOOPZERO_GOLD, markeredgecolor=TEXT_DARK,
        markersize=14, linewidth=0,
        label="Loopzero pre-registered (★)",
    )

    fig.legend(
        handles=family_handles, loc="lower left",
        bbox_to_anchor=(0.065, -0.02), ncol=4,
        frameon=False, fontsize=8.5,
        handlelength=2.2, columnspacing=1.4, handletextpad=0.6,
    )
    fig.legend(
        handles=horizon_handles + [band_handle, loopzero_handle],
        loc="lower right",
        bbox_to_anchor=(0.93, -0.045), ncol=5,
        frameon=False, fontsize=8.5,
        handlelength=2.4, columnspacing=1.4, handletextpad=0.6,
    )

    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT_PDF, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
