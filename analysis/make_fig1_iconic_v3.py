#!/usr/bin/env python3
"""Figure 1 (iconic v3): theorem-guided collapse signature.
FunSearch-style breathing room: taller figure, larger icons, labels adjacent to icons.
Each icon is a discrete object with substantial visual presence."""

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
CONNECTOR='#888888'  # darker arrow for more presence

fig = plt.figure(figsize=(14.0, 5.6), dpi=300)

# Four icon panels, taller, with substantial vertical room
PANEL_A = [0.045, 0.34, 0.190, 0.44]
PANEL_B = [0.275, 0.34, 0.190, 0.44]
PANEL_C = [0.505, 0.34, 0.190, 0.44]
PANEL_D = [0.735, 0.34, 0.220, 0.44]

CENTER_A = 0.140
CENTER_B = 0.370
CENTER_C = 0.600
CENTER_D = 0.845

# Titles - closer to icons, larger font
title_y = 0.85
titles = [(CENTER_A, "Formal obstruction"),
          (CENTER_B, "Observable triad"),
          (CENTER_C, "Matched-FP contract"),
          (CENTER_D, "Alert-budget calibration")]
for cx, title in titles:
    fig.text(cx, title_y, title, fontsize=14, fontweight='semibold',
             ha='center', va='center', color=TEXT_DARK)

# Italic captions - closer to icons, larger font
caption_y = 0.25
captions = [(CENTER_A, "verified \u00b7 Lean 4 machine-checked"),
            (CENTER_B, "stated \u00b7 under measurement-map assumption"),
            (CENTER_C, "protocol \u00b7 same contract, both benchmarks"),
            (CENTER_D, "tested \u00b7 across both flagship benchmarks")]
for cx, caption in captions:
    fig.text(cx, caption_y, caption, fontsize=10, fontstyle='italic',
             ha='center', va='center', color=TEXT_GRAY)

# ---------- A: code-card icon (substantial visual weight) ----------
ax = fig.add_axes(PANEL_A); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.add_patch(FancyBboxPatch((0.02, 0.28), 0.96, 0.44,
    boxstyle="round,pad=0.005,rounding_size=0.05",
    facecolor=NODE_FILL, edgecolor=NODE_EDGE, linewidth=1.4,
    transform=ax.transAxes, clip_on=False))
ax.text(0.50, 0.50, "collapse_via_progresscycle_public",
        fontsize=11, family='monospace', color=TEXT_DARK,
        ha='center', va='center', transform=ax.transAxes)

# ---------- B: triad symbols (larger, more presence) ----------
ax = fig.add_axes(PANEL_B); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.text(0.20, 0.50, "G \u2191", fontsize=44, fontweight='bold', color=BLUE,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.50, 0.50, "p \u2191", fontsize=44, fontweight='bold', color=GREEN,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.80, 0.50, "\u03b4 \u2193", fontsize=44, fontweight='bold', color=ORANGE,
        ha='center', va='center', transform=ax.transAxes)

# ---------- C: band glyph (interval shown via labels on the band itself) ----------
ax = fig.add_axes(PANEL_C); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
axis_y = 0.48
ax.plot([0.05, 0.95], [axis_y, axis_y], color='#999999', linewidth=1.3,
        transform=ax.transAxes, clip_on=False)
band_l = 0.05 + (0.03/0.10) * 0.90
band_r = 0.05 + (0.07/0.10) * 0.90
ax.add_patch(Rectangle((band_l, axis_y - 0.20), band_r - band_l, 0.40,
    facecolor=BAND_FILL, alpha=0.20, edgecolor=BAND_FILL, linewidth=1.0,
    linestyle='--', transform=ax.transAxes, clip_on=False))
ax.text(band_l, axis_y - 0.35, "0.03", fontsize=11, fontweight='semibold',
        color=BLUE, ha='center', va='center', transform=ax.transAxes)
ax.text(band_r, axis_y - 0.35, "0.07", fontsize=11, fontweight='semibold',
        color=BLUE, ha='center', va='center', transform=ax.transAxes)

# ---------- D: same band, two dots outside (gestalt = 0 accepted) ----------
ax = fig.add_axes(PANEL_D); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.plot([0.05, 0.95], [axis_y, axis_y], color='#999999', linewidth=1.3,
        transform=ax.transAxes, clip_on=False)
ax.add_patch(Rectangle((band_l, axis_y - 0.20), band_r - band_l, 0.40,
    facecolor=BAND_FILL, alpha=0.20, edgecolor=BAND_FILL, linewidth=1.0,
    linestyle='--', transform=ax.transAxes, clip_on=False))
ax.plot([0.16], [axis_y], 'o', color=DOT_GREY, markersize=14,
        markeredgecolor='white', markeredgewidth=1.2,
        transform=ax.transAxes, clip_on=False)
ax.plot([0.88], [axis_y], 'o', color=DOT_GREY, markersize=14,
        markeredgecolor='white', markeredgewidth=1.2,
        transform=ax.transAxes, clip_on=False)

# ---------- Arrows between icons (more visual presence) ----------
arrow_y = 0.56
for x1, x2 in [(0.237, 0.272), (0.467, 0.502), (0.697, 0.732)]:
    fig.add_artist(FancyArrowPatch(
        (x1, arrow_y), (x2, arrow_y),
        transform=fig.transFigure,
        arrowstyle='->', mutation_scale=18,
        color=CONNECTOR, linewidth=1.2))

# ---------- Bottom takeaway ----------
fig.text(0.50, 0.12,
         "No tested comparator configuration was accepted under the locked equal-false-positive contract.",
         fontsize=12, color=TEXT_DARK, ha='center', va='center')

fig.text(0.50, 0.05,
         "+ Shumailov et al. (LLM recursive replay) \u00b7 secondary analysis \u00b7 matched-FP deferred",
         fontsize=9, fontstyle='italic', color=TEXT_MUTE,
         ha='center', va='center')

fig.savefig('fig1_iconic_v3.png', dpi=300, bbox_inches=None,
            facecolor='white', edgecolor='none')
fig.savefig('fig1_iconic_v3.pdf', bbox_inches=None,
            facecolor='white', edgecolor='none')
print("Saved fig1_iconic_v3.png and fig1_iconic_v3.pdf")
