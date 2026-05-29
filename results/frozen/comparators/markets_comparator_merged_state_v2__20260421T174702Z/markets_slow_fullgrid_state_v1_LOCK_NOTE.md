# Markets Slow Full-Grid State v1 Lock Note

This freeze captures the full predeclared slow-family comparator grids on the
canonical markets comparator benchmark.

## Canonical benchmark
- Instantiation: `volmageddon_covid_public_v2`
- Canonical source config: `cfg_001339`
- Unitization rule: one underlying market segment = one comparator unit
- n_control_units = 38
- n_event_units = 16
- locked equal-FP band = [0.03, 0.07]
- fp_grid_step = 1 / 38 = 0.026316

## Scope
- Slow family 1: `matrix_profile` full predeclared grid
- Slow family 2: `permutation_entropy` full predeclared grid

## Bounded interpretation
- No full-grid slow comparator configuration was accepted under the locked equal-FP rule.
- Matrix profile exhibited a split between trivial silence and severe overfiring.
- Permutation entropy's nearest full-grid configurations were trivial-silent.
- This freeze should be treated as the canonical full-grid slow comparator state.

## Governance
- This freeze is archival and immutable.
- Any future slow-comparator expansion should be written as a new state.
