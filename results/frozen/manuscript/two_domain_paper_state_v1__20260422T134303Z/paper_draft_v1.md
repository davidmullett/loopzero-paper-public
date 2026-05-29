# **A theorem-grounded warning criterion for collapse in recursive systems**

**David Mullett**

Independent Researcher

ORCID: 0009-0004-2543-1664

**Corresponding author:**

David Mullett

Email: d@loopzero.org

## **One-Sentence Summary**

A Lean-verified obstruction for recursive no-progress cycles yields a theorem-guided pre-collapse signature that survives fair warning-budget benchmarking across public markets and recommender systems, while standard early-warning baselines fail to recover accepted operating points.

## **Abstract**

Recursive systems can enter collapse-like regimes before overt failure becomes visible. In such regimes, amplification, endogenous recycling, and contraction of accessible state trajectories reinforce one another while local updates remain internally coherent. We derive a warning criterion from a Lean-verified no-progress obstruction for recursive feedback systems and instantiate it using three telemetry witnesses: gain (G), self-reinforcement (p), and diversity (\\delta). Under explicit assumptions, the obstruction motivates a testable empirical prediction: pre-collapse regimes should exhibit rising amplification, rising recursive persistence, and declining diversity.

We evaluate this prediction under matched false-positive benchmarking, comparing detectors at the same alert budget rather than at arbitrary thresholds, across heterogeneous recursive settings including adaptive decision loops, recommender dynamics, recursive model replay, and public market event families. On the canonical segmented markets benchmark, no tested fast or slow comparator configuration achieved the locked equal-false-positive band \[0.03,0.07\], despite band reachability (n=38 control units; FP grid step \=1/38=0.026316). The nearest nontrivial comparator remained AC1 at FP \=0.131579 (5/38 control alarm units), whereas the numerically nearest slow configurations were trivial-silent and the best nontrivial slow family, permutation entropy, remained materially above band (FP \=0.368421). On a second public recursive benchmark built from MovieLens-25M user trajectories, no tested fast or slow comparator configuration was accepted on the canonical 50-step benchmark or on adjacent 40- and 60-step horizon variants. Directional witness summaries were fully aligned on the canonical recommender benchmark. On the canonical public-markets benchmark, the same directional pattern was recovered when markets were summarized over the last 30 minutes of each exact canonical unit; in a wider 60-minute markets summary, gain G and recursive persistence p remained aligned whereas diversity-change weakened. We therefore interpret the markets bridge as localized and late-window strongest rather than uniformly invariant across wider summary windows.

These results support a broader claim: a formally specified recursive obstruction leaves a measurable pre-collapse footprint that can be evaluated under a fair alert-budget contract, and standard early-warning baselines fail to recover accepted operating points on canonical public benchmarks. Collapse, on this view, becomes not merely a metaphor but a computable and falsifiable empirical regime.

---

# **Main Text**

## **A formally specified obstruction for recursive collapse**

Many systems of scientific and practical interest are recursive: present state shapes future state, and locally valid updates can reinforce their own continuation. In such systems, collapse need not begin as overt breakdown. It may instead begin when recursion remains locally coherent while genuine forward improvement becomes inaccessible. This distinction matters because much of the early-warning literature is organized around variance growth, autocorrelation shifts, or threshold excursions in observed channels, without first specifying the structural failure mode to which those observables are meant to correspond.

The starting point here is a formally specified no-progress obstruction for recursive feedback systems, verified in Lean. In that formal setting, one strictly worsening update coupled to monotone tethers can generate a cycle in which local continuation remains possible while meaningful progress is lost. The empirical question is therefore not whether one can engineer a useful detector from arbitrary signals. It is whether this formally specified obstruction leaves a measurable pre-collapse footprint in observed recursive systems.

## **Theorem-to-observable bridge**

The formal result does not itself prove that any particular empirical metric must move in any particular domain. The bridge is therefore theorem-guided rather than theorem-identical. To relate the obstruction to data, we consider recursive systems in which future updates depend partly on recent internal outputs, partly on external input, and partly on the diversity of accessible next states. In such systems, collapse need not first appear as immediate failure. It may instead appear as a pre-collapse regime in which perturbations are increasingly amplified, recent internally generated states increasingly determine subsequent states, and the accessible state space contracts.

