# Supplementary Materials

## Benchmarking Recursive-Collapse Warning Claims Under Matched False-Positive Control

**David Mullett** · ORCID: 0009-0004-2543-1664 · d@loopzero.org · Independent Researcher

This document contains the supplementary materials referenced in the main manuscript: one figure (S1) and four tables (S2, S3, S4, S5).

---

## Supplementary Figure S1

**Supplementary Figure S1. Fast-family segmentation and band sensitivity on the canonical markets benchmark.** No fast-family comparator was accepted at 60-, 120-, or 180-minute segmentation under the prespecified equal-false-positive band \[0.03, 0.07\]. Under widened post-processing bands with upper cutoff 0.08, acceptance appeared only for the 60-minute AC1 configuration; the canonical 120-minute and 180-minute segmentations remained non-accepted across all tested bands.

| Band | Segmentation | Band reachable | Any fast accepted | Nearest family | Nearest FP | Distance to band |
|---|---|---|---|---|---|---|
| [0.02, 0.08] | 60 min | Yes | Yes | `ac1_ews` | 0.0800 | 0.0000 |
| [0.02, 0.08] | 120 min | Yes | No | `ac1_ews` | 0.1316 | 0.0516 |
| [0.02, 0.08] | 180 min | Yes | No | `ac1_ews` | 0.1304 | 0.0504 |
| [0.03, 0.07] | 60 min | Yes | No | `ac1_ews` | 0.0800 | 0.0100 |
| [0.03, 0.07] | 120 min | Yes | No | `ac1_ews` | 0.1316 | 0.0616 |
| [0.03, 0.07] | 180 min | Yes | No | `ac1_ews` | 0.1304 | 0.0604 |
| [0.04, 0.08] | 60 min | Yes | Yes | `ac1_ews` | 0.0800 | 0.0000 |
| [0.04, 0.08] | 120 min | Yes | No | `ac1_ews` | 0.1316 | 0.0516 |
| [0.04, 0.08] | 180 min | Yes | No | `ac1_ews` | 0.1304 | 0.0504 |

Source: `results/frozen/comparators/markets_fast_robustness_packet_v1__20260421T175531Z/markets_fast_band_sensitivity_summary_v1.csv`.

---

## Supplementary Table S2

**Supplementary Table S2. Effect sizes with bootstrap 95% confidence intervals.** Per-witness Cohen's d, Glass's d, and rank AUC at each benchmark/horizon (4 benchmarks × 3 witnesses × 3 effect measures = 36 cells), with both BCa-adjusted and percentile bootstrap confidence intervals from cluster-aware resampling (10,000 iterations). Markets uses segment-level resampling (n=38 controls + 16 events); recommender (all horizons) uses user-level resampling (n = 40,339 user clusters). Canonical h=50 group is bolded throughout. A sensitivity section flags cells where BCa and percentile CI endpoints differ by ≥ 0.05 (markets p-witness cells only — the bootstrap distribution is right-skewed at low n, and BCa is the more honest read there). Full numerics rendered deterministically by `analysis/17_render_a3_supplementary_table_s2.py` from the per-cell bootstrap output at `results/rendered/effect_sizes/a3_effect_sizes_full.csv`.

**Source:** `results/rendered/effect_sizes/a3_effect_sizes_full.csv` (commit `d8908dd`)  
**Generator:** `analysis/17_render_a3_supplementary_table_s2.py`

Per-witness (G, p, δ) effect sizes at each benchmark/horizon with 95% BCa confidence intervals from cluster-aware bootstrap (10,000 iterations). Cohen's d, Glass's d, and Rank AUC are reported as complementary magnitude metrics. BCa is the primary CI method; percentile CIs are reported alongside for the cells where they differ meaningfully (sensitivity section below).

## Sign convention

Predicted direction by witness (event vs control):

- **G** (amplification): event > control predicted; positive d / AUC > 0.5 confirms
- **p** (concentration): event > control predicted; positive d / AUC > 0.5 confirms
- **δ** (contraction): event < control predicted; negative d / AUC < 0.5 confirms

## Bootstrap unit grain

- **Markets:** segment-level resampling (n = 38 controls + 16 events; ~30 rows per segment)
- **Recsys** (all horizons): user-level resampling (n = 40,339 user clusters; 10 rows per cluster)

## Effect sizes by benchmark

### Markets (Volmageddon + COVID-MWCB)

