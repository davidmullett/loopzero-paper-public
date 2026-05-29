# A1 Pre-Registration — Loopzero quantile detector

**Provenance.** This specification was committed on 2026-05-18, before the A1 quantile detector was executed on benchmark data: the detector code landed the same day explicitly marked "data execution deferred," and the A1 operating points were computed afterward (markets 2026-05-18, recommender 2026-05-19). The firing rule below was fixed before its results existed; the git history records this ordering.

## 1. Reference-window definition

### Markets
Decision: control-unit late-window rows only.

Reference quantiles for the markets benchmark are computed exclusively from rows belonging to control units (fit by `compute_reference_quantiles` in `analysis/14_build_a1_quantile_detector_v1.py`, control-unit rows only), within the late 30-minute window of each control unit's canonical span. Event units are not used for reference quantile computation under any circumstance. This excludes any peeking risk: the detector's threshold is determined by what (G, p, δ) look like during non-event periods only, and the event-window evaluation is therefore an out-of-distribution test of the firing rule. We use the 30-minute late window, not the 60-minute alternative supported by `analysis/13bb_build_witness_direction_table_v3.py`, because the 30-minute slice is the convention already used in the manuscript's existing witness-direction table for the markets canonical comparator analysis, preserving consistency across A1 and existing Table 1 rows.

### Recommender
Decision: control units only, full per-step rows within their canonical h=50 pre-collapse panel.

Reference quantiles for the recommender benchmark are computed exclusively from per-step rows of control units within their canonical 50-step pre-collapse panel. The recommender benchmark's unit of analysis is the user trajectory (the per-user-trajectory unit), and the canonical 50-step pre-collapse panel is the windowing convention used throughout the manuscript. EXPLICIT REJECTION: reference quantiles are NOT computed from pre-collapse rows of event units, even though those rows are available in the same telemetry panel. Using event-unit pre-collapse rows for reference quantile computation would make the detector self-referential: the rule would calibrate against the same trajectories whose alarms it then evaluates. Control units only preserves the same out-of-distribution-test property as the markets reference selection.

## 2. Firing rule

Detector fires at window t when:
  (G_t > q_G) AND (p_t > q_p) AND (δ_t < q_δ)
for k consecutive windows, where (q_G, q_p, q_δ) are (95th, 95th, 5th) percentiles of (G, p, δ) on the reference window defined in §1.

A canonical unit is "alarmed" iff any k-consecutive fire occurs within its window.

## 3. Configuration grid

Primary: (q=95, k=3) — bolded in Table 1.
Sensitivity: q ∈ {90, 95, 99} × k ∈ {1, 3, 5} = 9 cells per benchmark.

## 4. Pass/fail accounting

For each (benchmark, q, k):
- n_event_units, n_control_units
- n_event_alarmed, n_control_alarmed
- event_alarm_rate = n_event_alarmed / n_event_units
- control_fp = n_control_alarmed / n_control_units
- accepted_under_locked_contract = (0.03 ≤ control_fp ≤ 0.07)

Multi-event handling: a unit containing multiple events counts as one alarmed unit if any fire occurs.
NaN handling: rows with any NaN in (G, p, δ) are excluded from both reference quantile computation and firing evaluation.