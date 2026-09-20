# -*- coding: utf-8 -*-
"""TASK 5 (P1, strong): pose-active mechanism closed loop BEFORE/AFTER compensation.

For Raw / Patch / Full, under the IDENTICAL reference pose (xi=0 GT-aligned), identical weights
(w=(1/N)I, frozen LS) and identical correspondence convention (GT-local k=1 nearest point of THAT
arm's target), compute per frame:
  RMS(delta)              : RMS of the pointwise mismatch delta_i = P_i - target(P_i)
  ||g_t||, ||g_r||        : translation/rotation block of the ANALYTIC gradient g=J'W delta
  ||P_{J,W} delta||       : W-RMS of the projection of delta onto the pose-Jacobian column space,
                            = sqrt(g' (J'WJ)^{-1} g)  (the pose-ACTIONABLE part of mismatch)
and attach the realized frozen-solver pose errors (Raw M0 / Patch M4 / Full M5). Changes
(Raw->Patch, Raw->Full) are then correlated at BLOCK level with translation/rotation ERROR changes
(Spearman), to connect "mechanism" to "method effectiveness" -- in particular why Full fails to
improve translation and worsens rotation on II. No parameter changes; II/IV/V/III frozen oracle.
"""
import os
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys, time
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
import af_common as A
import g_common as G

G1 = os.path.join(A.GCHAIN, "G1_MITIGATION", "results")
G3 = os.path.join(A.GCHAIN, "G3_FINAL_CONFIRMATION", "results")
_G = {}


def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    fz = A.frozen_bundle()
    model, normals, plab, mp = fz["model"], fz["normals"], fz["plab"], fz["mu_patch"]
    mtrue = model + mp[plab]
    _G.update(model=model, normals=normals, plab=plab, mp=mp,
              Vmean=fz["Vmean"], Vcnt=fz["Vcnt"], vrange=fz["vrange"], uview=fz["uview"],
              tree_raw=cKDTree(model), tree_patch=cKDTree(mtrue))


def _hat(w):
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])


def pose_active(P, target, tree, kind="p2p"):
    """Analytic normal-equation quantities at xi=0 for frozen LS.

    Internal analytic gradient g_s = mean J' delta drives the Gauss-Newton solver (kabsch_step).
    The FROZEN convention used everywhere else (m_common.grad_hess FD of robust_objective = mean
    SQUARED residual) equals 2*g_s -- reported ||g_t||,||g_r|| therefore carry that same factor 2 so
    they line up with task 1 and the saved __g arrays. ||P_{J,W}delta|| is geometric (W-RMS of the
    projection onto col(J)) and is computed from the factor-1 normal equations:
    sqrt(g_s' (J'WJ)^{-1} g_s).
    """
    _, nn = tree.query(P, k=1, workers=2)
    q = target[nn]
    delta = P - q                       # (N,3) point-to-point mismatch
    N = len(P)
    if kind == "p2p":
        # stacked J_i=[I | [P_i]_x]
        gt = delta.mean(0)
        gr = np.cross(P, delta).mean(0)
        Htt = np.eye(3)
        Htr = np.stack([_hat(P[i]) for i in range(N)]).mean(0)
        Hrr = np.zeros((3, 3))
        for i in range(N):
            hx = _hat(P[i]); Hrr += hx.T @ hx
        Hrr /= N
        rms = float(np.sqrt((delta ** 2).sum(1).mean()))
        H = np.block([[Htt, Htr], [Htr.T, Hrr]])
    else:
        nrm = _G["normals"][nn]
        rn = (nrm * delta).sum(1)                        # signed normal residual
        a = np.zeros((N, 6))
        a[:, :3] = nrm
        a[:, 3:] = np.cross(P, nrm)                      # [P]_x^T n = P x n
        g = (rn[:, None] * a).mean(0)
        H = (a[:, :, None] * a[:, None, :]).mean(0)
        gt, gr = g[:3], g[3:]
        rms = float(np.sqrt((rn ** 2).mean()))
    g6 = np.concatenate([gt, gr])
    pjw2 = float(g6 @ np.linalg.solve(H, g6))
    pjw = float(np.sqrt(max(pjw2, 0)))
    # report gradient norms in the frozen FD-of-mean-squared-objective convention (factor 2)
    return (rms * 1000.0, 2.0 * float(np.linalg.norm(gt)), 2.0 * float(np.linalg.norm(gr)),
            pjw * 1000.0)


