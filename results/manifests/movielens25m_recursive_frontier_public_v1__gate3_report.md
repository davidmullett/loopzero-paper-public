# Gate 3 Report — movielens25m_recursive_frontier_public_v1

**Decision:** `PASS_WITH_QUALIFICATION`

**Final framing:** `corroborating_second_flagship_benchmark_with_bounded_bridge_sensitivity`

**Recommended action:** The recommender branch supports a corroborating second flagship benchmark on the comparator claim, with a bounded robustness qualification on the theorem-to-observable bridge under adjacent horizon shortening. Proceed to manuscript freeze using qualified robustness language.

## Adjudication

- all_horizons_no_accept: `True`
- all_horizons_bridge_pass: `False`
- bounded_bridge_sensitivity: `True`
- canonical_bridge_pass: `True`
- h40_bridge_pass: `False`
- h60_bridge_pass: `True`

## Horizon-by-horizon summary

### canonical_50

- bridge_decision: `PASS`
- bridge_aligned_count: `3`
- accepted_comparator_count: `0`
- no_comparator_accepted: `True`
- nearest_family: `matrix_profile`
- nearest_config_id: `matrix_profile__44b81bd6`
- nearest_control_fp: `0.013669821240799159`
- nearest_band_distance: `0.016330178759200842`

### horizon_40

- bridge_decision: `PARTIAL`
- bridge_aligned_count: `2`
- accepted_comparator_count: `0`
- no_comparator_accepted: `True`
- nearest_family: `matrix_profile`
- nearest_config_id: `matrix_profile__44b81bd6`
- nearest_control_fp: `0.02362084730265163`
- nearest_band_distance: `0.006379152697348369`

### horizon_60

- bridge_decision: `PASS`
- bridge_aligned_count: `3`
- accepted_comparator_count: `0`
- no_comparator_accepted: `True`
- nearest_family: `matrix_profile`
- nearest_config_id: `matrix_profile__44b81bd6`
- nearest_control_fp: `0.008758758758758759`
- nearest_band_distance: `0.02124124124124124`

## Canonical comparator context

- total_accepted_configs: `0`
- overall_nearest_family: `matrix_profile`
- overall_nearest_config_id: `matrix_profile__44b81bd6`
- overall_nearest_control_fp: `0.013669821240799159`
- overall_nearest_band_distance: `0.016330178759200842`
- overall_nearest_nontrivial_family: `matrix_profile`
- overall_nearest_nontrivial_config_id: `matrix_profile__44b81bd6`
- overall_nearest_nontrivial_control_fp: `0.013669821240799159`
- overall_nearest_nontrivial_band_distance: `0.016330178759200842`