Under this interpretation, the obstruction motivates three observable tendencies before externally defined collapse events: rising gain G, indicating amplification rather than damping of perturbation; rising self-reinforcement p, indicating increasing persistence of internally generated state; and declining diversity \\delta, indicating contraction of the effective range of system trajectories. We therefore treat G, p, and \\delta as empirical proxies for amplification, recursive persistence, and state-space contraction. This bridge is explicitly falsifiable. It would be weakened if benchmark-defined collapse repeatedly occurred without prior elevation of G and p and reduction of \\delta, or if matched-false-positive comparator families repeatedly recovered accepted operating points without this triad.

## **Telemetry witnesses and matched-false-positive benchmarking**

The theorem-guided prediction is operationalized through a triplet of witnesses. G estimates short-horizon amplification of perturbation, p estimates short-horizon recursive persistence of active state, and \\delta estimates the effective breadth of observed system behavior across channels, modes, or trajectories. The predicate is therefore designed to test the empirical signature implied by the formal mechanism, not to restate the theorem in observational language.

In the current implementation, the three witnesses are not equally directional in their operational role. G is evaluated as an elevated-gain condition relative to recent background, and \delta is evaluated through a non-increase condition over the relevant lookback window. The p witness is used most conservatively: it functions as a non-relaxation gate consistent with monotone-tether semantics rather than as a standalone directional effect-size claim. In the public-markets adapter, p is constructed from a trailing recurrence statistic over stress events defined using a fixed z-threshold of 1.5; this threshold is part of the current adapter definition and should be interpreted as such.

All empirical evaluation is conducted under a matched false-positive contract. In heterogeneous systems, comparator families can appear competitive simply by spending false alarms differently. We therefore compare detectors only at the same alert budget, defined by a locked equal-false-positive criterion rather than by arbitrary family-specific thresholds. A configuration is accepted only if its control-unit false-positive rate lies within the prespecified interval \\mathrm{FP} \\in \[0.03,0.07\]. Under this contract, the empirical program is directly falsifiable: it fails if any comparator family admits an accepted operating point on the canonical benchmark under the same criterion.

## **Cross-domain evidence for a pre-collapse signature**

We therefore test whether the theorem-guided triad (G,p,\\delta) appears before externally defined collapse events under a locked equal-false-positive benchmark across heterogeneous recursive systems. Across retained domain families, the criterion identifies pre-collapse structure before externally defined breakdown or intervention points and does so under the same alert-budget rule. These retained families were chosen not because they are easy cases, but because they admit externally defined event times, nontrivial controls, and fair comparator evaluation under a common false-positive contract.

On the canonical public-markets benchmark, the same directional pattern was recovered when markets were summarized over the last 30 minutes of each exact canonical unit; in a wider 60-minute markets summary, gain G and recursive persistence p remained directionally aligned whereas diversity-change weakened. We therefore interpret the markets bridge as localized and late-window strongest rather than uniformly invariant across wider summary windows.

The broader significance is not that a new warning statistic works in one domain. It is that a formally specified recursive obstruction appears to leave a domain-resolved empirical signature across systems that differ strongly in substrate, timescale, and external semantics. The evidence therefore supports a theorem-guided empirical program rather than a single-domain detector construction.

A domain-resolved witness-direction summary is provided in Table Sy.

## **Canonical public recommender benchmark**

A second flagship benchmark was constructed from MovieLens-25M user trajectories to test whether the theorem-guided program survives outside markets. User ratings were sorted chronologically, reduced to one episode per user, and replayed under a deterministic item-item collaborative-filtering engine with a warm-start prefix and a held-out positive frontier. On the canonical 50-step benchmark, 40,339 user-level units satisfied inclusion criteria, including 35,584 event units and 4,755 control units. The control-unit false-positive grid step was 1/4755 \= 0.0002103, so the prespecified acceptance band \[0.03,0.07\] was reachable by construction.

On this canonical recommender benchmark, the theorem-guided bridge passed in the prespecified pre-collapse window: pre-collapse event units showed higher amplification G, higher recursive persistence p, and lower diversity \\delta than reference controls. User-level bootstrap summaries were directionally consistent with this pattern and were used descriptively rather than as a significance test. Under the same locked equal-false-positive contract, no tested fast or slow comparator family admitted an accepted operating point. Across 105 tested configurations, the overall nearest comparator was matrix profile (`matrix_profile__44b81bd6`), which remained below the lower edge of the accepted band with control FP \=0.0136698, band distance \=0.0163302, and event alarm rate \=0.110668. Among fast families, the numerically nearest operating point was a trivial-silent variance EWS configuration at FP \=0.0, whereas the nearest nontrivial fast-family configurations overfired controls substantially.