def _one(args):
    traj, order, sid, zr, ux, uy, uz, scandir = args
    P = A.load_aligned(scandir, sid)
    out = dict(order=order, scan=int(sid))
    # raw & patch (global targets)
    r_raw = pose_active(P, _G["model"], _G["tree_raw"], "p2p")
    l_raw = pose_active(P, _G["model"], _G["tree_raw"], "p2l")
    mpat = _G["model"] + _G["mp"][_G["plab"]]
    r_pat = pose_active(P, mpat, _G["tree_patch"], "p2p")
    l_pat = pose_active(P, mpat, _G["tree_patch"], "p2l")
    # full (view-conditioned target for this exact frame)
    zu = np.array([ux, uy, uz])
    mv, _ = G.mu_for_view(_G["Vmean"], _G["Vcnt"], _G["vrange"], _G["uview"], zr, zu)
    mfull = _G["model"] + mv[_G["plab"]]
    tfull = cKDTree(mfull)
    r_ful = pose_active(P, mfull, tfull, "p2p")
    l_ful = pose_active(P, mfull, tfull, "p2l")
    for nm, r, l in [("raw", r_raw, l_raw), ("patch", r_pat, l_pat), ("full", r_ful, l_ful)]:
        for kind, v in [("p2p", r), ("p2l", l)]:
            out[f"{nm}_{kind}_rms"] = v[0]; out[f"{nm}_{kind}_gt"] = v[1]
            out[f"{nm}_{kind}_gr"] = v[2]; out[f"{nm}_{kind}_pjw"] = v[3]
    return out


def pose_errors():
    """Frozen realized pose errors per trajectory/order/arm (M0 raw, M4 patch, M5 full), p2p."""
    paths = dict(VI=os.path.join(G1, "g1_oracle_vi.csv"), IV=os.path.join(G1, "g1_oracle_iv.csv"),
                 II=os.path.join(G1, "g1_oracle_ii.csv"), V=os.path.join(G1, "g1_oracle_v.csv"),
                 III=os.path.join(G3, "g1_iii.csv"))
    L = {}
    for tr, p in paths.items():
        d = pd.read_csv(p)
        keep = {}
        for arm, meth in [("raw", "M0_raw_p2p"), ("patch", "M4_patch_corr"), ("full", "M5_full_corr")]:
            q = d[d.method == meth].sort_values("order")[["order", "et_mm", "eR_deg"]].reset_index(drop=True)
            keep[arm] = q
        L[tr] = keep
    return L


def frame_tasks():
    tasks = {}; insup = {}
    # VI: view geometry from GT poses, all in support
    zr, zu = A.vi_view_geometry()
    tasks["VI"] = [("VI", i, i, float(zr[i]), zu[i, 0], zu[i, 1], zu[i, 2],
                    os.path.join(A.M.CACHE, "scans")) for i in range(501)]
    insup["VI"] = np.ones(501, bool)
    for tr in ["IV", "II", "III", "V"]:
        cfg = A.REG[tr]; meta = pd.read_csv(cfg["meta"]); P = np.load(cfg["pred"])
        tasks[tr] = [(tr, i, int(meta.scan.iloc[i]), float(meta.range_m.iloc[i]),
                      float(meta.ux.iloc[i]), float(meta.uy.iloc[i]), float(meta.uz.iloc[i]),
                      cfg["scandir"]) for i in range(len(meta))]
        insup[tr] = P["insup"].astype(bool)
    return tasks, insup


