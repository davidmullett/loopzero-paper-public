#!/usr/bin/env python3
"""Figure 1 (iconic v5): theorem-guided collapse signature.
FunSearch-grade visual language: top bracket with system title, variable panel widths,
two-line captions, mathtext-rendered triad, curved arrows, X-mark rejection indicators."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

NODE_FILL='#F4F4F4'; NODE_EDGE='#444444'
TEXT_DARK='#1A1A1A'; TEXT_BODY='#333333'
TEXT_GRAY='#555555'; TEXT_MUTE='#777777'
BLUE='#3B5C8C'; GREEN='#4F7B5C'; ORANGE='#B66B30'; RED='#B0463A'
DOT_GREY='#3A3A3A'; BAND_FILL='#3B5C8C'
CONNECTOR='#444444'; BRACKET='#666666'

fig = plt.figure(figsize=(14.0, 6.8), dpi=300)

# Variable-width panels — D wider to hold multiple comparator dots
PANEL_A = [0.045, 0.36, 0.17, 0.30]
PANEL_B = [0.245, 0.36, 0.22, 0.30]
PANEL_C = [0.495, 0.36, 0.17, 0.30]
PANEL_D = [0.695, 0.36, 0.26, 0.30]

CENTER_A = PANEL_A[0] + PANEL_A[2]/2
CENTER_B = PANEL_B[0] + PANEL_B[2]/2
CENTER_C = PANEL_C[0] + PANEL_C[2]/2
CENTER_D = PANEL_D[0] + PANEL_D[2]/2

# ---------- Top bracket + system title (FunSearch grammar) ----------
fig.text(0.50, 0.93, "Loopzero claim ladder",
         fontsize=17, fontweight='normal',
         ha='center', va='center', color=TEXT_DARK)

bracket_y = 0.885
bracket_l, bracket_r = 0.055, 0.945
bracket_drop = 0.022
fig.add_artist(plt.Line2D([bracket_l, bracket_r], [bracket_y, bracket_y],
                          color=BRACKET, linewidth=1.3,
                          transform=fig.transFigure))
fig.add_artist(plt.Line2D([bracket_l, bracket_l],
                          [bracket_y, bracket_y - bracket_drop],
                          color=BRACKET, linewidth=1.3,
                          transform=fig.transFigure))
fig.add_artist(plt.Line2D([bracket_r, bracket_r],
                          [bracket_y, bracket_y - bracket_drop],
                          color=BRACKET, linewidth=1.3,
                          transform=fig.transFigure))

# ---------- Panel titles (regular weight, FunSearch style) ----------
title_y = 0.80
titles = [(CENTER_A, "Formal obstruction"),
          (CENTER_B, "Observable triad"),
          (CENTER_C, "Matched-FP contract"),
          (CENTER_D, "Alert-budget calibration")]
for cx, title in titles:
    fig.text(cx, title_y, title, fontsize=14, fontweight='normal',
             ha='center', va='center', color=TEXT_DARK)

# ---------- Two-line captions (FunSearch "Programs / database" pattern) ----------
status_y = 0.30
desc_y = 0.26
captions = [
    (CENTER_A, "verified",  "Lean 4 machine-checked"),
    (CENTER_B, "stated",    "under measurement-map assumption"),
    (CENTER_C, "protocol",  "same contract, both benchmarks"),
    (CENTER_D, "tested",    "across both flagship benchmarks"),
]
for cx, status, desc in captions:
    fig.text(cx, status_y, status, fontsize=11.5, fontweight='semibold',
             ha='center', va='center', color=TEXT_DARK)
    fig.text(cx, desc_y, desc, fontsize=9.5, fontstyle='italic',
             ha='center', va='center', color=TEXT_GRAY)

# ---------- A: code-card icon (wrapped across two lines) ----------
ax = fig.add_axes(PANEL_A); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.add_patch(FancyBboxPatch((0.03, 0.15), 0.94, 0.70,
    boxstyle="round,pad=0.008,rounding_size=0.06",
    facecolor=NODE_FILL, edgecolor=NODE_EDGE, linewidth=1.4,
    transform=ax.transAxes, clip_on=False))
ax.text(0.50, 0.50, "collapse_via_\nprogresscycle_public",
        fontsize=11, family='monospace', color=TEXT_DARK,
        ha='center', va='center', transform=ax.transAxes,
        linespacing=1.4)

# ---------- B: triad rendered via mathtext (kerning-clean) ----------
ax = fig.add_axes(PANEL_B); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.text(0.16, 0.50, r"$\mathbf{G\,\uparrow}$",
        fontsize=44, color=BLUE,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.50, 0.50, r"$\mathbf{p\,\uparrow}$",
        fontsize=44, color=GREEN,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.84, 0.50, r"$\mathbf{\delta\,\downarrow}$",
        fontsize=44, color=ORANGE,
        ha='center', va='center', transform=ax.transAxes)

# ---------- C: band glyph ----------
ax = fig.add_axes(PANEL_C); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
axis_y = 0.55
ax.plot([0.05, 0.95], [axis_y, axis_y], color='#888888', linewidth=1.4,
        transform=ax.transAxes, clip_on=False)
band_l = 0.05 + (0.03/0.10) * 0.90
band_r = 0.05 + (0.07/0.10) * 0.90
ax.add_patch(Rectangle((band_l, axis_y - 0.28), band_r - band_l, 0.56,
    facecolor=BAND_FILL, alpha=0.22, edgecolor=BAND_FILL, linewidth=1.0,
    linestyle='--', transform=ax.transAxes, clip_on=False))
ax.text(band_l, axis_y - 0.44, "0.03", fontsize=11, fontweight='semibold',
        color=BLUE, ha='center', va='center', transform=ax.transAxes)
ax.text(band_r, axis_y - 0.44, "0.07", fontsize=11, fontweight='semibold',
        color=BLUE, ha='center', va='center', transform=ax.transAxes)

# ---------- D: same band + multiple rejected comparators with X-marks ----------
ax = fig.add_axes(PANEL_D); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
ax.plot([0.03, 0.97], [axis_y, axis_y], color='#888888', linewidth=1.4,
        transform=ax.transAxes, clip_on=False)
# Band positioned so [0.03, 0.07] maps to [30%, 70%] of the visual axis
band_l_d = 0.03 + 0.30 * 0.94
band_r_d = 0.03 + 0.70 * 0.94
ax.add_patch(Rectangle((band_l_d, axis_y - 0.28), band_r_d - band_l_d, 0.56,
    facecolor=BAND_FILL, alpha=0.22, edgecolor=BAND_FILL, linewidth=1.0,
    linestyle='--', transform=ax.transAxes, clip_on=False))
# Multiple comparator dots — below-band cluster, above-band cluster
# Each marked with a small ✗ to indicate rejection
below_dots = [0.08, 0.13, 0.18, 0.24]
above_dots = [0.76, 0.82, 0.88, 0.94]
for x_pos in below_dots + above_dots:
    ax.plot([x_pos], [axis_y], 'o', color=DOT_GREY, markersize=10,
            markeredgecolor='white', markeredgewidth=1.0,
            transform=ax.transAxes, clip_on=False)
    ax.text(x_pos, axis_y + 0.22, "\u2717", fontsize=10, color=RED,
            fontweight='bold',
            ha='center', va='center', transform=ax.transAxes)

# ---------- Arrows: straight + one curved (FunSearch character) ----------
arrow_y = 0.51
# A -> B (straight)
fig.add_artist(FancyArrowPatch(
    (0.215, arrow_y), (0.245, arrow_y),
    transform=fig.transFigure,
    arrowstyle='->', mutation_scale=24,
    color=CONNECTOR, linewidth=1.6))
# B -> C (straight)
fig.add_artist(FancyArrowPatch(
    (0.465, arrow_y), (0.495, arrow_y),
    transform=fig.transFigure,
    arrowstyle='->', mutation_scale=24,
    color=CONNECTOR, linewidth=1.6))
# C -> D (slight curve)
fig.add_artist(FancyArrowPatch(
    (0.665, arrow_y), (0.695, arrow_y),
    transform=fig.transFigure,
    arrowstyle='->', mutation_scale=24,
    color=CONNECTOR, linewidth=1.6,
    connectionstyle="arc3,rad=-0.12"))

# ---------- Bottom takeaway ----------
fig.text(0.50, 0.13,
         "No tested comparator configuration was accepted under the locked equal-false-positive contract.",
         fontsize=12.5, color=TEXT_DARK, ha='center', va='center')

fig.text(0.50, 0.05,
         "+ Shumailov et al. (LLM recursive replay) \u00b7 secondary analysis \u00b7 matched-FP deferred",
         fontsize=9.5, fontstyle='italic', color=TEXT_MUTE,
         ha='center', va='center')

fig.savefig('fig1_iconic_v5.png', dpi=300, bbox_inches=None,
            facecolor='white', edgecolor='none')
fig.savefig('fig1_iconic_v5.pdf', bbox_inches=None,
            facecolor='white', edgecolor='none')
print("Saved fig1_iconic_v5.png and fig1_iconic_v5.pdf")