## **Recommender robustness under adjacent horizon sensitivity**

To test whether the recommender result depended on the canonical episode horizon, the benchmark was rebuilt at adjacent horizons of 40 and 60 recursive update steps while holding benchmark construction and comparator rules fixed. At both adjacent horizons, no comparator family recovered an accepted operating point under the locked equal-false-positive band. The overall nearest comparator remained matrix profile in all three horizon settings and remained outside the accepted interval. The theorem-guided bridge remained fully aligned at 60 steps but became partial at 40 steps. This horizon dependence is mechanistically expected: shorter pre-collapse windows leave less time for the recursive signature to separate cleanly from matched controls. The recommender branch therefore supports a corroborating second flagship benchmark on the comparator claim, with a bounded robustness qualification on the bridge layer under adjacent horizon shortening rather than an unqualified invariance claim.

## **Public market event family**

Public markets provide a stringent test because they combine exogenous shocks, endogenous amplification, heterogeneous liquidity structure, and a substantial comparator literature. We therefore assembled a reproducible public market event family centered on the February 2018 Volmageddon dislocation and the March 2020 COVID market-wide circuit-breaker cluster, together with hard negative controls. The purpose was not to present markets as a universal separator domain, but to ask whether a theorem-guided recursive warning criterion survives externally auditable benchmark construction in a domain with strong prior baselines and obvious confounds.

In this branch, the critical distinction is between narrative motivation and frozen benchmark evaluation. Narrative examples such as the 2010 Flash Crash motivate the broader problem of recursive dislocation, but the quantitative claims reported here are anchored to the frozen canonical markets benchmark and its comparator contract. That benchmark is the relevant object for comparator availability, equal-false-positive reachability, and robustness.

## **Comparator calibration on the canonical markets benchmark**

To test whether the markets result depended on a narrow comparator set, we evaluated a broader comparator suite on the canonical segmented markets benchmark, `volmageddon_covid_public_v2`, constructed from a single canonical source configuration and a rule in which one underlying market segment constituted one comparator unit. This yielded 38 control units and 16 event units, so the prespecified equal-false-positive acceptance band, \\mathrm{FP} \\in \[0.03,0.07\], was reachable on this benchmark with grid step 1/38 \= 0.026316. Fast comparator families comprised variance EWS, lag-1 autocorrelation (AC1), CUSUM, and Page-Hinkley; slow families comprised matrix profile and permutation entropy. Fast comparator families were evaluated over predeclared parameter grids, followed by full-grid expansion of the two slow comparator families on the frozen canonical benchmark.

No tested fast or slow comparator configuration achieved the acceptance band on the canonical markets benchmark. The nearest nontrivial comparator remained AC1: configuration `ac1_ews__632f23b2` alarmed on 5/38 control units (FP \=0.131579) and 1/16 event units, leaving it 0.061579 above the admissible band. Full-grid slow-family evaluation did not rescue the comparator branch. The numerically nearest slow configurations were tied across matrix profile and permutation entropy, but both were trivial-silent, producing 0/38 control alarms and 0/16 event alarms. Among slow families, the best nontrivial configuration came from permutation entropy (`permutation_entropy__259c1b96`), which alarmed on 14/38 control units (FP \=0.368421) and 4/16 event units, remaining 0.298421 above band. Thus, under a reachable and locked equal-false-positive criterion, no tested comparator family admitted an acceptable operating point on the canonical markets benchmark.

## **Fast-family robustness under canonical and relaxed band specifications**

The comparator conclusion in markets admits a narrower and more precise robustness statement than earlier drafts. Under the prespecified equal-false-positive band \[0.03,0.07\], no tested fast-family comparator configuration was accepted on the canonical 120-minute segmented markets benchmark or on 60-minute and 180-minute segmentation sensitivity variants. In all three cases, the nearest fast family remained AC1; the nearest false-positive rate was 0.1316 for the canonical 120-minute units, 0.0800 for the 60-minute units, and 0.1304 for the 180-minute units. Thus, fast-family non-acceptance was robust across tested segmentations at the locked canonical specification.

By contrast, post-processing band-sensitivity analysis showed that widening the acceptable interval to \[0.02,0.08\] or \[0.04,0.08\] admitted the 60-minute AC1 configuration, whereas the canonical 120-minute and 180-minute segmentations remained non-accepted. We therefore distinguish canonical robustness from relaxed-band sensitivity and do not claim full invariance to post hoc band relaxation. The result that carries manuscript weight is the stronger one: at the prespecified canonical band, no fast-family comparator is accepted at 60-, 120-, or 180-minute segmentation.

