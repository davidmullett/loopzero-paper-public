# Main Text Citation Plan

**Paper:** A theorem-grounded warning criterion for collapse in recursive systems
**Plan date:** 2026-04-28 (updated after manual metadata verification)
**Source:** `final_main_cites.csv` — compressed_priority = MUST_MAIN
**Total main-text citations:** 29
**Verify-manually queue:** empty — all metadata confirmed

---

## Notes on this plan

- Citations are listed in recommended insertion order within each section.
- All entries previously marked [verify] have been resolved. No outstanding verification flags remain in the main-text set.
- The six LIKELY_MAIN citations (Dakos 2008, Lenton 2008, Albert 2000, Folke 2004, Sun 2019, Jadidinejad 2021) are not listed here but should be considered for insertion if word-count or reviewer pressure demands expanded coverage in their respective sections. See `citation_compression_report.md`.
- Section names below are conventional; adjust to match actual manuscript headings.

---

## §1 Introduction (6 citations)

**Claim cluster: the collapse-warning problem and its existing landscape**

| # | Citation | DOI / Source | Insertion point |
|---|---|---|---|
| 1 | Scheffer, Carpenter, et al. (2009) *Nature* | 10.1038/nature08227 | First paragraph: introduce variance and lag-1 autocorrelation (AC1) as the established generic baselines the paper is evaluated against |
| 2 | Scheffer, Carpenter, et al. (2012) *Science* | 10.1126/science.1225244 | Alongside Scheffer 2009 when naming the critical slowing down (CSD) paradigm |
| 3 | Carpenter et al. (2011) *Science* | 10.1126/science.1203672 | Alongside Scheffer 2009/2012 to establish baselines as empirically validated (not just theoretical) |
| 4 | Scheffer, Carpenter, et al. (2001) *Nature* | 10.1038/35098000 | When introducing catastrophic shifts, hysteresis, and loss of viable state as the failure mode the criterion detects |
| 5 | Holling (1973) *Ann Rev Ecol Syst* | 10.1146/annurev.es.04.110173.000245 | First use of "resilience" and "viable state space" in the framing — cite as the origin of both terms |
| 6 | Shumailov et al. (2024) *Nature* | 10.1038/s41586-024-07566-y | When positioning the paper's contribution relative to existing work; this is the nearest prior result — not citing it is conspicuous |

**Insertion guidance:** The first paragraph should establish the problem (recursive systems fail; prior warning methods are unreliable under matched false-positive constraints). Citations 1–3 anchor the EWS baseline family. Citation 4 introduces the catastrophic-shift vocabulary. Citation 5 grounds the theoretical language. Citation 6 marks the nearest prior contribution and signals awareness of the model-collapse literature.

---

## §2 Theory (3 citations)

**Claim cluster: recursive collapse as a first-order structural phenomenon**

| # | Citation | DOI / Source | Insertion point |
|---|---|---|---|
| 7 | Buldyrev et al. (2010) *Nature* | 10.1038/nature08932 | When introducing the recursive / cascading no-progress failure mode; iterative mutual failure is the network-science analogue of the paper's recursive obstruction |
| 8 | Gao, Barzel & Barabási (2016) *Nature* | 10.1038/nature16948 | When justifying that a scalar criterion (G, p, δ) can characterize collapse proximity in a high-dimensional system; the universal resilience function is the theoretical license |
| 9 | Walker et al. (2004) *Ecology and Society* | 10.5751/ES-00650-090205 | First use of "viable state space," "latitude," or "precariousness" — cite as the primary source for this vocabulary |

**Insertion guidance:** The theory section should situate the Lean-verified obstruction within the network-collapse and resilience literatures. Buldyrev 2010 anchors the recursive failure mode. Gao 2016 licenses the scalar-criterion design choice. Walker 2004 is the vocabulary source for the stability-landscape geometry. These three citations serve distinct roles; none is redundant.

---

## §3 Methods (5 citations)

**Claim cluster: benchmarking design and false-positive control**

| # | Citation | DOI / Source | Insertion point |
|---|---|---|---|
| 10 | Dakos et al. (2012) *PLOS ONE* | 10.1371/journal.pone.0041010 | When describing the comparator EWS metrics; this is the toolbox paper that defines the computational standard |
| 11 | Boettiger & Hastings (2012a) *Proc Roy Soc B* | 10.1098/rspb.2012.2085 | When justifying why generic EWS baselines have inflated false-positive rates; this is the prosecutor's fallacy paper |
| 12 | Boettiger & Hastings (2012b) *J Royal Society Interface* | 10.1098/rsif.2012.0125 | When describing the matched false-positive (locked FP rate) benchmarking design; this paper introduces the EWS-specific ROC / power analysis framework |
| 13 | Hanley & McNeil (1982) *Radiology* | 10.1148/radiology.143.1.7063747 | When introducing AUC comparison or ROC curve methodology; foundational citation; conspicuous if absent |
| 14 | Diks, Hommes & Wang (2019) *PLOS ONE* | 10.1371/journal.pone.0211072 | When explaining why a matched-FP design is necessary; this paper proves that entire classes of systems produce rising variance/AC1 without approaching transition, making unadjusted comparisons misleading |

**Insertion guidance:** Citations 11 and 12 are distinct papers with distinct DOIs (rspb.2012.2085 vs. rsif.2012.0125). Citation 12 was published in J. Royal Society Interface, not Proc Roy Soc B; cite the verified DOI 10.1098/rsif.2012.0125. Together they form the complete false-positive methodology foundation. Citation 13 is the general ROC methodology anchor; cite it at first AUC mention. Citations 11, 12, and 14 together make the complete argument for why the matched-FP design is the correct experimental frame.

---

