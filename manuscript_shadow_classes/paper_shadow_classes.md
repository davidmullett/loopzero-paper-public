# Absorbing Shadow Classes in Conjunctive Label Rules

### A control-class contamination in a recursive-recommender benchmark, a protocol that detects it, and a pre-registered null on the repaired instrument

**David Mullett** *Independent researcher* · ORCID 0009-0004-2543-1664 · correspondence: d@loopzero.org

  
  

## Abstract

Benchmarks for early-warning detection in recursive systems label each unit as a degradation case or a control, then ask whether a detector fires before degradation. We show that a natural construction for such a label — declaring degradation only when a run condition co-occurs with an *eligibility* condition — can silently corrupt the control class, and we report what happens when the corruption is repaired.

  

In a MovieLens-25M recommender replay, degradation requires eight consecutive frontier misses **and** a remaining frontier of at least ten items. The eligibility clause is absorbing: once a unit's frontier falls below the floor it can never satisfy the rule again, so units that fail continuously are filed as controls. In the landmark population, 69.2% of controls are frontier-starved and no events are; the "controls" miss a median of 15 of 20 pre-landmark steps against at most 7 for events, making the most natural early-warning statistic anti-informative. A pre-registered learnability gate detected this before any detector result existed. We prove the contamination is structural: because starvation is absorbing, the clean-control set is invariant to the landmark step, so no landmark choice rescues it.

  

Treating starvation as a competing terminal event and restricting the control class accordingly, we then execute a pre-registered evaluation on the purified population. (A conformance audit before execution found four departures of the executed configuration from the registration; an earlier execution, which had halted at its own gate without producing a detector comparison, was vacated and the registered design executed once. All findings are reported.) The gate, which failed before repair, passes after it (TPR 0.561 against a chance rate of 0.05) — the first valid measurement this benchmark has produced. On that instrument the pre-registered slate-structure composite fails all three evaluated criteria: it is *worse* than the best miss-based baseline at every matched budget (ΔTPR = −0.472, CI [−0.496, −0.444] at the primary), and two of its three covariate coefficients are inverted while the set carries substantial incremental discrimination (0.162, CI [0.143, 0.183]).

  

Purification eliminates or reverses the large contaminated-population effects: churn inverts (+2.01 → −0.64), occupancy collapses to null (+0.05), and the outcome-stream quantity reverses *into* the informative direction (−2.62 → +0.81). Coverage alone retains a moderate effect in the hypothesised direction (−0.68): on marginal effects one indicator is inverted, one is null, and one is consistent with the theory. The composite separates pre-landmark starved units from clean controls at d = +4.20: what the contaminated benchmark rewarded was frontier depletion, not early warning.

  

The failure mode is not new: it is an absorbing competing-risk pathology. We repair the binary benchmark by landmarking the at-risk population and excluding subsequent competing-event units from the residual control class. The contribution is its unrecognized instance in algorithmically-labeled benchmark construction, and a detection and audit protocol (a learnability gate plus a shadow-class census) that exposed both the original label pathology and a subsequent nonconformant execution before either could support a detector conclusion.

  

## Part 1 — The benchmark and the claim it was built to test

Recursive systems — those whose current output conditions their future input — recur across recommender systems, model-training loops, and market microstructure. A natural question is whether such systems emit an early-warning signal before they lose the ability to make progress — a signal whose detectability has known limits even in well-characterised dynamical systems (Boettiger and Hastings, 2012). Answering it requires a benchmark: a population of units, each labeled as a degradation case or a control by an operational rule, over which candidate detectors can be compared at matched false-positive budgets.

  

We study one such benchmark: a deterministic offline replay on MovieLens-25M (Harper and Konstan, 2015). Each user is replayed for up to 50 recursive steps through a frozen item-item collaborative-filtering engine. At each step the engine recommends a top-K slate; a "hit" recovers a held-out positive item and appends it to the profile; the user's *frontier* is the set of remaining recoverable positives. A unit is labeled **degraded** when it accrues a run of eight consecutive frontier misses while its remaining frontier is at least ten, within the horizon; otherwise it is a **control**. A prior preprint (arXiv:2606.00329) reported a directional early-warning association on this benchmark using three slate-derived indicators.

  

Two clarifications frame what follows. First, that prior study's specific indicators were subsequently found to be partly coupled to the label rule, which motivated a redefinition. The problem we describe here is deeper and independent of any indicator: it is a defect in how the benchmark constructs its *labels*, and it would compromise any detector, including the strongest imaginable one. Second, and this governs the paper's contribution: **the failure mode is not a new phenomenon.** It is a concrete instance of hazards that are well developed elsewhere: informative censoring and competing risks in survival analysis, depletion of susceptibles and immortal-time bias in pharmacoepidemiology, negative-class contamination in positive-unlabeled learning, and reject inference in credit scoring. Our claim is not phenomenon-novelty. It is that this hazard has an unrecognized and undetected instance in the construction of recursive-recommender benchmarks, that its presence inverts the sign of the most natural early-warning signal, and that a lightweight, pre-registerable protocol detects it before any result is produced. Throughout we use the conservative terms *degradation* and *frontier failure* rather than *collapse*.

  

## Part 2 — The pathology, and the gate that caught it before any result existed

### 2.1 The eligibility conjunct and the absorbing shadow state

The degradation rule is a conjunction. Let m_t be the count of consecutive frontier misses at step t and f_t the remaining frontier size. Degradation is declared at the first step where

  

m_t ≥ 8   AND   f_t ≥ 10.

  

The first clause is the *signal* the benchmark intends to measure. The second is an *eligibility* clause: it restricts labeling to units that still have enough frontier left to fail against. But f_t is monotonically non-increasing — the frontier can only shrink as positives are recovered or the horizon advances — so once f_t falls below the floor of 10, it never returns. Call a unit **starved** at step t if f_t < 10. Starvation is therefore *absorbing*: a starved unit can never again satisfy the eligibility clause, hence can never be labeled degraded, no matter how badly it fails thereafter. It falls out of the "degraded" class and, because the benchmark defines the control class *residually* (everything not degraded), it lands among the **controls**.

  

Figure 1 shows the resulting state structure. This yields a deterministic statement that is the crux of the pathology.

  

![](assets/fig1_absorbing_shadow_state.pdf){width=100%}

