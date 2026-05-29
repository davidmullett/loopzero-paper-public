# A1 — Loopzero quantile detector operating points

Pre-registered detector (see `analysis/14_a1_prereg.md`). Reference quantiles are fit on **control-unit rows only** for each domain (markets: last 30 min of each canonical unit window; recommender: per-step rows inside the canonical h=50 pre-collapse panel). Event-unit rows are never used in quantile computation. Pass criterion: `0.03 ≤ control_fp ≤ 0.07`.

| Method | Benchmark | Config | Control FP | Event alarm rate | Accepted? |
|---|---|---|---:|---:|---|
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=50, k=1 | 0.236842 | 0.187500 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=50, k=3 | 0.236842 | 0.187500 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=50, k=5 | 0.078947 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=60, k=1 | 0.236842 | 0.187500 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=60, k=3 | 0.210526 | 0.125000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=60, k=5 | 0.026316 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=70, k=1 | 0.210526 | 0.187500 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=70, k=3 | 0.105263 | 0.062500 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=70, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=75, k=1 | 0.184211 | 0.187500 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=75, k=3 | 0.078947 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=75, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=80, k=1 | 0.184211 | 0.125000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=80, k=3 | 0.026316 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=80, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=85, k=1 | 0.052632 | 0.000000 | Yes |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=85, k=3 | 0.026316 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=85, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=90, k=1 | 0.052632 | 0.000000 | Yes |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=90, k=3 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=90, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=95, k=1 | 0.026316 | 0.000000 | No |
| **Loopzero quantile (A1)** | **volmageddon_covid_public_v2** | **q=95, k=3** | **0.000000** | **0.000000** | **No** |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=95, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=99, k=1 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=99, k=3 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | volmageddon_covid_public_v2 | q=99, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=50, k=1 | 0.019348 | 0.353389 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=50, k=3 | 0.002313 | 0.075343 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=50, k=5 | 0.000210 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=60, k=1 | 0.009674 | 0.262815 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=60, k=3 | 0.001682 | 0.047718 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=60, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=70, k=1 | 0.004837 | 0.177158 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=70, k=3 | 0.000631 | 0.025995 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=70, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=75, k=1 | 0.000421 | 0.021358 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=75, k=3 | 0.000000 | 0.000084 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=75, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=80, k=1 | 0.000210 | 0.014866 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=80, k=3 | 0.000000 | 0.000028 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=80, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=85, k=1 | 0.000210 | 0.009161 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=85, k=3 | 0.000000 | 0.000028 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=85, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=90, k=1 | 0.000000 | 0.001827 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=90, k=3 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=90, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=95, k=1 | 0.000000 | 0.000899 | No |
| **Loopzero quantile (A1)** | **movielens25m_recursive_frontier_public_v1__canonical_h50** | **q=95, k=3** | **0.000000** | **0.000000** | **No** |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=95, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=99, k=1 | 0.000000 | 0.000084 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=99, k=3 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__canonical_h50 | q=99, k=5 | 0.000000 | 0.000000 | No |

## Reading note
- **Primary** rows (bolded) are the pre-registered headline operating point per benchmark: `q=95, k=3`.
- All numeric values use the `{:.6f}` format convention of the comparator paper-table family (see `analysis/13am_build_markets_comparator_paper_table_v1.py`).
- `Accepted?` is `Yes` iff control FP lies in the locked equal-FP band `[0.03, 0.07]`.
- Sensitivity grid: `q ∈ {90, 95, 99}` paired with `q_delta = 100 − q`, and `k ∈ {1, 3, 5}` — 9 cells per benchmark.
