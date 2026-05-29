# Markets Fast Band Robustness State v1 Lock Note

This freeze captures the first frozen interpretation-layer robustness state for
the fast-family markets comparator branch after segmentation sensitivity and
band-sensitivity post-processing.

## Parent provenance
- parent merged comparator state: `markets_comparator_merged_state_v2`
- parent fast segmentation sensitivity state: `markets_fast_segmentation_sensitivity_state_v1`

## Scope
This state freezes:
- the canonical fast-family comparator result (120-minute benchmark)
- the 60-minute fast-family segmentation sensitivity result
- the 180-minute fast-family segmentation sensitivity result
- the band-sensitivity summary derived from frozen fast outputs
- the combined segmentation × band robustness table

## Canonical robustness statement
Under the locked equal-FP band `[0.03, 0.07]`, no tested fast-family comparator
configuration was accepted for:
- canonical 120-minute segmentation
- 60-minute segmentation
- 180-minute segmentation

Nearest fast-family comparator in all tested segmentation settings:
- family = `ac1_ews`

Nearest fast false-positive rates under the canonical band:
- canonical 120-minute: `0.131578947368421`
- 60-minute: `0.08`
- 180-minute: `0.1304347826086956`

## Relaxed-band sensitivity statement
Under post-processing bands widened to include an upper cutoff of `0.08`,
acceptance appeared only for the 60-minute segmentation:
- `[0.02, 0.08]`: `seg60` accepted
- `[0.04, 0.08]`: `seg60` accepted

Canonical 120-minute and 180-minute segmentations remained non-accepted across
all tested bands in this robustness layer.

## Interpretation boundary
This state supports a two-part scientific claim:
1. canonical robustness at the prespecified band `[0.03, 0.07]`
2. relaxed-band sensitivity under post hoc widening of the acceptable interval

It does not support a stronger claim of full invariance across tested bands.

## Governance
- archival and immutable
- any further robustness expansions should be written as a new state
