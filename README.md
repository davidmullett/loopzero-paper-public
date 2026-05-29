# Loopzero — Benchmarking Recursive-Collapse Warning Claims Under Matched False-Positive Control

> **arXiv:** _to be added on submission_
> **License:** paper, documentation, and data — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); code — [Apache 2.0](LICENSE)

Reproducibility artifacts for the paper. This repository contains everything downstream of the frozen derived telemetry packets: analysis code, frozen calibration outputs, operating-point data, benchmark construction code, and the manuscript itself. Raw vendor market data and the upstream ingestion/preprocessing repository are not redistributed — see the paper's *Markets data provenance* and *Data and code availability* sections.

## Repository structure

- **`analysis/`** — scripts that generate every figure and table in the paper: markets and recommender comparator calibration, Loopzero quantile detector evaluation, threshold-path envelope analysis, effect-size decomposition, and the supplementary tables.
- **`results/frozen/`** — frozen calibration outputs, freeze manifests, and operating-point data.
  **`results/rendered/`** — rendered CSVs, parquet, and Markdown tables used as inputs to the manuscript.
- **`src/loopzero_paper/benchmarks/`** — benchmark construction code for the markets domain (`volmageddon_covid_public_v2`) and the recommender domain (MovieLens-25M deterministic replay, `movielens25m_recursive_frontier_public_v1`).
- **`manuscript/`** — manuscript source (Markdown), rendered outputs (`build/`), and arXiv submission metadata.

## Reproducing key results

The analysis is pre-registered (see `analysis/14_a1_prereg.md`) and operates on frozen derived packets in `results/frozen/`. The scripts in `analysis/` — each named for the figure or table it generates — take those packets as input and produce the rendered outputs in `results/rendered/`:

- **Table 1** — `analysis/04_make_table1.py`
- **Table 2** — `analysis/05_make_table2.py`
- **Figure 1** (claim ladder) — `analysis/make_fig1_iconic_v5.py`
- **Figure 6** (per-witness effect sizes) — `analysis/16_render_a3_effect_size_forest.py` (data: `analysis/15_compute_effect_sizes.py`)
- **Figure 7** (ROC at low FP) — `analysis/19_render_a4_roc_lowfp.py` (data: `analysis/18_load_a4_roc_data.py`)
- **Loopzero quantile detector** — `analysis/14_build_a1_quantile_detector_v1.py`; horizon variants in `analysis/14b_a1_recsys_horizon_variants.py`
- **A2 envelope-boundary analysis** — `analysis/20_compute_a2_threshold_path.py`, `analysis/21_compute_a2_alert_count_exact.py`
- **Supplementary Table S2** — `analysis/17_render_a3_supplementary_table_s2.py`
- **Supplementary Table S3** — `analysis/21_compute_a2_alert_count_exact.py`

The frozen `.parquet` and `.csv` artifacts in `results/frozen/` and `results/rendered/` are the canonical reference values; running the corresponding scripts should regenerate them.

## Citation

A BibTeX entry will be added here once the arXiv preprint is announced. In the interim:

> Mullett, D. (2026). *Benchmarking Recursive-Collapse Warning Claims Under Matched False-Positive Control*. arXiv preprint.

## License

- **Paper, documentation, and data** (Markdown, CSVs, JSON manifests, rendered manuscript outputs): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Code** (Python in `analysis/`, `src/`): [Apache 2.0](LICENSE)
