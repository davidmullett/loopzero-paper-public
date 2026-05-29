# Gate 2 Report — movielens25m_recursive_frontier_public_v1

**Decision:** `PASS`

**Recommended action:** No fast-family comparator achieved an accepted equal-FP operating point. The recommender branch remains viable as a corroborating flagship benchmark after fast-family testing. Proceed to slow-family full-grid evaluation.

## Fast-family verdict

- total_configs: `60`
- total_available_configs: `60`
- total_accepted_configs: `0`
- no_fast_family_accepted: `True`
- corroboration_survives_fast_families: `True`

## Overall nearest

- family: `variance_ews`
- config_id: `variance_ews__a92c1715`
- nontrivial: `False`
- control_fp: `0.0`
- band_distance: `0.03`
- event_alarm_rate: `0.0`

## Overall nearest nontrivial

- family: `variance_ews`
- config_id: `variance_ews__1a27323c`
- control_fp: `0.8370870870870871`
- band_distance: `0.7670870870870872`
- event_alarm_rate: `1.0`

## Per-family summary

### variance_ews

- n_configs: `15`
- n_available_configs: `15`
- n_accepted_configs: `0`
- nearest_config_id: `variance_ews__a92c1715`
- nearest_control_fp: `0.0`
- nearest_band_distance: `0.03`
- nearest_nontrivial_flag: `False`
- nearest_nontrivial_config_id: `variance_ews__1a27323c`
- nearest_nontrivial_control_fp: `0.8370870870870871`
- nearest_nontrivial_band_distance: `0.7670870870870872`

### ac1

- n_configs: `15`
- n_available_configs: `15`
- n_accepted_configs: `0`
- nearest_config_id: `ac1__9c410aa4`
- nearest_control_fp: `0.8668668668668669`
- nearest_band_distance: `0.7968668668668668`
- nearest_nontrivial_flag: `True`
- nearest_nontrivial_config_id: `ac1__9c410aa4`
- nearest_nontrivial_control_fp: `0.8668668668668669`
- nearest_nontrivial_band_distance: `0.7968668668668668`

### cusum

- n_configs: `15`
- n_available_configs: `15`
- n_accepted_configs: `0`
- nearest_config_id: `cusum__d0ad25c6`
- nearest_control_fp: `0.8583583583583584`
- nearest_band_distance: `0.7883583583583584`
- nearest_nontrivial_flag: `True`
- nearest_nontrivial_config_id: `cusum__d0ad25c6`
- nearest_nontrivial_control_fp: `0.8583583583583584`
- nearest_nontrivial_band_distance: `0.7883583583583584`

### page_hinkley

- n_configs: `15`
- n_available_configs: `15`
- n_accepted_configs: `0`
- nearest_config_id: `page_hinkley__1a3eb752`
- nearest_control_fp: `0.8668668668668669`
- nearest_band_distance: `0.7968668668668668`
- nearest_nontrivial_flag: `True`
- nearest_nontrivial_config_id: `page_hinkley__1a3eb752`
- nearest_nontrivial_control_fp: `0.8668668668668669`
- nearest_nontrivial_band_distance: `0.7968668668668668`

