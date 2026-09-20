# -*- coding: utf-8 -*-
"""Read-only inspection of frozen inputs for the final targeted round."""
# ==== portable repo root (auto-added; replaces hard-coded D:\doubao) ====
import os as _os
def _repo_root():
    _d = _os.path.dirname(_os.path.abspath(__file__))
    while not _os.path.exists(_os.path.join(_d, '.repo_root')):
        _p = _os.path.dirname(_d)
        if _p == _d:
            raise RuntimeError('repo-root marker .repo_root not found')
        _d = _p
    return _d
_REPO = _repo_root()
def _pp(*_a):
    return _os.path.join(_REPO, *_a).replace('\\', '/')
# ==== end portable root ====

import pandas as pd, numpy as np, json, os
R = _pp("revision_experiments")

e4 = pd.read_csv(os.path.join(R, "exp4_historical_baselines", "dbs_vector_framewise.csv"))
print("E4 cols:", list(e4.columns))
print("E4 sizes:\n", e4.groupby("trajectory").size())
print("in_support:", e4.in_support.unique(), " posthoc:", e4.posthoc.unique())

rep = pd.read_csv(_pp("FOLLOWUP_6_9/scripts/replay79_arms.csv"))
print("\nREPLAY cols:", list(rep.columns))
print("arms:", sorted(rep.arm.unique()))
print(rep.groupby(["trajectory", "arm"]).size().unstack().reindex(["VI", "IV", "II", "III"]))

bm = pd.read_csv(_pp("POSE_AUDIT/results/master_pose_results_frame.csv"))
blk = {(r.trajectory, int(r.order)): int(r.block) for r in bm.itertuples()}
e4["blk"] = [blk.get((t, int(o))) for t, o in zip(e4.trajectory, e4.order)]
print("\nE4 block join NaN:", int(e4.blk.isna().sum()))
print("E4 blocks per traj:", e4.groupby("trajectory").blk.nunique().to_dict())
print("E4 block-id sets:", {t: sorted(g.blk.dropna().unique().tolist()) for t, g in e4.groupby("trajectory")})

# replay block coverage
rep["blk"] = [blk.get((t, int(o))) for t, o in zip(rep.trajectory, rep.order)]
print("\nREPLAY block NaN:", int(rep.blk.isna().sum()))
print("REPLAY blocks/traj:", rep.groupby("trajectory").blk.nunique().to_dict())

plan = json.load(open(os.path.join(R, "exp2_iter_budget", "diagnostic_frames.json")))
print("\nplan rule:", plan["rule"])
for tr in ["VI", "IV", "II", "III"]:
    sel = plan["trajectories"][tr]["selected_order"]
    half = sel[0::2]
    present = set(int(o) for o in rep[rep.trajectory == tr].order.unique())
    missing = [o for o in half if o not in present]
    print(f"{tr}: n40={len(sel)} half={len(half)} half_in_replay={len(half)-len(missing)} missing={missing}")
