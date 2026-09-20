# -*- coding: utf-8 -*-
"""g1_run.py -- B2-informed frozen mismatch mitigation, ORACLE view z=z(T_GT).
Corrected nominal geometry M_corr = M + mu_{j(i)}; NO relearning, NO new model/network/fusion.
Methods (frozen): M0 raw p2p LS | M1 raw p2l LS | M2 raw Huber(p2p) |
                  M3 global-corr p2p LS | M4 patch-corr p2p LS | M5 full view-conditioned-corr p2p LS (oracle).
Every method's final pose is also scored by the COMMON raw-model LS objective for the objective-vs-pose test."""
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

import os, sys, argparse
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from scipy.spatial import cKDTree
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G
import s0_common as C, m_common as M

CACHE = M.CACHE; TJ = _pp("tj2_supplemental")
OUT = _pp("g_chain/G1_MITIGATION/results"); os.makedirs(OUT, exist_ok=True)
REG = {
 "vi": dict(scandir=os.path.join(CACHE, "scans"), meta=None, pred=None),
 "iv": dict(scandir=os.path.join(CACHE, "ext", "iv"), meta=os.path.join(CACHE, "ext", "meta_iv.csv"),
            pred=os.path.join(CACHE, "ext", "ext_predict_iv.npz")),
 "v":  dict(scandir=os.path.join(CACHE, "ext", "v"), meta=os.path.join(CACHE, "ext", "meta_v.csv"),
            pred=os.path.join(CACHE, "ext", "ext_predict_v.npz")),
 "ii": dict(scandir=os.path.join(TJ, "cache", "ii"), meta=os.path.join(TJ, "cache", "ii", "meta_ii.csv"),
            pred=os.path.join(TJ, "cache", "ii", "ext_predict_ii.npz")),
}
_G = {}

def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    fz = G.load_frozen()
    model, normals, plab = fz["model"], fz["normals"], fz["plab"]
    Vmean, Vcnt = fz["Vmean"], fz["Vcnt"]
    mu_global, mu_patch = G.hierarchy_library(Vmean, Vcnt)
    mglob = G.corrected_model(model, plab, mu_global, mu_patch, None, "global")
    mpatch = G.corrected_model(model, plab, mu_global, mu_patch, None, "patch")
    _G.update(model=model, normals=normals, plab=plab, Vmean=Vmean, Vcnt=Vcnt,
              vrange=fz["vrange"], uview=fz["uview"], mu_global=mu_global, mu_patch=mu_patch,
              tree_raw=cKDTree(model), tree_glob=cKDTree(mglob), tree_patch=cKDTree(mpatch),
              sfloor=fz["s_floor"])

def _load(tag, scandir, sid):
    if tag == "vi":
        z = M.load_scan(int(sid))
    else:
        z = np.load(os.path.join(scandir, f"scan_{int(sid):04d}.npz"))
    return z["aligned"].astype(np.float64)

def J_raw_against_model(P, xi, tree_raw, model):
    """Common yardstick: mean squared point distance to RAW nominal model at pose xi."""
    Q = M.apply_xi(P, xi)
    _, idx = tree_raw.query(Q, k=1, workers=2)
    return float(np.einsum("ij,ij->i", Q - model[idx], Q - model[idx]).mean())

def _run_method(P, target, tree, kind, form, sfloor, tree_raw, model):
    r = G.robust_icp(target, _G["normals"], tree, P, kind, form, s_floor=sfloor)
    xi = r["xi"]
    gn, _ = G.robust_grad_norm(target, _G["normals"], tree, P, kind, form, sfloor)
    Jgt_raw = J_raw_against_model(P, np.zeros(6), tree_raw, model)
    Jfin_raw = J_raw_against_model(P, xi, tree_raw, model)
    return dict(et_mm=np.linalg.norm(xi[:3]) * 1000, eR_deg=np.degrees(np.linalg.norm(xi[3:])),
                g_corr_gt=gn, J_raw_gt=Jgt_raw, J_raw_final=Jfin_raw,
                dJ_raw=Jgt_raw - Jfin_raw, iters=r["iters"], on_bound=int(r["on_bound"]), wmean=r["wmean"])

def _one(args):
    tag, order_i, sid, zr, zu, ndist, insup = args
    model, plab = _G["model"], _G["plab"]
    P = _load(tag, REG[tag]["scandir"], sid)
    mu_full, dmin = G.mu_for_view(_G["Vmean"], _G["Vcnt"], _G["vrange"], _G["uview"], zr, zu)
    mfull = G.corrected_model(model, plab, _G["mu_global"], _G["mu_patch"], mu_full, "full")
    tree_full = cKDTree(mfull)
    sf = _G["sfloor"]; tr0 = _G["tree_raw"]
    methods = [
        ("M0_raw_p2p",      model,  tr0,               "p2p", "ls"),
        ("M1_raw_p2l",      model,  tr0,               "p2l", "ls"),
        ("M2_raw_huber",    model,  tr0,               "p2p", "huber"),
        ("M3_global_corr",  None,   _G["tree_glob"],   "p2p", "ls"),
        ("M4_patch_corr",   None,   _G["tree_patch"],  "p2p", "ls"),
        ("M5_full_corr",    mfull,  tree_full,         "p2p", "ls"),
    ]
    rows = []
    for name, tgt, tree, kind, form in methods:
        if tgt is None:  # build target lazily from tree data (global/patch)
            tgt = tree.data
        rr = _run_method(P, np.asarray(tgt), tree, kind, form, sf, tr0, model)
        rr.update(method=name, traj=tag, order=order_i, scan=int(sid), view="oracle",
                  ndist=float(ndist), in_support=bool(insup), nearest_d=float(dmin))
        rows.append(rr)
    return rows

def run(tag, nw=22):
    cfg = REG[tag]
    if tag == "vi":
        ids = np.arange(501); ndist = np.zeros(501); insup = np.ones(501, bool)
        zr = np.zeros(501); zu = np.zeros((501, 3))
        for i in range(501):
            _, t, q = C.load_pose(i)
            zr[i], zu[i], _ = G.view_geometry_from_pose(t, q)
    else:
        meta = pd.read_csv(cfg["meta"]); ids = meta.scan.values.astype(int)
        zr = meta.range_m.values; zu = meta[["ux", "uy", "uz"]].values
        pr = np.load(cfg["pred"]); ndist = pr["ndist"]; insup = pr["insup"]
    tasks = [(tag, i, ids[i], zr[i], zu[i], ndist[i], insup[i]) for i in range(len(ids))]
    import time; t0 = time.perf_counter(); allrows = []
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, rows in enumerate(ex.map(_one, tasks, chunksize=2)):
            allrows.extend(rows)
            if (k + 1) % 200 == 0:
                print(f"[g1 {tag}] {k+1}/{len(ids)} {time.perf_counter()-t0:.0f}s", flush=True)
    df = pd.DataFrame(allrows)
    df.to_csv(os.path.join(OUT, f"g1_oracle_{tag}.csv"), index=False)
    print(f"[g1 {tag}] DONE frames={len(ids)} rows={len(df)} {time.perf_counter()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("tags", nargs="+"); ap.add_argument("--nw", type=int, default=22)
    a = ap.parse_args()
    for t in a.tags:
        run(t, a.nw)
