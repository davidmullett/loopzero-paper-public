"""Synthetic-fixture tests for the A1 pre-registered quantile detector.

The detector script (analysis/14_build_a1_quantile_detector_v1.py) is
data-ready: its loaders consume the real markets per-row packets and the
recsys per-step telemetry panel. Those raw inputs are not redistributed in
the public branch (see docs/REPRODUCTION.md §1). These tests exercise the
detector engine with synthetic panels that match the documented input
contract, plus a data-absence test that the loaders raise a clean
FileNotFoundError when their sources are missing.
"""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_ANALYSIS_DIR = _ROOT / "analysis"
if str(_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_DIR))

a1 = import_module("14_build_a1_quantile_detector_v1")


# ---------------------------------------------------------------------------
# Synthetic-panel helpers
# ---------------------------------------------------------------------------
def _synthetic_panel(
    domain: str,
    *,
    n_event: int = 4,
    n_control: int = 12,
    n_rows_per_unit: int = 40,
    seed: int = 20260518,
) -> pd.DataFrame:
    """Build a per-row/per-step panel matching the detector's input contract.

    Control rows are drawn from a calm distribution (low G, low p, high
    delta); event rows are drawn from an elevated-signal distribution (high
    G, high p, low delta). Sample sizes are chosen large enough for nan-safe
    percentile estimates to be well-defined across the {90, 95, 99} grid.
    """
    rng = np.random.default_rng(seed)

    def _draw(n: int, kind: str) -> dict:
        if kind == "control":
            G = rng.uniform(0.0, 1.0, n)
            p = rng.uniform(0.0, 1.0, n)
            delta = rng.uniform(0.5, 1.0, n)
        elif kind == "event":
            G = rng.uniform(0.8, 1.2, n)
            p = rng.uniform(0.8, 1.2, n)
            delta = rng.uniform(-0.2, 0.4, n)
        else:
            raise ValueError(kind)
        return {"G": G, "p": p, "delta": delta}

    blocks: list[pd.DataFrame] = []
    base_ts = pd.Timestamp("2026-01-01T00:00:00Z")
    unit_offset = 0
    for kind, n_units in (("event", n_event), ("control", n_control)):
        for u in range(n_units):
            unit_offset += 1
            unit_id = f"unit_{kind}_{u:03d}"
            draws = _draw(n_rows_per_unit, kind)
            block = pd.DataFrame(
                {
                    "unit_id": unit_id,
                    "kind": kind,
                    "G": draws["G"],
                    "p": draws["p"],
                    "delta": draws["delta"],
                }
            )
            if domain == a1.DOMAIN_MARKETS:
                # Each unit gets its own day so units don't share timestamps.
                block["ts"] = pd.date_range(
                    base_ts + pd.Timedelta(days=unit_offset),
                    periods=n_rows_per_unit,
                    freq="1min",
                    tz="UTC",
                )
            elif domain == a1.DOMAIN_RECSYS:
                block["step"] = np.arange(n_rows_per_unit, dtype=int)
            else:
                raise ValueError(domain)
            blocks.append(block)
    return pd.concat(blocks, ignore_index=True)


# ---------------------------------------------------------------------------
# (a) Row count + primary-flag count
# ---------------------------------------------------------------------------
def test_a_grid_emits_expected_rows_with_two_primary_flags() -> None:
    panels = {
        a1.DOMAIN_MARKETS: _synthetic_panel(a1.DOMAIN_MARKETS),
        a1.DOMAIN_RECSYS: _synthetic_panel(a1.DOMAIN_RECSYS),
    }
    out = a1.build_a1_table(panels)

    n_q = len(a1.Q_GRID_PCT)
    n_k = len(a1.K_GRID)
    expected_rows = 2 * n_q * n_k  # 2 benchmarks × q-grid × k-grid
    assert len(out) == expected_rows, (
        f"expected 2 benchmarks × {n_q}q × {n_k}k = {expected_rows} rows, "
        f"got {len(out)}"
    )
    assert int(out["primary"].sum()) == 2, (
        f"expected exactly 2 primary rows (one per benchmark at q=95, k=3), "
        f"got {int(out['primary'].sum())}"
    )

    primaries = out.loc[out["primary"]]
    assert set(primaries["benchmark"]) == {
        a1.MARKETS_BENCHMARK_ID,
        a1.RECSYS_BENCHMARK_ID,
    }
    for _, r in primaries.iterrows():
        assert r["q_G_pct"] == 95
        assert r["q_p_pct"] == 95
        assert r["q_delta_pct"] == 5
        assert r["k"] == 3


