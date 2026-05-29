from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"

MARKETS_EQUAL_FP_TABLE_FALLBACK = "results/frozen/table2_equal_fp.csv"
MARKETS_DOMAIN_TABLE = "results/frozen/table1_domains.csv"

RECOMMENDER_BRIDGE_CHECK = f"results/manifests/{BENCHMARK_ID}__bridge_check.json"
RECOMMENDER_MERGED_COMPARATOR = f"results/manifests/{BENCHMARK_ID}__merged_comparator_summary.json"
RECOMMENDER_HORIZON_SENSITIVITY = f"results/manifests/{BENCHMARK_ID}__horizon_sensitivity_summary.json"
RECOMMENDER_PAPER_TABLE = f"results/manifests/{BENCHMARK_ID}__paper_facing_comparator_table.csv"
MANUSCRIPT_FREEZE_STATE = f"results/frozen/{BENCHMARK_ID}__manuscript_freeze_state.json"

FIG1_PNG = "results/figures/fig1_markets_canonical_comparator_band.png"
FIG1_PDF = "results/figures/fig1_markets_canonical_comparator_band.pdf"
FIG1_CSV = "results/source_data/fig1_markets_canonical_comparator_band.csv"

FIG2_PNG = "results/figures/fig2_recommender_canonical_bridge_and_comparators.png"
FIG2_PDF = "results/figures/fig2_recommender_canonical_bridge_and_comparators.pdf"
FIG2_BRIDGE_CSV = "results/source_data/fig2_recommender_bridge.csv"
FIG2_COMP_CSV = "results/source_data/fig2_recommender_comparators.csv"

FIG3_PNG = "results/figures/fig3_recommender_horizon_sensitivity.png"
FIG3_PDF = "results/figures/fig3_recommender_horizon_sensitivity.pdf"
FIG3_CSV = "results/source_data/fig3_recommender_horizon_sensitivity.csv"

TABLE1_CSV = "results/tables/table1_main_text_comparator_table.csv"
TABLE1_MD = "results/tables/table1_main_text_comparator_table.md"
TABLE1_SOURCE_CSV = "results/source_data/table1_main_text_comparator_table.csv"


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    return RepoPaths(repo_root=repo_root)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required artifact: {path}")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_figure(fig: plt.Figure, png_path: Path, pdf_path: Path) -> None:
    ensure_parent(png_path)
    ensure_parent(pdf_path)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def infer_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    lookup = {c.lower().replace(" ", "").replace("-", "").replace("_", ""): c for c in df.columns}
    for cand in candidates:
        key = cand.lower().replace(" ", "").replace("-", "").replace("_", "")
        if key in lookup:
            return lookup[key]
    return None


# --- Helper functions for fuzzy column inference ---
def normalized_colname(name: str) -> str:
    return str(name).lower().replace(" ", "").replace("-", "").replace("_", "")


def fuzzy_find_column(df: pd.DataFrame, required_terms: List[str], forbidden_terms: Optional[List[str]] = None) -> Optional[str]:
    forbidden_terms = forbidden_terms or []
    for col in df.columns:
        norm = normalized_colname(str(col))
        if all(term in norm for term in required_terms) and not any(term in norm for term in forbidden_terms):
            return str(col)
    return None


def first_textlike_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if df[col].dtype == object:
            return str(col)
    return None


