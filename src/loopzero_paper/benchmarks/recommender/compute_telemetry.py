

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
CONTRACT_FILENAME = f"{BENCHMARK_ID}__contract_freeze.json"
BENCHMARK_FREEZE_FILENAME = f"{BENCHMARK_ID}__benchmark_freeze_state.json"
PROVENANCE_FILENAME = f"{BENCHMARK_ID}__raw_input_provenance.json"
MANIFEST_FILENAME = f"{BENCHMARK_ID}__canonical_user_episode_manifest.csv"

TELEMETRY_PANEL_FILENAME = f"{BENCHMARK_ID}__telemetry_panel.csv.gz"
TELEMETRY_SUMMARY_FILENAME = f"{BENCHMARK_ID}__telemetry_summary.json"

PREC_COLLAPSE_WINDOW = 10
SELF_REINFORCEMENT_ABLATION_WINDOW = 5
EPS = 1e-9


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    contract_path: Path
    benchmark_freeze_path: Path
    provenance_path: Path
    manifest_path: Path


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
    benchmark_freeze_sha256: str


@dataclass(frozen=True)
class UserTrajectory:
    user_id: int
    movie_ids: np.ndarray
    ratings: np.ndarray
    timestamps: np.ndarray


@dataclass(frozen=True)
class FrontierItem:
    movie_id: int
    rating: float
    timestamp: int


@dataclass(frozen=True)
class EpisodeMeta:
    user_id: int
    label: str
    collapse_step: Optional[int]
    natural_alarm_window_start_step: int
    natural_alarm_window_end_step: int


