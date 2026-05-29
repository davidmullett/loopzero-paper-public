# Adversarial Citation Embedding Audit (v2 — post-fix)

**Manuscript:** `manuscript/paper_v1_main_citation_working.md`
**Audit date:** 2026-04-28
**Prompt:** `citation_map/prompts_adversarial_citation_embedding_audit.txt`
**Auditor stance:** Hostile reviewer / editorial desk check
**Previous audit:** `adversarial_citation_fix_change_log.md` documents the 8 fixes applied before this re-audit

---

## Method

Full re-audit of every in-text citation after Fix 1–8 were applied. All 12 checklist items evaluated against the current manuscript state.

---

## Issues resolved since v1

| v1 Issue | Resolution |
|---|---|
| Buldyrev 2010 on paper's own formal claim | Fixed: now on "cascading failure in interdependent systems" motivation sentence |
| Scheffer 2001 / Holling 1973 on recursive-specific claim | Fixed: moved to "collapse in complex systems" framing sentence |
| EWS citations used adversarially | Fixed: now cited as "established early-warning and critical slowing down literature" |
| Fleder 2009 in technical methods sentence | Fixed: moved to dedicated diversity-motivation sentence |
| ESRB 2019 co-cited with Augustin for Volmageddon | Fixed: moved to VIX/volatility-linked products sentence |
| Hales 2017 inside Lean parenthetical | Fixed: separated into formal-verification-epistemics sub-cluster |
| Table X placeholder | Fixed: Table 1 with body cross-reference added |
| Figure [robustness] placeholder | Fixed: Supplementary Figure S1 |

---

## Remaining issues

### Issue 1 — MINOR: "The starting point here" echo across adjacent paragraphs

**Location:** §1 "A formally specified obstruction for recursive collapse," lines 33 and 35

**Current text (line 33, last sentence):**
> "...the starting point here is instead a formally specified structural obstruction."

**Current text (line 35, first sentence):**
> "The starting point here is a formally specified no-progress obstruction for recursive feedback systems, verified in Lean..."

**Problem:**
The phrase "the starting point here" now appears in the closing sentence of paragraph 1 and the opening sentence of paragraph 2, separated only by a blank line. This verbal echo is awkward and slightly redundant — the reader is told twice in succession that the starting point is a formal obstruction. This is a manuscript quality issue (not a citation accuracy issue) introduced when Fix 2 rewrote the last sentence of paragraph 1.

**Recommended fix:**
Rephrase paragraph 1's closing sentence to avoid the duplicate: e.g., "...the starting point here is instead a formally specified structural obstruction, described in the following section." Or rephrase paragraph 2's opening: "This paper begins from a formally specified no-progress obstruction..." Either way, one occurrence of "starting point here" is enough.

**Fix timing:** Before advisor share (minor but immediately visible)

---

### Issue 2 — MINOR: "The result instead" pronoun may momentarily misattribute (§2)

**Location:** §2 "Theorem-to-observable bridge," line 39

**Current text:**
> "Cascading failure in interdependent systems provides structural motivation for treating recursive no-progress as a distinct failure mode (Buldyrev et al., 2010). The result instead identifies a class of recursive no-progress regimes in which local continuation remains possible while meaningful forward improvement becomes inaccessible."

**Problem:**
After the Buldyrev sentence, "The result instead" could momentarily be parsed as "Buldyrev's result instead..." before context clarifies it means the paper's formal result. The ambiguity is brief and resolved by the next clause, but it creates a micro-stumble for a fast reader. This is a secondary effect of Fix 1's insertion of the Buldyrev motivation sentence.

**Recommended fix:**
Clarify the referent: "The formal result derived here instead identifies..." or simply "The paper's obstruction instead identifies..."

**Fix timing:** Before arXiv

---

### Issue 3 — MINOR (unchanged from v1): EWS 4-citation cluster density

**Location:** §1 line 33

**Current text:**
> "(Scheffer et al., 2009; Scheffer et al., 2012; Carpenter et al., 2011; Dakos et al., 2012)"

