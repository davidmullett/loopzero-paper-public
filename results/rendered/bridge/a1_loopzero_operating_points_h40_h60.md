# A1 — Loopzero quantile detector operating points

Pre-registered detector (see `analysis/14_a1_prereg.md`). Reference quantiles are fit on **control-unit rows only** for each domain (markets: last 30 min of each canonical unit window; recommender: per-step rows inside the canonical h=50 pre-collapse panel). Event-unit rows are never used in quantile computation. Pass criterion: `0.03 ≤ control_fp ≤ 0.07`.

| Method | Benchmark | Config | Control FP | Event alarm rate | Accepted? |
|---|---|---|---:|---:|---|
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=50, k=1 | 0.103170 | 0.404536 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=50, k=1 | 0.005005 | 0.285447 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=50, k=3 | 0.014782 | 0.092163 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=50, k=3 | 0.000501 | 0.055141 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=50, k=5 | 0.002591 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=50, k=5 | 0.000250 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=60, k=1 | 0.020573 | 0.125026 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=60, k=1 | 0.002252 | 0.207825 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=60, k=3 | 0.000152 | 0.001303 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=60, k=3 | 0.000501 | 0.033459 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=60, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=60, k=5 | 0.000250 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=70, k=1 | 0.009906 | 0.089084 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=70, k=1 | 0.000501 | 0.047134 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=70, k=3 | 0.000000 | 0.000829 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=70, k=3 | 0.000250 | 0.004100 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=70, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=70, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=75, k=1 | 0.001524 | 0.030849 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=75, k=1 | 0.000501 | 0.036651 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=75, k=3 | 0.000000 | 0.000148 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=75, k=3 | 0.000250 | 0.002531 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=75, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=75, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=80, k=1 | 0.001067 | 0.023063 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=80, k=1 | 0.000501 | 0.025727 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=80, k=3 | 0.000000 | 0.000089 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=80, k=3 | 0.000250 | 0.001651 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=80, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=80, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=85, k=1 | 0.000762 | 0.015040 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=85, k=1 | 0.000501 | 0.007127 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=85, k=3 | 0.000000 | 0.000030 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=85, k=3 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=85, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=85, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=90, k=1 | 0.000610 | 0.008201 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=90, k=1 | 0.000000 | 0.001513 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=90, k=3 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=90, k=3 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=90, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=90, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=95, k=1 | 0.000000 | 0.001391 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=95, k=1 | 0.000000 | 0.000825 | No |
| **Loopzero quantile (A1)** | **movielens25m_recursive_frontier_public_v1__horizon_40** | **q=95, k=3** | **0.000000** | **0.000000** | **No** |
| **Loopzero quantile (A1)** | **movielens25m_recursive_frontier_public_v1__horizon_60** | **q=95, k=3** | **0.000000** | **0.000000** | **No** |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=95, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=95, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=99, k=1 | 0.000000 | 0.000089 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=99, k=1 | 0.000000 | 0.000083 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=99, k=3 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=99, k=3 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_40 | q=99, k=5 | 0.000000 | 0.000000 | No |
| Loopzero quantile (A1) | movielens25m_recursive_frontier_public_v1__horizon_60 | q=99, k=5 | 0.000000 | 0.000000 | No |

## Reading note
- **Primary** rows (bolded) are the pre-registered headline operating point per benchmark: `q=95, k=3`.
- All numeric values use the `{:.6f}` format convention of the comparator paper-table family (see `analysis/13am_build_markets_comparator_paper_table_v1.py`).
- `Accepted?` is `Yes` iff control FP lies in the locked equal-FP band `[0.03, 0.07]`.
- Sensitivity grid: `q ∈ {90, 95, 99}` paired with `q_delta = 100 − q`, and `k ∈ {1, 3, 5}` — 9 cells per benchmark.
