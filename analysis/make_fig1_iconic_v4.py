#!/usr/bin/env python3
"""Figure 1 (iconic v4): theorem-guided collapse signature.
FunSearch-grade presence: large icons, generous gutters, tight label-to-icon proximity.
Triad rendered as separate letter+arrow text objects to eliminate kerning overlap."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

NODE_FILL='#EEEEEE'; NODE_EDGE='#333333'
TEXT_DARK='#1A1A1A'; TEXT_BODY='#333333'
TEXT_GRAY='#555555'; TEXT_MUTE='#666666'
BLUE='#4A6FA5'; GREEN='#5A8A6B'; ORANGE='#C77B3A'
DOT_GREY='#444444'; BAND_FILL=BLUE
CONNECTOR='#555555'

fig = plt.figure(figsize=(13.0, 5.5), dpi=300)

# Tall panels with substantial vertical room for icons
PANEL_A = [0.075, 0.36, 0.16, 0.40]
PANEL_B = [0.305, 0.36, 0.16, 0.40]
PANEL_C = [0.535, 0.36, 0.16, 0.40]
PANEL_D = [0.765, 0.36, 0.16, 0.40]

CENTER_A, CENTER_B = 0.155, 0.385
CENTER_C, CENTER_D = 0.615, 0.845

# Titles tight above icons
title_y = 0.85
titles = [(CENTER_A, "Formal obstruction"),
          (CENTER_B, "Observable triad"),
          (CENTER_C, "Matched-FP contract"),
          (CENTER_D, "Alert-budget calibration")]
for cx, title in titles:
    fig.text(cx, title_y, title, fontsize=15, fontweight='semibold',
             ha='center', va='center', color=TEXT_DARK)

# Captions tight below icons
caption_y = 0.27
captions = [(CENTER_A, "verified \u00b7 Lean 4 machine-checked"),
            (CENTER_B, "stated \u00b7 under measurement-map assumption"),
            (CENTER_C, "protocol \u00b7 same contract, both benchmarks"),
            (CENTER_D, "tested \u00b7 across both flagship benchmarks")]
for cx, caption in captions:
    fig.text(cx, caption_y, caption, fontsize=10.5, fontstyle='italic',
             ha='center', va='center', color=TEXT_GRAY)

# ---------- A: code-card icon (substantial size) ----------
ax = fig.add_axes(PANEL_A); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.add_patch(FancyBboxPatch((0.02, 0.18), 0.96, 0.64,
    boxstyle="round,pad=0.005,rounding_size=0.06",
    facecolor=NODE_FILL, edgecolor=NODE_EDGE, linewidth=1.4,
    transform=ax.transAxes, clip_on=False))
ax.text(0.50, 0.50, "collapse_via_progresscycle_public",
        fontsize=11, family='monospace', color=TEXT_DARK,
        ha='center', va='center', transform=ax.transAxes)

# ---------- B: triad symbols (separated letter+arrow rendering) ----------
ax = fig.add_axes(PANEL_B); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()

def witness(letter_x, letter, arrow_x, arrow, color):
    """Render letter and arrow as separate text objects to avoid kerning overlap."""
    ax.text(letter_x, 0.50, letter, fontsize=50, fontweight='bold', color=color,
            ha='center', va='center', transform=ax.transAxes)
    ax.text(arrow_x, 0.50, arrow, fontsize=38, fontweight='bold', color=color,
            ha='center', va='center', transform=ax.transAxes)

witness(0.12, "G",        0.25, "\u2191", BLUE)
witness(0.45, "p",        0.58, "\u2191", GREEN)
witness(0.78, "\u03b4",   0.91, "\u2193", ORANGE)

# ---------- C: band glyph (interval shown via labels under the band) ----------
ax = fig.add_axes(PANEL_C); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
axis_y = 0.55
ax.plot([0.05, 0.95], [axis_y, axis_y], color='#888888', linewidth=1.4,
        transform=ax.transAxes, clip_on=False)
band_l = 0.05 + (0.03/0.10) * 0.90
band_r = 0.05 + (0.07/0.10) * 0.90
ax.add_patch(Rectangle((band_l, axis_y - 0.25), band_r - band_l, 0.50,
    facecolor=BAND_FILL, alpha=0.22, edgecolor=BAND_FILL, linewidth=1.0,
    linestyle='--', transform=ax.transAxes, clip_on=False))
ax.text(band_l, axis_y - 0.42, "0.03", fontsize=11, fontweight='semibold',
        color=BLUE, ha='center', va='center', transform=ax.transAxes)
ax.text(band_r, axis_y - 0.42, "0.07", fontsize=11, fontweight='semibold',
        color=BLUE, ha='center', va='center', transform=ax.transAxes)

# ---------- D: same band, two dots clearly outside ----------
ax = fig.add_axes(PANEL_D); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.plot([0.05, 0.95], [axis_y, axis_y], color='#888888', linewidth=1.4,
        transform=ax.transAxes, clip_on=False)
ax.add_patch(Rectangle((band_l, axis_y - 0.25), band_r - band_l, 0.50,
    facecolor=BAND_FILL, alpha=0.22, edgecolor=BAND_FILL, linewidth=1.0,
    linestyle='--', transform=ax.transAxes, clip_on=False))
ax.plot([0.14], [axis_y], 'o', color=DOT_GREY, markersize=16,
        markeredgecolor='white', markeredgewidth=1.4,
        transform=ax.transAxes, clip_on=False)
ax.plot([0.88], [axis_y], 'o', color=DOT_GREY, markersize=16,
        markeredgecolor='white', markeredgewidth=1.4,
        transform=ax.transAxes, clip_on=False)

# ---------- Arrows (darker, more presence, matching FunSearch weight) ----------
arrow_y = 0.58
for x1, x2 in [(0.245, 0.295), (0.475, 0.525), (0.705, 0.755)]:
    fig.add_artist(FancyArrowPatch(
        (x1, arrow_y), (x2, arrow_y),
        transform=fig.transFigure,
        arrowstyle='->', mutation_scale=22,
        color=CONNECTOR, linewidth=1.5))

# ---------- Bottom takeaway and footer ----------
fig.text(0.50, 0.14,
         "No tested comparator configuration was accepted under the locked equal-false-positive contract.",
         fontsize=12.5, color=TEXT_DARK, ha='center', va='center')

fig.text(0.50, 0.05,
         "+ Shumailov et al. (LLM recursive replay) \u00b7 secondary analysis \u00b7 matched-FP deferred",
         fontsize=9.5, fontstyle='italic', color=TEXT_MUTE,
         ha='center', va='center')

fig.savefig('fig1_iconic_v4.png', dpi=300, bbox_inches=None,
            facecolor='white', edgecolor='none')
fig.savefig('fig1_iconic_v4.pdf', bbox_inches=None,
            facecolor='white', edgecolor='none')
print("Saved fig1_iconic_v4.png and fig1_iconic_v4.pdf")