**Figure 1.** *The eligibility conjunct creates an absorbing shadow state.* **(A)** The rule sends a unit to *Degraded* only on eight consecutive misses while the frontier is still eligible (f_t ≥ 10); once the frontier falls below the floor the unit is *Starved* — an absorbing state with no exit — and is filed, at the horizon, as a residual control. An outcome no longer ascertainable is not thereby a negative outcome. **(B)** Read at the landmark (t = 20), 69.2% of the nominal control class — 3,292 of 4,755 — is starved-by-the-landmark shadow class, against 1,460 clean controls and 3 post-landmark starvers.

  

**Observation 1 (starvation implies control).** If a unit becomes starved at any time before the horizon without first being degraded, it can never subsequently become an event and therefore enters the residual control class. This includes units already starved at the landmark and units that starve subsequently.

  

An event must satisfy f ≥ 10 at its degradation step. Since f is non-increasing, once a unit is starved (f < 10) it can never again meet the eligibility clause and can never be degraded; not being degraded by the horizon, it is a control by the residual definition. For a unit already starved at the landmark the argument is immediate — it is unlabelable at the landmark; for a unit that starves later it applies from the starvation step onward.

  

The consequence is that the control class does not mean "a healthy user who did not degrade." It substantially means "a user whose frontier ran out — who is failing continuously — and whom the rule is structurally unable to label." The event/control contrast the benchmark presents is not *will-degrade* versus *will-not-degrade*; it is *will-degrade* versus *(will-not-degrade OR cannot-be-labeled)*.

Two terms recur below and are worth fixing precisely. The phrase *shadow class* has unrelated uses in other fields; we use it here in a specific measurement-theoretic sense.

**Definition 1 (shadow class).** Given a population, a target outcome, and a labeling rule, a *shadow class* is a subset of units that (i) remains relevant to the inferential contrast the labels are used to support; (ii) is structurally prevented by the labeling architecture from having the target outcome ascertained — not merely unlabeled empirically, but unlabelable by construction; and (iii) is consequentially treated: omitted, censored, or absorbed into another nominal class in a way that changes inference. All three conditions matter. Eligibility rules legitimately place units out of scope; a shadow class exists only where units relevant to the contrast become structurally unascertainable and their residual treatment changes what the instrument reports. The starved controls of §2.2 satisfy all three: after starvation, degradation status is unascertainable under the rule, and the residual definition converts that unascertainability into a negative label. An outcome that is no longer ascertainable is not thereby a negative outcome.

**Definition 2 (shadow-class census).** The report, prior to any use of the benchmark for inference, of the prevalence and behaviour of each shadow class the label rule induces.

A shadow class in this sense is not a latent class: its membership is exactly identifiable from observables (here, f_t < 10). Nor is it missing data. Three situations should be kept distinct: *data invisibility* — the unit is not observed; *label uncertainty* — the unit is observed but its correct label is unknown; and *shadow-class unascertainability* — the unit is fully observed, every step of its trajectory recorded, while the labeling architecture has made one relevant outcome structurally unreachable. The pathology reported here is the third.

### 2.2 The empirical signature

The contamination is not marginal. Of the 4,755 units the rule files as controls (every unit not labelled degraded through the horizon), read at the landmark step (step 20):

  

  - **3,292 of 4,755 controls (69.2%) are frontier-starved by step 20.** By Observation 1, **0 of 20,265 events are** — verified by direct assertion.
  - The starved controls fail almost continuously: control units miss a **median of 15 of the 20** pre-landmark steps (up to 19). Event units, which by construction have not yet degraded, miss **at most 7 of 20** (median 1).

  

The resulting bias runs in one direction. The most natural early-warning statistic — the early miss rate — is therefore **anti-informative** on this benchmark: the highest-missing units are the controls, not the events. A detector that simply reads "who is missing a lot early" ranks the controls above the events. And because any indicator computed from the recommendation stream is downstream of the same frontier mechanics, an indicator can partially recover the label's mechanical structure — *who is starved* — with no early-warning content whatsoever. The benchmark measures the wrong quantity, and therefore presents a corrupted target to any detector evaluated against these labels.

  

A separate quantity shows the importance of warning runway: of 35,584 whole-horizon events, only 20,265 remain event-free and eligible at step 20 — **43% had already degraded**, with no runway over which a step-20 warning could have been assessed. These early events are labeled, not shadow-class members; they are excluded by standard landmark logic.

### 2.3 A reductio via a random recommender

The pathology is a property of the *label rule's interaction with the engine*, not of any particular recommender. Replace the collaborative-filtering engine with a uniform-random recommender and drive the *same* frozen replay rules over the *same* users: the population and their rating histories are unchanged, and only the engine differs. A random recommender draws a ten-item slate from the full unseen catalogue, so frontier recovery is rare by construction: essentially every eligible user accrues eight consecutive misses within the first several steps and is labelled degraded immediately. Because degradation before the landmark removes a unit from the analysis population, the landmark population under this engine is empty — literally so on the pre-registered degeneracy probe, which admitted **0 of 3,000 users**, with 63.5% excluded for collapsing before the minimum warning runway.

  

That the users are held fixed is what makes this an invalidity rather than a sensitivity. A metric may legitimately vary with the quality of the system it measures. But the construct here claims to describe *users*, and the same users move from a fifth of the horizon population being labelled to essentially all of them, on an engine swap alone.

  

The label nominally measuring *user degradation* therefore fires on essentially everyone the moment the engine stops being a competent recommender. That is difficult to reconcile with a construct supposed to measure a property of users, and it is near-dispositive evidence that the construct is substantially engine-recovery behaviour rather than a user property.

### 2.4 Detection: a learnability gate, evaluated before any decision quantity

The reason this pathology is reported here rather than discovered by a reviewer is that the evaluation was pre-registered (OSF) with a **learnability gate** placed upstream of the detector comparison. The gate asks a prerequisite question: at the primary false-positive budget, does the simplest label-derived signal — the early miss rate — separate events from controls above chance? Functionally this is a prerequisite-direction test: the outcome is defined through runs of misses, so the simplest outcome-adjacent observable must not have its direction structurally reversed by the negative class. On the contaminated population it does not; its true-positive rate is zero at the operating point, its confidence interval excluding zero on the wrong side. Under the frozen protocol, a learnability-gate failure routes the study to *uninterpretable-by-construction*: the detector results are reported but carry no evidential weight, because the population cannot distinguish "no early-warning signal" from "a label whose control class is contaminated." The gate is evaluated *before* any detector-versus-baseline decision quantity is computed, so the finding cannot be a post-hoc rationalization of an unwelcome result. The gate blocked interpretation of detector results until the directional contradiction in the benchmark had been resolved.

  

