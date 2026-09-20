# -*- coding: utf-8 -*-
"""One-off schema/env inspection for the objective-bias rescue audit."""
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

import sys, time, platform
import numpy as np
print("python", sys.version.split()[0], platform.platform())
for m in ("numpy","scipy","pandas","sklearn"):
    try:
        mod=__import__(m); print(m, getattr(mod,"__version__","?"))
    except Exception as e:
        print(m, "MISSING", e)

import os
CACHE = _pp("structured_mismatch_phase0/scripts/cache")
def peek(name):
    p=os.path.join(CACHE,name)
    z=np.load(p)
    print("\n==",name,"== keys:", list(z.keys()) if hasattr(z,"keys") else "npy")
    if hasattr(z,"keys"):
        for k in z.keys():
            a=z[k]; print(f"   {k:10s} shape={a.shape} dtype={a.dtype}")
for n in ("model_cache.npz","patches.npz","patch_matrix.npz"):
    try: peek(n)
    except Exception as e: print(n,"ERR",e)
z=np.load(os.path.join(CACHE,"scans","scan_0000.npz"))
print("\n== scan_0000 ==")
for k in z.keys():
    a=z[k]; print(f"   {k:10s} shape={a.shape} dtype={a.dtype}",
          ("min=%.4f max=%.4f mean=%.4f"%(a.min(),a.max(),a.mean())) if a.dtype.kind=="f" else "")
mpr = np.load(os.path.join(CACHE,"model_point_resid.npy"))
print("\nmodel_point_resid.npy", mpr.shape, mpr.dtype, "nan?",np.isnan(mpr).any())

# raw target model head + one pose
tp = _pp("external_dataset_scout/intermediate/samples/epos_target_model.3d")
import itertools
with open(tp) as f:
    head=[next(f).strip() for _ in range(3)]
print("\ntarget model head:", head)
with open(_pp("structured_mismatch_phase0/scripts/vi_data/epos_dataset_vi/0000.pose")) as f:
    print("pose0000:",[l.strip() for l in f if l.strip()])

# timing benchmark: one NN query of 10k source against 68k model tree
from scipy.spatial import cKDTree
mc=np.load(os.path.join(CACHE,"model_cache.npz"))
model=mc["xyz"].astype(np.float64)
tree=cKDTree(model)
src=z["aligned"].astype(np.float64)
t=time.perf_counter()
for _ in range(20):
    d,i=tree.query(src,k=1,workers=-1)
dt=(time.perf_counter()-t)/20
print(f"\nNN query Nsrc={len(src)} Nmodel={len(model)}: {dt*1000:.2f} ms/eval")
