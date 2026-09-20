# -*- coding: utf-8 -*-
"""hierarchy_transfer.py -- POST-HOC / POST-DEVELOPMENT EXPLORATORY ANALYSIS (section E).
Frozen global / patch / full view-conditioned mismatch levels re-evaluated on IV and II (V as note).
Directional cosine of the predicted local correction step vs the OBSERVED GT-started optimum translation.
NO parameter is fit here; the FULL frozen VI library is used (deployed definition), matching r8 external query."""
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
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G
import m_common as M

CACHE = M.CACHE; TJ = _pp("tj2_supplemental"); OUT = _pp("g_chain/HIERARCHY_TRANSFER/results")
os.makedirs(OUT, exist_ok=True)
CFG = {
 "iv": dict(scandir=os.path.join(CACHE, "ext", "iv"), obj=os.path.join(CACHE, "ext", "ext_objective_iv.npz"),
            meta=os.path.join(CACHE, "ext", "meta_iv.csv"), pred=os.path.join(CACHE, "ext", "ext_predict_iv.npz")),
 "ii": dict(scandir=os.path.join(TJ, "cache", "ii"), obj=os.path.join(TJ, "cache", "ii", "ext_objective_ii.npz"),
            meta=os.path.join(TJ, "cache", "ii", "meta_ii.csv"), pred=os.path.join(TJ, "cache", "ii", "ext_predict_ii.npz")),
 "v":  dict(scandir=os.path.join(CACHE, "ext", "v"), obj=os.path.join(CACHE, "ext", "ext_objective_v.npz"),
            meta=os.path.join(CACHE, "ext", "meta_v.csv"), pred=os.path.join(CACHE, "ext", "ext_predict_v.npz")),
}
_G = {}
def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    fz = G.load_frozen()
    mg, mp = G.hierarchy_library(fz["Vmean"], fz["Vcnt"])
    _G.update(model=fz["model"], plab=fz["plab"], Vmean=fz["Vmean"], Vcnt=fz["Vcnt"],
              vrange=fz["vrange"], uview=fz["uview"], mu_global=mg, mu_patch=mp, obj=M.Objective())

def cos(a, b):
    na, nb = np.linalg.norm(a[:3]), np.linalg.norm(b)
    return float(a[:3] @ b / (na * nb)) if na > 1e-12 and nb > 1e-12 else np.nan

def _one(args):
    tag, order_i, sid, zr, zu, obs3 = args
    z = np.load(os.path.join(CFG[tag]["scandir"], f"scan_{int(sid):04d}.npz"))
    P = z["aligned"].astype(np.float64); nn = z["nnidx"]; m = _G["model"][nn]; lab = _G["plab"][nn]
    Hp = M.grad_hess(_G["obj"], m)["Hp"]; pinvH = np.linalg.pinv(Hp)
    def step(Q): return -pinvH @ M.grad_hess(_G["obj"], Q)["gp"]
    qg = np.broadcast_to(_G["mu_global"], (len(nn), 3))
    mu_f, _ = G.mu_for_view(_G["Vmean"], _G["Vcnt"], _G["vrange"], _G["uview"], zr, zu)
    cg = cos(step(m + qg), obs3); cp = cos(step(m + _G["mu_patch"][lab]), obs3)
    cf = cos(step(m + mu_f[lab]), obs3)
    return dict(traj=tag, order=order_i, scan=int(sid), cos_global=cg, cos_patch=cp, cos_full=cf)

def run(tag, nw=24):
    cfg = CFG[tag]
    E = np.load(cfg["obj"]); PR = np.load(cfg["pred"]); meta = pd.read_csv(cfg["meta"])
    ids = E["ids"]; obs = E["raw__xistar"][:, :3, 0]; zr = meta.range_m.values; zu = meta[["ux", "uy", "uz"]].values
    insup = PR["insup"]
    msk = insup if insup.sum() > 0 else np.ones(len(ids), bool)   # V: all (out-support note)
    idx = np.where(msk)[0]
    tasks = [(tag, i, ids[i], zr[i], zu[i], obs[i]) for i in idx]
    import time; t0 = time.perf_counter(); rows = []
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, r in enumerate(ex.map(_one, tasks, chunksize=2)):
            rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, f"{tag}_global_patch_full.csv"), index=False)
    # block stats: median + moving block bootstrap CI
    srows = []
    for lvl in ["cos_global", "cos_patch", "cos_full"]:
        x = df[lvl].values; bb = G.block_boot(np.nan_to_num(x, nan=0.0), np.median, B=2000, Ls=(5, 10, 20), seed=42)
        srows.append(dict(traj=tag, level=lvl, n=len(x), median=float(np.nanmedian(x)),
                          mean=float(np.nanmean(x)), L5_lo=bb["L5_lo"], L5_hi=bb["L5_hi"]))
    print(f"[{tag}] n={len(df)}  global {np.nanmedian(df.cos_global):.3f}  patch {np.nanmedian(df.cos_patch):.3f}  full {np.nanmedian(df.cos_full):.3f}  ({time.perf_counter()-t0:.0f}s)", flush=True)
    return pd.DataFrame(srows)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("tags", nargs="+"); ap.add_argument("--nw", type=int, default=24)
    a = ap.parse_args()
    alls = [run(t, a.nw) for t in a.tags]
    pd.concat(alls, ignore_index=True).to_csv(os.path.join(OUT, "block_stats.csv"), index=False)
    print("[saved] block_stats.csv")
