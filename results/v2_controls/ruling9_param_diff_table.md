# RULING 9 — Parameter diff table: Study 1 (7bvgz) vs Study 2 (wka72) vs code-at-C*

Read-only audit. Sources: 7bvgz = OSF Study 1 pre-registration (carried-over values as
re-declared in wka72 §1/§4); wka72 = `STUDY2-prereg-frozen.pdf` (sha256 `2374e370…`, verified);
code-at-C* = the v2_controls tree + frozen contract anchored under `CODE_ANCHOR.sha256`
(rollup `096355fe…`) and `contract_freeze.json` (`2e256b25…`). "carried" = wka72 §1/§4 declares
the value transferred intact from Study 1. Where 7bvgz ≠ wka72, the "follows" column states
which registration the code matches.

| # | param | 7bvgz | wka72 | code-at-C* (file:line = value) | conformance |
|---|-------|-------|-------|--------------------------------|-------------|
| 1 | t_split (landmark) | 20 | 20 | config.py:22 = 20 | CONFORMS |
| 2 | indicator window | 20 | 20 | config.py:23 = 20 | CONFORMS |
| 3 | slate size K / top_k | 10 | 10 | config.py:24 = 10; contract top_k=10 | CONFORMS |
| 4 | slate slots N_SLOTS | 200 | 200 | config.py:25 = 200 | CONFORMS |
| 5 | degradation streak (consec misses) | 8 | 8 | contract collapse_streak_len=8 (assert config.py:71) | CONFORMS |
| 6 | frontier floor | 10 | 10 | producer.py:57 FRONTIER_FLOOR=10; contract (config.py:72) | CONFORMS |
| 7 | max horizon | 50 | 50 | contract max_horizon_steps=50 (assert config.py:70) | CONFORMS |
| 8 | min_warning_runway | 15 | 15 (carried) | contract min_warning_runway=15 (inherited via frozen panel labels) | CONFORMS |
| 9 | positive_rating_threshold | 4.0 | 4.0 (carried) | contract=4.0 (covariates.py warm-start) | CONFORMS |
| 10 | warm_start_ratings | 30 | 30 (carried) | contract=30 (covariates.py) | CONFORMS |
| 11 | ΔTPR floor (Δ) | 0.05 | 0.05 (unchangeable) | config.py:39 GUARD_DELTA_TPR / decision.py:35 | CONFORMS |
| 12 | incremental AUC threshold | 0.02 | 0.02 (unchangeable) | config.py:40 GUARD_INCREMENTAL_AUC / decision.py:36 | CONFORMS |
| 13 | bootstrap seed | 201 | 201 | config.py:29 = 201 | CONFORMS |
| 14 | bootstrap iterations | 10,000 | 10,000 | config.py:28 = 10_000 | CONFORMS |
| 15 | fold-split rule | seedless SHA-256, cal iff last hex ∈{0..7} | same (per-user unchanged) | population.py:16-18 | CONFORMS |
| 16 | composite S | z(G)+z(p)−z(δ) | same | indicators.py:73-75 | CONFORMS |
| 17 | indicator G (churn) | mean Jaccard dissimilarity t..t+1 | same | indicators.py:12-20 | CONFORMS |
| 18 | indicator p (occupancy) | Herfindahl Σ s_i² over 200 slots | same | indicators.py:31-37 | CONFORMS |
| 19 | indicator δ (coverage) | \|∪R_t\| / 200 | same | indicators.py:23-28 | CONFORMS |
| 20 | matched-count formula | round(b·n_eval_controls) | same | sweep.py:11-13 | CONFORMS |
| 21 | tie-break | ascending userId | same | sweep.py:16 lexsort((uid,-score)) | CONFORMS |
| 22 | best-baseline set | {six families ∪ PC1}, each family maxed over structural grid (I-12) | same | producer.py:107-118 | CONFORMS |
| 23 | PC1 definition | early miss rate over 1..20, increasing | same | producer.py:104; decision.py:53-55 | CONFORMS |
| 24 | PC1 gate | TPR@b=0.05 − 0.05 > 0, BCa CI excl 0 | same | decision.py:53-55 (I-7) | CONFORMS |
| 25 | PC2 (liveness) | δ distinct ≥ 20 AND IQR > 0 | same | producer.py:150-153 | CONFORMS |
| 26 | power gate | ≥ 200 eval events | same | config.py:41 = 200 | CONFORMS |
| 27 | viability gate | N(CLEAN,total)≥1000 ∧ N(CLEAN,fold)≥450 | same | census gate (summary PASS) | CONFORMS |
| 28 | covariate set | log(warm_start_positive_count) + pop_affinity LOUO/162,541; headroom EXCLUDED | same (I-1/I-2) | covariates.py | CONFORMS |
| 29 | criterion 1 | ΔTPR≥0.05@0.05, CI excl 0 | same | decision.py:47 bar_met | CONFORMS |
| 30 | criterion 3 | signs bG>0,bP>0,bD<0 + incrAUC≥0.02 | same | decision.py:57-63 | CONFORMS |
| 31 | criterion 4 | shuffled-TS ∧ popularity FAIL crit-1 | same (dispositive) | decision.py dispositive = popularity + shuffled-TS | CONFORMS |
| 32 | engine seeds | random101, shuffledTS102, MF103, seq104 (+{0..4}) | same | config.py:30-35 CONTROL_SEEDS | CONFORMS |
| 33 | engine hash | 56c1cff2… | 56c1cff2… | contract engine_hash 56c1cff225d60c09 | CONFORMS |
| 34 | slate-panel provenance | ea972e2e… (content) | ea972e2e… | live decompressed = ea972e2e… (D-16/D-17 RESOLVED) | CONFORMS |
| — | **budget grid** | **{0.01,0.02,0.05,0.10}** | **{0.02,0.05,0.10,0.20}** (0.01 removed, 0.20 added) | config.py:26 / decision.py:33 = **{0.01,0.02,0.05,0.10}** → **follows 7bvgz** | **DIVERGES (D-15)** |
| — | **criterion-2 budget set** | ≥3/4 of {0.01,0.02,0.05,0.10} | ≥3/4 of {0.02,0.05,0.10,0.20} | decision.py:115 over Study-1 grid → **follows 7bvgz** | **DIVERGES (D-15)** |
| — | **population / control class** | DEGRADED vs all non-degraded (no purification) | DEGRADED vs CLEAN (competing-risk purified; starvers excluded) | producer.py:84 admits ALL controls; z-source (producer.py:98) & matched-count denominator (producer.py:123) over all controls, not CLEAN → **follows NEITHER** | **DIVERGES (D-7)** |

## Findings
- **34 audited parameters conform** (rows 1–34), including the panel-provenance row now
  RESOLVED (D-16/D-17: the registered `ea972e2e` is the decompressed-content hash and matches).
- **Where 7bvgz ≠ wka72** there are exactly two axes: the **budget grid** and the
  **population/control definition**. On both, the code does **NOT** follow wka72:
  the budget grid follows 7bvgz (**D-15**); the population admits all controls rather than the
  wka72-purified CLEAN class (**D-7**, with its z-parameter-source and matched-count-denominator
  consequences).
- **No divergence found that is not already logged as D-15 or D-7.** (D-16 panel-hash resolved;
  D-18/D-19/D-20 are provenance/uncommitted-generator findings, not parameter divergences.)
- All divergences are remediated only at C** (deferred); this table changes nothing.

decision.RATIFIED = False.
