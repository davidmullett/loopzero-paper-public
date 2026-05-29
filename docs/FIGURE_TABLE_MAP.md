# Figure and Table Map

Maps every manuscript-facing figure and table, plus supplementary regenerable artifacts, to its source frozen artifact and,
where unambiguous, the script that regenerates it. Frozen state paths use
`__LATEST.txt` pointers; resolve each pointer to get the exact timestamped
directory with SHA provenance.

Source of truth: `results/frozen/manuscript/two_domain_paper_state_v1__LATEST.txt`

---

## Main text

### Table 1 — Comparator calibration on the canonical public benchmarks

**Caption:** Comparator families were evaluated under the same prespecified
equal-false-positive criterion, FP ∈ [0.03, 0.07]. On the canonical segmented
markets benchmark, the nearest nontrivial comparator was AC1 (FP = 0.131579,
5/38 control alarm units). On the canonical 50-step recommender benchmark, no
tested fast or slow comparator was accepted across 105 tested configurations;
the overall nearest was matrix profile at FP = 0.0136698. Across both domains,
no tested comparator family admitted an accepted operating point.

| Component | Frozen source | Rendered artifact | Generating script |
|---|---|---|---|
| Markets comparator rows | `results/frozen/comparators/markets_comparator_merged_state_v2__LATEST.txt` → `markets_comparator_merged_summary_v2.csv` | `results/rendered/comparators/markets_comparator_paper_table_v1.md` | `analysis/13am_build_markets_comparator_paper_table_v1.py` |
| Recommender comparator rows | `results/manifests/movielens25m_recursive_frontier_public_v1__paper_facing_comparator_table.csv` | `results/manifests/movielens25m_recursive_frontier_public_v1__paper_facing_comparator_table.md` | `src/loopzero_paper/benchmarks/recommender/build_paper_facing_comparator_table.py` |

**Claim supported:** No tested standard early-warning comparator family achieves an
accepted operating point under the locked equal-FP contract on either canonical
benchmark.

---

### Figure 1 — Markets comparator calibration under the locked equal-FP band

| Item | Path |
|---|---|
| PNG | `results/figures/fig1_markets_canonical_comparator_band.png` |
| PDF | `results/figures/fig1_markets_canonical_comparator_band.pdf` |
| Frozen input | `results/frozen/comparators/markets_comparator_merged_state_v2__LATEST.txt` |

**Claim supported:** Visual positioning of all tested fast and slow comparator
families relative to the prespecified [0.03, 0.07] acceptance band on the
canonical segmented markets benchmark; no configuration inside the band.

---

### Figure 2 — Recommender benchmark: bridge summary and comparator calibration

| Item | Path |
|---|---|
| PNG | `results/figures/fig2_recommender_canonical_bridge_and_comparators.png` |
| PDF | `results/figures/fig2_recommender_canonical_bridge_and_comparators.pdf` |
| Frozen input | `results/frozen/movielens25m_recursive_frontier_public_v1__manuscript_freeze_state.json` |

**Claim supported:** Bridge PASS and comparator non-acceptance on the canonical
50-step MovieLens recursive frontier benchmark.

---

### Figure 3 — Recommender adjacent-horizon sensitivity (h40 / h50 / h60)

| Item | Path |
|---|---|
| PNG | `results/figures/fig3_recommender_horizon_sensitivity.png` |
| PDF | `results/figures/fig3_recommender_horizon_sensitivity.pdf` |
| Frozen input | `results/manifests/movielens25m_recursive_frontier_public_v1__horizon_sensitivity_summary.json` |

**Claim supported:** Comparator non-acceptance is robust across h40, h50, and h60;
bridge is PASS at h50 and h60 and PARTIAL at h40 (horizon-sensitive, not anomalous).

---

## Supplement

### Table Sx — Recommender comparator calibration and adjacent-horizon sensitivity

**Caption:** Results for the canonical 50-step benchmark and adjacent 40- and
60-step sensitivity variants. No tested configuration was accepted at any
horizon. The overall nearest comparator was matrix profile at all three horizons.
Bridge: PASS at h50 and h60; PARTIAL at h40.

| Component | Frozen source | Rendered artifact |
|---|---|---|
| Per-horizon summary | `results/manifests/movielens25m_recursive_frontier_public_v1__horizon_sensitivity_summary.json` | `results/manifests/movielens25m_recursive_frontier_public_v1__horizon_sensitivity_summary.md` |

**Claim supported:** Comparator robustness across horizon perturbations; bounded
bridge sensitivity under horizon shortening.

---

### Table Sy — Witness-direction measurement on the canonical benchmarks

**Caption:** On the canonical recommender benchmark, pre-collapse event units
showed higher mean G, higher p, and lower δ than controls. On the canonical
markets benchmark, the same directional pattern was recovered in the last 30
minutes of each canonical unit; in a wider 60-minute summary, G and p remained
aligned whereas diversity-change weakened.

| Component | Frozen source | Rendered artifact | Generating script |
|---|---|---|---|
| All rows | `results/frozen/bridge/witness_direction_bridge_state_v3__LATEST.txt` → `witness_direction_table_v3.csv` | `results/frozen/bridge/witness_direction_bridge_state_v3__*/witness_direction_table_v3.md` | `analysis/13bb_build_witness_direction_table_v3.py` |

**Claim supported:** Directional witness alignment — recommender: full triad (3/3);
markets at 30-min late window: full triad (3/3); markets at 60-min: partial (G and p
align, delta_change does not). Markets bridge is localized and late-window strongest,
not uniformly invariant across wider summary windows.

---

## Superseded artifacts

The following files exist in the repository but belong to earlier paper versions
and are **not** referenced by the current submission:

| File | Status |
|---|---|
| `results/frozen/table1_domains.csv` | Superseded — prior manuscript structure |
| `results/frozen/table2_equal_fp.csv` | Superseded — prior manuscript structure |
| `results/frozen/fig3_leadtime_source.csv` | Superseded — prior manuscript structure |
| `results/rendered/figure3_leadtime.svg` | Superseded — prior manuscript structure |
| `results/frozen/table_s1_thresholds_public.csv` | Retained for disclosure purposes; not a manuscript-facing table in the current submission |