| Witness | Cohen's d [BCa 95% CI] | Glass's d [BCa 95% CI] | Rank AUC [BCa 95% CI] |
|---|---|---|---|
| G | -0.029 [-0.169, +0.147] | -0.028 [-0.155, +0.160] | 0.507 [0.459, 0.555] |
| p | +0.097 [-0.488, +0.941] | +0.119 [-0.412, +2.094] | 0.482 [0.398, 0.614] |
| δ | +0.029 [-0.568, +0.617] | +0.029 [-0.563, +0.617] | 0.516 [0.353, 0.680] |

### Recsys h=40 (off-pre-reg)

| Witness | Cohen's d [BCa 95% CI] | Glass's d [BCa 95% CI] | Rank AUC [BCa 95% CI] |
|---|---|---|---|
| G | -0.214 [-0.235, -0.192] | -0.213 [-0.233, -0.192] | 0.441 [0.436, 0.447] |
| p | +0.180 [+0.155, +0.205] | +0.172 [+0.147, +0.197] | 0.555 [0.549, 0.562] |
| δ | -0.268 [-0.299, -0.237] | -0.219 [-0.245, -0.190] | 0.415 [0.407, 0.423] |

### **Recsys h=50 (canonical, pre-registered)**

| Witness | Cohen's d [BCa 95% CI] | Glass's d [BCa 95% CI] | Rank AUC [BCa 95% CI] |
|---|---|---|---|
| **G** | **+0.100 [+0.076, +0.124]** | **+0.112 [+0.084, +0.139]** | **0.519 [0.513, 0.525]** |
| **p** | **+0.080 [+0.049, +0.111]** | **+0.073 [+0.043, +0.102]** | **0.531 [0.523, 0.539]** |
| **δ** | **-0.168 [-0.208, -0.128]** | **-0.125 [-0.155, -0.095]** | **0.457 [0.447, 0.467]** |

### Recsys h=60 (off-pre-reg)

| Witness | Cohen's d [BCa 95% CI] | Glass's d [BCa 95% CI] | Rank AUC [BCa 95% CI] |
|---|---|---|---|
| G | +0.333 [+0.310, +0.354] | +0.453 [+0.411, +0.495] | 0.575 [0.570, 0.580] |
| p | +0.007 [-0.028, +0.043] | +0.006 [-0.026, +0.038] | 0.513 [0.504, 0.522] |
| δ | -0.029 [-0.072, +0.016] | -0.021 [-0.053, +0.011] | 0.508 [0.497, 0.520] |

## BCa-vs-percentile sensitivity

BCa correction matters where the bootstrap distribution is skewed (small n; right-skewed tails on small-n p-witness). Cells where |BCa endpoint − percentile endpoint| ≥ 0.05 on either side:

| Benchmark | Witness | Measure | Percentile CI | BCa CI | max Δ |
|---|---|---|---|---|---|
| Markets | p | glasss_d | [-0.492, +1.356] | [-0.412, +2.094] | 0.74 |
| Markets | p | cohens_d | [-0.589, +0.695] | [-0.488, +0.941] | 0.25 |

## Notes

- **Recsys BCa correction is empirically negligible.** Across all 27 recsys cells at n = 40,339, |BCa − percentile| < 0.01 on every endpoint. Consistent with BCa's O(1/√n) second-order correction theory: at this n the correction is below the bootstrap Monte Carlo noise floor. Percentile CIs would suffice for recsys; BCa is reported for completeness and procedural consistency with markets.

- **Markets BCa correction is substantive for the p witness.** The Glass's d markets p cell upper bound shifts from percentile +1.357 to BCa +2.094 (54% right-shift). Bootstrap distribution is right-skewed at n=54; percentile CIs systematically understate the right tail. BCa is the honest read here.

- **Canonical h=50 is the only configuration where all three witnesses align in the predicted direction with CIs clear of 0** (bolded above). Adjacent recsys horizons degrade asymmetrically: h=40 G flips sign while p and δ hold; h=60 G strengthens while p and δ collapse to null. The pre-registered horizon delivers the cleanest signature — evidence that pre-registration was load-bearing for the bridge claim.

- **Markets row-level effects are uniformly null** (all three witnesses, all three measures, all CIs span 0 or 0.5). The directional bridge claim for markets operates at unit-level aggregation grain (mean per unit, then compare unit means across the n=38+16 segments); the row-level effect-size table above is honest data at the finer grain. See main text Cross-domain evidence section for the unit-level framing.

---

**See also:** Figure 6 (effect-size forest plot, results/figures/a3_effect_size_forest.{png,pdf}); Cross-domain evidence section of the main manuscript.

---

## Supplementary Table S3