## **Controls, falsification boundary, and bounded exceptions**

The theorem-to-observable bridge is explicitly falsifiable. It would be weakened if externally defined collapse events occurred without prior increase in G and p and decrease in \\delta; if comparator configurations detected the same events under matched false-positive constraints without exhibiting this triad; if the (G,p,\\delta) pattern appeared frequently in control periods without progression toward externally defined collapse; or if alternative reasonable operationalizations of amplification, recursive persistence, and diversity contraction failed to agree directionally with the present measurements. At the benchmark level, the empirical program would be invalidated if any comparator family achieved an accepted operating point on the canonical benchmark under the same equal-false-positive contract.

The markets branch also contains a bounded near-miss rather than a universal separator. Binary and topological diagnostics did not separate Volmageddon from vol-heavy hard negatives. The strongest remaining signal instead appeared in continuous witness quality, with the clearest confirmation in corroborating configuration `cfg_002053`, particularly against `volmageddon_control_2018_02_08`. We therefore treat this residual as a bounded exception that sharpens the empirical interpretation rather than as a contradiction of the broader result. Across the retained domains, we do not observe either falsifying condition.

## **Discussion**

The scientific claim of the paper is deliberately minimal. First, collapse in recursive systems can be rendered computable through a theorem-guided observable predicate. Second, under equal-false-positive fairness, standard early-warning families do not recover the same admissible operating behavior on canonical benchmarks. The significance of the paper lies in the conjunction of those two claims: a formal obstruction motivates a measurable pre-collapse signature, and that signature survives fair benchmarking against a broad comparator suite. Unlike threshold-tuned detectors, the empirical program is explicitly falsifiable under a fixed equal-false-positive contract.

The markets branch is especially informative because it is both strong and bounded. It is strong in the sense that the canonical segmented benchmark is externally grounded, the acceptance band is reachable, the comparator suite is broad, and no tested fast or slow family admits an accepted operating point. It is bounded in the sense that the 60-minute fast-family branch becomes admissible only under widened post hoc bands, and the Volmageddon residual is not presented as a universal separator. That boundedness is scientifically useful. It marks the difference between a detector paper that optimizes narrative smoothness and a theory-led manuscript that preserves the structure of its own exceptions.

The recommender branch provides a second flagship empirical benchmark. On the canonical 50-step MovieLens recursive frontier benchmark, the theorem-guided bridge passes and no tested fast or slow comparator family admits an accepted operating point under the locked equal-false-positive rule. Adjacent-horizon sensitivity preserves the comparator result at 40 and 60 steps, while the bridge remains stable at 50 and 60 and becomes partial at 40\. The recommender evidence therefore supports a corroborating second flagship benchmark with bounded bridge sensitivity under adjacent horizon shortening rather than a claim of unqualified invariance.

Several limitations remain. Witness construction is still domain-adapted. Comparator scope could expand further. And the theorem-to-observable bridge, although explicit and falsifiable here, remains an empirical bridge rather than an identification theorem. The next scientific step is therefore not rhetorical expansion but stress-testing: additional domains, external replication, intervention logic, and broader comparator classes. The present results support a precise claim: a formally specified recursive collapse obstruction leaves a measurable pre-collapse footprint that can be evaluated under a fair alert-budget benchmark, and across the canonical public markets and recommender benchmarks no tested standard comparator family achieves an accepted operating point under that contract.

## **Materials and Methods (brief)**

The paper combines a Lean-verified formal obstruction with empirical witness construction over gain, self-reinforcement, and diversity. Empirical evaluation is performed under a locked equal-false-positive contract, so detector families are compared at the same alert budget rather than at arbitrary thresholds. In markets, the expanded comparator suite included variance EWS, AC1, CUSUM, Page-Hinkley, matrix profile, and permutation entropy, all evaluated under the same locked equal-false-positive contract on the canonical segmented benchmark and its adjacent robustness variants. In recommenders, a public MovieLens-25M recursive frontier benchmark was constructed from one episode per user under a deterministic item-item replay engine, with collapse defined by failure to recover held-out positive frontier items under frozen benchmark rules. Across both domains, the witness triplet (G,p,\\delta) was evaluated as an empirical instantiation of the formal collapse obstruction under the assumptions stated in the theorem-to-observable bridge and Supplementary Materials. Full benchmark construction, parameter grids, robustness packets, theorem-to-observable assumptions, falsification conditions, and availability outcomes are reported in the Supplementary Materials.

