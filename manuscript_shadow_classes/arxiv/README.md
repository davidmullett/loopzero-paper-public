# arXiv submission source — "Absorbing Shadow Classes in Conjunctive Label Rules"

Exact source package submitted to arXiv on **2026-08-20** (submission 7973355).
Committed here to close a receipts gap: the successor manuscript builds through
`../build/build.sh`, whose intermediate `.tex` is gitignored, so the file arXiv
actually compiled was never in version control. These are the byte-exact
artifacts that were uploaded.

## Contents

- **`main.tex`** — the exact `.tex` submitted (single file, no local `.sty`).
- **`arxiv_source.zip`** — the exact uploaded package: `main.tex` plus the three
  figure PDFs (`fig1_absorbing_shadow_state.pdf`, `fig2_bounding_diagnostic.pdf`,
  `fig3_delta_tpr_by_budget.pdf`) at the top level.

## Build notes (how arXiv compiled it)

- **Engine:** arXiv AutoTeX selects **XeLaTeX** because the preamble loads
  `fontspec` unconditionally. Compiled against **TeX Live 2025**.
- **Fonts:** **Latin Modern** (the fontspec default, loaded from bundled `.otf`
  with no by-name lookup) is used throughout. **STIX Two** — the repo's local
  build font — is deliberately *not* requested here, because it is not in the
  arXiv TeX Live tree; Latin Modern was substituted for portability. This is the
  only intentional divergence from the local `build/` PDF.
- **Figures:** referenced by **bare relative paths** (`fig1_...pdf`, not
  `assets/fig1_...pdf`), since all four files sit at the archive root.
- Compiles clean under `xelatex` ×2: 17 pp, no missing glyphs, no overfull hbox,
  no table of contents.

## Relationship to the repository sources

`main.tex` is generated (pandoc → XeLaTeX) from the canonical Markdown at
`../paper_shadow_classes.md`; the figure PDFs are the committed
`../../assets/fig{1,2,3}_*.pdf`. The prose is identical to the manuscript at the
tagged commit — the arXiv-only adjustments are render-level (Latin Modern
substitution, table-of-contents removed, `\sloppy` on the reference list) and
carry no wording changes.

## Known cosmetic issue (tracked for the next replacement)

Figure 1's "LABEL RULE" card overlaps the "Degraded" box; no text is obscured.
Fixed in the Figma source and will ship with the next arXiv replacement version.
