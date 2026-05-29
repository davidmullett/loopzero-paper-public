# Markets comparator paper table v1

Paper-facing comparator summary derived strictly from frozen merged comparator state v2: `results/frozen/comparators/markets_comparator_merged_state_v2__20260421T174702Z`.

| Row | Family | Config | FP | Control alarms | Event alarms | Distance to band | Interpretation |
|---|---|---|---:|---:|---:|---:|---|
| Nearest nontrivial fast comparator | ac1_ews | ac1_ews__632f23b2 | 0.131579 | 5/38 | 1/16 | 0.061579 | Nearest nontrivial comparator overall under the locked equal-FP rule. |
| Nearest numeric slow tie 1 | matrix_profile | matrix_profile__0a536aa4 | 0.000000 | 0/38 | 0/16 | 0.030000 | Numerically nearest slow config to the band, but trivial-silent. |
| Nearest numeric slow tie 2 | permutation_entropy | permutation_entropy__001577c8 | 0.000000 | 0/38 | 0/16 | 0.030000 | Numerically nearest slow config to the band, but trivial-silent. |
| Best nontrivial slow comparator | permutation_entropy | permutation_entropy__259c1b96 | 0.368421 | 14/38 | 4/16 | 0.298421 | Best slow-family config with nonzero event alarms; still materially above band. |
| Final conclusion | — | — |  | — | — |  | No tested fast or slow comparator configuration achieved the locked equal-FP band; AC1 remains the nearest nontrivial comparator. |

## Reading note
- `Control alarms` reports alarmed control units over total control units.
- `Event alarms` reports alarmed event units over total event units.
- `Distance to band` is the absolute amount by which the config misses the locked equal-FP interval `[0.03, 0.07]`.
- The slow-family numeric nearest row is separated from the best nontrivial slow-family row to avoid conflating trivial silence with a meaningful near miss.