## Part 3 — The contamination is structural, and how to build a benchmark that avoids it

A natural hope is that the contamination can be tuned away — for instance by moving the landmark earlier, so that fewer units have starved by the time labels are read. It cannot. The following makes that precise.

  

**Proposition 2 (landmark invariance).** Define a *clean control* as a unit that is neither degraded nor starved through the horizon T. The set of clean controls is invariant to the choice of landmark step. Consequently, no landmark choice can increase the number of usable controls: their scarcity is a structural property of the (floor, horizon, engine) triple, not of the evaluation design.

  

*Proof.* Both predicates defining a clean control — "never degraded by T" and "never starved by T" — are evaluated over the full horizon and are functions of the unit's trajectory alone. The landmark step determines only the window over which indicators are computed and the point after which labels are read; it does not alter any trajectory or its terminal classification. Hence the clean-control set is identical for every landmark. Because starvation is absorbing, an earlier landmark cannot rescue a unit that will starve later: changing the landmark while holding T fixed cannot alter whether a trajectory subsequently starves by T. ∎

  

The corollary is the design lesson: **an eligibility conjunct with a monotone, absorbing bound cannot yield a valid residual control class, and no downstream analysis choice repairs it.** The fix must be made at construction time. We give a specification for a benchmark of this family that can support early-warning evaluation:

  

1.  **Decouple eligibility from labelability.** Remove the absorbing shadow state — for example, a *replenishing* frontier (a rolling window of upcoming positives) so that no unit is permanently barred from being labeled, and failure is always measurable against a live frontier.
2.  **Define the control class positively, never residually.** A control should be a unit that demonstrably *sustains recovery capability* through the horizon, not merely a unit the rule failed to label.
3.  **Require a shadow-class census for any conjunctive label rule.** Every eligibility condition partitions the population into labelable and unlabelable units. Not every unlabelable stratum is pathological — rules may legitimately place units out of scope — but wherever the three conditions of Definition 1 co-occur, the benchmark must report the size and behaviour of the shadow class, because that is where residual contamination hides.
4.  **Engineer prevalence at construction.** Fix a minority-class floor (e.g. ≥ 15%) so that the interesting class is neither degenerate nor overwhelming, rather than accepting whatever prevalence the rule happens to produce.
5.  **Ship a learnability gate as a required validation artifact.** The prerequisite check — can the simplest label-derived signal beat chance? — should be part of releasing the benchmark, not an optional downstream analysis.

  

**Relation to prior work.** The statistical phenomenon reported here is not new. Observation 1 describes an absorbing competing-risk pathology, a hazard with a five-decade literature in survival analysis, and we claim no priority over it. Starvation and degradation are competing terminal events. The benchmark's error is to collapse the starvation event into the residual negative class rather than represent it as a competing outcome. When starvation is instead treated as if it conveyed ordinary non-event status, the resulting analysis has the same inferential pathology that motivates competing-risk methods, for which Putter, Fiocco and Geskus (2007) is a standard tutorial and Fine and Gray (1999) one canonical treatment. The remedy we adopt is equally standard and equally not ours: restricting analysis to a landmark population is landmark analysis (Anderson, Cain and Gelber, 1983; van Houwelingen, 2007), and Proposition 2 is a statement about why landmarking cannot rescue this particular construction rather than a novel method.

  

Three further literatures stand in weaker relations. Reject inference is the closest structural analogue: there, as here, labels exist only conditional on a gate operated by the system under evaluation (Hand and Henley, 1997; Crook and Banasik, 2004). Positive-unlabeled learning is an inverted analogue — its unlabeled class hides positives, whereas ours hides the worst failures by rule (Elkan and Noto, 2008; Bekker and Davis, 2020). And the eligibility-bias cluster in pharmacoepidemiology — depletion of susceptibles (Moride and Abenhaim, 1994), immortal-time bias, collider stratification (Suissa, 2008; Hernán et al., 2004) — is the direct epidemiological cousin, differing in substrate rather than in mechanism.

  

One demarcation matters before it is blurred. The offline-evaluation biases familiar in recommender research — exposure bias and missing-not-at-random feedback (Marlin and Zemel, 2009; Steck, 2013), and closed-loop contamination from prior recommendation policies (Chaney, Stewart and Engelhardt, 2018) — are properties of how the data were collected. The pathology here lives in the definition of the label itself, and would persist under perfectly collected data.

  

Our contribution is the location of this hazard and a means of detecting it. What appears to be unrecognized is that it is latent in recursive-recommender degradation benchmarks whose labels are algorithmically defined rather than observed; that it inverts the sign of the most natural early-warning statistic, so that the contamination is invisible in every summary the benchmark reports; and that a pre-registered learnability gate together with a shadow-class census detects it cheaply, before any result exists. That places the work in the benchmark-construct-validity literature (Raji et al., 2021; Jacobs and Wallach, 2021) rather than in survival analysis: the statistics are borrowed, the measurement problem is the finding. The gate and the census are what we offer for reuse.

  

## Part 4 — The corrected study, as executed

**Statistical procedures.** Effect sizes are Cohen's *d*; the contaminated and purified columns of §4.4 report each indicator's event-versus-control separation before and after competing-risk purification of the control class, and the mechanical Δd for each indicator is their difference — the registered contrast between its contaminated- and purified-population effect sizes. The separate bounding diagnostic of §4.4 contrasts controls starved by the landmark against clean controls (|d| = 5.6–6.1). Interval estimates are bias-corrected and accelerated bootstrap intervals (BCa; Efron, 1987), resampled over the clustering unit wherever a statistic pools across units. Detectors are compared at matched control-alarm counts rather than at fixed score thresholds — k = {15, 38, 77, 153} at the four registered budgets — so every comparison sits at an identical false-positive count, with the operating point taken as the largest matched alarm count not exceeding the budget. The z-standardisation parameters for all indicators are estimated once on the 694 calibration-fold clean controls and applied unchanged out of fold.

### 4.1 What was corrected, and what was audited

