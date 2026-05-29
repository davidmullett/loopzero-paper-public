# A2 — Threshold-path comparator calibration (Path A+C v2)

## Goal

Replace band-reachability with threshold-path calibration at FPR=0.05.

## Path A+C v2 — locked after Day 1 audit (2026-05-21)

After Day 1 audit revealed that (a) most comparator (family, benchmark, horizon)
cells do not bracket FPR=0.05 in existing calibration data, and (b) the recsys
comparator calibration pipeline is not in the public repo (frozen state preserved
for byte-exact reproducibility), the strategic path is A+C v2:

- **EXTEND**: Loopzero q-grid only, within its design envelope.
- **REPORT directly**: comparator cells where the frozen calibration data already
  brackets FPR=0.05.
- **ACKNOWLEDGE**: comparator cells where the frozen calibration data does not
  bracket — reported as a structural property of the standard EWS comparator
  literature.

This preserves the frozen-state byte-exact reproducibility of the comparator
calibration matrices while extending Loopzero within its own parameter design
space.

## EXTEND target

- **Loopzero q-grid**: `Q_GRID_PCT = [90, 95, 99]` → `[50, 60, 70, 75, 80, 85, 90, 95, 99]`
  in `analysis/14_build_a1_quantile_detector_v1.py` line 112. k=3 fixed. Joint
  quantile across G (high), p (high), δ (low: `q_delta_pct = 100 - q`).
- Single edit point. `analysis/14b_a1_recsys_horizon_variants.py` reuses the
  canonical detector via importlib, so markets canonical + recsys h=40/h=50/h=60
  all pick up the new q values automatically.

## REPORT directly (existing data brackets FPR=0.05)

| Cell | Bracketing | Notes |
|---|---|---|
| variance_ews recsys h=40 | 5/5 | full sweep available |
| variance_ews recsys h=60 | 5/5 | full sweep available |
| matrix_profile recsys h=60 | 5/5 | full sweep available |
| matrix_profile recsys h=40 | 4/5 | FPR ∈ {0.025, 0.05, 0.075, 0.10} reportable; FPR=0.01 below min, omitted with note |

## ACKNOWLEDGE (data does not bracket, frozen state preserved)

| Cell | Status |
|---|---|
| markets ac1_ews | min FP = 0.13; standard grid does not reach low-FP region |
| markets cusum | min FP = 0.37 |
| markets page_hinkley | min FP = 0.68 |
| markets variance_ews | min FP = 0.45 |
| recsys ac1 h=40, h=60 | min FP > 0.64 |
| recsys cusum h=40, h=60 | min FP > 0.61 |
| recsys page_hinkley h=40, h=60 | min FP > 0.64 |
| recsys permutation_entropy h=40, h=60 | 1 unique FP only |
| recsys h=50 canonical (5 families) | sparse markers only (full grid not retained on disk post-summarization) |

## Methodological argument (defends Path A+C v2 against rigorous review)

Loopzero's quantile detector admits parameter extension within its design
envelope: `q ∈ [50, 99]` is the full percentile range the detector is
mathematically defined for. We extend the q-grid to produce a continuous ROC
envelope and report threshold-path event detection at FPR=0.05 on this envelope.

Standard EWS comparator families operate from frozen calibration matrices
produced by pre-registered parameter grids. We do not extend these grids
post-hoc, since doing so would either compromise byte-exact reproducibility of
the frozen state or constitute research-grade extension into parameter regimes
outside the original method papers' recommendations.

Of the (family, benchmark, horizon) combinations where the frozen calibration
grid brackets FPR=0.05, threshold-path event detection rates are reported
directly via linear interpolation. The remainder are acknowledged as a
structural property of the standard EWS comparator literature: pre-registered
parameter grids in the EWS field span the high-FP regime; reaching FPR=0.05
would require parameter regimes the original method papers do not address.

## Day-by-day execution

- **Day 1 (today, ~half-day):** audit + scope freeze + commit
- **Day 2:** Loopzero q-grid extension; re-run; validate byte-exact reproducibility for q ∈ {90, 95, 99}
- **Day 3:** Threshold-path computation (`analysis/20_compute_a2_threshold_path.py`)
- **Day 4:** Alert-count exact matching sensitivity check (`analysis/21_compute_a2_alert_count_exact.py`)
- **Day 5:** Manuscript integration

## Outputs

- `results/rendered/a2_threshold_path/day1_audit_output.txt` — saved audit output (this commit)
- `results/rendered/bridge/a1_loopzero_operating_points_extended_q.csv` — extended Loopzero ops (Day 2)
- `results/calibrated/a2_threshold_path_results.csv` — threshold-path numbers at FPR sweep (Day 3)
- `results/calibrated/a2_alert_count_exact_results.csv` — alert-count sensitivity (Day 4)
- Manuscript updates (Day 5)
