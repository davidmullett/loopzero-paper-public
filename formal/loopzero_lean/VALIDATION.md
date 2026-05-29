# Lean Proof Validation Record

## Public keeper surface
- `no_progress_cycle_public` (LoopzeroLean/NoProgressCyclePublic.lean)
- `no_progress_kcycle_public` (LoopzeroLean/NoProgressCyclePublic.lean)
- `collapse_via_progresscycle_public` (LoopzeroLean/NoProgressCyclePublic.lean)
- `TelemetryState` (LoopzeroLean/TelemetryBridgePublic.lean)
- `telemetryμ` (LoopzeroLean/TelemetryBridgePublic.lean)
- `telemetry_bridge_obstruction_public` (LoopzeroLean/TelemetryBridgePublic.lean)
- `no_telemetry_forbidden_cycle_public` (LoopzeroLean/TelemetryBridgePublic.lean)

## Environment
- Lean version: 4.30.0-rc2
- Mathlib commit: 3ba1ec58ec69cd649b9e5c61485a98d1dd37a00f
- Build system: Lake (lake-manifest.json present)
- Platform: macOS Sequoia, arm64-apple-darwin

## Validation results

### Level 1 — Kernel acceptance
- Command: `lake build`
- Result: Build completed successfully
- Date: 2026-05-07

### Level 2 — Axiom audit
- Command: inline `#print axioms` declarations in the public Lean files
- Result: `no_progress_cycle_public`, `no_progress_kcycle_public`, and `collapse_via_progresscycle_public` do not depend on any axioms. The telemetry theorems over `ℚ` may depend on standard Lean/mathlib foundations such as `propext`, `Classical.choice`, and `Quot.sound`.
- Interpretation: The public artifact uses no Loopzero-specific or user-declared axioms. The telemetry layer is a schematic rational measurement-map specialization, not a verified empirical adapter.
- Date: 2026-05-07

### Level 3 — External re-checking with lean4checker
- Command: `lake env lean4checker LoopzeroLean.NoProgressCyclePublic`
- Result: silent successful exit, all declarations re-accepted by the kernel
- Tool version: lean4checker master at commit 91a7f0e8e9dffe927089f5a6edcfeeb8a0e07709
- Date: 2026-05-01

### Level 4 — Independent kernel verification with nanoda
- Exporter: leanprover/lean4export at v4.30.0-rc2 (format version 3.1.0)
- Independent kernel: nanoda_lib v0.4.9-beta (Rust)
- Export size: 704 MB (full transitive closure of theorem dependencies)
- Result: `Checked 168354 declarations with no typechecker errors`
- Date: 2026-05-01
- Note: This corresponds to the multi-kernel verification architecture described in de Moura, "Who Watches the Provers?" (2026-03-16).
