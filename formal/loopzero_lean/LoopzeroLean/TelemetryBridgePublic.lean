import LoopzeroLean.NoProgressCyclePublic
import Mathlib.Algebra.Order.Ring.Rat

/-!
# Public schematic telemetry bridge

This file gives a deliberately schematic G/p/δ-style specialization of the
abstract measurement-map bridge. `TelemetryState` is not a verified parser or
adapter for the empirical benchmarks. The empirical claim that real benchmark
telemetry supplies an appropriate measurement map remains external to Lean and
is tested by the manuscript's benchmark protocol.
-/

/-- Minimal rational telemetry state with gain, persistence, and diversity fields. -/
structure TelemetryState where
  G : ℚ
  p : ℚ
  δ : ℚ

/-- Schematic ordered measurement used by the public telemetry bridge. -/
def telemetryμ (s : TelemetryState) : ℚ :=
  s.G + s.p - s.δ

/--
Instantiation of the public measurement bridge at `TelemetryState` and
`telemetryμ`.
-/
theorem telemetry_bridge_obstruction_public
    {x y z : TelemetryState}
    (hxy : telemetryμ x < telemetryμ y)
    (hyz : telemetryμ y ≤ telemetryμ z)
    (hzx : telemetryμ z ≤ telemetryμ x) : False :=
  collapse_via_progresscycle_public telemetryμ hxy hyz hzx

/-- No three telemetry states can form a forbidden strict/weak/weak measured cycle. -/
theorem no_telemetry_forbidden_cycle_public :
    ¬ ∃ x y z : TelemetryState,
      telemetryμ x < telemetryμ y ∧
      telemetryμ y ≤ telemetryμ z ∧
      telemetryμ z ≤ telemetryμ x := by
  intro ⟨x, y, z, hxy, hyz, hzx⟩
  exact telemetry_bridge_obstruction_public hxy hyz hzx

#print axioms telemetry_bridge_obstruction_public
#print axioms no_telemetry_forbidden_cycle_public
