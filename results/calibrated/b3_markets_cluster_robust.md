# B3 — Markets cluster-robust sensitivity (scenario grain)

## Cluster composition

Event-side scenario clusters (derived from `unit_id` parsing; n=2):

| Cluster | Segments |
|---------|----------|
| volmageddon_2018_xiv  | 8 |
| covid_mwcb_2020_03_18 | 8 |

Control-side scenario clusters (n=5):

| Cluster | Segments |
|---------|----------|
| covid_noncollapse_2020_03_11   | 8 |
| volmageddon_control_2018_01_29 | 8 |
| volmageddon_control_2018_02_08 | 8 |
| covid_noncollapse_2020_03_13   | 7 |
| volmageddon_control_2018_01_25 | 7 |

Total cluster units: 7 (2 event + 5 control), down from 54 segment units in A3.

## Methodological framing

Cluster-aware bootstrap (10,000 iterations) at scenario grain. Reported as a **conservative upper bound on dependence-induced CI inflation** under the matched-control experimental design. Wild cluster bootstrap (Cameron, Gelbach & Miller 2008) — the methodologically appropriate response to the small-cluster regime (n=2 event clusters) — is deferred to v2.

## Effect sizes at scenario grain (B3)

| Witness | Measure   | Point | Percentile 95% CI | BCa 95% CI |
|---------|-----------|-------|-------------------|------------|
| G | cohens_d | -0.0293 | [-0.0916, +0.0489] | [-0.0932, +0.0473] |
| G | glasss_d | -0.0285 | [-0.0934, +0.0472] | [-0.0938, +0.0472] |
| G | rank_auc | +0.5073 | [+0.4569, +0.5581] | [+0.4520, +0.5530] |
| p | cohens_d | +0.0966 | [-0.3309, +0.4082] | [-0.3285, +0.4313] |
| p | glasss_d | +0.1188 | [-0.2952, +0.7102] | [-0.2950, +0.7102] |
| p | rank_auc | +0.4823 | [+0.4376, +0.5310] | [+0.4361, +0.5305] |
| delta | cohens_d | +0.0286 | [-0.1534, +0.1993] | [-0.1534, +0.1993] |
| delta | glasss_d | +0.0287 | [-0.1610, +0.1928] | [-0.1610, +0.1928] |
| delta | rank_auc | +0.5162 | [+0.4495, +0.5773] | [+0.4495, +0.5757] |

## Side-by-side: A3 segment grain vs B3 scenario grain (BCa 95% CI)

| Witness | Measure | A3 segment grain (n=54) | B3 scenario grain (n=7) | CI width ratio |
|---------|---------|--------------------------|--------------------------|----------------|
| G | cohens_d | [-0.1686, +0.1469] | [-0.0932, +0.0473] | 0.45× |
| G | glasss_d | [-0.1552, +0.1598] | [-0.0938, +0.0472] | 0.45× |
| G | rank_auc | [+0.4592, +0.5552] | [+0.4520, +0.5530] | 1.05× |
| p | cohens_d | [-0.4884, +0.9409] | [-0.3285, +0.4313] | 0.53× |
| p | glasss_d | [-0.4123, +2.0944] | [-0.2950, +0.7102] | 0.40× |
| p | rank_auc | [+0.3979, +0.6141] | [+0.4361, +0.5305] | 0.44× |
| delta | cohens_d | [-0.5682, +0.6167] | [-0.1534, +0.1993] | 0.30× |
| delta | glasss_d | [-0.5632, +0.6174] | [-0.1610, +0.1928] | 0.30× |
| delta | rank_auc | [+0.3527, +0.6799] | [+0.4495, +0.5757] | 0.39× |
