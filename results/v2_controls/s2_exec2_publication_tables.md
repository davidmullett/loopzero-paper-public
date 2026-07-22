# Study 2 — Execution-2 publication tables (§12, SIGNAL DIES route)
Registration: OSF osf.io/wka72 (frozen, SHA-256 2374e370…). Conformance audit: DEVIATIONS D-25 (30/34 params conformant; three §6 divergences + one relabelled §4 diagnostic, all remediated; provenance content-pinned to the arXiv 2606.00329 GroupLens hash). Config C*** (CODE_ANCHOR 42075400…). All numbers re-derive from the canonical sealed payload (internal sha256 472571471d94…); every value below is a value-match assertion against it, not read by eye. NO analysis beyond the pre-registered set was performed.

## Verdict
SIGNAL DIES — reason: fails on own merits: c1=False c2=False c3=False. §11 lattice route (ii): any of criteria 1–3 fails ⇒ DIES; criterion 4 (dispositive control arms) not reached.

## Criteria (verbatim from §10) + quantities + booleans
| criterion | registered statement | quantity | boolean |
|---|---|---|---|
| 1 | ΔTPR ≥ 0.05 at b=0.05, BCa 95% CI excl 0 | ΔTPR@0.05 = -0.4716 [-0.4957, -0.4438] | **False** |
| 2 | ΔTPR positive-signed at ≥3 of 4 budgets {0.02,0.05,0.10,0.20} | positive at 0/4 budgets | **False** |
| 3 | covariate criterion (§7): signs bG>0,bP>0,bD<0 (CI excl 0) AND incr AUC ≥ 0.02 | signs bG/bP wrong direction; incr AUC = +0.1621 [+0.1431, +0.1831] | **False** |
| 4 | crit-1 fails under both shuffled-TS and popularity | NOT REACHED (DIES on 1–3) | — |

## ΔTPR = TPR(S) − TPR(best baseline over {six families ∪ PC1}), matched budget, cluster BCa 95% CI (seed 201, 10k)
| budget b | k (eval CLEAN controls, n=766) | ΔTPR [95% CI] |
|---|---|---|
| 0.02 | 15 | -0.5027 [-0.5247, -0.4871] |
| 0.05 | 38 | -0.4716 [-0.4957, -0.4438] |
| 0.1 | 77 | -0.4355 [-0.4586, -0.4153] |
| 0.2 | 153 | -0.3857 [-0.4122, -0.3488] |

Every ΔTPR is **negative** with CI excluding 0 on the wrong side: S is strictly worse than the best miss-based baseline at all four budgets.

## Covariate model (§9), eval-fold L₂
| term | β [95% CI] | registered sign | direction |
|---|---|---|---|
| z(G) | -0.4753 [-0.6349, -0.3127] | > 0 | **wrong (negative)** |
| z(p) | -0.4188 [-0.5120, -0.3280] | > 0 | **wrong (negative)** |
| z(δ) | -0.5384 [-0.6909, -0.3850] | < 0 | correct (negative) |
| incremental AUC over covariates | +0.1621 [+0.1431, +0.1831] | ≥ 0.02 | met in magnitude (but signs fail ⇒ c3 False) |

## Dispositive control arms — ΔTPR at primary b=0.05 (criterion-4 machinery; not reached)
| arm | ΔTPR@0.05 [95% CI] |
|---|---|
| popularity_only | -0.5940 [-0.6169, -0.5704] |
| shuffled_ts_102 | -0.5139 [-0.5264, -0.4975] |
| shuffled_ts_103 | -0.5275 [-0.5408, -0.5120] |
| shuffled_ts_104 | -0.5259 [-0.5414, -0.5098] |
| shuffled_ts_105 | -0.5306 [-0.5453, -0.5170] |
| shuffled_ts_106 | -0.5401 [-0.5522, -0.5272] |

## Population accounting (label-side, census 6b6ac55)
- Events (DEGRADED in (20,50]): 20,265 · Candidate controls (unstarved at t_split=20): 1,463 · CLEAN controls: 1,460 = 694 calibration + 766 evaluation · L₂ = 21,725
- z-parameters estimated on the 694 calibration-fold CLEAN controls.

---

## PC1 learnability gate (re-derived, value-matched to payload)
PASSED. TPR@b=0.05 = **0.561016** [0.549265, 0.574181]; (TPR−b) = 0.511016 [0.499265, 0.524181], CI excludes 0. The early-miss-rate detector on the CLEAN population is strongly learnable — the recovered user-process component (D-32b). PC2 liveness: PASS.

