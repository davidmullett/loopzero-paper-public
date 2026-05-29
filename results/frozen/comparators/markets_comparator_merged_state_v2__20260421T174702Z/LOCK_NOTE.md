# Markets Comparator Merged State v2 Lock Note

This freeze captures the merged comparator state for the canonical markets benchmark
after completion of the full-grid slow-family pass.

## Canonical benchmark
- Instantiation: `volmageddon_covid_public_v2`
- locked equal-FP band = `[0.03, 0.07]`
- n_control_units = `38`
- n_event_units = `16`
- fp_grid_step = `0.0263157894736842`
- calibration_semantics: full_benchmark_all_units (fp_cal computed over all 38 control units; per-unit rolling-quantile thresholds; no held-out partition)

## Comparator conclusion
- any_family_accepted = `0`
- best_fast_family = `ac1_ews`
- best_fast_fp = `0.131578947368421`
- best_fast_config_id = `ac1_ews__632f23b2`
- best_fast_distance_to_band = `0.061578947368421`

## Slow-family interpretation
- nearest_numeric_slow_configs_are_trivial_silent = `1`
- numeric_nearest_slow_families_tied = `matrix_profile; permutation_entropy`
- numeric_nearest_slow_config_ids_tied = `matrix_profile__0a536aa4; permutation_entropy__001577c8`
- numeric_nearest_slow_distance_to_band = `0.03`
- best_nontrivial_slow_family = `permutation_entropy`
- best_nontrivial_slow_fp = `0.3684210526315789`
- best_nontrivial_slow_config_id = `permutation_entropy__259c1b96`
- best_nontrivial_slow_distance_to_band = `0.2984210526315789`

## Best nontrivial comparator overall
- best_nontrivial_family = `ac1_ews`
- best_nontrivial_fp = `0.131578947368421`
- best_nontrivial_config_id = `ac1_ews__632f23b2`
- best_nontrivial_distance_to_band = `0.061578947368421`

## Editorially bounded statement
On the canonical segmented markets benchmark, no tested fast or slow comparator configuration
achieved the locked equal-FP operating band. The nearest nontrivial comparator remained
`ac1_ews` at FP = `0.131578947368421` with config
`ac1_ews__632f23b2`. The numerically nearest slow configurations were tied
across `matrix_profile; permutation_entropy` and were trivial-silent, while the best
nontrivial slow family remained `permutation_entropy` and still sat materially
above band.

## Governance
- This freeze is archival and immutable.
- Any further comparator expansion should be written as a new state.
