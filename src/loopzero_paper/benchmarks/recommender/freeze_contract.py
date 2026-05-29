from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple


# ============================================================
# Contract constants
# ============================================================

BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
BENCHMARK_DISPLAY_NAME = "MovieLens-25M Recursive Frontier Benchmark"
BENCHMARK_DOMAIN = "recommender_systems"
BENCHMARK_VERSION = "v1"

DATASET_NAME = "MovieLens-25M"
DATASET_SOURCE = "GroupLens"
DATASET_ARCHIVE_FILENAME = "ml-25m.zip"
DATASET_README_FILENAME = "ml-25m-README.html"
DATASET_RATINGS_FILENAME = "ratings.csv"
DATASET_MOVIES_FILENAME = "movies.csv"
DATASET_TAGS_FILENAME = "tags.csv"

# Prespecified fairness rule
EQUAL_FP_BAND = (0.03, 0.07)

# Canonical comparator families
FAST_COMPARATOR_FAMILIES = [
    "variance_ews",
    "ac1",
    "cusum",
    "page_hinkley",
]

SLOW_COMPARATOR_FAMILIES = [
    "matrix_profile",
    "permutation_entropy",
]

# Canonical robustness horizons
CANONICAL_HORIZON = 50
ROBUSTNESS_HORIZONS = [40, 50, 60]


# ============================================================
# Data classes
# ============================================================

@dataclass(frozen=True)
class DatasetSpec:
    name: str
    source: str
    archive_filename: str
    readme_filename: str
    ratings_filename: str
    movies_filename: str
    tags_filename: str
    rating_timestamp_unit: Literal["unix_seconds"] = "unix_seconds"
    sort_rule_within_user: Tuple[str, ...] = ("timestamp", "movieId")
    one_episode_per_user: bool = True
    notes: str = (
        "Canonical public snapshot. Ratings must be chronologically sorted within "
        "user before episode construction because released files are not globally "
        "time-ordered by timestamp."
    )


@dataclass(frozen=True)
class EngineSpec:
    """
    This is the exact recommender engine contract to hash and freeze.

    The engine hash must reflect the true scientific benchmark object.
    That means it should include:
    - model family
    - scoring rule / similarity rule
    - candidate filtering policy
    - update policy
    - tie-break rule
    - any fixed hyperparameters
    - code version or commit if known
    """
    engine_family: str
    engine_name: str
    engine_version: str
    deterministic: bool
    candidate_policy: str
    update_policy: str
    tie_break_rule: str
    hyperparameters: Dict[str, Any]
    code_commit: Optional[str] = None
    notes: str = ""

    def stable_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        return _normalize_for_hash(payload)

    def engine_hash(self) -> str:
        blob = json.dumps(
            self.stable_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:16]


@dataclass(frozen=True)
class CollapseSpec:
    warm_start_ratings: int = 30
    positive_rating_threshold: float = 4.0
    top_k: int = 10
    max_horizon_steps: int = CANONICAL_HORIZON
    collapse_streak_len: int = 8
    remaining_frontier_floor: int = 10
    min_warning_runway: int = 15
    deterministic_frontier_reveal_rule: str = (
        "highest_rating_then_earliest_true_timestamp_then_lowest_movieId"
    )
    collapse_definition: str = (
        "Collapse occurs at the first step tau where the recommender fails for "
        "collapse_streak_len consecutive recursive update steps to recover any "
        "remaining held-out positive item while remaining frontier size remains "
        "at least remaining_frontier_floor, within max_horizon_steps."
    )


@dataclass(frozen=True)
class ComparatorSpec:
    fast_families: List[str] = field(default_factory=lambda: FAST_COMPARATOR_FAMILIES.copy())
    slow_families: List[str] = field(default_factory=lambda: SLOW_COMPARATOR_FAMILIES.copy())
    equal_fp_band_lower: float = EQUAL_FP_BAND[0]
    equal_fp_band_upper: float = EQUAL_FP_BAND[1]
    control_fp_definition: str = (
        "Fraction of control units containing at least one gated alarm."
    )
    acceptance_rule: str = (
        "A comparator configuration is accepted iff control-unit FP is within "
        "[equal_fp_band_lower, equal_fp_band_upper]."
    )
    nearest_rule: str = (
        "Nearest = minimum distance to the accepted FP band, even if trivial-silent."
    )
    nontrivial_rule: str = (
        "Nontrivial = configuration produces at least one alarm on any unit."
    )
    availability_rule: str = (
        "A comparator configuration is available only if it can be evaluated on all "
        "frozen units under the prespecified admissible windowing rule."
    )