## **Figure and Table Legends**

### **Main-text table caption**

**Table X. Comparator calibration on the canonical public benchmarks under the locked equal-false-positive contract.** Comparator families were evaluated under the same prespecified equal-false-positive criterion, \\mathrm{FP} \\in \[0.03,0.07\]. On the canonical segmented markets benchmark, the nearest nontrivial comparator was AC1, which remained above band at FP \=0.131579 (5/38 control alarm units). On the canonical 50-step recommender benchmark, no tested fast or slow comparator was accepted across 105 tested configurations; the overall nearest comparator was matrix profile (`matrix_profile__44b81bd6`) at FP \=0.0136698, remaining below the lower edge of the accepted band. Across both flagship domains, no tested comparator family admitted an accepted operating point.

### **Robustness caption**

**Fast-family segmentation and band sensitivity on the canonical markets benchmark.** No fast-family comparator was accepted at 60-, 120-, or 180-minute segmentation under the prespecified equal-false-positive band \[0.03,0.07\]. Under widened post-processing bands that included an upper cutoff of 0.08, acceptance appeared only for the 60-minute AC1 configuration.

### **Supplementary table caption**

**Table Sx. Recommender comparator calibration and adjacent-horizon sensitivity under the locked equal-false-positive rule.** Results are shown for the canonical 50-step MovieLens recursive frontier benchmark and the adjacent 40- and 60-step sensitivity variants. No tested fast or slow comparator configuration was accepted at any of the three horizons. The overall nearest comparator in all three cases was matrix profile (`matrix_profile__44b81bd6`), which remained outside the accepted band. The bridge passed at 50 and 60 steps and was partial at 40 steps.

**Table Sx. Witness-direction measurement on the canonical markets and recommender benchmarks.** On the canonical recommender benchmark, pre-collapse event units showed higher mean gain G, higher recursive persistence p, and lower diversity δ than matched controls. On the canonical public-markets benchmark, the same directional pattern was recovered when markets were summarized over the last 30 minutes of each exact canonical unit using G, p, and diversity-change Δδ within the late window. In a wider 60-minute markets summary, G and p remained directionally aligned whereas diversity-change weakened, indicating that the markets bridge is strongest in the localized late-window regime.

The 30-minute markets summary should be interpreted as a localized late-window measurement: it captures the terminal phase of the canonical benchmark units, where amplification and recursive reinforcement are strongest.

Taken together, these witness-direction summaries support a differentiated bridge claim rather than a universal one. The recommender benchmark exhibits full triad alignment on the canonical benchmark. The markets benchmark exhibits the same pattern in localized late-window form, with the clearest recovery in the final 30 minutes of each exact canonical unit and weaker diversity-change alignment over 60 minutes. This is consistent with the broader markets result: the bridge is present, but its clearest empirical expression is temporally concentrated near the terminal regime.

---

# **Supplementary Materials Draft**

## **S3. Theorem-to-observable bridge**

### **S3.1. Formal obstruction and empirical interpretation**

The formal core of Loopzero is a no-progress obstruction for recursive feedback systems. In the formal setting, the obstruction arises when a system admits one strict worsening leg while remaining tethered by monotone update structure, yielding a cycle in which local recursion can continue without genuine progress. The theorem does not by itself specify a unique empirical measurement scheme. Its role is instead to define a class of collapse mechanisms: recursive systems can become trapped in self-referential update dynamics that preserve local continuation while eroding the conditions required for meaningful forward evolution.

To interpret this result empirically, we consider observed systems as partial projections of an underlying recursive state process. Let x\_t denote system state at time t. We interpret updates as depending on three broad factors: responsiveness to prior perturbation, persistence of the system’s own recent state in determining its next state, and the breadth of distinguishable next-state possibilities available to the system. Under this view, collapse is approached not only through overt failure, but through progressive amplification, recursive self-dependence, and contraction of effective state-space diversity.

### **S3.2. Assumptions linking the theorem to observables**

We make four assumptions to connect the formal obstruction to empirical observables.

**Assumption 1 (partial observability).** The measured channels constitute incomplete but informative projections of the underlying recursive state process.

**Assumption 2 (amplification).** When recursive correction weakens relative to recursive reinforcement, small perturbations propagate forward with increasing local gain rather than being damped.

**Assumption 3 (self-reinforcement).** As the system approaches a no-progress cycle, the next state depends increasingly on the system’s own recent state rather than on novel external variation.

