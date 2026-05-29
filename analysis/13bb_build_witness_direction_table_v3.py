from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

import pandas as pd


ROOT = Path(".")
OUT_DIR = ROOT / "results" / "rendered" / "bridge"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "witness_direction_table_v3.csv"
OUT_MD = OUT_DIR / "witness_direction_table_v3.md"

# ---------------------------------------------------------------------
# Markets canonical branch inputs
# ---------------------------------------------------------------------
MARKETS_CANONICAL_INPUT_CSV = ROOT / "results" / "rendered" / "comparators" / "markets_comparator_input_v2.csv"
MARKETS_PACKET_DIR = (
    ROOT / "results" / "rendered" / "equity_dislocation_family" / "intraday_v2_ingredient_packet"
)
MARKETS_CANONICAL_CONFIG_ID = "cfg_001339"
MARKETS_EVENT_SLICE_IDS = {
    "volmageddon_2018_xiv",
    "covid_mwcb_2020_03_18",
}
MARKETS_LATE_WINDOWS_MIN = [30, 60]

# ---------------------------------------------------------------------
# Recommender canonical branch inputs
# ---------------------------------------------------------------------
RECSYS_TELEMETRY_CANDIDATES = [
    ROOT / "results" / "manifests" / "movielens25m_recursive_frontier_public_v1__telemetry_panel.csv.gz",
    ROOT / "results" / "manifests" / "movielens25m_recursive_frontier_public_v1__telemetry_panel.csv",
]
RECSYS_CANONICAL_HORIZON = 50

# ---------------------------------------------------------------------
# Witness column candidates
# ---------------------------------------------------------------------
G_CANDIDATES = ["G", "gain", "g"]
P_CANDIDATES = ["p_v7_ttl", "raw_p_debug", "p", "self_reinforcement", "self_reinforcement_share"]
D_CANDIDATES = ["delta", "δ", "diversity"]

UNIT_ID_CANDIDATES = ["unit_id", "episode_id", "user_episode_id", "user_id"]
KIND_CANDIDATES = ["kind", "unit_kind", "label"]
HORIZON_CANDIDATES = ["horizon", "horizon_steps", "max_steps", "benchmark_horizon", "steps"]
PRECOLLAPSE_FLAG_CANDIDATES = ["is_precollapse_window", "precollapse_flag", "in_precollapse_window"]
PRECOLLAPSE_ROLE_CANDIDATES = ["window_role", "role", "window_kind"]


def choose_existing(paths: Iterable[Path]) -> Path:
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError(f"none of these files exist: {[str(p) for p in paths]}")


def choose_column(df: pd.DataFrame, candidates: list[str], label: str) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"[{label}] none of these columns found: {candidates}")


def choose_column_optional(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def parse_markets_unit_id(unit_id: str) -> tuple[str, str, str]:
    m = re.match(r"^(?P<config>cfg_[0-9]+)__(?P<slice>.+)__(?P<seg>seg_[0-9]+)$", unit_id)
    if not m:
        raise ValueError(f"[markets] could not parse unit_id: {unit_id}")
    return m.group("config"), m.group("slice"), m.group("seg")


def load_markets_canonical_unit_windows() -> pd.DataFrame:
    if not MARKETS_CANONICAL_INPUT_CSV.exists():
        raise FileNotFoundError(MARKETS_CANONICAL_INPUT_CSV)

    df = pd.read_csv(MARKETS_CANONICAL_INPUT_CSV)
    required = {"unit_id", "kind", "ts_utc"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"[markets canonical input] missing columns: {sorted(missing)}")

    df = df.copy()
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)

    out = (
        df.groupby("unit_id", as_index=False)
        .agg(
            kind=("kind", "first"),
            unit_start_ts_utc=("ts_utc", "min"),
            unit_end_ts_utc=("ts_utc", "max"),
            canonical_n_rows=("ts_utc", "size"),
        )
        .copy()
    )

    parsed = out["unit_id"].map(parse_markets_unit_id)
    out["config_id"] = parsed.map(lambda x: x[0])
    out["slice_id"] = parsed.map(lambda x: x[1])
    out["segment_id"] = parsed.map(lambda x: x[2])

    out = out.sort_values(["kind", "slice_id", "unit_start_ts_utc"], kind="stable").reset_index(drop=True)
    return out


