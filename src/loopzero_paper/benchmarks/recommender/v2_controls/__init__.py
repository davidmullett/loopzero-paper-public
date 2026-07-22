"""V2 controls pre-registration analysis (osf.io/7bvgz, frozen 2026-07-09).

Implements the frozen pre-reg clause-by-clause. Reads only; writes non-frozen
outputs to results/v2_controls/. §11 decision quantities are gated behind
decision.RATIFIED and must not be computed until the author ratifies the Phase-1
rulings (deviations log).
"""