## §4 Recommender Systems (4 citations)

**Claim cluster: MovieLens as a recursive feedback test bed**

| # | Citation | DOI / Source | Insertion point |
|---|---|---|---|
| 15 | Fleder & Hosanagar (2009) *Management Science* | 10.1287/mnsc.1080.0974 | When motivating the diversity-degradation hypothesis; establishes that recommender systems narrow sales diversity over time |
| 16 | Chaney, Stewart & Engelhardt (2018) *ACM RecSys* | 10.1145/3240323.3240370 | When justifying the use of MovieLens as the experimental dataset; this paper explicitly identifies MovieLens as a confounded dataset generated under collaborative filtering |
| 17 | Jiang et al. (2019) *AIES/ACM* | 10.1145/3306618.3314288 | When framing recursive collapse as structural degeneracy rather than incidental drift; degenerate fixed-point attractor is the theoretical object the criterion detects before it is reached |
| 18 | Mansoury et al. (2020) *CIKM* | 10.1145/3340531.3412152 | When describing the round-by-round degradation trajectory in MovieLens; this is the direct empirical baseline the paper's results are positioned against |

**Insertion guidance:** The recommender section's citation load is deliberately lean. Citation 16 is the single most important citation for dataset justification. Citations 17 and 18 bracket the theoretical and empirical baselines. Citation 15 provides historical motivation for the diversity metric.

---

## §5 Financial Markets (6 citations)

**Claim cluster: Volmageddon and March 2020 circuit breakers as empirical test cases**

| # | Citation | DOI / Source | Insertion point |
|---|---|---|---|
| 19 | Brunnermeier & Pedersen (2009) *Rev Financial Studies* | 10.1093/rfs/hhn098 | When describing the liquidity-spiral mechanism underlying both Volmageddon and the March 2020 events; this is the theoretical backbone |
| 20 | Augustin, Chen & Van den Bergen (2021) *Financial Analysts Journal* | 10.1080/0015198x.2021.1913040 | When introducing Volmageddon as a labeled event; this is the only peer-reviewed post-mortem |
| 21 | Whaley (2009) *Journal of Portfolio Management* | 10.3905/jpm.2009.35.3.098 | First use of VIX as a market-stress indicator; required methodological citation when VIX features appear in the experimental setup |
| 22 | NYSE Market-Wide Circuit Breaker Working Group (2020) *institutional report* | URL: nyse.com/publicdocs/nyse/markets/nyse/Report_of_the_Market-Wide_Circuit_Breaker_Working_Group.pdf | When defining the four March 2020 circuit-breaker trigger dates as collapse labels; this is the official post-event documentation |
| 23 | CFTC and SEC Staff (2010) *institutional report* | URL: sec.gov/news/studies/2010/marketevents-report.pdf | When introducing the 2010 Flash Crash as a labeled event; official regulatory documentation |
| 24 | ESRB Advisory Scientific Committee (2019) *institutional report* | 10.2849/45983 | When framing Volmageddon as a systemic event (not idiosyncratic); regulatory authority for VIX ETP systemic risk |

**Insertion guidance:** Citations 22 and 23 are institutional reports, not peer-reviewed, but are the authoritative primary sources for event labels. Citations 19 and 24 together frame the endogenous-amplification mechanism and its regulatory recognition. Citation 20 DOI is now confirmed as 10.1080/0015198x.2021.1913040. Citation 21 is mandatory when VIX appears as a variable.

---

## §6 Formal Verification (5 citations)

**Claim cluster: the Lean-verified obstruction as a meaningful scientific artifact**

| # | Citation | DOI / Source | Insertion point |
|---|---|---|---|
| 25 | de Moura & Ullrich (2021) *CADE-28* | 10.1007/978-3-030-79876-5_37 | When naming Lean 4 as the proof assistant used; this citation establishes the specific kernel that constitutes the trust anchor |
| 26 | The mathlib Community (2020) *CPP* | 10.1145/3372885.3373824 | Whenever `import Mathlib` appears in the Lean code; required citation for any use of the mathlib library |
| 27 | Avigad & Harrison (2014) *Comm ACM* | 10.1145/2591012 | When justifying why a Lean-verified result is epistemically superior to an informally refereed proof; bridges the gap for Science-level reviewers unfamiliar with proof assistants |
| 28 | Avigad (2024) *Bull AMS* | 10.1090/bull/1832 | Alongside Avigad & Harrison 2014 for the most current survey of the formalization landscape; this citation signals that formalization is mainstream, not niche |
| 29 | Hales et al. (2017) *Forum of Mathematics, Pi* | 10.1017/fmp.2017.1 | When citing the canonical precedent for a formally verified proof accepted in a flagship mathematics journal; the Kepler Conjecture proof is the gold standard |

**Insertion guidance:** Citations 25 and 26 are mechanical requirements for any Lean 4 artifact. Citations 27 and 28 serve the same reviewer-trust function at different time horizons — cite both. Citation 29 is the single most compelling precedent: a formally verified proof published in a top mathematics journal.

---

## DOI corrections applied in this revision

| Entry | Old DOI (seed) | Corrected DOI (verified) | Venue correction |
|---|---|---|---|
| Augustin, Chen & Van den Bergen (2021) | 10.1080/0015198X.2021.1908937 | 10.1080/0015198x.2021.1913040 | No venue change |
| Boettiger & Hastings (2012b) | 10.1098/rspb.2012.2079 | 10.1098/rsif.2012.0125 | Journal of the Royal Society Interface (not Proc Roy Soc B) |

---

*Total MUST_MAIN citations: 29. All seven required coverage areas satisfied. Verify-manually queue: empty. See `final_supplement_cites.csv` and `supplement_citation_plan.md` for the supplement entries.*
