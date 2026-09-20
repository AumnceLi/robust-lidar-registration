# -*- coding: utf-8 -*-
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

import sys
import numpy as np, pandas as pd
sys.path.insert(0, _pp("figure_redesign_v2/configs"))
from paths import SRC, DATA_DERIVED_DIR
import os

# --- Figure 2: real per-patch frame counts ---
d2 = np.load(os.path.join(DATA_DERIVED_DIR, "figure2_residual_stats.npz"))
print("FIG2 n_frames patch3/20/8 =",
      int(d2["n_frames_patch3"]), int(d2["n_frames_patch20"]), int(d2["n_frames_patch8"]))
print("FIG2 heatmap shape (blocks x patches) =", d2["block_patch_med"].shape)
print("FIG2 bin_count 3 =", d2["bin_count_3"], " 8 =", d2["bin_count_8"])

# --- Figure 3: zeros, columns, on_bound ---
pa = pd.read_csv(SRC.get("pose_active",
    _pp("revision_experiments/exp3_pose_active/pose_active_direct_framewise.csv")))
p = pa[pa["kind"] == "p2p"]
print("\nFIG3 columns =", list(pa.columns))
print("FIG3 traj n =", p["trajectory"].value_counts().to_dict(), "total", len(p))
print("FIG3 rms_mm==0:", int((p["rms_mm"] == 0).sum()),
      " rms_pa_mm==0:", int((p["rms_pa_mm"] == 0).sum()))
print("FIG3 rms_mm min>0:", p.loc[p["rms_mm"] > 0, "rms_mm"].min(),
      " rms_pa min>0:", p.loc[p["rms_pa_mm"] > 0, "rms_pa_mm"].min())
print("FIG3 actual_t max:", p["actual_t_mm"].max(),
      " n>=295:", int((p["actual_t_mm"] >= 295).sum()))
for c in pa.columns:
    if "bound" in c.lower() or "clip" in c.lower() or "iter" in c.lower():
        print("  bound/iter col:", c, p[c].dropna().unique()[:6])

# --- Figure 4: zero-error phase samples; dose zero presence ---
dose = pd.read_csv(SRC["dose_response"])
phase = pd.read_csv(SRC["phase_samples"])
print("\nFIG4 dose mag unique (sorted) =", sorted(dose["mag"].unique())[:8])
print("FIG4 phase ete_med <=0 count:", int((phase["ete_med"] <= 0).sum()),
      "of", len(phase), " min positive:", phase.loc[phase["ete_med"] > 0, "ete_med"].min())
