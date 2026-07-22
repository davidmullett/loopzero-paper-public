"""§10 dispositive control — POPULARITY-ONLY recommender (deterministic).

Interface-compatible with FrozenItemItemCFEngine: `recommend(*, positive_profile_items,
seen_items) -> List[int]`. Recommends the top-K most globally-popular UNSEEN items
(popularity = item_positive_counts, the frozen positive co-rating count), tie-broken
by ascending movieId for determinism. Ignores the profile (personalization-severed);
no RNG (deterministic → no per-seed replicates, per §10).
"""
from __future__ import annotations
from typing import Dict, List, Sequence
import numpy as np


class PopularityRecommender:
    def __init__(self, item_positive_counts: Dict[int, int], top_k: int):
        # frozen popularity ranking: popularity desc, then movieId asc (deterministic tie-break)
        self.item_positive_counts = dict(item_positive_counts)
        self._ranked = np.array(
            [m for m, _ in sorted(self.item_positive_counts.items(), key=lambda kv: (-kv[1], kv[0]))],
            dtype=np.int64,
        )
        self.top_k = int(top_k)
        # Stub CF attributes so the legacy diversity_proxy(recs, engine) path does not crash;
        # its output is IGNORED (§6 δ comes from slate_json, and the pre-census reads no indicators).
        self._pairwise_similarity_cache: dict = {}
        self._item_user_sets: dict = {}

    def recommend(self, *, positive_profile_items: Sequence[int], seen_items) -> List[int]:
        seen = set(int(x) for x in seen_items)
        out: List[int] = []
        for m in self._ranked:
            it = int(m)
            if it not in seen:
                out.append(it)
                if len(out) >= self.top_k:
                    break
        return out
