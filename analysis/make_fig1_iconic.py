#!/usr/bin/env python3
"""Figure 1 (iconic version): theorem-guided collapse signature.
Four iconic panels in a single horizontal row. Pure architecture; no detailed
result reproduction. Comparator calibration detail lives in its own figure."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

# Palette
NODE_FILL='#EEEEEE'; NODE_EDGE='#444444'
TEXT_DARK='#222222'; TEXT_BODY='#333333'
TEXT_GRAY='#555555'; TEXT_MUTE='#666666'
BLUE='#4A6FA5'; GREEN='#5A8A6B'; ORANGE='#C77B3A'
DOT_GREY=TEXT_GRAY; BAND_FILL=BLUE
CONNECTOR='#bbbbbb'

fig = plt.figure(figsize=(13.0, 4.6), dpi=300)

# Single-row horizontal flow, four iconic panels of roughly equal width.
PANEL_A = [0.035, 0.32, 0.205, 0.46]
PANEL_B = [0.275, 0.32, 0.205, 0.46]
PANEL_C = [0.515, 0.32, 0.205, 0.46]
PANEL_D = [0.755, 0.32, 0.215, 0.46]

def panel_header(ax, letter, title, status=None):
    ax.text(0.000, 1.06, letter, fontsize=13, fontweight='bold',
            ha='left', va='bottom', transform=ax.transAxes, color=TEXT_DARK)
    ax.text(0.058, 1.06, title, fontsize=11.5, fontweight='semibold',
            ha='left', va='bottom', transform=ax.transAxes, color=TEXT_DARK)
    if status:
        ax.text(1.00, 1.06, status, fontsize=9, fontstyle='italic',
                ha='right', va='bottom', transform=ax.transAxes, color=TEXT_GRAY)

def panel_caption(ax, text):
    ax.text(0.50, -0.10, text,
            fontsize=8.5, fontstyle='italic', color=TEXT_GRAY,
            ha='center', va='top', transform=ax.transAxes)

# ---------- A: verified theorem (code-card glyph) ----------
ax = fig.add_axes(PANEL_A); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
panel_header(ax, 'A', 'Formal obstruction', status='verified')

ax.add_patch(FancyBboxPatch((0.04, 0.32), 0.92, 0.38,
    boxstyle="round,pad=0.005,rounding_size=0.05",
    facecolor=NODE_FILL, edgecolor=NODE_EDGE, linewidth=1.2,
    transform=ax.transAxes, clip_on=False))
ax.text(0.50, 0.51, "collapse_via_progresscycle_public",
        fontsize=10, family='monospace', color=TEXT_DARK,
        ha='center', va='center', transform=ax.transAxes)
panel_caption(ax, "Lean 4 \u00b7 machine-checked")

# ---------- B: stated bridge (triad glyph) ----------
ax = fig.add_axes(PANEL_B); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
panel_header(ax, 'B', 'Observable triad', status='stated')

ax.text(0.20, 0.50, "G \u2191", fontsize=34, fontweight='bold', color=BLUE,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.50, 0.50, "p \u2191", fontsize=34, fontweight='bold', color=GREEN,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.80, 0.50, "\u03b4 \u2193", fontsize=34, fontweight='bold', color=ORANGE,
        ha='center', va='center', transform=ax.transAxes)
panel_caption(ax, "under measurement-map assumption")

# ---------- C: matched-FP contract (band glyph) ----------
ax = fig.add_axes(PANEL_C); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
panel_header(ax, 'C', 'Matched-FP contract', status='protocol')

ax.text(0.50, 0.78, "FP \u2208 [0.03, 0.07]",
        fontsize=14, fontweight='bold', color=TEXT_DARK,
        ha='center', va='center', transform=ax.transAxes)

axis_y = 0.42
ax.plot([0.10, 0.90], [axis_y, axis_y], color='#999999', linewidth=1.0,
        transform=ax.transAxes, clip_on=False)
band_left  = 0.10 + (0.03/0.10) * 0.80
band_right = 0.10 + (0.07/0.10) * 0.80
ax.add_patch(Rectangle((band_left, axis_y - 0.10), band_right - band_left, 0.20,
    facecolor=BAND_FILL, alpha=0.20, edgecolor=BAND_FILL, linewidth=0.8,
    linestyle='--', transform=ax.transAxes, clip_on=False))
for val in [0.00, 0.05, 0.10]:
    xpos = 0.10 + (val/0.10) * 0.80
    ax.plot([xpos, xpos], [axis_y - 0.03, axis_y + 0.03], color='#999999',
            linewidth=0.8, transform=ax.transAxes, clip_on=False)
    ax.text(xpos, axis_y - 0.16, f"{val:.2f}", fontsize=7.5, color=TEXT_GRAY,
            ha='center', va='center', transform=ax.transAxes)

panel_caption(ax, "same contract \u00b7 both benchmarks")

# ---------- D: tested result (iconic rejection glyph) ----------
ax = fig.add_axes(PANEL_D); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
panel_header(ax, 'D', 'Alert-budget calibration', status='tested')

ax.text(0.50, 0.78, "0 accepted",
        fontsize=14, fontweight='bold', color=TEXT_DARK,
        ha='center', va='center', transform=ax.transAxes)

# Iconic strip-plot: band + two dots clearly outside. No labels.
icon_y = 0.42
ax.plot([0.05, 0.95], [icon_y, icon_y], color='#999999', linewidth=1.0,
        transform=ax.transAxes, clip_on=False)
ax.add_patch(Rectangle((0.40, icon_y - 0.10), 0.15, 0.20,
    facecolor=BAND_FILL, alpha=0.20, edgecolor=BAND_FILL, linewidth=0.8,
    linestyle='--', transform=ax.transAxes, clip_on=False))
ax.plot([0.18], [icon_y], 'o', color=DOT_GREY, markersize=11,
        markeredgecolor='white', markeredgewidth=1.0,
        transform=ax.transAxes, clip_on=False)
ax.plot([0.85], [icon_y], 'o', color=DOT_GREY, markersize=11,
        markeredgecolor='white', markeredgewidth=1.0,
        transform=ax.transAxes, clip_on=False)

panel_caption(ax, "across both flagship benchmarks")

# ---------- Cross-panel flow arrows ----------
arrow_y = 0.55
for x1, x2 in [(0.244, 0.272), (0.484, 0.512), (0.724, 0.752)]:
    fig.add_artist(FancyArrowPatch(
        (x1, arrow_y), (x2, arrow_y),
        transform=fig.transFigure,
        arrowstyle='->', mutation_scale=14,
        color=CONNECTOR, linewidth=1.0))

# ---------- Bottom takeaway ----------
fig.text(0.50, 0.13,
         "No tested comparator configuration was accepted under the locked equal-false-positive contract.",
         fontsize=11.5, color=TEXT_DARK, ha='center', va='center')

fig.text(0.50, 0.055,
         "+ Shumailov et al. (LLM recursive replay) \u00b7 secondary analysis \u00b7 matched-FP deferred",
         fontsize=8.5, fontstyle='italic', color=TEXT_MUTE,
         ha='center', va='center')

fig.savefig('fig1_iconic.png', dpi=300, bbox_inches=None,
            facecolor='white', edgecolor='none')
fig.savefig('fig1_iconic.pdf', bbox_inches=None,
            facecolor='white', edgecolor='none')
print("Saved fig1_iconic.png and fig1_iconic.pdf")
