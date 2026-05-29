from __future__ import annotations

import argparse
import csv
import functools
import gzip
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
CONTRACT_FILENAME = f"{BENCHMARK_ID}__contract_freeze.json"
PROVENANCE_FILENAME = f"{BENCHMARK_ID}__raw_input_provenance.json"
MANIFEST_FILENAME = f"{BENCHMARK_ID}__canonical_user_episode_manifest.csv"
SUMMARY_FILENAME = f"{BENCHMARK_ID}__canonical_user_episode_manifest_summary.json"


# ============================================================
# Repo paths
# ============================================================

@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=repo_root / "results" / "frozen",
        results_manifests=repo_root / "results" / "manifests",
    )


# ============================================================
# Frozen contract / provenance loading
# ============================================================

def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_contract(paths: RepoPaths) -> Dict:
    path = paths.results_frozen / CONTRACT_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Missing contract freeze: {path}\n"
            f"Run freeze_contract.py first."
        )
    contract = load_json(path)
    if contract.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in contract: {contract.get('benchmark_id')!r}"
        )
    return contract


def load_provenance(paths: RepoPaths) -> Dict:
    path = paths.results_manifests / PROVENANCE_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Missing raw input provenance manifest: {path}\n"
            f"Run raw_input_provenance.py first."
        )
    provenance = load_json(path)
    if provenance.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in provenance: {provenance.get('benchmark_id')!r}"
        )
    return provenance


# ============================================================
# Typed config extracted from contract
# ============================================================

@dataclass(frozen=True)
class BenchmarkConfig:
    warm_start_ratings: int
    positive_rating_threshold: float
    top_k: int
    max_horizon_steps: int
    collapse_streak_len: int
    remaining_frontier_floor: int
    min_warning_runway: int

    engine_family: str
    engine_name: str
    engine_version: str
    engine_hash: str
    deterministic: bool
    candidate_policy: str
    update_policy: str
    tie_break_rule: str
    neighborhood_size: int
    similarity: str
    score_aggregation: str
    min_common_raters: int

    contract_sha256: str


def parse_config(contract: Dict) -> BenchmarkConfig:
    collapse = contract["collapse"]
    engine = contract["engine"]

    if engine["engine_family"] != "item_item_collaborative_filtering":
        raise ValueError(
            f"This manifest builder currently expects engine_family="
            f"'item_item_collaborative_filtering', got {engine['engine_family']!r}"
        )

    hyper = engine["hyperparameters"]

    return BenchmarkConfig(
        warm_start_ratings=int(collapse["warm_start_ratings"]),
        positive_rating_threshold=float(collapse["positive_rating_threshold"]),
        top_k=int(collapse["top_k"]),
        max_horizon_steps=int(collapse["max_horizon_steps"]),
        collapse_streak_len=int(collapse["collapse_streak_len"]),
        remaining_frontier_floor=int(collapse["remaining_frontier_floor"]),
        min_warning_runway=int(collapse["min_warning_runway"]),
        engine_family=str(engine["engine_family"]),
        engine_name=str(engine["engine_name"]),
        engine_version=str(engine["engine_version"]),
        engine_hash=str(engine["engine_hash"]),
        deterministic=bool(engine["deterministic"]),
        candidate_policy=str(engine["candidate_policy"]),
        update_policy=str(engine["update_policy"]),
        tie_break_rule=str(engine["tie_break_rule"]),
        neighborhood_size=int(hyper["neighborhood_size"]),
        similarity=str(hyper["similarity"]),
        score_aggregation=str(hyper["score_aggregation"]),
        min_common_raters=int(hyper["min_common_raters"]),
        contract_sha256=str(contract["contract_sha256"]),
    )


# ============================================================
# User trajectory structures
# ============================================================

@dataclass(frozen=True)
class UserTrajectory:
    user_id: int
    movie_ids: np.ndarray      # shape [n]
    ratings: np.ndarray        # shape [n]
    timestamps: np.ndarray     # shape [n]

    @property
    def n_events(self) -> int:
        return int(len(self.movie_ids))


