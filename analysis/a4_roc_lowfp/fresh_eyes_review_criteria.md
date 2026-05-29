# Fresh-eyes review criteria — A4 ROC + low-FP zoom figure (v0)

**Figure file:** `results/figures/a4_roc_lowfp_main.png` (300 dpi PNG; vector PDF also at `a4_roc_lowfp_main.pdf`)
**Manuscript position:** Candidate replacement for Figure 1 right panel, OR new Figure 6, depending on Day 3 integration decision.
**Reviewer task:** Two reviews in one. First, vote on a narrative-design question (see Section 1 below). Second, conduct a standard figure-craft review (Sections 2-5). The narrative vote drives whether the craft review is binding or whether the figure gets reframed before craft polish.

---

## Section 1 — Caption review (decision (b) locked)

The author has chosen reframe option (b): keep the ROC figure as rendered; position the Loopzero gold star explicitly in the caption as the pre-registered conservative anchor; the continuous Loopzero ROC envelope is reported in the A2 follow-up section of the same manuscript. A2 is committed to land before arXiv (v1.0 launch ~June 3-4 2026), so the caption's forward reference is to in-paper work, not external follow-up.

### The reviewer's task

Two parts:

**(i) Caption adequacy assessment.** The proposed caption is below. Read it alongside the figure and assess: does it adequately position the gold star at (fp ≈ 0, tpr ≈ 0) so the reader does not interpret Loopzero as "never fires"? Does the forward reference to the A2 section read as a confident planned step rather than a hand-wave? Could a peer reviewer reasonably attack the framing, and if so, where?

**(ii) Standard craft review** per Sections 2-5 below.

### Proposed caption (draft, ~125 words)

> **Figure 6.** Comparator inadequacy on the canonical public benchmarks under the locked equal-FP contract [0.03, 0.07]. **(A)** Markets (Volmageddon + COVID, late-30min window): four fast families overfire above the band; slow families (matrix profile, permutation entropy) fail at the data-availability gate before calibration because their min-length requirement reduces n_control_units below band reachability. **(B)** Recommender (MovieLens-25M) at horizons h=40 (long dash), h=50 (★ canonical), h=60 (short dash): all six families miss the band; inset shows the low-FP region [0.0, 0.10] with the matrix-profile near-miss at FP ≈ 0.014. Gold ★ marks the pre-registered Loopzero conservative operating point (q=95, k=3); the continuous Loopzero ROC envelope via threshold-path sweeping is reported in Section [A2-section] of this manuscript. No tested comparator configuration achieves an accepted operating point under the locked equal-FP contract.

### Caption-review output format

Return: caption verdict (passes / needs minor revision / needs substantive rework), and if revision needed, specific prescriptions. The caption should ideally remain in the 80-150 word range for journal figure conventions.

---

## Section 2 — Substantive content claims the figure must support

If reframe (b) is chosen, the figure must visually carry these claims clearly. If (a) or (c), some of these still apply to whatever visual replaces this one.

