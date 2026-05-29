# Bridge Checkpoint — movielens25m_recursive_frontier_public_v1

**Status:** `telemetry_checkpoint_only`

**Decision:** `PASS`

**Recommended action:** Bridge appears directionally aligned under the current telemetry package. Proceed to a formal bridge-check stage and, if confirmed, then to fast-family comparator calibration.

## Checkpoint note

- benchmark freeze holds: `True`
- telemetry completed: `True`
- G aligned: `True`
- p aligned: `True`
- delta aligned: `True`

## Proxy values

### Pre-collapse events

- G_mean: `0.06058198642809157`
- p_mean: `0.208219100465888`
- delta_mean: `0.5997551700069771`

### Reference controls

- G_mean: `0.029034045700712365`
- p_mean: `0.20714670695320847`
- delta_mean: `0.6010488987900375`

## Summary note

- Benchmark freeze holds and telemetry completed. This artifact records an exploratory telemetry checkpoint only.
- Formal bridge decisions for robustness and manuscript use must be taken from bridge_check.py, not this checkpoint artifact.
- Do not treat this telemetry checkpoint as a manuscript-final bridge decision.

## Next steps

- Use bridge_check.py as the formal bridge decision artifact.
- Use gate2_check.py for fast-family adjudication.
- Use merged comparator summaries and the paper-facing table for comparator claims.
- Treat this checkpoint as descriptive telemetry provenance only.

