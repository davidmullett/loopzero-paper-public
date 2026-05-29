# A2 — Alert-count exact-matching sensitivity check

Companion to `a2_threshold_path_envelope_boundary.{csv,md}`. Re-frames the envelope-boundary comparison in integer alarm counts to surface (a) discrete-FP-space coincidences as exact alarm-count matches, and (b) linear-interpolation gaps as quantitative gap widths in alarm-count space.

Comparator alarm counts derived from `round(fp_comp * panel.n_control_units)` and `round(tpr_comp * panel.n_event_units)`. Status legend:

- `loopzero_envelope_boundary` — Loopzero's anchor at panel max FP, k=3
- `exact_match` — comparator has a breakpoint at exactly Loopzero's alarm count
- `bounded_gap` — Loopzero's alarm count falls strictly between two adjacent comparator breakpoints; `gap_width_n_control` records the gap size
- `no_overlap_above` — all comparator breakpoints have higher alarm counts
- `no_overlap_below` — all comparator breakpoints have lower alarm counts
- `insufficient_data` — comparator has <1 useful breakpoint

## Panel: markets

Panel n_control_units=38, n_event_units=16. Loopzero at envelope boundary (q=50, k=3): **9 false alarms / 38 controls** (FP=0.236842), **3 true detections / 16 events** (TPR=0.1875).

| family | status | comp_lower (n_control, n_event) | comp_upper (n_control, n_event) | gap_width_n_control | n_breakpoints |
|---|---|---|---|---|---|
| ac1_ews | exact_match | (9, 3) | (9, 3) | 0 | 25 |
| cusum | no_overlap_above | — | (14, 5) | — | 15 |
| page_hinkley | no_overlap_above | — | (26, 14) | — | 6 |
| variance_ews | no_overlap_above | — | (17, 5) | — | 20 |

## Panel: recsys_h40

Panel n_control_units=6562, n_event_units=33777. Loopzero at envelope boundary (q=50, k=3): **97 false alarms / 6562 controls** (FP=0.014782), **3113 true detections / 33777 events** (TPR=0.0922).

| family | status | comp_lower (n_control, n_event) | comp_upper (n_control, n_event) | gap_width_n_control | n_breakpoints |
|---|---|---|---|---|---|
| ac1 | no_overlap_above | — | (4206, 33777) | — | 3 |
| cusum | no_overlap_above | — | (4010, 33777) | — | 4 |
| matrix_profile | no_overlap_above | — | (155, 3938) | — | 2 |
| page_hinkley | no_overlap_above | — | (4206, 33777) | — | 4 |
| permutation_entropy | no_overlap_above | — | (6562, 33777) | — | 1 |
| variance_ews | bounded_gap | (0, 0) | (3559, 33777) | 3559 | 6 |

## Panel: recsys_h50

Panel n_control_units=4755, n_event_units=35584. Loopzero at envelope boundary (q=50, k=3): **11 false alarms / 4755 controls** (FP=0.002313), **2681 true detections / 35584 events** (TPR=0.0753).

| family | status | comp_lower (n_control, n_event) | comp_upper (n_control, n_event) | gap_width_n_control | n_breakpoints |
|---|---|---|---|---|---|

## Panel: recsys_h60

Panel n_control_units=3996, n_event_units=36343. Loopzero at envelope boundary (q=50, k=3): **2 false alarms / 3996 controls** (FP=0.000501), **2004 true detections / 36343 events** (TPR=0.0551).

| family | status | comp_lower (n_control, n_event) | comp_upper (n_control, n_event) | gap_width_n_control | n_breakpoints |
|---|---|---|---|---|---|
| ac1 | no_overlap_above | — | (3464, 36343) | — | 3 |
| cusum | no_overlap_above | — | (3430, 36343) | — | 4 |
| matrix_profile | no_overlap_above | — | (35, 3938) | — | 2 |
| page_hinkley | no_overlap_above | — | (3464, 36343) | — | 4 |
| permutation_entropy | no_overlap_above | — | (3996, 36343) | — | 1 |
| variance_ews | bounded_gap | (0, 0) | (3345, 36343) | 3345 | 6 |
