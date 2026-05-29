# Intraday v2 ingredient packet

- scan_family: `equity_dislocations_intraday_v2_valid`
- breadth_event_min_share: `0.5`
- min_run_length: `3`

## Intent
- compare true events vs killer controls at the raw ingredient level
- inspect whether killer controls are cascade look-alikes, broad downside days, or vol-complex dominance cases

## primary_near_miss_cfg_001339
- config_id: `cfg_001339`
- thresholds: `{"delta_window": 30, "eps_g": 0.15, "g_window": 30, "k_consec_alarm": 5, "p_min": 0.02, "p_window": 60, "p_z_threshold": 1.0, "tau_delta": -0.02, "tau_p": 0.0, "warmup_bars": 0}`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_001339__volmageddon_2018_xiv.packet.csv`
### volmageddon_2018_xiv (event)
- rows: `943`
- start_ts_utc: `2018-02-05T09:00:00Z`
- end_ts_utc: `2018-02-06T01:00:00Z`
- collapse_ts_utc: `2018-02-05T22:09:00Z`
- control_source: `None`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_001339__covid_mwcb_2020_03_18.packet.csv`
### covid_mwcb_2020_03_18 (event)
- rows: `937`
- start_ts_utc: `2020-03-18T08:00:00Z`
- end_ts_utc: `2020-03-19T00:00:00Z`
- collapse_ts_utc: `2020-03-18T16:56:17Z`
- control_source: `None`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_001339__covid_noncollapse_2020_03_11.packet.csv`
### covid_noncollapse_2020_03_11 (control)
- rows: `955`
- start_ts_utc: `2020-03-11T08:00:00Z`
- end_ts_utc: `2020-03-12T00:00:00Z`
- collapse_ts_utc: `None`
- control_source: `current`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_001339__covid_noncollapse_2020_03_13.packet.csv`
### covid_noncollapse_2020_03_13 (control)
- rows: `840`
- start_ts_utc: `2020-03-13T08:00:00Z`
- end_ts_utc: `2020-03-14T00:00:00Z`
- collapse_ts_utc: `None`
- control_source: `current`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_001339__volmageddon_control_2018_01_25.packet.csv`
### volmageddon_control_2018_01_25 (control)
- rows: `751`
- start_ts_utc: `2018-01-25T09:00:00Z`
- end_ts_utc: `2018-01-26T01:00:00Z`
- collapse_ts_utc: `None`
- control_source: `backfill`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_001339__volmageddon_control_2018_01_29.packet.csv`
### volmageddon_control_2018_01_29 (control)
- rows: `857`
- start_ts_utc: `2018-01-29T09:00:00Z`
- end_ts_utc: `2018-01-30T01:00:00Z`
- collapse_ts_utc: `None`
- control_source: `current`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_001339__volmageddon_control_2018_02_08.packet.csv`
### volmageddon_control_2018_02_08 (control)
- rows: `933`
- start_ts_utc: `2018-02-08T09:00:00Z`
- end_ts_utc: `2018-02-09T01:00:00Z`
- collapse_ts_utc: `None`
- control_source: `current`

## corroborating_cfg_002053
- config_id: `cfg_002053`
- thresholds: `{"delta_window": 45, "eps_g": 0.15, "g_window": 30, "k_consec_alarm": 5, "p_min": 0.02, "p_window": 60, "p_z_threshold": 1.0, "tau_delta": -0.05, "tau_p": 0.0, "warmup_bars": 0}`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_002053__volmageddon_2018_xiv.packet.csv`
### volmageddon_2018_xiv (event)
- rows: `943`
- start_ts_utc: `2018-02-05T09:00:00Z`
- end_ts_utc: `2018-02-06T01:00:00Z`
- collapse_ts_utc: `2018-02-05T22:09:00Z`
- control_source: `None`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_002053__covid_mwcb_2020_03_18.packet.csv`
### covid_mwcb_2020_03_18 (event)
- rows: `937`
- start_ts_utc: `2020-03-18T08:00:00Z`
- end_ts_utc: `2020-03-19T00:00:00Z`
- collapse_ts_utc: `2020-03-18T16:56:17Z`
- control_source: `None`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_002053__volmageddon_control_2018_01_25.packet.csv`
### volmageddon_control_2018_01_25 (control)
- rows: `751`
- start_ts_utc: `2018-01-25T09:00:00Z`
- end_ts_utc: `2018-01-26T01:00:00Z`
- collapse_ts_utc: `None`
- control_source: `backfill`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_002053__volmageddon_control_2018_01_29.packet.csv`
### volmageddon_control_2018_01_29 (control)
- rows: `857`
- start_ts_utc: `2018-01-29T09:00:00Z`
- end_ts_utc: `2018-01-30T01:00:00Z`
- collapse_ts_utc: `None`
- control_source: `current`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_002053__volmageddon_control_2018_02_08.packet.csv`
### volmageddon_control_2018_02_08 (control)
- rows: `933`
- start_ts_utc: `2018-02-08T09:00:00Z`
- end_ts_utc: `2018-02-09T01:00:00Z`
- collapse_ts_utc: `None`
- control_source: `current`

- built packet: `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_002053__covid_noncollapse_2020_04_03.packet.csv`
### covid_noncollapse_2020_04_03 (control)
- rows: `813`
- start_ts_utc: `2020-04-03T08:00:00Z`
- end_ts_utc: `2020-04-04T00:00:00Z`
- collapse_ts_utc: `None`
- control_source: `current`

