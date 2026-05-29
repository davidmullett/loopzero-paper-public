#!/usr/bin/env python3
"""Figure 1 (iconic v2): theorem-guided collapse signature.
FunSearch grammar: plain titles above, content-bearing icons, single italic caption below.
No panel letters, no floating status badges, no headline duplications."""

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

fig = plt.figure(figsize=(14.0, 4.4), dpi=300)

# Four icon panels in a single row with generous gutters (FunSearch breathing room)
PANEL_A = [0.050, 0.42, 0.175, 0.34]
PANEL_B = [0.290, 0.42, 0.175, 0.34]
PANEL_C = [0.530, 0.42, 0.175, 0.34]
PANEL_D = [0.770, 0.42, 0.175, 0.34]

CENTER_A = 0.1375
CENTER_B = 0.3775
CENTER_C = 0.6175
CENTER_D = 0.8575

# Plain titles above (no panel letters)
title_y = 0.85
titles = [(CENTER_A, "Formal obstruction"),
          (CENTER_B, "Observable triad"),
          (CENTER_C, "Matched-FP contract"),
          (CENTER_D, "Alert-budget calibration")]
for cx, title in titles:
    fig.text(cx, title_y, title, fontsize=12.5, fontweight='semibold',
             ha='center', va='center', color=TEXT_DARK)

# Italic captions below (status folded in)
caption_y = 0.26
captions = [(CENTER_A, "verified \u00b7 Lean 4 machine-checked"),
            (CENTER_B, "stated \u00b7 under measurement-map assumption"),
            (CENTER_C, "protocol \u00b7 same contract, both benchmarks"),
            (CENTER_D, "tested \u00b7 across both flagship benchmarks")]
for cx, caption in captions:
    fig.text(cx, caption_y, caption, fontsize=9, fontstyle='italic',
             ha='center', va='center', color=TEXT_GRAY)

# ---------- A: code-card icon ----------
ax = fig.add_axes(PANEL_A); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.add_patch(FancyBboxPatch((0.02, 0.28), 0.96, 0.46,
    boxstyle="round,pad=0.005,rounding_size=0.05",
    facecolor=NODE_FILL, edgecolor=NODE_EDGE, linewidth=1.2,
    transform=ax.transAxes, clip_on=False))
ax.text(0.50, 0.51, "collapse_via_progresscycle_public",
        fontsize=9.5, family='monospace', color=TEXT_DARK,
        ha='center', va='center', transform=ax.transAxes)

# ---------- B: triad symbols ----------
ax = fig.add_axes(PANEL_B); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.text(0.20, 0.50, "G \u2191", fontsize=34, fontweight='bold', color=BLUE,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.50, 0.50, "p \u2191", fontsize=34, fontweight='bold', color=GREEN,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.80, 0.50, "\u03b4 \u2193", fontsize=34, fontweight='bold', color=ORANGE,
        ha='center', va='center', transform=ax.transAxes)

# ---------- C: band glyph (interval shown via axis labels) ----------
ax = fig.add_axes(PANEL_C); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
axis_y = 0.48
ax.plot([0.05, 0.95], [axis_y, axis_y], color='#999999', linewidth=1.0,
        transform=ax.transAxes, clip_on=False)
band_l = 0.05 + (0.03/0.10) * 0.90
band_r = 0.05 + (0.07/0.10) * 0.90
ax.add_patch(Rectangle((band_l, axis_y - 0.16), band_r - band_l, 0.32,
    facecolor=BAND_FILL, alpha=0.20, edgecolor=BAND_FILL, linewidth=0.8,
    linestyle='--', transform=ax.transAxes, clip_on=False))
ax.text(band_l, axis_y - 0.32, "0.03", fontsize=9.5, fontweight='semibold',
        color=BLUE, ha='center', va='center', transform=ax.transAxes)
ax.text(band_r, axis_y - 0.32, "0.07", fontsize=9.5, fontweight='semibold',
        color=BLUE, ha='center', va='center', transform=ax.transAxes)

# ---------- D: same band, two dots outside (visual gestalt = 0 accepted) ----------
ax = fig.add_axes(PANEL_D); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.plot([0.05, 0.95], [axis_y, axis_y], color='#999999', linewidth=1.0,
        transform=ax.transAxes, clip_on=False)
ax.add_patch(Rectangle((band_l, axis_y - 0.16), band_r - band_l, 0.32,
    facecolor=BAND_FILL, alpha=0.20, edgecolor=BAND_FILL, linewidth=0.8,
    linestyle='--', transform=ax.transAxes, clip_on=False))
# Two dots clearly outside the band on either side
ax.plot([0.16], [axis_y], 'o', color=DOT_GREY, markersize=12,
        markeredgecolor='white', markeredgewidth=1.0,
        transform=ax.transAxes, clip_on=False)
ax.plot([0.88], [axis_y], 'o', color=DOT_GREY, markersize=12,
        markeredgecolor='white', markeredgewidth=1.0,
        transform=ax.transAxes, clip_on=False)

# ---------- Arrows between icons ----------
arrow_y = 0.59
for x1, x2 in [(0.227, 0.288), (0.467, 0.528), (0.707, 0.768)]:
    fig.add_artist(FancyArrowPatch(
        (x1, arrow_y), (x2, arrow_y),
        transform=fig.transFigure,
        arrowstyle='->', mutation_scale=16,
        color=CONNECTOR, linewidth=1.0))

# ---------- Bottom takeaway ----------
fig.text(0.50, 0.11,
         "No tested comparator configuration was accepted under the locked equal-false-positive contract.",
         fontsize=11, color=TEXT_DARK, ha='center', va='center')

fig.text(0.50, 0.045,
         "+ Shumailov et al. (LLM recursive replay) \u00b7 secondary analysis \u00b7 matched-FP deferred",
         fontsize=8, fontstyle='italic', color=TEXT_MUTE,
         ha='center', va='center')

fig.savefig('fig1_iconic_v2.png', dpi=300, bbox_inches=None,
            facecolor='white', edgecolor='none')
fig.savefig('fig1_iconic_v2.pdf', bbox_inches=None,
            facecolor='white', edgecolor='none')
print("Saved fig1_iconic_v2.png and fig1_iconic_v2.pdf")
