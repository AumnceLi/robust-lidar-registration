# -*- coding: utf-8 -*-
"""
g_common.py -- G-chain (G0/G1/G2) shared numerical core.

READ-ONLY reuse of the frozen phase-0 conventions (never edits phase0 files):
  * target frame, GT-aligned source cloud P at xi=0, local chart xi=[tx,ty,tz,rx,ry,rz]
    (translation m, rotation rad), T(xi)P = exp([r]x) P + t
  * fixed nominal model M + frozen PCA normals + frozen 24 model-point patches
  * nearest-MODEL point correspondence recomputed at every probe (cKDTree over fixed M)
  * basin clip 0.30 m / 15 deg, identical for every formulation.

G0 REGISTRATION FORMULATIONS (the ONLY thing allowed to differ is per-correspondence weight):
  R0 point-to-point LEAST-SQUARES ICP  : w = 1            (must reproduce frozen local_min_p2p)
  R1 point-to-plane LEAST-SQUARES ICP  : w = 1            (must reproduce frozen local_min_p2l)
  R2 HUBER-WEIGHTED ICP (PRIMARY robust), IRLS:
        per-iteration residual metric r_i (p2p: |e_i| ; p2l: |n_i.e_i|),
        robust scale s = max(1.4826 median|r_i - median r_i|, s_floor), s_floor = model median NN spacing,
        u_i = r_i / s, Huber weight w_i = 1 if u_i<=delta else delta/u_i, delta = 1.345 (FROZEN).
  R3 TRIMMED ICP (pre-registered SECONDARY sensitivity only): keep fixed fraction q=0.80 of the
        smallest-residual correspondences each iteration (binary weights). NOT used to pick a winner.
All four share one weighted solver, so R0/R1 are literally the w=1 special case -> controlled falsification.
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

import os, sys, hashlib, json
import numpy as np
from scipy.spatial import cKDTree

PHASE0 = _pp("structured_mismatch_phase0/scripts")
sys.path.insert(0, PHASE0)
import s0_common as C  # noqa: E402  (frozen IO / rotations)
import m_common as M  # noqa: E402  (frozen chart / objectives / vanilla solvers)

GROOT = _pp("g_chain")

# ---------------------------------------------------------------- frozen invariants (verified == manifests)
PREDICTOR = os.path.join(M.RESCACHE, "VI_ONLY_PREDICTOR_FROZEN.npz")
PREDICTOR_SHA = "8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe"
MODEL_NPZ = os.path.join(M.CACHE, "model_cache.npz")
PATCH_NPZ = os.path.join(M.CACHE, "patches.npz")
KSTAR = 16
RANGE_STD = 2.064279860893169
TAU_SUPPORT = 0.4403305559611483
ALPHA_VI = 0.019993613253598837
N_PATCH = 24

# ---------------------------------------------------------------- G0 FROZEN robust config (locked BEFORE first outcome comparison)
HUBER_DELTA = 1.345          # 95%-Gaussian-efficiency Huber tuning constant (standard, not outcome-fit)
SCALE_K = 1.4826            # consistency factor for MAD -> Gaussian sigma
TRIM_KEEP = 0.80            # R3 fixed trimmed fraction (secondary sensitivity)
BASIN_T = 0.30
BASIN_R_DEG = 15.0
MAX_ITER = 40
TOL_P2P = 1e-8
TOL_P2L = 1e-9
P2L_REG = 1e-9
FD_T = M.FD_T               # 0.005 m
FD_R = M.FD_R               # 0.25 deg
RNG = np.random.default_rng(M.RNG_SEED)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def load_frozen():
    assert sha256(PREDICTOR) == PREDICTOR_SHA, "predictor hash mismatch -- refusing to run on altered predictor"
    mc = np.load(MODEL_NPZ)
    model = mc["xyz"].astype(np.float64)
    normals = mc["normals"].astype(np.float64)
    s_floor = float(mc["dnn"])                      # model median NN spacing (numerical floor for MAD scale)
    plab = np.load(PATCH_NPZ)["lab"].astype(int)
    F = np.load(PREDICTOR)
    return dict(model=model, normals=normals, s_floor=s_floor, plab=plab, F=F,
                Vmean=F["Vmean"], Vcnt=F["Vcnt"], vrange=F["vrange"], uview=F["uview"],
                vi_blocks=F["blocks"])


# ================================================================ weighted rigid solvers (one shared engine)
def _basin(Racc, tacc, bt, br):
    f = 1.0
    nt = np.linalg.norm(tacc)
    nr = np.linalg.norm(M.rodrigues_log(Racc))
    if nt > bt:
        f = min(f, bt / nt)
    if nr > br:
        f = min(f, br / nr)
    return f


def weighted_kabsch(Q, m, w):
    """R,t with m ~= R Q + t under per-point weights w>=0. 3xN convention."""
    sw = w.sum()
    cq = (w[:, None] * Q).sum(0) / sw
    cm = (w[:, None] * m).sum(0) / sw
    Hm = ((Q - cq) * w[:, None]).T @ (m - cm)
    U, _, Vt = np.linalg.svd(Hm)
    D = np.eye(3)
    D[2, 2] = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ D @ U.T
    return R, cm - R @ cq


def huber_weights(resid_metric, delta, s_floor):
    s = max(SCALE_K * np.median(np.abs(resid_metric - np.median(resid_metric))), s_floor)
    u = np.abs(resid_metric) / s
    w = np.ones_like(u)
    msk = u > delta
    w[msk] = delta / u[msk]
    return w, s


def trim_weights(resid_metric, keep):
    n = len(resid_metric)
    w = np.zeros(n)
    k = max(3, int(round(keep * n)))
    idx = np.argpartition(resid_metric, k - 1)[:k]
    w[idx] = 1.0
    return w, k / n


def robust_icp(model, normals, tree, P, kind="p2p", formulation="huber",
               max_iter=MAX_ITER, bound_t=BASIN_T, bound_r_deg=BASIN_R_DEG, s_floor=1e-3, x0=None,
               clip_basin=True):
    """Local ICP. By default GT-started (xi=0). x0=[t(3),r(3)] warm-starts at a given pose (G2 deployable).
    kind: p2p|p2l ; formulation: ls|huber|trim. Weights are the ONLY differing factor across formulations."""
    br = np.deg2rad(bound_r_deg)
    if x0 is None:
        Racc, tacc = np.eye(3), np.zeros(3)
    else:
        tacc = np.asarray(x0[:3], float).copy()
        Racc = M.rodrigues(np.asarray(x0[3:], float))
    hist = []
    hit = False
    wmean_last = np.nan
    keep_last = np.nan
    scale_last = np.nan
    tol = TOL_P2P if kind == "p2p" else TOL_P2L
    for it in range(max_iter):
        Q = (Racc @ P.T).T + tacc
        _, idx = tree.query(Q, k=1, workers=-1)
        m = model[idx]
        e = Q - m
        if kind == "p2p":
            metric = np.linalg.norm(e, axis=1)
        else:
            metric = np.abs(np.einsum("ij,ij->i", normals[idx], e))
        if formulation == "ls":
            w = np.ones(len(P))
        elif formulation == "huber":
            w, scale_last = huber_weights(metric, HUBER_DELTA, s_floor)
        elif formulation == "trim":
            w, keep_last = trim_weights(metric, TRIM_KEEP)
        else:
            raise ValueError(formulation)
        wmean_last = float(w.mean())
        if kind == "p2p":
            Rd, vd = weighted_kabsch(Q, m, w)
        else:
            n = normals[idx]
            cx = np.cross(Q, n)
            A = np.concatenate([n, cx], axis=1)
            b = np.einsum("ij,ij->i", n, m - Q)
            AtA = (A * w[:, None]).T @ A + P2L_REG * np.eye(6)
            Atb = (A * w[:, None]).T @ b
            try:
                delta = np.linalg.solve(AtA, Atb)
            except np.linalg.LinAlgError:
                delta = np.linalg.lstsq(AtA, Atb, rcond=None)[0]
            vd = delta[:3]
            Rd = M.rodrigues(delta[3:])
        Rn = Rd @ Racc
        tn = Rd @ tacc + vd
        if clip_basin:
            f = _basin(Rn, tn, bound_t, br)
            if f < 1.0:
                tacc = tacc + f * (tn - tacc)
                hit = True
                break
        Racc, tacc = Rn, tn
        # objective value under THIS formulation's own weights (mean weighted squared residual metric)
        Qn = (Rd @ Q.T).T + vd
        en = Qn - model[idx]
        if kind == "p2p":
            r2 = np.einsum("ij,ij->i", en, en)
        else:
            nd = np.einsum("ij,ij->i", normals[idx], en)
            r2 = nd * nd
        J = float((w * r2).sum() / w.sum())
        hist.append(J)
        if it > 0 and abs(hist[-2] - J) < tol * max(1, hist[-2]):
            break
    xi = M.se3_log(Racc, tacc)
    return dict(xi=xi, R=Racc, t=tacc, iters=it + 1, on_bound=bool(hit),
                wmean=wmean_last, keep=keep_last, scale=scale_last,
                Jlast=(hist[-1] if hist else np.nan))


# ---------------------------------------------------------------- robust objective at arbitrary xi (NN+weights recomputed)
def robust_objective(model, normals, tree, P, xi, kind="p2p", formulation="huber", s_floor=1e-3):
    Q = M.apply_xi(P, xi)
    _, idx = tree.query(Q, k=1, workers=-1)
    m = model[idx]
    e = Q - m
    if kind == "p2p":
        metric2 = np.einsum("ij,ij->i", e, e)
        metric = np.sqrt(metric2)
    else:
        metric = np.abs(np.einsum("ij,ij->i", normals[idx], e))
        metric2 = metric ** 2
    if formulation == "ls":
        return float(metric2.mean())
    if formulation == "huber":
        s = max(SCALE_K * np.median(np.abs(metric - np.median(metric))), s_floor)
        u = metric / s
        h = np.where(u <= HUBER_DELTA, 0.5 * u ** 2, HUBER_DELTA * (u - 0.5 * HUBER_DELTA))
        return float(s ** 2 * h.mean())           # same physical units as mean squared residual
    if formulation == "trim":
        k = max(3, int(round(TRIM_KEEP * len(P))))
        part = np.partition(metric2, k - 1)[:k]
        return float(part.mean())
    raise ValueError(formulation)


def robust_grad_norm(model, normals, tree, P, kind="p2p", formulation="huber", s_floor=1e-3):
    """Central-difference gradient MAGNITUDE of the chosen robust objective at xi=0 (GT)."""
    h = np.array([FD_T] * 3 + [FD_R] * 3)
    g = np.zeros(6)
    for a in range(6):
        ep = np.zeros(6); ep[a] = h[a]
        jp = robust_objective(model, normals, tree, P, ep, kind, formulation, s_floor)
        jm = robust_objective(model, normals, tree, P, -ep, kind, formulation, s_floor)
        g[a] = (jp - jm) / (2 * h[a])
    return float(np.linalg.norm(g)), g


# ---------------------------------------------------------------- frozen mu_j(z) from the VI-only predictor
def mu_for_view(Vmean, Vcnt, vrange, uview, zr, zu, k=KSTAR, sr=RANGE_STD):
    """Frozen adaptive-Gaussian k-nearest-VI-view per-patch mean mismatch mu_j(z), identical to r8._mu.
    Vmean (501,24,3), Vcnt (501,24), training view library vrange/uview; query z=(zr,zu)."""
    Dv = np.sqrt(((vrange - zr) / sr) ** 2 + np.arccos(np.clip(uview @ zu, -1, 1)) ** 2)
    order = np.argsort(Dv)[:k]
    dk = max(Dv[order[-1]], 1e-9)
    w = np.exp(-0.5 * (Dv[order] / dk) ** 2)
    wc = Vcnt[order] > 0
    num = np.einsum("k,kpj,kp->pj", w, Vmean[order], wc)
    den = (w[:, None] * wc).sum(0)
    mu = np.zeros((N_PATCH, 3))
    ok = den > 0
    mu[ok] = num[ok] / den[ok, None]
    if (~ok).any():
        aw = 1.0 / (1.0 + Dv)
        for j in np.where(~ok)[0]:
            seen = Vcnt[:, j] > 0
            if seen.any():
                mu[j] = (aw[seen, None] * Vmean[seen, j]).sum(0) / aw[seen].sum()
    return mu, float(Dv.min())


def load_pose_dir(path):
    """Generic .pose loader (timestamp, t, quaternion scalar-first)."""
    with open(path, "r") as fh:
        ln = [x.strip() for x in fh if x.strip()]
    t = np.array([float(v) for v in ln[1].split()])
    q = np.array([float(v) for v in ln[2].split()])
    return t, q

def view_geometry_from_pose(t, q):
    """z=(range, unit view dir in TARGET frame) from lidar-frame pose: o=-R^T t."""
    R = C.quat_to_R(q)
    o = -R.T @ t
    rng = float(np.linalg.norm(o))
    return rng, o / rng, R

def estimated_view(t_gt, R_gt, xi):
    """View geometry at the ESTIMATED pose obtained by composing local chart xi onto GT pose.
    P_GT-aligned is moved by T(xi); estimated lidar pose is R_est=Rxi R_GT, t_est=Rxi t_GT+txi,
    and target-frame sensor origin o_est = o_GT - R_GT^T Rxi^T txi."""
    Rxi = M.rodrigues(xi[3:]); txi = xi[:3]
    R_est = Rxi @ R_gt
    t_est = Rxi @ t_gt + txi
    o_est = -R_est.T @ t_est
    return float(np.linalg.norm(o_est)), o_est / np.linalg.norm(o_est)


# ---------------------------------------------------------------- frozen spatial hierarchy of mu (global / patch / full)
def hierarchy_library(Vmean, Vcnt):
    """From the frozen VI mismatch library return the two VIEW-INDEPENDENT levels:
       mu_global : (3,)   one pooled 3-vector over all VI scans and all 24 patches
       mu_patch  :(24,3)  per-patch pooled 3-vector over all VI scans (no view conditioning)
    Full view-conditioned level is mu_for_view(...) per query z. Vsum = Vmean*Vcnt."""
    vsum = Vmean * Vcnt[:, :, None]
    tot_c = Vcnt.sum()
    mu_global = vsum.sum((0, 1)) / max(tot_c, 1)
    pc = Vcnt.sum(0)
    mu_patch = np.divide(vsum.sum(0), pc[:, None], out=np.zeros_like(vsum.sum(0)),
                         where=pc[:, None] > 0)
    return mu_global, mu_patch


def corrected_model(model, plab, mu_global, mu_patch, mu_full, level):
    """Corrected nominal geometry M_corr = M + mu_{j(i)}. level in global/patch/full/none."""
    if level == "none":
        return model
    if level == "global":
        return model + mu_global[None, :]
    if level == "patch":
        return model + mu_patch[plab]
    if level == "full":
        return model + mu_full[plab]
    raise ValueError(level)


# ---------------------------------------------------------------- block bootstrap (temporal moving block)
def block_boot(x, stat=np.median, B=2000, Ls=(5, 10, 20), seed=42):
    x = np.asarray(x, float)
    n = len(x)
    rng = np.random.default_rng(seed)
    out = {"point": float(stat(x)), "n": int(n)}
    for L in Ls:
        vals = np.empty(B)
        nb = int(np.ceil(n / L))
        starts = rng.integers(0, n - L + 1 if n > L else 1, size=(B, nb))
        for b in range(B):
            samp = np.concatenate([x[s:s + L] for s in starts[b]])[:n]
            vals[b] = stat(samp)
        lo, hi = np.percentile(vals, [2.5, 97.5])
        out[f"L{L}_lo"] = float(lo)
        out[f"L{L}_hi"] = float(hi)
    return out


def block_signflip_p(delta, B=2000, L=5, seed=42):
    """One-sided block sign-flip permutation p for H: median(delta)>0 (paired)."""
    delta = np.asarray(delta, float)
    n = len(delta)
    obs = np.median(delta)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / L))
    cnt = 0
    null = np.empty(B)
    for b in range(B):
        signs = np.where(rng.random(nb) < 0.5, -1.0, 1.0)
        d = np.concatenate([np.full(L, signs[j]) for j in range(nb)])[:n] * delta
        null[b] = np.median(d)
    p = (1 + np.sum(null >= obs)) / (B + 1)
    return float(obs), float(p)
