# -*- coding: utf-8 -*-
"""
rev_common.py -- Revision Phase-1 shared library (READ-ONLY reuse of frozen code).

Hard rules honored here:
  * Never modifies/overwrites/regenerates any existing main-result file; all new
    artifacts live under revision_experiments/.
  * Imports the FROZEN numerical cores (s0_common / m_common / g_common) and calls
    them unchanged. No frozen parameter (patch/Full/DBS/support/kernel/k/patch count/
    iterator/basin/tol/robust) is re-tuned.
  * Trajectory III is treated strictly as post-hoc / secondary diagnostic.

Conventions (identical to frozen code): target frame, xi=[t(3) m, r(3) rad],
T(xi)P = exp([r])P + t, GT-started at xi=0. p2p LS weights w=1/N.
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

import os, sys, glob, hashlib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = _pp("")
PHASE = os.path.join(ROOT, "structured_mismatch_phase0", "scripts")
RESC = os.path.join(PHASE, "cache", "rescue")
EXT = os.path.join(PHASE, "cache", "ext")
IIP = os.path.join(ROOT, "tj2_supplemental", "cache", "ii")
II_DATA = os.path.join(ROOT, "tj2_supplemental", "ii_data", "epos_dataset_ii")
GCHAIN = os.path.join(ROOT, "g_chain")
GCOMMON = os.path.join(GCHAIN, "common")
G1RES = os.path.join(GCHAIN, "G1_MITIGATION", "results")
G3RES = os.path.join(GCHAIN, "G3_FINAL_CONFIRMATION", "results")
III_CACHE = os.path.join(GCHAIN, "G3_FINAL_CONFIRMATION", "iii_cache")
III_POSE = os.path.join(GCHAIN, "G3_FINAL_CONFIRMATION", "download", "epos_dataset_iii")
OUTROOT = os.path.join(ROOT, "revision_experiments")

sys.path.insert(0, PHASE)
sys.path.insert(0, GCOMMON)
import s0_common as C   # noqa: E402  (frozen IO / rotations)
import m_common as M   # noqa: E402  (frozen chart / objectives / solvers)
import g_common as G   # noqa: E402  (frozen weighted ICP / frozen constants)

# ---------------------------------------------------------------- frozen constants (re-exported, never changed)
MAX_ITER_FROZEN = G.MAX_ITER            # 40
BASIN_T = G.BASIN_T                     # 0.30 m
BASIN_R_DEG = G.BASIN_R_DEG             # 15 deg
TOL_P2P = G.TOL_P2P                     # 1e-8
P2L_REG = G.P2L_REG                     # 1e-9
TAU_SUPPORT = G.TAU_SUPPORT             # 0.4403...
N_PATCH = G.N_PATCH                     # 24
KSTAR = G.KSTAR                         # 16

TRAJS = ["VI", "IV", "II", "III"]       # Phase-1 scope (V excluded per instruction)

REG = {
    "VI": dict(n=501,
               pose_dir=os.path.join(PHASE, "vi_data", "epos_dataset_vi"),
               scan_dir=os.path.join(PHASE, "cache", "scans"),
               meta=None, pred=None,
               obj=os.path.join(RESC, "objective_main.npz"),
               g1=os.path.join(G1RES, "g1_oracle_vi.csv")),
    "IV": dict(n=2428,
               pose_dir=os.path.join(PHASE, "ivv_data", "epos_dataset_iv"),
               scan_dir=os.path.join(EXT, "iv"),
               meta=os.path.join(EXT, "meta_iv.csv"),
               pred=os.path.join(EXT, "ext_predict_iv.npz"),
               obj=os.path.join(EXT, "ext_objective_iv.npz"),
               g1=os.path.join(G1RES, "g1_oracle_iv.csv")),
    "II": dict(n=1253,
               pose_dir=II_DATA,
               scan_dir=IIP,
               meta=os.path.join(IIP, "meta_ii.csv"),
               pred=os.path.join(IIP, "ext_predict_ii.npz"),
               obj=os.path.join(IIP, "ext_objective_ii.npz"),
               g1=os.path.join(G1RES, "g1_oracle_ii.csv")),
    "III": dict(n=1302,
                pose_dir=III_POSE,
                scan_dir=III_CACHE,
                meta=os.path.join(III_CACHE, "meta_iii.csv"),
                pred=os.path.join(III_CACHE, "ext_predict_iii.npz"),
                obj=None,   # III has NO objective cache -> FD computed on demand
                g1=os.path.join(G3RES, "g1_iii.csv"),
                posthoc=True),
}


# ================================================================ frozen asset bundle (hash-verified)
_BUNDLE = None
def frozen_bundle():
    """model / frozen PCA normals / 24 patch labels / VI-trained patch field (read-only, hashed)."""
    global _BUNDLE
    if _BUNDLE is None:
        fz = G.load_frozen()  # asserts frozen predictor SHA256
        mu_global, mu_patch = G.hierarchy_library(fz["Vmean"], fz["Vcnt"])
        fz.update(mu_global=mu_global, mu_patch=mu_patch,
                  tree_model=cKDTree(fz["model"]),
                  model_patch=fz["model"] + mu_patch[fz["plab"]])
        fz["tree_patch"] = cKDTree(fz["model_patch"])
        _BUNDLE = fz
    return _BUNDLE


# ================================================================ loaders
def load_pose(pose_dir, sid):
    with open(os.path.join(pose_dir, f"{int(sid):04d}.pose"), "r") as fh:
        L = [x.strip() for x in fh if x.strip()]
    ts = float(L[0]); t = np.array(L[1].split(), float); q = np.array(L[2].split(), float)
    return ts, t, q


def load_aligned(traj, sid):
    cfg = REG[traj]
    return np.load(os.path.join(cfg["scan_dir"], f"scan_{int(sid):04d}.npz"))["aligned"].astype(np.float64)


def load_scan_npz(traj, sid):
    cfg = REG[traj]
    return np.load(os.path.join(cfg["scan_dir"], f"scan_{int(sid):04d}.npz"))


def support_mask(traj):
    cfg = REG[traj]
    if cfg["pred"] is None:
        return np.ones(cfg["n"], bool)
    return np.load(cfg["pred"])["insup"].astype(bool)


def meta_frame(traj):
    cfg = REG[traj]
    if cfg["meta"] and os.path.exists(cfg["meta"]):
        return pd.read_csv(cfg["meta"])
    return None


def realized_pose_errors(traj):
    """order -> dict(raw_et,raw_eR,patch_et,patch_eR,iters,on_bound) from FROZEN master results (read-only)."""
    d = pd.read_csv(REG[traj]["g1"])
    raw = d[d.method == "M0_raw_p2p"].sort_values("order")
    pat = d[d.method == "M4_patch_corr"].sort_values("order")
    out = {}
    for _, r in raw.iterrows():
        out[int(r.order)] = dict(raw_et=float(r.et_mm), raw_eR=float(r.eR_deg),
                                 raw_iters=int(r.iters))
    for _, r in pat.iterrows():
        out[int(r.order)]["patch_et"] = float(r.et_mm)
        out[int(r.order)]["patch_eR"] = float(r.eR_deg)
        out[int(r.order)]["patch_iters"] = int(r.iters)
    return out


def all_poses(traj):
    """Return arrays ts(n,), t(n,3), R(n,3,3) for the full ordered pose sequence."""
    cfg = REG[traj]
    n = cfg["n"]
    ts = np.zeros(n); tt = np.zeros((n, 3)); RR = np.zeros((n, 3, 3))
    for i in range(n):
        s, t, q = load_pose(cfg["pose_dir"], i)
        ts[i] = s; tt[i] = t; RR[i] = C.quat_to_R(q)
    return ts, tt, RR


def gap_flags(ts, win=3, ratio=5.0):
    """Isolated temporal discontinuities only (adaptive-rate slow regimes are NOT gaps).
    gap[i]=True when dt[i]=ts[i+1]-ts[i] exceeds ratio x the local-window median dt."""
    dt = np.diff(ts)
    n = len(dt); gap = np.zeros(n, bool)
    for i in range(n):
        lo, hi = max(0, i - win), min(n, i + win + 1)
        local = np.delete(dt[lo:hi], i - lo)
        base = np.median(local) if len(local) else np.median(dt)
        if base > 0 and dt[i] > ratio * base:
            gap[i] = True
    return dt, gap


# ================================================================ instrumented frozen ICP (mathematically identical)
def instrumented_p2p_icp(target, tree, P, max_iter,
                         bound_t=BASIN_T, bound_r_deg=BASIN_R_DEG, tol=TOL_P2P):
    """Byte-faithful copy of g_common.robust_icp for kind='p2p', formulation='ls', GT-started,
    but additionally records per-iteration diagnostics. NO algorithmic change:
    same w=1 LS, same weighted_kabsch (== Kabsch for w=1), same basin clip rule, same tol,
    same boundary partial-move-and-break, same objective definition/order of operations."""
    br = np.deg2rad(bound_r_deg)
    Racc, tacc = np.eye(3), np.zeros(3)
    hist_J, hist_xi_t, hist_xi_r = [], [], []
    prev_idx = None
    switch_counts, switch_rates = [], []
    last_step_t, last_step_r = np.nan, np.nan
    hit_t_boundary = hit_r_boundary = False
    termination = "cap"
    it = 0
    for it in range(max_iter):
        Q = (Racc @ P.T).T + tacc
        _, idx = tree.query(Q, k=1, workers=-1)
        # correspondence switches vs previous iteration (diagnostic only; does not alter the solve)
        if prev_idx is not None:
            sw = int(np.sum(idx != prev_idx))
            switch_counts.append(sw); switch_rates.append(sw / len(P))
        prev_idx = idx
        m = target[idx]
        Rd, vd = G.weighted_kabsch(Q, m, np.ones(len(P)))   # w=1 LS, identical frozen call
        Rn = Rd @ Racc
        tn = Rd @ tacc + vd
        # basin clip (identical rule); separately record which bound was active for diagnostics
        nt = np.linalg.norm(tn); nr = np.linalg.norm(M.rodrigues_log(Rn))
        f = 1.0
        if nt > bound_t: f = min(f, bound_t / nt); hit_t_boundary = True
        if nr > br:      f = min(f, br / nr); hit_r_boundary = True
        if f < 1.0:
            # frozen behavior: only tacc partially moves, Racc NOT updated, then break
            tacc = tacc + f * (tn - tacc)
            termination = "boundary"
            break
        # incremental step size (diagnostic)
        step_t = float(np.linalg.norm(tn - tacc))
        dR = Rn @ Racc.T
        step_r = float(np.degrees(np.linalg.norm(M.rodrigues_log(dR))))
        last_step_t, last_step_r = step_t, step_r
        Racc, tacc = Rn, tn
        Qn = (Rd @ Q.T).T + vd
        en = Qn - target[idx]
        J = float(np.einsum("ij,ij->i", en, en).mean())
        xi_now = M.se3_log(Racc, tacc)
        hist_J.append(J); hist_xi_t.append(float(np.linalg.norm(xi_now[:3])) * 1000.0)
        hist_xi_r.append(float(np.degrees(np.linalg.norm(xi_now[3:]))))
        if it > 0 and abs(hist_J[-2] - J) < tol * max(1, hist_J[-2]):
            termination = "tol"
            break
    actual = it + 1
    xi = M.se3_log(Racc, tacc)
    return dict(
        xi=xi, R=Racc, t=tacc,
        actual_iterations=int(actual),
        termination_reason=termination,
        hit_iteration_cap=bool(termination == "cap" and actual == max_iter),
        hit_translation_boundary=bool(hit_t_boundary and termination == "boundary"),
        hit_rotation_boundary=bool(hit_r_boundary and termination == "boundary"),
        final_objective=float(hist_J[-1]) if hist_J else np.nan,
        objective_change_last_step=float(hist_J[-2] - hist_J[-1]) if len(hist_J) >= 2 else np.nan,
        pose_change_last_step_translation_mm=float(last_step_t * 1000.0),
        pose_change_last_step_rotation_deg=float(last_step_r),
        correspondence_switch_count=float(np.mean(switch_counts)) if switch_counts else 0.0,
        correspondence_switch_rate=float(np.mean(switch_rates)) if switch_rates else 0.0,
        hist_J=np.array(hist_J), hist_xi_t=np.array(hist_xi_t), hist_xi_r=np.array(hist_xi_r),
        translation_error_mm=float(np.linalg.norm(xi[:3]) * 1000.0),
        rotation_error_deg=float(np.degrees(np.linalg.norm(xi[3:]))),
    )


# ================================================================ fixed-correspondence analytic pose-active core
def _hat(w):
    return np.array([[0., -w[2], w[1]], [w[2], 0., -w[0]], [-w[1], w[0], 0.]])


def fixed_corr_pose_active(P, target, tree, normals, nn=None, rcond=None):
    """Analytic fixed-correspondence GN quantities at xi=0, factor-1 normal equations, W=1/N.

    Follows the paper's pose-active equations exactly (notation.md Sec.3 / derivation A2-A3 /
    t5_mechanism_link.pose_active):
        delta_i = p_i - m_j(i) ;  p2p A_i=[I | [p_i]_x] ;  p2l a_i=[n ; p_i x n]
        g = J^T W delta ; H = J^T W J ; dxi_FO = -H^dag g
        delta_PA = J H^dag g  (= P_{J,W} delta, projection onto col(J) in W metric)
        RMS_PA = sqrt(g^T H^dag g) = W-RMS of delta_PA
    Returns p2p and p2l blocks with SVD/rank/condition diagnostics. rcond=None -> numpy default.
    """
    if nn is None:
        _, nn = tree.query(P, k=1, workers=-1)
    m = target[nn]
    N = len(P)
    out = {}
    # ---------------- point-to-point (vectorized; [p]_x^T[p]_x = ||p||^2 I - p p^T) ----------------
    delta = P - m
    gt = delta.mean(0)
    gr = np.cross(P, delta).mean(0)
    Htt = np.eye(3)
    Htr = _hat_vec(P).mean(0)
    Hrr = (np.mean(np.einsum("ij,ij->i", P, P)) * np.eye(3) - (P.T @ P) / N)
    H = np.block([[Htt, Htr], [Htr.T, Hrr]])
    g = np.concatenate([gt, gr])
    # P_{J,W} delta = J H^dag g ; per point q_t + [p]_x q_r = q_t + p x q_r  (no 3N x 6 matrix)
    rc = np.linalg.pinv(H, rcond=rcond) if rcond is not None else np.linalg.pinv(H)
    q = rc @ g
    delta_pa = q[:3][None, :] + np.cross(P, q[3:][None, :])
    out["p2p"] = _finish_block_precomputed(g, H, rc, delta.reshape(-1), delta_pa.reshape(-1), N)
    # ---------------- point-to-plane (N scalar residuals) ----------------
    nrm = normals[nn]
    rn = (nrm * delta).sum(1)
    a = np.zeros((N, 6)); a[:, :3] = nrm; a[:, 3:] = np.cross(P, nrm)
    gl = (rn[:, None] * a).mean(0)
    Hl = (a[:, :, None] * a[:, None, :]).mean(0)
    rcl = np.linalg.pinv(Hl, rcond=rcond) if rcond is not None else np.linalg.pinv(Hl)
    delta_pa_l = a @ (rcl @ gl)
    out["p2l"] = _finish_block_precomputed(gl, Hl, rcl, rn, delta_pa_l, N)
    return out


def _hat_vec(P):
    """Stacked [p]_x for an (N,3) array -> (N,3,3)."""
    K = np.zeros((len(P), 3, 3))
    K[:, 0, 1] = -P[:, 2]; K[:, 0, 2] = P[:, 1]
    K[:, 1, 0] = P[:, 2];  K[:, 1, 2] = -P[:, 0]
    K[:, 2, 0] = -P[:, 1]; K[:, 2, 1] = P[:, 0]
    return K


def _finish_block_precomputed(g, H, rc, delta_flat, delta_pa_flat, N):
    eig = np.linalg.eigvalsh(H)
    sv = np.linalg.svd(H, compute_uv=False)
    cond = float(sv[0] / max(sv[-1], 1e-300))
    dfo = -rc @ g
    rms = float(np.sqrt((delta_flat ** 2).sum() / N))
    rms_pa = float(np.sqrt((delta_pa_flat ** 2).sum() / N))
    pjw_check = float(np.sqrt(max(g @ rc @ g, 0.0)))
    rank_default = int(np.linalg.matrix_rank(H))
    ranks = {f"rank@{rc_:g}": int(np.linalg.matrix_rank(H, tol=sv[0] * rc_))
             for rc_ in (1e-12, 1e-10, 1e-8, 1e-6)}
    ne_resid = float(np.linalg.norm(g - H @ rc @ g) / (np.linalg.norm(g) + 1e-300))
    JtW_dpa = None  # idempotence needs J; computed by caller via idem_check
    return dict(g=g, H=H, Hpinv=rc, dfo=dfo, eig=eig, sv=sv, cond=cond,
                rms=rms, rms_pa=rms_pa, pjw_check=pjw_check,
                ratio_pa=float(rms_pa / max(rms, 1e-300)),
                gt_norm=float(np.linalg.norm(g[:3])), gr_norm=float(np.linalg.norm(g[3:])),
                rank_default=rank_default, ranks=ranks, ne_resid=ne_resid,
                delta_pa=delta_pa_flat, idem_rel=np.nan)


def projector_idempotence_p2p(P, rc, g):
    """P^2 delta == P delta check for p2p: rebuild J^T W delta_PA analytically (W=1/N).
    delta_PA_i = q_t + p x q_r  with q=H^dag g. Returns relative ||P^2 d - P d||/||P d||."""
    q = rc @ g
    dpa = q[:3][None, :] + np.cross(P, q[3:][None, :])          # (N,3); J rot block K(p): p x q_r
    # J^T W dpa: translation = mean dpa ; rotation = mean K(p)^T dpa = -mean p x dpa
    jtw = np.concatenate([dpa.mean(0), -np.cross(P, dpa).mean(0)])
    q2 = rc @ jtw
    dpa2 = q2[:3][None, :] + np.cross(P, q2[3:][None, :])
    return float(np.linalg.norm(dpa2 - dpa) / (np.linalg.norm(dpa) + 1e-300))


def projector_idempotence_p2l(P, nrm, rc, g):
    a = np.zeros((len(P), 6)); a[:, :3] = nrm; a[:, 3:] = np.cross(P, nrm)
    dpa = a @ (rc @ g)
    jtw = (dpa[:, None] * a).mean(0)
    dpa2 = a @ (rc @ jtw)
    return float(np.linalg.norm(dpa2 - dpa) / (np.linalg.norm(dpa) + 1e-300))


def _finish_block(g, H, J, delta_flat, N, dim3, rcond):
    """Compute FO step, projection delta_PA, RMS quantities and linear-algebra diagnostics.
    Uniform frozen weights W=(1/N)I (p2p) / (1/N) (p2l). Projector P_{J,W}=J H^dag J^T W."""
    eig = np.linalg.eigvalsh(H)
    sv = np.linalg.svd(H, compute_uv=False)
    cond = float(sv[0] / max(sv[-1], 1e-300))
    rc = np.linalg.pinv(H, rcond=rcond) if rcond is not None else np.linalg.pinv(H)
    dfo = -rc @ g
    delta_pa_flat = J @ (rc @ g)                  # P_{J,W} delta = J H^dag J^T W delta = J H^dag g
    rms = float(np.sqrt((delta_flat ** 2).sum() / N))
    rms_pa = float(np.sqrt((delta_pa_flat ** 2).sum() / N))
    pjw_check = float(np.sqrt(max(g @ rc @ g, 0.0)))     # identity: RMS_PA == sqrt(g^T H^dag g)
    rank_default = int(np.linalg.matrix_rank(H))
    ranks = {f"rank@{rc_:g}": int(np.linalg.matrix_rank(H, tol=sv[0] * rc_))
             for rc_ in (1e-12, 1e-10, 1e-8, 1e-6)}
    # normal-equation residual ||g - H H^dag g|| / ||g|| (component of g in null(H))
    ne_resid = float(np.linalg.norm(g - H @ rc @ g) / (np.linalg.norm(g) + 1e-300))
    # idempotence on the ACTUAL residual: P^2 delta == P delta  (uses H H^dag H = H)
    JtW_dpa = J.T @ delta_pa_flat / N             # J^T W delta_PA with uniform W=1/N
    pa2 = J @ (rc @ JtW_dpa)
    idem = float(np.linalg.norm(pa2 - delta_pa_flat) / (np.linalg.norm(delta_pa_flat) + 1e-300))
    # col-space membership: (I-P)delta_PA must be ~0  <=>  J^T W (delta - delta_PA) = g - H H^dag g ~ 0
    colspace_resid = ne_resid
    return dict(g=g, H=H, Hpinv=rc, dfo=dfo, eig=eig, sv=sv, cond=cond,
                rms=rms, rms_pa=rms_pa, pjw_check=pjw_check,
                ratio_pa=float(rms_pa / max(rms, 1e-300)),
                gt_norm=float(np.linalg.norm(g[:3])), gr_norm=float(np.linalg.norm(g[3:])),
                rank_default=rank_default, ranks=ranks, ne_resid=ne_resid,
                colspace_resid=float(colspace_resid), idem_rel=idem,
                delta_pa=delta_pa_flat)


def cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-14 or nb < 1e-14:
        return np.nan
    return float(a @ b / (na * nb))


def equal_spaced_ids(n, k=40):
    """Deterministic time-order equal-spaced diagnostic frame selection (fixed BEFORE any result)."""
    sel = np.unique(np.round(np.linspace(0, n - 1, k)).astype(int))
    return sel


# ================================================================ Phase-2 helpers (frozen history/neighbors/weights)
def predictor_library(fz=None):
    """Frozen VI mismatch library Vmean(501,24,3), Vcnt(501,24), views vrange/uview, blocks, sr, k."""
    fz = fz or frozen_bundle()
    return dict(Vmean=fz["Vmean"], Vcnt=fz["Vcnt"], vrange=fz["vrange"], uview=fz["uview"],
                blocks=fz["vi_blocks"], sr=float(G.RANGE_STD), k=int(G.KSTAR))


def view_neighbors(zr, zu, lib, train_idx=None, keep_full=False):
    """Frozen adaptive-Gaussian k-nearest-VI-view selection (identical to g_common.mu_for_view /
    run_dbs.view_predict_mag). Returns cand indices, weights w, neighbor distances; with
    keep_full=True also returns distances to ALL training views (needed for the mu_for_view fallback)."""
    Vmean, Vcnt = lib["Vmean"], lib["Vcnt"]; vr, uv, sr, k = lib["vrange"], lib["uview"], lib["sr"], lib["k"]
    tr = np.arange(len(vr)) if train_idx is None else np.asarray(train_idx, int)
    Dv = np.sqrt(((vr[tr] - zr) / sr) ** 2 + np.arccos(np.clip(uv[tr] @ zu, -1, 1)) ** 2)
    order = np.argsort(Dv)[:k]
    cand = tr[order]; dk = max(Dv[order[-1]], 1e-9)
    w = np.exp(-0.5 * (Dv[order] / dk) ** 2)
    if keep_full:
        return cand, w, Dv[order], Dv
    return cand, w, Dv[order]


def field_allhistory_point(Vmean, Vcnt):
    """A1 = current Patch: all-history + POINT-weighted (weight each scan by its point count Vcnt)."""
    vsum = Vmean * Vcnt[:, :, None]; pc = Vcnt.sum(0)
    return np.divide(vsum.sum(0), pc[:, None], out=np.zeros_like(vsum.sum(0)), where=pc[:, None] > 0)


def field_allhistory_scan(Vmean, Vcnt):
    """A2: all-history + SCAN-weighted (each scan one equal vote, averaged over scans that saw patch)."""
    mu = np.zeros((Vmean.shape[1], 3))
    for j in range(Vmean.shape[1]):
        seen = Vcnt[:, j] > 0
        mu[j] = Vmean[seen, j].mean(0) if seen.any() else 0.0
    return mu


def field_view_scan(cand, w, Dv_full, Vmean, Vcnt):
    """B2 = current Full: view-neighbor + SCAN-weighted, byte-for-byte g_common.mu_for_view
    (validity mask only; uncovered patches fall back to a 1/(1+d) mean over ALL seen views)."""
    wc = Vcnt[cand] > 0
    num = np.einsum("k,kpj,kp->pj", w, Vmean[cand], wc)
    den = (w[:, None] * wc).sum(0)
    mu = np.zeros((Vmean.shape[1], 3)); ok = den > 0
    mu[ok] = num[ok] / den[ok, None]
    if (~ok).any():                                  # EXACT mu_for_view fallback
        aw = 1.0 / (1.0 + Dv_full)
        for j in np.where(~ok)[0]:
            seen = Vcnt[:, j] > 0
            if seen.any():
                mu[j] = (aw[seen, None] * Vmean[seen, j]).sum(0) / aw[seen].sum()
    return mu


def field_view_point(cand, w, Dv_full, Vmean, Vcnt):
    """B1: view-neighbor + POINT-weighted (weight each neighbor scan by its point count Vcnt);
    uncovered patches use the SAME 1/(1+d) neighborhood but point-weighted."""
    cw = w[:, None] * Vcnt[cand]                       # (k,24)
    num = np.einsum("kp,kpj->pj", cw, Vmean[cand])
    den = cw.sum(0)
    mu = np.zeros((Vmean.shape[1], 3)); ok = den > 0
    mu[ok] = num[ok] / den[ok, None]
    if (~ok).any():
        aw = 1.0 / (1.0 + Dv_full)
        for j in np.where(~ok)[0]:
            seen = Vcnt[:, j] > 0
            if seen.any():
                ww = aw[seen] * Vcnt[seen, j]
                mu[j] = (ww[:, None] * Vmean[seen, j]).sum(0) / ww.sum()
    return mu


def unit(x, axis=-1):
    n = np.linalg.norm(x, axis=axis, keepdims=True)
    return x / np.where(n > 1e-12, n, 1.0)


def dbs_state_vector(cand, w, b_hist):
    """EXISTING DBS: mean UNIT direction (renormalised) x mean magnitude, from historical bias vecs."""
    vhat = unit((w[:, None] * unit(b_hist[cand])).sum(0))
    mhat = float((w * np.linalg.norm(b_hist[cand], axis=1)).sum() / w.sum())
    return mhat * vhat


def vector_dbs_state_vector(cand, w, b_hist):
    """NEW Vector-DBS: direct weighted mean of the FULL historical translation-bias vectors."""
    return (w[:, None] * b_hist[cand]).sum(0) / w.sum()
