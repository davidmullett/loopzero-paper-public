#!/usr/bin/env python3
"""Figure 2 - "Every large contaminated-population effect is mechanical."

Paired Cohen's d for the four indicators on the contaminated population
(d_full, vs all controls) and the purified population (d_purified, vs clean
controls). The contaminated marks carry the vermillion contamination accent;
the purified marks are ink. The story: every large contaminated effect
collapses toward zero or reverses under purification.

FROZEN INPUT (read-only; values are read, never recomputed):
    results/v2_controls/s2_exec2_phase4.json  ->  item1_bounding_diagnostic
        {G,p,delta,mrf}.{d_full, d_purified}

OUTPUT:
    assets/fig2_bounding_diagnostic.pdf   (vector, print width)
    assets/fig2_bounding_diagnostic_gray.png   (grayscale survival test)

Visual system (matches fig1): vermillion #D55E00 is reserved exclusively for
the contaminated / shadow-class values; purified values take ink #1A1A1A and
grays. Color is redundantly encoded by marker shape (contaminated = circle,
purified = square) so the figure survives grayscale.
"""
import json
import pathlib
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "results/v2_controls/s2_exec2_phase4.json"
OUT = ROOT / "assets/fig2_bounding_diagnostic.pdf"
OUT_GRAY = ROOT / "assets/fig2_bounding_diagnostic_gray.png"

VERM = "#D55E00"   # contamination / shadow-class ONLY
INK = "#1A1A1A"
GRAY = "#8A8A8A"
MINUS = "−"   # unicode minus, to match the manuscript

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 11, "pdf.fonttype": 42, "svg.fonttype": "none",  # F11: legible at 3.3in col
    "text.color": INK, "axes.edgecolor": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
})


def fmt(v):
    return ("+" if v >= 0 else MINUS) + f"{abs(v):.2f}"


def build(ax):
    d = json.load(open(SRC))["item1_bounding_diagnostic"]
    rows = [("G (churn)", "G"), ("p (occupancy)", "p"),
            ("δ (coverage)", "delta"), ("miss-run fraction", "mrf")]
    ys = list(range(len(rows)))[::-1]
    for y, (label, key) in zip(ys, rows):
        e = d[key]
        cont, pur = e["d_full"], e["d_purified"]
        ax.annotate("", xy=(pur, y), xytext=(cont, y),
                    arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.0,
                                    shrinkA=5, shrinkB=5))
        ax.plot([cont], [y], marker="o", ms=8, color=VERM, zorder=3)
        ax.plot([pur], [y], marker="s", ms=8, color=INK, zorder=3)  # F9: +~14% weight
        ax.annotate(fmt(cont), (cont, y), textcoords="offset points",
                    xytext=(0, 10), ha="center", va="bottom",
                    color=VERM, fontsize=11, fontweight="bold")  # F11
        ax.annotate(fmt(pur), (pur, y), textcoords="offset points",
                    xytext=(0, -12), ha="center", va="top",
                    color=INK, fontsize=12, fontweight="bold")  # F9 heavier + F11
    # direct key (marks, not a legend box), in the empty upper-left
    ax.plot([-2.95], [3.42], marker="o", ms=8, color=VERM, clip_on=False)
    ax.text(-2.74, 3.42, "contaminated", va="center", color=VERM, fontsize=11)  # F11
    ax.plot([-2.95], [3.06], marker="s", ms=8, color=INK, clip_on=False)
    ax.text(-2.74, 3.06, "purified", va="center", color=INK, fontsize=11)  # F11

    ax.axvline(0, color=GRAY, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(-0.6, 3.7)
    ax.set_xlim(-3.3, 2.7)
    ax.set_xlabel("Cohen's d  (event vs control separation)")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(left=False)


fig, ax = plt.subplots(figsize=(5.2, 2.9))
build(ax)
fig.savefig(OUT, bbox_inches="tight")

# grayscale survival test
fig.savefig("/tmp/_fig2_rgb.png", dpi=150, bbox_inches="tight")
from PIL import Image
Image.open("/tmp/_fig2_rgb.png").convert("L").save(OUT_GRAY)
print(f"wrote {OUT}")
print(f"wrote {OUT_GRAY}")
