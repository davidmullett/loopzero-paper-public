# Markets fast band sensitivity summary v1

Band-sensitivity post-processing across frozen fast-family outputs for canonical 120-minute units and 60-minute / 180-minute segmentation variants.

Derived from frozen robustness branch: `results/frozen/comparators/markets_fast_segmentation_sensitivity_state_v1__LATEST.txt`.

| Band | Segmentation | Controls | Events | FP grid step | Band reachable | Any accepted | Nearest fast family | Nearest FP | Nearest config | Distance to band | Control alarms | Event alarms | Interpretation |
|---|---|---:|---:|---:|---:|---:|---|---:|---|---:|---:|---:|---|
| [0.02, 0.08] | seg60 | 75 | 32 | 0.013333 | 1 | 1 | ac1_ews | 0.080000 | ac1_ews__1665d7f2 | 0.000000 | 6/75 | 1/32 | At least one fast comparator reaches the specified equal-FP band. |
| [0.02, 0.08] | canonical_120 | 38 | 16 | 0.026316 | 1 | 0 | ac1_ews | 0.131579 | ac1_ews__632f23b2 | 0.051579 | 5/38 | 1/16 | No fast comparator accepted; nearest fast comparator remained outside band. |
| [0.02, 0.08] | seg180 | 23 | 10 | 0.043478 | 1 | 0 | ac1_ews | 0.130435 | ac1_ews__80bc0069 | 0.050435 | 3/23 | 1/10 | No fast comparator accepted; nearest fast comparator remained outside band. |
| [0.03, 0.07] | seg60 | 75 | 32 | 0.013333 | 1 | 0 | ac1_ews | 0.080000 | ac1_ews__1665d7f2 | 0.010000 | 6/75 | 1/32 | No fast comparator accepted; nearest fast comparator remained outside band. |
| [0.03, 0.07] | canonical_120 | 38 | 16 | 0.026316 | 1 | 0 | ac1_ews | 0.131579 | ac1_ews__632f23b2 | 0.061579 | 5/38 | 1/16 | No fast comparator accepted; nearest fast comparator remained outside band. |
| [0.03, 0.07] | seg180 | 23 | 10 | 0.043478 | 1 | 0 | ac1_ews | 0.130435 | ac1_ews__80bc0069 | 0.060435 | 3/23 | 1/10 | No fast comparator accepted; nearest fast comparator remained outside band. |
| [0.04, 0.08] | seg60 | 75 | 32 | 0.013333 | 1 | 1 | ac1_ews | 0.080000 | ac1_ews__1665d7f2 | 0.000000 | 6/75 | 1/32 | At least one fast comparator reaches the specified equal-FP band. |
| [0.04, 0.08] | canonical_120 | 38 | 16 | 0.026316 | 1 | 0 | ac1_ews | 0.131579 | ac1_ews__632f23b2 | 0.051579 | 5/38 | 1/16 | No fast comparator accepted; nearest fast comparator remained outside band. |
| [0.04, 0.08] | seg180 | 23 | 10 | 0.043478 | 1 | 0 | ac1_ews | 0.130435 | ac1_ews__80bc0069 | 0.050435 | 3/23 | 1/10 | No fast comparator accepted; nearest fast comparator remained outside band. |

## Reading note
- `Band reachable` indicates whether the specified equal-FP interval is attainable at that control-unit resolution.
- `Any accepted` is recomputed directly from `fp_cal` for each band; this is a post-processing robustness layer and does not rerun calibration.
- Tied nearest configs are preserved in the CSV via `nearest_fast_config_ids_tied` and `nearest_fast_family_tied`.
