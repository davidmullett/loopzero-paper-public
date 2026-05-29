# Paper-Facing Comparator Table — movielens25m_recursive_frontier_public_v1

- equal-FP band: `[0.03, 0.07]`
- total comparator configs: `105`
- total accepted configs: `0`
- no comparator accepted: `True`

| Family | Group | Accepted configs | Nearest FP | Nearest distance | Nearest event rate | Nearest nontrivial FP | Nearest nontrivial distance |
|---|---:|---:|---:|---:|---:|---:|---:|
| Variance EWS | fast | 0 | 0.000000 | 0.030000 | 0.000000 | 0.837087 | 0.767087 |
| AC1 | fast | 0 | 0.866867 | 0.796867 | 1.000000 | 0.866867 | 0.796867 |
| CUSUM | fast | 0 | 0.858358 | 0.788358 | 1.000000 | 0.858358 | 0.788358 |
| Page-Hinkley | fast | 0 | 0.866867 | 0.796867 | 1.000000 | 0.866867 | 0.796867 |
| Matrix Profile | slow | 0 | 0.008759 | 0.021241 | 0.108356 | 0.008759 | 0.021241 |
| Permutation Entropy | slow | 0 | 1.000000 | 0.930000 | 1.000000 | 1.000000 | 0.930000 |

## Reviewer-facing interpretation

- `Nearest FP` is the numerically nearest operating point to the locked equal-FP band, whether or not it is trivial.
- `Nearest nontrivial FP` excludes trivial-silent configurations and therefore reflects the closest firing configuration.
- A family is accepted only if at least one configuration lands inside the prespecified equal-FP band.

