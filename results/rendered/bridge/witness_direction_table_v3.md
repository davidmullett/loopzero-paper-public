# Witness-direction measurement table v3

Two-domain descriptive exhibit of witness direction on the public markets and recommender benchmarks, with localized late-window markets summaries and change-based diversity measurement for markets.

| Domain | Benchmark | Window definition | Units (event/control) | Witness | Event mean | Control mean | Event - control | Expected direction | Observed | Consistent |
|---|---|---|---:|---|---:|---:|---:|---|---|---:|
| markets | volmageddon_covid_public_v2 | canonical_unit_windows_last_30min | 16/38 | G | 2099335.453703 | 2.729991 | 2099332.723712 | event_gt_control | event > control | 1 |
| markets | volmageddon_covid_public_v2 | canonical_unit_windows_last_30min | 16/38 | p | 0.014281 | 0.010739 | 0.003542 | event_gt_control | event > control | 1 |
| markets | volmageddon_covid_public_v2 | canonical_unit_windows_last_30min | 16/38 | delta_change | -0.057441 | -0.012161 | -0.045279 | event_lt_control | event < control | 1 |
| markets | volmageddon_covid_public_v2 | canonical_unit_windows_last_60min | 16/38 | G | 7808592.994798 | 589125.632520 | 7219467.362278 | event_gt_control | event > control | 1 |
| markets | volmageddon_covid_public_v2 | canonical_unit_windows_last_60min | 16/38 | p | 0.013653 | 0.008556 | 0.005097 | event_gt_control | event > control | 1 |
| markets | volmageddon_covid_public_v2 | canonical_unit_windows_last_60min | 16/38 | delta_change | 0.012534 | -0.018571 | 0.031105 | event_lt_control | event >= control | 0 |
| recommender | movielens25m_recursive_frontier_public_v1__canonical_h50 | canonical_50step_precollapse_units | 35584/4755 | G | 0.060664 | 0.051029 | 0.009635 | event_gt_control | event > control | 1 |
| recommender | movielens25m_recursive_frontier_public_v1__canonical_h50 | canonical_50step_precollapse_units | 35584/4755 | p | 0.209480 | 0.197917 | 0.011563 | event_gt_control | event > control | 1 |
| recommender | movielens25m_recursive_frontier_public_v1__canonical_h50 | canonical_50step_precollapse_units | 35584/4755 | delta | 0.598662 | 0.606113 | -0.007450 | event_lt_control | event < control | 1 |

## Reading note
- `directionally_consistent = 1` means the observed event-vs-control comparison matches the theorem-guided expectation for that witness.
- Markets are summarized over the exact canonical benchmark unit windows defined in `results/rendered/comparators/markets_comparator_input_v2.csv`, restricted to the last 30 or 60 minutes inside each canonical unit.
- In markets, diversity is summarized as `delta_change = terminal delta - initial delta` within each late window, aligning the table more closely to the implemented non-increase semantics.
- Recommenders are summarized over canonical 50-step pre-collapse benchmark units from the MovieLens telemetry panel.