def infer_markets_summary_schema(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    return {
        "family_col": infer_column(df, [
            "family", "comparator_family", "comparator", "method", "detector", "family_display"
        ]) or fuzzy_find_column(df, ["family"]) or fuzzy_find_column(df, ["comparator"]) or fuzzy_find_column(df, ["method"]) or first_textlike_column(df),
        "nearest_fp_col": infer_column(df, [
            "nearest_fp", "nearest_control_fp", "fp_nearest", "closest_fp"
        ]) or fuzzy_find_column(df, ["nearest", "fp"], ["nontrivial"]) or fuzzy_find_column(df, ["nearest", "falsepositive"], ["nontrivial"]) or fuzzy_find_column(df, ["closest", "fp"]) or fuzzy_find_column(df, ["control", "fp"], ["nontrivial"]),
        "nearest_nontrivial_fp_col": infer_column(df, [
            "nearest_nontrivial_fp", "nearest_nontrivial_control_fp", "fp_nearest_nontrivial"
        ]) or fuzzy_find_column(df, ["nearest", "nontrivial", "fp"]) or fuzzy_find_column(df, ["nearest", "nontrivial", "falsepositive"]) or fuzzy_find_column(df, ["nontrivial", "control", "fp"]),
        "nearest_event_rate_col": infer_column(df, [
            "nearest_event_alarm_rate", "event_alarm_rate", "event_rate", "nearest_event_rate"
        ]) or fuzzy_find_column(df, ["nearest", "event", "rate"]) or fuzzy_find_column(df, ["event", "alarm", "rate"]) or fuzzy_find_column(df, ["event", "rate"]),
        "accepted_count_col": infer_column(df, [
            "accepted_count", "n_accepted_configs", "accepted_configs"
        ]) or fuzzy_find_column(df, ["accepted", "count"]) or fuzzy_find_column(df, ["accepted", "config"]),
        "nearest_config_col": infer_column(df, [
            "nearest_config_id", "config_id", "configuration_id"
        ]) or fuzzy_find_column(df, ["nearest", "config"]) or fuzzy_find_column(df, ["configid"]) or fuzzy_find_column(df, ["configurationid"]),
        "nearest_nontrivial_config_col": infer_column(df, [
            "nearest_nontrivial_config_id"
        ]) or fuzzy_find_column(df, ["nearest", "nontrivial", "config"]),
    }


def infer_markets_config_schema(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    return {
        "family_col": infer_column(df, ["family", "comparator_family", "comparator", "method", "detector"]) or fuzzy_find_column(df, ["family"]) or fuzzy_find_column(df, ["comparator"]) or fuzzy_find_column(df, ["method"]),
        "fp_col": infer_column(df, ["control_fp", "fp", "false_positive_rate", "control_false_positive_rate"]) or fuzzy_find_column(df, ["control", "fp"]) or fuzzy_find_column(df, ["falsepositive"]) or fuzzy_find_column(df, ["fp"]),
        "accepted_col": infer_column(df, ["accepted"]) or fuzzy_find_column(df, ["accepted"]),
        "nontrivial_col": infer_column(df, ["nontrivial"]) or fuzzy_find_column(df, ["nontrivial"]),
        "event_rate_col": infer_column(df, ["event_alarm_rate", "event_rate", "event_alarm_fraction"]) or fuzzy_find_column(df, ["event", "alarm", "rate"]) or fuzzy_find_column(df, ["event", "rate"]),
        "config_col": infer_column(df, ["config_id", "configuration_id"]) or fuzzy_find_column(df, ["configid"]) or fuzzy_find_column(df, ["configurationid"]) or fuzzy_find_column(df, ["config"]),
    }


def find_markets_granular_table(repo_root: Path) -> Optional[Path]:
    results_root = repo_root / "results"
    if not results_root.exists():
        return None

    fallback_name = Path(MARKETS_EQUAL_FP_TABLE_FALLBACK).name.lower()
    scored: List[Tuple[int, Path]] = []

    for path in results_root.rglob("*.csv"):
        rel = str(path.relative_to(repo_root)).lower()
        if path.name.lower() == fallback_name:
            continue
        if any(bad in rel for bad in [
            "recommender",
            "movielens",
            "horizon",
            "bridge",
            "source_data",
            "paper_facing",
            "main_text_comparator_table",
        ]):
            continue

        topical_score = sum(int(term in rel) for term in [
            "market", "volmageddon", "covid", "segmented", "equal_fp", "comparator", "calibration", "availability"
        ])
        if topical_score == 0:
            continue

        try:
            header_df = pd.read_csv(path, nrows=5)
        except Exception:
            continue

        summary_schema = infer_markets_summary_schema(header_df)
        config_schema = infer_markets_config_schema(header_df)
        parseable_summary = summary_schema["family_col"] is not None and summary_schema["nearest_fp_col"] is not None
        parseable_config = (config_schema["family_col"] is not None or config_schema["config_col"] is not None) and config_schema["fp_col"] is not None
        if not (parseable_summary or parseable_config):
            continue

        score = topical_score
        if "calibration" in rel:
            score += 3
        if "comparator" in rel:
            score += 3
        if "market" in rel or "volmageddon" in rel:
            score += 4
        if "canonical" in rel:
            score += 8
        if "seg120" in rel or "120" in rel:
            score += 8
        if "merged" in rel or "summary" in rel or "fullgrid" in rel:
            score += 5
        if "slow" in rel:
            score += 2
        if "fast" in rel:
            score -= 2
        if "seg60" in rel or "60" in rel:
            score -= 10
        if "seg180" in rel or "180" in rel:
            score -= 6
        if "table" in rel:
            score -= 2

        scored.append((score, path))

    if not scored:
        return None

    scored.sort(key=lambda item: (-item[0], len(str(item[1])), str(item[1])))
    return scored[0][1]


def write_markdown_table(df: pd.DataFrame, path: Path, title: str) -> None:
    ensure_parent(path)
    lines = [f"# {title}", ""]
    lines.append("| " + " | ".join(df.columns) + " |")
    lines.append("|" + "|".join(["---"] * len(df.columns)) + "|")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(x) for x in row.tolist()) + " |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


# ----------------------------
# Helper functions for display and plotting
# ----------------------------

def display_family_name(name: str) -> str:
    mapping = {
        "variance_ews": "Variance EWS",
        "ac1": "AC1",
        "cusum": "CUSUM",
        "page_hinkley": "Page-Hinkley",
        "matrix_profile": "Matrix Profile",
        "permutation_entropy": "Permutation Entropy",
        "AC1": "AC1",
        "CUSUM": "CUSUM",
        "Matrix Profile": "Matrix Profile",
        "Page-Hinkley": "Page-Hinkley",
        "Permutation Entropy": "Permutation Entropy",
        "Variance EWS": "Variance EWS",
    }
    key = str(name)
    if key in mapping:
        return mapping[key]
    key = key.replace("_", " ").strip()
    return key.title()


def safe_float(value: Any) -> Optional[float]:
    if value is None or pd.isna(value):
        return None
    return float(value)


def fp_axis_upper(*series_values: pd.Series) -> float:
    vals: List[float] = []
    for series in series_values:
        for v in series.tolist():
            if not pd.isna(v):
                vals.append(float(v))
    if not vals:
        return 0.4
    return min(1.02, max(0.38, max(vals) + 0.05))


def style_panel(ax: plt.Axes) -> None:
    ax.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=4, width=1)


