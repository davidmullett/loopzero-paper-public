# Witness-Direction Summary: Shumailov 2024 Secondary Analysis

Source data: Shumailov et al. 2024, Nature, doi:10.1038/s41586-024-07566-y, Figure 1b/1c right panels (mean perplexity over 5 random-seed runs, 10 recursive generations).

Window labeling: **control** = generation 0 (Real wikitext2 baseline, pre-recursive); **event** = generations 1-9 (recursive synthetic training).

## Summary table

| Regime | Witness | Control window (g=0) | Event window (g>=1) | Predicted direction | Observed match |
|---|---|---|---|---|---|
| No preservation (Fig 1b) | G.1 amplification | 0 (baseline; G undefined for g<2) | 33.57 at g=2; 1.49 for g>=3 | large magnitude at phase transition, small at steady state | yes |
| No preservation (Fig 1b) | p.1 recursive persistence | 0.000 (no gap yet) | 0.752 (mean over event window); min = 0.661 (never relaxes to baseline) | rises to ~1 at onset; non-relaxing across trajectory | yes |
| No preservation (Fig 1b) | delta.1 diversity proxy | 25.97 (seeds converge to same baseline) | 1.96 (mean over event window); ratio control/event = 13.3x | declines at collapse onset (cross-seed coherence breaks) | yes |
| 10% preservation (Fig 1c) | G.1 amplification | 0 (baseline; G undefined for g<2) | 8.84 at g=2; 0.53 for g>=3 | large magnitude at phase transition, small at steady state | yes |
| 10% preservation (Fig 1c) | p.1 recursive persistence | 0.000 (no gap yet) | 0.567 (mean over event window); min = 0.360 (never relaxes to baseline) | rises to ~1 at onset; non-relaxing across trajectory | yes |
| 10% preservation (Fig 1c) | delta.1 diversity proxy | 86.00 (seeds converge to same baseline) | 5.72 (mean over event window); ratio control/event = 15.0x | declines at collapse onset (cross-seed coherence breaks) | yes |

## Interpretation

All three witnesses move in the predicted direction across the recursive-collapse transition in both regimes:

- **G.1** shows a sharp phase-transition signature (large |G| at g=2 vs near-zero at g>=3). The magnitude of the transition scales with collapse severity: ~3.8x larger in the no-preservation regime than in the 10%-preservation regime, consistent with the partial-preservation regime having a milder collapse.
- **p.1** rises from 0 at baseline to ~1 at gen 1 in both regimes, then partially relaxes. The plateau height differs by regime: ~0.7 (no-preservation, ~25% relaxation from peak) vs ~0.5 (10%-preservation, ~50% relaxation from peak). The non-relaxation gate is open in both cases - p never returns to baseline.
- **delta.1** declines sharply at collapse onset in both regimes (control/event ratio ~14x for no-preservation, ~15x for 10%-preservation). In the 10%-preservation regime delta partially recovers in later generations (gen >= 5) as seeds re-converge to a similar stable collapsed state - a graded prediction the framework allows but did not pre-register for this v1 analysis.

## Caveats

- This is a **secondary analysis** on values digitized from the paper's published figures, not raw author data. Numerical precision is limited to the digitization fidelity (X positions within ~0.03 of integer, Y positions to the visual gridline resolution).
- The **delta.1 proxy** measures inter-seed convergence of per-generation perplexity, not within-model output-distribution diversity. The direct distributional measurement (perplexity histograms in the left panels of Figure 1b/1c) was not digitized in this v1.
- No **comparator-acceptance evaluation under a matched false-positive contract** was conducted in this domain. The full matched-FP benchmark for the LLM-collapse domain is deferred to a follow-up extension.
