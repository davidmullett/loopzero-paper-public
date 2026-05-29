# Reproduction

This document describes what can and cannot be reproduced from this repository,
the canonical artifact chain, and the exact commands needed to verify and
regenerate manuscript-facing outputs.

---

## Scope of SHA-256 provenance

Frozen state files in this repository record SHA-256 hashes for two categories of artifacts: (a) distributed artifacts present in this public branch — primarily under `results/frozen/`, `results/manifests/`, `results/figures/`, and `manuscript/` — which can be independently rehashed and verified against the recorded values; and (b) upstream provenance records — including paths under `generated_by_analysis/`, `results/rendered/`, `results/source_data/`, and historical comparator variants — which are recorded for chain-of-custody but are not redistributed in the public branch. Independent verification covers category (a); category (b) records the construction lineage but is not externally rehashable from this repo alone.

---

## 1. Scope of reproducibility

### What this repository supports

- **Frozen artifact verification.** Every manuscript-facing frozen state includes a
  `freeze_manifest.json` with SHA-256 checksums. The test suite checks these checksums
  against current file state. A reviewer can independently verify any file by computing
  its SHA-256 and comparing against the manifest.

- **Table regeneration from frozen inputs.** The comparator-calibration table
  (Table 1, manuscript-facing) and the supplementary regenerable artifacts
  (Table Sx, Table Sy) can each be regenerated from their respective frozen canonical
  inputs using the scripts listed in section 5. No external data access is required
  for this step.

- **Figure regeneration from frozen inputs.** All three publication figures can be
  regenerated from frozen canonical inputs using the script listed in section 5.

- **Public threshold validation.** The public-facing threshold disclosure for the
  canonical benchmarks can be validated against the frozen artifact state.

### What this repository does not support without additional steps

- **Full markets comparator pipeline from raw data.** Raw and processed market panels
  are not included in this public branch. All manuscript-facing results are reproduced
  from frozen artifacts in `results/frozen/`. Raw Alpaca re-fetch scripts are not
  included in this public branch.

- **Full recommender benchmark pipeline from scratch.** The MovieLens-25M dataset is
  not redistributed. It is freely downloadable without registration from
  `https://grouplens.org/datasets/movielens/25m/`. Reproducing the full recommender
  pipeline from raw data requires this download plus the full pipeline execution
  described in section 6.

- **Witness computation internals.** The artifact-generation scripts used by the
  Makefile (`src/loopzero_paper/benchmarks/recommender/`) are included. Platform
  deployment infrastructure, operational governance systems, private calibration
  machinery, and the full witness adapter source are outside the scope of this
  public branch and are not disclosed here.

---

## 2. Environment

Requires Python 3.10.16. A locked dependency file is provided.

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r environment/requirements-lock.txt
```

Full version record: `environment/software_versions.md`.

---

## 3. Canonical artifact chain

Each `__LATEST.txt` pointer resolves to a timestamped, immutable frozen directory.
Each frozen directory contains a `LOCK_NOTE.md` stating what is frozen and which
manuscript claims it supports, and a `freeze_manifest.json` with SHA-256 provenance
for every file in the freeze.

| Artifact | Pointer | Resolved directory |
|---|---|---|
| Manuscript state | `results/frozen/manuscript/two_domain_paper_state_v1__LATEST.txt` | `...two_domain_paper_state_v1__20260422T134303Z/` |
| Bridge exhibit v3 (Table Sy) | `results/frozen/bridge/witness_direction_bridge_state_v3__LATEST.txt` | `...witness_direction_bridge_state_v3__20260422T130759Z/` |
| Markets comparator v2 (Table 1, markets rows) | `results/frozen/comparators/markets_comparator_merged_state_v2__LATEST.txt` | `...markets_comparator_merged_state_v2__20260421T174702Z/` |
| Markets robustness packet | `results/frozen/comparators/markets_fast_robustness_packet_v1__LATEST.txt` | `...markets_fast_robustness_packet_v1__20260421T175531Z/` |
| Recommender benchmark | `results/frozen/movielens25m_recursive_frontier_public_v1__manuscript_freeze_state.json` | (single-file freeze; contains SHA index of all dependent manifests) |

The manuscript-state freeze bundles the canonical paper draft, the frozen bridge
exhibit, bridge provenance notes, and a stable pointer to the exact bridge freeze
used by the manuscript. It is the primary source of truth for all manuscript-facing
claims.

---

## 4. Step-by-step verification

### 4.1 Inspect the manuscript freeze

```bash
# Resolve the pointer
cat results/frozen/manuscript/two_domain_paper_state_v1__LATEST.txt

# Read the lock note (states what is frozen and what claims it supports)
cat results/frozen/manuscript/two_domain_paper_state_v1__20260422T134303Z/LOCK_NOTE.md

# Read the SHA manifest (all files with sha256 and size)
cat results/frozen/manuscript/two_domain_paper_state_v1__20260422T134303Z/freeze_manifest.json

# Read the frozen manuscript draft
cat results/frozen/manuscript/two_domain_paper_state_v1__20260422T134303Z/paper_draft_v1.md
```

### 4.2 Inspect the bridge exhibit (Table Sy)

```bash
# Resolve the pointer
cat results/frozen/bridge/witness_direction_bridge_state_v3__LATEST.txt

# Read the lock note (states the exact directional alignment supported by this state)
cat results/frozen/bridge/witness_direction_bridge_state_v3__20260422T130759Z/LOCK_NOTE.md

# Read the rendered table
cat results/frozen/bridge/witness_direction_bridge_state_v3__20260422T130759Z/witness_direction_table_v3.md
```

The lock note states precisely what this freeze supports: full triad alignment on
the canonical recommender benchmark; full triad alignment in the markets last-30-minute
window; partial alignment (G and p only) in the markets last-60-minute window.

### 4.3 Inspect the markets comparator outputs (Table 1, markets rows)

```bash
# Resolve the pointer
cat results/frozen/comparators/markets_comparator_merged_state_v2__LATEST.txt

