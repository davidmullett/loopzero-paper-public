# Figure 6 caption (post-review-1, ~145 words)

**Status:** revised per fresh-eyes review 2026-05-20 (caption verdict: needs minor revision; gold-star coordinate framing strengthened per reviewer prescription).

---

**Figure 6.** Comparator inadequacy on the canonical public benchmarks under the locked equal-FP contract [0.03, 0.07]. **(A)** Markets (Volmageddon + COVID, late-30min window): four fast families overfire above the band; slow families (matrix profile, permutation entropy) fail at the data-availability gate before calibration because their min-length requirement reduces n_control_units below band reachability. **(B)** Recommender (MovieLens-25M) at horizons h=40 (long dash), h=50 (★ canonical), h=60 (short dash): all six families miss the band; inset shows the low-FP region [0.0, 0.10] with the matrix-profile near-miss at FP ≈ 0.014. Gold ★ marks the pre-registered Loopzero conservative operating point (q=95, k=3) at (FP ≈ 0, TPR ≈ 0); this is a single deliberately strict configuration, not the achievable Loopzero envelope. The continuous Loopzero ROC via threshold-path sweeping is reported in Section [A2-section] of this manuscript. No tested comparator configuration achieves an accepted operating point under the locked equal-FP contract.

---

## Outstanding placeholders before submission

- `[A2-section]` — fill with the actual A2 section number once A2 manuscript integration lands.

## Forward references documented

- Section [A2-section] (threshold-path calibration sweep generating the continuous Loopzero ROC envelope; the gold ★ in this figure is one operating point on that envelope).

## Why this caption framing

The reviewer flagged the original "Gold ★ marks the pre-registered Loopzero conservative operating point (q=95, k=3)" as inadequate because the rendered star sits at the ROC origin, and at display scale a reader can read that as "Loopzero plotted at zero TPR / never fires". The revised text:

1. Names the star's coordinates explicitly: `(FP ≈ 0, TPR ≈ 0)`. Removes the ambiguity.
2. Frames the coordinates as "a single deliberately strict configuration, not the achievable Loopzero envelope". Pre-empts the "Loopzero never fires" misreading by distinguishing single-config from continuous-envelope.
3. Forward-references A2 by section number. The continuous envelope lives in the same manuscript, not external follow-up.

A peer reviewer attempting to write "calling this a conservative operating point is special pleading" is answered by the explicit-coordinates + envelope-deferral structure. As long as A2 lands before arXiv (which is committed), this caption defends.

Word count: 145 words. Within 80-150 journal-figure convention range.
