# -*- coding: utf-8 -*-
"""replay79.py -- UNIFIED FROZEN REPLAY for items 7 (Patch x robust loss) and 9 (view support).

NO parameter is tuned and NO method is selected on II/III outcomes. Every registration is the
frozen g_common.robust_icp, GT-local (x0=0), basin 0.30m/15deg, Huber delta=1.345 + MAD(1.4826)
scale with the RAW-model NN spacing floor, Trim keep=0.80 -- identical for every arm. Patch geometry
is the frozen view-INDEPENDENT mu_patch (same frozen mu_j for ls/huber/trim); Full is the frozen
oracle view-conditioned field. The ONLY new evaluations are the two mechanical crosses
Patch+Huber / Patch+Trim (same corrected target, only per-correspondence weight changes).

Scope (locked): VI all 501; IV/II/III in-support ONLY (matches master primary); V ALL 1868 (item 9).
Blocks are JOINED from frozen artifacts (master frame for VI/IV/II/III; g0_frame_v for V), never
recomputed, so every paired statistic inherits the existing frozen block definition.

Verification (hard gates, logged): Raw LS==g1 M0, Huber/Trim==g0 p2p forms, Patch LS==g1 M4,
Full LS==g1 M5; predicted dxi==stored ext_predict dxi; nearest_d==g1 nearest_d.
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

import os
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys, time
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, _pp("AUDIT_FOLLOWUP/scripts"))
import af_common as A
import m_common as M
import g_common as G

OUT = A.OUT.replace("AUDIT_FOLLOWUP", "FOLLOWUP_6_9")
os.makedirs(OUT, exist_ok=True)
K = G.KSTAR
_G = {}


def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    fz = A.frozen_bundle()
    model, normals, plab, mp = fz["model"], fz["normals"], fz["plab"], fz["mu_patch"]
    mpatch = model + mp[plab]
    _G.update(model=model, normals=normals, plab=plab, sf=fz["s_floor"],
              Vmean=fz["Vmean"], Vcnt=fz["Vcnt"], vrange=fz["vrange"], uview=fz["uview"],
              mu_patch=mp, tree_raw=cKDTree(model), tree_patch=cKDTree(mpatch),
              OBJ=M.Objective(model, normals))


# --------------------------------------------------------------- frozen view-support descriptor
def view_support(zr, zu):
    """Exact replica of g_common.mu_for_view, additionally exposing k=16 neighbor geometry,
    kernel ESS, per-patch valid observations, coverage and fallback count."""
    Vmean, Vcnt, vrange, uview = _G["Vmean"], _G["Vcnt"], _G["vrange"], _G["uview"]
    Dv = np.sqrt(((vrange - zr) / G.RANGE_STD) ** 2 + np.arccos(np.clip(uview @ zu, -1, 1)) ** 2)
    order = np.argsort(Dv)[:K]
    dk = max(Dv[order[-1]], 1e-9)
    w = np.exp(-0.5 * (Dv[order] / dk) ** 2)
    wc = Vcnt[order] > 0                                   # (16,24) valid patch-neighbor obs
    num = np.einsum("k,kpj,kp->pj", w, Vmean[order], wc)
    den = (w[:, None] * wc).sum(0)
    mu = np.zeros((G.N_PATCH, 3)); ok = den > 0; mu[ok] = num[ok] / den[ok, None]
    n_fallback = int((~ok).sum())
    if (~ok).any():                                        # identical all-library fallback branch
        aw = 1.0 / (1.0 + Dv)
        for j in np.where(~ok)[0]:
            seen = Vcnt[:, j] > 0
            if seen.any():
                mu[j] = (aw[seen, None] * Vmean[seen, j]).sum(0) / aw[seen].sum()
    ess = float((w.sum() ** 2) / (w ** 2).sum())           # kernel effective sample size
    n_valid_obs = int(wc.sum())                            # valid patch-neighbor observations (<=16*24)
    coverage = float(ok.sum() / G.N_PATCH)
    d16 = Dv[order]
    return mu, dict(nearest_d=float(Dv.min()), k_min=float(d16.min()), k_median=float(np.median(d16)),
                    k_max=float(dk), ess_kernel=ess, n_valid_patchobs=n_valid_obs,
                    coverage=coverage, n_fallback=n_fallback)


def predicted_dxi(P, nnidx, mu):
    """r8-equivalent predicted step -H^-1 g on GT-local nominal correspondence (p2p & p2l)."""
    lab = _G["plab"][nnidx]
    m_nom = _G["model"][nnidx]
    Qhat = m_nom + mu[lab]
    gh = M.grad_hess(_G["OBJ"], Qhat)
    gn = M.grad_hess(_G["OBJ"], m_nom)
    dxi = np.column_stack([-np.linalg.pinv(gn["Hp"]) @ gh["gp"],
                           -np.linalg.pinv(gn["Hl"]) @ gh["gl"]])
    return dxi


def final_weight_stats(target, tree, P, R, t, form):
    """Recompute the CONVERGED-iteration per-correspondence weight vector (frozen rules) for
    effective weighted-point diagnostics. Does not change the solved pose."""
    Q = (R @ P.T).T + t
    _, idx = tree.query(Q, k=1, workers=2)
    e = Q - target[idx]
    metric = np.linalg.norm(e, axis=1)
    n = len(P)
    if form == "ls":
        w = np.ones(n); keep = 1.0
    elif form == "huber":
        w, _ = G.huber_weights(metric, G.HUBER_DELTA, _G["sf"]); keep = np.nan
    else:
        w, keep = G.trim_weights(metric, G.TRIM_KEEP)
    sumw = float(w.sum())
    ess = float(sumw ** 2 / (w ** 2).sum())
    return dict(n_points=n, wmean=float(w.mean()), sumw=sumw, ess_w=ess,
                keep_ratio=(float(keep) if not np.isnan(keep) else np.nan),
                n_retain=(int(round(keep * n)) if not np.isnan(keep) else int(np.sum(w > 0))))


def reg(target, tree, P, form):
    r = G.robust_icp(target, _G["normals"], tree, P, "p2p", form, s_floor=_G["sf"])
    xi = r["xi"]
    fw = final_weight_stats(target, tree, P, r["R"], r["t"], form)
    fw.update(et_mm=float(np.linalg.norm(xi[:3]) * 1000), eR_deg=float(np.degrees(np.linalg.norm(xi[3:]))),
              iters=int(r["iters"]), on_bound=int(r["on_bound"]), xi=xi)
    return fw


def cos3(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 1e-12 and nb > 1e-12 else np.nan


def _one(args):
    traj, order, sid, zr, zu, scandir = args
    P = A.load_aligned(scandir, sid)
    z = np.load(os.path.join(scandir, f"scan_{int(sid):04d}.npz"))
    nnidx = z["nnidx"]
    mu_full, sup = view_support(zr, zu)
    mfull = _G["model"] + mu_full[_G["plab"]]
    tree_full = cKDTree(mfull)
    corr_full = np.linalg.norm(mu_full, axis=1) * 1000
    corr_patch = np.linalg.norm(_G["mu_patch"], axis=1) * 1000
    sup.update(corr_full_mean_mm=float(corr_full.mean()), corr_full_median_mm=float(np.median(corr_full)),
               corr_patch_mean_mm=float(corr_patch.mean()),
               nearest_over_tau=float(sup["nearest_d"] / G.TAU_SUPPORT), range_m=float(zr))
    arms = {}
    arms["Raw"] = reg(_G["model"], _G["tree_raw"], P, "ls")
    arms["Huber"] = reg(_G["model"], _G["tree_raw"], P, "huber")
    arms["Trim"] = reg(_G["model"], _G["tree_raw"], P, "trim")
    arms["Patch"] = reg(_G["model"] + _G["mu_patch"][_G["plab"]], _G["tree_patch"], P, "ls")
    arms["PatchHuber"] = reg(_G["model"] + _G["mu_patch"][_G["plab"]], _G["tree_patch"], P, "huber")
    arms["PatchTrim"] = reg(_G["model"] + _G["mu_patch"][_G["plab"]], _G["tree_patch"], P, "trim")
    arms["Full"] = reg(mfull, tree_full, P, "ls")
    dxi = predicted_dxi(P, nnidx, mu_full)
    sup["pred_mag_t_mm"] = float(np.linalg.norm(dxi[:3, 0]) * 1000)
    sup["cos_pred_raw_t"] = cos3(dxi[:3, 0], arms["Raw"]["xi"][:3])
    sup["cos_pred_full_t"] = cos3(dxi[:3, 0], arms["Full"]["xi"][:3])
    arows = []
    for name, d in arms.items():
        r = dict(trajectory=traj, order=order, scan=int(sid), arm=name)
        for k in ["et_mm", "eR_deg", "iters", "on_bound", "n_points", "wmean", "sumw",
                  "ess_w", "keep_ratio", "n_retain"]:
            r[k] = d[k]
        arows.append(r)
    srow = dict(trajectory=traj, order=order, scan=int(sid), **sup,
                raw_et_mm=arms["Raw"]["et_mm"], patch_et_mm=arms["Patch"]["et_mm"], full_et_mm=arms["Full"]["et_mm"],
                raw_eR_deg=arms["Raw"]["eR_deg"], patch_eR_deg=arms["Patch"]["eR_deg"], full_eR_deg=arms["Full"]["eR_deg"],
                full_minus_patch_mm=arms["Patch"]["et_mm"] - arms["Full"]["et_mm"],
                full_minus_raw_mm=arms["Raw"]["et_mm"] - arms["Full"]["et_mm"])
    return arows, srow


def frame_tasks():
    tasks, keep_order = {}, {}
    zr, zu = A.vi_view_geometry()
    tasks["VI"] = [("VI", i, i, float(zr[i]), zu[i], os.path.join(A.M.CACHE, "scans")) for i in range(501)]
    keep_order["VI"] = list(range(501))
    for tr in ["IV", "II", "III"]:
        cfg = A.REG[tr]; meta = pd.read_csv(cfg["meta"]); P = np.load(cfg["pred"])
        insup = P["insup"].astype(bool)
        idx = np.where(insup)[0]                       # in-support ONLY for IV/II/III
        tasks[tr] = [(tr, int(i), int(meta.scan.iloc[i]), float(meta.range_m.iloc[i]),
                      np.array([float(meta.ux.iloc[i]), float(meta.uy.iloc[i]), float(meta.uz.iloc[i])]),
                      cfg["scandir"]) for i in idx]
        keep_order[tr] = idx.tolist()
    # V: ALL frames
    cfg = A.REG["V"]; meta = pd.read_csv(cfg["meta"]); P = np.load(cfg["pred"])
    tasks["V"] = [("V", int(i), int(meta.scan.iloc[i]), float(meta.range_m.iloc[i]),
                   np.array([float(meta.ux.iloc[i]), float(meta.uy.iloc[i]), float(meta.uz.iloc[i])]),
                   cfg["scandir"]) for i in range(len(meta))]
    keep_order["V"] = list(range(len(meta)))
    return tasks


def frozen_block_lookup():
    mf = pd.read_csv(os.path.join(A.ROOT, "POSE_AUDIT", "results", "master_pose_results_frame.csv"))
    look = {}
    for tr in ["VI", "IV", "II", "III"]:
        q = mf[mf.trajectory == tr][["order", "block"]].drop_duplicates()
        look[tr] = dict(zip(q.order, q.block))
    g0v = pd.read_csv(os.path.join(A.GCHAIN, "G0_ROBUST_FALSIFICATION", "results", "g0_frame_v.csv"))
    q = g0v[["order", "block"]].drop_duplicates()
    look["V"] = dict(zip(q.order, q.block))
    return look


def run(nw=16):
    tasks = frame_tasks(); blok = frozen_block_lookup()
    arms_all, sup_all = [], []
    for tr in ["VI", "IV", "II", "III", "V"]:
        t0 = time.perf_counter(); arows, srows = [], []
        with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
            for k, (a, s) in enumerate(ex.map(_one, tasks[tr], chunksize=3)):
                arows.extend(a); srows.append(s)
                if (k + 1) % 500 == 0:
                    print(f"  [R79 {tr}] {k+1}/{len(tasks[tr])} {time.perf_counter()-t0:.0f}s", flush=True)
        AD = pd.DataFrame(arows); SD = pd.DataFrame(srows)
        AD["block"] = AD.order.map(blok[tr]); SD["block"] = SD.order.map(blok[tr])
        AD["in_support"] = tr != "V"; SD["in_support"] = tr != "V"
        assert AD.block.notna().all() and SD.block.notna().all(), (tr, "block join failed")
        arms_all.append(AD); sup_all.append(SD)
        print(f"[R79 {tr}] done {len(tasks[tr])} frames in {time.perf_counter()-t0:.0f}s", flush=True)
    ADF = pd.concat(arms_all, ignore_index=True); SDF = pd.concat(sup_all, ignore_index=True)
    ADF.to_csv(os.path.join(OUT, "scripts", "replay79_arms.csv"), index=False)
    SDF.to_csv(os.path.join(OUT, "scripts", "replay79_support.csv"), index=False)
    print("[R79] wrote raw replay tables")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--nw", type=int, default=16)
    run(ap.parse_args().nw)