# Read the lock note (states benchmark parameterization and conclusion)
cat results/frozen/comparators/markets_comparator_merged_state_v2__20260421T174702Z/LOCK_NOTE.md

# Read the merged comparator summary
cat results/frozen/comparators/markets_comparator_merged_state_v2__20260421T174702Z/markets_comparator_merged_summary_v2.md
```

The lock note records the benchmark identity (`volmageddon_covid_public_v2`),
control and event unit counts (38 and 16), FP grid step (1/38 = 0.026316),
and the conclusion that no tested fast or slow configuration achieved the
acceptance band [0.03, 0.07].

### 4.4 Inspect the markets robustness packet

```bash
# Resolve the pointer
cat results/frozen/comparators/markets_fast_robustness_packet_v1__LATEST.txt

# Read the lock note
cat results/frozen/comparators/markets_fast_robustness_packet_v1__20260421T175531Z/LOCK_NOTE.md

# Read the segmentation × band robustness table
cat results/frozen/comparators/markets_fast_robustness_packet_v1__20260421T175531Z/markets_fast_segmentation_band_robustness_table_v1.md
```

### 4.5 Inspect the recommender benchmark freeze

```bash
# Read the recommender manuscript freeze (JSON; contains SHA index of all manifests)
cat results/frozen/movielens25m_recursive_frontier_public_v1__manuscript_freeze_state.json

# Read the gate-3 report (contains final framing decision and bridge/comparator outcome)
cat results/manifests/movielens25m_recursive_frontier_public_v1__gate3_report.json

# Read the rendered recommender comparator table
cat results/manifests/movielens25m_recursive_frontier_public_v1__paper_facing_comparator_table.csv
```

---

## 5. Frozen verification layer: commands

These commands reproduce manuscript-facing and supplementary outputs from frozen canonical inputs.
No external data access is required.

### 5.1 Validate artifact integrity

```bash
# Validate public threshold disclosure against frozen state
python analysis/09_validate_public_thresholds.py

# Run the artifact integrity test suite
python -m pytest -q tests/test_public_thresholds.py tests/test_artifact_manifest.py
```

### 5.2 Regenerate Table Sy (witness-direction bridge exhibit)

Reads from the frozen bridge state. Writes the rendered table to
`results/rendered/bridge/witness_direction_table_v3.{csv,md}`.

```bash
python analysis/13bb_build_witness_direction_table_v3.py
```

### 5.3 Regenerate Table 1 (markets comparator rows)

Reads from the frozen markets comparator merged state. Writes the paper-facing
table to the markets comparator frozen directory.

```bash
python analysis/13am_build_markets_comparator_paper_table_v1.py
```

### 5.4 Regenerate recommender comparator tables (Table 1 recommender rows and Table Sx)

Reads from the frozen recommender manifests.

```bash
python src/loopzero_paper/benchmarks/recommender/build_paper_facing_comparator_table.py
```

### 5.5 Regenerate all publication figures

Reads from the frozen recommender manuscript freeze state and the frozen markets
comparator merged state. Writes Figures 1–3 to `results/figures/` in PNG and PDF.

```bash
python src/loopzero_paper/benchmarks/recommender/generate_manuscript_artifacts.py
```

---

## 6. Full pipeline (requires external data)

This section describes the full upstream pipeline. It is included for completeness;
external data access is required for both domains.

### 6.1 Markets domain

**Data access.** Raw and processed market panels are not included in this public
branch. The canonical markets comparator benchmark (`volmageddon_covid_public_v2`)
was produced from Alpaca free-tier minute-bar data for SPY, QQQ, IWM, VXX, UVXY,
and SVXY over the Volmageddon (February 2018) and COVID circuit-breaker (March 2020)
event families. Raw re-fetch scripts are not included in this public branch. An Alpaca
free-tier account is required to access source data independently.

**Pipeline.** The frozen canonical outputs in `results/frozen/` are the authoritative
reproducibility layer for this public branch. Full upstream reruns require additional
local setup, external data access, and pipeline components not included here.

### 6.2 Recommender domain

**Data access.** MovieLens-25M is freely downloadable from
`https://grouplens.org/datasets/movielens/25m/`. Place the extracted archive so
that `ml-25m/ratings.csv` is accessible at the path expected by the pipeline.

**Pipeline.** The full recommender pipeline — benchmark construction, bridge check,
fast-family calibration, slow-family calibration, horizon sensitivity, and freeze —
is implemented in `src/loopzero_paper/benchmarks/recommender/`. Individual stages are
gated; each gate must pass before the next stage runs. The frozen manifests in
`results/manifests/` are the canonical record of each stage outcome.

---

## 7. Artifact provenance and SHA verification

Each frozen state contains a `freeze_manifest.json` listing every file with its
`sha256` hash and `size_bytes`. To manually verify a specific file:

```bash
python3 -c "
import hashlib, pathlib
p = pathlib.Path('results/frozen/bridge/witness_direction_bridge_state_v3__20260422T130759Z/witness_direction_table_v3.csv')
print(hashlib.sha256(p.read_bytes()).hexdigest())
"
# Compare against the sha256 field in freeze_manifest.json
```

Expected SHA-256 values for the primary manuscript-facing files are recorded in the
manifests listed in section 3. The test suite (`tests/test_artifact_manifest.py`)
automates this check for all registered artifacts.

---

## 8. Figures and tables: source map

See `docs/FIGURE_TABLE_MAP.md` for the full mapping of each manuscript figure and
table to its frozen source, rendered artifact path, and generating script.