Study 1's benchmark could not support the measurement it was built for. Study 2 was pre-registered (OSF, osf.io/wka72) as its repair: starvation is treated as a competing terminal event, the control class is restricted to units that neither degrade nor starve through the horizon, and every downstream quantity — indicator normalisation, matched alarm budgets, covariate adjustment — is computed against that purified population. The analysis plan, the four acceptance criteria, and the response to each possible verdict were all fixed before the clean-control census existed.

  

One methodological point should be stated exactly. Landmarking defines the at-risk population at L; the repair here additionally treats subsequent starvation as a competing terminal event and excludes that stratum from the residual control class, which goes beyond landmark analysis proper. The repaired benchmark's estimand is therefore: among units event-free and eligible at the landmark, does a detector distinguish subsequent degradation from sustained non-degradation-and-non-starvation through the horizon?

  

Between registration and execution, an exhaustive conformance audit of the executed configuration against the registration returned thirty of thirty-four parameters conformant and four departures: three arithmetic divergences in registered quantities — the analysis population filter, the matched-alarm budget grid, and a pre-census table inheriting the same denominator error — and one labelling defect, since corrected. All four share one root cause: configuration constants transcribed from the Study 1 registration rather than the operative Study 2 one. A parallel sweep found three artifact writers absent from the versioned tree; each was committed, and its artifact content-verified or canonically re-derived to byte identity. Three further findings, detailed in the supplement, concerned input provenance and the completeness of a process attestation.

  

Each finding was recorded in the deviations log before it was investigated. The provenance chain is content-pinned end to end, from the published source-dataset hash through the derived panel, the clean-control census and the covariate cache, to the verdict artifact.

  

Two of the divergences invalidated an earlier execution, which ran on a population appearing in no registered analysis. **That execution had halted at its own learnability gate and produced no detector comparison; vacating it overturned no result.** Its record is retained and its verdict vacated. **The analysis reported below is the first execution of the registered design.**

### 4.2 The repaired instrument measures

Before any detector comparison, the pre-registered protocol evaluates a learnability gate: on the analysis population, does the most direct label-derived signal — the early miss rate — separate events from controls above the matched-budget chance rate? On Study 1's contaminated population it did not, which is what routed that study to *uninterpretable*.

  

On the purified population it does. The gate passes with a true-positive rate of **0.561, BCa 95% CI [0.549, 0.574]** at the primary budget, against a chance rate of 0.05 — an excess over chance of 0.511 [0.499, 0.524].

  

We report this as a primary result. It establishes that competing-risk purification, applied to a benchmark exhibiting the shadow-class pathology, recovers a population that supports the registered binary early-warning contrast — a single-instance demonstration that the repair works, on the benchmark where the pathology was found.

  

The remaining gates pass likewise: the liveness check on indicator distributions, and the power gate at 10,153 evaluation-fold events against a floor of 200.

  

Analysis population: 20,265 events and 1,460 clean controls, split 694 calibration and 766 evaluation by the pre-registered seedless hash rule. Matched alarm counts at the registered budgets {0.02, 0.05, 0.10, 0.20} are k = {15, 38, 77, 153}.

### 4.3 Verdict: the signal dies

The pre-registered composite is S = z(G) + z(p) − z(δ), evaluated out of fold at matched control-alarm counts against six baseline families and the early-miss-rate reference. Three of the four acceptance criteria are evaluated and all three fail; the fourth, which concerns mechanism specificity of a detected signal, is not reached.

  

**Criterion 1 — discrimination advantage at the primary budget.** Required: ΔTPR ≥ 0.05 with a cluster-aware BCa interval excluding zero. Observed: **ΔTPR = −0.472, CI [−0.496, −0.444]**. The composite does not fall short of the bar; it is substantially worse than the best baseline, with the entire interval on the opposite side of zero.

  

**Criterion 2 — sign consistency across budgets.** Required: positive at three of four. Observed: negative at four of four — **−0.503, −0.472, −0.436, −0.386** at b = {0.02, 0.05, 0.10, 0.20}. The disadvantage is monotone in budget and never approaches parity.

  

**Criterion 3 — covariate adjustment.** Required: coefficient signs in the hypothesised directions (bG > 0, bp > 0, bδ < 0) and incremental AUC ≥ 0.02 over the covariates alone. Observed:

  

|  |  |  |  |  |
| :-: | :-: | :-: | :-: | :-: |
| **coefficient** | **estimate** | **BCa 95% CI** | **required** | **met** |
| bG (churn) | −0.475 | [−0.635, −0.313] | > 0 | no |
| bp (occupancy) | −0.419 | [−0.512, −0.328] | > 0 | no |
| bδ (coverage) | −0.538 | [−0.691, −0.385] | < 0 | **yes** |

  

Incremental AUC = **0.162, CI [0.143, 0.183]** — eight times the required floor. The criterion fails on the two inverted coefficients.

  

Two things follow. The indicators carry considerable discriminative information beyond the covariates, and for two of the three the relationship runs opposite to the hypothesis. But the coverage coefficient satisfies its registered direction with an interval clear of zero. The criterion's failure is not uniform, and reporting it as uniform would misdescribe the result.

  

Two frames must be kept distinct when counting. In the **joint model** two coefficients are inverted and one is consistent. On **marginal effects** (§4.4) one indicator is inverted, one is null and one is consistent. Occupancy illustrates why the frames differ: its marginal effect is +0.05, effectively null, while its partial coefficient is −0.419 with an interval clear of zero. Partial and marginal effects can legitimately diverge under shared variance, and that divergence is expected here rather than anomalous.

  

The predictors are correlated but not severely so: on the standardisation population the variance inflation factors are approximately 3.5 for churn, 3.3 for coverage and 1.3 for occupancy — moderate by conventional standards, and not high enough to render the estimates unstable. We therefore let the coefficients stand as reported. What this implies for the theory: bG at −0.475 with a clean interval and a moderate VIF is a robust inverted partial effect, which is more damaging to the hypothesis than an unstable one would be.

  

**We do not fit a re-signed composite.** Inverted coefficients invite the obvious follow-up — a composite with the signs corrected to match the data. Under the registration that is a post-hoc hypothesis constructed after seeing the result, and it is foreclosed. We publish the incremental AUC of 0.162 as the constraint any future, separately registered hypothesis would have to respect, and pursue nothing further here.

  