@dataclass(frozen=True)
class FrontierItem:
    movie_id: int
    rating: float
    timestamp: int


@dataclass
class EpisodeResult:
    user_id: int
    inclusion_status: str                 # included / excluded
    exclusion_reason: Optional[str]

    n_total_ratings: int
    n_positive_ratings_total: int
    warm_start_ratings: int
    warm_start_positive_count: int
    future_ratings_count: int
    frontier_start_size: int

    benchmark_horizon: int
    simulated_steps: int
    episode_end_step: Optional[int]

    label: Optional[str]                  # event / control / None
    collapse_step: Optional[int]
    collapse_criterion_met: Optional[bool]

    consecutive_miss_streak_at_end: Optional[int]
    remaining_frontier_at_end: Optional[int]
    recovered_frontier_hits: Optional[int]

    warning_runway_steps: Optional[int]
    natural_alarm_window_start_step: Optional[int]
    natural_alarm_window_end_step: Optional[int]

    engine_family: str
    engine_name: str
    engine_version: str
    engine_hash: str
    contract_sha256: str

    notes: Optional[str] = None

    def to_row(self) -> Dict[str, object]:
        return {
            "user_id": self.user_id,
            "inclusion_status": self.inclusion_status,
            "exclusion_reason": self.exclusion_reason,
            "n_total_ratings": self.n_total_ratings,
            "n_positive_ratings_total": self.n_positive_ratings_total,
            "warm_start_ratings": self.warm_start_ratings,
            "warm_start_positive_count": self.warm_start_positive_count,
            "future_ratings_count": self.future_ratings_count,
            "frontier_start_size": self.frontier_start_size,
            "benchmark_horizon": self.benchmark_horizon,
            "simulated_steps": self.simulated_steps,
            "episode_end_step": self.episode_end_step,
            "label": self.label,
            "collapse_step": self.collapse_step,
            "collapse_criterion_met": self.collapse_criterion_met,
            "consecutive_miss_streak_at_end": self.consecutive_miss_streak_at_end,
            "remaining_frontier_at_end": self.remaining_frontier_at_end,
            "recovered_frontier_hits": self.recovered_frontier_hits,
            "warning_runway_steps": self.warning_runway_steps,
            "natural_alarm_window_start_step": self.natural_alarm_window_start_step,
            "natural_alarm_window_end_step": self.natural_alarm_window_end_step,
            "engine_family": self.engine_family,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "engine_hash": self.engine_hash,
            "contract_sha256": self.contract_sha256,
            "notes": self.notes,
        }


# ============================================================
# Data loading and preprocessing
# ============================================================

def load_sorted_ratings(provenance: Dict) -> pd.DataFrame:
    sorted_path = provenance["sorted_ratings"]["path"]
    path = Path(sorted_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Sorted ratings file not found at {path}\n"
            f"Run raw_input_provenance.py again or inspect provenance manifest."
        )

    print(f"[load] sorted ratings: {path}")
    df = pd.read_csv(
        path,
        compression="gzip" if path.suffix == ".gz" else None,
        usecols=["userId", "movieId", "rating", "timestamp"],
        dtype={
            "userId": "int32",
            "movieId": "int32",
            "rating": "float32",
            "timestamp": "int64",
        },
    )
    return df