# ---------------------------------------------------------------------------
# (b) Quantile monotonicity at fixed k
# ---------------------------------------------------------------------------
def test_b_quantile_monotonicity_at_fixed_k() -> None:
    panel = _synthetic_panel(a1.DOMAIN_MARKETS)
    spec = a1.DOMAIN_SPECS[a1.DOMAIN_MARKETS]

    for k in a1.K_GRID:
        threshold_rows: dict[int, dict] = {}
        for q in a1.Q_GRID_PCT:
            threshold_rows[q] = a1.run_configuration(
                spec, panel, q_G_pct=q, q_p_pct=q, q_delta_pct=100 - q, k=k
            )

        assert threshold_rows[90]["q_G"] <= threshold_rows[95]["q_G"] <= threshold_rows[99]["q_G"], (
            f"q_G non-monotone at k={k}: "
            f"{threshold_rows[90]['q_G']}, {threshold_rows[95]['q_G']}, {threshold_rows[99]['q_G']}"
        )
        assert threshold_rows[90]["q_p"] <= threshold_rows[95]["q_p"] <= threshold_rows[99]["q_p"], (
            f"q_p non-monotone at k={k}"
        )
        # q_delta uses (100 - q) as the percentile, so its value falls as q rises.
        assert threshold_rows[90]["q_delta"] >= threshold_rows[95]["q_delta"] >= threshold_rows[99]["q_delta"], (
            f"q_delta non-monotone (reversed) at k={k}: "
            f"{threshold_rows[90]['q_delta']}, {threshold_rows[95]['q_delta']}, {threshold_rows[99]['q_delta']}"
        )


# ---------------------------------------------------------------------------
# (c) Reference-window purity — no event rows in select_reference_rows output
# ---------------------------------------------------------------------------
def test_c_reference_rows_contain_no_event_rows() -> None:
    for domain in (a1.DOMAIN_MARKETS, a1.DOMAIN_RECSYS):
        panel = _synthetic_panel(domain)
        ref = a1.select_reference_rows(panel, domain)
        assert not ref.empty, f"reference set unexpectedly empty for {domain}"
        assert (ref["kind"] == "control").all(), (
            f"reference set contains non-control rows for {domain}: "
            f"{ref['kind'].value_counts().to_dict()}"
        )
        assert (ref["kind"] != "event").all(), (
            f"reference set leaked event-unit rows for {domain}"
        )


# ---------------------------------------------------------------------------
# (d) Within-unit run-length: A alarms at k=3, B does not
# ---------------------------------------------------------------------------
def test_d_within_unit_run_length() -> None:
    # qs are chosen so that the fire predicate (G > 0.5) & (p > 0.5) & (delta < 0.5)
    # collapses to a per-row indicator.
    qs = {"q_G": 0.5, "q_p": 0.5, "q_delta": 0.5}

    # Unit A: row 0 has G below threshold; rows 1..4 satisfy all three -> 4-consec fire.
    # Unit B: alternating fire / non-fire across the 5 steps -> max run length = 1.
    panel = pd.DataFrame(
        {
            "unit_id": ["A"] * 5 + ["B"] * 5,
            "kind": ["event"] * 10,
            "step": list(range(5)) * 2,
            "G": [0.1, 0.9, 0.9, 0.9, 0.9, 0.9, 0.1, 0.9, 0.1, 0.9],
            "p": [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.1, 0.9, 0.1, 0.9],
            "delta": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.9, 0.1, 0.9, 0.1],
        }
    )
    alarms = a1.apply_firing_rule(panel, qs, k=3, order_col="step")

    a_row = alarms.loc[alarms["unit_id"] == "A"].iloc[0]
    b_row = alarms.loc[alarms["unit_id"] == "B"].iloc[0]
    assert bool(a_row["unit_alarmed"]) is True, "unit A should alarm at k=3 (4 consec)"
    assert bool(b_row["unit_alarmed"]) is False, "unit B must not alarm at k=3 (max run 1)"

    # And: at k=1, unit B does alarm (any single fire suffices).
    alarms_k1 = a1.apply_firing_rule(panel, qs, k=1, order_col="step")
    b_k1 = alarms_k1.loc[alarms_k1["unit_id"] == "B"].iloc[0]
    assert bool(b_k1["unit_alarmed"]) is True, "unit B should alarm at k=1"


# ---------------------------------------------------------------------------
# (e) Data-absence handling: loaders raise a clean FileNotFoundError
# ---------------------------------------------------------------------------
def test_e_markets_loader_clean_filenotfound(tmp_path, monkeypatch) -> None:
    fake_csv = tmp_path / "no_such_markets_units.csv"
    fake_dir = tmp_path / "no_such_packet_dir"
    monkeypatch.setattr(a1, "MARKETS_CANONICAL_INPUT_CSV", fake_csv)
    monkeypatch.setattr(a1, "MARKETS_PACKET_DIR", fake_dir)

    with pytest.raises(FileNotFoundError) as excinfo:
        a1.load_markets_per_row_panel()

    msg = str(excinfo.value)
    assert "Markets canonical units CSV not found" in msg
    assert str(fake_csv) in msg
    assert "REPRODUCTION.md" in msg


def test_e_recsys_loader_clean_filenotfound(tmp_path, monkeypatch) -> None:
    fake_candidates = [tmp_path / "no_such_panel.csv.gz", tmp_path / "no_such_panel.csv"]
    monkeypatch.setattr(a1, "RECSYS_TELEMETRY_CANDIDATES", fake_candidates)

    with pytest.raises(FileNotFoundError) as excinfo:
        a1.load_recsys_per_step_panel()

    msg = str(excinfo.value)
    assert "Recsys telemetry panel not found" in msg
    assert any(str(p) in msg for p in fake_candidates)
    assert "REPRODUCTION.md" in msg