class FrozenItemItemCFEngine:
    """
    Mirror of the frozen canonical benchmark engine used in build_user_episode_manifest.py.
    Keep this implementation behaviorally aligned with the frozen engine spec and audit.
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
        self._item_user_sets: Dict[int, set[int]] = {
            int(movie_id): set(user_ids)
            for movie_id, user_ids in self.item_to_users.items()
        }
        self._pairwise_similarity_cache: Dict[Tuple[int, int], float] = {}

        self.tie_break_rule_score_desc_movieId_asc = "score_desc_then_movieId_asc"
        self.global_popularity_fallback_rule = "popularity_desc_then_movieId_asc"
        self._global_popularity = tuple(
            sorted(
                self.item_positive_counts.items(),
                key=lambda kv: (-kv[1], kv[0]),
            )
        )

    def _top_neighbors(self, movie_id: int) -> Tuple[Tuple[int, float], ...]:
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

        out: List[int] = []
        global_popularity = self._global_popularity
        for movie_id, _count in global_popularity:
            if movie_id in seen_items:
                continue
            out.append(movie_id)
            if len(out) >= self.top_k:
                break
        return out

    def warm_neighbor_cache(
        self,
        seed_movie_ids: Sequence[int],
        *,
        progress_every: int = 250,
    ) -> None:
        unique_ids = sorted({int(movie_id) for movie_id in seed_movie_ids})
        total = len(unique_ids)
        if total == 0:
            print("[engine] no seed movie ids supplied for neighbor-cache warmup")
            return

        print(f"[engine] warming neighbor cache for {total:,} seed items")
        for idx, movie_id in enumerate(unique_ids, start=1):
            self._top_neighbors(int(movie_id))
            if idx % progress_every == 0 or idx == total:
                print(f"[engine] warmed {idx:,}/{total:,} seed items")


def build_repo_paths(repo_root: Path) -> RepoPaths:
    results_frozen = repo_root / "results" / "frozen"
    results_manifests = repo_root / "results" / "manifests"
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=results_frozen,
        results_manifests=results_manifests,
        contract_path=results_frozen / CONTRACT_FILENAME,
        benchmark_freeze_path=results_frozen / BENCHMARK_FREEZE_FILENAME,
        provenance_path=results_manifests / PROVENANCE_FILENAME,
        manifest_path=results_manifests / MANIFEST_FILENAME,
    )


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ensure_inputs(paths: RepoPaths) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], pd.DataFrame]:
    missing = [
        str(path)
        for path in [
            paths.contract_path,
            paths.benchmark_freeze_path,
            paths.provenance_path,
            paths.manifest_path,
        ]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required telemetry inputs:\n- " + "\n- ".join(missing))

    contract = load_json(paths.contract_path)
    benchmark_freeze = load_json(paths.benchmark_freeze_path)
    provenance = load_json(paths.provenance_path)
    manifest_df = pd.read_csv(paths.manifest_path)

    if contract.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(f"Unexpected benchmark_id in contract: {contract.get('benchmark_id')!r}")
    if benchmark_freeze.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(f"Unexpected benchmark_id in benchmark freeze: {benchmark_freeze.get('benchmark_id')!r}")
    if provenance.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(f"Unexpected benchmark_id in provenance: {provenance.get('benchmark_id')!r}")

    frozen_contract = benchmark_freeze.get("frozen_inputs", {}).get("contract", {})
    if frozen_contract.get("contract_sha256") != contract.get("contract_sha256"):
        raise ValueError(
            "Contract SHA mismatch between current contract freeze and benchmark freeze state."
        )

    frozen_manifest = benchmark_freeze.get("frozen_inputs", {}).get("canonical_manifest", {})
    observed_manifest_sha = sha256_file(paths.manifest_path)
    if frozen_manifest.get("sha256") != observed_manifest_sha:
        raise ValueError(
            "Canonical manifest SHA mismatch between current manifest and benchmark freeze state."
        )

    return contract, benchmark_freeze, provenance, manifest_df


def parse_config(contract: Dict[str, Any], benchmark_freeze: Dict[str, Any]) -> BenchmarkConfig:
    collapse = contract["collapse"]
    engine = contract["engine"]
    hyper = engine["hyperparameters"]

    if engine["engine_hash"] != benchmark_freeze["frozen_contract"]["engine_hash"]:
        raise ValueError("Engine hash mismatch between contract and benchmark freeze state.")

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
        benchmark_freeze_sha256=str(benchmark_freeze["benchmark_freeze_sha256"]),
    )


def load_sorted_ratings(provenance: Dict[str, Any]) -> pd.DataFrame:
    sorted_path = Path(provenance["sorted_ratings"]["path"])
    if not sorted_path.exists():
        raise FileNotFoundError(f"Sorted ratings file not found: {sorted_path}")

    print(f"[load] sorted ratings: {sorted_path}")
    df = pd.read_csv(
        sorted_path,
        compression="gzip" if sorted_path.suffix == ".gz" else None,
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
) -> Tuple[
    Dict[int, UserTrajectory],
    Dict[int, Tuple[int, ...]],
    Dict[int, Tuple[int, ...]],
    Dict[int, int],
]:
    trajectories: Dict[int, UserTrajectory] = {}
    user_positive_items: Dict[int, Tuple[int, ...]] = {}
    item_to_users_tmp: Dict[int, List[int]] = defaultdict(list)
    item_positive_counts: Dict[int, int] = Counter()

    grouped = df.groupby("userId", sort=False)

    user_counter = 0
    for user_id, g in grouped:
        movies = g["movieId"].to_numpy(dtype=np.int32, copy=True)
        ratings = g["rating"].to_numpy(dtype=np.float32, copy=True)
        timestamps = g["timestamp"].to_numpy(dtype=np.int64, copy=True)

        uid = int(user_id)
        trajectories[uid] = UserTrajectory(
            user_id=uid,
            movie_ids=movies,
            ratings=ratings,
            timestamps=timestamps,
        )

        seen = set()
        pos_items: List[int] = []
        for movie_id, rating in zip(movies, ratings):
            mid = int(movie_id)
            if rating >= positive_threshold and mid not in seen:
                seen.add(mid)
                pos_items.append(mid)

        user_positive_items[uid] = tuple(pos_items)
        for movie_id in pos_items:
            item_to_users_tmp[movie_id].append(uid)
            item_positive_counts[movie_id] += 1

        user_counter += 1
        if user_counter % 25000 == 0:
            print(f"[index] processed users: {user_counter}")

    item_to_users = {movie_id: tuple(user_ids) for movie_id, user_ids in item_to_users_tmp.items()}

    print(f"[index] built trajectories for {len(trajectories):,} users")
    print(f"[index] positive-index covers {len(item_to_users):,} items")
    return trajectories, user_positive_items, item_to_users, dict(item_positive_counts)


def choose_frontier_hit(candidate_movie_ids: Sequence[int], frontier: Dict[int, FrontierItem]) -> FrontierItem:
    candidates = [frontier[int(movie_id)] for movie_id in candidate_movie_ids if int(movie_id) in frontier]
    if not candidates:
        raise ValueError("choose_frontier_hit called with no valid frontier candidates")

    return sorted(
        candidates,
        key=lambda x: (-x.rating, x.timestamp, x.movie_id),
    )[0]


def jaccard_topk(prev_recs: Sequence[int], curr_recs: Sequence[int]) -> float:
    a = set(int(x) for x in prev_recs)
    b = set(int(x) for x in curr_recs)
    if not a and not b:
        return 1.0
    denom = len(a | b)
    if denom == 0:
        return 1.0
    return len(a & b) / denom




def item_cosine_similarity(engine: FrozenItemItemCFEngine, movie_a: int, movie_b: int) -> float:
    a = int(movie_a)
    b = int(movie_b)

    if a == b:
        return 1.0

    key = (a, b) if a < b else (b, a)
    cached = engine._pairwise_similarity_cache.get(key)
    if cached is not None:
        return cached

    users_a = engine._item_user_sets.get(a, set())
    users_b = engine._item_user_sets.get(b, set())
    pop_a = engine.item_positive_counts.get(a, 0)
    pop_b = engine.item_positive_counts.get(b, 0)

    if pop_a <= 0 or pop_b <= 0 or not users_a or not users_b:
        engine._pairwise_similarity_cache[key] = 0.0
        return 0.0

    common = len(users_a & users_b)
    if common <= 0:
        engine._pairwise_similarity_cache[key] = 0.0
        return 0.0

    sim = common / math.sqrt(pop_a * pop_b)
    engine._pairwise_similarity_cache[key] = sim
    return sim


# Diversity proxy uses adjacent-pair similarity across the ranked recommendation list
# rather than full pairwise top-k similarity. This keeps the proxy aligned with
# recommendation-list concentration while avoiding the much higher O(k^2) cost of
# full pairwise similarity at every replay step.
def diversity_proxy(recs: Sequence[int], engine: FrozenItemItemCFEngine) -> float:
    rec_list = [int(mid) for mid in recs]
    if len(rec_list) <= 1:
        return 1.0 if rec_list else 0.0

    sims: List[float] = []
    for i in range(len(rec_list) - 1):
        sims.append(item_cosine_similarity(engine, rec_list[i], rec_list[i + 1]))

    if not sims:
        return 1.0

    mean_similarity = float(np.mean(sims))
    return float(max(0.0, min(1.0, 1.0 - mean_similarity)))


def reinforcement_proxy(
    recs_full: Sequence[int],
    recs_ablated: Sequence[int],
) -> float:
    if not recs_full:
        return 0.0
    return float(max(0.0, min(1.0, 1.0 - jaccard_topk(recs_full, recs_ablated))))


def amplification_proxy(prev_recs: Sequence[int], curr_recs: Sequence[int]) -> float:
    if not curr_recs:
        return 0.0
    if not prev_recs:
        return 0.0

    stability = jaccard_topk(prev_recs, curr_recs)
    gain = 1.0 - stability
    return float(max(0.0, min(1.0, gain)))


def simulate_user_telemetry(
    traj: UserTrajectory,
    episode_meta: EpisodeMeta,
    *,
    cfg: BenchmarkConfig,
    engine: FrozenItemItemCFEngine,
) -> List[Dict[str, Any]]:
    movies = traj.movie_ids
    ratings = traj.ratings
    timestamps = traj.timestamps

    warm_slice = slice(0, cfg.warm_start_ratings)
    future_slice = slice(cfg.warm_start_ratings, None)

    warm_movies = movies[warm_slice]
    warm_ratings = ratings[warm_slice]
    future_movies = movies[future_slice]
    future_ratings = ratings[future_slice]
    future_timestamps = timestamps[future_slice]

    positive_profile_items: List[int] = []
    warm_positive_seen = set()
    for movie_id, rating in zip(warm_movies, warm_ratings):
        mid = int(movie_id)
        if rating >= cfg.positive_rating_threshold and mid not in warm_positive_seen:
            warm_positive_seen.add(mid)
            positive_profile_items.append(mid)

    frontier: Dict[int, FrontierItem] = {}
    for movie_id, rating, ts in zip(future_movies, future_ratings, future_timestamps):
        mid = int(movie_id)
        r = float(rating)
        t = int(ts)
        if r < cfg.positive_rating_threshold:
            continue
        current = frontier.get(mid)
        candidate = FrontierItem(movie_id=mid, rating=r, timestamp=t)
        if current is None:
            frontier[mid] = candidate
        else:
            frontier[mid] = sorted([current, candidate], key=lambda x: (-x.rating, x.timestamp, x.movie_id))[0]

    seen_items: set[int] = set(int(x) for x in warm_movies.tolist())
    self_generated_items: List[int] = []
    rows: List[Dict[str, Any]] = []
    prev_recs: List[int] = []
    consecutive_misses = 0

    end_step = int(episode_meta.natural_alarm_window_end_step)
    if episode_meta.label == "event" and episode_meta.collapse_step is not None:
        replay_end = int(episode_meta.collapse_step)
    else:
        replay_end = end_step

    for step in range(1, replay_end + 1):
        frontier_before = len(frontier)
        recs = engine.recommend(
            positive_profile_items=positive_profile_items,
            seen_items=seen_items,
        )

        hit_candidates = [movie_id for movie_id in recs if movie_id in frontier]
        hit_this_step = 1 if hit_candidates else 0
        recovered_movie_id: Optional[int] = None

        recent_self_generated = self_generated_items[-min(SELF_REINFORCEMENT_ABLATION_WINDOW, len(self_generated_items)):]
        if recent_self_generated:
            ablated_recent = set(int(x) for x in recent_self_generated)
            ablated_profile_items = [
                int(mid) for mid in positive_profile_items
                if int(mid) not in ablated_recent
            ]
            recs_ablated = engine.recommend(
                positive_profile_items=ablated_profile_items,
                seen_items=seen_items,
            )
        else:
            recs_ablated = list(recs)

        G = amplification_proxy(prev_recs, recs)
        p = reinforcement_proxy(recs, recs_ablated)
        delta = diversity_proxy(recs, engine)

        if hit_candidates:
            revealed = choose_frontier_hit(hit_candidates, frontier)
            recovered_movie_id = revealed.movie_id
            del frontier[revealed.movie_id]
            consecutive_misses = 0
            seen_items.add(revealed.movie_id)
            if revealed.movie_id not in positive_profile_items:
                positive_profile_items.append(revealed.movie_id)
            self_generated_items.append(revealed.movie_id)
        else:
            consecutive_misses += 1

        frontier_after = len(frontier)
        collapse_step = episode_meta.collapse_step
        if episode_meta.label == "event" and collapse_step is not None:
            steps_to_collapse = collapse_step - step
            is_precollapse_window = 0 <= steps_to_collapse < PREC_COLLAPSE_WINDOW
            aligned_step = steps_to_collapse
        else:
            steps_to_collapse = None
            is_precollapse_window = step > (end_step - PREC_COLLAPSE_WINDOW)
            aligned_step = -(end_step - step)

        rows.append(
            {
                "user_id": episode_meta.user_id,
                "label": episode_meta.label,
                "step": step,
                "aligned_step": int(aligned_step),
                "collapse_step": collapse_step,
                "steps_to_collapse": steps_to_collapse,
                "natural_alarm_window_start_step": int(episode_meta.natural_alarm_window_start_step),
                "natural_alarm_window_end_step": int(episode_meta.natural_alarm_window_end_step),
                "is_precollapse_window": bool(is_precollapse_window),
                "G": float(G),
                "p": float(p),
                "delta": float(delta),
                "frontier_size_before": int(frontier_before),
                "frontier_size_after": int(frontier_after),
                "hit_this_step": int(hit_this_step),
                "consecutive_misses_after_step": int(consecutive_misses),
                "recovered_movie_id": recovered_movie_id,
                "topk_size": int(len(recs)),
                "profile_positive_size_after_step": int(len(positive_profile_items)),
                "engine_hash": cfg.engine_hash,
                "contract_sha256": cfg.contract_sha256,
                "benchmark_freeze_sha256": cfg.benchmark_freeze_sha256,
            }
        )
        prev_recs = list(recs)

        if (
            episode_meta.label == "event"
            and collapse_step is not None
            and step >= collapse_step
        ):
            break

    return rows


def build_episode_meta(manifest_df: pd.DataFrame) -> List[EpisodeMeta]:
    included = manifest_df[manifest_df["inclusion_status"] == "included"].copy()
    metas: List[EpisodeMeta] = []
    for _, row in included.iterrows():
        metas.append(
            EpisodeMeta(
                user_id=int(row["user_id"]),
                label=str(row["label"]),
                collapse_step=None if pd.isna(row["collapse_step"]) else int(row["collapse_step"]),
                natural_alarm_window_start_step=int(row["natural_alarm_window_start_step"]),
                natural_alarm_window_end_step=int(row["natural_alarm_window_end_step"]),
            )
        )
    return metas

def build_included_seed_item_universe(
    metas: Sequence[EpisodeMeta],
    user_positive_items: Dict[int, Tuple[int, ...]],
) -> List[int]:
    seed_items: set[int] = set()
    for meta in metas:
        for movie_id in user_positive_items.get(int(meta.user_id), ()):
            seed_items.add(int(movie_id))
    return sorted(seed_items)


def write_panel(rows: List[Dict[str, Any]], out_path: Path) -> pd.DataFrame:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False, compression="gzip")
    print(f"[ok] wrote telemetry panel: {out_path}")
    return df


def summarize_group_means(df: pd.DataFrame, *, mask: pd.Series, label: str) -> Dict[str, Any]:
    sub = df[mask].copy()
    if len(sub) == 0:
        return {
            "label": label,
            "n_rows": 0,
            "G_mean": None,
            "p_mean": None,
            "delta_mean": None,
        }
    return {
        "label": label,
        "n_rows": int(len(sub)),
        "G_mean": float(sub["G"].mean()),
        "p_mean": float(sub["p"].mean()),
        "delta_mean": float(sub["delta"].mean()),
    }


def build_summary(df: pd.DataFrame, *, cfg: BenchmarkConfig, benchmark_freeze: Dict[str, Any]) -> Dict[str, Any]:
    event_mask = df["label"] == "event"
    control_mask = df["label"] == "control"
    precollapse_mask = df["is_precollapse_window"] == True

    summary = {
        "benchmark_id": BENCHMARK_ID,
        "stage": "compute_telemetry",
        "contract_sha256": cfg.contract_sha256,
        "benchmark_freeze_sha256": cfg.benchmark_freeze_sha256,
        "engine_hash": cfg.engine_hash,
        "precollapse_window": PREC_COLLAPSE_WINDOW,
        "n_panel_rows": int(len(df)),
        "n_unique_users": int(df["user_id"].nunique()),
        "n_event_users": int(df.loc[event_mask, "user_id"].nunique()),
        "n_control_users": int(df.loc[control_mask, "user_id"].nunique()),
        "group_means": {
            "all_events": summarize_group_means(df, mask=event_mask, label="all_events"),
            "all_controls": summarize_group_means(df, mask=control_mask, label="all_controls"),
            "precollapse_events": summarize_group_means(df, mask=(event_mask & precollapse_mask), label="precollapse_events"),
            "reference_controls": summarize_group_means(
                df,
                mask=(control_mask & (df["step"] > (df["natural_alarm_window_end_step"] - PREC_COLLAPSE_WINDOW))),
                label="reference_controls",
            ),
        },
        "telemetry_ranges": {
            "G": {
                "min": float(df["G"].min()) if len(df) else None,
                "max": float(df["G"].max()) if len(df) else None,
            },
            "p": {
                "min": float(df["p"].min()) if len(df) else None,
                "max": float(df["p"].max()) if len(df) else None,
            },
            "delta": {
                "min": float(df["delta"].min()) if len(df) else None,
                "max": float(df["delta"].max()) if len(df) else None,
            },
        },
        "sanity_checks": {
            "panel_users_match_frozen_included_units": int(df["user_id"].nunique()) == int(benchmark_freeze["frozen_counts"]["n_included_units"]),
            "panel_engine_hash_matches_freeze": cfg.engine_hash == benchmark_freeze["frozen_contract"]["engine_hash"],
            "contains_event_rows": bool(event_mask.any()),
            "contains_control_rows": bool(control_mask.any()),
        },
    }
    return summary


def write_summary(summary: Dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[ok] wrote telemetry summary: {out_path}")


def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    contract, benchmark_freeze, provenance, manifest_df = ensure_inputs(paths)
    cfg = parse_config(contract, benchmark_freeze)

    ratings_df = load_sorted_ratings(provenance)
    trajectories, user_positive_items, item_to_users, item_positive_counts = build_user_trajectories_and_positive_index(
        ratings_df,
        positive_threshold=cfg.positive_rating_threshold,
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

    metas = build_episode_meta(manifest_df)
    seed_movie_ids = build_included_seed_item_universe(metas, user_positive_items)
    print(f"[engine] included-user seed item universe: {len(seed_movie_ids):,} items")
    engine.warm_neighbor_cache(seed_movie_ids, progress_every=250)

    rows: List[Dict[str, Any]] = []
    total = len(metas)
    print(f"[telemetry] beginning replay across {total:,} included users")
    for idx, meta in enumerate(metas, start=1):
        traj = trajectories.get(meta.user_id)
        if traj is None:
            raise KeyError(f"Missing trajectory for included user_id={meta.user_id}")
        rows.extend(simulate_user_telemetry(traj, meta, cfg=cfg, engine=engine))
        if idx % 250 == 0 or idx == total:
            print(f"[telemetry] processed {idx:,}/{total:,} included users")

    panel_path = paths.results_manifests / TELEMETRY_PANEL_FILENAME
    summary_path = paths.results_manifests / TELEMETRY_SUMMARY_FILENAME

    panel_df = write_panel(rows, panel_path)
    summary = build_summary(panel_df, cfg=cfg, benchmark_freeze=benchmark_freeze)
    write_summary(summary, summary_path)

    print("[done] telemetry computation complete")
    print(f"[done] panel:   {panel_path}")
    print(f"[done] summary: {summary_path}")
    return panel_path, summary_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()