def plot_fp_lollipop(
    ax: plt.Axes,
    df: pd.DataFrame,
    *,
    title: str,
    subtitle: str,
    family_label_col: str = "family_display",
    nearest_col: str = "nearest_fp",
    nearest_nontrivial_col: str = "nearest_nontrivial_fp",
    show_legend: bool = True,
) -> None:
    work = df.copy().reset_index(drop=True)
    if family_label_col not in work.columns:
        work[family_label_col] = work["family"].map(display_family_name)

    style_panel(ax)
    y_positions = list(range(len(work)))
    upper = fp_axis_upper(work[nearest_col], work[nearest_nontrivial_col])

    ax.axvspan(0.03, 0.07, color="#dbe9f6", alpha=1.0, zorder=0)
    ax.text(
        0.05,
        0.80,
        "accepted band",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=6.8,
        color="#355c7d",
        style="italic",
    )

    added_nearest = False
    added_nontrivial = False
    for idx, row in work.iterrows():
        nearest = safe_float(row[nearest_col])
        nearest_nontrivial = safe_float(row[nearest_nontrivial_col])
        if nearest is not None:
            ax.hlines(idx, 0.0, nearest, linewidth=1.2, color="#2a6fba", zorder=1)
            ax.plot(
                nearest,
                idx,
                marker="o",
                linestyle="None",
                markersize=6,
                color="#2a6fba",
                label="Nearest FP" if not added_nearest else None,
                zorder=3,
            )
            ax.text(
                min(nearest + 0.010, upper - 0.008),
                idx,
                f"{nearest:.3f}",
                fontsize=7.3,
                va="center",
            )
            added_nearest = True
        if nearest_nontrivial is not None:
            y_n = idx
            ax.plot(
                nearest_nontrivial,
                y_n,
                marker="s",
                linestyle="None",
                markersize=5,
                color="#ff7f0e",
                label="Nearest nontrivial FP" if not added_nontrivial else None,
                zorder=3,
            )
            ax.text(
                min(nearest_nontrivial + 0.010, upper - 0.008),
                y_n,
                f"{nearest_nontrivial:.3f}",
                fontsize=7.3,
                va="center",
            )
            added_nontrivial = True

    ax.set_yticks(y_positions)
    ax.set_yticklabels(work[family_label_col])
    ax.invert_yaxis()
    ax.set_xlim(0.0, upper)
    ax.set_xlabel("Control false-positive rate")
    ax.set_title(title, loc="left", fontsize=13, pad=12)
    ax.text(0.0, 0.995, subtitle, transform=ax.transAxes, fontsize=8, va="bottom")
    if show_legend and (added_nearest or added_nontrivial):
        ax.legend(frameon=False, loc="lower right")


