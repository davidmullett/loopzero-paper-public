# Bridge Check — movielens25m_recursive_frontier_public_v1

**Decision:** `PARTIAL`

**Recommended action:** Bridge check is only partially aligned. Refine telemetry proxies before comparator calibration.

## Bootstrap

- unit: `user`
- reps: `1000`
- seed: `0`
- note: User-level bootstrap is descriptive uncertainty only; bridge decision is directional, not a significance test.

## Counts

- n_unique_users_in_panel: `40339`
- n_event_rows_in_bridge_window: `337770`
- n_control_rows_in_bridge_window: `65620`
- n_event_users_in_bridge_window: `33777`
- n_control_users_in_bridge_window: `6562`

## Metric checks

### G

- aligned: `False`
- expected_direction: `event>control`
- event_mean: `0.060854795811275064`
- event_ci: `[0.06073842694035427, 0.060964345045302494]`
- control_mean: `0.08175988899853572`
- control_ci: `[0.0796950186103645, 0.08387034394539725]`
- difference_event_minus_control: `-0.02090509318726065`

### p

- aligned: `True`
- expected_direction: `event>control`
- event_mean: `0.2127795290931448`
- event_ci: `[0.21153817444200934, 0.21411497967456666]`
- control_mean: `0.18697102468599017`
- control_ci: `[0.18361050328991974, 0.19031726924374437]`
- difference_event_minus_control: `0.025808504407154625`

### delta

- aligned: `True`
- expected_direction: `event<control`
- event_mean: `0.5968521773531568`
- event_ci: `[0.596437844207866, 0.5972776582137561]`
- control_mean: `0.6084493348409566`
- control_ci: `[0.6071617578946368, 0.6097574532342738]`
- difference_event_minus_control: `-0.01159715748779988`