def build_user_trajectories_and_positive_index(
    df: pd.DataFrame,
    *,
    positive_threshold: float,
    max_users: Optional[int] = None,
) -> Tuple[
    Dict[int, UserTrajectory],
    Dict[int, Tuple[int, ...]],    # user_id -> positive movie ids (deduped)
    Dict[int, Tuple[int, ...]],    # movie_id -> users with positive rating
    Dict[int, int],                # movie_id -> positive-user count
]:
    """
    Build:
      - one full chronological trajectory per user
      - one deduped positive-item profile per user
      - one inverted index movie -> positive users
      - positive user-count per item

    Note:
    The sorted ratings input is already sorted by userId, timestamp, movieId.
    We preserve that order as the canonical replay order.
    """
    trajectories: Dict[int, UserTrajectory] = {}
    user_positive_items: Dict[int, Tuple[int, ...]] = {}
    item_to_users_tmp: Dict[int, List[int]] = defaultdict(list)
    item_positive_counts: Dict[int, int] = Counter()

    grouped = df.groupby("userId", sort=False)

    user_counter = 0
    for user_id, g in grouped:
        if max_users is not None and user_counter >= max_users:
            break

        movies = g["movieId"].to_numpy(dtype=np.int32, copy=True)
        ratings = g["rating"].to_numpy(dtype=np.float32, copy=True)
        timestamps = g["timestamp"].to_numpy(dtype=np.int64, copy=True)

        trajectories[int(user_id)] = UserTrajectory(
            user_id=int(user_id),
            movie_ids=movies,
            ratings=ratings,
            timestamps=timestamps,
        )

        # Dedup positive items in chronological order for recommender indexing
        seen = set()
        pos_items: List[int] = []
        for movie_id, rating in zip(movies, ratings):
            if rating >= positive_threshold and int(movie_id) not in seen:
                seen.add(int(movie_id))
                pos_items.append(int(movie_id))

        user_positive_items[int(user_id)] = tuple(pos_items)

        for movie_id in pos_items:
            item_to_users_tmp[int(movie_id)].append(int(user_id))
            item_positive_counts[int(movie_id)] += 1

        user_counter += 1
        if user_counter % 25000 == 0:
            print(f"[index] processed users: {user_counter}")

    item_to_users = {movie_id: tuple(user_ids) for movie_id, user_ids in item_to_users_tmp.items()}

    print(f"[index] built trajectories for {len(trajectories):,} users")
    print(f"[index] positive-index covers {len(item_to_users):,} items")
    return trajectories, user_positive_items, item_to_users, dict(item_positive_counts)


# ============================================================
# Deterministic frozen recommender
# ============================================================

class FrozenItemItemCFEngine:
    """
    Deterministic item-item collaborative filtering engine aligned with the
    contract currently frozen in freeze_contract.py.

    Scoring:
      - binary positive-feedback item-item cosine similarity
      - weighted_sum score aggregation over profile-positive items
      - top-N similar neighbors per profile item
      - exclude seen items
      - tie-break: score desc, movieId asc

    This is the benchmark engine used to construct episodes. It is intentionally
    deterministic and public-facing.
    """

    def __init__(
        self,
        *,
        user_positive_items: Dict[int, Tuple[int, ...]],
        item_to_users: Dict[int, Tuple[int, ...]],
        item_positive_counts: Dict[int, int],
        neighborhood_size: int,
        min_common_raters: int,
        top_k: int,
        tie_break_rule: str,
    ) -> None:
        self.user_positive_items = user_positive_items
        self.item_to_users = item_to_users
        self.item_positive_counts = item_positive_counts
        self.neighborhood_size = neighborhood_size
        self.min_common_raters = min_common_raters
        self.top_k = top_k
        self.tie_break_rule = tie_break_rule

        self._neighbor_cache: Dict[int, Tuple[Tuple[int, float], ...]] = {}

        # Explicit frozen tie-break contract:
        # score_desc_then_movieId_asc
        self.tie_break_rule_score_desc_movieId_asc = "score_desc_then_movieId_asc"

        # Deterministic global popularity fallback:
        # popularity_desc_then_movieId_asc
        self.global_popularity_fallback_rule = "popularity_desc_then_movieId_asc"
        self._global_popularity = tuple(
            sorted(
                self.item_positive_counts.items(),
                key=lambda kv: (-kv[1], kv[0]),
            )
        )

    def _top_neighbors(self, movie_id: int) -> Tuple[Tuple[int, float], ...]:
        """
        Returns cached top neighbors:
          ((neighbor_movie_id, similarity_score), ...)
        """
        cached = self._neighbor_cache.get(movie_id)
        if cached is not None:
            return cached

        users = self.item_to_users.get(movie_id, ())
        pop_i = self.item_positive_counts.get(movie_id, 0)

        if pop_i == 0 or not users:
            self._neighbor_cache[movie_id] = ()
            return ()

        co_counts: Dict[int, int] = Counter()

        for user_id in users:
            for other_movie_id in self.user_positive_items[user_id]:
                if other_movie_id == movie_id:
                    continue
                co_counts[other_movie_id] += 1

        scored: List[Tuple[int, float]] = []
        for other_movie_id, common in co_counts.items():
            if common < self.min_common_raters:
                continue
            pop_j = self.item_positive_counts.get(other_movie_id, 0)
            if pop_j <= 0:
                continue

            # Cosine on binary positive-rater incidence
            sim = common / math.sqrt(pop_i * pop_j)
            scored.append((other_movie_id, sim))

        if self.tie_break_rule != "score_desc_then_movieId_asc":
            raise ValueError(
                f"Unsupported tie_break_rule for frozen benchmark engine: {self.tie_break_rule!r}"
            )

        scored.sort(key=lambda x: (-x[1], x[0]))
        top = tuple(scored[: self.neighborhood_size])
        self._neighbor_cache[movie_id] = top
        return top

    def recommend(
        self,
        *,
        positive_profile_items: Sequence[int],
        seen_items: set[int],
    ) -> List[int]:
        """
        Recommend top_k items under the contract:
          - aggregate neighbors from profile-positive items
          - exclude seen items
          - fallback to global popularity if no scored candidates
          - tie-break score desc then movieId asc
        """
        if self.tie_break_rule != "score_desc_then_movieId_asc":
            raise ValueError(
                f"Unsupported tie_break_rule for frozen benchmark engine: {self.tie_break_rule!r}"
            )

        scores: Dict[int, float] = defaultdict(float)

        if positive_profile_items:
            for movie_id in positive_profile_items:
                for cand_movie_id, sim in self._top_neighbors(int(movie_id)):
                    if cand_movie_id in seen_items:
                        continue
                    scores[cand_movie_id] += sim

        if scores:
            ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
            return [movie_id for movie_id, _ in ranked[: self.top_k]]

        # deterministic global popularity fallback
        out: List[int] = []
        global_popularity = self._global_popularity
        for movie_id, _count in global_popularity:
            if movie_id in seen_items:
                continue
            out.append(movie_id)
            if len(out) >= self.top_k:
                break
        return out


