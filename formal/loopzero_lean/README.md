# loopzero_lean
# Loopzero Lean Proof Artifact

A formally verified theorem in Lean 4 supporting the manuscript "A formally specified warning criterion for collapse in recursive systems" (Mullett 2026, in preparation).

## What's here

This repository contains a small Lean 4 artifact: an abstract no-progress obstruction, a measurement-map bridge, a schematic G/p/δ-style telemetry specialization, the Lake project that builds them, and validation notes.

The formal layer is intentionally minimal. Its role in the manuscript is not to prove a deep result — it is to provide a kernel-verified claim boundary for the paper's pre-collapse criterion.

## The public keeper surface

```lean
theorem no_progress_cycle_public {x y z : α} [Preorder α]
    (hxy : x < y) (hyz : y ≤ z) (hzx : z ≤ x) : False

theorem no_progress_kcycle_public {α : Type u} [Preorder α]
    {x y z : α} (hxy : x < y) (hpath : y ≤ z) (hzx : z ≤ x) : False

theorem collapse_via_progresscycle_public
    {α : Type u} {β : Type u} [Preorder β]
    (μ : α → β) {x y z : α}
    (hxy : μ x < μ y) (hyz : μ y ≤ μ z) (hzx : μ z ≤ μ x) : False
```

In words: in any preorder, you cannot have a strict step from `x` to `y`, a non-strict path from `y` to `z`, and a non-strict step from `z` back to `x`. The measurement bridge states the same obstruction after applying any map `μ` into an ordered codomain.

The telemetry specialization is schematic:

```lean
structure TelemetryState where
  G : ℚ
  p : ℚ
  δ : ℚ

def telemetryμ (s : TelemetryState) : ℚ :=
  s.G + s.p - s.δ

theorem telemetry_bridge_obstruction_public ...
theorem no_telemetry_forbidden_cycle_public ...
```

It does not verify any empirical parser, benchmark adapter, or real-world measurement claim. The empirical claim that benchmark telemetry supplies an appropriate measurement map remains external to Lean and is tested by the benchmark protocol.

## Verification record

The theorem has been verified by four independent levels of checking:

| Level | What | Result |
|-------|------|--------|
| 1 | Kernel acceptance via `lake build` | Build completed successfully |
| 2 | Axiom audit via `#print axioms` | No Loopzero-specific or user-declared axioms |
| 3 | External re-checking via `lean4checker` | All declarations re-accepted, no errors |
| 4 | Independent kernel via `nanoda` | 168,354 declarations checked, no typechecker errors |

Full validation outputs are in `VALIDATION.md`.

## Environment

- Lean: 4.30.0-rc2
- Mathlib commit: 3ba1ec58ec69cd649b9e5c61485a98d1dd37a00f
- Build system: Lake
- Verified on: macOS Sequoia, arm64

Exact dependency commits are pinned in `lake-manifest.json`.

## Reproducing the verification

### Level 1 — Build

```bash
lake update
lake build
```

Expected output: `Build completed successfully` plus inline `#print axioms` output for the public keeper theorems. The preorder obstruction does not depend on axioms. The telemetry theorems over `ℚ` may depend on standard Lean/mathlib foundations such as `propext`, `Classical.choice`, and `Quot.sound`; they do not depend on Loopzero-specific or user-declared axioms.

### Level 3 — External re-checking with lean4checker

Add `lean4checker` to `lakefile.toml`:

```toml
[[require]]
name = "lean4checker"
git = "https://github.com/leanprover/lean4checker.git"
rev = "master"
```

Then:

```bash
lake update lean4checker
lake build lean4checker
lake env lean4checker LoopzeroLean.NoProgressCyclePublic
```

### Level 4 — Independent kernel via nanoda

Build `lean4export` and `nanoda_lib`:

```bash
git clone https://github.com/leanprover/lean4export.git
cd lean4export
lake build

git clone https://github.com/ammkrn/nanoda_lib.git
cd nanoda_lib
cargo build --release
```

Generate the export and run nanoda:

```bash
cd <this-artifact-directory>
lake env <path-to>/lean4export/.lake/build/bin/lean4export LoopzeroLean.NoProgressCyclePublic > export.out
<path-to>/nanoda_lib/target/release/nanoda_bin nanoda_config.json
```

Expected output: `Checked 168354 declarations with no typechecker errors`.

## How to cite

If you use or reference this artifact, please cite the manuscript when published, and the Zenodo deposit:

```
Mullett, D. (2026). Loopzero Lean Proof Artifact (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/[DOI-PENDING]
```

## License

Apache License 2.0. See `LICENSE`.

## Contact

David Mullett — d@loopzero.org — ORCID 0009-0004-2543-1664
