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
REPO="$(cd ../.. && pwd)"   # repo root, for resolving assets/ image paths

# Map the math glyphs the text font (STIX Two Text) does not carry to LaTeX math,
# rewrite repo-relative image paths to absolute, and (main paper only) drop the
# not-for-manuscript appendix.
prep() { # prep <src> <out> <strip_appendix:0|1>
python3 - "$1" "$2" "$3" "$REPO" <<'PY'
import sys, re
src, out, strip, repo = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
s = open(src).read()
if strip == '1':
    s = s.split('## APPENDIX — Notes for revision')[0].rstrip() + '\n'
# resolve repo-relative image paths (assets/...) to absolute so xelatex finds them
s = s.replace('](assets/', f']({repo}/assets/')
subs = {
    '≥': r'$\geq$', '≤': r'$\leq$', '→': r'$\rightarrow$',
    '≈': r'$\approx$', '√': r'$\sqrt{}$', '∎': r'$\blacksquare$',
}
for k, v in subs.items():
    s = s.replace(k, v)
# pandoc's currency heuristic will not close inline math when the closing '$'
# is immediately followed by a digit (e.g. $\sqrt{}$1.208). Insert a space so
# the math closes; a math-closing '$' is always the one adjacent to a digit here.
s = re.sub(r'\$(\d)', r'$ \1', s)
open(out, 'w').write(s)
PY
}

render() { # render <intermediate.md> <out.pdf>
# Two-step (pandoc -> standalone .tex -> xelatex) rather than pandoc's direct
# -o PDF: direct mode copies images into a temp media dir, and xelatex fails to
# load the Figma-exported fig1 from that copy. The .tex keeps the absolute
# assets/ paths (rewritten in prep) and xelatex loads them in place. Run twice
# for the table of contents.
local base="${2%.pdf}"
pandoc "$1" -s -o "$base.tex" --pdf-engine=xelatex \
  --from=markdown-implicit_figures \
  -V geometry:margin=1in -V fontsize=11pt \
  -V mainfont="STIX Two Text" \
  -V colorlinks=true -V linkcolor=black -V urlcolor=blue \
  --resource-path="$REPO" \
  --toc -V toc-title="Contents"
xelatex -interaction=nonstopmode -halt-on-error "$base.tex" >/dev/null 2>&1 || true
xelatex -interaction=nonstopmode -halt-on-error "$base.tex" > "$base.xelog" 2>&1
grep -q "Output written on $base.pdf" "$base.xelog" || { echo "BUILD FAILED: $2"; tail -15 "$base.xelog"; exit 1; }
rm -f "$base.tex" "$base.aux" "$base.log" "$base.out" "$base.toc" "$base.xelog"
echo "Built $2"
}

prep "../paper_shadow_classes.md"    "paper_main.md"       1
render "paper_main.md" "paper_main.pdf"

if [ -f "../supplement_shadow_classes.md" ]; then
  prep "../supplement_shadow_classes.md" "supplement_main.md" 0
  render "supplement_main.md" "supplement_main.pdf"
fi
