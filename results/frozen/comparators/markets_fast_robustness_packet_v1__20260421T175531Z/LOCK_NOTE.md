# Markets Fast Robustness Packet v1 Lock Note

This packet is the manuscript-facing freeze for the fast-family robustness branch
of the canonical markets comparator benchmark.

## Parent provenance
- parent robustness state: `markets_fast_band_robustness_state_v1`

## Packet contents
This packet freezes:
- the band-sensitivity summary (`markets_fast_band_sensitivity_summary_v1`)
- the combined segmentation × band robustness table (`markets_fast_segmentation_band_robustness_table_v1`)
- parent provenance artifacts sufficient to audit the robustness interpretation

## Scientific conclusion supported by this packet

### Canonical robustness
Under the prespecified equal-FP band `[0.03, 0.07]`, no tested fast-family
comparator configuration was accepted for:
- canonical 120-minute segmentation
- 60-minute segmentation
- 180-minute segmentation

In all tested segmentation settings, the nearest fast family remained `ac1_ews`.

### Relaxed-band sensitivity
Under widened post-processing bands that included an upper cutoff of `0.08`,
acceptance appeared only for the 60-minute segmentation:
- `[0.02, 0.08]`: `seg60` accepted
- `[0.04, 0.08]`: `seg60` accepted

Canonical 120-minute and 180-minute segmentation remained non-accepted across
all tested bands in this packet.

## Editorial boundary
This packet supports:
1. canonical robustness at the locked prespecified band `[0.03, 0.07]`
2. relaxed-band sensitivity under post hoc band widening

It does not support a stronger claim of full invariance across tested bands.

## Governance
- archival and immutable
- manuscript wording should cite this packet, not mutable rendered files