## Per-detector operating tables — matched TPR (point) at the four registered budgets, eval CLEAN population (766 controls)
| detector | b=0.02 (k=15) | b=0.05 (k=38) | b=0.1 (k=77) | b=0.2 (k=153) |
|---|---|---|---|---|
| S_composite | 0.0473 | 0.0894 | 0.1480 | 0.2396 |
| PC1_early_miss | 0.5500 | 0.5610 | 0.5836 | 0.6253 |
| variance_ews | 0.5500 | 0.5610 | 0.5836 | 0.6253 |
| cusum | 0.5500 | 0.5610 | 0.5836 | 0.6253 |
| page_hinkley | 0.5500 | 0.5610 | 0.5836 | 0.6253 |
| matrix_profile | 0.5500 | 0.5610 | 0.5836 | 0.6253 |
| ac1 | 0.5004 | 0.5127 | 0.5378 | 0.5848 |
| permutation_entropy | 0.0164 | 0.0413 | 0.0933 | 0.1828 |

The registered composite **S is near-chance at every budget** (≈ the budget itself); PC1 and the four miss-based families cluster at 0.55–0.63. S is strictly dominated — hence ΔTPR < 0 everywhere.

---

## Phase-4 (D-33) — six REQUIRED items

### Item 1 — bounding diagnostic (Cohen's d; eval: 10,153 events / 766 clean / 1,687 starved controls)
| indicator | d_full (vs all ctrl) | d_purified (vs clean) | d_starved_contrast (starved vs clean) | mechanical Δd [95% CI] | coupling |
|---|---|---|---|---|---|
| z(G) churn | 2.0096 | **-0.6363** | -5.6224 | 2.6459 [2.5527, 2.7393] | slate-structure (engine-frontier-coupled) |
| z(p) occupancy | -2.2508 | **0.046** | 4.0945 | -2.2968 [-2.389, -2.2035] | slate-structure (engine-frontier-coupled) |
| z(δ) coverage | 1.9993 | **-0.6803** | -5.6034 | 2.6796 [2.5849, 2.7751] | slate-structure (engine-frontier-coupled) |
| miss_run_fraction | -2.6217 | **0.8109** | 6.1397 | -3.4325 [-3.5498, -3.3166] | outcome-stream (behavioral/miss-coupled) |

The slate indicators' whole-L event-discrimination is a contamination artifact — it collapses or reverses on the CLEAN population (d_purified ≈ 0 or negative). Only miss_run_fraction retains discrimination on clean (d_purified = +0.811). Mechanical Δd CI excludes 0 for all four.

### Item 2 — t_split sensitivity (full primary form; D-37 power rule, D-38 coverage rule)
| t_split | form | eval events | ΔTPR@0.05 [CI] | c1 | c2 | c3 |
|---|---|---|---|---|---|---|
| 15 | PARTIAL | 17,877 | -0.4251 [-0.4462, -0.3930] | False | False | COVERAGE-LIMITED (59% cov) |
| 20 | FULL (KAT) | 10,153 | -0.4716 [-0.4957, -0.4438] | False | False | False |
| 25 | FULL | 5,762 | -0.5210 [-0.5405, -0.4999] | False | False | False |

Robust null at all three landmarks. t=20 is the known-answer arm and reproduces the sealed payload exactly (points + BCa CI).

### Item 3 — frontier-headroom split (ΔTPR@0.05, matched)
- headroom_10_15: n_events=38 — n<100; ΔTPR not reported
- headroom_gt15: n_events=10,115 ΔTPR@0.05 = -0.4698 [-0.4932, -0.4415]

### Item 4 — indicator correlation matrix (Pearson r, eval L n=12,606)
| | G | p | delta | mrf |
|---|---|---|---|---|
| G | 1.000 | -0.869 | 0.975 | -0.923 |
| p | -0.869 | 1.000 | -0.869 | 0.876 |
| delta | 0.975 | -0.869 | 1.000 | -0.926 |
| mrf | -0.923 | 0.876 | -0.926 | 1.000 |

The indicators are near-collinear (|r| 0.87–0.98) — a single miss/frontier axis; S carries no information the miss stream lacks.

### Item 5 — I-5b absolute S discrimination on the six severed control arms (TPR_S − b, BCa CI)
| arm | TPR_S − b [CI] | beats chance |
|---|---|---|
| popularity_only | -0.0254 [-0.0386, -0.0137] | False |
| shuffled_ts_102 | -0.0085 [-0.0162, 0.0035] | False |
| shuffled_ts_103 | -0.0108 [-0.0203, 0.0003] | False |
| shuffled_ts_104 | -0.0168 [-0.0279, -0.0072] | False |
| shuffled_ts_105 | -0.0165 [-0.0260, -0.0063] | False |
| shuffled_ts_106 | -0.0240 [-0.0328, -0.0165] | False |