@dataclass(frozen=True)
class RobustnessSpec:
    canonical_horizon: int = CANONICAL_HORIZON
    adjacent_horizons: List[int] = field(default_factory=lambda: ROBUSTNESS_HORIZONS.copy())
    robustness_axis: str = "episode_length_sensitivity"
    rule: str = (
        "Only adjacent horizon sensitivity is canonical for this benchmark: "
        "40, 50, 60 recursive update steps. No other sensitivity analyses are "
        "considered canonical at contract freeze."
    )


@dataclass(frozen=True)
class BenchmarkContract:
    benchmark_id: str
    benchmark_display_name: str
    benchmark_domain: str
    benchmark_version: str
    created_utc: str
    dataset: DatasetSpec
    engine: Dict[str, Any]
    collapse: CollapseSpec
    comparators: ComparatorSpec
    robustness: RobustnessSpec
    scientific_purpose: str
    falsification_rule: str
    notes: str = ""

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "benchmark_id": self.benchmark_id,
            "benchmark_display_name": self.benchmark_display_name,
            "benchmark_domain": self.benchmark_domain,
            "benchmark_version": self.benchmark_version,
            "created_utc": self.created_utc,
            "dataset": asdict(self.dataset),
            "engine": _normalize_for_hash(self.engine),
            "collapse": asdict(self.collapse),
            "comparators": asdict(self.comparators),
            "robustness": asdict(self.robustness),
            "scientific_purpose": self.scientific_purpose,
            "falsification_rule": self.falsification_rule,
            "notes": self.notes,
        }
        return payload


# ============================================================
# Helpers
# ============================================================

