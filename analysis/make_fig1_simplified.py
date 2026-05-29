#!/usr/bin/env python3
"""Figure 1 (simplified iconic version): theorem-guided collapse signature.
Three orientation glyphs (A, B, C) above one empirical result panel (D).
Internal detail in A/B/C is intentionally stripped; numbers live in Methods/Table 1."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

# Palette (matches detailed version for visual consistency)
NODE_FILL='#EEEEEE'; NODE_EDGE='#444444'
TEXT_DARK='#222222'; TEXT_BODY='#333333'
TEXT_GRAY='#555555'; TEXT_MUTE='#666666'
BLUE='#4A6FA5'; GREEN='#5A8A6B'; ORANGE='#C77B3A'
DOT_GREY=TEXT_GRAY; BAND_FILL=BLUE
CONNECTOR='#bbbbbb'

fig = plt.figure(figsize=(13.0, 7.5), dpi=300)

# Layout: top row = three iconic orientation glyphs; bottom = wide empirical result.
# The empirical panel carries the headline; A/B/C orient and cede the stage.
PANEL_A = [0.060, 0.620, 0.255, 0.255]
PANEL_B = [0.375, 0.620, 0.255, 0.255]
PANEL_C = [0.685, 0.620, 0.255, 0.255]
PANEL_D = [0.060, 0.135, 0.880, 0.395]

def panel_header(ax, letter, title, status=None):
    ax.text(0.000, 1.06, letter, fontsize=14, fontweight='bold',
            ha='left', va='bottom', transform=ax.transAxes, color=TEXT_DARK)
    ax.text(0.055, 1.06, title, fontsize=12, fontweight='semibold',
            ha='left', va='bottom', transform=ax.transAxes, color=TEXT_DARK)
    if status:
        ax.text(1.00, 1.06, status, fontsize=9, fontstyle='italic',
                ha='right', va='bottom', transform=ax.transAxes, color=TEXT_GRAY)

# ---------- PANEL A: verified theorem (iconic code-card) ----------
ax = fig.add_axes(PANEL_A); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
panel_header(ax, 'A', 'Formal obstruction', status='verified')

ax.add_patch(FancyBboxPatch((0.05, 0.30), 0.90, 0.36,
    boxstyle="round,pad=0.005,rounding_size=0.04",
    facecolor=NODE_FILL, edgecolor=NODE_EDGE, linewidth=1.2,
    transform=ax.transAxes, clip_on=False))
ax.text(0.50, 0.48, "collapse_via_progresscycle_public",
        fontsize=10.5, family='monospace', color=TEXT_DARK,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.50, 0.12, "Lean 4 \u00b7 machine-checked",
        fontsize=9, fontstyle='italic', color=TEXT_GRAY,
        ha='center', va='center', transform=ax.transAxes)

# ---------- PANEL B: stated bridge (triad symbols only) ----------
ax = fig.add_axes(PANEL_B); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
panel_header(ax, 'B', 'Observable triad', status='stated')

ax.text(0.20, 0.50, "G \u2191", fontsize=30, fontweight='bold', color=BLUE,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.50, 0.50, "p \u2191", fontsize=30, fontweight='bold', color=GREEN,
        ha='center', va='center', transform=ax.transAxes)
ax.text(0.80, 0.50, "\u03b4 \u2193", fontsize=30, fontweight='bold', color=ORANGE,
        ha='center', va='center', transform=ax.transAxes)

ax.text(0.50, 0.12, "under measurement-map assumption",
        fontsize=9, fontstyle='italic', color=TEXT_GRAY,
        ha='center', va='center', transform=ax.transAxes)

# ---------- PANEL C: matched-FP protocol contract (band glyph) ----------
ax = fig.add_axes(PANEL_C); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
panel_header(ax, 'C', 'Matched-FP contract', status='protocol')

# Headline: the band specification itself
ax.text(0.50, 0.72, "FP \u2208 [0.03, 0.07]",
        fontsize=14, fontweight='bold', color=TEXT_DARK,
        ha='center', va='center', transform=ax.transAxes)

# Mini band visualization (echoes the band shown larger in Panel D)
axis_y = 0.40
ax.plot([0.10, 0.90], [axis_y, axis_y], color='#999999', linewidth=1.0,
        transform=ax.transAxes, clip_on=False)
band_left  = 0.10 + (0.03/0.10) * 0.80
band_right = 0.10 + (0.07/0.10) * 0.80
ax.add_patch(Rectangle((band_left, axis_y - 0.07), band_right - band_left, 0.14,
    facecolor=BAND_FILL, alpha=0.18, edgecolor=BAND_FILL, linewidth=0.8,
    linestyle='--', transform=ax.transAxes, clip_on=False))
for val in [0.00, 0.05, 0.10]:
    xpos = 0.10 + (val/0.10) * 0.80
    ax.plot([xpos, xpos], [axis_y - 0.025, axis_y + 0.025], color='#999999',
            linewidth=0.8, transform=ax.transAxes, clip_on=False)
    ax.text(xpos, axis_y - 0.11, f"{val:.2f}", fontsize=8, color=TEXT_GRAY,
            ha='center', va='center', transform=ax.transAxes)

ax.text(0.50, 0.12, "same contract \u00b7 both benchmarks",
        fontsize=9, fontstyle='italic', color=TEXT_GRAY,
        ha='center', va='center', transform=ax.transAxes)

# ---------- PANEL D: empirical calibration result (kept detailed) ----------
ax = fig.add_axes(PANEL_D)
panel_header(ax, 'D', 'Alert-budget calibration', status='tested')

ax.set_xlim(-0.075, 0.180)
ax.set_ylim(-0.5, 1.5)
ax.set_yticks([])
ax.set_xticks([0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16])
ax.tick_params(axis='x', labelsize=9, colors=TEXT_GRAY)
for s in ['top', 'right', 'left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color('#999999')
ax.set_xlabel("control false-positive rate", fontsize=10, color=TEXT_GRAY, labelpad=6)

ax.axvspan(0.03, 0.07, color=BAND_FILL, alpha=0.13, zorder=0)
ax.axvline(0.03, color=BAND_FILL, linestyle='--', linewidth=1.0, zorder=1)
ax.axvline(0.07, color=BAND_FILL, linestyle='--', linewidth=1.0, zorder=1)

ax.text(0.05, 0.50, "accepted band\n[0.03, 0.07]",
        fontsize=9, color=BLUE, ha='center', va='center',
        fontweight='semibold', zorder=4,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white',
                  edgecolor='none', alpha=0.95))

ax.hlines(1.0, 0, 0.131579, colors=DOT_GREY, linewidth=1.2, alpha=0.6, zorder=2)
ax.plot([0.131579], [1.0], 'o', color=DOT_GREY, markersize=10,
        markeredgecolor='white', markeredgewidth=1.0, zorder=3)
ax.text(-0.070, 1.0, "Markets \u00b7 nearest\ncomparator: AC1",
        fontsize=9.5, color=TEXT_DARK, ha='left', va='center')
ax.text(0.131579, 0.65, "above band \u00b7 over-fires",
        fontsize=8.5, fontstyle='italic', color=TEXT_MUTE,
        ha='center', va='center')

ax.hlines(0.0, 0, 0.0136698, colors=DOT_GREY, linewidth=1.2, alpha=0.6, zorder=2)
ax.plot([0.0136698], [0.0], 'o', color=DOT_GREY, markersize=10,
        markeredgecolor='white', markeredgewidth=1.0, zorder=3)
ax.text(-0.070, 0.0, "Recommender \u00b7 nearest\ncomparator: matrix profile",
        fontsize=9.5, color=TEXT_DARK, ha='left', va='center')
ax.text(0.0136698, -0.35, "below band \u00b7 under-fires",
        fontsize=8.5, fontstyle='italic', color=TEXT_MUTE,
        ha='center', va='center')

ax.text(0.180, 1.25, "Full markets grid tested \u00b7 0 accepted",
        fontsize=8.5, fontstyle='italic', color=TEXT_MUTE,
        ha='right', va='center')
ax.text(0.180, 0.25, "105 recommender configurations tested \u00b7 0 accepted",
        fontsize=8.5, fontstyle='italic', color=TEXT_MUTE,
        ha='right', va='center')

# ---------- Cross-panel flow arrows (top row only; D's role is implicit) ----------
fig.add_artist(FancyArrowPatch(
    (0.320, 0.7475), (0.370, 0.7475),
    transform=fig.transFigure,
    arrowstyle='->', mutation_scale=12,
    color=CONNECTOR, linewidth=0.9))

fig.add_artist(FancyArrowPatch(
    (0.635, 0.7475), (0.680, 0.7475),
    transform=fig.transFigure,
    arrowstyle='->', mutation_scale=12,
    color=CONNECTOR, linewidth=0.9))

# ---------- Bottom takeaway ----------
fig.text(0.50, 0.070,
         "No tested comparator configuration was accepted under the locked equal-false-positive contract.",
         fontsize=12, color=TEXT_DARK, ha='center', va='center')

fig.text(0.50, 0.028,
         "+ Shumailov et al. (LLM recursive replay) \u00b7 secondary analysis \u00b7 matched-FP deferred",
         fontsize=8.5, fontstyle='italic', color=TEXT_MUTE,
         ha='center', va='center')

fig.savefig('fig1_simplified.png', dpi=300, bbox_inches=None,
            facecolor='white', edgecolor='none')
fig.savefig('fig1_simplified.pdf', bbox_inches=None,
            facecolor='white', edgecolor='none')
print("Saved fig1_simplified.png and fig1_simplified.pdf")
