# Supplementary Materials

## Absorbing Shadow Classes in Conjunctive Label Rules

**David Mullett** *Independent researcher* · ORCID 0009-0004-2543-1664 · correspondence: d@loopzero.org

This document contains the supplementary materials referenced in the main manuscript: the learnability gate stated in the registration's own vocabulary (S1), the pre-execution conformance audit in full (S2), the two revision-stage deviations D-43 and D-44 (S3), the content-pinned provenance chain (S4), and the supporting robustness and control-arm tables (S5). Section references of the form §7, §11 are to the frozen Study 2 pre-registration (OSF osf.io/wka72); Study 1's frozen pre-registration document is hosted in OSF project osf.io/7bvgz. Hashes are given in short form; the full manifest is in the repository.

---

## S1. The learnability gate, in registered vocabulary

The main text describes a learnability gate placed upstream of the detector comparison. Stated in the registration's own terms, the gate is §7's construction-validity precondition PC1, evaluated before any §11 decision quantity.

**PC1 (early-miss-rate learnability).** At the primary budget b = 0.05, does the early miss rate separate events from controls above the matched-budget chance rate? §7 fixes the consequence verbatim: *"If PC1 fails, the landmark population carries no learnable signal and all indicator results are reported as uninterpretable-by-construction rather than as evidence."* The route is not SURVIVES and not DIES; the full sweep is still published under §12.

On Study 1's population the gate fails. PC1 TPR at b = 0.05 is **0.0**, BCa 95% CI [0.0, 0.0], failing under both readings of the §7 wording (TPR − chance = −0.05; TPR − prevalence = −0.805; both intervals exclude zero on the wrong side). The subsequent census showed that this was a label-validity failure rather than merely a weak baseline: L-events miss at most 7 of 20 in-window steps, L-controls a median of 15 of 20, because frontier-starved units can never be labeled degraded and are filed as controls by construction. Amending the gate after seeing the baseline collapse would have produced a false SURVIVES — a non-discriminative composite scores TPR ≈ 0.05 at a 5% control-alarm budget by chance, exactly clearing §11 criterion 1 — so the gate prevented a chance-level result from being interpreted as a positive detector finding.

On the purified Study 2 population the gate passes. PC1 TPR at b = 0.05 is **0.561** (BCa 95% CI [0.549, 0.574]), an excess over chance of 0.511 [0.499, 0.524]. The liveness check PC2 passes, and the §11 power gate is met at 10,153 evaluation-fold events against a floor of 200.

**Table S1. PC1 before and after repair, at the four registered budgets.** Study 1 population: the full nominal control class at the landmark (4,755 controls, of which 3,292 are frontier-starved by step 20). Study 2 population: the clean control class (1,460 = 694 calibration + 766 evaluation).

| budget b | k (eval clean, n=766) | Study 1 PC1 route | Study 2 PC1 TPR |
| :-: | :-: | :-: | :-: |
| 0.02 | 15 | fail → uninterpretable | 0.550 |
| 0.05 (primary) | 38 | fail → uninterpretable | 0.561 |
| 0.10 | 77 | fail → uninterpretable | 0.584 |
| 0.20 | 153 | fail → uninterpretable | 0.625 |

The same gate returned both answers on the same benchmark, before and after competing-event purification of the control class.

---

## S2. The pre-execution conformance audit

Before the registered Study 2 analysis was executed, the executed configuration was audited parameter by parameter against the frozen registration. Of thirty-four registered parameters, thirty were conformant and four departed. Each finding was recorded in the deviations log before it was investigated, and no §11 decision quantity was computed until the audit closed.

### S2.1 The four departures

All four share one root cause: configuration constants transcribed from the Study 1 registration into the operative Study 2 configuration.