**Assumption 4 (state-space contraction).** As recursive failure develops, the effective range of accessible next states contracts, so that observed trajectories become increasingly concentrated in fewer modes or patterns.

These assumptions do not identify a unique empirical representation of collapse. They instead specify the observable consequences expected from the class of recursive obstructions formalized by the theorem.

### **S3.2a. Minimal state-space sketch**

A minimal empirical sketch can be written as

x\_{t+1} \= F(x\_t, u\_t, \\epsilon\_t),

where x\_t is latent system state, u\_t is external input, and \\epsilon\_t is residual variation. We interpret recursive instability as a regime in which local sensitivity to x\_t increases, dependence on recent internally generated state strengthens, and the effective support of reachable states narrows. In this regime, one expects increasing local amplification, increasing persistence, and decreasing diversity in observed projections of the process.

### **S3.3. Predicted observable consequences**

Under assumptions 1–4, the formal obstruction yields three qualitative empirical predictions.

**Prediction 1 (rising gain).** If perturbations are no longer corrected but instead propagated forward, local update dynamics should exhibit increasing amplification. Empirically, this predicts elevation in a gain statistic G that measures whether deviations tend to expand rather than decay over short horizons.

**Prediction 2 (rising self-reinforcement).** If subsequent states are increasingly determined by the system’s own recent outputs, persistence of internally generated state should increase. Empirically, this predicts elevation in a self-reinforcement statistic p that measures short-horizon recurrence or carry-forward of active state.

**Prediction 3 (declining diversity).** If the effective state space is contracting, the system should occupy fewer distinguishable modes, trajectories, or channel combinations before collapse. Empirically, this predicts reduction in a diversity statistic \\delta that measures dispersion or effective rank across observed channels.

Taken together, these predictions define a pre-collapse regime: amplification rises, self-reinforcement rises, and diversity falls before externally defined failure or intervention points.

### **S3.4. Operationalization in Loopzero**

The empirical program operationalizes these predicted tendencies through the triplet (G,p,\\delta). Here, G estimates local amplification of system deviations across short horizons; p estimates persistence of active state under recursive update; and \\delta estimates the effective breadth of observed system behavior across channels or modes. The resulting predicate is intended as an empirical test of the theorem’s qualitative consequences, not as a direct restatement of the theorem itself.

This distinction is important. The theorem identifies a collapse mechanism at the level of recursive structure. The empirical predicate measures whether observed systems exhibit the corresponding signature expected under that mechanism. Accordingly, success of the predicate supports the theorem-guided empirical program, whereas failure of the predicate would count against the adequacy of this operationalization.

### **S3.5. Falsification conditions**

The bridge between the formal obstruction and the empirical predicate is falsifiable. It would be weakened by any of the following observations.

**Falsification condition 1\.** Externally defined collapse events repeatedly occur without prior increase in G and p and decrease in \\delta.

**Falsification condition 2\.** Under matched false-positive constraints, accepted comparator configurations repeatedly detect the same collapse events without exhibiting the predicted triad.

**Falsification condition 3\.** The (G,p,\\delta) triad appears frequently in control periods without progression toward externally defined collapse.

**Falsification condition 4\.** Alternative reasonable operationalizations of amplification, recursive persistence, or diversity contraction do not agree directionally with the Loopzero measurements.

These conditions make clear that the theorem does not immunize the empirical predicate from failure. Rather, the empirical program stands or falls on whether the predicted observable signature is borne out in data.

### **S3.6. Scope and non-claims**

We do not claim that all forms of collapse must instantiate this triad, nor that G, p, and \\delta are the only valid observables of recursive failure. We claim only that, for the class of recursive feedback systems targeted here, the formal obstruction motivates a testable empirical prediction: collapse should be preceded by increasing amplification, increasing self-reinforcement, and decreasing diversity. The empirical analyses evaluate that prediction against externally defined events and matched-false-positive comparator baselines.

---

## **S6. Equal-FP benchmark procedure**

### **S6.1. Canonical markets comparator benchmark**

Comparator calibration in markets was performed on the frozen canonical benchmark `volmageddon_covid_public_v2`. This benchmark was constructed from a single canonical source configuration (`cfg_001339`) and a comparator-specific unitization rule in which one underlying market segment constituted one comparator unit. The resulting benchmark contained 38 control units and 16 event units. Because control-unit false-positive rate was defined as the fraction of control units containing at least one gated alarm, the attainable FP grid had step size 1/38 \= 0.026316, making the prespecified equal-FP acceptance interval \[0.03, 0.07\] reachable on this benchmark. This construction avoided the earlier invalid markets comparator state in which the target FP band was structurally unreachable under the original unitization.

