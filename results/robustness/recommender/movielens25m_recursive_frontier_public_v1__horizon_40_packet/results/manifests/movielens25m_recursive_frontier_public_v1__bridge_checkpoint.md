# Bridge Checkpoint — movielens25m_recursive_frontier_public_v1

**Status:** `telemetry_checkpoint_only`

**Decision:** `PARTIAL`

**Recommended action:** Benchmark freeze holds and telemetry completed, but the theorem-to-observable bridge is only partially aligned. Treat this as an exploratory checkpoint, not manuscript-final, and refine the proxy definitions before comparator calibration.

## Checkpoint note

- benchmark freeze holds: `True`
- telemetry completed: `True`
- G aligned: `False`
- p aligned: `True`
- delta aligned: `True`

## Proxy values

### Pre-collapse events

- G_mean: `0.06085479581127507`
- p_mean: `0.2127795290931448`
- delta_mean: `0.5968521773531568`

### Reference controls

- G_mean: `0.08175988899853573`
- p_mean: `0.1869710246859902`
- delta_mean: `0.6084493348409566`

## Summary note

- Benchmark freeze holds and telemetry completed. This artifact records an exploratory telemetry checkpoint only.
- Formal bridge decisions for robustness and manuscript use must be taken from bridge_check.py, not this checkpoint artifact.
- Do not treat this telemetry checkpoint as a manuscript-final bridge decision.

## Next steps

- Use bridge_check.py as the formal bridge decision artifact.
- Use gate2_check.py for fast-family adjudication.
- Use merged comparator summaries and the paper-facing table for comparator claims.
- Treat this checkpoint as descriptive telemetry provenance only.