1. **Analysis-population filter.** An earlier execution ran PC1 over the full landmark control class — 2,453 evaluation controls, matched count k = 123 — rather than the registered clean control class of 766 evaluation controls, k = 38. The registered Study 2 population restricts controls to units that neither degrade nor starve through the horizon; the earlier execution admitted the starved stratum. (Logged as D-7 / D-9.)
2. **Matched-alarm budget grid.** The executed code carried the Study 1 grid {0.01, 0.02, 0.05, 0.10}; the frozen registration specifies {0.02, 0.05, 0.10, 0.20} with primary 0.05, removing 0.01 by design and adding 0.20 as a stable moderate-budget readout. §11 criterion 2 counts positive signs over the four-budget set, so the grid enters the verdict directly. (Logged as D-15.)
3. **Pre-census denominator.** The Phase-2.5 label-side pre-census inherited the same Study 1 grid, so its per-budget counts carried the same denominator error. (Downstream of D-15; corrected in the re-derivation under the C** anchor.)
4. **Labelling defect.** One output writer carried a placeholder labelling defect, found and corrected before the run. (Logged with the Phase-4 harness disclosure, D-39.)

Two of these — the population filter and the budget grid — invalidated the earlier execution. That execution had halted at its own PC1 gate and produced no detector comparison, so vacating it overturned no result; its record is retained and its verdict void. The analysis reported in the main text is the first execution of the registered design, adjudicated against the verbatim frozen registration: the executed population there (2,453 controls) matched neither the registered clean class (1,460) nor the candidate class (1,463), and the 3,292 pre-landmark-starved units were never admissible under any registered label.

### S2.2 Three further findings

Beyond the four departures, three findings concerned provenance and attestation. The main text defers their detail here.

1. **Input provenance.** The slate telemetry panel verified against its registered content hash (`ea972e2e…`), but the raw-ratings provenance anchor was stale: the recorded container hash (`a6221995…`) matched neither the live container nor its decompressed content, and no content hash existed for the file. The chain was re-established against a public anchor — the MovieLens-25M distribution hash published in arXiv:2606.00329 (`8b21cfb7…`), whose member `ratings.csv` (`9c855257…`) sorts deterministically to the panel input (`360fb201…`). (Logged as D-16 / D-21 and their resolutions.)
2. **Uncommitted artifact writers.** A sweep found three generators absent from the versioned tree — the slate-panel generator, the clean-control census generator, and the covariate-cache builder. Each was committed, and its artifact content-verified or canonically re-derived to byte identity; the re-derived covariate cache (`c338f55b…`) was proven a byte-exact row-subset of the pre-registered cache record. (Logged as D-18 / D-19 / D-20.)
3. **Attestation completeness.** An earlier contamination-clearance attestation was incomplete as written: it stated that no PC1 true-positive rate or interval had ever been surfaced, but a pre-block accounting file already contained a whole-horizon PC1 rate and interval. The no-peek corridor itself held — the blind block's decision quantities were never written (a 240-byte payload with the decision quantities null) — and the surfaced quantity was the whole-horizon Study 1 rate already public as the Study 1 pathology headline, not a Study 2 clean-population quantity. The attestation was re-issued against a corrected, exhaustive enumeration and the corridor re-certified. (Logged as D-28.)

The provenance chain is content-pinned end to end, from the published source-dataset hash through the derived panel, the clean-control census, and the covariate cache to the verdict artifact (S4).

---

## S3. Deviations D-43 and D-44

The abstract reports four pre-execution departures. The deviations log runs past them to D-45. This section reconciles the two so that a reader who finds D-43 or D-44 cannot set them against the abstract's scoped count: D-43 and D-44 are revision-stage entries made after the verdict, not pre-execution departures, and neither touches the verdict.

**D-43 (withdrawn).** A revision briefly advanced a geometric-infeasibility argument: that r(G, δ) = 0.975 made the registered composite signature effectively unrealisable, with a variance decomposition placing roughly 95% of the composite's variance in the occupancy term (Var(D) = 2(1 − 0.975) ≈ 0.05 for D = z(G) − z(δ)). Verification established that the correlation matrix had been computed on the full evaluation-fold arm (n = 12,606) rather than on the 694 calibration-fold clean controls that define the z-parameters — a departure from the ruled Phase-4 scope.

