# A4 — ROC/PR curves + low-FP zoom (design decisions, LOCKED)

## Data source inventory (Day 1 confirmed)

| Source | Path | Coverage | Type |
|---|---|---|---|
| Markets full grid (both fast + slow) | `results/frozen/comparators/markets_comparator_merged_state_v2__20260421T174702Z/comparator_acceptance_matrix_v1.csv` | 964 configs, all 6 families | curve points |
| Recsys h=40 fast | `results/robustness/recommender/movielens25m_recursive_frontier_public_v1__horizon_40_packet/results/manifests/movielens25m_recursive_frontier_public_v1__fast_calibration_matrix.csv` | 60 configs | curve points |
| Recsys h=40 slow | Same path, slow_calibration_matrix.csv | ~30 configs | curve points |
| Recsys h=60 fast/slow | Same pattern with horizon_60 | 60+30 configs | curve points |
| Recsys h=50 canonical | `results/manifests/movielens25m_recursive_frontier_public_v1__merged_comparator_summary.json` | 14 markers (2 per family) | selected markers |

## Family taxonomy (locked)

- **Fast comparators:** `variance_ews`, `ac1` (also `ac1_ews` in markets), `cusum`, `page_hinkley`
- **Slow comparators:** `matrix_profile`, `permutation_entropy`

## Normalized schema for `a4_roc_data.parquet`

| Column | Type | Description |
|---|---|---|
| `domain` | str | `markets` or `recsys` |
| `benchmark` | str | benchmark_id |
| `horizon` | int or NaN | recsys horizon (40, 50, 60); NaN for markets |
| `family` | str | detector family name |
| `family_group` | str | `fast` or `slow` |
| `config_id` | str | unique configuration identifier |
| `params_json` | str | JSON-encoded parameters |
| `fp` | float | false-positive rate on controls |
| `tpr` | float | true-positive rate on events (event alarm rate) |
| `source_type` | str | `curve_point` or `selected_marker` |
| `marker_category` | str or None | `nearest` / `nearest_nontrivial` / None |
| `accepted` | bool | whether config landed in [0.03, 0.07] band |
| `nontrivial` | bool | whether config had non-zero alarms |
| `band_distance` | float | distance from acceptance band [0.03, 0.07] |

## Figure design (Day 2 plan, LOCKED)

- **Layout:** single panel with corner inset (low-FP zoom 0.0 to 0.10). Inset placed at the empirically informative corner — likely upper-right or lower-right depending on data distribution.
- **Domains:** separate sub-panels by domain (markets, recsys). Sub-panel by horizon for recsys (h=40, h=50, h=60 overlaid).
- **Encoding:**
  - Curves: 6 family colors, colorblind-safe palette (`#3B5C8C`, `#4F7B5C`, `#B66B30`, `#C04C3F`, plus two additional muted tones)
  - h=50 canonical markers: ★ star marker per family at the `nearest` operating point; smaller circle at `nearest_nontrivial` if different
  - Acceptance band: shaded vertical strip at FP ∈ [0.03, 0.07]
  - Loopzero pre-registered operating point: ★ at FP=0.0 (from a1_loopzero_operating_points.csv); full continuous ROC deferred to A2
- **Toolchain:** matplotlib hand-coded (matches v13 iconic claim ladder + a3 forest plot conventions). 300 dpi PNG + vector PDF.
- **B&W readability:** line dashes per family (`-`, `--`, `-.`, `:`) plus color, so families remain distinguishable in grayscale.

## Day-by-day plan (3 days)

- **Day 1 (TODAY):** Load + normalize all 5 sources into `a4_roc_data.parquet`. Inventory print summary. Commit + push.
- **Day 2:** Figure construction. matplotlib script. Two rounds of fresh-eyes review.
- **Day 3:** Manuscript integration. Decide whether to update existing Figure 1 right panel (`fig2_recommender_canonical_bridge_and_comparators.png` source) or introduce as separate Figure 6. Commit + push.

## Open question for Day 2

Whether to update the **existing** Figure 1 right panel (replacing the comparator-calibration content) or add a **new** Figure 6 that's purely ROC + low-FP zoom. The former keeps figure count tight; the latter preserves the existing figure's narrative integrity. Decision deferred to Day 2 after seeing the actual ROC plot in v0.


## Known data architecture facts (confirmed Day 1, post-loader-verification)

### Markets row count breakdown (964 → 314 usable)

The acceptance matrix has 964 rows on disk. After filtering for valid `fp_cal`, 314 rows remain. The 650 dropped rows have `acceptance_reason: unreachable_fp_band:n_control_units=N` where N is far below what the [0.03, 0.07] band requires. Per-family breakdown:

| Family | Total | NaN fp_cal | Usable |
|---|---:|---:|---:|
| permutation_entropy | 240 | 240 (100%) | 0 |
| matrix_profile | 96 | 96 (100%) | 0 |
| cusum | 168 | 84 (50%) | 84 |
| ac1_ews | 160 | 80 (50%) | 80 |
| variance_ews | 160 | 80 (50%) | 80 |
| page_hinkley | 140 | 70 (50%) | 70 |

The slow families (`matrix_profile`, `permutation_entropy`) have **zero usable points** in markets. This is not a loader defect — it is a data-availability gate failure. Slow comparators require time-series length exceeding what the canonical late-30min window provides; after the window slice, only ~6 control units survive their `required_min_len` filter, and {0, 1/6, 2/6, ...} = {0, 0.167, 0.333, ...} does not intersect the [0.03, 0.07] band. The configs were never even evaluated (`n_event_alarm_units` is NaN, not 0).

**Manuscript implication:** slow comparators fail at the data-availability gate in markets before they reach calibration. This is a stronger statement than "they performed poorly" — they were architecturally unevaluable on the canonical markets benchmark. Worth noting in the comparator-failure narrative.

### Family naming asymmetry across domains

Markets has the family `ac1_ews` (autocorrelation-at-lag-1 + EWS-style smoothing). Recsys has `ac1` (autocorrelation-at-lag-1 base). These are sibling implementations of the same underlying statistic with different smoothing pipelines, **not the same detector**. The Day 2 figure should treat them as visually distinct (separate color/style) rather than collapsing them under one label, since collapsing would mis-represent what was actually evaluated.

Family parity summary:

| Domain | Fast families | Slow families | Total usable |
|---|---|---|---|
| markets | ac1_ews, cusum, page_hinkley, variance_ews (4) | (none — gate failure) | 4 |
| recsys (any horizon) | ac1, cusum, page_hinkley, variance_ews (4) | matrix_profile, permutation_entropy (2) | 6 |

### Low-FP inset coverage (confirmed Day 1)

- Markets: min fp = 0.131 → **markets contributes nothing to the [0.0, 0.10] inset**. The inset will show recsys only.
- Recsys h=40 + h=60: 20 points in [0.0, 0.10] combined (4 fast + 16 slow). Slow families dominate the low-FP region — they fire rarely on controls but also rarely on events.
- Recsys h=50 canonical markers: 3 points in [0.0, 0.10] (1 fast + 2 slow).

The inset design therefore visualizes how comparators that achieve low FP (slow families) also achieve low TPR — the trade-off that makes them inadequate for the canonical band.