S beats chance on **zero** severed arms.

### Item 6 — two DISTINCT control populations (D-41 correction; census 6b6ac55)
**Partition check:** 3,292 (pre-landmark ≤20) + 1,460 (clean) + 3 (post-landmark (20,50]) = **4,755** total controls ✓ closes.

**(a) H3-as-frozen** — STARVED-in-(20,50] (**3 units**) vs CLEAN (1,460). **VACUOUS by population fact** — only 3 candidate controls starve post-landmark; no power, no discrimination computed. (Events crossing the floor before collapse: 0/20,265 by the degradation contract.)

**(b) starvation-concurrence probe** — STARVED-at-≤20 (**3,292** pre-landmark, excluded from L₂) vs CLEAN (1,460), indicators over steps 1–20. Cohen's d (pre-landmark vs clean): z(G) **−5.70**, z(p) **+4.17**, z(δ) **−5.77**, miss_run_fraction **+6.29**, S composite **+4.20**. **Pre-committed reading met (|d| ≥ 0.8): slate structure READS frontier depletion** — S is in part a frontier-depletion detector, which is exactly the contamination the CLEAN-population purification removes (and why item 1's whole-L d collapses on the purified population).

### Not-run ledger (three MOOT items, verbatim reasons)
- **H3_as_frozen**: MOOT — vacuous by population fact: by the degradation contract (collapse fires only when frontier>=floor) no event can cross the floor before collapse, and the CLEAN population excludes starvers by construction; the starvation-concurrence probe (item 6) reports the within-window-starver counts directly. Not run as a separate test.
- **MF_sequential_engines**: MOOT — existed to test mechanism specificity of a DETECTED signal; none was detected (SIGNAL DIES on c1–c3); not run. Deferred as future characterization (D-33).
- **random_arm_rerun**: MOOT — the random-arm degeneracy IS the result (D-3); a re-run adds nothing. Not run.

---

## D-42 — permitted characterization: history-richness of the starved stratum
Variable: **log_activity = log(1 + warm_start_positive_count)** — WARM-START POSITIVE COUNT (thin early positive history), NOT total rating volume. Source: C* cache b7a0aa36 (25,020-row superset). Covariate-side + label-side only; pop_affinity deliberately NOT compared (non-inference clause).

| stratum | n | median log_activity | IQR |
|---|---|---|---|
| starved-at-≤20 | 3,292 | 2.890372 | [2.639057, 3.091042] |
| clean | 1,460 | 3.044522 | [2.833213, 3.218876] |

Standardized difference (starved − clean): **Cohen's d = -0.441137**, bootstrap 95% CI [-0.500015, -0.381052] (10,000 iters, seed 201).

**Trigger evaluation — ASSOCIATED: FIRED.** predicted direction (starved below clean): True; |d|≥0.2: True; CI excludes 0: True.

Licensed reading: **users with thin early positive history** are over-represented in the starved-at-≤20 stratum relative to clean controls (moderate association, |d|=0.44). Foreclosed readings (D-42 a/b) apply: an association among EXCLUDED units cannot bear on the purified comparison, and the starved-sparse stratum is unlabelable by construction — this makes the §11 scope more legible, never smaller. ECDFs in the anchored artifact.

---

## §5.1 correction (D-44): item-4 correlation recomputed on the standardization population
The anchored item-4 matrix above was computed on the full eval arm (n=12,606: events + clean + starved) — a D-7-class population deviation from the ruled §6 scope (694 cal-fold CLEAN controls). Recomputed on the standardization population:

| pair | eval arm (withdrawn) | cal-clean n=694 (correct) |
|---|---|---|
| r(G,p) | −0.8694 | −0.47798 |
| r(G,δ) | 0.9751 | **0.83298** |
| r(p,δ) | −0.8689 | −0.41469 |

Decomposition on the correct population: Var(D)=2(1−0.83298)=0.33404; Cov(D,z(p))=−0.06329; Var(S)=1.20745; occupancy variance share = **82.8%**. **Pre-committed reading REVERT** (r(G,δ)=0.833 < 0.90): the near-total-cancellation / geometric-infeasibility claim is withdrawn; §5.1 reverts to the qualitative form (occupancy still dominant at ~83%, but the contrast does not structurally cancel). The DIES verdict is untouched.
