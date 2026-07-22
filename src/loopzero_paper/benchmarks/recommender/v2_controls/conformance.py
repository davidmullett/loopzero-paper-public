"""Load-time conformance gates for the Phase-3 block (C** — tasking E, F).

Executed BEFORE any computation. Any mismatch raises ConformanceError, which the block turns into a
hard-stop emitting ONLY the assertion failure (no decision quantity computed or written).

  E (input_gate): the three analysis inputs must match their CONTENT (decompressed) hashes — never
    container hashes — pinned in PANEL_MANIFEST.json (slate panel) and INPUT_MANIFEST.json (sorted
    ratings, covariate cache = the C** hash). Discipline: inputs verified against content pins before
    anything (D-16/D-21).

  F (assert_population_conformance): the loaded real population is verified against the anchored
    clean-control census (commit 6b6ac55) by COUNT and per-class per-fold SET-HASH, with the expected
    sets DERIVED FROM the census file (not hardcoded); the census is cross-checked against the
    registration composition (20,265 events; 1,463 candidate; 1,460 CLEAN = 694 + 766) and any
    disagreement hard-stops and routes to §4.3; the matched counts k = {15,38,77,153} for
    b = {0.02,0.05,0.10,0.20} are COMPUTED from the census eval-CLEAN count (766), not written as
    literals. Discipline: populations verified before compute (D-7).
"""
from __future__ import annotations
import csv, gzip, hashlib, json
from pathlib import Path
from . import config as C
from . import sweep as SW
from .population import fold as _fold

CENSUS_CSV = C.OUT_DIR / "study2_clean_control_census.csv"
CENSUS_SHA = "f286952cd7011bd562aee449d68f221aaa6d0cae6a52350e4c2df2f256188cfc"   # STUDY2_CENSUS 6b6ac55
PANEL_MANIFEST = C.REPO / "preregistration/PANEL_MANIFEST.json"
INPUT_MANIFEST = C.REPO / "preregistration/INPUT_MANIFEST.json"
# registration composition (wka72 §2/§3) — the cross-check literals; census must equal these.
REG = {"events": 20265, "candidate": 1463, "clean": 1460, "clean_cal": 694, "clean_eval": 766}
REG_K = {0.02: 15, 0.05: 38, 0.10: 77, 0.20: 153}   # expected matched counts over 766 eval CLEAN


class ConformanceError(RuntimeError):
    pass


def _dec_sha(p) -> str:
    h = hashlib.sha256()
    with gzip.open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _set_hash(ids) -> str:
    return hashlib.sha256((",".join(str(i) for i in sorted(int(x) for x in ids))).encode()).hexdigest()


def _manifest_dec_hash(manifest_path, name_substr):
    m = json.loads(Path(manifest_path).read_text())
    arts = m.get("artifacts", []) + m.get("panels", [])
    for a in arts:
        if name_substr in a["path"]:
            return a["decompressed_sha256"]
    raise ConformanceError(f"content pin for {name_substr} not found in {manifest_path.name}")


def input_gate():
    """E: verify the three inputs against their DECOMPRESSED content pins (never containers)."""
    checks = [
        ("slate panel", C.PANEL, _manifest_dec_hash(PANEL_MANIFEST, "telemetry_panel__slate_v1")),
        ("sorted ratings", C.SORTED_RATINGS, _manifest_dec_hash(INPUT_MANIFEST, "ratings__sorted_by_user_time")),
        ("covariate cache", C.OUT_DIR / "real_covariates.csv.gz", _manifest_dec_hash(INPUT_MANIFEST, "real_covariates.csv.gz")),
    ]
    for label, path, target in checks:
        live = _dec_sha(path)
        if live != target:
            raise ConformanceError(f"INPUT GATE FAIL ({label}): decompressed {live} != pinned {target}")
    return {label: target for label, _, target in checks}


def _census_clean_sets():
    """Derive, from the anchored census, expected CLEAN-control userId sets per fold + composition."""
    if hashlib.sha256(CENSUS_CSV.read_bytes()).hexdigest() != CENSUS_SHA:
        raise ConformanceError("census file does not match its anchor (6b6ac55)")
    clean = {"cal": set(), "eval": set()}
    n_candidate = 0
    for row in csv.DictReader(CENSUS_CSV.open()):
        is_cand = row["is_candidate"] == "1"
        starved = row["starved_in_2050"] == "1"
        if is_cand:
            n_candidate += 1
        if is_cand and not starved:
            fold = "cal" if row["fold"] == "calibration" else "eval"
            clean[fold].add(int(row["user_id"]))
    return clean, n_candidate


def assert_population_conformance(real_units):
    """F: loaded real population vs census (count + per-class per-fold set-hash), census vs
    registration composition, k derivation. Raises ConformanceError on any mismatch."""
    clean, n_candidate = _census_clean_sets()
    n_clean_cal, n_clean_eval = len(clean["cal"]), len(clean["eval"])
    n_clean = n_clean_cal + n_clean_eval

    # census vs registration composition — disagreement routes to §4.3
    if (n_candidate != REG["candidate"] or n_clean != REG["clean"]
            or n_clean_cal != REG["clean_cal"] or n_clean_eval != REG["clean_eval"]):
        raise ConformanceError(
            f"§4.3: census composition (candidate={n_candidate}, clean={n_clean}={n_clean_cal}+{n_clean_eval}) "
            f"disagrees with registration ({REG['candidate']}, {REG['clean']}={REG['clean_cal']}+{REG['clean_eval']})")

    # loaded population, per class per fold
    uid = real_units.user_id
    is_ev = real_units.is_event
    is_clean = real_units.clean_control
    loaded_clean = {"cal": set(), "eval": set()}
    n_events = 0
    for i in range(len(uid)):
        u = int(uid[i])
        if is_ev[i]:
            n_events += 1
        elif is_clean[i]:
            loaded_clean[_fold(u)].add(u)

    # CLEAN-control class: count + set-hash per fold, against the census-derived sets
    for f in ("cal", "eval"):
        if len(loaded_clean[f]) != len(clean[f]):
            raise ConformanceError(f"CLEAN control count[{f}] loaded {len(loaded_clean[f])} != census {len(clean[f])}")
        if _set_hash(loaded_clean[f]) != _set_hash(clean[f]):
            raise ConformanceError(f"CLEAN control SET-HASH[{f}] loaded != census")

    # event class: census does not enumerate events; assert count against the registration
    if n_events != REG["events"]:
        raise ConformanceError(f"event count loaded {n_events} != registration {REG['events']}")

    # matched-count k COMPUTED from the census eval-CLEAN count (766), not literals
    for b, expected in REG_K.items():
        k = SW.matched_count(b, n_clean_eval)
        if k != expected:
            raise ConformanceError(f"matched count k(b={b}) computed {k} over {n_clean_eval} eval CLEAN != expected {expected}")

    return {"events": n_events, "clean_cal": n_clean_cal, "clean_eval": n_clean_eval,
            "clean_set_hash": {f: _set_hash(clean[f]) for f in ("cal", "eval")},
            "k": {str(b): SW.matched_count(b, n_clean_eval) for b in REG_K}}