Fast comparator families were variance EWS, AC1, CUSUM, and Page-Hinkley. Slow comparator families were matrix profile and permutation entropy. All comparator families were calibrated under the same locked equal-FP contract and with predeclared parameter grids. For each configuration, alarms were scored on the oriented scalar input series used by the comparator package, then thresholded and gated according to family-specific rules declared in the comparator suite specification. In the canonical markets benchmark, this oriented comparator input series is \log(1 + G_t), where G_t is the Loopzero gain witness computed on the public market telemetry panel. All comparator families therefore operate on the same one-dimensional instability channel, while the theorem-guided predicate additionally imposes the \delta and p tether conditions. A configuration was accepted only if its control-unit false-positive rate fell within \[0.03, 0.07\]. Distances to band were computed as absolute miss distance from this interval. Because slow families could produce trivial silent configurations that were numerically close to the target band but scientifically uninformative, the markets comparator summaries distinguish numerically nearest slow configurations from best nontrivial slow configurations, where nontrivial requires at least one event alarm unit.

### **S6.2. Full-grid slow-family expansion**

To close the residual comparator loophole, the slow comparator branch was expanded from an initial controlled subset to the full predeclared slow-family grids on the frozen canonical benchmark. Matrix profile and permutation entropy were each rerun over their full declared parameter ranges using the same frozen benchmark input and the same locked equal-FP criterion. This full-grid expansion did not alter the scientific conclusion. No slow comparator configuration was accepted. Matrix profile exhibited a split between trivial-silent configurations and severe control overfiring once nontrivial alarms appeared. Permutation entropy likewise failed to yield an accepted operating point: its numerically nearest configurations were trivial-silent, and its best nontrivial configuration remained substantially above band.

---

## **S9. Comparator availability in markets**

### **S9.1. Markets comparator availability under the locked equal-FP rule**

On the canonical segmented markets benchmark, no comparator family admitted an accepted operating point under the locked equal-FP rule. The nearest nontrivial fast-family comparator was AC1 (`ac1_ews__632f23b2`), which produced FP \= 0.131579 from 5/38 control alarm units and alarmed on 1/16 event units. Variance, CUSUM, and Page-Hinkley were farther above band. In the full-grid slow pass, the numerically nearest slow configurations were tied across matrix profile (`matrix_profile__0a536aa4`) and permutation entropy (`permutation_entropy__001577c8`), both with FP \= 0.0 and 0/16 event alarm units, and are therefore interpreted as trivial-silent rather than substantively competitive. The best nontrivial slow-family configuration was permutation entropy (`permutation_entropy__259c1b96`), which produced FP \= 0.368421 from 14/38 control alarm units and alarmed on 4/16 event units. Accordingly, the nearest nontrivial comparator overall remained AC1, and the broader comparator expansion did not overturn the markets conclusion.

---

## **S10. Fast-family segmentation and band sensitivity in markets**

### **S10.1. Segmentation sensitivity for the markets fast-family branch**

Segmentation sensitivity was evaluated by reconstructing canonical comparator input tables at 60-minute and 180-minute unitization, in parallel with the canonical 120-minute segmentation, while preserving the same canonical source sessions and fast-family comparator grids. Under the canonical band \[0.03, 0.07\], no fast-family comparator was accepted at 60-, 120-, or 180-minute segmentation. The nearest fast-family comparator remained AC1 in all three cases.

### **S10.2. Band-sensitivity post-processing**

Band sensitivity was evaluated as a post-processing layer on frozen fast-calibration outputs and did not rerun comparator calibration. For each segmentation, acceptance was recomputed directly from stored false-positive rates under the canonical band \[0.03, 0.07\] and under two widened bands, \[0.02, 0.08\] and \[0.04, 0.08\]. Under the widened bands, acceptance appeared only for the 60-minute AC1 configuration. The canonical 120-minute and 180-minute segmentations remained non-accepted across all tested bands.

### **S10.3. Interpretation boundary**

These results support the narrower claim that the fast-family non-acceptance conclusion is robust at the locked canonical specification, while also showing sensitivity of the 60-minute branch to relaxed band definitions. They do not support a stronger claim of full invariance to post hoc widening of the acceptable false-positive interval.

Under the canonical [0.03,0.07] acceptance band, no comparator family was accepted at any tested segmentation (60, 120, or 180 minutes). A single fast-family comparator configuration (AC1 at 60-minute segmentation) was admitted only under widened post hoc acceptance bands.

