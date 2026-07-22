"""§10 mechanism control — RANDOM recommender.

Interface-compatible with the frozen `FrozenItemItemCFEngine`: exposes
`recommend(*, positive_profile_items, seen_items) -> List[int]`, so it can drive
the frozen `simulate_user_episode` / `simulate_user_telemetry` unchanged and thus
reproduce the frozen replay rules exactly.

Design invariants (correctness-critical):
- **§4-safe seeding.** The RNG seed is derived ONLY from pre-episode ids
  (`arm_seed`, `user_id`) and the current `seen_items` set. `seen_items` is the
  recommender's own candidate-exclusion state (the frozen engine excludes seen
  items too) — it is NOT a step *outcome* fed into the seed to leak the label.
- **Stateless / order-independent.** `recommend()` is a pure function of
  (arm_seed, user_id, seen_items): same inputs → same slate, regardless of call
  order or count. This is required because the telemetry replay calls
  `recommend()` twice per step (primary + self-reinforcement-ablated) while the
  labeling replay calls it once; an RNG advancing across calls would desync the
  two replays and make labels and slates inconsistent. A stateless engine mirrors
  the deterministic CF engine, so both replays agree.
- Profile-independent by construction (a random recommender ignores the profile),
  which also makes the ablated slate equal the primary slate (legacy `p` is
  retired anyway and unused).
"""
from __future__ import annotations
import hashlib
from typing import List, Sequence
import numpy as np


class RandomRecommender:
    def __init__(self, item_universe: Sequence[int], top_k: int, user_id: int, arm_seed: int):
        self.universe = np.array(sorted(int(x) for x in set(item_universe)), dtype=np.int64)
        self.top_k = int(top_k)
        self.user_id = int(user_id)
        self.arm_seed = int(arm_seed)
        # Stub CF attributes so the legacy diversity_proxy(recs, engine) path does not
        # crash if invoked; its output is IGNORED (§6 δ is computed from slate_json).
        self._pairwise_similarity_cache: dict = {}
        self._item_user_sets: dict = {}
        self.item_positive_counts: dict = {}

    def _seed(self, seen: set) -> int:
        h = hashlib.sha256()
        h.update(b"loopzero-random-arm")
        h.update(int(self.arm_seed).to_bytes(8, "little", signed=True))
        h.update(int(self.user_id).to_bytes(8, "little", signed=True))
        for s in sorted(seen):
            h.update(int(s).to_bytes(8, "little", signed=True))
        return int.from_bytes(h.digest()[:8], "little")

    def recommend(self, *, positive_profile_items: Sequence[int], seen_items) -> List[int]:
        seen = set(int(x) for x in seen_items)
        rng = np.random.default_rng(self._seed(seen))
        # Draw top_k + |seen| distinct positions → at least top_k are unseen.
        m = min(len(self.universe), self.top_k + len(seen))
        idx = rng.choice(len(self.universe), size=m, replace=False)
        out: List[int] = []
        for i in idx:
            it = int(self.universe[i])
            if it not in seen:
                out.append(it)
                if len(out) >= self.top_k:
                    break
        return out
