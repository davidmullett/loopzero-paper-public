# Figure Order Fix Change Log

**Manuscript:** `manuscript/paper_v1_main_citation_working.md`
**Fix date:** 2026-04-28
**Prompt:** `citation_map/prompts_fix_figure_ordering.txt`

---

## Final figure placement

| Figure | Section | Image path | Line |
|---|---|---|---|
| Figure 1 | Comparator calibration on the canonical markets benchmark | `assets/fig1_markets_canonical_comparator_band.png` | 91 |
| Figure 2 | Canonical public recommender benchmark | `assets/fig2_recommender_canonical_bridge_and_comparators.png` | 67 |
| Figure 3 | Recommender robustness under adjacent horizon sensitivity | `assets/fig3_recommender_horizon_sensitivity.png` | 75 |

---

## Changes made

### Figure 1 (markets comparator calibration)
- **Was:** `![][image3]` in "Comparator calibration on the canonical markets benchmark" section, labeled **Figure 3**
- **Now:** `![Figure 1](assets/fig1_markets_canonical_comparator_band.png)` in same section, labeled **Figure 1**
- Caption updated: `\=` escape removed → `=`; `0.03, 0.07` → `[0.03, 0.07]` (restoring brackets); title changed from "Figure 3" to "Figure 1"
- Section location: unchanged (was already in the correct section)

### Figure 2 (recommender bridge summary)
- **Was:** `![][image2]` in "Recommender robustness under adjacent horizon sensitivity" section, labeled **Figure 2**
- **Now:** `![Figure 2](assets/fig2_recommender_canonical_bridge_and_comparators.png)` in "Canonical public recommender benchmark" section, labeled **Figure 2**
- Moved from §6 to §5
- Caption: `\=` escape removed → `=`; figure number label unchanged (was already Figure 2)
- Content of caption unchanged

### Figure 3 (recommender horizon sensitivity)
- **Was:** `![][image1]` in "Canonical public recommender benchmark" section, labeled **Figure 1**
- **Now:** `![Figure 3](assets/fig3_recommender_horizon_sensitivity.png)` in "Recommender robustness under adjacent horizon sensitivity" section, labeled **Figure 3**
- Moved from §5 to §6
- Caption title updated: "Recommender robustness by horizon" → "Recommender robustness by adjacent horizon sensitivity" (per canonical caption)
- Figure number label changed: Figure 1 → Figure 3

---

## Base64 image references remaining

None. No `[image1]: <data:...>` or similar reference definitions were found in the manuscript.

---

## Remaining image placeholder status

No `![][imageN]` placeholders remain. All three figures now use explicit local asset paths:
- `![Figure 1](assets/fig1_markets_canonical_comparator_band.png)` ✓
- `![Figure 2](assets/fig2_recommender_canonical_bridge_and_comparators.png)` ✓
- `![Figure 3](assets/fig3_recommender_horizon_sensitivity.png)` ✓

---

## Note on Figure [robustness]

Line 127 contains `**Figure \[robustness\]. Fast-family segmentation and band sensitivity on the canonical markets benchmark.**` in the Figure and Table Legends section. This figure has no assigned number and no image placeholder; it was not part of the canonical figure map in the prompt and was not modified.