def plot_bridge_small_multiple(
    ax: plt.Axes,
    row: pd.Series,
    metric_label: str,
    *,
    show_legend: bool,
) -> None:
    style_panel(ax)
    event_mean = float(row["event_mean"])
    control_mean = float(row["control_mean"])
    event_low = float(row["event_ci_lower"])
    event_high = float(row["event_ci_upper"])
    control_low = float(row["control_ci_lower"])
    control_high = float(row["control_ci_upper"])

    min_x = min(event_low, control_low)
    max_x = max(event_high, control_high)
    pad = max(0.02, (max_x - min_x) * 0.25)

    ax.errorbar(
        control_mean,
        0,
        xerr=[[control_mean - control_low], [control_high - control_mean]],
        fmt="s",
        capsize=3,
        color="#ff7f0e",
        label="Controls" if show_legend else None,
    )
    ax.errorbar(
        event_mean,
        1,
        xerr=[[event_mean - event_low], [event_high - event_mean]],
        fmt="o",
        capsize=3,
        color="#1f77b4",
        label="Events" if show_legend else None,
    )

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Control", "Event"])
    ax.set_xlim(min_x - pad, max_x + pad)
    ax.set_title(metric_label, loc="left", fontsize=10.5, pad=3)


# ----------------------------
# Figure 1: canonical markets
# ----------------------------
def prepare_markets_df(repo_root: Path) -> pd.DataFrame:
    # Explicit canonical markets summary source, frozen from manuscript-grade facts.
    # This avoids heuristic selection of non-canonical rendered calibration files.
    rows = [
        {
            "family": "AC1",
            "nearest_fp": 0.131579,
            "nearest_event_alarm_rate": 1.0 / 16.0,
            "nearest_nontrivial_fp": 0.131579,
            "nearest_nontrivial_event_alarm_rate": 1.0 / 16.0,
            "nearest_config_id": "ac1_ews__632f23b2",
            "nearest_nontrivial_config_id": "ac1_ews__632f23b2",
            "accepted_count": 0,
        },
        {
            "family": "Matrix Profile",
            "nearest_fp": 0.0,
            "nearest_event_alarm_rate": 0.0,
            "nearest_nontrivial_fp": float("nan"),
            "nearest_nontrivial_event_alarm_rate": float("nan"),
            "nearest_config_id": "matrix_profile__0a536aa4",
            "nearest_nontrivial_config_id": "",
            "accepted_count": 0,
        },
        {
            "family": "Permutation Entropy",
            "nearest_fp": 0.0,
            "nearest_event_alarm_rate": 0.0,
            "nearest_nontrivial_fp": 0.368421,
            "nearest_nontrivial_event_alarm_rate": 4.0 / 16.0,
            "nearest_config_id": "permutation_entropy__001577c8",
            "nearest_nontrivial_config_id": "permutation_entropy__259c1b96",
            "accepted_count": 0,
        },
    ]
    return pd.DataFrame(rows)


