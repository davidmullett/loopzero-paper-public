# Witness Direction Bridge State v3 Lock Note

This freeze captures the manuscript-facing witness-direction bridge exhibit for the
canonical public-markets and recommender benchmarks.

## Scope
This state freezes:
- `witness_direction_table_v3.csv`
- `witness_direction_table_v3.md`

## Scientific interpretation supported by this state

### Recommender benchmark
On the canonical 50-step MovieLens recursive frontier benchmark, the theorem-guided
directional witness summary is fully aligned:
- gain `G`: event > control
- recursive persistence `p`: event > control
- diversity `delta`: event < control

### Markets benchmark
On the canonical public-markets benchmark, directional witness alignment depends on
the localization window used inside each exact canonical unit.

At the last 30 minutes of each canonical unit, the markets witness summary is fully aligned:
- gain `G`: event > control
- recursive persistence `p`: event > control
- diversity-change `delta_change`: event < control

At the last 60 minutes of each canonical unit, the markets witness summary is partial:
- gain `G`: event > control
- recursive persistence `p`: event > control
- diversity-change `delta_change`: not directionally aligned

## Editorial boundary
This state supports the narrower claim that:
- the recommender bridge is fully aligned on the canonical benchmark
- the markets bridge is strongest in the localized 30-minute late-window regime
- the 60-minute markets summary is a sensitivity variant, not the primary bridge exhibit

It does not support a stronger claim of uniform full-triad invariance across all wider
markets late-window summaries.

## Governance
- archival and immutable
- manuscript wording should cite this frozen state rather than mutable rendered files
