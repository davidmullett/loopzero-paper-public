"""§4 landmark population L + §5 seedless folds + population accounting.

READ-ONLY. Loads the slate panel once into per-user records restricted to the
step 1..20 indicator window. No indicator-vs-label decision quantity here.
"""
from __future__ import annotations
import gzip, csv, hashlib, json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np
from . import config as C

csv.field_size_limit(1 << 24)


def fold(user_id: int) -> str:
    """§5: SHA-256 of ASCII decimal userId; calibration iff last hex digit in {0..7}."""
    h = hashlib.sha256(str(int(user_id)).encode("ascii")).hexdigest()
    return "cal" if h[-1] in "01234567" else "eval"


@dataclass
class Unit:
    user_id: int
    fold: str
    label: str                       # 'event' | 'control' (whole-horizon v1 label)
    collapse_step: Optional[int]
    in_L: bool
    slates: List[List[int]] = field(default_factory=list)     # steps 1..20, each len K
    miss_run_fraction: List[float] = field(default_factory=list)  # steps 1..20 (min(1,consec/8))
    hit: List[int] = field(default_factory=list)              # steps 1..20 (1=hit,0=miss)
    consec_at_20: int = 0                                     # raw consecutive_misses at step 20


def load_units() -> Dict[int, Unit]:
    """Load every included unit with its step 1..20 window (slates + miss series)."""
    streak_len = C.load_frozen_constants()["collapse_streak_len"]
    tmp: Dict[int, dict] = {}
    with gzip.open(C.PANEL, "rt", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            u = int(row["user_id"]); st = int(row["step"])
            rec = tmp.get(u)
            if rec is None:
                cs = row["collapse_step"]
                rec = tmp[u] = {
                    "label": row["label"],
                    "cs": None if cs in ("", "NA") else int(float(cs)),
                    "slates": {}, "mrf": {}, "hit": {},
                }
            if st <= C.WINDOW:
                rec["slates"][st] = [int(x) for x in json.loads(row["slate_json"])]
                consec = int(row["consecutive_misses_after_step"])
                rec["mrf"][st] = min(1.0, consec / streak_len)
                rec["hit"][st] = int(row["hit_this_step"])
                if st == C.WINDOW:
                    rec["consec20"] = consec
    units: Dict[int, Unit] = {}
    for u, rec in tmp.items():
        cs = rec["cs"]; lab = rec["label"]
        in_L = (lab == "control") or (lab == "event" and cs is not None and C.T_SPLIT < cs <= 50)
        unit = Unit(user_id=u, fold=fold(u), label=lab, collapse_step=cs, in_L=in_L)
        if in_L:
            steps = list(range(1, C.WINDOW + 1))
            assert all(s in rec["slates"] for s in steps), f"user {u} incomplete window"
            unit.slates = [rec["slates"][s] for s in steps]
            unit.miss_run_fraction = [rec["mrf"][s] for s in steps]
            unit.hit = [rec["hit"][s] for s in steps]
            unit.consec_at_20 = int(rec.get("consec20", 0))
        units[u] = unit
    return units


def landmark_L(units: Dict[int, Unit]) -> List[Unit]:
    """Deterministic L ordering: ascending userId (matches §8 tie-break)."""
    return [units[u] for u in sorted(units) if units[u].in_L]


def population_accounting(units: Dict[int, Unit]) -> dict:
    """§4 accounting — reported BEFORE any indicator-label analysis. Not a decision quantity."""
    included = list(units.values())
    n_event = sum(1 for u in included if u.label == "event")
    n_control = sum(1 for u in included if u.label == "control")
    early = sum(1 for u in included if u.label == "event" and u.collapse_step is not None and u.collapse_step <= C.T_SPLIT)
    L = [u for u in included if u.in_L]
    def counts(subset):
        return {
            "n": len(subset),
            "events": sum(1 for u in subset if u.label == "event"),
            "controls": sum(1 for u in subset if u.label == "control"),
        }
    per_fold = {fd: counts([u for u in L if u.fold == fd]) for fd in ("cal", "eval")}
    return {
        "n_included_units": len(included),
        "included_events": n_event,
        "included_controls": n_control,
        "excluded_early_degraders_collapse_le_20": early,
        "n_L": len(L),
        "L_events": counts(L)["events"],
        "L_controls": counts(L)["controls"],
        "L_per_fold": per_fold,
        "eval_events_in_L": per_fold["eval"]["events"],
        "eval_controls_in_L": per_fold["eval"]["controls"],
        "cal_controls_in_L": per_fold["cal"]["controls"],
        # §4 wording correction (flag-4 ruling option-i, disclosed):
        "flag4_correction": _flag4_miss_saturation(units),
    }


def _flag4_miss_saturation(units: Dict[int, Unit]) -> dict:
    """Disclosed correction to §4's false 'consec<=7 by construction' sentence.

    miss_run_fraction = min(1, consec/8) saturates at 1.0 when consec>=8, so it
    cannot recover the true max streak; the true max consecutive_misses (=19) is
    read directly from the panel in the runner. Here we report the (exact)
    fraction of L with in-window miss saturation.
    """
    L = [u for u in units.values() if u.in_L]
    n_sat = sum(1 for u in L if any(m >= 1.0 for m in u.miss_run_fraction))
    max_consec_at_20 = max((u.consec_at_20 for u in L), default=0)
    return {
        "note": "§4 'consecutive_misses at step 20 <=7 by construction' is FALSE; frontier-floor(>=10) exception permits long unlabeled streaks in L.",
        "corrected_max_consecutive_misses_at_step20_over_L": max_consec_at_20,
        "L_units_with_in_window_miss_saturation": n_sat,
        "fraction_of_L": round(n_sat / max(1, len(L)), 4),
    }