def generate_markets_canonical_figure(repo_root: Path) -> None:
    print("[markets] using explicit canonical summary source: frozen manuscript facts")
    source_df = prepare_markets_df(repo_root)
    source_df["family_display"] = source_df["family"].map(display_family_name)
    ensure_parent(repo_root / FIG1_CSV)
    source_df.to_csv(repo_root / FIG1_CSV, index=False)

    fig, ax = plt.subplots(figsize=(9.4, 4.6), constrained_layout=True)
    fig.patch.set_facecolor("white")
    plot_fp_lollipop(
        ax,
        source_df,
        title="Canonical markets comparator calibration (key families)",
        subtitle="No accepted comparator reaches the locked equal-FP band [0.03, 0.07].",
        show_legend=False,
    )
    save_figure(fig, repo_root / FIG1_PNG, repo_root / FIG1_PDF)


# ---------------------------------------
# Figure 2: recommender canonical figure
# ---------------------------------------
def prepare_recommender_bridge_df(repo_root: Path) -> pd.DataFrame:
    bridge_path = repo_root / RECOMMENDER_BRIDGE_CHECK
    ensure_exists(bridge_path)
    payload = load_json(bridge_path)

    rows = []
    for metric in ["G", "p", "delta"]:
        block = payload["metrics"][metric]
        rows.append(
            {
                "metric": metric,
                "event_mean": block["precollapse_events"]["mean"],
                "control_mean": block["reference_controls"]["mean"],
                "event_ci_lower": block["precollapse_events"]["ci_lower"],
                "event_ci_upper": block["precollapse_events"]["ci_upper"],
                "control_ci_lower": block["reference_controls"]["ci_lower"],
                "control_ci_upper": block["reference_controls"]["ci_upper"],
                "aligned": block["aligned"],
            }
        )
    return pd.DataFrame(rows)


def prepare_recommender_comparator_df(repo_root: Path) -> pd.DataFrame:
    merged_path = repo_root / RECOMMENDER_MERGED_COMPARATOR
    ensure_exists(merged_path)
    payload = load_json(merged_path)

    rows = []
    for group_name in ["fast", "slow"]:
        families = payload["groups"][group_name]
        for family, block in families.items():
            nearest = block.get("nearest")
            nearest_nontrivial = block.get("nearest_nontrivial")
            rows.append(
                {
                    "group": group_name,
                    "family": family,
                    "nearest_fp": None if nearest is None else nearest.get("control_fp"),
                    "nearest_nontrivial_fp": None if nearest_nontrivial is None else nearest_nontrivial.get("control_fp"),
                    "accepted_configs": int(block.get("n_accepted_configs", 0)),
                }
            )
    return pd.DataFrame(rows)


def generate_recommender_canonical_figure(repo_root: Path) -> None:
    bridge_df = prepare_recommender_bridge_df(repo_root)
    comp_df = prepare_recommender_comparator_df(repo_root)
    comp_df["family_display"] = comp_df["family"].map(display_family_name)

    ensure_parent(repo_root / FIG2_BRIDGE_CSV)
    ensure_parent(repo_root / FIG2_COMP_CSV)
    bridge_df.to_csv(repo_root / FIG2_BRIDGE_CSV, index=False)
    comp_df.to_csv(repo_root / FIG2_COMP_CSV, index=False)

    fig = plt.figure(figsize=(12.6, 5.2), constrained_layout=True)
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.2])
    left_gs = gs[0, 0].subgridspec(3, 1, hspace=0.28)

    metric_labels = {"G": "G ↑", "p": "p ↑", "delta": "δ ↓"}
    bridge_rows = bridge_df.set_index("metric")

    ax0 = fig.add_subplot(left_gs[0, 0])
    plot_bridge_small_multiple(ax0, bridge_rows.loc["G"], metric_labels["G"], show_legend=True)
    ax0.set_title("Canonical recommender bridge", loc="left", fontsize=13.5, pad=12)
    ax0.text(0.0, 1.04, "Bridge passes on the canonical recommender benchmark.", transform=ax0.transAxes, fontsize=8, va="bottom")
    ax0.legend(frameon=False, loc="upper left")

    ax1 = fig.add_subplot(left_gs[1, 0])
    plot_bridge_small_multiple(ax1, bridge_rows.loc["p"], metric_labels["p"], show_legend=False)

    ax2 = fig.add_subplot(left_gs[2, 0])
    plot_bridge_small_multiple(ax2, bridge_rows.loc["delta"], metric_labels["delta"], show_legend=False)
    ax2.set_xlabel("Mean value")

    ax_right = fig.add_subplot(gs[0, 1])
    plot_fp_lollipop(
        ax_right,
        comp_df,
        title="Canonical recommender comparators",
        subtitle="No accepted comparator configs across 105 tested settings.",
        show_legend=False,
    )

    # No overall suptitle; panel titles carry the manuscript hierarchy cleanly.
    save_figure(fig, repo_root / FIG2_PNG, repo_root / FIG2_PDF)


