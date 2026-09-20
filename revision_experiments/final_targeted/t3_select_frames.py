# -*- coding: utf-8 -*-
"""TASK 3.1/3.3 -- fix the deterministic half-subset and perturbation design BEFORE any new result.

Half-subset: from Exp.2's already pre-registered 40 equally-spaced frames per trajectory, take
positions 0,2,4,...,38  -> 20 frames/trajectory, 80 unique frames total. Fixed here and never altered
after seeing results. Also records the three fixed LOCAL levels and four sign-balanced deterministic
SE(3) perturbation directions (translation axis -> cyclically paired rotation axis)."""
import os, json
import numpy as np
import ft_common as F

plan = json.load(open(F.DIAG_FRAMES))
DIRS = {  # sign-balanced tetrahedral directions, unit normalized
    "v1": [1, 1, 1], "v2": [1, -1, -1], "v3": [-1, 1, -1], "v4": [-1, -1, 1]}
ROT_PAIR = {"v1": "v2", "v2": "v3", "v3": "v4", "v4": "v1"}   # cyclic, axes never aligned
LEVELS = {"L1": dict(translation_mm=10.0, rotation_deg=0.5),
          "L2": dict(translation_mm=30.0, rotation_deg=1.0),
          "L3": dict(translation_mm=50.0, rotation_deg=2.0)}

def unit(v):
    v = np.asarray(v, float); return (v / np.linalg.norm(v)).tolist()

out = dict(
    rule="Reuse Exp.2 pre-registered 40 equal-spaced frames; take positions 0,2,...,38 (20/traj); "
         "fixed before any initialization result; never altered afterwards.",
    source_40frame_list=os.path.relpath(F.DIAG_FRAMES, F.ROOT),
    selection_positions=list(range(0, 40, 2)),
    n_per_trajectory=20, n_unique_frames=80,
    se3_convention="local chart xi=[t(m) r(rad)], T(xi)P=exp([r]x)P+t; warm-start via frozen "
                   "g_common.robust_icp x0 (rodrigues = SO(3) exponential); NO ad-hoc Euler addition.",
    levels=LEVELS,
    translation_directions={k: unit(v) for k, v in DIRS.items()},
    translation_to_rotation_axis=ROT_PAIR,
    n_perturbations_per_frame=3 * 4,
    methods=["Raw", "Huber", "Patch", "PatchHuber"],
    trajectories={})
total = 0
for tr in F.TRAJS:
    sel40 = plan["trajectories"][tr]["selected_order"]
    half = sel40[0::2]
    assert half == [sel40[i] for i in range(0, 40, 2)] and len(half) == 20
    out["trajectories"][tr] = dict(n_total_frames=plan["trajectories"][tr]["n_frames"],
                                   selected_40=sel40, selected_order=half, n_selected=len(half),
                                   posthoc=tr in F.POSTHOC)
    total += len(half)
assert total == 80, total
out["n_unique_frames"] = total
with open(os.path.join(F.OUT, "initialization_frames.json"), "w") as fh:
    json.dump(out, fh, indent=2)
print("saved initialization_frames.json; total frames =", total)
for tr in F.TRAJS:
    print(tr, out["trajectories"][tr]["selected_order"])
