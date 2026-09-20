# -*- coding: utf-8 -*-
"""Quick deeper inspection of D1/D2/torque, landscape, and ext conditions."""
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

import numpy as np

d = np.load(_pp("structured_mismatch_phase0/scripts/cache/rescue/objective_main.npz"),
            allow_pickle=True)

print("=== D1 / D2 / torque diagnostics (raw condition) ===")
for key in ["raw__D1", "raw__D2", "raw__torque"]:
    a = d[key]
    print(f"\n{key}: shape={a.shape}")
    print(f"  col means: {a.mean(axis=0)}")
    print(f"  col stds:  {a.std(axis=0)}")
    print(f"  col mins:  {a.min(axis=0)}")
    print(f"  col maxs:  {a.max(axis=0)}")
    nrm = np.linalg.norm(a, axis=1)
    print(f"  ||vec||: median={np.median(nrm):.6f}, IQR=[{np.percentile(nrm,25):.6f},{np.percentile(nrm,75):.6f}]")

print("\n=== g stats (raw) ===")
g = d["raw__g"]  # (501,6,2)
print(f"g[:,:,0] (p2p): trans norm median={np.median(np.linalg.norm(g[:,:3,0],axis=1)):.6f}, "
      f"rot norm median={np.median(np.linalg.norm(g[:,3:,0],axis=1)):.6f}")
print(f"g[:,:,1] (p2l): trans norm median={np.median(np.linalg.norm(g[:,:3,1],axis=1)):.6f}, "
      f"rot norm median={np.median(np.linalg.norm(g[:,3:,1],axis=1)):.6f}")

print("\n=== xistar stats (raw) ===")
xi = d["raw__xistar"]  # (501,6,2)
print(f"xi[:,:,0] (p2p): trans norm median={np.median(np.linalg.norm(xi[:,:3,0],axis=1))*1000:.2f} mm")
print(f"xi[:,:,1] (p2l): trans norm median={np.median(np.linalg.norm(xi[:,:3,1],axis=1))*1000:.2f} mm")

print("\n=== dhat stats (raw) ===")
dh = d["raw__dhat"]
print(f"dhat[:,:,0] (p2p): trans norm median={np.median(np.linalg.norm(dh[:,:3,0],axis=1))*1000:.2f} mm")
print(f"dhat[:,:,1] (p2l): trans norm median={np.median(np.linalg.norm(dh[:,:3,1],axis=1))*1000:.2f} mm")

print("\n=== landscape shape decode ===")
ls = d["landscape"]  # (501,2,3,3,2,2)
print(f"landscape shape: {ls.shape}")
# dim1=0 likely translation group, dim1=1 rotation group
# dim4=0 positive, dim4=1 negative
# dim5=0 Jp2p, dim5=1 Jp2l
# Check zero reference: J0
J0 = d["raw__J0"]  # (501,2)
print(f"J0[0] (Jp2p,Jp2l for frame 0): {J0[0]}")
print(f"landscape[0,0,0,0,0,:] (trans ax0, scale0, +): {ls[0,0,0,0,0,:]}")
print(f"landscape[0,0,0,0,1,:] (trans ax0, scale0, -): {ls[0,0,0,0,1,:]}")
# The first scale is 0.01 m = 1 cm. Check if + perturbation on x axis increases/decreases J
print(f"  vs J0 p2p={J0[0,0]:.6e}, p2l={J0[0,1]:.6e}")

# Correlation of D1 norm with g norm
D1n = np.linalg.norm(d["raw__D1"], axis=1)
D2n = np.linalg.norm(d["raw__D2"], axis=1)
Tn = np.linalg.norm(d["raw__torque"], axis=1)
gn_p2p = np.linalg.norm(d["raw__g"][:, :, 0], axis=1)
gn_p2l = np.linalg.norm(d["raw__g"][:, :, 1], axis=1)
from scipy.stats import spearmanr, pearsonr
print("\n=== D1/D2/torque norm vs g norm (raw) ===")
for name, vec in [("D1", D1n), ("D2", D2n), ("torque", Tn)]:
    for oname, gv in [("p2p", gn_p2p), ("p2l", gn_p2l)]:
        sp = spearmanr(vec, gv)
        pe = pearsonr(vec, gv)
        print(f"  {name} vs g[{oname}]: spearman={sp.statistic:.3f} (p={sp.pvalue:.2e}), pearson={pe.statistic:.3f} (p={pe.pvalue:.2e})")