**Problem:**
Four citations in a single parenthetical remains atypical for Science-style introductory framing, even though the framing is now positive and non-adversarial (Fix 3). Science papers typically lead with 1–2 representative anchors for an established literature.

**Note:** This was not reduced by Fix 3 (the prompt scoped Fix 3 to framing tone, not citation count). Flagged here for completeness; it is the lowest-priority remaining citation issue.

**Recommended fix:**
Before final typesetting, consider reducing to two most foundational anchors (e.g., Scheffer et al., 2009 and Dakos et al., 2012) and moving Scheffer 2012 and Carpenter 2011 to supplementary or a Methods sentence.

**Fix timing:** Before arXiv (low priority)

---

### Issue 4 — MINOR: Supplementary Figure S1 has no image path

**Location:** §Figure and Table Legends, line 127

**Current text:**
> "**Supplementary Figure S1. Fast-family segmentation and band sensitivity on the canonical markets benchmark.**..."

**Problem:**
No `![Supplementary Figure S1](assets/...)` image reference exists in the manuscript. The figure legend is present but there is no corresponding rendered figure asset. This is a known placeholder state (noted in the fix change log).

**Recommended fix:**
When the segmentation/band-sensitivity figure is rendered, add the image path and a Supplementary Materials cross-reference in the body (e.g., §9 fast-family robustness section).

**Fix timing:** Before arXiv

---

## Checks with no issues

| Check | Result |
|---|---|
| References in body but missing from References section | None |
| References section entries not cited in body | None — all 29 cited |
| Institutional reports used for peer-reviewed theory claims | None — CFTC 2010 at Flash Crash narrative; NYSE 2020 at circuit-breaker event; ESRB 2019 at VIX/volatility-linked systemic risk context (regulatory fact) |
| Buldyrev 2010 placement | Resolved — now on cascading failure motivation sentence |
| Scheffer 2001 / Holling 1973 placement | Resolved — on "collapse in complex systems is well-established" |
| Shumailov 2024 used conservatively | Yes — one occurrence, only for recursive/model-collapse adjacency |
| Lean citations in correct context | Resolved — de Moura & Ullrich 2021 and mathlib 2020 are Lean-specific; Hales 2017 separated into formal-verification-precedent sub-cluster |
| Hales 2017 no longer implies Lean usage | Yes — now cited under "formally verified proofs in mathematics" sub-clause |
| Recommender citations supporting dataset/feedback-loop claims | Resolved — Fleder 2009 on diversity motivation; Chaney/Jiang/Mansoury on construction |
| Markets citations supporting Volmageddon/VIX/circuit-breaker claims | Resolved — Augustin 2021 alone for Volmageddon; ESRB 2019 with Whaley 2009 for VIX/volatility-linked systemic risk framing |
| Boettiger 2012a/b disambiguation | Consistent in body and References |
| Table 1 cross-reference present | Yes — §4 and Legends both reference Table 1 |
| Figures 1–3 image paths intact | Yes — all three asset paths unchanged |
| Supplementary Figure S1 identified | Yes — legend present; image path pending |

---

## Final Verdict

**advisor_share_ready:** yes (conditional on fixing Issue 1 — the "starting point here" echo is immediately visible to any reader and takes one sentence to fix)

**arxiv_ready:** no (Issues 1–4 should be resolved; Supplementary Figure S1 needs an image path before arXiv submission)

**Top three required fixes:**

1. **"Starting point here" echo** (Issue 1 — MINOR, but first-impression risk): Rephrase one of the two occurrences of "the starting point here" in adjacent paragraphs of §1.

2. **"The result instead" pronoun ambiguity** (Issue 2 — MINOR): Clarify to "The formal result derived here instead identifies..." so no reader momentarily attributes the identification claim to Buldyrev.

3. **Supplementary Figure S1 image path** (Issue 4 — MINOR): Add asset path and body cross-reference when the figure is rendered.
