# -*- coding: utf-8 -*-
"""Test whether the frozen synthetic generator reproduces stored geometry_results bit-exactly,
and how hash((geom,dtype)) behaves under different PYTHONHASHSEED (must be set before interpreter)."""
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
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
import numpy as np, pandas as pd
sys.path.insert(0, _pp("g_chain/common"))
sys.path.insert(0, _pp("g_chain/G_GENERALITY/scripts"))
import g_common as G
import importlib.util
spec = importlib.util.spec_from_file_location("ggr", _pp("g_chain/G_GENERALITY/scripts/g_generality_run.py"))
ggr = importlib.util.module_from_spec(spec); spec.loader.exec_module(ggr)

print("PYTHONHASHSEED env =", os.environ.get("PYTHONHASHSEED"))
print("hash(('GA','D1_appendage_disp')) =", hash(("GA", "D1_appendage_disp")))

stored = pd.read_csv(_pp("g_chain/G_GENERALITY/results/geometry_results.csv"))

def regen(geom, dtype, mag, rep):
    M, Nm, comp, specd = ggr.build_geometry(geom)
    from scipy.spatial import cKDTree
    tree0 = cKDTree(M); sf0 = float(np.median(cKDTree(M).query(M, k=2)[0][:, 1]))
    rng = np.random.default_rng(10_000 + (hash((geom, dtype)) % 100000) + rep)
    Ptrue, Ntrue, model_keep = ggr.apply_discrepancy(M, Nm, comp, specd, dtype, mag)
    if model_keep.all():
        Mreg, Nreg, tree, sf = M, Nm, tree0, sf0
    else:
        Mreg, Nreg = M[model_keep], Nm[model_keep]; tree = cKDTree(Mreg)
        sf = float(np.median(cKDTree(Mreg).query(Mreg, k=2)[0][:, 1]))
    vant = specd["vants"][rep % 3]
    P = ggr._observe(Ptrue, Ntrue, vant, rng)
    r = G.robust_icp(Mreg, Nreg, tree, P, "p2p", "ls", s_floor=sf)
    J0 = G.robust_objective(Mreg, Nreg, tree, P, np.zeros(6), "p2p", "ls", sf)
    return np.linalg.norm(r["xi"][:3]) * 1000, J0

tests = [("GA", "D1_appendage_disp", 2.0, 0), ("GB", "D4_appendage_scale", .025, 3),
         ("GC", "D2_missing_component", .5, 7), ("GA", "D5_appendage_tilt", .5, 11)]
worst_et, worst_j = 0.0, 0.0
for geom, dt, mag, rep in tests:
    s = stored[(stored.geometry == geom) & (stored.dtype == dt) & (stored.mag == mag)
               & (stored.rep == rep) & (stored.kind == "p2p") & (stored.form == "ls")].iloc[0]
    et, J0 = regen(geom, dt, mag, rep)
    de = abs(et - s.et_mm); dj = abs(J0 - s.J0)
    worst_et = max(worst_et, de); worst_j = max(worst_j, dj)
    print(f"{geom} {dt} mag={mag} rep={rep}: stored et={s.et_mm:.6f} J0={s.J0:.6e} | regen et={et:.6f} J0={J0:.6e} | dEt={de:.3e} dJ0={dj:.3e}")
print("WORST dEt", worst_et, "WORST dJ0", worst_j)
