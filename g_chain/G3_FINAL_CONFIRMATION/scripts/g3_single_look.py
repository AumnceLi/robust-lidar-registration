# -*- coding: utf-8 -*-
"""g3_single_look.py -- the ONE-AND-ONLY frozen-chain evaluation on untouched Dataset III.
Runs the already-frozen G0 (robust falsification + matched self-null), G1 (oracle M0-M5) and G2 (estimated-view
arms) per frame with byte-identical calls to g_common; nothing is tuned, no frame is removed, no re-run on outcome.
Primary set = in-support frames; secondary = all 1302. Outputs g0_iii.csv / g1_iii.csv / g2_iii.csv and a
combined single_look_results.csv. The confirmation verdict is computed by g3_decide.py from these CSVs only."""
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
from scipy.spatial import cKDTree
sys.path.insert(0, _pp("g_chain/common"))
sys.path.insert(0, _pp("structured_mismatch_phase0/scripts"))
import g_common as G
import s0_common as C, m_common as M

ROOT = _pp("g_chain/G3_FINAL_CONFIRMATION")
CACHE = os.path.join(ROOT, "iii_cache"); DATA = os.path.join(ROOT, "download", "epos_dataset_iii")
OUT = os.path.join(ROOT, "results"); os.makedirs(OUT, exist_ok=True)
FORMS = ["ls", "huber", "trim"]; KINDS = ["p2p", "p2l"]
_G = {}

def _init(selfidx_all):
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    fz = G.load_frozen()
    model, normals, plab = fz["model"], fz["normals"], fz["plab"]
    mg, mp = G.hierarchy_library(fz["Vmean"], fz["Vcnt"])
    mglob = G.corrected_model(model, plab, mg, mp, None, "global")
    mpatch = G.corrected_model(model, plab, mg, mp, None, "patch")
    _G.update(model=model, normals=normals, plab=plab, Vmean=fz["Vmean"], Vcnt=fz["Vcnt"],
              vrange=fz["vrange"], uview=fz["uview"], mu_global=mg, mu_patch=mp,
              tree_raw=cKDTree(model), tree_glob=cKDTree(mglob), tree_patch=cKDTree(mpatch),
              sfloor=fz["s_floor"], selfidx=selfidx_all)

