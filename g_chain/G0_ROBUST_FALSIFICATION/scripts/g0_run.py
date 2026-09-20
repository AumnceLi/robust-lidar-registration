# -*- coding: utf-8 -*-
"""g0_run.py -- run the frozen G0 harness on VI/IV/II/V (real cloud + matched model-self null).
No parameter is chosen here; everything is read from g_common / frozen_config. Per-trajectory raw npz."""
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

import os, sys, time, argparse
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G
import s0_common as C, m_common as M

CACHE = M.CACHE
TJ = _pp("tj2_supplemental")
OUT = _pp("g_chain/G0_ROBUST_FALSIFICATION/results")
os.makedirs(OUT, exist_ok=True)
FORMS = ["ls", "huber", "trim"]
KINDS = ["p2p", "p2l"]

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
    from scipy.spatial import cKDTree
    _G.update(model=fz["model"], normals=fz["normals"], sfloor=fz["s_floor"],
              tree=cKDTree(fz["model"]), vi_blocks=fz["vi_blocks"])

def _load_aligned(tag, scandir, scan_id):
    if tag == "vi":
        return M.load_scan(int(scan_id))["aligned"].astype(np.float64)
    return np.load(os.path.join(scandir, f"scan_{int(scan_id):04d}.npz"))["aligned"].astype(np.float64)

def _one(args):
    tag, order_i, scan_id, selfidx, ndist, insup = args
    model, normals, tree, sfloor = _G["model"], _G["normals"], _G["tree"], _G["sfloor"]
    P = _load_aligned(tag, REG[tag]["scandir"], scan_id)
    S = model[selfidx]
    rows = []
    blk = int(_G["vi_blocks"][order_i]) if tag == "vi" else int(order_i // 50)
    for kind in KINDS:
        for form in FORMS:
            gn, _ = G.robust_grad_norm(model, normals, tree, P, kind, form, sfloor)
            r = G.robust_icp(model, normals, tree, P, kind, form, s_floor=sfloor)
            Jgt = G.robust_objective(model, normals, tree, P, np.zeros(6), kind, form, sfloor)
            et = np.linalg.norm(r["xi"][:3]) * 1000.0
            eR = np.degrees(np.linalg.norm(r["xi"][3:]))
            rows.append(dict(kind=kind, form=form, real=1, g_gt=gn, et_mm=et, eR_deg=eR,
                             J_gt=Jgt, J_star=r["Jlast"], dJ=Jgt - r["Jlast"], iters=r["iters"],
                             on_bound=int(r["on_bound"]), wmean=r["wmean"], keep=r["keep"]))
            # matched self-null
            gns, _ = G.robust_grad_norm(model, normals, tree, S, kind, form, sfloor)
            rs = G.robust_icp(model, normals, tree, S, kind, form, s_floor=sfloor)
            rows.append(dict(kind=kind, form=form, real=0, g_gt=gns,
                             et_mm=np.linalg.norm(rs["xi"][:3]) * 1000.0,
                             eR_deg=np.degrees(np.linalg.norm(rs["xi"][3:])),
                             J_gt=np.nan, J_star=rs["Jlast"], dJ=np.nan, iters=rs["iters"],
                             on_bound=int(rs["on_bound"]), wmean=rs["wmean"], keep=rs["keep"]))
    meta_row = dict(traj=tag, order=order_i, scan=int(scan_id), ndist=float(ndist),
                    in_support=bool(insup), block=blk, n=len(P))
    for r in rows:
        r.update(meta_row)
    return rows

def run(tag, nw=22):
    cfg = REG[tag]
    if tag == "vi":
        ids = np.arange(501)
        ndist = np.zeros(501); insup = np.ones(501, bool)
    else:
        meta = pd.read_csv(cfg["meta"])
        ids = meta.scan.values.astype(int)
        pr = np.load(cfg["pred"])
        assert len(pr["ids"]) == len(ids), (len(pr["ids"]), len(ids))
        ndist = pr["ndist"]; insup = pr["insup"]
    rng = np.random.default_rng(42)
    modeln = len(G.load_frozen()["model"])
    npts = [len(_load_aligned(tag, cfg["scandir"], i)) for i in ids]
    selfidx = [rng.choice(modeln, n, replace=False) for n in npts]
    tasks = [(tag, i, ids[i], selfidx[i], ndist[i], insup[i]) for i in range(len(ids))]
    t0 = time.perf_counter(); allrows = []
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, rows in enumerate(ex.map(_one, tasks, chunksize=2)):
            allrows.extend(rows)
            if (k + 1) % 200 == 0:
                print(f"[{tag}] {k+1}/{len(ids)} {time.perf_counter()-t0:.0f}s", flush=True)
    df = pd.DataFrame(allrows)
    df.to_csv(os.path.join(OUT, f"g0_frame_{tag}.csv"), index=False)
    np.savez_compressed(os.path.join(OUT, f"g0_selfidx_{tag}.npz"),
                        ids=ids, ndist=ndist, insup=insup)
    print(f"[{tag}] DONE n_frames={len(ids)} rows={len(df)} {time.perf_counter()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("tags", nargs="+")
    ap.add_argument("--nw", type=int, default=22)
    a = ap.parse_args()
    for t in a.tags:
        run(t, a.nw)