def run(nw=14):
    tasks, insup = frame_tasks(); E = pose_errors()
    long_rows = []
    vi_blocks = A.frozen_bundle()["F"]["blocks"]
    verif = []
    saved_g = dict(VI=os.path.join(A.RESC, "objective_main.npz"))
    for tr in ["VI", "IV", "II", "III", "V"]:
        t0 = time.perf_counter(); rows = []
        with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
            for k, r in enumerate(ex.map(_one, tasks[tr], chunksize=3)):
                rows.append(r)
                if (k + 1) % 1500 == 0:
                    print(f"  [T5 {tr}] {k+1}/{len(tasks[tr])} {time.perf_counter()-t0:.0f}s", flush=True)
        df = pd.DataFrame(rows).sort_values("order").reset_index(drop=True)
        ins = insup[tr]
        bf, bp = A.block_series(tr, df.order.values, ins, vi_blocks if tr == "VI" else None)
        df["in_support"] = ins; df["block_full"] = bf; df["block_primary"] = bp
        for arm in ["raw", "patch", "full"]:
            assert len(E[tr][arm]) == len(df), (tr, arm)
            df[f"{arm}_et_mm"] = E[tr][arm].et_mm.values
            df[f"{arm}_eR_deg"] = E[tr][arm].eR_deg.values
        # analytic-vs-saved-FD gradient check (raw p2p)
        if tr == "VI":
            gz = np.load(saved_g["VI"])["raw__g"][:, :, 0]
            dgt = np.abs(df.raw_p2p_gt.values - np.linalg.norm(gz[:, :3], axis=1)).max()
            dgr = np.abs(df.raw_p2p_gr.values - np.linalg.norm(gz[:, 3:], axis=1)).max()
            verif.append(dict(trajectory=tr, max_abs_dgt=float(dgt), max_abs_dgr=float(dgr)))
        elif tr != "III":
            gz = np.load(A.REG[tr]["obj"])["raw__g"][:, :, 0]
            dgt = np.abs(df.raw_p2p_gt.values - np.linalg.norm(gz[:, :3], axis=1)).max()
            dgr = np.abs(df.raw_p2p_gr.values - np.linalg.norm(gz[:, 3:], axis=1)).max()
            verif.append(dict(trajectory=tr, max_abs_dgt=float(dgt), max_abs_dgr=float(dgr)))
        # melt long
        for kind in ["p2p", "p2l"]:
            for arm in ["raw", "patch", "full"]:
                q = pd.DataFrame(dict(trajectory=tr, order=df.order, scan=df.scan,
                                      block_full=df.block_full, block_primary=df.block_primary,
                                      in_support=df.in_support, channel=kind, arm=arm,
                                      rms_delta_mm=df[f"{arm}_{kind}_rms"],
                                      gt_norm=df[f"{arm}_{kind}_gt"], gr_norm=df[f"{arm}_{kind}_gr"],
                                      pjw_delta_mm=df[f"{arm}_{kind}_pjw"],
                                      et_mm=df[f"{arm}_et_mm"], eR_deg=df[f"{arm}_eR_deg"]))
                long_rows.append(q)
        print(f"[T5 {tr}] done {len(df)} in {time.perf_counter()-t0:.0f}s", flush=True)
    L = pd.concat(long_rows, ignore_index=True)
    L.to_csv(os.path.join(A.OUT, "mechanism_before_after.csv"), index=False)
    pd.DataFrame(verif).to_csv(os.path.join(A.OUT, "scripts", "t5_analytic_vs_fd.csv"), index=False)
    block_corr(L)


def block_corr(L):
    """Block-level Spearman: change in mechanism metric vs change in pose error (primary scope)."""
    metrics = ["rms_delta_mm", "gt_norm", "gr_norm", "pjw_delta_mm", "et_mm", "eR_deg"]
    rows = []
    for tr in ["VI", "IV", "II", "III", "V"]:
        d = L[(L.trajectory == tr) & (L.channel == "p2p")]
        d = d if tr == "V" else d[d.in_support]
        for comp in ["patch", "full"]:
            ra = d[d.arm == "raw"].set_index("order")
            co = d[d.arm == comp].set_index("order")
            jx = ra.index.intersection(co.index)
            D = pd.DataFrame({"block": ra.loc[jx, "block_primary"]})
            for m in metrics:
                D["d_" + m] = co.loc[jx, m].values - ra.loc[jx, m].values
            deltas = []
            for b, q in D.groupby("block"):
                r = dict(trajectory=tr, comparison=f"raw_to_{comp}", block=int(b), n=len(q))
                for m in metrics:
                    r["d_" + m] = float(q["d_" + m].median())
                deltas.append(r)
            B = pd.DataFrame(deltas)
            if len(B) >= 4:
                for m in ["rms_delta_mm", "gt_norm", "gr_norm", "pjw_delta_mm"]:
                    for em in ["et_mm", "eR_deg"]:
                        rho, p = spearmanr(B[f"d_{m}"], B[f"d_{em}"])
                        rows.append(dict(trajectory=tr, comparison=f"raw_to_{comp}", metric=m,
                                         error=em, spearman_rho=float(rho), p=float(p), K=len(B)))
    C = pd.DataFrame(rows)
    C.to_csv(os.path.join(A.OUT, "scripts", "t5_block_spearman.csv"), index=False)
    # primary-scope median table per arm
    rows2 = []
    for (tr, arm), q in L[L.channel == "p2p"].groupby(["trajectory", "arm"]):
        qq = q if tr == "V" else q[q.in_support]
        rows2.append(dict(trajectory=tr, arm=arm, n=len(qq),
                          rms_delta_mm=qq.rms_delta_mm.median(), gt_norm=qq.gt_norm.median(),
                          gr_norm=qq.gr_norm.median(), pjw_delta_mm=qq.pjw_delta_mm.median(),
                          et_mm=qq.et_mm.median(), eR_deg=qq.eR_deg.median()))
    M = pd.DataFrame(rows2)
    M.to_csv(os.path.join(A.OUT, "scripts", "t5_arm_medians.csv"), index=False)
    print("[T5 analytic vs saved FD gradient]"); print(pd.read_csv(os.path.join(A.OUT, "scripts", "t5_analytic_vs_fd.csv")).round(2).to_string(index=False))
    print("[T5 arm medians]"); print(M.round(4).to_string(index=False))
    print("[T5] wrote mechanism_before_after.csv")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--nw", type=int, default=14)
    run(ap.parse_args().nw)
