# -*- coding: utf-8 -*-
"""g2_perturb.py -- FROZEN sensitivity of the view-conditioned correction to initial-pose/view error.
Grid fixed BEFORE outcomes (D3): translation {10,25,50,100} mm along each body axis;
rotation {0.25,0.5,1,2} deg about each axis; combined (25mm+0.5),(50+1),(100+2).
We perturb the GT pose -> z_eps -> mu(z_eps) -> corrected model -> GT-started registration, and report
e_t/eR and the correction displacement-direction cosine vs the oracle (eps=0). Subsampled, frozen stride."""
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

OUT = _pp("g_chain/G2_ESTIMATED_VIEW/results"); os.makedirs(OUT, exist_ok=True)
T_MM = [10.0, 25.0, 50.0, 100.0]; R_DEG = [0.25, 0.5, 1.0, 2.0]
COMB = [(25.0, 0.5), (50.0, 1.0), (100.0, 2.0)]
AXES = [np.array([1., 0, 0]), np.array([0, 1., 0]), np.array([0, 0, 1.])]
CAP = 150
_G = {}

def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    fz = G.load_frozen()
    _G.update(model=fz["model"], normals=fz["normals"], plab=fz["plab"], Vmean=fz["Vmean"], Vcnt=fz["Vcnt"],
              vrange=fz["vrange"], uview=fz["uview"], tree_raw=cKDTree(fz["model"]), sfloor=fz["s_floor"])
    mg, mp = G.hierarchy_library(fz["Vmean"], fz["Vcnt"]); _G["mu_global"], _G["mu_patch"] = mg, mp

def view_from_pose(R, t):
    o = -R.T @ t; return np.linalg.norm(o), o / np.linalg.norm(o)

def corr_register(P, r, u):
    mu, _ = G.mu_for_view(_G["Vmean"], _G["Vcnt"], _G["vrange"], _G["uview"], r, u)
    mc = G.corrected_model(_G["model"], _G["plab"], _G["mu_global"], _G["mu_patch"], mu, "full")
    xi = G.robust_icp(mc, _G["normals"], cKDTree(mc), P, "p2p", "ls", s_floor=_G["sfloor"])["xi"]
    return xi, mu

def _one(args):
    tag, sid, sd, posedir = args
    P = (M.load_scan(int(sid))["aligned"] if tag == "vi" else
         np.load(os.path.join(sd, f"scan_{int(sid):04d}.npz"))["aligned"]).astype(np.float64)
    t_gt, q_gt = G.load_pose_dir(os.path.join(posedir, f"{int(sid):04d}.pose"))
    R_gt = C.quat_to_R(q_gt)
    rGT, uGT = view_from_pose(R_gt, t_gt)
    xi_orc, mu_orc = corr_register(P, rGT, uGT)
    rows = [dict(traj=tag, scan=int(sid), ptype="oracle", magnitude=0.0, axis="all",
                 et_mm=np.linalg.norm(xi_orc[:3]) * 1000, eR_deg=np.degrees(np.linalg.norm(xi_orc[3:])),
                 dir_cos=1.0)]
    def perturb(dt_m, dr_deg, ptype, axis, mag):
        Rd = M.rodrigues(axis * np.deg2rad(dr_deg)); dt = axis * (dt_m / 1000.0)
        R_e = Rd @ R_gt; t_e = Rd @ t_gt + dt
        re, ue = view_from_pose(R_e, t_e)
        xi, mu = corr_register(P, re, ue)
        dc = float(xi_orc[:3] @ xi[:3] / (np.linalg.norm(xi_orc[:3]) * np.linalg.norm(xi[:3]) + 1e-15))
        rows.append(dict(traj=tag, scan=int(sid), ptype=ptype, magnitude=float(mag), axis=str(axis.tolist()),
                         et_mm=np.linalg.norm(xi[:3]) * 1000, eR_deg=np.degrees(np.linalg.norm(xi[3:])), dir_cos=dc))
    for ax in AXES:
        for mm in T_MM: perturb(mm, 0.0, "translation", ax, mm)
        for dg in R_DEG: perturb(0.0, dg, "rotation", ax, dg)
        for (mm, dg) in COMB: perturb(mm, dg, "combined", ax, mm)
    return rows

def run(tag, nw=24):
    from g2_run import REG
    cfg = REG[tag]
    if tag == "vi":
        ids = np.arange(501)
    else:
        meta = pd.read_csv(cfg["meta"]); pr = np.load(cfg["pred"])
        ids = meta.scan.values[pr["insup"]].astype(int) if pr["insup"].sum() > 0 else meta.scan.values[::13].astype(int)
    stride = max(1, len(ids) // CAP); ids = ids[::stride][:CAP]
    tasks = [(tag, i, cfg["scandir"], cfg["posedir"]) for i in ids]
    import time; t0 = time.perf_counter(); rows = []
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, rr in enumerate(ex.map(_one, tasks, chunksize=1)):
            rows.extend(rr)
            if (k + 1) % 50 == 0: print(f"[pert {tag}] {k+1}/{len(ids)} {time.perf_counter()-t0:.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, f"g2_perturb_{tag}.csv"), index=False)
    print(f"[pert {tag}] DONE n_frames={len(ids)} {time.perf_counter()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("tags", nargs="+"); ap.add_argument("--nw", type=int, default=24)
    a = ap.parse_args()
    for t in a.tags: run(t, a.nw)
