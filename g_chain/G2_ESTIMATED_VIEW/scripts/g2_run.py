# -*- coding: utf-8 -*-
"""g2_run.py -- Estimated-View Bias-Aware Registration (deployable, one-pass; NO pose network).
Pipeline: P,M -> T0=Reg(P,M) [frozen raw p2p LS] -> z0=z(T0) -> mu_j(z0) [frozen library]
          -> M_corr(z0) -> T_hat=Reg(P,M_corr).
Three paired arms per frame:
  oracle   : correction view z=z(T_GT), second reg GT-started  (== G1 M5, mechanistic upper bound)
  est_gt   : correction view z=z(T0),    second reg GT-started  (isolates pure oracle->estimated VIEW gap)
  est_warm : correction view z=z(T0),    second reg warm-started from T0 (the true one-pass pipeline)
T0 source is frozen identically for every trajectory (raw p2p LS local optimum). No GT used except to score.
"""
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
OUT = _pp("g_chain/G2_ESTIMATED_VIEW/results"); os.makedirs(OUT, exist_ok=True)
REG = {
 "vi": dict(scandir=os.path.join(CACHE, "scans"), posedir=C.VI_DIR,
            meta=None, pred=None),
 "iv": dict(scandir=os.path.join(CACHE, "ext", "iv"),
            posedir=_pp("structured_mismatch_phase0/scripts/ivv_data/epos_dataset_iv"),
            meta=os.path.join(CACHE, "ext", "meta_iv.csv"), pred=os.path.join(CACHE, "ext", "ext_predict_iv.npz")),
 "v":  dict(scandir=os.path.join(CACHE, "ext", "v"),
            posedir=_pp("structured_mismatch_phase0/scripts/ivv_data/epos_dataset_v"),
            meta=os.path.join(CACHE, "ext", "meta_v.csv"), pred=os.path.join(CACHE, "ext", "ext_predict_v.npz")),
 "ii": dict(scandir=os.path.join(TJ, "cache", "ii"),
            posedir=_pp("tj2_supplemental/ii_data/epos_dataset_ii"),
            meta=os.path.join(TJ, "cache", "ii", "meta_ii.csv"), pred=os.path.join(TJ, "cache", "ii", "ext_predict_ii.npz")),
}
_G = {}

def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    fz = G.load_frozen()
    _G.update(model=fz["model"], normals=fz["normals"], plab=fz["plab"], Vmean=fz["Vmean"], Vcnt=fz["Vcnt"],
              vrange=fz["vrange"], uview=fz["uview"], tree_raw=cKDTree(fz["model"]),
              sfloor=fz["s_floor"])
    mg, mp = G.hierarchy_library(fz["Vmean"], fz["Vcnt"]); _G["mu_global"], _G["mu_patch"] = mg, mp

def _load_aligned(tag, sd, sid):
    if tag == "vi": return M.load_scan(int(sid))["aligned"].astype(np.float64)
    return np.load(os.path.join(sd, f"scan_{int(sid):04d}.npz"))["aligned"].astype(np.float64)

def et(x): return np.linalg.norm(x[:3]) * 1000.0
def eR(x): return np.degrees(np.linalg.norm(x[3:]))
def cos3(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 1e-12 and nb > 1e-12 else np.nan

def _one(args):
    tag, order_i, sid, ndist, insup = args
    model, plab = _G["model"], _G["plab"]
    cfg = REG[tag]
    P = _load_aligned(tag, cfg["scandir"], sid)
    t_gt, q_gt = G.load_pose_dir(os.path.join(cfg["posedir"], f"{int(sid):04d}.pose"))
    R_gt = C.quat_to_R(q_gt)
    sf = _G["sfloor"]; tree_raw = _G["tree_raw"]; normals = _G["normals"]
    # Step 1: T0 = frozen raw p2p LS local optimum (GT-started diagnostic; this is the baseline output)
    xi0 = G.robust_icp(model, normals, tree_raw, P, "p2p", "ls", s_floor=sf)["xi"]
    # oracle view and estimated view
    rGT, uGT, _ = G.view_geometry_from_pose(t_gt, q_gt)
    r0, u0 = G.estimated_view(t_gt, R_gt, xi0)
    mu_orc, _ = G.mu_for_view(_G["Vmean"], _G["Vcnt"], _G["vrange"], _G["uview"], rGT, uGT)
    mu_est, _ = G.mu_for_view(_G["Vmean"], _G["Vcnt"], _G["vrange"], _G["uview"], r0, u0)
    m_orc = G.corrected_model(model, plab, _G["mu_global"], _G["mu_patch"], mu_orc, "full")
    m_est = G.corrected_model(model, plab, _G["mu_global"], _G["mu_patch"], mu_est, "full")
    tr_orc, tr_est = cKDTree(m_orc), cKDTree(m_est)
    xi_orc = G.robust_icp(m_orc, normals, tr_orc, P, "p2p", "ls", s_floor=sf)["xi"]
    xi_eg = G.robust_icp(m_est, normals, tr_est, P, "p2p", "ls", s_floor=sf)["xi"]
    xi_ew = G.robust_icp(m_est, normals, tr_est, P, "p2p", "ls", s_floor=sf, x0=xi0, clip_basin=False)["xi"]
    view_angle = float(np.degrees(np.arccos(np.clip(uGT @ u0, -1, 1))))
    return [dict(traj=tag, order=order_i, scan=int(sid), ndist=float(ndist), in_support=bool(insup),
                 arm=arm, et_mm=float(v[0]), eR_deg=float(v[1])) for arm, v in
            [("T0_raw", (et(xi0), eR(xi0))), ("oracle", (et(xi_orc), eR(xi_orc))),
             ("est_gtstart", (et(xi_eg), eR(xi_eg))), ("est_warmstart", (et(xi_ew), eR(xi_ew)))]] + \
           [dict(traj=tag, order=order_i, scan=int(sid), ndist=float(ndist), in_support=bool(insup),
                  arm="view_gap", et_mm=view_angle, eR_deg=abs(r0 - rGT) * 1000,
                  corr_dir_cos=cos3(mu_orc.sum(0), mu_est.sum(0)),
                  disp_dir_cos=cos3(xi_orc[:3], xi_eg[:3]))]

def run(tag, nw=22):
    cfg = REG[tag]
    if tag == "vi":
        ids = np.arange(501); ndist = np.zeros(501); insup = np.ones(501, bool)
    else:
        meta = pd.read_csv(cfg["meta"]); ids = meta.scan.values.astype(int)
        pr = np.load(cfg["pred"]); ndist = pr["ndist"]; insup = pr["insup"]
    tasks = [(tag, i, ids[i], ndist[i], insup[i]) for i in range(len(ids))]
    import time; t0 = time.perf_counter(); rows = []
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, rr in enumerate(ex.map(_one, tasks, chunksize=2)):
            rows.extend(rr)
            if (k + 1) % 200 == 0: print(f"[g2 {tag}] {k+1}/{len(ids)} {time.perf_counter()-t0:.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, f"g2_{tag}.csv"), index=False)
    print(f"[g2 {tag}] DONE {len(ids)} frames {time.perf_counter()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("tags", nargs="+"); ap.add_argument("--nw", type=int, default=22)
    a = ap.parse_args()
    for t in a.tags: run(t, a.nw)
