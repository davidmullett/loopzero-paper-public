# Markets Comparator State v1 (Canonical Freeze)

## Status
This snapshot represents the first valid comparator calibration state for markets.

## Key Outcomes
- v1 (probe-based) comparator input: INVALID (unreachable FP band due to n=6)
- v2 (segmented canonical input): VALID

## Calibration Results
- Equal-FP band: [0.03, 0.07]
- n_control_units: 38
- fp_grid_step: ~0.0263

## Findings
- No fast comparator family admits a configuration within the equal-FP band
- Closest fast comparator:
    - family: AC1
    - fp ≈ 0.131579
    - distance_to_band ≈ 0.061579

## Interpretation
This establishes a valid negative result:
Fast comparator families cannot be calibrated under equal-FP constraints in real segmented market data.

## Notes
- matrix_profile: deferred (slow comparator)
- permutation_entropy: deferred (slow comparator)

## Freeze Metadata
This snapshot is immutable and must be used for:
- paper tables
- reviewer artifacts
- reproducibility