1. **No tested comparator family reaches the locked equal-FP acceptance band [0.03, 0.07]** on either markets or recsys at any horizon (h=40, h=50, h=60).
2. **Markets and recsys are visibly distinct domains** with non-overlapping comparator family sets (markets: 4 fast families, no usable slow because slow families fail at the data-availability gate; recsys: 4 fast + 2 slow at every horizon).
3. **The low-FP region [0.0, 0.10]** is where slow comparators (matrix_profile, permutation_entropy) operate on recsys. They achieve low FP but also low TPR — the trade-off that makes them inadequate.
4. **Matrix profile near-miss at FP ≈ 0.014 at h=50 canonical** (the manuscript's headline near-miss) should be visible in the inset.
5. **Recsys h=50 canonical operating points** (the manuscript's headline horizon) are plotted as star markers to distinguish them from the h=40/h=60 line-curve evidence.
6. **Loopzero pre-registered position** (gold star) — per reframe vote, either prominent + caption-positioned (b), absent (a), or replaced by different visual (c).

---

## Section 3 — Design vocabulary (inherited from v13 iconic claim ladder + a3 forest plot)

**Palette (colorblind-safe, must read in B&W):**

| Family | Color | Hex | Domain availability |
|---|---|---|---|
| variance_ews | deep blue | #3B5C8C | both |
| cusum | forest green | #4F7B5C | both |
| page_hinkley | warm orange | #B66B30 | both |
| ac1_ews | red | #C04C3F | markets only |
| ac1 | darker red | #A03828 | recsys only |
| matrix_profile | muted purple | #7A5C9C | both (markets gate-failed) |
| permutation_entropy | olive | #8C7D3B | both (markets gate-failed) |

**Family naming asymmetry to verify:** markets uses `ac1_ews`; recsys uses `ac1`. These are sibling autocorrelation implementations with different smoothing pipelines, NOT the same detector. The two reds should be distinguishable but visually proximate, signaling sibling relationship.

**Text grays:** `#1A1A1A` (titles), `#444444` (labels), `#777777` (faint reference lines).

**Acceptance band fill:** sand `#EFE9D6`, edge lines `#D8C99C` at 0.6 pt.

**Loopzero gold:** `#C9A227` with dark `#1A1A1A` star edge.

**Typography:** DejaVu Sans throughout. Titles 10.5 pt semibold. Axis labels 9.5 pt. Tick labels 8.5 pt. Legend 8.5 pt.

**Line styles for horizon encoding (recsys):**
- h=40: long dash `(0, (5, 2))`, 1.5 pt, alpha 0.85
- h=60: short dash `(0, (1.5, 2))`, 1.5 pt, alpha 0.85
- h=50: star markers, no line

**Other style notes:**
- No top/right spines
- No minor gridlines
- Chance diagonal y=x drawn faint in main panels (alpha 0.5, dotted), suppressed in inset
- 300 dpi PNG + vector PDF; figure size 11.5 × 5.4 inches

---

## Section 4 — Standard craft review checklist

For each item, mark: ✓ (passes), ✗ (blocker), ⚠ (nice-to-fix), ◯ (cosmetic).

### Readability
- [ ] Family colors distinguishable at 180 mm physical print width
- [ ] All curves visible (no curves rendered below background, no z-order conflicts)
- [ ] Star markers (h=50 canonical + Loopzero gold) clearly distinct from line endpoints and curve dots
- [ ] Inset frame indicator on main recsys panel is legible but not visually heavy
- [ ] Inset tick labels are large enough to read (currently 7.5 pt)
- [ ] Legend handles match the curves they represent (no mismatches)
- [ ] Acceptance band visually clear without dominating

### B&W readability
- [ ] Print the figure in grayscale (or simulate via screenshot + desaturate). Are families still distinguishable?
- [ ] If not, which families collide? Flag specifically.
- [ ] Recsys horizons (h=40 vs h=60) distinguishable in B&W via line style alone?

### Numerical anchors (verify against on-disk data)

These specific numbers should be visually consistent with the figure:

- Markets: 4 family curves, all entering frame at FP ≥ 0.131
- Recsys h=40 (long dash), h=60 (short dash), h=50 (stars): 6 families each, FP range [0.0, ~1.0]
- Acceptance band: vertical strip at exactly [0.03, 0.07]
- Inset: zoom to FP ∈ [0.0, 0.10], xticks at {0.0, 0.03, 0.07, 0.10}
- Matrix profile h=50 marker at fp ≈ 0.0137, tpr ≈ 0.111
- Matrix profile h=40 curve point at fp ≈ 0.0236, tpr ≈ 0.117
- Matrix profile h=60 curve point at fp ≈ 0.0088, tpr ≈ 0.108
- Loopzero gold stars at fp ≈ 0, tpr ≈ 0 (one on markets panel, three overlapping on recsys panel)

### Layout
- [ ] Two-panel side-by-side, markets left, recsys right
- [ ] Shared TPR axis interpretation; markets shows y-label, recsys does not
- [ ] Panel titles "A. Markets — …" / "B. Recommender — …" at upper-left, semibold
- [ ] Inset positioned at lower-right of recsys panel (axes-fraction bounds [0.50, 0.06, 0.48, 0.42])
- [ ] Inset is large enough to read at print scale but not crowding the main panel
- [ ] Legends positioned below the figure, two-legend split (families left, encoding right)

### Composition (v13/a3 vocabulary specifics)
- [ ] Spine widths 0.7 pt, color `#444444`
- [ ] Family color palette matches the table in Section 3
- [ ] Star marker sizes: h=50 family stars 180 pt, Loopzero gold stars 340 pt
- [ ] No emoji, no decorative elements

---

## Section 5 — Expected output format

Please return:

1. **Caption verdict** — passes / needs minor revision / needs substantive rework. If revision needed, specific prescriptions for the caption text.
2. **Blockers** — anything in Section 2 that the figure fails to communicate, or anything in Section 4 marked ✗. List each with a one-sentence prescription.
3. **Nice-to-fix** — anything marked ⚠. List with prescriptions.
4. **Cosmetic** — anything marked ◯. List with prescriptions.
5. **Overall verdict** — "go for v1.1" / "needs craft pass + re-review" / "caption needs rework before re-review".

A3 Day 4 first-round review found 1 blocker + 3 nice-to-fix + 3 cosmetic; similar density expected here.

---

## Section 6 — Context the reviewer should NOT factor in

- The 30,000-ft Science Advances positioning conversation is happening separately. Your job is to review the figure on its own merits, not pre-flight it for any specific journal. The narrative-reframe vote feeds the journal conversation downstream, but you should vote based on what the figure is honestly capable of carrying, not based on what would maximize acceptance odds.
- A2 (threshold-path calibration) is committed to land in v1.0 before arXiv launch ~June 3-4 2026. The caption's forward reference to A2 is to a confirmed companion section in the same manuscript, not speculative future work.
- The manuscript currently has Figures 1-5 (Fig 5 is the A3 forest plot). Wherever this figure lands (replace Fig 1 right panel, or new Fig 6), the numbering is a Day 3 concern, not yours.