# ============================================================
# Episode construction
# ============================================================

def choose_frontier_hit(
    candidate_movie_ids: Sequence[int],
    frontier: Dict[int, FrontierItem],
) -> FrontierItem:
    """
    Deterministic reveal rule from contract:
      highest_rating_then_earliest_true_timestamp_then_lowest_movieId
    """
    candidates = [frontier[int(movie_id)] for movie_id in candidate_movie_ids if int(movie_id) in frontier]
    if not candidates:
        raise ValueError("choose_frontier_hit called with no valid frontier candidates")

    return sorted(
        candidates,
        key=lambda x: (-x.rating, x.timestamp, x.movie_id),
    )[0]


def simulate_user_episode(
    traj: UserTrajectory,
    *,
    cfg: BenchmarkConfig,
    engine: FrozenItemItemCFEngine,
) -> EpisodeResult:
    movies = traj.movie_ids
    ratings = traj.ratings
    timestamps = traj.timestamps

    n_total = int(len(movies))
    positive_mask_all = ratings >= cfg.positive_rating_threshold
    n_pos_total = int(np.sum(positive_mask_all))

    if n_total <= cfg.warm_start_ratings:
        return EpisodeResult(
            user_id=traj.user_id,
            inclusion_status="excluded",
            exclusion_reason="insufficient_total_ratings_for_warm_start",
            n_total_ratings=n_total,
            n_positive_ratings_total=n_pos_total,
            warm_start_ratings=cfg.warm_start_ratings,
            warm_start_positive_count=0,
            future_ratings_count=max(0, n_total - cfg.warm_start_ratings),
            frontier_start_size=0,
            benchmark_horizon=cfg.max_horizon_steps,
            simulated_steps=0,
            episode_end_step=None,
            label=None,
            collapse_step=None,
            collapse_criterion_met=None,
            consecutive_miss_streak_at_end=None,
            remaining_frontier_at_end=None,
            recovered_frontier_hits=None,
            warning_runway_steps=None,
            natural_alarm_window_start_step=None,
            natural_alarm_window_end_step=None,
            engine_family=cfg.engine_family,
            engine_name=cfg.engine_name,
            engine_version=cfg.engine_version,
            engine_hash=cfg.engine_hash,
            contract_sha256=cfg.contract_sha256,
            notes=None,
        )

    warm_slice = slice(0, cfg.warm_start_ratings)
    future_slice = slice(cfg.warm_start_ratings, None)

    warm_movies = movies[warm_slice]
    warm_ratings = ratings[warm_slice]

    future_movies = movies[future_slice]
    future_ratings = ratings[future_slice]
    future_timestamps = timestamps[future_slice]

    warm_positive_profile: List[int] = []
    warm_positive_seen = set()
    for movie_id, rating in zip(warm_movies, warm_ratings):
        if rating >= cfg.positive_rating_threshold and int(movie_id) not in warm_positive_seen:
            warm_positive_seen.add(int(movie_id))
            warm_positive_profile.append(int(movie_id))

    # Build initial frontier from future positive items, deduped by movieId using earliest future timestamp
    frontier: Dict[int, FrontierItem] = {}
    for movie_id, rating, ts in zip(future_movies, future_ratings, future_timestamps):
        movie_id = int(movie_id)
        rating = float(rating)
        ts = int(ts)
        if rating < cfg.positive_rating_threshold:
            continue
        current = frontier.get(movie_id)
        if current is None:
            frontier[movie_id] = FrontierItem(movie_id=movie_id, rating=rating, timestamp=ts)
        else:
            # keep better item by the same deterministic reveal priority
            better = sorted(
                [current, FrontierItem(movie_id=movie_id, rating=rating, timestamp=ts)],
                key=lambda x: (-x.rating, x.timestamp, x.movie_id),
            )[0]
            frontier[movie_id] = better

    frontier_start_size = len(frontier)
    future_ratings_count = int(len(future_movies))
    warm_start_positive_count = len(warm_positive_profile)

    if frontier_start_size < cfg.remaining_frontier_floor:
        return EpisodeResult(
            user_id=traj.user_id,
            inclusion_status="excluded",
            exclusion_reason="initial_frontier_below_remaining_frontier_floor",
            n_total_ratings=n_total,
            n_positive_ratings_total=n_pos_total,
            warm_start_ratings=cfg.warm_start_ratings,
            warm_start_positive_count=warm_start_positive_count,
            future_ratings_count=future_ratings_count,
            frontier_start_size=frontier_start_size,
            benchmark_horizon=cfg.max_horizon_steps,
            simulated_steps=0,
            episode_end_step=None,
            label=None,
            collapse_step=None,
            collapse_criterion_met=None,
            consecutive_miss_streak_at_end=None,
            remaining_frontier_at_end=None,
            recovered_frontier_hits=None,
            warning_runway_steps=None,
            natural_alarm_window_start_step=None,
            natural_alarm_window_end_step=None,
            engine_family=cfg.engine_family,
            engine_name=cfg.engine_name,
            engine_version=cfg.engine_version,
            engine_hash=cfg.engine_hash,
            contract_sha256=cfg.contract_sha256,
            notes=None,
        )

    seen_items: set[int] = set(int(x) for x in warm_movies.tolist())
    positive_profile_items: List[int] = list(warm_positive_profile)

    consecutive_misses = 0
    recovered_hits = 0
    collapse_step: Optional[int] = None
    simulated_steps = 0

    for step in range(1, cfg.max_horizon_steps + 1):
        simulated_steps = step

        recs = engine.recommend(
            positive_profile_items=positive_profile_items,
            seen_items=seen_items,
        )

        hit_candidates = [movie_id for movie_id in recs if movie_id in frontier]

        if hit_candidates:
            revealed = choose_frontier_hit(hit_candidates, frontier)
            del frontier[revealed.movie_id]

            recovered_hits += 1
            consecutive_misses = 0

            seen_items.add(revealed.movie_id)
            if revealed.movie_id not in positive_profile_items:
                positive_profile_items.append(revealed.movie_id)
        else:
            consecutive_misses += 1

        remaining_frontier = len(frontier)

        if (
            consecutive_misses >= cfg.collapse_streak_len
            and remaining_frontier >= cfg.remaining_frontier_floor
        ):
            collapse_step = step
            break

        if remaining_frontier == 0:
            break

    episode_end_step = simulated_steps
    remaining_frontier_at_end = len(frontier)
    warning_runway_steps = None
    natural_alarm_window_start_step = None
    natural_alarm_window_end_step = None
    label = None
    inclusion_status = "included"
    exclusion_reason = None
    collapse_met = collapse_step is not None

    if collapse_step is not None:
        warning_runway_steps = collapse_step - 1
        if warning_runway_steps < cfg.min_warning_runway:
            inclusion_status = "excluded"
            exclusion_reason = "collapse_before_min_warning_runway"
        else:
            label = "event"
            natural_alarm_window_start_step = 1
            natural_alarm_window_end_step = collapse_step - 1
    else:
        warning_runway_steps = episode_end_step
        if episode_end_step < cfg.min_warning_runway:
            inclusion_status = "excluded"
            exclusion_reason = "episode_too_short_for_min_warning_runway"
        else:
            label = "control"
            natural_alarm_window_start_step = 1
            natural_alarm_window_end_step = episode_end_step

    if inclusion_status == "excluded":
        label = None
        collapse_met = None
        warning_runway_steps = None
        natural_alarm_window_start_step = None
        natural_alarm_window_end_step = None

    return EpisodeResult(
        user_id=traj.user_id,
        inclusion_status=inclusion_status,
        exclusion_reason=exclusion_reason,
        n_total_ratings=n_total,
        n_positive_ratings_total=n_pos_total,
        warm_start_ratings=cfg.warm_start_ratings,
        warm_start_positive_count=warm_start_positive_count,
        future_ratings_count=future_ratings_count,
        frontier_start_size=frontier_start_size,
        benchmark_horizon=cfg.max_horizon_steps,
        simulated_steps=simulated_steps,
        episode_end_step=episode_end_step,
        label=label,
        collapse_step=collapse_step if inclusion_status == "included" else None,
        collapse_criterion_met=collapse_met,
        consecutive_miss_streak_at_end=consecutive_misses if inclusion_status == "included" else None,
        remaining_frontier_at_end=remaining_frontier_at_end if inclusion_status == "included" else None,
        recovered_frontier_hits=recovered_hits if inclusion_status == "included" else None,
        warning_runway_steps=warning_runway_steps,
        natural_alarm_window_start_step=natural_alarm_window_start_step,
        natural_alarm_window_end_step=natural_alarm_window_end_step,
        engine_family=cfg.engine_family,
        engine_name=cfg.engine_name,
        engine_version=cfg.engine_version,
        engine_hash=cfg.engine_hash,
        contract_sha256=cfg.contract_sha256,
        notes=None if inclusion_status == "included" else "Excluded before comparator calibration.",
    )


