# -*- coding: utf-8 -*-
"""TJ2 validation: reproduce TJ1 support flags for IV/V from geometry only, and compare
bit-for-bit against the frozen ext_predict_*.npz['insup'] produced in TJ1.
Reads ONLY cached IV/V geometry meta + frozen predictor; reads NO new point cloud."""
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

import os, sys
import numpy as np, pandas as pd
PHASE0 = _pp("structured_mismatch_phase0/scripts")
sys.path.insert(0, PHASE0)
EXT = os.path.join(PHASE0, "cache", "ext")
F = np.load(os.path.join(PHASE0, "cache", "rescue", "VI_ONLY_PREDICTOR_FROZEN.npz"))
vr, uv = F["vrange"].astype(float), F["uview"].astype(float)
sr, tau = float(F["range_std"]), float(F["tau_support"])
for tag, expect_in in [("iv", 156), ("v", 0)]:
    meta = pd.read_csv(os.path.join(EXT, f"meta_{tag}.csv"))
    U = meta[["ux", "uy", "uz"]].to_numpy(float); rg = meta.range_m.to_numpy(float)
    ang = np.arccos(np.clip(U @ uv.T, -1, 1))
    D = np.sqrt(((rg[:, None] - vr[None, :]) / sr) ** 2 + ang ** 2)
    ins = D.min(1) <= tau
    PR = np.load(os.path.join(EXT, f"ext_predict_{tag}.npz"))
    ref = PR["insup"]; ref_tau = float(PR["tau"])
    agree = bool((ins == ref).all())
    print(f"{tag}: recomputed IN={int(ins.sum())}  TJ1-frozen IN={int(ref.sum())} "
          f"expected={expect_in}  tau_match={abs(ref_tau-tau)<1e-12}  bitwise_agree={agree}")
