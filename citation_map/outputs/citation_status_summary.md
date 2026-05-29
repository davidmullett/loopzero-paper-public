# Citation Status Summary

**Paper:** A theorem-grounded warning criterion for collapse in recursive systems
**Summary date:** 2026-04-28
**Status:** Ready for manuscript insertion

---

## Counts

| Category | Count | File |
|---|---|---|
| Total candidates evaluated | 85 | `candidates_triaged.csv` |
| Final main-text citations | 29 | `final_main_cites.csv` |
| Supplement citations | 16 | `final_supplement_cites.csv` |
| Future-paper citations (AI-agentic) | 9 | `final_future_cites.csv` |
| Demoted to LIKELY_MAIN (main-text candidates) | 6 | `citation_compression_report.md` |
| Removed (cross-bucket duplicates) | 3 | `candidates_triaged.csv` (triage_priority = REMOVE) |
| verify_manually remaining | 0 | — |

---

## Coverage verification

All seven required citation areas are covered by the 29-citation main-text set:

| Area | Covered by | Status |
|---|---|---|
| EWS / critical transitions | Scheffer 2009, 2012; Carpenter 2011; Dakos 2012; Boettiger 2012a | ✓ |
| Collapse / cascading failure | Scheffer 2001; Holling 1973; Buldyrev 2010; Gao 2016; Walker 2004 | ✓ |
| Recommender feedback loops | Fleder 2009; Chaney 2018; Jiang 2019; Mansoury 2020 | ✓ |
| Markets / Volmageddon / circuit breakers | Brunnermeier 2009; Augustin 2021; Whaley 2009; NYSE MWCB 2020; SEC/CFTC 2010; ESRB 2019 | ✓ |
| Lean / formal verification | de Moura & Ullrich 2021; mathlib 2020; Avigad & Harrison 2014; Avigad 2024; Hales 2017 | ✓ |
| False-positive / statistical evaluation | Boettiger 2012a; Boettiger 2012b; Hanley 1982; Diks 2019 | ✓ |
| Model collapse / recursive generative systems | Shumailov 2024 | ✓ |

---

## DOI corrections applied

| Entry | Seed DOI | Verified DOI | Venue correction |
|---|---|---|---|
| Augustin, Chen & Van den Bergen (2021) | 10.1080/0015198X.2021.1908937 | **10.1080/0015198x.2021.1913040** | None |
| Boettiger & Hastings (2012b) "Quantifying limits…" | 10.1098/rspb.2012.2079 | **10.1098/rsif.2012.0125** | **J. Royal Society Interface** (not Proc Roy Soc B) |

---

## Institutional report entries in main text (not peer-reviewed)

These three entries in `final_main_cites.csv` are institutional reports. They should be cited as institutional reports, not as journal articles.

| Entry | metadata_status | Citation format |
|---|---|---|
| NYSE MWCB Working Group (2020) | institutional_report | NYSE Report of the Market-Wide Circuit Breaker Working Group, 2020 |
| CFTC and SEC Staff (2010) | institutional_report | SEC/CFTC, Findings Regarding the Market Events of May 6, 2010, 2010 |
| ESRB Advisory Scientific Committee (2019) | institutional_report | ESRB Advisory Scientific Committee Report No. 9, 2019 |

---

## Supplement note

The 5 primary supplement entries (from the compressed MUST set) plus 11 optional supplement entries are listed in `final_supplement_cites.csv` and documented in `supplement_citation_plan.md`. Of these:
- **Danielsson 2012** should not be cited until peer-reviewed publication status is confirmed.
- **Schnabel 2016** has no formal DOI; use arXiv 1602.05352 as the stable identifier.
- All other supplement entries have confirmed metadata.

---

## Future-paper reserve

9 AI-agentic citations are held in `final_future_cites.csv` for the LLM/agentic extension paper. Recommended subset for a V1 future-work paragraph (2–3 citations): Amodei et al. (2016), Shinn et al. / Reflexion (2023), Dalrymple et al. (2024).

---

## Readiness assessment

**Citation layer is ready for manuscript insertion.**

- All 29 main-text citations have confirmed metadata.
- No verify_manually flags remain outstanding in `final_main_cites.csv`.
- All seven required coverage areas are satisfied.
- Institutional reports are clearly labeled.
- DOI corrections for Augustin 2021 and Boettiger 2012b are applied.

Next step: insert citations into manuscript draft following `main_text_citation_plan.md`.