# ============================================================
# Manifest builder
# ============================================================

def build_manifest_rows(
    *,
    trajectories: Dict[int, UserTrajectory],
    cfg: BenchmarkConfig,
    engine: FrozenItemItemCFEngine,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    n_users = len(trajectories)
    for idx, user_id in enumerate(sorted(trajectories.keys()), start=1):
        result = simulate_user_episode(
            trajectories[user_id],
            cfg=cfg,
            engine=engine,
        )
        rows.append(result.to_row())

        if idx % 1000 == 0:
            print(f"[episodes] built {idx:,}/{n_users:,} user episodes")

    return rows


def write_manifest_csv(rows: List[Dict[str, object]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    print(f"[ok] wrote canonical manifest CSV: {out_path}")


def build_summary(rows: List[Dict[str, object]], *, cfg: BenchmarkConfig) -> Dict[str, object]:
    df = pd.DataFrame(rows)

    included = df[df["inclusion_status"] == "included"].copy()
    events = included[included["label"] == "event"].copy()
    controls = included[included["label"] == "control"].copy()
    excluded = df[df["inclusion_status"] == "excluded"].copy()

    exclusion_counts = (
        excluded["exclusion_reason"].fillna("unknown").value_counts().sort_index().to_dict()
    )

    summary: Dict[str, object] = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "canonical_user_episode_manifest",
        "contract_sha256": cfg.contract_sha256,
        "engine_hash": cfg.engine_hash,
        "engine_family": cfg.engine_family,
        "engine_name": cfg.engine_name,
        "engine_version": cfg.engine_version,
        "n_total_users_processed": int(len(df)),
        "n_included_units": int(len(included)),
        "n_event_units": int(len(events)),
        "n_control_units": int(len(controls)),
        "n_excluded_units": int(len(excluded)),
        "exclusion_counts": exclusion_counts,
        "canonical_constants": {
            "warm_start_ratings": cfg.warm_start_ratings,
            "positive_rating_threshold": cfg.positive_rating_threshold,
            "top_k": cfg.top_k,
            "max_horizon_steps": cfg.max_horizon_steps,
            "collapse_streak_len": cfg.collapse_streak_len,
            "remaining_frontier_floor": cfg.remaining_frontier_floor,
            "min_warning_runway": cfg.min_warning_runway,
        },
    }

    if len(controls) > 0:
        summary["control_fp_grid_step"] = 1.0 / float(len(controls))
    else:
        summary["control_fp_grid_step"] = None

    if len(events) > 0:
        summary["event_collapse_step"] = {
            "min": int(events["collapse_step"].min()),
            "median": float(events["collapse_step"].median()),
            "max": int(events["collapse_step"].max()),
        }
        summary["event_warning_runway_steps"] = {
            "min": int(events["warning_runway_steps"].min()),
            "median": float(events["warning_runway_steps"].median()),
            "max": int(events["warning_runway_steps"].max()),
        }

    if len(controls) > 0:
        summary["control_episode_end_step"] = {
            "min": int(controls["episode_end_step"].min()),
            "median": float(controls["episode_end_step"].median()),
            "max": int(controls["episode_end_step"].max()),
        }

    return summary


def write_summary_json(summary: Dict[str, object], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[ok] wrote canonical manifest summary JSON: {out_path}")


# ============================================================
# Main
# ============================================================

def run(
    *,
    repo_root: Path,
    max_users: Optional[int] = None,
) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    contract = load_contract(paths)
    provenance = load_provenance(paths)
    cfg = parse_config(contract)

    df = load_sorted_ratings(provenance)

    trajectories, user_positive_items, item_to_users, item_positive_counts = (
        build_user_trajectories_and_positive_index(
            df,
            positive_threshold=cfg.positive_rating_threshold,
            max_users=max_users,
        )
    )

    print("[engine] initializing deterministic frozen item-item CF engine")
    engine = FrozenItemItemCFEngine(
        user_positive_items=user_positive_items,
        item_to_users=item_to_users,
        item_positive_counts=item_positive_counts,
        neighborhood_size=cfg.neighborhood_size,
        min_common_raters=cfg.min_common_raters,
        top_k=cfg.top_k,
        tie_break_rule=cfg.tie_break_rule,
    )

    rows = build_manifest_rows(
        trajectories=trajectories,
        cfg=cfg,
        engine=engine,
    )

    manifest_path = paths.results_manifests / MANIFEST_FILENAME
    summary_path = paths.results_manifests / SUMMARY_FILENAME

    write_manifest_csv(rows, manifest_path)
    summary = build_summary(rows, cfg=cfg)
    write_summary_json(summary, summary_path)

    print("[done] canonical user-episode manifest build complete")
    print(f"[done] manifest: {manifest_path}")
    print(f"[done] summary:  {summary_path}")
    return manifest_path, summary_path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build canonical user-episode manifest for MovieLens-25M recommender benchmark."
    )
    p.add_argument(
        "--max-users",
        type=int,
        default=None,
        help="Optional smoke-test limit on number of users to process.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[4]
    run(
        repo_root=repo_root,
        max_users=args.max_users,
    )


if __name__ == "__main__":
    main()