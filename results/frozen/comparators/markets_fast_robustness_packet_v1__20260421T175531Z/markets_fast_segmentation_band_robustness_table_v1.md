# Markets fast segmentation × band robustness table v1

Combined robustness table with one row per `(band, segmentation)` pair.

Derived from `results/rendered/comparators/markets_fast_band_sensitivity_summary_v1.csv`.

| Band | Segmentation | Controls | Events | FP grid step | Band reachable | Accepted | Nearest fast | Nearest FP | Distance to band | Control alarms | Event alarms | Interpretation |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| [0.03, 0.07] | canonical_120 | 38 | 16 | 0.026316 | 1 | 0 | ac1_ews | 0.131579 | 0.061579 | 5/38 | 1/16 | canonical fail |
| [0.03, 0.07] | seg60 | 75 | 32 | 0.013333 | 1 | 0 | ac1_ews | 0.080000 | 0.010000 | 6/75 | 1/32 | canonical fail |
| [0.03, 0.07] | seg180 | 23 | 10 | 0.043478 | 1 | 0 | ac1_ews | 0.130435 | 0.060435 | 3/23 | 1/10 | canonical fail |
| [0.02, 0.08] | canonical_120 | 38 | 16 | 0.026316 | 1 | 0 | ac1_ews | 0.131579 | 0.051579 | 5/38 | 1/16 | stable fail across tested bands |
| [0.02, 0.08] | seg60 | 75 | 32 | 0.013333 | 1 | 1 | ac1_ews | 0.080000 | 0.000000 | 6/75 | 1/32 | relaxed-band only acceptance |
| [0.02, 0.08] | seg180 | 23 | 10 | 0.043478 | 1 | 0 | ac1_ews | 0.130435 | 0.050435 | 3/23 | 1/10 | stable fail across tested bands |
| [0.04, 0.08] | canonical_120 | 38 | 16 | 0.026316 | 1 | 0 | ac1_ews | 0.131579 | 0.051579 | 5/38 | 1/16 | stable fail across tested bands |
| [0.04, 0.08] | seg60 | 75 | 32 | 0.013333 | 1 | 1 | ac1_ews | 0.080000 | 0.000000 | 6/75 | 1/32 | relaxed-band only acceptance |
| [0.04, 0.08] | seg180 | 23 | 10 | 0.043478 | 1 | 0 | ac1_ews | 0.130435 | 0.050435 | 3/23 | 1/10 | stable fail across tested bands |

## Reading note
- `accepted` is recomputed per tested band from the frozen fast outputs.
- `canonical fail` means the segmentation is not accepted under the canonical band `[0.03, 0.07]`.
- `relaxed-band only acceptance` means acceptance appears only after widening the band beyond the canonical specification.
- `stable fail across tested bands` means the segmentation never reaches any tested band in this post-processing layer.
