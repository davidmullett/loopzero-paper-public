# A3 — Effect sizes, confidence intervals, bootstrap uncertainty

Sprint brief: [v1.1 → v1.0 expanded scope (locked Tue May 19)](https://www.notion.so/3652f04eb69181ac8505cfdaf80788a8)

Companion to `analysis/14_build_a1_quantile_detector_v1.py` (canonical A1 detector) and `analysis/14b_a1_recsys_horizon_variants.py` (recsys h40/h60 wrapper). Adds magnitude + uncertainty bounds to the directional witness summaries that the A1 work computed binary alarm rates on.

## Why this exists

Pre-A3, the manuscript reports per-witness directional summaries ("event > control" or equivalent) without effect-size magnitudes or confidence intervals. The adversarial review's concern: *"With ~40k users, tiny differences can be stable. Direction alone is not enough."*

A3 closes that gap by computing standardized effect sizes (Cohen's d, Glass's d, rank AUC) with bootstrap 95% CIs at the four byte-exact-reproducible benchmark/horizon targets.

## Scope

| Dimension | Cardinality |
|---|---|
| Benchmark/horizon targets | 4 (markets canonical + recsys h40/h50/h60) |
| Witnesses | 3 (G, p, δ) |
| Effect measures | 3 (Cohen's d, Glass's d, Rank AUC) |
| Effect estimates | 4 × 3 × 3 = **36 cells** |
| CI columns per cell | 4 (percentile lower/upper + BCa lower/upper) |
| Total numerics | **~180 values** for Supplementary Table S2 |

## Locked design decisions

These decisions are settled. Day 2 implementation follows them without re-litigation.

### Bootstrap unit

| Domain | Unit | Rationale |
|---|---|---|
| markets | segment-level (canonical unit_id) | preserves intra-event clustering around Volmageddon and March 2020 MWCB; n=38 controls + 16 events |
| recsys (h40, h50, h60) | user-level (unit_id) | 40,339 user clusters; respects user-level independence; same partition as A1 detector |

### Bootstrap iterations & checkpointing

- **10,000 iterations** (publication-grade percentile CIs converge)
- Checkpoint every **1,000 iterations** to `results/rendered/effect_sizes/a3_bootstrap_checkpoints/`
- Checkpoint contents: partial bootstrap distribution as `.npy`, metadata JSON with iteration count + seed + elapsed time
- Resume-on-interruption logic deferred to Day 3 (not blocking Day 2 first pass)

### CI method

- **Primary:** percentile bootstrap (95% CI = 2.5th and 97.5th percentiles of bootstrap distribution). Simpler, no normality assumption.
- **Sensitivity:** BCa bootstrap (bias-corrected accelerated). Reported alongside percentile in Supplementary Table S2.

### Effect-size measures

| Measure | Formula | When it shines |
|---|---|---|
| Cohen's d (pooled SD) | (μ_event − μ_control) / sd_pooled | primary headline reporting; most common in published literature |
| Glass's d (control SD) | (μ_event − μ_control) / sd_control | n-asymmetric comparisons (recsys n_control ≪ n_event); pooled SD dominated by larger sample |
| Rank AUC | Mann-Whitney U / (n_event × n_control) | non-parametric; robust to outliers and distributional asymmetry; intuitive (P[event row > control row]) |

All three computed and reported for every cell. Sign convention: positive d → event mean > control mean. AUC = 0.5 → no separation; AUC = 1.0 → perfect separation in predicted direction.

### Reference rows (event/control selection)

Mirrors canonical `analysis/14:select_reference_rows` logic for partition consistency with A1 operating-point tables.

- **markets:** per-row ingredient-packet rows from the last 30 min of each canonical unit window. Event rows = pre-collapse rows within event-unit windows; control rows = same window within control-unit windows.
- **recsys (all horizons):** control-unit per-step rows inside the pre-collapse panel. Event rows = pre-collapse event-unit per-step rows.

### NaN handling

Rows with any NaN in (G, p, δ) dropped before effect-size computation. Consistent with pre-reg §4 of the A1 detector.

### Random seed

- Top-level: `numpy.random.default_rng(42)`
- Child generators spawned per (benchmark, horizon, witness, measure) cell via `numpy.random.SeedSequence.spawn()` for reproducible per-cell streams independent of execution order or parallelism

## Inputs

All four panels verified accessible Tue May 19 PM with sha256 anchors recorded:

| Target | Panel path | Size | Anchor (`benchmark_freeze_sha256`) |
|---|---|---|---|
| markets canonical | `results/rendered/equity_dislocation_family/intraday_v2_ingredient_packet/cfg_001339__*.packet.csv` | ~5 files | (per-packet; see cfg_001339 manifest) |
| recsys h=40 | `results/robustness/recommender/.../horizon_40_packet/.../telemetry_panel.csv.gz` | 21 MB | `b7a8cae1...` ✅ May 8 anchor |
| recsys h=50 (canonical) | `results/manifests/.../telemetry_panel.csv.gz` | 22 MB | `daa7b8fa...` ✅ canonical |
| recsys h=60 | `results/robustness/recommender/.../horizon_60_packet/.../telemetry_panel.csv.gz` | 23 MB | `b59a54d1...` ✅ May 8 anchor |

## Outputs

results/rendered/effect_sizes/
├── a3_effect_sizes_full.csv         # Supplementary Table S2 (36 rows × all measure/CI columns)
├── a3_effect_sizes_summary.md       # paper-facing condensed summary for prose integration
└── a3_bootstrap_checkpoints/        # per-1K-iteration checkpoints (npy + json)

## Execution plan

### Day 1 — scaffolding + design lock ✅ COMPLETE

- [x] Create `analysis/a3_effect_sizes/` directory
- [x] Write `analysis/15_compute_effect_sizes.py` skeleton (458 lines; locked constants, BenchmarkSpec instances, function stubs with full signatures + docstrings)
- [x] Write `analysis/a3_effect_sizes/README.md` (this file)
- [x] Verify all four input panels accessible

### Day 2 — implementation (raw effect sizes + bootstrap loop)

- [ ] Implement `compute_cohens_d`, `compute_glasss_d`, `compute_rank_auc` (each ~10 lines numpy)
- [ ] Implement `load_panel_for_spec` (mirror canonical loader logic; copy from `14b_a1_recsys_horizon_variants.py:load_packet_per_step_panel` with markets/recsys branching)
- [ ] Implement `bootstrap_ci` with percentile method (BCa deferred to Day 3)
- [ ] Wire up `main` glue loop over `BENCHMARK_SPECS × WITNESSES × EFFECT_MEASURES`
- [ ] First test run with `--n-iterations 100` for smoke check

### Day 3 — validation

- [ ] Sanity check: known effects against manuscript-reported witness directions
- [ ] Cross-check Rank AUC against `scipy.stats.mannwhitneyu` U statistic (should match)
- [ ] Verify CI percentiles converge with iteration progression (1K → 5K → 10K)
- [ ] Implement BCa CI as sensitivity layer
- [ ] Implement checkpoint resume logic

### Day 4 — visualization

- [ ] Update Figure 1 left panel with effect-size whiskers (95% CI)
- [ ] Generate Supplementary Table S2 with full numerical results
- [ ] B&W readability check per C4 editor's-review spec
- [ ] Two rounds of fresh-eyes review on the figure

### Day 5 — manuscript integration

- [ ] Add effect-size sentence to "Cross-domain evidence" section
- [ ] Add Supplementary Table S2 reference + caption
- [ ] Update Figure 1 caption with effect-size details
- [ ] Commit + push as `A3: effect sizes + bootstrap CIs across 4 benchmark/horizon targets`

## Key technical risks

1. **Memory at scale.** Bootstrap = 40,339 users × 10K iterations on the recsys panels. Estimated ~10-20 GB peak. Use numpy + multiprocessing.Pool with ~4 workers as default; profile and switch to numba JIT only if needed.
2. **Bootstrap unit decision is load-bearing.** Cluster-level resampling is conservative and correct given dependency structure. Wrong choice invalidates CIs. Lock the cluster choice before implementing (already locked above).
3. **CI method consistency.** Percentile primary is simpler and defensible. BCa is more accurate but harder to verify. Lock on percentile primary; BCa as sensitivity check.
4. **Result interpretation.** If effect sizes are very small with tight CIs around 0, the directional witness claims weaken. Honest disclosure pattern from v1.0 commit `9fc561b` (precision reframing) absorbs whichever outcome the data produces.

## Effort estimate

3-5 days focused work. Day 1 complete; Day 2-5 to go.

## Cross-references

- Adversarial review backlog item A3
- Figure 1 v13 iconic claim ladder design vocabulary from C4 work
- B&W readability standards from C4 editor's-review spec
- `analysis/14_build_a1_quantile_detector_v1.py` — canonical A1 detector (column resolution, pre-collapse filter, reference-row selection)
- `analysis/14b_a1_recsys_horizon_variants.py` — recsys h40/h60 packet loader (parameterized panel loader template for Day 2)
- v1.0 commit `9fc561b` — precision reframing language ready to absorb A3 outcomes

---

*Status: Day 1 complete Tue May 19 PM. Day 2 implementation ready to begin.*
MDEOF

# Verify
echo "=== File written ==="
wc -l analysis/a3_effect_sizes/README.md
echo ""
echo "=== First 30 lines ==="
head -30 analysis/a3_effect_sizes/README.md