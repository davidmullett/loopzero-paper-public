# Adversarial Citation Fix Change Log

**Manuscript:** `manuscript/paper_v1_main_citation_working.md`
**Fix date:** 2026-04-28
**Prompt:** `citation_map/prompts_fix_adversarial_citation_audit_items.txt`
**Source audit:** `citation_map/outputs/adversarial_citation_embedding_audit.md`

---

## Fix 1 — Buldyrev citation placement (§2 Theorem-to-observable bridge)

**Before:**
> "Instead, it identifies a class of recursive no-progress regimes in which local continuation remains possible while meaningful forward improvement becomes inaccessible (Buldyrev et al., 2010)."

**After:**
> "Cascading failure in interdependent systems provides structural motivation for treating recursive no-progress as a distinct failure mode (Buldyrev et al., 2010). The result instead identifies a class of recursive no-progress regimes in which local continuation remains possible while meaningful forward improvement becomes inaccessible."

**Summary:** Buldyrev 2010 now supports a structural-motivation sentence rather than the paper's own original claim. The "identifies a class" sentence no longer carries the Buldyrev citation.

---

## Fix 2 — Opening cluster semantic precision (§1)

**Before:**
> "In such systems, collapse need not begin as overt breakdown. It may instead begin when recursion remains locally coherent while genuine forward improvement becomes inaccessible (Scheffer et al., 2001; Holling, 1973; Shumailov et al., 2024)."

**After:**
> "Collapse, catastrophic shift, and resilience loss are well-established phenomena in complex systems (Scheffer et al., 2001; Holling, 1973). In such recursive systems, collapse need not begin as overt breakdown. It may instead begin when recursion remains locally coherent while genuine forward improvement becomes inaccessible (Shumailov et al., 2024)."

**Summary:** Scheffer 2001 and Holling 1973 are now on the broader "collapse in complex systems" claim. Shumailov 2024 is retained only for the recursive/model-collapse-adjacent specific claim.

---

## Fix 3 — EWS cluster tone (§1)

**Before:**
> "This distinction matters because much of the early-warning literature is organized around variance growth, autocorrelation shifts, or threshold excursions in observed channels, without first specifying the structural failure mode to which those observables are meant to correspond (Scheffer et al., 2009; Scheffer et al., 2012; Carpenter et al., 2011; Dakos et al., 2012)."

**After:**
> "This distinction matters because the established early-warning and critical slowing down literature (Scheffer et al., 2009; Scheffer et al., 2012; Carpenter et al., 2011; Dakos et al., 2012) grounds its observables in variance growth, autocorrelation shifts, and threshold excursions; the starting point here is instead a formally specified structural obstruction."

**Summary:** EWS papers now cited positively as the "established... literature." The implicit "lacks structural theory" characterization removed. The paper's distinct starting point (formally specified obstruction) is preserved.

---

## Fix 4 — Recommender citation placement (§5 Canonical public recommender benchmark)

**Before:**
> "...replayed under a deterministic item-item collaborative-filtering engine with a warm-start prefix and a held-out positive frontier (Chaney et al., 2018; Jiang et al., 2019; Mansoury et al., 2020; Fleder & Hosanagar, 2009)."

**After:**
> "Recommender systems are known to narrow accessible diversity through feedback-driven filtering (Fleder & Hosanagar, 2009). User ratings were sorted chronologically, reduced to one episode per user, and replayed under a deterministic item-item collaborative-filtering engine with a warm-start prefix and a held-out positive frontier (Chaney et al., 2018; Jiang et al., 2019; Mansoury et al., 2020)."

**Summary:** Fleder 2009 (diversity motivation) moved to a dedicated sentence preceding the technical construction sentence. Chaney, Jiang, Mansoury remain on the replay engine / feedback-loop construction sentence.

---

## Fix 5 — Markets citation precision (§7 Public market event family)

**Before:**
> "...volatility-linked stress indicators such as the VIX (Whaley, 2009), heterogeneous liquidity structure..."
> "...centered on the February 2018 Volmageddon dislocation (Augustin et al., 2021; ESRB Advisory Scientific Committee, 2019)..."

**After:**
> "...volatility-linked stress indicators such as the VIX (Whaley, 2009; ESRB Advisory Scientific Committee, 2019), heterogeneous liquidity structure..."
> "...centered on the February 2018 Volmageddon dislocation (Augustin et al., 2021)..."

**Summary:** ESRB 2019 (ETF systemic risk context) moved to the VIX/volatility-linked products sentence alongside Whaley 2009, where its content about ETF systemic risk is semantically appropriate. Augustin 2021 now stands alone as the Volmageddon post-mortem citation.

---

## Fix 6 — Hales / Lean parenthetical split (§Materials and Methods)

**Before:**
> "The paper combines a Lean-verified formal obstruction (de Moura & Ullrich, 2021; The mathlib Community, 2020; Hales et al., 2017; Avigad & Harrison, 2014; Avigad, 2024) with empirical witness construction..."

**After:**
> "The paper combines a Lean-verified formal obstruction (de Moura & Ullrich, 2021; The mathlib Community, 2020) — an approach anchored by prior formally verified proofs in mathematics (Hales et al., 2017; Avigad & Harrison, 2014; Avigad, 2024) — with empirical witness construction..."

**Summary:** Lean-specific cluster (de Moura & Ullrich 2021, mathlib 2020) separated from formal-verification-epistemics cluster (Hales 2017, Avigad & Harrison 2014, Avigad 2024). Hales 2017 no longer implies Lean usage; it is cited for "formally verified proofs in mathematics" broadly.

---

## Fix 7 — Table X placeholder → Table 1

**7a — Legend:**
- `**Table X. Comparator calibration...` → `**Table 1. Comparator calibration...`

**7b — Body cross-reference added in §4 (Cross-domain evidence):**
- Added to end of paragraph: "The combined comparator calibration summary across both flagship benchmarks is reported in Table 1."

---

## Fix 8 — Figure [robustness] → Supplementary Figure S1

**Before:** `**Figure \[robustness\]. Fast-family segmentation...`
**After:** `**Supplementary Figure S1. Fast-family segmentation...`

The legend is retained in the Figure and Table Legends section as a supplementary figure legend. No image path added; no main-text Figure 4 created.

---

## Unresolved issues

| Issue | Status |
|---|---|
| EWS 4-citation cluster density (Scheffer 2009/2012, Carpenter 2011, Dakos 2012) | Not reduced — prompt Fix 3 required retaining all four as the established baseline set; reducing the count was not part of Fix 3's scope |
| Recommender 4-citation cluster density now 3-citation | Resolved by Fix 4 (Fleder removed from that cluster) |
| Supplementary Figure S1 has no image path | Known; noted as supplementary material without a current asset path |
| Table 1 has no corresponding data table in the manuscript body | The legend and cross-reference are present; the actual formatted table is in the Supplementary Materials or to be added at final typesetting |

---

## Citation correctness after fixes

All 29 references remain in the References section. All 29 are cited in the body. No citations were added or removed.
