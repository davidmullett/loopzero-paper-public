#!/usr/bin/env python3
"""Figure 3 - "Discrimination advantage at matched alarm budgets."

Composite minus best baseline (ΔTPR) at the four registered budgets, with
cluster-aware BCa 95% intervals, and the parity (ΔTPR = 0) and acceptance
(ΔTPR ≥ 0.05) lines marked. Every point is negative with its interval clear
of zero on the wrong side: the composite is strictly worse than the best
miss-based baseline at every budget. These are purified-instrument (Study 2)
values, so they take ink, not the contamination accent.

FROZEN INPUT (read-only; values are read, never recomputed):
    results/v2_controls/s2_exec2_phase4.json
        -> item2_tsplit_sensitivity["20"].delta_by_budget[b] = [value, lo, hi]

OUTPUT:
    assets/fig3_delta_tpr_by_budget.pdf   (vector, print width)
    assets/fig3_delta_tpr_by_budget_gray.png   (grayscale survival test)

Visual system (matches fig1): no contamination here, so no vermillion; ink
#1A1A1A for the estimate, grays for the reference lines. Parity vs acceptance
lines differ by linestyle (solid vs dashed), so the figure survives grayscale.
"""
import json
import pathlib
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "results/v2_controls/s2_exec2_phase4.json"
OUT = ROOT / "assets/fig3_delta_tpr_by_budget.pdf"
OUT_GRAY = ROOT / "assets/fig3_delta_tpr_by_budget_gray.png"

INK = "#1A1A1A"
GRAY = "#8A8A8A"      # reference lines
MIDGRAY = "#333333"  # F14: reference-line LABELS, dark enough to survive print
LGRAY = "#D8D8D8"
MINUS = "−"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 11, "pdf.fonttype": 42, "svg.fonttype": "none",  # F14: y-title legible at 3.3in col
    "text.color": INK, "axes.edgecolor": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
})

# frozen keys -> manuscript display strings for budget and matched count k
BUDGETS = [("0.02", "0.02", 15), ("0.05", "0.05", 38),
           ("0.1", "0.10", 77), ("0.2", "0.20", 153)]


def fmt3(v):
    return (MINUS if v < 0 else "") + f"{abs(v):.3f}"


def build(ax):
    db = json.load(open(SRC))["item2_tsplit_sensitivity"]["20"]["delta_by_budget"]
    xs = list(range(len(BUDGETS)))
    vals = [db[k][0] for k, _, _ in BUDGETS]
    los = [db[k][1] for k, _, _ in BUDGETS]
    his = [db[k][2] for k, _, _ in BUDGETS]
    yerr = [[v - lo for v, lo in zip(vals, los)],
            [hi - v for v, hi in zip(vals, his)]]

    # reference lines (labeled directly at the right edge, no legend)
    ax.axhline(0.05, color=GRAY, lw=1.0, ls=(0, (5, 3)), zorder=1)
    ax.axhline(0.0, color=GRAY, lw=1.0, ls="-", zorder=1)
    ax.axhspan(-0.6, 0.0, color=LGRAY, alpha=0.35, lw=0, zorder=0)
    # F14: darkened to mid-gray, moved inside the axes (kills the right overhang
    # that was starving the y-title), stacked clear of each other
    ax.text(3.0, 0.05, "acceptance  ΔTPR ≥ 0.05", va="bottom", ha="right",
            color=MIDGRAY, fontsize=10)
    ax.text(3.0, 0.0, "parity  0", va="top", ha="right",
            color=MIDGRAY, fontsize=10)

    ax.plot(xs, vals, "-", color=INK, lw=1.2, zorder=2)
    ax.errorbar(xs, vals, yerr=yerr, fmt="o", ms=7, color=INK,
                ecolor=INK, elinewidth=1.2, capsize=4, zorder=3)
    for x, v in zip(xs, vals):
        ax.annotate(fmt3(v), (x, v), textcoords="offset points",
                    xytext=(9, 0), ha="left", va="center",
                    color=INK, fontsize=8, fontweight="bold")

    ax.set_xticks(xs)
    ax.set_xticklabels([f"b = {disp}\nk = {k}" for _, disp, k in BUDGETS])
    ax.set_xlim(-0.35, 3.05)
    ax.set_ylim(-0.58, 0.12)
    ax.set_ylabel("ΔTPR = TPR(composite) − TPR(best baseline)")
    ax.spines[["top", "right"]].set_visible(False)


fig, ax = plt.subplots(figsize=(5.6, 3.2))
build(ax)
fig.savefig(OUT, bbox_inches="tight")

fig.savefig("/tmp/_fig3_rgb.png", dpi=150, bbox_inches="tight")
from PIL import Image
Image.open("/tmp/_fig3_rgb.png").convert("L").save(OUT_GRAY)
print(f"wrote {OUT}")
print(f"wrote {OUT_GRAY}")