---

## **S11. Canonical public recommender benchmark**

### **S11.1. Benchmark construction**

The canonical recommender benchmark was constructed from MovieLens-25M after chronologically sorting ratings within user. One episode was generated per user. Each episode used the first 30 ratings as a warm-start prefix and defined a held-out positive frontier from future ratings \\ge 4.0. Episodes were advanced under a frozen deterministic item-item collaborative-filtering replay engine with fixed tie-breaking, candidate exclusion, and update rules. Collapse was declared at the first step at which the recommender failed for eight consecutive recursive update steps to recover any remaining positive frontier item while at least 10 frontier items remained, within a maximum horizon of 50 steps on the canonical benchmark.

### **S11.2. Canonical unit counts and equal-FP reachability**

On the canonical 50-step benchmark, 40,339 units satisfied inclusion criteria, comprising 35,584 event units and 4,755 control units. Because control-unit false-positive rate was defined as the fraction of control units containing at least one gated alarm, the attainable FP grid had step size 1/4755 \= 0.0002103, so the prespecified acceptance interval \[0.03,0.07\] was reachable by construction.

### **S11.3. Theorem-guided bridge on the canonical benchmark**

On the canonical benchmark, the bridge passed in the prespecified pre-collapse window: relative to reference controls, pre-collapse event units showed higher mean G, higher mean p, and lower mean \\delta. User-level bootstrap summaries were used descriptively rather than inferentially.

---

## **S12. Comparator calibration on the canonical recommender benchmark**

For the recommender benchmark, comparator families are likewise evaluated on a single predeclared scalar instability channel derived from the same telemetry panel used by the theorem-guided predicate. The purpose of this design is to ensure that all comparator families receive the same one-dimensional input series, while Loopzero’s predicate adds the tether structure through the companion witnesses rather than through access to a different raw information stream.

### **S12.1. Comparator families and contract**

Fast comparator families were variance EWS, AC1, CUSUM, and Page-Hinkley. Slow families were matrix profile and permutation entropy. All configurations were evaluated under the same locked equal-false-positive contract used in markets, with acceptance defined by control-unit FP in \[0.03,0.07\].

### **S12.2. Canonical comparator result**

No tested fast or slow comparator configuration was accepted on the canonical recommender benchmark. Across 105 tested configurations, the overall nearest comparator was matrix profile (`matrix_profile__44b81bd6`) at control FP \=0.0136698, band distance \=0.0163302, and event alarm rate \=0.110668. The numerically nearest fast-family operating point was a trivial-silent variance EWS configuration at FP \=0.0. The nearest nontrivial fast-family operating points overfired controls substantially, with control FP values above 0.71. Thus, as in the canonical markets benchmark, no tested comparator family recovered an accepted operating point under the same warning-budget rule.

Permutation-entropy configurations uniformly over-fired on the canonical recommender benchmark, with control-unit false-positive rate reaching 1.0, and were therefore not competitive in the nearest-comparator analysis.

---

## **S13. Adjacent-horizon sensitivity in the recommender benchmark**

### **S13.1. Sensitivity design**

Adjacent-horizon robustness was evaluated by rebuilding the recommender benchmark at 40 and 60 recursive update steps while holding all other benchmark definitions fixed. The full downstream pipeline was rerun for each adjacent horizon, including benchmark construction, bridge checking, fast-family calibration, slow-family calibration, merged comparator summaries, and paper-facing comparator tables.

### **S13.2. Sensitivity outcome**

At both 40 and 60 steps, no tested comparator family admitted an accepted operating point. The overall nearest comparator remained matrix profile (`matrix_profile__44b81bd6`) in both adjacent-horizon variants and remained outside the accepted band. The bridge remained fully aligned at 60 steps and became partial at 40 steps. This horizon dependence is mechanistically expected: shorter pre-collapse windows leave less time for the recursive signature to separate cleanly from matched controls. Gate 3 therefore classified the recommender branch as a corroborating second flagship benchmark with bounded bridge sensitivity under adjacent horizon shortening.

### **S13.3. Interpretation**

The adjacent-horizon sensitivity result qualifies rather than overturns the recommender branch. The comparator claim is robust across the tested local horizon perturbations, whereas the bridge is stable at the canonical and longer adjacent horizon and only partial under shortening. The appropriate interpretation is therefore corroboration on the comparator claim with an explicit and bounded qualification on bridge invariance.