**Supplementary Table S3. Alert-count exact-matching sensitivity check.** Re-expression of the envelope-boundary matched-FP comparison (main-text Table 2) in integer alarm counts. For each panel at the canonical k = 3, Loopzero is reported at its envelope-boundary alarm counts (n_control_alarmed, n_event_alarmed); each comparator family's frozen pre-registered calibration grid is searched for the operating point with the nearest n_control_alarmed value, with status classified as `exact_match` (comparator has an operating point at Loopzero's exact alarm count), `bounded_gap` (Loopzero's alarm count falls between two adjacent comparator operating points, with `gap` quantifying the calibration coverage gap), `no_overlap_above` (all comparator operating points have higher alarm counts), or `insufficient_data`. On the markets benchmark, ac1_ews exhibits `exact_match` at Loopzero's envelope-boundary anchor: both methods alarm on exactly 9 of 38 controls and detect exactly 3 of 16 events. On the recommender benchmark, variance_ews exhibits the widest bounded gaps across Loopzero's envelope boundary: 3559 alarms at h = 40 (Loopzero at 97 of 6562 controls) and 3345 alarms at h = 60 (Loopzero at 2 of 3996 controls), in each case with the upper-bound comparator operating point detecting all panel event units (TPR = 1.0). At h = 50, no comparator family produced a non-trivial breakpoint at Loopzero's envelope-boundary FP of 0.002313; accordingly, h = 50 is reported for transparency but excluded from the cross-horizon comparator-envelope comparison. Full numerics rendered by `analysis/21_compute_a2_alert_count_exact.py` from frozen calibration data at `results/rendered/a4_roc_lowfp/a4_roc_data.parquet` and operating-point data at `results/rendered/bridge/a1_loopzero_operating_points{,_h40_h60}.csv`. Columns renamed in this rendering for compactness: `lower` and `upper` abbreviate `comp_lower` and `comp_upper`; `gap` abbreviates `gap_width_n_control`; `n_bp` abbreviates `n_breakpoints`.

Companion to `a2_threshold_path_envelope_boundary.{csv,md}`. Re-frames the envelope-boundary comparison in integer alarm counts to surface (a) discrete-FP-space coincidences as exact alarm-count matches, and (b) linear-interpolation gaps as quantitative gap widths in alarm-count space.

Comparator alarm counts derived from `round(fp_comp * panel.n_control_units)` and `round(tpr_comp * panel.n_event_units)`. Status legend:

- `loopzero_envelope_boundary` — Loopzero's anchor at panel max FP, k=3
- `exact_match` — comparator has a breakpoint at exactly Loopzero's alarm count
- `bounded_gap` — Loopzero's alarm count falls strictly between two adjacent comparator breakpoints; `gap` records the gap size
- `no_overlap_above` — all comparator breakpoints have higher alarm counts
- `no_overlap_below` — all comparator breakpoints have lower alarm counts
- `insufficient_data` — comparator has <1 useful breakpoint

## Panel: markets

Panel n_control_units=38, n_event_units=16. Loopzero at envelope boundary (q=50, k=3): **9 false alarms / 38 controls** (FP=0.236842), **3 true detections / 16 events** (TPR=0.1875).

| family | status | lower (ctrl, evt) | upper (ctrl, evt) | gap | n_bp |
|---|---|---|---|---|---|
| ac1_ews | exact_match | (9, 3) | (9, 3) | 0 | 25 |
| cusum | no_overlap_above | — | (14, 5) | — | 15 |
| page_hinkley | no_overlap_above | — | (26, 14) | — | 6 |
| variance_ews | no_overlap_above | — | (17, 5) | — | 20 |

## Panel: recsys_h40

Panel n_control_units=6562, n_event_units=33777. Loopzero at envelope boundary (q=50, k=3): **97 false alarms / 6562 controls** (FP=0.014782), **3113 true detections / 33777 events** (TPR=0.0922).

| family | status | lower (ctrl, evt) | upper (ctrl, evt) | gap | n_bp |
|---|---|---|---|---|---|
| ac1 | no_overlap_above | — | (4206, 33777) | — | 3 |
| cusum | no_overlap_above | — | (4010, 33777) | — | 4 |
| matrix_profile | no_overlap_above | — | (155, 3938) | — | 2 |
| page_hinkley | no_overlap_above | — | (4206, 33777) | — | 4 |
| permutation_entropy | no_overlap_above | — | (6562, 33777) | — | 1 |
| variance_ews | bounded_gap | (0, 0) | (3559, 33777) | 3559 | 6 |

## Panel: recsys_h50

Panel n_control_units=4755, n_event_units=35584. Loopzero at envelope boundary (q=50, k=3): **11 false alarms / 4755 controls** (FP=0.002313), **2681 true detections / 35584 events** (TPR=0.0753).

| family | status | lower (ctrl, evt) | upper (ctrl, evt) | gap | n_bp |
|---|---|---|---|---|---|
| _no comparator breakpoint at this boundary FP_ | `insufficient_data` | — | — | — | 0 |

## Panel: recsys_h60

Panel n_control_units=3996, n_event_units=36343. Loopzero at envelope boundary (q=50, k=3): **2 false alarms / 3996 controls** (FP=0.000501), **2004 true detections / 36343 events** (TPR=0.0551).

| family | status | lower (ctrl, evt) | upper (ctrl, evt) | gap | n_bp |
|---|---|---|---|---|---|
| ac1 | no_overlap_above | — | (3464, 36343) | — | 3 |
| cusum | no_overlap_above | — | (3430, 36343) | — | 4 |
| matrix_profile | no_overlap_above | — | (35, 3938) | — | 2 |
| page_hinkley | no_overlap_above | — | (3464, 36343) | — | 4 |
| permutation_entropy | no_overlap_above | — | (3996, 36343) | — | 1 |
| variance_ews | bounded_gap | (0, 0) | (3345, 36343) | 3345 | 6 |

---

## Supplementary Table S4

**Supplementary Table S4. Cluster-robust sensitivity at scenario grain (markets benchmark).** Per-witness effect sizes (Cohen's d, Glass's d, rank AUC) on the markets benchmark at the A3 segment grain (n = 54 segments) and the B3 scenario grain (n = 7 clusters: 2 event scenarios — `volmageddon_2018_xiv` with 8 segments and `covid_mwcb_2020_03_18` with 8 segments; 5 control scenarios — `covid_noncollapse_2020_03_11` with 8 segments, `volmageddon_control_2018_01_29` with 8 segments, `volmageddon_control_2018_02_08` with 8 segments, `covid_noncollapse_2020_03_13` with 7 segments, `volmageddon_control_2018_01_25` with 7 segments). Bootstrap iterations: 10,000 per cell; CI level: 0.95; RNG seed for scenario grain: 43 (distinct from A3 segment grain seed: 42). For `p`|Glass's d at scenario grain, 2 of 10,000 iterations produced degenerate samples (control SD ≈ 0 from same-scenario cluster resamples); finite-filter applied to remaining 9,998 iterations. All other 8 cells: n_degenerate = 0. Scenario-grain CIs are reported as sensitivity, not primary inference; the segment-grain baseline (Supplementary Table S2) remains the primary report.

## Cluster composition

Event-side scenario clusters (derived from `unit_id` parsing; n=2):

| Cluster | Segments |
|---------|----------|
| volmageddon_2018_xiv  | 8 |
| covid_mwcb_2020_03_18 | 8 |

Control-side scenario clusters (n=5):

| Cluster | Segments |
|---------|----------|
| covid_noncollapse_2020_03_11   | 8 |
| volmageddon_control_2018_01_29 | 8 |
| volmageddon_control_2018_02_08 | 8 |
| covid_noncollapse_2020_03_13   | 7 |
| volmageddon_control_2018_01_25 | 7 |

Total cluster units: 7 (2 event + 5 control), down from 54 segment units in A3.

## Methodological framing

Cluster-aware bootstrap (10,000 iterations) at scenario grain. Reported as a **dependence-sensitivity diagnostic** at n = 2 event clusters; at this sample size the bootstrap intervals are not reliable conservative inferential intervals. Wild cluster bootstrap (Cameron, Gelbach & Miller 2008) — the methodologically appropriate response to the small-cluster regime — is deferred to follow-up work.

## Effect sizes at scenario grain (B3)

| Witness | Measure   | Point | Percentile 95% CI | BCa 95% CI |
|---------|-----------|-------|-------------------|------------|
| G | cohens_d | -0.0293 | [-0.0916, +0.0489] | [-0.0932, +0.0473] |
| G | glasss_d | -0.0285 | [-0.0934, +0.0472] | [-0.0938, +0.0472] |
| G | rank_auc | +0.5073 | [+0.4569, +0.5581] | [+0.4520, +0.5530] |
| p | cohens_d | +0.0966 | [-0.3309, +0.4082] | [-0.3285, +0.4313] |
| p | glasss_d | +0.1188 | [-0.2952, +0.7102] | [-0.2950, +0.7102] |
| p | rank_auc | +0.4823 | [+0.4376, +0.5310] | [+0.4361, +0.5305] |
| delta | cohens_d | +0.0286 | [-0.1534, +0.1993] | [-0.1534, +0.1993] |
| delta | glasss_d | +0.0287 | [-0.1610, +0.1928] | [-0.1610, +0.1928] |
| delta | rank_auc | +0.5162 | [+0.4495, +0.5773] | [+0.4495, +0.5757] |

## Side-by-side: A3 segment grain vs B3 scenario grain (BCa 95% CI)

| Witness | Measure | A3 segment grain (n=54) | B3 scenario grain (n=7) | CI width ratio |
|---------|---------|--------------------------|--------------------------|----------------|
| G | cohens_d | [-0.1686, +0.1469] | [-0.0932, +0.0473] | 0.45× |
| G | glasss_d | [-0.1552, +0.1598] | [-0.0938, +0.0472] | 0.45× |
| G | rank_auc | [+0.4592, +0.5552] | [+0.4520, +0.5530] | 1.05× |
| p | cohens_d | [-0.4884, +0.9409] | [-0.3285, +0.4313] | 0.53× |
| p | glasss_d | [-0.4123, +2.0944] | [-0.2950, +0.7102] | 0.40× |
| p | rank_auc | [+0.3979, +0.6141] | [+0.4361, +0.5305] | 0.44× |
| delta | cohens_d | [-0.5682, +0.6167] | [-0.1534, +0.1993] | 0.30× |
| delta | glasss_d | [-0.5632, +0.6174] | [-0.1610, +0.1928] | 0.30× |
| delta | rank_auc | [+0.3527, +0.6799] | [+0.4495, +0.5757] | 0.39× |

---

### Supplementary Table S5. Reproducibility anchor hashes

Freeze-manifest SHA-256 hashes for the empirical components anchoring all results in this paper. Each frozen directory additionally contains a `LOCK_NOTE.md` documenting that freeze's scientific and editorial scope.

| Component | Freeze path | SHA-256 |
|---|---|---|
| Recsys benchmark freeze state (canonical) | `results/frozen/movielens25m_recursive_frontier_public_v1__benchmark_freeze_state.json` | `050aa725e6608f659b3f7eb103731bb7fbabaa23aeefdc4b11043999b7fed4cf` |
| Recsys contract freeze | `results/frozen/movielens25m_recursive_frontier_public_v1__contract_freeze.json` | `f361d937cc07cbb946753ac9e5e2d1d386c8706a6bb43841229ec846fd69ecd6` |
| Recsys manuscript freeze state | `results/frozen/movielens25m_recursive_frontier_public_v1__manuscript_freeze_state.json` | `bc8542cc0b76cdfad9726a4085c760d38ed7ace24772f0e3c6103fba962891b8` |
| Markets comparator merged state (v2) | `results/frozen/comparators/markets_comparator_merged_state_v2__20260421T174702Z/freeze_manifest.json` | `784895418953b1646bd40eb7b5266e39901326b1335b2ec5f2390b70af4642c7` |
| Markets fast robustness packet (v1) | `results/frozen/comparators/markets_fast_robustness_packet_v1__20260421T175531Z/freeze_manifest.json` | `f8f8c5c58d10796d4b71545282a8b352c47dc9590fc268fcb96cfb84c181adec` |
| Witness-direction bridge state (v3, canonical) | `results/frozen/bridge/witness_direction_bridge_state_v3__20260422T130759Z/freeze_manifest.json` | `bd47e75851fcaea1e6d843f9b74156ec036ddb487ca76e815d7b6fb0cf258f94` |
| Manuscript two-domain state (v1) | `results/frozen/manuscript/two_domain_paper_state_v1__20260422T134303Z/freeze_manifest.json` | `1763b04cb128a274dd12313a8cccdb2a04e2845d176d3444d6214e0aafe2e1d5` |
| Recsys horizon sensitivity manifest (covers h=40, h=50, h=60) | `results/manifests/movielens25m_recursive_frontier_public_v1__horizon_sensitivity_summary.json` | `b5d7ef3b5ca10f9e446a9792bc7d677a323913c66c087e753c6de944a8b7f215` |
| MovieLens-25M source archive (upstream) | `https://files.grouplens.org/datasets/movielens/ml-25m.zip` (GroupLens; not redistributed) | `8b21cfb7eb1706b4ec0aac894368d90acf26ebdfb6aced3ebd4ad5bd1eb9c6aa` |

Engine: `movielens_recursive_replay_engine` v1.0.0 (`item_item_collaborative_filtering`, hash `56c1cff225d60c09`). Recsys contract: SHA-256 `2e256b255a7f074c1516d70315ebb216241a4a7e8aba2db88b194417705fd71d`. All hashes are SHA-256 in lowercase hexadecimal.

---

*Generated 2026-05-28 alongside the main manuscript v17.17 render. Companion to the main paper PDF.*
