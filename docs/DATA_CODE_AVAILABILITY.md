# Data and Code Availability

This repository is the publication-facing research package for the manuscript
*A formally specified warning criterion for collapse in recursive systems* (Mullett, 2026).
It contains the code, benchmark configurations, frozen outputs, and documentation
required to verify and reproduce the reported results. This branch supports verification
and regeneration of manuscript-facing outputs from frozen artifacts; it does not support
full raw-data reconstruction. Reproduction instructions are in `docs/REPRODUCTION.md`.

---

## Code availability

The following components are included in this repository:

- `analysis/` — analysis scripts used to regenerate manuscript-facing tables and bridge
  artifacts from frozen canonical inputs
- `src/` — artifact-generation and benchmark-facing scripts used by the Makefile;
  includes the public recommender pipeline scripts required for table and figure regeneration
- `formal/` — Lean 4 formal artifact for the no-progress obstruction referenced by the
  manuscript (toolchain pinned in `lean-toolchain`; see `formal/LEAN_ENVIRONMENT.md`)
- `tests/` — lightweight validation tests for public thresholds and frozen artifact manifests
- `configs/` — publication-grade benchmark specification files

Rendered publication figures are in `results/figures/`. Frozen manuscript-facing states
are in `results/frozen/`. Benchmark manifests are in `results/manifests/`.

The included code is sufficient to:

- inspect the canonical frozen manuscript, bridge, comparator, and robustness states
- verify SHA-256 provenance recorded in freeze manifests
- regenerate all manuscript-facing tables and publication figures from frozen canonical inputs
- rerun the public validation checks described in `docs/REPRODUCTION.md`

This repository does not include production deployment infrastructure, operational
governance systems, private calibration machinery, or any platform components outside
the scope of the published analyses.

---

## Data availability

### Recommender benchmark — MovieLens-25M

The canonical public recommender benchmark is derived from **MovieLens-25M**, provided
by GroupLens Research, University of Minnesota.

- URL: https://grouplens.org/datasets/movielens/25m/
- Access: freely downloadable, no registration required
- Benchmark identifier: `movielens25m_recursive_frontier_public_v1`

MovieLens-25M is not redistributed in this repository. Reproducing the full recommender
benchmark pipeline from raw source requires downloading the dataset separately and running
the pipeline described in `docs/REPRODUCTION.md`.

### Markets benchmark — Alpaca Markets API

The canonical public markets benchmark uses minute-bar equity data sourced from the
**Alpaca Markets API** (free tier).

- Symbols: `SPY`, `QQQ`, `IWM`, `VXX`, `UVXY`, `SVXY`
- Event families: February 2018 Volmageddon dislocation; March 2020 COVID market-wide
  circuit-breaker cluster
- Benchmark identifier: `volmageddon_covid_public_v2`

Raw and processed market panels are not included in this public branch. An Alpaca
free-tier account is required to access source data independently. Raw re-fetch scripts
are not included in this public branch.

### Regulatory and exchange source documents

Supporting regulatory and exchange documentation for the markets event families is cited
in the manuscript. Source PDFs are not included in this public branch; the relevant
public documents are CBOE, NYSE, and SEC filings relating to the Volmageddon and
circuit-breaker events, available from their respective issuing bodies.

### Frozen manuscript-facing artifacts

The frozen states in `results/frozen/` and benchmark manifests in `results/manifests/`
are sufficient to verify all reported results and to regenerate all manuscript-facing
tables and figures without raw or processed data access. Each frozen state includes a
`freeze_manifest.json` with SHA-256 checksums and a `LOCK_NOTE.md` identifying which
manuscript claims it supports.

---

## Scope note

This repository is designed to support scientific reproducibility of the published results.
It does not include:

- raw minute-bar market data redistribution
- proprietary or paid data feeds
- production data pipelines or live data ingestion systems
- non-public platform or deployment architecture

These omissions reflect licensing, access, IP, and scope constraints. They are not gaps
in the scientific artifact chain: the frozen artifacts included in `results/frozen/` and
`results/manifests/` are sufficient to verify and reproduce all results reported in the
manuscript.
