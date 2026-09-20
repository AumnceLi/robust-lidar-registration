# -*- coding: utf-8 -*-
"""Step 2a: fix the diagnostic frames BEFORE any new result is produced.
Rule (pre-registered): VI/II/III = 40 frames each, IV = 40 frames, chosen by EQUAL-SPACED
indices over the ORIGINAL TIME ORDER (unique round(linspace(0,n-1,40))). No frame is chosen by
error magnitude or by any method outcome. The original 40-iteration cap is covered by
construction because budget=40 re-runs the frozen solver; post-hoc cap-hit counts of the SHIPPED
results are recorded only as descriptors and never used for selection."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import rev_common as Rv  # noqa

K = 40
plan = {"rule": "unique round(linspace(0,n-1,40)) over original time order; fixed before results",
        "k_per_trajectory": K, "trajectories": {}}
for tr in Rv.TRAJS:
    n = Rv.REG[tr]["n"]
    sel = Rv.equal_spaced_ids(n, K).tolist()
    # post-hoc DESCRIPTOR ONLY (shipped frozen Raw iters==40 cap-hit among selected); not used to choose
    real = Rv.realized_pose_errors(tr)
    shipped_cap = sum(1 for i in sel if real.get(i, {}).get("raw_iters", None) == 40)
    plan["trajectories"][tr] = dict(n_frames=n, selected_order=sel, selected_scan=sel,
                                    n_selected=len(sel),
                                    shipped_raw_cap40_hits_among_selected_DESCRIPTOR=shipped_cap)
    print(f"{tr}: n={n} selected={len(sel)} (shipped Raw iters==40 among selected = {shipped_cap}, descriptor only)")
with open(os.path.join(HERE, "diagnostic_frames.json"), "w") as f:
    json.dump(plan, f, indent=2)
print("saved diagnostic_frames.json")
