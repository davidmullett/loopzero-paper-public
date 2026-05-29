# Supplementary Table S2 — Effect sizes with bootstrap 95% BCa CIs

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
- **Recsys** (all horizons): user-level resampling (n ≈ 40,339 user clusters; 10 rows per cluster)

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

- **Recsys BCa correction is empirically negligible.** Across all 27 recsys cells at n ≈ 40K, |BCa − percentile| < 0.01 on every endpoint. Consistent with BCa's O(1/√n) second-order correction theory: at this n the correction is below the bootstrap Monte Carlo noise floor. Percentile CIs would suffice for recsys; BCa is reported for completeness and procedural consistency with markets.

- **Markets BCa correction is substantive for the p witness.** The Glass's d markets p cell upper bound shifts from percentile +1.357 to BCa +2.094 (54% right-shift). Bootstrap distribution is right-skewed at n=54; percentile CIs systematically understate the right tail. BCa is the honest read here.

- **Canonical h=50 is the only configuration where all three witnesses align in the predicted direction with CIs clear of 0** (bolded above). Adjacent recsys horizons degrade asymmetrically: h=40 G flips sign while p and δ hold; h=60 G strengthens while p and δ collapse to null. The pre-registered horizon delivers the cleanest signature — evidence that pre-registration was load-bearing for the bridge claim.

- **Markets row-level effects are uniformly null** (all three witnesses, all three measures, all CIs span 0 or 0.5). The directional bridge claim for markets operates at unit-level aggregation grain (mean per unit, then compare unit means across the n=38+16 segments); the row-level effect-size table above is honest data at the finer grain. See main text Cross-domain evidence section for the unit-level framing.

---

**See also:** Figure [N] (effect-size forest plot, results/figures/a3_effect_size_forest.{png,pdf}); Cross-domain evidence section of the main manuscript.