In absolute terms the composite reaches a matched true-positive rate of **0.089** at the primary operating point — against a chance rate of 0.05, and against **0.561** for the best baseline. Figure 3 shows the discrimination gap at all four budgets.

  

![](assets/fig3_delta_tpr_by_budget.pdf)

**Figure 3.** *Discrimination advantage at matched alarm budgets.* Composite minus best baseline (ΔTPR) at the four registered budgets, with cluster-aware BCa 95% intervals; the parity (ΔTPR = 0) and acceptance (ΔTPR ≥ 0.05) lines are marked. Every point is negative with its interval clear of zero — the composite is strictly worse than the best miss-based baseline at every budget.

  

The baseline set is narrower than it looks. Five of the seven comparators — the early-miss reference, variance EWS, CUSUM, Page–Hinkley and matrix profile — achieve *identical* matched true-positive rates of 0.561. All are computed from the same derived miss-run series, and at matched alarm counts they select the same units. They are therefore not seven independent baselines but essentially two: a miss-based family and permutation entropy, the latter below chance at 0.041 — under the 0.05 matched-budget chance rate here, and under the matched chance rate at all four budgets (0.016, 0.041, 0.093, 0.183 against 0.02, 0.05, 0.10, 0.20), so its sub-chance behaviour is consistent across budgets rather than a single-budget artifact. This weakens the "best of six families" framing while leaving the comparison itself intact, since the composite loses to the miss-based family by a wide margin however that family is counted.

### 4.4 Characterisation

Six pre-registered analyses and one post-verdict descriptive comparison characterise the result. The scope of the six was fixed and anchored before the sealed decision quantities were opened. The seventh was granted afterwards under the same default-denied mechanism, with its interpretive rule and reporting threshold fixed and anchored before its values existed; it is identified as such below.

  

**The apparent Study 1 signal was contamination.** All four indicators show large effects on the contaminated population. Purification removes or reverses every one of them (Figure 2):

  

|  |  |  |  |
| :-: | :-: | :-: | :-: |
| **indicator** | **contaminated** | **purified** | **mechanical Δd [95% CI]** |
| G (churn) | +2.01 | **−0.64** | 2.65 [2.55, 2.74] |
| p (occupancy) | −2.25 | **+0.05** | −2.30 [−2.39, −2.20] |
| δ (coverage) | +2.00 | **−0.68** | 2.68 [2.58, 2.78] |
| miss-run fraction | −2.62 | **+0.81** | −3.43 [−3.55, −3.32] |

  

![](assets/fig2_bounding_diagnostic.pdf)

**Figure 2.** *Every large contaminated-population effect is mechanical.* Paired Cohen's d for all four indicators on the contaminated population (vermillion circles, vs all controls) and the purified population (ink squares, vs clean controls); each large contaminated effect collapses toward zero or reverses under purification.

  

Two distinct frames must be kept apart here, and conflating them would misstate the result. Relative to the *contaminated* values, all four quantities change substantially: G and δ invert, p collapses, and the miss-run fraction reverses. Relative to the *hypothesis*, the picture is not uniform. The theory predicted G high, p high and δ low in events. On the purified population G is inverted (−0.64), p is null (+0.05), and **δ is in the predicted direction (−0.68)**. The miss-run fraction's reversal runs the other way again — from anti-informative on the contaminated population to informative on the purified one, the same flip the learnability gate shows.

  

So one of the three registered slate indicators retains a moderate effect consistent with the hypothesis.

  

The mechanical component of the shift has a cluster-bootstrap interval excluding zero for all four quantities. The contrast against the starved stratum identifies what the contaminated effects were tracking. In this bounding diagnostic — evaluation-fold starved controls against clean controls — the slate indicators reach |d| of 5.6 to 5.7 and the miss-run fraction 6.1. (This is a distinct comparison from the pre-landmark probe reported next, and its d range should not be merged with that one.)

  

**And the mechanism is visible directly.** In the pre-landmark starvation-concurrence probe — controls starved by the landmark (n = 3,292) against clean controls (n = 1,460), indicators taken over steps 1–20 — the composite separates them at **d = +4.20**, with individual indicators from −5.77 to +6.29. The composite is, in substantial part, a frontier-depletion detector. In the contaminated population that is exactly what it was rewarded for detecting; purification removes the thing it was reading.

  

**The null is robust to landmark choice.** Repeating the full primary analysis at landmarks 15 and 25: criteria 1 and 2 fail at every landmark; criterion 3 fails at 20 and 25 and is coverage-limited at 15 (58.65% covariate coverage, declared before computation).

  

**The indicators are substantially correlated.** On the standardisation population — the 694 calibration-fold clean controls from which the z-parameters derive — the pairwise correlations are r(G, δ) = **0.833**, r(G, p) = **−0.478**, r(p, δ) = **−0.415**. The composite's three terms are therefore not three independent axes, though neither are they a single quantity measured three times.

  

The population matters here. Computed instead on the full evaluation-fold arm, which includes events and starved controls, the same correlations are far higher (0.975, −0.869, −0.869). That inflation is itself attributable to the contamination: the starved stratum carries extreme indicator values, and its presence drives the indicators into apparent lockstep. Label contamination changed not only estimated discrimination but the apparent covariance structure of the proposed measurement instrument. The values reported above are those on the population where standardisation is defined.

  

The generalisable point follows. **Feature geometry estimated on a population whose labels have not been validated inherits the contamination.** Any composite, index, factor structure or weighting scheme designed from such correlations is designed on an artifact — here, a difference between 0.975 and 0.833 that would materially change how one reasons about the feature space. Taken with the label itself and the effect sizes, the same contamination has now been shown to corrupt three distinct layers of the analysis.

  

**The composite carries nothing on severed arms.** Absolute discrimination against chance, reported unconditionally under the pre-registered protocol, exceeds chance on **zero of six** control arms in which the recursive personalisation mechanism is disabled. Four arms are significantly below chance; on two of the shuffled-timestamp arms the interval includes zero, so those are indistinguishable from chance rather than below it.

  

**Frontier headroom does not localise the null.** Events with remaining frontier above the eligibility threshold reproduce the primary result (**ΔTPR = −0.470**); the narrow-headroom stratum contains 38 events and is reported as underpowered rather than estimated.

  

