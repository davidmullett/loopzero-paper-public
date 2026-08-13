#!/usr/bin/env bash
# Build a draft PDF of the successor manuscript from the markdown SSOT.
#
# Pipeline: paper_shadow_classes.md
#   -> strip the "APPENDIX — Notes for revision (not for the manuscript)" section
#   -> map the handful of math Unicode glyphs XeLaTeX's text font lacks to LaTeX math
#   -> pandoc -> xelatex -> paper_main.pdf
#
# This is a DRAFT render for verification. Figures (fig1/2/3) are described in the
# text but not embedded (the figure PDFs are not yet in the repo), and the final
# arXiv submission is expected to be a hand-managed .tex intermediate (see the
# pandoc>=3.9 \seqsplit note in the session brief). The SSOT markdown is never
# modified by this script.
set -euo pipefail
cd "$(dirname "$0")"
SRC="../paper_shadow_classes.md"
MAIN="paper_main.md"
OUT="paper_main.pdf"

python3 - "$SRC" "$MAIN" <<'PY'
import sys
src, out = sys.argv[1], sys.argv[2]
s = open(src).read()
# drop the appendix (explicitly "not for the manuscript")
s = s.split('## APPENDIX — Notes for revision')[0].rstrip() + '\n'
# map math glyphs the text font (STIX Two Text) does not carry to LaTeX math
subs = {
    '≥': r'$\geq$', '≤': r'$\leq$', '→': r'$\rightarrow$',
    '≈': r'$\approx$', '√': r'$\sqrt{}$', '∎': r'$\blacksquare$',
}
for k, v in subs.items():
    s = s.replace(k, v)
open(out, 'w').write(s)
PY

pandoc "$MAIN" -o "$OUT" --pdf-engine=xelatex \
  -V geometry:margin=1in -V fontsize=11pt \
  -V mainfont="STIX Two Text" \
  -V colorlinks=true -V linkcolor=black -V urlcolor=blue \
  --toc -V toc-title="Contents"

echo "Built $OUT"
