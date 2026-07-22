"""DATA PREP: generate the six control-arm INDICATOR-side slate panels
(popularity + shuffled-TS 102+{0..4}) under the frozen rules. Logs slates only —
computes NO ΔTPR and NO indicator-vs-label separation (same epistemic class as the
real slate re-run). Each arm rebuilds its own slates/labels/L via the frozen
simulate_user_episode + simulate_user_telemetry. Panels are gitignored payloads;
each is hash-anchored two-tier. decision.RATIFIED stays False.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

from ... import build_user_episode_manifest as bem
from ... import compute_telemetry as ct
from .. import config as C
from . import replay as R
from . import shuffled_ts as STS
from .popularity_engine import PopularityRecommender

SHUFFLED_TS_SEEDS = [102 + i for i in range(5)]


def _arm_panel(make_engine, trajectories, *, bem_cfg, ct_cfg, out_path: Path, label: str):
    ids = sorted(trajectories.keys())
    rows = []
    for n, uid in enumerate(ids, 1):
        traj = trajectories[uid]
        ep = bem.simulate_user_episode(traj, cfg=bem_cfg, engine=make_engine(uid))
        if ep.inclusion_status != "included":
            continue
        meta = ct.EpisodeMeta(
            user_id=traj.user_id, label=ep.label, collapse_step=ep.collapse_step,
            natural_alarm_window_start_step=int(ep.natural_alarm_window_start_step),
            natural_alarm_window_end_step=int(ep.natural_alarm_window_end_step))
        rows.extend(ct.simulate_user_telemetry(traj, meta, cfg=ct_cfg, engine=make_engine(uid)))
        if n % 20000 == 0:
            print(f"[panel {label}] {n}/{len(ids)} users  rows={len(rows):,}", flush=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # G convention (C**): gzip with mtime=0 so the container is reproducible (closes container-drift, D-16/D-21).
    import gzip as _gz, io as _io
    _buf = _io.BytesIO()
    with _gz.GzipFile(fileobj=_buf, mode="wb", mtime=0) as _g:
        _g.write(pd.DataFrame(rows).to_csv(index=False).encode())
    out_path.write_bytes(_buf.getvalue())
    print(f"[panel {label}] wrote {out_path}  rows={len(rows):,}", flush=True)
    return len(rows)


def run(out_dir: Path = None):
    out_dir = out_dir or C.OUT_DIR
    bem_cfg, ct_cfg, traj, universe = R.load_context()
    prov = json.loads((C.REPO / "results/manifests/movielens25m_recursive_frontier_public_v1__raw_input_provenance.json").read_text())
    df = bem.load_sorted_ratings(prov)
    _, user_pos, item_to_users, item_pos_counts = bem.build_user_trajectories_and_positive_index(
        df, positive_threshold=bem_cfg.positive_rating_threshold)
    seed_items = sorted({int(m) for items in user_pos.values() for m in items})

    # popularity-only (deterministic; fast)
    pop = PopularityRecommender(item_pos_counts, bem_cfg.top_k)
    _arm_panel(lambda uid: pop, traj, bem_cfg=bem_cfg, ct_cfg=ct_cfg,
               out_path=out_dir / "arm_popularity_only__slate_panel.csv.gz", label="popularity")

    # shuffled-TS: build the canonical CF engine once (order-independent index), warm cache
    cf = STS.build_cf_engine(ct_cfg, user_pos, item_to_users, item_pos_counts,
                             seed_movie_ids=seed_items, warm_cache=True)
    for s in SHUFFLED_TS_SEEDS:
        shuffled = STS.build_shuffled_trajectories(traj, s)
        _arm_panel(lambda uid: cf, shuffled, bem_cfg=bem_cfg, ct_cfg=ct_cfg,
                   out_path=out_dir / f"arm_shuffled_ts_{s}__slate_panel.csv.gz", label=f"shuffledTS{s}")
    print("PANELS_DONE", flush=True)


def main():
    raise SystemExit("generate_arm_panels is data-prep; invoke run() explicitly under authorization.")


if __name__ == "__main__":
    main()
