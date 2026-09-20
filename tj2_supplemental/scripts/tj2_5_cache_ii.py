# -*- coding: utf-8 -*-
"""TJ2 cache build for the SINGLE selected trajectory Dataset II.
Numerically identical to frozen r6_ext_cache.py (same model, same 24 patches, same NN policy,
same view geometry); only paths differ. Reads II .3d point clouds (permitted post-manifest for
the selected trajectory only). No re-clustering: scan patch = frozen model-patch label of NN."""
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

import os, sys, time, glob
import numpy as np, pandas as pd
from scipy.spatial import cKDTree

PHASE0 = _pp("structured_mismatch_phase0/scripts")
sys.path.insert(0, PHASE0)
import s0_common as C, m_common as M

TJ = _pp("tj2_supplemental")
DATA_DIR = os.path.join(TJ, "ii_data", "epos_dataset_ii")
OUTROOT = os.path.join(TJ, "cache", "ii"); os.makedirs(OUTROOT, exist_ok=True)

mc = np.load(os.path.join(M.CACHE, "model_cache.npz"))
MODEL = mc["xyz"].astype(np.float64); NM = mc["normals"].astype(np.float64)
PLAB = np.load(os.path.join(M.CACHE, "patches.npz"))["lab"]
TREE = cKDTree(MODEL)

def load_pose(d, i):
    with open(os.path.join(d, f"{i:04d}.pose")) as fh:
        L = [ln.strip() for ln in fh if ln.strip()]
    return float(L[0]), np.array(L[1].split(), float), np.array(L[2].split(), float)

def main():
    ids = sorted(int(os.path.basename(f)[:4]) for f in glob.glob(os.path.join(DATA_DIR, "*.3d")))
    assert len(ids) == 1253, len(ids)
    rows = []; t0 = time.perf_counter()
    for k, i in enumerate(ids):
        pc = np.loadtxt(os.path.join(DATA_DIR, f"{i:04d}.3d"))
        ts, t, q = load_pose(DATA_DIR, i); R = C.quat_to_R(q)
        aligned = ((R.T) @ (pc - t).T).T
        dd, nn = TREE.query(aligned, k=1, workers=-1)
        signed = ((aligned - MODEL[nn]) * NM[nn]).sum(1)
        patch = PLAB[nn]
        o = -R.T @ t; rng = np.linalg.norm(o); u = o / rng
        np.savez_compressed(os.path.join(OUTROOT, f"scan_{i:04d}.npz"),
                            aligned=aligned.astype(np.float32), nnidx=nn.astype(np.int32),
                            patch=patch.astype(np.int16), signed=signed.astype(np.float32),
                            d=dd.astype(np.float32))
        rows.append(dict(scan=i, range_m=rng, n=len(pc), ux=u[0], uy=u[1], uz=u[2], ts=ts))
        if (k + 1) % 200 == 0:
            print(f"[ii] {k+1}/{len(ids)} {time.perf_counter()-t0:.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUTROOT, "meta_ii.csv"), index=False)
    print(f"[ii] cache done n={len(ids)} in {time.perf_counter()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
