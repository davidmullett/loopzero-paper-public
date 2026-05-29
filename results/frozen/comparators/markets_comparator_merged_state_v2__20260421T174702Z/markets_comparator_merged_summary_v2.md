# Markets comparator merged summary v2

Merged one-row canonical summary across fast-pass and full-grid slow-pass comparator calibration.

| field | value |
|---|---:|
| instantiation | volmageddon_covid_public_v2 |
| slow_artifact_source | results/rendered/comparators/markets_slow_comparator_calibration_fullgrid_v1.csv |
| fp_band | [0.03, 0.07] |
| n_control_units | 38 |
| n_event_units | 16 |
| fp_grid_step | 0.0263157894736842 |
| any_family_accepted | 0 |
| accepted_families |  |
| best_fast_family | ac1_ews |
| best_fast_fp | 0.131578947368421 |
| best_fast_config_id | ac1_ews__632f23b2 |
| best_fast_distance_to_band | 0.061578947368421 |
| nearest_numeric_slow_configs_are_trivial_silent | 1 |
| numeric_nearest_slow_families_tied | matrix_profile; permutation_entropy |
| numeric_nearest_slow_config_ids_tied | matrix_profile__0a536aa4; permutation_entropy__001577c8 |
| numeric_nearest_slow_distance_to_band | 0.03 |
| best_nontrivial_slow_family | permutation_entropy |
| best_nontrivial_slow_fp | 0.3684210526315789 |
| best_nontrivial_slow_config_id | permutation_entropy__259c1b96 |
| best_nontrivial_slow_distance_to_band | 0.2984210526315789 |
| best_nontrivial_family | ac1_ews |
| best_nontrivial_fp | 0.131578947368421 |
| best_nontrivial_config_id | ac1_ews__632f23b2 |
| best_nontrivial_distance_to_band | 0.061578947368421 |
| any_family_silent_only | 0 |
| silent_only_families |  |
| silent_only_slow_families |  |

## Reading note
- `slow_artifact_source` identifies the exact slow comparator artifact used for this merged state.
- `best_fast_family` is the nearest fast-family comparator under the locked equal-FP rule.
- `nearest_numeric_slow_configs_are_trivial_silent` indicates whether the numerically nearest slow configs are all trivial-silent.
- `numeric_nearest_slow_families_tied` lists slow families tied at the nearest numeric distance to band.
- `best_nontrivial_slow_family` excludes silent slow configurations and requires at least one event alarm unit.
- `best_nontrivial_family` excludes trivial silent configurations across all tested families and requires at least one event alarm unit.
- `any_family_accepted` indicates whether any tested family admits an accepted config.
- `any_family_silent_only` indicates whether any family is silent across all evaluated configs.