def et(x): return np.linalg.norm(x[:3]) * 1000.0
def eR(x): return np.degrees(np.linalg.norm(x[3:]))
def cos3(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 1e-12 and nb > 1e-12 else np.nan

def J_raw(P, xi, tree, model):
    Q = M.apply_xi(P, xi); _, idx = tree.query(Q, k=1, workers=2)
    return float(np.einsum("ij,ij->i", Q - model[idx], Q - model[idx]).mean())

def _one(args):
    order_i, sid, zr, zu, ndist, insup = args
    model, normals, plab, sf = _G["model"], _G["normals"], _G["plab"], _G["sfloor"]
    P = np.load(os.path.join(CACHE, f"scan_{int(sid):04d}.npz"))["aligned"].astype(np.float64)
    t_gt, q_gt = G.load_pose_dir(os.path.join(DATA, f"{int(sid):04d}.pose")); R_gt = C.quat_to_R(q_gt)
    blk = int(order_i // 50)
    g0, g1, g2 = [], [], []
    # ---------------- G0: robust falsification + matched self-null ----------------
    S = model[_G["selfidx"][order_i]]
    for kind in KINDS:
        for form in FORMS:
            gn, _ = G.robust_grad_norm(model, normals, _G["tree_raw"], P, kind, form, sf)
            r = G.robust_icp(model, normals, _G["tree_raw"], P, kind, form, s_floor=sf)
            Jgt = G.robust_objective(model, normals, _G["tree_raw"], P, np.zeros(6), kind, form, sf)
            g0.append(dict(kind=kind, form=form, real=1, g_gt=gn, et_mm=et(r["xi"]), eR_deg=eR(r["xi"]),
                           J_gt=Jgt, J_star=r["Jlast"], dJ=Jgt - r["Jlast"], iters=r["iters"]))
            gns, _ = G.robust_grad_norm(model, normals, _G["tree_raw"], S, kind, form, sf)
            rs = G.robust_icp(model, normals, _G["tree_raw"], S, kind, form, s_floor=sf)
            g0.append(dict(kind=kind, form=form, real=0, g_gt=gns, et_mm=et(rs["xi"]), eR_deg=eR(rs["xi"]),
                           J_gt=np.nan, J_star=rs["Jlast"], dJ=np.nan, iters=rs["iters"]))
    for r in g0:
        r.update(traj="iii", order=order_i, scan=int(sid), ndist=float(ndist), in_support=bool(insup),
                 block=blk, n=len(P))
    # ---------------- G1: oracle M0-M5 ----------------
    mu_full, dmin = G.mu_for_view(_G["Vmean"], _G["Vcnt"], _G["vrange"], _G["uview"], zr, zu)
    mfull = G.corrected_model(model, plab, _G["mu_global"], _G["mu_patch"], mu_full, "full")
    tree_full = cKDTree(mfull)
    methods = [("M0_raw_p2p", model, _G["tree_raw"], "p2p", "ls"),
               ("M1_raw_p2l", model, _G["tree_raw"], "p2l", "ls"),
               ("M2_raw_huber", model, _G["tree_raw"], "p2p", "huber"),
               ("M3_global_corr", None, _G["tree_glob"], "p2p", "ls"),
               ("M4_patch_corr", None, _G["tree_patch"], "p2p", "ls"),
               ("M5_full_corr", mfull, tree_full, "p2p", "ls")]
    for name, tgt, tree, kind, form in methods:
        if tgt is None: tgt = np.asarray(tree.data)
        rr = G.robust_icp(tgt, normals, tree, P, kind, form, s_floor=sf); xi = rr["xi"]
        gn, _ = G.robust_grad_norm(tgt, normals, tree, P, kind, form, sf)
        g1.append(dict(method=name, et_mm=et(xi), eR_deg=eR(xi), g_corr_gt=gn,
                       J_raw_gt=J_raw(P, np.zeros(6), _G["tree_raw"], model),
                       J_raw_final=J_raw(P, xi, _G["tree_raw"], model), iters=rr["iters"],
                       traj="iii", order=order_i, scan=int(sid), view="oracle",
                       ndist=float(ndist), in_support=bool(insup), nearest_d=float(dmin)))
    # ---------------- G2: estimated-view arms ----------------
    xi0 = G.robust_icp(model, normals, _G["tree_raw"], P, "p2p", "ls", s_floor=sf)["xi"]
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
    va = float(np.degrees(np.arccos(np.clip(uGT @ u0, -1, 1))))
    arms = [("T0_raw", xi0), ("oracle", xi_orc), ("est_gtstart", xi_eg), ("est_warmstart", xi_ew)]
    for arm, x in arms:
        g2.append(dict(traj="iii", order=order_i, scan=int(sid), ndist=float(ndist),
                       in_support=bool(insup), arm=arm, et_mm=float(et(x)), eR_deg=float(eR(x))))
    g2.append(dict(traj="iii", order=order_i, scan=int(sid), ndist=float(ndist), in_support=bool(insup),
                   arm="view_gap", et_mm=va, eR_deg=abs(r0 - rGT) * 1000,
                   corr_dir_cos=cos3(mu_orc.sum(0), mu_est.sum(0)), disp_dir_cos=cos3(xi_orc[:3], xi_eg[:3])))
    return g0, g1, g2

def run(nw=26):
    meta = pd.read_csv(os.path.join(CACHE, "meta_iii.csv")); pr = np.load(os.path.join(CACHE, "ext_predict_iii.npz"))
    ids = meta.scan.values.astype(int); zr = meta.range_m.values; zu = meta[["ux", "uy", "uz"]].values
    ndist, insup = pr["ndist"], pr["insup"]
    assert len(ids) == 1302 and int(insup.sum()) == 371, (len(ids), int(insup.sum()))
    rng = np.random.default_rng(42); modeln = len(G.load_frozen()["model"])
    npts = [int(meta.n.iloc[i]) for i in range(len(ids))]
    selfidx = [rng.choice(modeln, n, replace=False) for n in npts]
    tasks = [(i, ids[i], zr[i], zu[i], ndist[i], insup[i]) for i in range(len(ids))]
    t0 = time.perf_counter(); A, B, Cc = [], [], []
    with ProcessPoolExecutor(max_workers=nw, initializer=_init, initargs=(selfidx,)) as ex:
        for k, (a, b, c) in enumerate(ex.map(_one, tasks, chunksize=2)):
            A.extend(a); B.extend(b); Cc.extend(c)
            if (k + 1) % 200 == 0: print(f"[g3] {k+1}/{len(ids)} {time.perf_counter()-t0:.0f}s", flush=True)
    g0 = pd.DataFrame(A); g1 = pd.DataFrame(B); g2 = pd.DataFrame(Cc)
    g0.to_csv(os.path.join(OUT, "g0_iii.csv"), index=False)
    g1.to_csv(os.path.join(OUT, "g1_iii.csv"), index=False)
    g2.to_csv(os.path.join(OUT, "g2_iii.csv"), index=False)
    # combined wide table (p2p real for G0; methods for G1; arms for G2)
    g0p = g0[(g0.kind == "p2p") & (g0.real == 1)].pivot_table(index="scan", columns="form", values="et_mm")
    g0s = g0[(g0.kind == "p2p") & (g0.real == 0)].groupby("scan").et_mm.median()
    g1w = g1.pivot_table(index="scan", columns="method", values="et_mm")
    g2w = g2[g2.arm != "view_gap"].pivot_table(index="scan", columns="arm", values="et_mm")
    comb = pd.concat([g0p.add_prefix("g0_"), g0s.rename("g0_selfnull_et"), g1w, g2w], axis=1)
    comb = comb.merge(meta[["scan", "range_m"]], left_index=True, right_on="scan")
    comb["in_support"] = comb.scan.map(dict(zip(ids, insup)))
    comb.to_csv(os.path.join(OUT, "single_look_results.csv"), index=False)
    print(f"[g3] DONE {len(ids)} frames in {time.perf_counter()-t0:.0f}s; in-support {int(insup.sum())}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--nw", type=int, default=26); a = ap.parse_args()
    run(a.nw)
