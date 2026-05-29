# A3 — Effect sizes & bootstrap 95% CIs

Per-row Cohen's d, Glass's d, and Rank AUC with cluster-aware bootstrap 95% percentile CIs.

Bootstrap unit grain:
- markets: segment-level (n=38 controls + 16 events)
- recsys (all horizons): user-level (40,339 user clusters; ~10 rows/unit)

Bootstrap iterations: 10000 per cell. BCa CI computation deferred to Day 3.

Sign convention: Cohen's d > 0 and AUC > 0.5 => event mean > control mean. For the δ witness, predicted direction is event < control (δ contracted in events), so d < 0 and AUC < 0.5 are the expected directions.

| Benchmark | Witness | Measure | Point | 95% CI lower | 95% CI upper |
|---|---|---|---:|---:|---:|
| volmageddon_covid_public_v2 | G | cohens_d | -0.0293 | -0.1804 | 0.1333 |
| volmageddon_covid_public_v2 | G | glasss_d | -0.0285 | -0.1632 | 0.1420 |
| volmageddon_covid_public_v2 | G | rank_auc | 0.5073 | 0.4592 | 0.5552 |
| volmageddon_covid_public_v2 | p | cohens_d | 0.0966 | -0.5895 | 0.6949 |
| volmageddon_covid_public_v2 | p | glasss_d | 0.1188 | -0.4922 | 1.3556 |
| volmageddon_covid_public_v2 | p | rank_auc | 0.4823 | 0.3850 | 0.5912 |
| volmageddon_covid_public_v2 | delta | cohens_d | 0.0286 | -0.5688 | 0.6163 |
| volmageddon_covid_public_v2 | delta | glasss_d | 0.0287 | -0.5613 | 0.6193 |
| volmageddon_covid_public_v2 | delta | rank_auc | 0.5162 | 0.3525 | 0.6795 |
| movielens25m_recursive_frontier_public_v1__horizon_40 | G | cohens_d | -0.2136 | -0.2358 | -0.1920 |
| movielens25m_recursive_frontier_public_v1__horizon_40 | G | glasss_d | -0.2129 | -0.2336 | -0.1925 |
| movielens25m_recursive_frontier_public_v1__horizon_40 | G | rank_auc | 0.4412 | 0.4358 | 0.4466 |
| movielens25m_recursive_frontier_public_v1__horizon_40 | p | cohens_d | 0.1796 | 0.1549 | 0.2046 |
| movielens25m_recursive_frontier_public_v1__horizon_40 | p | glasss_d | 0.1716 | 0.1473 | 0.1973 |
| movielens25m_recursive_frontier_public_v1__horizon_40 | p | rank_auc | 0.5554 | 0.5489 | 0.5616 |
| movielens25m_recursive_frontier_public_v1__horizon_40 | delta | cohens_d | -0.2678 | -0.2991 | -0.2370 |
| movielens25m_recursive_frontier_public_v1__horizon_40 | delta | glasss_d | -0.2186 | -0.2462 | -0.1909 |
| movielens25m_recursive_frontier_public_v1__horizon_40 | delta | rank_auc | 0.4148 | 0.4068 | 0.4229 |
| movielens25m_recursive_frontier_public_v1__canonical_h50 | G | cohens_d | 0.1002 | 0.0758 | 0.1242 |
| movielens25m_recursive_frontier_public_v1__canonical_h50 | G | glasss_d | 0.1116 | 0.0842 | 0.1395 |
| movielens25m_recursive_frontier_public_v1__canonical_h50 | G | rank_auc | 0.5189 | 0.5132 | 0.5246 |
| movielens25m_recursive_frontier_public_v1__canonical_h50 | p | cohens_d | 0.0804 | 0.0491 | 0.1115 |
| movielens25m_recursive_frontier_public_v1__canonical_h50 | p | glasss_d | 0.0726 | 0.0432 | 0.1018 |
| movielens25m_recursive_frontier_public_v1__canonical_h50 | p | rank_auc | 0.5311 | 0.5231 | 0.5390 |
| movielens25m_recursive_frontier_public_v1__canonical_h50 | delta | cohens_d | -0.1681 | -0.2075 | -0.1281 |
| movielens25m_recursive_frontier_public_v1__canonical_h50 | delta | glasss_d | -0.1251 | -0.1554 | -0.0952 |
| movielens25m_recursive_frontier_public_v1__canonical_h50 | delta | rank_auc | 0.4570 | 0.4467 | 0.4671 |
| movielens25m_recursive_frontier_public_v1__horizon_60 | G | cohens_d | 0.3325 | 0.3101 | 0.3540 |
| movielens25m_recursive_frontier_public_v1__horizon_60 | G | glasss_d | 0.4530 | 0.4123 | 0.4961 |
| movielens25m_recursive_frontier_public_v1__horizon_60 | G | rank_auc | 0.5752 | 0.5700 | 0.5804 |
| movielens25m_recursive_frontier_public_v1__horizon_60 | p | cohens_d | 0.0075 | -0.0282 | 0.0434 |
| movielens25m_recursive_frontier_public_v1__horizon_60 | p | glasss_d | 0.0065 | -0.0252 | 0.0385 |
| movielens25m_recursive_frontier_public_v1__horizon_60 | p | rank_auc | 0.5128 | 0.5039 | 0.5217 |
| movielens25m_recursive_frontier_public_v1__horizon_60 | delta | cohens_d | -0.0288 | -0.0728 | 0.0150 |
| movielens25m_recursive_frontier_public_v1__horizon_60 | delta | glasss_d | -0.0208 | -0.0524 | 0.0110 |
| movielens25m_recursive_frontier_public_v1__horizon_60 | delta | rank_auc | 0.5081 | 0.4968 | 0.5198 |
