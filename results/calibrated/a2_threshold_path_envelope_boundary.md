# Table 2 — Envelope-boundary matched-FP comparison per panel

Loopzero is reported at its envelope-boundary operating point per panel (maximum control_fp across the extended q-grid [50,60,70,75,80,85,90,95,99] at the canonical k=3). Comparator families are interpolated at the same FP where envelope overlap exists, or marked `no_overlap_*` otherwise. Status legend: `loopzero_envelope_boundary` = Loopzero's anchor at max FP; `interpolated` = comparator interpolated at Loopzero boundary FP; `no_overlap_comparator_above_loopzero_envelope` = comparator min FP exceeds Loopzero's boundary FP. Breakpoints reported alongside for transparency.

## Panel: markets

Loopzero envelope boundary at k=3: FP=0.236842 (q=50), TPR=0.1875

| family | TPR @ FP | status | lower (fp, tpr) | upper (fp, tpr) |
|---|---|---|---|---|
| loopzero | 0.1875 | loopzero_envelope_boundary | — | — |
| ac1_ews | 0.1875 | at_observed_fp | (0.1842, 0.0625) | (0.2368, 0.1875) |
| cusum | — | no_overlap_comparator_above_loopzero_envelope | — | (0.3684, 0.3125) |
| page_hinkley | — | no_overlap_comparator_above_loopzero_envelope | — | (0.6842, 0.8750) |
| variance_ews | — | no_overlap_comparator_above_loopzero_envelope | — | (0.4474, 0.3125) |

## Panel: recsys_h40

Loopzero envelope boundary at k=3: FP=0.014782 (q=50), TPR=0.0922

| family | TPR @ FP | status | lower (fp, tpr) | upper (fp, tpr) |
|---|---|---|---|---|
| loopzero | 0.0922 | loopzero_envelope_boundary | — | — |
| ac1 | — | no_overlap_comparator_above_loopzero_envelope | — | (0.6410, 1.0000) |
| cusum | — | no_overlap_comparator_above_loopzero_envelope | — | (0.6111, 1.0000) |
| matrix_profile | — | no_overlap_comparator_above_loopzero_envelope | — | (0.0236, 0.1166) |
| page_hinkley | — | no_overlap_comparator_above_loopzero_envelope | — | (0.6410, 1.0000) |
| permutation_entropy | — | insufficient_data | — | — |
| variance_ews | 0.0273 | interpolated | (0.0000, 0.0000) | (0.5424, 1.0000) |

## Panel: recsys_h50

Loopzero envelope boundary at k=3: FP=0.002313 (q=50), TPR=0.0753

| family | TPR @ FP | status | lower (fp, tpr) | upper (fp, tpr) |
|---|---|---|---|---|
| loopzero | 0.0753 | loopzero_envelope_boundary | — | — |

## Panel: recsys_h60

Loopzero envelope boundary at k=3: FP=0.000501 (q=50), TPR=0.0551

| family | TPR @ FP | status | lower (fp, tpr) | upper (fp, tpr) |
|---|---|---|---|---|
| loopzero | 0.0551 | loopzero_envelope_boundary | — | — |
| ac1 | — | no_overlap_comparator_above_loopzero_envelope | — | (0.8669, 1.0000) |
| cusum | — | no_overlap_comparator_above_loopzero_envelope | — | (0.8584, 1.0000) |
| matrix_profile | — | no_overlap_comparator_above_loopzero_envelope | — | (0.0088, 0.1084) |
| page_hinkley | — | no_overlap_comparator_above_loopzero_envelope | — | (0.8669, 1.0000) |
| permutation_entropy | — | insufficient_data | — | — |
| variance_ews | 0.0006 | interpolated | (0.0000, 0.0000) | (0.8371, 1.0000) |
