# References Section Change Log

**Manuscript:** `manuscript/paper_v1_main_citation_working.md`
**Sources:** `citation_map/outputs/final_main_cites.csv`, `citation_map/outputs/final_main_cites.bib`
**Added date:** 2026-04-28
**Prompt:** `citation_map/prompts_add_references_section.txt`

---

## Summary

| Item | Value |
|---|---|
| References added | 29 |
| Entries with DOI | 26 |
| Entries without DOI (arXiv only) | 1 |
| Entries without DOI (URL only) | 3 |
| Institutional reports | 3 |
| Page numbers included | 0 (omitted — not in source data) |

---

## Entries without DOI

| Reference | Identifier used | Reason |
|---|---|---|
| Avigad (2024) — Mathematics and the formal turn | arXiv:2311.00007 | No DOI field in `final_main_cites.bib`; arXiv eprint present |
| CFTC and SEC Staff (2010) | URL: sec.gov/news/studies/2010/marketevents-report.pdf | Institutional report; no DOI assigned |
| NYSE Market-Wide Circuit Breaker Working Group (2020) | URL: nyse.com/publicdocs/... | Institutional report; no DOI assigned |
| ESRB Advisory Scientific Committee (2019) | URL: esrb.europa.eu/pub/pdf/asc/... | Institutional report; no DOI assigned |

---

## Institutional reports included

Three entries were formatted as institutional reports (not journal articles), consistent with `@techreport` entries in the bib file:

1. **CFTC and SEC Staff (2010).** Findings Regarding the Market Events of May 6, 2010. Report, SEC / CFTC.
2. **ESRB Advisory Scientific Committee (2019).** Can ETFs Contribute to Systemic Risk? Report, ESRB.
3. **NYSE Market-Wide Circuit Breaker Working Group (2020).** Report of the Market-Wide Circuit Breaker (MWCB) Working Group. Report, NYSE / SEC.

---

## Boettiger 2012a/b disambiguation

Two papers share the same first-author-year (Boettiger & Hastings, 2012). These are disambiguated as `2012a` and `2012b` in both the inline citations inserted in Task 3 and in the References section:

- **Boettiger & Hastings (2012a):** Early warning signals and the prosecutor's fallacy. *Proc. Royal Society B*. DOI: 10.1098/rspb.2012.2085 — BibTeX key `Boettiger2012`
- **Boettiger & Hastings (2012b):** Quantifying limits to detection of early warning for critical transitions. *Journal of the Royal Society Interface*. DOI: 10.1098/rsif.2012.0125 — BibTeX key `Boettiger20122`

Recommended: rename BibTeX key `Boettiger20122` → `Boettiger2012b` before final typesetting to match the `a/b` disambiguation convention used in the manuscript.

---

## Metadata limitations

- **Page numbers:** Omitted throughout. The `final_main_cites.csv` source contains no page number fields. Per the prompt rule ("If page numbers are missing, omit them rather than inventing them"), no page numbers were added.
- **Volume/issue numbers:** Omitted. Not present in source CSV or bib file for any entry. Same rule applies.
- **Long author lists:** For entries with more than 6 authors (Carpenter 2011, Dakos 2012, Scheffer 2009, Scheffer 2012, Hales 2017), the first 6 authors are listed followed by "et al." consistent with the bib file's own use of "et al." in the Hales entry.
- **Whaley (2009):** Included in the References section per the prompt ("Preserve all 29 final main citations"), even though this citation was not inserted in the manuscript body (see `citation_insertion_change_log.md` for rationale).

---

## Reference section placement

Appended after the `## Figure and Table Legends` section, separated by a horizontal rule (`---`). Heading used: `## References` (exact per prompt).