**Who the label discards** *(the post-verdict comparison)*. Starvation is absorbing and never co-occurs with an event: **zero of 20,265 events** cross the eligibility floor before collapse, confirming Observation 1 empirically. The discarded stratum is not a random sample of users — those excluded have thinner early positive histories than clean controls (**d = −0.441, CI [−0.500, −0.381]**), a moderate association. This comparison was granted after the verdict, with its direction, effect-size threshold and reporting rule fixed and anchored before any value was computed. The measured variable is warm-start positive count, not total activity; no claim about usage frequency is made or licensed, and no other covariate was compared.

  

Three registered analyses were not run and are reported with their reasons: the matrix-factorisation and sequential control engines existed to establish mechanism specificity of a detected signal, and none was detected; the random-engine re-run is moot, its degeneracy being the result itself; and the starvation-discrimination diagnostic as originally framed is vacuous by population fact, with three within-window starvers against 1,460 clean controls.

  

## Part 5 — What this shows

### 5.1 Conflation, separation, and what remains unexplained

**The label conflated two signals.** One was mechanical — the interaction between the recommender and a depleting frontier, which the composite detects at d = +4.20 and which the eligibility conjunct silently promoted into the control class. The other was a genuine early-warning signal in the outcome stream, which becomes informative once purification removes the contamination and which drives the learnability gate. In the contaminated benchmark these were welded together, and the apparent success of the slate composite was almost entirely the first.

  

**A first-order consistency check explains the near-cancellation:** Combining the purified marginals as the registered composite combines them — z(G) + z(p) − z(δ) — gives (−0.64) + (+0.05) − (−0.68) ≈ +0.09, against a composite standard deviation of √(3 + 2[r(G,p) − r(G,δ) − r(p,δ)]) = √1.208 ≈ 1.10. The inverted churn term approximately cancels the coverage term it is subtracted from, the null occupancy term carries the remainder, and the net standardised separation is roughly 0.08. That is near chance, and it is consistent with the observed matched true-positive rate of 0.089 against a chance rate of 0.05. The figure is approximate: it treats the marginal effect sizes as though pooled-SD standardised.

  

So the composite's failure is arithmetically consistent with its own components. **What we do not explain is why churn inverts on the purified population at all.** That is the deeper question, and this design cannot answer it; we decline to speculate.

  

What the result establishes is narrower. On this benchmark, at this landmark, the registered composite carries no usable early-warning signal; on marginal effects one component points in the predicted direction, one is null and one is inverted; and the outcome-stream quantity the design treated as a baseline outperforms all of them.

  

The single sentence: **On this benchmark, the outcome-stream baseline carries substantially more early-warning information than the registered slate-structure composite — and the theory placed its signal on the wrong side of the instrument.**

### 5.2 What the repair validated, and what remains proposed

Three elements of the §3 specification were exercised in this case: competing-event purification restored the intended binary contrast; the shadow-class census exposed the magnitude and behaviour of the excluded stratum; and the pre-registered gate confirmed that the repaired population recovers the required directional prerequisite. The gate's passing on the purified population, having failed on the contaminated one, is direct evidence for the first two and a demonstration of the third.

  

Two elements remain proposed rather than validated: the replenishing frontier and engineered minority-class prevalence. Their necessity is partially evidenced — the invariance result shows that no landmark choice rescues a construction with an absorbing eligibility bound, which is the argument for decoupling eligibility from labelability at construction time. Their sufficiency is untested here, because the repair adopted was purification of an existing benchmark rather than construction of a new one.

  

The distinction matters for anyone adopting the specification: the diagnostic half was exercised and demonstrated in this instance, the constructive half is proposed.

### 5.3 What the negative does and does not establish

The pre-registered composite showed no advantage over miss-based baselines at matched alarm budgets, no consistent sign across budgets, and no incremental discrimination in the hypothesised direction — on this benchmark, this engine family, this horizon, and this landmark, robust across two alternative landmarks.

  

That is decisive against the registered hypothesis. It is not a demonstration that no slate-derived statistic could carry early-warning information in any recursive recommender. Three limits on the claim:

  

The composite was pre-specified, not searched. Its three terms proved to be substantially correlated rather than independent; a different construction is not tested here and is not excluded by this result.

  

The population is definitionally restricted. Units that starve before the landmark are unlabelable by construction in this benchmark family — nothing about the composite was measured on them and nothing could be, under any design in this family. This is a scope statement, not a qualification of the verdict, and it is one the specification already makes.

  

The setting is one offline replay, one item-item collaborative-filtering engine family, one dataset. Cross-domain generalisation was never tested and is not claimed.

### 5.4 Implications for benchmark construction

**The prescriptions below apply to algorithmically labeled benchmarks in which an eligibility condition can render the target outcome structurally unascertainable while the residual class remains inferentially active.** Any conjunctive label rule containing an eligibility condition should be audited for that possibility: audit broadly, claim pathology narrowly.

  

First, any such evaluation should publish a shadow-class census: the size and behaviour of the population the rule renders unlabelable. In the case reported here that population was 69% of the nominal control class and was failing roughly twice as often as the labelled failures. No summary statistic the benchmark reported revealed it.

  

Second, label validity should be established *before* the feature geometry used to design an instrument is estimated. Correlations, factor structures and composite weightings computed on an unvalidated-label population inherit whatever contamination that population carries; the difference reported in §4.4 between 0.975 and 0.833 is a demonstration of the size such an artifact can reach. Designing a detector on the first figure would have produced a different and wrong understanding of the feature space: once the class ontology is wrong, feature selection and composite construction performed downstream inherit that error before any detector is evaluated.

  

Third, a learnability gate should be a release artifact rather than an optional downstream analysis. The check is cheap — can the most direct label-derived signal beat chance on this population? — and its failure flags that a null detector result cannot safely be interpreted as absence of early-warning information until label validity is investigated. In this project the same gate produced both answers on the same benchmark, before and after repair.

  

A more general observation follows from the audit rather than the experiment. Conformance between a registration and its executed configuration is not established by the existence of a registration. Three of the four departures found here were arithmetic divergences in registered quantities, all traceable to constants transcribed from the wrong document; none would have been visible in any reported result. Machine-checkable registration parameters, asserted against configuration at run time, would have caught all three.

### 5.5 The status of the question

The hypothesis that slate-structure statistics carry early warning of recursive degradation has been tested once, on a valid instrument, and failed on its own pre-registered terms.

  