def _normalize_for_hash(obj: Any) -> Any:
    """
    Recursively normalize objects so the hash is stable across runs.
    """
    if dataclasses.is_dataclass(obj):
        obj = asdict(obj)

    if isinstance(obj, dict):
        return {str(k): _normalize_for_hash(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, (list, tuple)):
        return [_normalize_for_hash(x) for x in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj


def _pretty_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _json_sha256(payload: Dict[str, Any]) -> str:
    blob = json.dumps(
        _normalize_for_hash(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _diff_payloads(old: Dict[str, Any], new: Dict[str, Any], prefix: str = "") -> List[str]:
    """
    Small recursive structural diff for human-readable contract drift detection.
    """
    diffs: List[str] = []

    old_keys = set(old.keys())
    new_keys = set(new.keys())

    for key in sorted(old_keys - new_keys):
        diffs.append(f"- removed {prefix}{key}: {old[key]!r}")
    for key in sorted(new_keys - old_keys):
        diffs.append(f"+ added   {prefix}{key}: {new[key]!r}")

    for key in sorted(old_keys & new_keys):
        old_v = old[key]
        new_v = new[key]
        path = f"{prefix}{key}"

        if isinstance(old_v, dict) and isinstance(new_v, dict):
            diffs.extend(_diff_payloads(old_v, new_v, prefix=path + "."))
        elif old_v != new_v:
            diffs.append(f"~ changed {path}: {old_v!r} -> {new_v!r}")

    return diffs


# ============================================================
# Contract builder
# ============================================================

def build_recommender_benchmark_contract(
    *,
    engine_spec: EngineSpec,
    notes: str = "",
) -> BenchmarkContract:
    """
    Build the frozen benchmark contract.

    Important:
    - engine_spec is the scientific engine contract
    - its stable payload is hashed and recorded
    """
    engine_hash = engine_spec.engine_hash()

    engine_payload = engine_spec.stable_payload()
    engine_payload["engine_hash"] = engine_hash

    contract = BenchmarkContract(
        benchmark_id=BENCHMARK_ID,
        benchmark_display_name=BENCHMARK_DISPLAY_NAME,
        benchmark_domain=BENCHMARK_DOMAIN,
        benchmark_version=BENCHMARK_VERSION,
        created_utc=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        dataset=DatasetSpec(
            name=DATASET_NAME,
            source=DATASET_SOURCE,
            archive_filename=DATASET_ARCHIVE_FILENAME,
            readme_filename=DATASET_README_FILENAME,
            ratings_filename=DATASET_RATINGS_FILENAME,
            movies_filename=DATASET_MOVIES_FILENAME,
            tags_filename=DATASET_TAGS_FILENAME,
        ),
        engine=engine_payload,
        collapse=CollapseSpec(),
        comparators=ComparatorSpec(),
        robustness=RobustnessSpec(),
        scientific_purpose=(
            "Freeze the canonical public recommender benchmark contract so that "
            "dataset identity, recommender engine identity, collapse definition, "
            "equal-FP comparator families, and robustness horizons cannot drift "
            "during calibration or manuscript preparation."
        ),
        falsification_rule=(
            "The recommender branch fails as a corroborating flagship benchmark if "
            "any comparator family achieves an accepted operating point on the "
            "canonical benchmark under the same locked equal-FP criterion."
        ),
        notes=notes,
    )
    return contract


# ============================================================
# Persistence API
# ============================================================

def write_contract_freeze(
    out_path: Path,
    *,
    engine_spec: EngineSpec,
    notes: str = "",
    overwrite: bool = False,
    fail_on_drift: bool = True,
) -> Dict[str, Any]:
    """
    Write the contract freeze to disk.

    Behavior:
    - if file does not exist: write it
    - if file exists and identical: return existing
    - if file exists and differs:
        - fail if fail_on_drift=True
        - overwrite only if overwrite=True and fail_on_drift=False
    """
    contract = build_recommender_benchmark_contract(engine_spec=engine_spec, notes=notes)
    payload = contract.to_payload()
    payload["contract_sha256"] = _json_sha256(payload)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists():
        existing = _load_json(out_path)
        if _normalize_for_hash(existing) == _normalize_for_hash(payload):
            return existing

        diffs = _diff_payloads(existing, payload)
        diff_text = "\n".join(diffs) if diffs else "(payloads differ but no structured diff was produced)"

        if fail_on_drift:
            raise RuntimeError(
                f"Existing contract freeze differs from new payload at {out_path}\n"
                f"Contract drift is not allowed after freeze.\n\n"
                f"{diff_text}"
            )

        if not overwrite:
            raise RuntimeError(
                f"Existing contract freeze differs from new payload at {out_path}\n"
                f"Set overwrite=True and fail_on_drift=False if you intentionally want "
                f"to replace the contract before downstream benchmark freezing.\n\n"
                f"{diff_text}"
            )

    with out_path.open("w", encoding="utf-8") as f:
        f.write(_pretty_json(payload))

    return payload


# ============================================================
# Example CLI entrypoint
# ============================================================

def main() -> None:
    """
    Example usage:
    Freeze a deterministic item-item CF benchmark engine.
    Replace this with your actual frozen engine spec if you already
    have a canonical MovieLens replay engine from prior work.
    """
    repo_root = Path(__file__).resolve().parents[4]
    out_dir = repo_root / "results" / "frozen"
    out_path = out_dir / f"{BENCHMARK_ID}__contract_freeze.json"

    engine_spec = EngineSpec(
        engine_family="item_item_collaborative_filtering",
        engine_name="movielens_recursive_replay_engine",
        engine_version="1.0.0",
        deterministic=True,
        candidate_policy="exclude_seen_items_then_rank_all_remaining_items",
        update_policy=(
            "at each recursive step append one deterministically revealed frontier hit "
            "to observed profile; otherwise append nothing"
        ),
        tie_break_rule="score_desc_then_movieId_asc",
        hyperparameters={
            "similarity": "cosine",
            "neighborhood_size": 100,
            "score_aggregation": "weighted_sum",
            "min_common_raters": 1,
            "top_k": 10,
        },
        code_commit="4fe4f5f27b3f911b7cc1a0fbf29246dd6ce8b7f5",
        notes=(
            "Canonical public deterministic item-item collaborative-filtering replay "
            "engine for the MovieLens-25M recursive frontier benchmark."
        ),
    )

    payload = write_contract_freeze(
        out_path,
        engine_spec=engine_spec,
        notes="Initial canonical recommender benchmark contract freeze.",
        overwrite=True,
        fail_on_drift=False,
    )

    print(f"Wrote contract freeze to: {out_path}")
    print(f"benchmark_id: {payload['benchmark_id']}")
    print(f"engine_hash:  {payload['engine']['engine_hash']}")
    print(f"sha256:       {payload['contract_sha256']}")


if __name__ == "__main__":
    main()