**D-44 (ruling and result).** The Phase-4 scope specifies the calibration-fold clean controls as the standardisation population, so recomputation there is a permitted remedy rather than a new analysis. The pre-committed reading was fixed before the value was seen: r(G, δ) ≥ 0.90 would restore the decomposition; r(G, δ) < 0.90 would revert §5.1 to a qualitative account permanently. Recomputed on the 694 calibration-fold clean controls, **r(G, δ) = 0.833** (not 0.975), with Var(D) = 0.334, Var(S) = 1.207 and an occupancy variance share near 83% rather than 95%. The reading fired **REVERT**: the decomposition was withdrawn, D-43 was not reinstated, and §5.1 declines a complete mechanistic account of the null. The inflation from 0.833 to 0.975 is itself a contamination artifact — the starved stratum's extreme indicator values drive the apparent lockstep — which is the same point §4.4 makes about feature geometry estimated on an unvalidated-label population. The verdict is untouched throughout; D-45 records the corrected first-order cancellation arithmetic that replaced the withdrawn decomposition.

The pre-specified threshold therefore required withdrawal of the revision-stage argument.

---

## S4. Provenance chain and tamper-evident anchors

Every quantity in the study is downstream of one public input and is content-pinned at each step.

**Chain.** Published MovieLens-25M distribution hash (equal to the anchor in arXiv:2606.00329) → deterministically sorted ratings → slate telemetry panel → clean-control census → covariate cache → verdict artifact. Content hashes, not container hashes, are pinned at each input gate, and population conformance is checked by per-class per-fold set-hash against the census before any computation runs; a mismatch hard-stops.

**Anchors.** A tamper-evident chain of SHA-256 anchors is committed to the public repository — over the deviations log, the analysis code, the Study 2 census, the sign-convention table, the verdict suite, the pre-census, the arm panels, the covariate cache, and the verdict — each committed before the run it governs, so timing is established by the repository rather than asserted in the text. The deviations log is anchored the same way: its hash is committed publicly before each sweep, making the log tamper-evident and dated while its embargoed contents stay closed until the OSF embargo lifts.

**A disclosed failure.** The Version-1 log anchor was non-functional: the committed hash file carried a template placeholder rather than a computed digest, so that commit establishes a date but no tamper-evidence. It was disclosed rather than silently repaired, and the commit was left unaltered; the first real content hash is Version 2, still committed before any decision quantity. The pre-decision timing of the Study 1 gate ruling rests independently on the contamination audit of disk and git history, which found that no discrimination advantage, incremental AUC, or four-criteria evaluation was ever computed or written.

---

## S5. Supporting tables

### S5.1 Bounding diagnostic (Cohen's d)

Evaluation fold: 10,153 events, 766 clean controls, 1,687 starved controls. Mechanical Δd is the registered contaminated-minus-purified contrast; the starved-vs-clean column is the separate bounding diagnostic.

| indicator | d, contaminated (vs all controls) | d, purified (vs clean) | d, starved vs clean | mechanical Δd [95% CI] |
| :-: | :-: | :-: | :-: | :-: |
| z(G) churn | 2.010 | −0.636 | −5.622 | 2.646 [2.553, 2.739] |
| z(p) occupancy | −2.251 | 0.046 | 4.095 | −2.297 [−2.389, −2.204] |
| z(δ) coverage | 1.999 | −0.680 | −5.603 | 2.680 [2.585, 2.775] |
| miss-run fraction | −2.622 | 0.811 | 6.140 | −3.433 [−3.550, −3.317] |

The slate indicators' whole-horizon event discrimination collapses or reverses on the clean population; only the miss-run fraction retains discrimination there (d = +0.811). Every mechanical Δd interval excludes zero.

### S5.2 Landmark robustness

The primary analysis was repeated at landmarks 15, 20 and 25. Criteria 1 and 2 fail at every landmark. Criterion 3 fails at 20 and 25 and is coverage-limited at 15 (58.65% covariate coverage, declared before computation).

### S5.3 Severed control arms

Absolute discrimination against chance, reported unconditionally under the pre-registered protocol, exceeds chance on zero of six control arms in which the recursive personalisation mechanism is disabled. Four arms are significantly below chance; on two shuffled-timestamp arms the interval includes zero, so those are indistinguishable from chance rather than below it.

### S5.4 History of the discarded stratum

Controls starved by the landmark (n = 3,292) have thinner early positive histories than clean controls (n = 1,460): standardised difference on warm-start positive count, Cohen's d = −0.441, bootstrap 95% CI [−0.500, −0.381] (10,000 iterations). The measured variable is warm-start positive count, not total activity; no claim about usage frequency is made or licensed. This comparison was granted after the verdict, with its direction, effect-size threshold and reporting rule fixed before any value was computed.
