# Abstract variants — Absorbing Shadow Classes in Conjunctive Label Rules

Two abstracts are maintained for this manuscript. The **full abstract** (~470 words)
lives in `paper_shadow_classes.md` and is used for the arXiv PDF and for venues with
no abstract-length cap. The **short abstract** (≤250 words) below is for TORS and any
venue that caps the abstract at 250 words. The arXiv metadata field (~1920-char cap)
uses the short abstract; see `arxiv_metadata.md`.

Both must preserve the Part-D no-drift invariants: the Study-1 signal was contamination
(**reversal**, 2.01 → −0.64, never attenuation); d = +4.20 appears only alongside what it
detects (frontier depletion); δ's purified effect **and** coefficient are both in the
hypothesised direction (two indicators failed, one held — never "all three failed"); the
marginal tally is one inverted / one null / one consistent.

---

## Short abstract (≤250 words — TORS / capped venues)

*(250 words)*

Benchmarks for early-warning detection in recursive systems label each unit as a degradation case or a control. A natural label — declaring degradation only when a run condition co-occurs with an eligibility condition — can silently corrupt the control class. In a MovieLens-25M recommender replay the eligibility clause, a minimum-frontier floor, is absorbing: once a unit's frontier falls below the floor it can never be labeled degraded, so units that fail continuously are filed as controls. In the landmark population 69.2% of controls are frontier-starved and no events are, making the most natural early-warning statistic anti-informative. A pre-registered learnability gate caught this before any detector result existed, and we prove the contamination is structural: because starvation is absorbing, no landmark choice rescues it. Treating starvation as a competing terminal event, we re-run the evaluation on the purified population, where the gate passes (TPR 0.561 against chance 0.05). The registered slate-structure composite fails every criterion, losing to the best miss-based baseline at every budget (ΔTPR = −0.472). Purification reverses or nulls the contaminated effects — churn inverts (+2.01 → −0.64), occupancy collapses to null (+0.05) — while coverage keeps a moderate effect in the hypothesised direction (−0.68); on marginal effects one indicator is inverted, one null, one consistent. The composite separates starved from clean controls at d = +4.20: it read frontier depletion, not early warning. The contribution is a detection protocol — a learnability gate plus a shadow-class census — that caught two distinct failures before either produced a result.