The broader question — whether early warning is achievable in recursive recommender systems — is not answered by this work. Answering it requires a benchmark built to the constructive half of the specification, or a live system, and the analysis reported here places the constraint precisely: the present results point future work toward the outcome stream and toward candidate quantities whose independence from frontier depletion can be demonstrated.

A further extension, not attempted here, is a taxonomy of shadow classes across label architectures: the absorbing variety studied here is one type; the gated labels of reject inference suggest another. The census of Definition 2 generalises accordingly.

### 5.6 Limitations

The benchmark is a deterministic offline replay, not a deployed system with feedback. The engine family is item-item collaborative filtering; the two mechanism-control engines that would have characterised alternative families were not run, because their registered purpose was to establish specificity of a detected signal and none was detected. The covariate set is fixed at two pre-registered variables.

  

The baseline set is less independent than its nomenclature suggests. Five of the seven comparators are computed from the same derived miss-run series and return identical matched true-positive rates; only one comparator is genuinely distinct, and it performs below chance. A stronger evaluation would draw baselines from structurally different signal families rather than from transformations of a single series. The verdict does not turn on this: the composite's *absolute* matched true-positive rate is 0.089 against a chance rate of 0.05, so no baseline set of any diversity would have rescued it. Effect sizes on the discarded stratum are descriptive and were computed under a scope granted after the verdict, with the interpretive rule fixed before the values existed.

  

The instrument now measures. What it measures is one narrow question, and the answer is no.

  

## References

*All entries verified against source (2026-07-22; additions verified 2026-08-14).*

  

Anderson, J. R., Cain, K. C., and Gelber, R. D. (1983). Analysis of survival by tumor response. *Journal of Clinical Oncology* 1(11), 710–719.

  

Bekker, J. and Davis, J. (2020). Learning from positive and unlabeled data: a survey. *Machine Learning* 109(4), 719–760. doi:10.1007/s10994-020-05877-5

  

Boettiger, C. and Hastings, A. (2012). Quantifying limits to detection of early warning for critical transitions. *Journal of the Royal Society Interface* 9(75), 2527–2539. doi:10.1098/rsif.2012.0125

  

Chaney, A. J. B., Stewart, B. M., and Engelhardt, B. E. (2018). How algorithmic confounding in recommendation systems increases homogeneity and decreases utility. *RecSys '18*.

  

Crook, J. and Banasik, J. (2004). Does reject inference really improve the performance of application scoring models? *Journal of Banking & Finance* 28(4), 857–874. doi:10.1016/j.jbankfin.2003.10.010

  

Efron, B. (1987). Better bootstrap confidence intervals. *Journal of the American Statistical Association* 82(397), 171–185. doi:10.1080/01621459.1987.10478410

  

Elkan, C. and Noto, K. (2008). Learning classifiers from only positive and unlabeled data. In *Proceedings of the 14th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD '08)*, 213–220.

  

Fine, J. P. and Gray, R. J. (1999). A proportional hazards model for the subdistribution of a competing risk. *Journal of the American Statistical Association* 94(446), 496–509.

  

Hand, D. J. and Henley, W. E. (1997). Statistical classification methods in consumer credit scoring: a review. *Journal of the Royal Statistical Society: Series A* 160(3), 523–541.

  

Harper, F. M. and Konstan, J. A. (2015). The MovieLens datasets: history and context. *ACM Transactions on Interactive Intelligent Systems* 5(4), Article 19. doi:10.1145/2827872

  

Hernán, M. A., Hernández-Díaz, S., and Robins, J. M. (2004). A structural approach to selection bias. *Epidemiology* 15(5), 615–625.

  

