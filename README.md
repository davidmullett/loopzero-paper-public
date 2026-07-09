> ## Status — July 2026
>
> **This manuscript is under major revision.** The forthcoming version narrows
> the paper to the recommender benchmark and matched alert-budget evaluation,
> adds pre-registered mechanism-control experiments (random, popularity-only,
> matrix-factorization, and sequential baselines, plus covariate adjustments),
> and replaces fixed false-positive-band acceptance with full threshold-sweep /
> matched alarm-count comparison. Please treat the current arXiv version as
> superseded-in-progress and check back before citing or building on it.
>
> A pre-registration for the narrowed v2 analysis has been filed on OSF
> (embargoed): https://osf.io/7bvgz — full document released when the embargo
> lifts.

# Loopzero — Benchmarking Recursive-Collapse Warning Claims Under Matched False-Positive Control

**arXiv:** [2606.00329](https://arxiv.org/abs/2606.00329) · **License:** paper, documentation, and data — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); code — [Apache 2.0](https://github.com/davidmullett/loopzero-paper-public/blob/main/LICENSE)

Reproducibility artifacts for the paper. This repository contains everything downstream of the frozen derived telemetry packets: analysis code, frozen calibration outputs, operating-point data, benchmark construction code, and the manuscript itself. Raw vendor market data and the upstream ingestion/preprocessing repository are not redistributed — see the paper's *Markets data provenance* and *Data and code availability* sections.

## What this paper claims — and what it does not

This work is a **benchmark and evaluation framework**, not a working early-warning detector. Stating the boundary plainly, up front:

**What it does claim**

- It defines a *claim-bounded* evaluation protocol: detectors are compared under a **locked, matched false-positive contract** (an equal-FP band fixed in advance), so that "it warns earlier" cannot be bought with a quietly higher false-alarm rate.
- Under that contract, on frozen public market and recommender-replay data, it reports an **honest null**: no detector evaluated — including the pre-registered Loopzero quantile detector — reached an accepted operating point within the locked band.
- The analysis is **pre-registered** (`analysis/14_a1_prereg.md`), and every figure and table regenerates from frozen, version-pinned artifacts.

**What it does not claim**

- It does **not** claim a validated method that predicts collapse in recursive systems. The headline result is that the tested detectors did not clear the bar.
- It does **not** claim the null is universal — only that it holds for the detectors, domains, and contract reported here. Other detectors or settings may clear the bar; that is the open question the benchmark exists to test.
- It does **not** redistribute raw vendor market data, and it does **not** include the upstream ingestion pipeline. Reproduction starts from the frozen derived packets, not from raw sources.
- The model-collapse (LLM) material is a clearly labeled **secondary analysis** of published trajectories, not a third primary benchmark domain.

A note added July 2026 while preparing the revision: whether a detector family
reaches an "accepted operating point" inside a fixed false-positive band depends
heavily on the granularity of its predeclared calibration grid, so band
non-acceptance is weaker evidence of comparator inadequacy than the v1 framing
suggests. This is one reason the revision replaces band acceptance with full
threshold-sweep, matched alarm-count comparison (see status note above).

## Repository structure

- `analysis/` — scripts that generate every figure and table in the paper: markets and recommender comparator calibration, Loopzero quantile detector evaluation, threshold-path envelope analysis, effect-size decomposition, and the supplementary tables.
- `results/frozen/` — frozen calibration outputs, freeze manifests, and operating-point data. `results/rendered/` — rendered CSVs, parquet, and Markdown tables used as inputs to the manuscript.
- `src/loopzero_paper/benchmarks/` — benchmark construction code for the markets domain (`volmageddon_covid_public_v2`) and the recommender domain (MovieLens-25M deterministic replay, `movielens25m_recursive_frontier_public_v1`).
- `manuscript/` — manuscript source (Markdown), rendered outputs (`build/`), and arXiv submission metadata.

## Reproducing key results

The analysis is pre-registered (see `analysis/14_a1_prereg.md`) and operates on frozen derived packets in `results/frozen/`. The scripts in `analysis/` — each named for the figure or table it generates — take those packets as input and produce the rendered outputs in `results/rendered/`:

- Table 1 — `analysis/04_make_table1.py`
- Table 2 — `analysis/05_make_table2.py`
- Figure 1 (claim ladder) — `analysis/make_fig1_iconic_v5.py`
- Figure 6 (per-witness effect sizes) — `analysis/16_render_a3_effect_size_forest.py` (data: `analysis/15_compute_effect_sizes.py`)
- Figure 7 (ROC at low FP) — `analysis/19_render_a4_roc_lowfp.py` (data: `analysis/18_load_a4_roc_data.py`)
- Loopzero quantile detector — `analysis/14_build_a1_quantile_detector_v1.py`; horizon variants in `analysis/14b_a1_recsys_horizon_variants.py`
- A2 envelope-boundary analysis — `analysis/20_compute_a2_threshold_path.py`, `analysis/21_compute_a2_alert_count_exact.py`
- Supplementary Table S2 — `analysis/17_render_a3_supplementary_table_s2.py`
- Supplementary Table S3 — `analysis/21_compute_a2_alert_count_exact.py`

The frozen `.parquet` and `.csv` artifacts in `results/frozen/` and `results/rendered/` are the canonical reference values; running the corresponding scripts should regenerate them.

## Citation

```bibtex
@misc{mullett2026loopzero,
  title         = {Benchmarking Recursive-Collapse Warning Claims Under Matched False-Positive Control},
  author        = {Mullett, David},
  year          = {2026},
  eprint        = {2606.00329},
  archivePrefix = {arXiv},
  primaryClass  = {eess.SY}
}
```

## License

- Paper, documentation, and data (Markdown, CSVs, JSON manifests, rendered manuscript outputs): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Code (Python in `analysis/`, `src/`): [Apache 2.0](https://github.com/davidmullett/loopzero-paper-public/blob/main/LICENSE)

## Disclosure

The author is the founder of Loopzero, Inc., which has filed a U.S. provisional
patent application related to methods described in this work. Full statement in
the manuscript's Competing Interests section.