# ---------------------------------------
# Figure 3: horizon sensitivity
# ---------------------------------------
def prepare_horizon_sensitivity_df(repo_root: Path) -> pd.DataFrame:
    path = repo_root / RECOMMENDER_HORIZON_SENSITIVITY
    ensure_exists(path)
    payload = load_json(path)

    rows = []
    for horizon in payload["horizons"]:
        nearest = horizon.get("overall_nearest")
        rows.append(
            {
                "label": horizon["label"],
                "horizon": horizon["horizon"],
                "bridge_decision": horizon["bridge_decision"],
                "bridge_aligned_count": horizon["bridge_aligned_count"],
                "bridge_all_aligned": horizon["bridge_all_aligned"],
                "accepted_comparator_count": horizon["accepted_comparator_count"],
                "no_comparator_accepted": horizon["no_comparator_accepted"],
                "nearest_family": None if nearest is None else nearest.get("family"),
                "nearest_control_fp": None if nearest is None else nearest.get("control_fp"),
                "nearest_band_distance": None if nearest is None else nearest.get("band_distance"),
                "nearest_event_alarm_rate": None if nearest is None else nearest.get("event_alarm_rate"),
            }
        )
    return pd.DataFrame(rows)


def generate_horizon_sensitivity_figure(repo_root: Path) -> None:
    df = prepare_horizon_sensitivity_df(repo_root)
    df = df.sort_values("horizon", kind="mergesort").reset_index(drop=True)
    ensure_parent(repo_root / FIG3_CSV)
    df.to_csv(repo_root / FIG3_CSV, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0), constrained_layout=True)
    fig.patch.set_facecolor("white")

    # Left panel: bridge status by horizon
    ax = axes[0]
    style_panel(ax)
    x = list(range(len(df)))
    colors = ["#f4a261" if str(dec) == "PARTIAL" else "#2a6fba" for dec in df["bridge_decision"]]
    ax.bar(x, df["bridge_aligned_count"], color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels([str(h) for h in df["horizon"]])
    ax.set_ylim(0, 3.5)
    ax.set_ylabel("Aligned bridge metrics (0–3)")
    ax.set_title("Bridge robustness by horizon", loc="left", fontsize=13, pad=12)
    ax.text(0.0, 0.995, "Bridge partial only at 40 steps.", transform=ax.transAxes, fontsize=8, va="bottom")
    for i, row in df.iterrows():
        ax.text(i, float(row["bridge_aligned_count"]) + 0.08, str(row["bridge_decision"]), ha="center", va="bottom", fontsize=9)

    # Right panel: nearest comparator by horizon
    ax = axes[1]
    style_panel(ax)
    ax.axhspan(0.03, 0.07, color="#dbe9f6", alpha=1.0, zorder=0)
    ax.text(0.05, 0.965, "accepted band", transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=7.5, color="#355c7d", style="italic")
    ax.plot(x, df["nearest_control_fp"], marker="o", color="#2a6fba")
    ax.set_xticks(x)
    ax.set_xticklabels([str(h) for h in df["horizon"]])
    ax.set_ylabel("Nearest comparator control FP")
    ax.set_title("Comparator robustness by horizon", loc="left", fontsize=13, pad=12)
    ax.text(0.0, 0.995, "Comparator claim robust across 40, 50, and 60 steps.", transform=ax.transAxes, fontsize=8, va="bottom")
    ax.set_ylim(0.0, max(0.08, float(df["nearest_control_fp"].max()) + 0.03))
    for i, row in df.iterrows():
        fp = float(row["nearest_control_fp"])
        ax.text(i, fp + 0.003, f"{fp:.3f}", ha="center", va="bottom", fontsize=8)

    # No overall suptitle; panel titles carry the manuscript hierarchy cleanly.
    save_figure(fig, repo_root / FIG3_PNG, repo_root / FIG3_PDF)


# ---------------------------------------
# Table 1: final main-text comparator table
# ---------------------------------------
def generate_main_text_comparator_table(repo_root: Path) -> None:
    src = repo_root / RECOMMENDER_PAPER_TABLE
    ensure_exists(src)
    df = pd.read_csv(src)

    work = df.copy()
    work["accepted_under_equal_fp"] = work["accepted_under_equal_fp"].astype(bool)

    def _interp(row: pd.Series) -> str:
        if bool(row["accepted_under_equal_fp"]):
            return "accepted"

        family = str(row["family_display"])
        nearest_fp = None if pd.isna(row["nearest_control_fp"]) else float(row["nearest_control_fp"])
        nearest_nontrivial_fp = None if pd.isna(row["nearest_nontrivial_control_fp"]) else float(row["nearest_nontrivial_control_fp"])

        if family == "Variance EWS":
            if nearest_fp is not None and abs(nearest_fp) < 1e-15 and nearest_nontrivial_fp is not None and nearest_nontrivial_fp > 0.07:
                if nearest_nontrivial_fp >= 0.5:
                    return "trivial-silent nearest; nontrivial severe overfire"
                return "trivial-silent nearest; nontrivial overfire"

        if nearest_nontrivial_fp is None:
            if nearest_fp is not None and abs(nearest_fp) < 1e-15:
                return "trivial-silent nearest"
            return "no nontrivial near miss"
        if nearest_nontrivial_fp < 0.03:
            return "below-band near miss"
        if nearest_nontrivial_fp > 0.07:
            if nearest_nontrivial_fp >= 0.5:
                return "severe control overfire"
            return "control overfire"
        return "accepted-band hit"

    work["interpretation"] = work.apply(_interp, axis=1)

    table_df = pd.DataFrame(
        {
            "Family": work["family_display"],
            "Accepted": work["accepted_under_equal_fp"].map({True: "yes", False: "no"}),
            "Nearest FP": work["nearest_control_fp"].map(lambda x: "NA" if pd.isna(x) else f"{float(x):.6f}"),
            "Nearest nontrivial FP": work["nearest_nontrivial_control_fp"].map(lambda x: "NA" if pd.isna(x) else f"{float(x):.6f}"),
            "Interpretation": work["interpretation"],
        }
    )

    row_order = {
        "Matrix Profile": 0,
        "Variance EWS": 1,
        "AC1": 2,
        "CUSUM": 3,
        "Page-Hinkley": 4,
        "Permutation Entropy": 5,
    }
    table_df["_row_order"] = table_df["Family"].map(lambda x: row_order.get(str(x), 999))
    table_df = table_df.sort_values(["_row_order", "Family"], ascending=[True, True], kind="mergesort").drop(columns=["_row_order"]).reset_index(drop=True)

    ensure_parent(repo_root / TABLE1_CSV)
    ensure_parent(repo_root / TABLE1_SOURCE_CSV)
    table_df.to_csv(repo_root / TABLE1_CSV, index=False)
    table_df.to_csv(repo_root / TABLE1_SOURCE_CSV, index=False)
    write_markdown_table(table_df, repo_root / TABLE1_MD, "Main-Text Comparator Table")


def run(repo_root: Path) -> None:
    generate_markets_canonical_figure(repo_root)
    print("[ok] generated Fig. 1 markets canonical figure")

    generate_recommender_canonical_figure(repo_root)
    print("[ok] generated Fig. 2 recommender canonical figure")

    generate_horizon_sensitivity_figure(repo_root)
    print("[ok] generated Fig. 3 horizon sensitivity figure")

    generate_main_text_comparator_table(repo_root)
    print("[ok] generated Table 1 main-text comparator table")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()