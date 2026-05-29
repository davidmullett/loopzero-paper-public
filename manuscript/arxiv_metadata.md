# arXiv Submission Metadata — Loopzero v1

Generated from manuscript **v17.16** on 2026-05-28.

## Files

Main manuscript: `mullett_loopzero_matched_fp_main_v1.pdf`  
Supplementary materials: `mullett_loopzero_matched_fp_supplement_v1.pdf`


## Title

Benchmarking Recursive-Collapse Warning Claims Under Matched False-Positive Control

## Author

David Mullett

## Affiliation

Independent Researcher

## ORCID

0009-0004-2543-1664

## Corresponding email

d@loopzero.org

## Abstract

Recursive systems can enter collapse-like regimes --- self-reinforcing amplification, persistent recursion, and narrowing diversity that mask accelerating internal degradation --- before overt failure becomes visible. We introduce Loopzero, a claim-bounded benchmark framework for testing whether recursive failures follow a directional telemetry pattern: rising gain (G), recursive persistence (p), and declining diversity ($\delta$). The claim boundary is specified in Lean; the Lean artifact does not verify real telemetry, benchmark validity, or detector performance.

We evaluate the bridge on two frozen public-artifact benchmarks: a segmented public-markets benchmark (Volmageddon 2018, COVID MWCB 2020) and a MovieLens-25M offline deterministic recommender replay. Detectors are evaluated under a locked equal-false-positive contract (FP $\in$ [0.03, 0.07], pre-registered) so all configurations face the same alert budget. Neither tested standard comparators nor Loopzero's pre-registered quantile detector achieved an accepted operating point. Directional witness alignment held on both canonical benchmarks, with adjacent-horizon and row-level limitations disclosed. Digitized Shumailov et al. (2024) LLM training-loop trajectories are directionally consistent with the pattern; matched-FP evaluation in that domain is deferred.

The contribution is a reproducible, falsifiable benchmark framework for evaluating recursive-collapse warning claims under an explicit alert-budget contract --- non-acceptance reported as a first-class scientific outcome.

## Primary category

eess.SY — Systems and Control

## Cross-list categories

cs.LG — Machine Learning  
stat.ML — Machine Learning

## License

CC BY 4.0

## Comments

29 pages, 7 figures, 2 tables; supplementary materials: 9 pages, 1 figure, 4 tables. Code, derived data packets, and Lean artifact: https://github.com/davidmullett/loopzero-paper-public

## Upload files

1. `mullett_loopzero_matched_fp_main_v1.pdf`
2. `mullett_loopzero_matched_fp_supplement_v1.pdf`

## Notes

- `cs.SY` is the Computer Science alias for `eess.SY`; use `eess.SY` as the primary category if that is the endorsed category shown in the arXiv submission flow.
- Use ASCII-safe abstract text in the arXiv form: `---`, `$\delta$`, `$\in$`, and plain apostrophes.