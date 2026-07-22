# Reproducing the Study-2 analysis

## Absolute paths in the analysis scripts are deliberate, not accidental

Several scripts under `src/loopzero_paper/benchmarks/recommender/` — including
`run_block_execution1.py`, `run_block_execution2.py`, `phase4_execution.py`,
`rederive_publication_tables.py`, `characterize_starved_history.py`, `item6_correction.py`,
`calclean_correlation_remedy.py`, and `tsplit_power_probe.py` — carry a hardcoded absolute
`sys.path` entry from the development environment:

```python
sys.path.insert(0, "/Users/david/Dev/loopzero-paper-public/src")
```

**These files are left byte-identical on purpose.** Their SHA-256 hashes are anchored and cited in
the manuscript (the C\*\*\* `CODE_ANCHOR` rollup and related manifests under `preregistration/`), and
the paper's tamper-evidence argument depends on the published files matching those anchored hashes
exactly. Relativizing the path would change the bytes and invalidate a hash the paper cites — trading
a cosmetic tidiness for a break in the provenance chain. We chose the provenance chain.

## To run the scripts

Either of the following works without editing any anchored file:

```bash
# Option A — set PYTHONPATH to the repo's src directory (recommended)
cd <repo-root>
PYTHONPATH=src python3 src/loopzero_paper/benchmarks/recommender/phase4_execution.py

# Option B — adjust the single sys.path line locally (do NOT commit the change;
# it will alter the file's anchored hash)
```

The registered analysis package lives at `src/loopzero_paper/benchmarks/recommender/v2_controls/`
and reads only anchored inputs. Numerical results re-derive from the sealed verdict payload
(`results/v2_controls/s2_verdict_payload.json`); the pre-registration and deviation log are under
`preregistration/`.

## What is and isn't in this repository

Published: the analysis code, the deviation log (`preregistration/DEVIATIONS.md`), the JSON/CSV/
Markdown result artifacts, and the small covariate caches — enough to exercise the reproducibility
claims rather than merely assert them.

Not published (content-hash anchored only): the six per-arm slate panels
(`results/v2_controls/arm_*__slate_panel.csv.gz`, anchored via `ARM_PANELS.sha256` /
`PANEL_MANIFEST.sha256`) and the raw/sorted MovieLens-25M ratings under `data/` (anchored via
`INPUT_MANIFEST.sha256`). These are large and are recoverable from the public GroupLens
distribution plus the anchored build scripts.
