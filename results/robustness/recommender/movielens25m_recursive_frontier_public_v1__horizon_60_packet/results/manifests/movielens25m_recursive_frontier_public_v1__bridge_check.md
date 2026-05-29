# Bridge Check — movielens25m_recursive_frontier_public_v1

**Decision:** `PASS`

**Recommended action:** Bridge check passes under the current telemetry package. Proceed to fast-family comparator calibration.

## Bootstrap

- unit: `user`
- reps: `1000`
- seed: `0`
- note: User-level bootstrap is descriptive uncertainty only; bridge decision is directional, not a significance test.

## Counts

- n_unique_users_in_panel: `40339`
- n_event_rows_in_bridge_window: `363430`
- n_control_rows_in_bridge_window: `39960`
- n_event_users_in_bridge_window: `36343`
- n_control_users_in_bridge_window: `3996`

## Metric checks

### G

- aligned: `True`
- expected_direction: `event>control`
- event_mean: `0.06058198642809158`
- event_ci: `[0.06047947564905782, 0.060680752501495135]`
- control_mean: `0.02903404570071235`
- control_ci: `[0.026979708438041754, 0.03109050192383524]`
- difference_event_minus_control: `0.03154794072737923`

### p

- aligned: `True`
- expected_direction: `event>control`
- event_mean: `0.20821910046588793`
- event_ci: `[0.20692592863175036, 0.20962426483816748]`
- control_mean: `0.20714670695320844`
- control_ci: `[0.20178562967165903, 0.21241054816411706]`
- difference_event_minus_control: `0.001072393512679487`

### delta

- aligned: `True`
- expected_direction: `event<control`
- event_mean: `0.5997551700069769`
- event_ci: `[0.599318111741462, 0.6001654084126337]`
- control_mean: `0.6010488987900374`
- control_ci: `[0.5992343954727084, 0.6029326644255132]`
- difference_event_minus_control: `-0.0012937287830605548`