def load_markets_packets() -> pd.DataFrame:
    packet_paths = sorted(MARKETS_PACKET_DIR.glob(f"{MARKETS_CANONICAL_CONFIG_ID}__*.packet.csv"))
    if not packet_paths:
        raise FileNotFoundError(
            f"no packet files found for {MARKETS_CANONICAL_CONFIG_ID} in {MARKETS_PACKET_DIR}"
        )

    parts: list[pd.DataFrame] = []
    for path in packet_paths:
        df = pd.read_csv(path)
        if "ts_utc" not in df.columns:
            raise KeyError(f"[markets] ts_utc missing in {path}")

        slice_id = path.name.split("__", 1)[1].replace(".packet.csv", "")
        df["config_id"] = MARKETS_CANONICAL_CONFIG_ID
        df["slice_id"] = slice_id
        df["kind"] = "event" if slice_id in MARKETS_EVENT_SLICE_IDS else "control"
        df["source_csv"] = str(path)
        parts.append(df)

    out = pd.concat(parts, ignore_index=True)
    out["ts_utc"] = pd.to_datetime(out["ts_utc"], utc=True)
    return out


def compute_terminal_minus_initial(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        raise RuntimeError("[markets] no non-null values available for delta_change")
    return float(s.iloc[-1] - s.iloc[0])


def build_markets_units_late_window(df: pd.DataFrame, late_window_min: int) -> pd.DataFrame:
    g_col = choose_column(df, G_CANDIDATES, "markets:G")
    p_col = choose_column(df, P_CANDIDATES, "markets:p")
    d_col = choose_column(df, D_CANDIDATES, "markets:delta")

    canonical_units = load_markets_canonical_unit_windows()
    work = df.copy()

    rows: list[dict] = []
    for _, unit in canonical_units.iterrows():
        slice_id = str(unit["slice_id"])
        kind = str(unit["kind"])
        unit_id = str(unit["unit_id"])
        start_ts = pd.Timestamp(unit["unit_start_ts_utc"])
        end_ts = pd.Timestamp(unit["unit_end_ts_utc"])

        unit_rows = work.loc[
            work["slice_id"].astype(str).eq(slice_id)
            & work["ts_utc"].ge(start_ts)
            & work["ts_utc"].le(end_ts)
        ].copy()

        if unit_rows.empty:
            raise RuntimeError(
                f"[markets] canonical unit {unit_id} produced no packet rows for "
                f"slice={slice_id} start={start_ts} end={end_ts}"
            )

        late_start = end_ts - pd.Timedelta(minutes=late_window_min)
        late_rows = unit_rows.loc[unit_rows["ts_utc"].ge(late_start)].copy()
        late_rows = late_rows.sort_values("ts_utc", kind="stable")

        if late_rows.empty:
            raise RuntimeError(
                f"[markets] canonical unit {unit_id} produced no late-window rows for "
                f"late_window_min={late_window_min}"
            )

        rows.append(
            {
                "domain": "markets",
                "benchmark_id": "volmageddon_covid_public_v2",
                "window_definition": f"canonical_unit_windows_last_{late_window_min}min",
                "late_window_min": late_window_min,
                "unit_id": unit_id,
                "kind": kind,
                "G_mean": float(pd.to_numeric(late_rows[g_col], errors="coerce").mean()),
                "p_mean": float(pd.to_numeric(late_rows[p_col], errors="coerce").mean()),
                "delta_change": compute_terminal_minus_initial(late_rows[d_col]),
                "n_rows": int(len(late_rows)),
                "canonical_n_rows": int(unit["canonical_n_rows"]),
                "unit_start_ts_utc": start_ts.isoformat(),
                "unit_end_ts_utc": end_ts.isoformat(),
                "late_window_start_ts_utc": late_start.isoformat(),
                "slice_id": slice_id,
                "segment_id": str(unit["segment_id"]),
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError(f"[markets] no canonical units were summarized for late_window_min={late_window_min}")
    return out


def load_recsys_telemetry() -> pd.DataFrame:
    path = choose_existing(RECSYS_TELEMETRY_CANDIDATES)
    if path.suffix == ".gz":
        df = pd.read_csv(path, compression="gzip")
    else:
        df = pd.read_csv(path)

    g_col = choose_column(df, G_CANDIDATES, "recsys:G")
    p_col = choose_column(df, P_CANDIDATES, "recsys:p")
    d_col = choose_column(df, D_CANDIDATES, "recsys:delta")

    horizon_col = choose_column_optional(df, HORIZON_CANDIDATES)
    if horizon_col is not None:
        h = pd.to_numeric(df[horizon_col], errors="coerce")
        mask = h.eq(RECSYS_CANONICAL_HORIZON)
        if mask.any():
            df = df.loc[mask].copy()

    precollapse_flag_col = choose_column_optional(df, PRECOLLAPSE_FLAG_CANDIDATES)
    if precollapse_flag_col is not None:
        flag = df[precollapse_flag_col]
        if pd.api.types.is_bool_dtype(flag):
            df = df.loc[flag].copy()
        else:
            df = df.loc[pd.to_numeric(flag, errors="coerce").fillna(0).astype(int).eq(1)].copy()
    else:
        role_col = choose_column_optional(df, PRECOLLAPSE_ROLE_CANDIDATES)
        if role_col is not None:
            role = df[role_col].astype(str).str.lower()
            if role.isin({"precollapse", "pre_collapse", "pre-collapse"}).any():
                df = df.loc[role.isin({"precollapse", "pre_collapse", "pre-collapse"})].copy()

    kind_col = choose_column_optional(df, KIND_CANDIDATES)
    if kind_col is not None:
        df["kind"] = df[kind_col].astype(str).str.lower()
    elif "is_event" in df.columns:
        df["kind"] = df["is_event"].map({True: "event", False: "control"})
    else:
        raise KeyError("[recsys] could not infer event/control kind column")

    unit_col = choose_column_optional(df, UNIT_ID_CANDIDATES)
    if unit_col is None:
        raise KeyError("[recsys] could not infer unit id column")

    rows: list[dict] = []
    for unit_id, g in df.groupby(unit_col, sort=False):
        kind_vals = g["kind"].dropna().unique().tolist()
        if len(kind_vals) != 1:
            raise RuntimeError(f"[recsys] unit {unit_id} has mixed kinds: {kind_vals}")
        kind = kind_vals[0]
        if kind not in {"event", "control"}:
            continue

        rows.append(
            {
                "domain": "recommender",
                "benchmark_id": "movielens25m_recursive_frontier_public_v1__canonical_h50",
                "window_definition": "canonical_50step_precollapse_units",
                "late_window_min": pd.NA,
                "unit_id": str(unit_id),
                "kind": kind,
                "G_mean": float(pd.to_numeric(g[g_col], errors="coerce").mean()),
                "p_mean": float(pd.to_numeric(g[p_col], errors="coerce").mean()),
                "delta_mean": float(pd.to_numeric(g[d_col], errors="coerce").mean()),
                "n_rows": int(len(g)),
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError("[recsys] no canonical pre-collapse units survived filtering")
    return out


def summarize_domain_witnesses(df_units: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    group_cols = ["domain", "benchmark_id", "window_definition", "late_window_min"]
    for keys, g_dom in df_units.groupby(group_cols, sort=False, dropna=False):
        domain, benchmark_id, window_definition, late_window_min = keys

        event = g_dom.loc[g_dom["kind"] == "event"].copy()
        control = g_dom.loc[g_dom["kind"] == "control"].copy()

        if event.empty or control.empty:
            raise RuntimeError(f"[{domain}] missing event or control units for {window_definition}")

        if domain == "markets":
            spec = [
                ("G", "G_mean", "event_gt_control"),
                ("p", "p_mean", "event_gt_control"),
                ("delta_change", "delta_change", "event_lt_control"),
            ]
        else:
            spec = [
                ("G", "G_mean", "event_gt_control"),
                ("p", "p_mean", "event_gt_control"),
                ("delta", "delta_mean", "event_lt_control"),
            ]

        for witness, col, expected in spec:
            event_mean = float(event[col].mean())
            control_mean = float(control[col].mean())
            diff = event_mean - control_mean

            if expected == "event_gt_control":
                consistent = int(event_mean > control_mean)
                observed_relation = "event > control" if consistent else "event <= control"
            else:
                consistent = int(event_mean < control_mean)
                observed_relation = "event < control" if consistent else "event >= control"

            rows.append(
                {
                    "domain": str(domain),
                    "benchmark_id": str(benchmark_id),
                    "window_definition": str(window_definition),
                    "late_window_min": late_window_min,
                    "n_event_units": int(len(event)),
                    "n_control_units": int(len(control)),
                    "witness": witness,
                    "event_mean": event_mean,
                    "control_mean": control_mean,
                    "event_minus_control": diff,
                    "expected_direction": expected,
                    "observed_relation": observed_relation,
                    "directionally_consistent": consistent,
                }
            )

    out = pd.DataFrame(rows)
    return out


def write_markdown(out: pd.DataFrame) -> None:
    lines: list[str] = []
    lines.append("# Witness-direction measurement table v3")
    lines.append("")
    lines.append(
        "Two-domain descriptive exhibit of witness direction on the public markets and recommender benchmarks, with localized late-window markets summaries and change-based diversity measurement for markets."
    )
    lines.append("")
    lines.append(
        "| Domain | Benchmark | Window definition | Units (event/control) | Witness | Event mean | Control mean | Event - control | Expected direction | Observed | Consistent |"
    )
    lines.append("|---|---|---|---:|---|---:|---:|---:|---|---|---:|")

    for _, r in out.iterrows():
        units = f"{int(r['n_event_units'])}/{int(r['n_control_units'])}"
        lines.append(
            f"| {r['domain']} | {r['benchmark_id']} | {r['window_definition']} | {units} | "
            f"{r['witness']} | {r['event_mean']:.6f} | {r['control_mean']:.6f} | {r['event_minus_control']:.6f} | "
            f"{r['expected_direction']} | {r['observed_relation']} | {int(r['directionally_consistent'])} |"
        )

    lines.append("")
    lines.append("## Reading note")
    lines.append(
        "- `directionally_consistent = 1` means the observed event-vs-control comparison matches the theorem-guided expectation for that witness."
    )
    lines.append(
        "- Markets are summarized over the exact canonical benchmark unit windows defined in `results/rendered/comparators/markets_comparator_input_v2.csv`, restricted to the last 30 or 60 minutes inside each canonical unit."
    )
    lines.append(
        "- In markets, diversity is summarized as `delta_change = terminal delta - initial delta` within each late window, aligning the table more closely to the implemented non-increase semantics."
    )
    lines.append(
        "- Recommenders are summarized over canonical 50-step pre-collapse benchmark units from the MovieLens telemetry panel."
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    frozen_csv = (
        ROOT
        / "results"
        / "frozen"
        / "bridge"
        / "witness_direction_bridge_state_v3__20260422T130759Z"
        / "witness_direction_table_v3.csv"
    )
    frozen_md = frozen_csv.with_suffix(".md")

    # Public-repo path: regenerate the manuscript-facing rendered table from the
    # frozen canonical bridge exhibit. This avoids requiring private/intermediate
    # packet artifacts that are not part of the public submission package.
    if frozen_csv.exists():
        out = pd.read_csv(frozen_csv)
        out.to_csv(OUT_CSV, index=False)
        if frozen_md.exists():
            OUT_MD.write_text(frozen_md.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            write_markdown(out)

        print(OUT_CSV)
        print(OUT_MD)
        print()
        print(out.to_string(index=False))
        return

    markets_raw = load_markets_packets()
    markets_units_parts: list[pd.DataFrame] = []
    for late_window_min in MARKETS_LATE_WINDOWS_MIN:
        markets_units_parts.append(build_markets_units_late_window(markets_raw, late_window_min))
    markets_units = pd.concat(markets_units_parts, ignore_index=True)

    recsys_units = load_recsys_telemetry()

    combined_units = pd.concat([markets_units, recsys_units], ignore_index=True)
    out = summarize_domain_witnesses(combined_units)

    out.to_csv(OUT_CSV, index=False)
    write_markdown(out)

    print(OUT_CSV)
    print(OUT_MD)
    print()
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
    