Jacobs, A. Z. and Wallach, H. (2021). Measurement and fairness. In *Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency (FAccT '21)*, 375–385. doi:10.1145/3442188.3445901

  

Marlin, B. M. and Zemel, R. S. (2009). Collaborative prediction and ranking with non-random missing data. *RecSys '09*.

  

Moride, Y. and Abenhaim, L. (1994). Evidence of the depletion of susceptibles effect in non-experimental pharmacoepidemiologic research. *Journal of Clinical Epidemiology* 47(7), 731–737. doi:10.1016/0895-4356(94)90170-8

  

Putter, H., Fiocco, M., and Geskus, R. B. (2007). Tutorial in biostatistics: competing risks and multi-state models. *Statistics in Medicine* 26(11), 2389–2430. doi:10.1002/sim.2712

  

Raji, I. D., Bender, E. M., Paullada, A., Denton, E., and Hanna, A. (2021). AI and the everything in the whole wide world benchmark. In *NeurIPS Track on Datasets and Benchmarks*. arXiv:2111.15366

  

Steck, H. (2013). Evaluation of recommendations: rating-prediction and ranking. *RecSys '13*.

  

Suissa, S. (2008). Immortal time bias in pharmacoepidemiology. *American Journal of Epidemiology* 167(4), 492–499. doi:10.1093/aje/kwm324

  

van Houwelingen, H. C. (2007). Dynamic prediction by landmarking in event history analysis. *Scandinavian Journal of Statistics* 34(1), 70–85. doi:10.1111/j.1467-9469.2006.00529.x

  

**Citation integrity.** Every listed reference carries a specific in-body citation, and every author–year citation in the text resolves to a listed entry — including the §3 pharmacoepidemiology attributions (Suissa, 2008; Hernán et al., 2004). No orphans in either direction.

  

## Data, code and pre-registration availability

Study 1 pre-registration: OSF osf.io/7bvgz. Study 2 pre-registration: OSF osf.io/wka72. Source data: MovieLens-25M, GroupLens Research, verified against the published distribution hash. Analysis code, frozen configuration, complete deviations log, and hash manifests: https://github.com/davidmullett/loopzero-paper-public. Derived panels are embargoed pending release; their content hashes are published in the input manifest and released artifacts verify against them.

  

## Competing interests

The author is the founder of Loopzero, Inc., which has filed a U.S. provisional patent application (No. 64/042,661, filed April 17, 2026) covering monitoring and verification methods related to the subject matter of this work; the author is the named inventor. The author declares no other competing interests.

  

## APPENDIX — Notes for revision (not for the manuscript)

### Hostile review, second pass — status

Second adversarial review received 2026-07-22 against the same eight-axis rubric. Delta: specialist credibility 3 → 7, mathematical seriousness 2 → 6, empirical seriousness 4 → 8, novelty 3 → 6, submission readiness 2 → 6, AI-writing risk 8 → 6 (unvoiced scaffold; 3 projected post-voicing), hostile-reviewer rejection 90–95% → 40%. The rejection memo the reviewer would now write asks for **scope**, not integrity.

  

**A-fixes implemented in this revision:**

  

  - **A-1** — the δ asymmetry. The draft had claimed purification "reverses or eliminates every indicator effect." It does not: δ's purified marginal (−0.68) and its coefficient (−0.538, CI [−0.691, −0.385]) are both in the hypothesised direction. Corrected in the abstract, §4.3, §4.4 and §5.1.

  

**Supplement requirement.** The conformance narrative in the supplement must include D-43 and D-44, so that the abstract's scoped count of pre-execution departures and the full deviations log cannot be played against each other by a reader who finds one and not the other.

  

**Withdrawn after A-1: the geometric-infeasibility argument.** A revision briefly advanced the claim that r(G, δ) = 0.975 made the registered signature unrealisable, with a variance decomposition putting 95% of the composite's variance in the occupancy term. Verification established that the correlation matrix had been computed on the full evaluation-fold arm (n = 12,606) rather than on the 694 calibration-fold clean controls that define the z-parameters — a conformance deviation from the ruled Phase 4 scope. Recomputed on the correct population, r(G, δ) = **0.833**, not 0.975; the pre-committed threshold fired REVERT, and the argument was withdrawn rather than qualified. The inflation was itself a contamination artifact: the starved stratum's extreme indicator values drive the apparent lockstep. §5.1 now declines to offer a complete mechanistic account of the null. Logged as D-43 (added), D-44 (withdrawn), and the remedy anchored separately.

  

  - **A-2** — §4.1 compressed to \~150 words, with the load-bearing sentence added: the vacated execution halted at its own gate and produced no detector comparison, so vacating it overturned no result. Three findings moved to supplement.
  - **A-3** — bδ now reported, collinearity noted, and the decline to fit a re-signed composite stated explicitly with its reason.
  - **A-4** — three recsys citations added to the demarcation; Efron alphabetised; a citation-integrity checklist added above.
  - **A-5** — §2.3's unbacked catalogue arithmetic removed. The "roughly 40,000" figure was anchored nowhere and the derived probability was wrong by an order of magnitude (10/40,000 = 0.025%, not 0.5%). The empirical degeneracy result carries the argument without it; the undefined runway filter is cut.

  

**B-fixes implemented:** abstract discloses the vacated execution; the 0.089-absolute inoculation added to the baseline limitation; Proposition 1 demoted to Observation 1 and its statement tightened; "first valid measurement" now appears once; §5.4 leads with the class claim; six banned constructions removed.

  

**B-fixes outstanding:** a short statistical-procedures paragraph (d definition and populations per column, BCa with the Efron citation, tie-breaking, z-source); the S1 gate described in registered rather than Study-2 vocabulary; a significance clause on permutation entropy's 0.041; the two starved-stratum ranges labelled to distinguish the comparisons.

### Still missing before submission

  - **Abstract.** Now \~390 words. Fine for arXiv; several journals cap at 250.
  - **Venue list** should add NeurIPS Datasets & Benchmarks — per the reviewer, precisely this genre, and where the Raji citation lives. Order: TORS, NeurIPS D\&B, R. Soc. Open Sci. Mainline RecSys is roughly a coin-flip on desk. Avoid KDD-class.
  - **Affiliation line** and correspondence address.
  - **OSF embargoes must be lifted** before submission — the paper's central credibility claim is that the analysis was registered before the data could vote, and a reader cannot verify that against a private registration.
  - **The voicing pass**, which is the only substantial work remaining.

### The residual kill vector

Per the reviewer: *one benchmark, your own, n = 1.* The generalisation from a single artifact's defect to a class is asserted rather than surveyed. The defence is §5.4's class claim, now moved to the front of that section. The durable fix is demonstrating the census on one external benchmark — which is a co-author's natural contribution, and the strongest single thing that could be added to this paper.

### Five sentences that must not drift during voicing

1.  The apparent Study 1 signal was contamination — **reversal**, not attenuation (2.01 → −0.64).
2.  d = +4.20 is evidence **against** the composite. It only ever appears in a sentence naming what it detects.
3.  The specification's diagnostic half is validated; its constructive half is proposed.
4.  "Thin early positive history," never "rarely used the service."
5.  **δ's purified effect and coefficient are both in the hypothesised direction.** Never write that purification reversed every indicator, or that all three registered signs failed. Two failed; one held. This is the axis on which the paper can overclaim a negative, and it already did once.
6.  **The correlations are r(G, δ) = 0.833, r(G, p) = −0.478, r(p, δ) = −0.415**, on the 694 calibration-fold clean controls. Never cite the evaluation-arm values (0.975, −0.869, −0.869) as the paper's finding — they were computed on a nonconformant population and are reported only as the contamination artifact they are. "Substantially correlated," never "one axis" or "near-collinear."
7.  **Two tallies, never merged.** Joint model: two coefficients inverted, one consistent. Marginal effects: one inverted, one **null**, one consistent. Occupancy's null is not a contradiction, and §4.4 explicitly instructs the reader not to conflate these frames — so the abstract and §5.1 must not do it either.

### Register

§4.1 is the one place a reviewer will look for defensiveness. Keep it flat and declarative. Every impulse to explain how careful the process was is the impulse to delete. The hostile review of the prior preprint scored AI-writing risk at 8/10 — highest of any axis except submission readiness — and located it in connective prose, introduction and discussion, not in the tables. Kill every "not X but Y" construction, every rhetorical triad, every meta-epistemic noun ("claim ladder," "first-class outcome," "load-bearing," "epistemic"). Read it aloud; anything you would not say out loud goes.

### Shape of the argument

A broken measuring tool → the mechanism of the break → the repair specification → the repaired tool demonstrably working → a clean pre-registered negative obtained with it.

### Venue

RecSys or TORS for the recommender framing; a methods-tolerant venue (R. Soc. Open Sci., PLOS ONE) if the competing-risks translation leads. The prior review judged the recsys venues an immediate rejection for the earlier paper on three grounds — mislabelled phenomenon, deferred controls, 88% event prevalence — all three of which are now the paper's content rather than its defects.

  