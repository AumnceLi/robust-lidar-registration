# -*- coding: utf-8 -*-
"""
s0_common.py  --  Structured Model Mismatch Phase-0 (VI-only) common library.

All conventions here are re-verified against epos_README.txt:
  .3d   : ASCII "x y z" per line, metres, LIDAR frame (target_model.3d = TARGET frame)
  .pose : line1 timestamp [s, absolute]
          line2 pos_x pos_y pos_z = target position in lidar frame (t)
          line3 q_s q_x q_y q_z    = rotation TARGET -> LIDAR, scalar-first Hamilton
  => P_lidar = R * P_target + t ;  GT-align scan back: P_target = R^T (P_lidar - t)
  pose anchors the scan END instant.

No learned methods live here; only IO, rigid transforms, PCA normals, classical
FPFH / RANSAC / point-to-point ICP (faithful re-implementations because open3d
has no wheel for the interpreter on this machine: Python 3.14).
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

import os, re, time
import numpy as np

# ---------------------------------------------------------------- paths
ROOT      = _pp("structured_mismatch_phase0")
SCRIPTS   = os.path.join(ROOT, "scripts")
VI_DIR    = os.path.join(SCRIPTS, "vi_data", "epos_dataset_vi")
TARGET    = _pp("external_dataset_scout/intermediate/samples/epos_target_model.3d")
RESULTS   = os.path.join(ROOT, "results")
FIGDIR    = os.path.join(RESULTS, "figures")
REPORTS   = os.path.join(ROOT, "reports")
CACHE     = os.path.join(SCRIPTS, "cache")
for d in (RESULTS, FIGDIR, REPORTS, CACHE):
    os.makedirs(d, exist_ok=True)

N_SCANS   = 501
RNG_SEED  = 42

# ---------------------------------------------------------------- IO
def scan_ids():
    return list(range(N_SCANS))

def f3d(i):
    return os.path.join(VI_DIR, f"{i:04d}.3d")

def fpose(i):
    return os.path.join(VI_DIR, f"{i:04d}.pose")

def load_xyz(path):
    return np.loadtxt(path, dtype=np.float64)

def load_pose(i):
    with open(fpose(i), "r") as fh:
        lines = [ln.strip() for ln in fh if ln.strip()]
    ts = float(lines[0])
    t  = np.array([float(v) for v in lines[1].split()], dtype=np.float64)
    q  = np.array([float(v) for v in lines[2].split()], dtype=np.float64)  # s,x,y,z
    return ts, t, q

# ---------------------------------------------------------------- rotations
def quat_to_R(q):
    """Scalar-first Hamilton quaternion -> rotation matrix (target->lidar)."""
    s, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1-2*(y*y+z*z),   2*(x*y-s*z),   2*(x*z+s*y)],
        [  2*(x*y+s*z), 1-2*(x*x+z*z),   2*(y*z-s*x)],
        [  2*(x*z-s*y),   2*(y*z+s*x), 1-2*(x*x+y*y)]], dtype=np.float64)

def rot_x(deg):
    c, s = np.cos(np.deg2rad(deg)), np.sin(np.deg2rad(deg))
    return np.array([[1,0,0],[0,c,-s],[0,s,c]], dtype=np.float64)

def geodesic_deg(Ra, Rb):
    """Geodesic angle [deg] between two rotation matrices."""
    cdelta = np.clip((np.trace(Ra @ Rb.T) - 1.0)/2.0, -1.0, 1.0)
    return float(np.degrees(np.arccos(cdelta)))

def sym_aware_attitude_err(R_est, R_gt, sym_axis="x", sym_deg=120.0):
    """Min geodesic over the 3 symmetry-equivalent GT poses (k=0,1,2 about X)."""
    best = (1e9, 0, np.eye(3))
    for k in range(3):
        S = rot_x(k*sym_deg)
        Rgt_eq = R_gt @ S                 # symmetry applied in target frame
        Rerr   = R_est @ Rgt_eq.T         # lidar-frame misalignment
        ang = geodesic_deg(Rerr, np.eye(3))
        if ang < best[0]:
            best = (ang, k, Rerr)
    return best  # (deg, k, Rerr)

def rot_axis(R):
    """Axis of a rotation matrix (unit vector, sign-stabilised)."""
    w = np.array([R[2,1]-R[1,2], R[0,2]-R[2,0], R[1,0]-R[0,1]])
    n = np.linalg.norm(w)
    if n < 1e-12:
        return np.array([1.0,0,0])
    ax = w/n
    # stabilise sign: make the component with largest abs positive
    j = int(np.argmax(np.abs(ax)))
    if ax[j] < 0: ax = -ax
    return ax

# ---------------------------------------------------------------- geometry helpers
def pca_normals(xyz, tree, k=16):
    """Estimate outward normals by local PCA; orient away from centroid."""
    _, idx = tree.query(xyz, k=k)
    nbrs = xyz[idx]                                  # N,k,3
    cent = nbrs.mean(axis=1)
    H = np.einsum('nkj,nki->nji', nbrs-cent[:,None,:], nbrs-cent[:,None,:])
    evals, evecs = np.linalg.eigh(H)                 # ascending
    normals = evecs[:, :, 0]                         # smallest-eigenvalue vector
    outward = cent - xyz.mean(axis=0)
    flip = np.einsum('nj,nj->n', normals, outward) < 0
    normals[flip] *= -1
    return normals / (np.linalg.norm(normals,axis=1,keepdims=True)+1e-12)

def voxel_downsample(xyz, voxel, *extra):
    """Mean voxel grid downsample; extra arrays (normals, feats) averaged too."""
    keys = np.floor(xyz/voxel).astype(np.int64)
    _, inv, counts = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
    order = np.argsort(inv, kind="stable")
    csum = np.cumsum(counts)
    xout = np.zeros((len(counts),3))
    starts = np.r_[0, csum[:-1]]
    np.add.at(xout, inv, xyz)
    xout /= counts[:,None]
    outs = [xout]
    for a in extra:
        ao = np.zeros((len(counts), a.shape[1]))
        np.add.at(ao, inv, a)
        ao /= counts[:,None]
        outs.append(ao)
    return tuple(outs) if len(outs)>1 else xout

# ---------------------------------------------------------------- FPFH (Rusu 2009)
def _darbo(u, v, w, diff):
    """3 angular features for one neighbour pair (vectorised)."""
    n1 = np.linalg.norm(diff,axis=1); n1=np.maximum(n1,1e-12)
    d = diff/n1[:,None]
    alpha = (v*d).sum(1)
    phi   = (u*d).sum(1)
    proj  = (w*d).sum(1)
    theta = np.arctan2(proj, alpha)
    return alpha, phi, theta

def spfh(xyz, normals, tree, radius):
    """Simplified Point Feature Histogram, 33-dim (11 bins per alpha/phi/theta).
    Rusu et al. 2009: u=n_i; v=normalise((p_j-p_i)_perp_to_u); w=u x v;
    alpha=v.n_j, phi=u.(p_j-p_i)/d, theta=atan2(w.n_j, u.n_j)."""
    n = len(xyz)
    out = np.zeros((n,33), dtype=np.float32)
    idxlist = tree.query_ball_point(xyz, r=radius)
    abins = np.linspace(-1,1,12); abins[-1]=1.0001
    tbins = np.linspace(-np.pi,np.pi,12); tbins[-1]=np.pi+1e-6
    for i in range(n):
        js = np.array(idxlist[i], dtype=int)
        js = js[js!=i]
        if len(js)<2:
            continue
        u = np.tile(normals[i],(len(js),1))
        disp = xyz[js]-xyz[i]
        dnorm = disp/np.maximum(np.linalg.norm(disp,axis=1,keepdims=True),1e-12)
        v = dnorm - u*np.einsum('nj,nj->n',u,dnorm)[:,None]
        v /= np.maximum(np.linalg.norm(v,axis=1,keepdims=True),1e-12)
        w = np.cross(u,v)
        nj = normals[js]
        alpha = (v*nj).sum(1)
        phi   = (u*dnorm).sum(1)
        theta = np.arctan2((w*nj).sum(1),(u*nj).sum(1))
        ha,_=np.histogram(alpha,bins=abins); hp,_=np.histogram(phi,bins=abins)
        ht,_=np.histogram(theta,bins=tbins)
        h = np.concatenate([ha,hp,ht]).astype(np.float32)
        s = h.sum()
        out[i] = h/s if s>0 else h
    return out

def fpfh(xyz, normals, tree, radius):
    """FPFH = SPFH(p) + weighted mean of neighbour SPFH."""
    sp = spfh(xyz, normals, tree, radius).astype(np.float64)
    out = sp.copy()
    idxlist = tree.query_ball_point(xyz, r=radius)
    for i in range(len(xyz)):
        js = np.array(idxlist[i], dtype=int); js = js[js!=i]
        if len(js)==0: continue
        d = np.linalg.norm(xyz[js]-xyz[i],axis=1); w = 1.0/np.maximum(d,1e-9)
        out[i] += (w[:,None]*sp[js]).sum(0)/w.sum()
    n = np.linalg.norm(out,axis=1,keepdims=True)
    return (out/np.maximum(n,1e-12)).astype(np.float32)

# ---------------------------------------------------------------- Kabsch
def kabsch(A, B):
    """R,t such that B ~= R@A + t for matched 3xM arrays A(src) B(dst)."""
    ca, cb = A.mean(1), B.mean(1)
    H = (A-ca[:,None]) @ (B-cb[:,None]).T
    U,_,Vt = np.linalg.svd(H)
    D = np.eye(3); D[2,2] = np.sign(np.linalg.det(Vt.T@U.T))
    R = Vt.T @ D @ U.T
    return R, cb - R@ca

# ---------------------------------------------------------------- RANSAC global reg.
def ransac_global(src, dst, feat_s, feat_d, rng, dist_thresh=0.10,
                  max_iter=4_000_000, max_validation=500, confidence=0.999,
                  batch=2048):
    """
    Global registration from FPFH correspondences. Finds (R,t): dst = R src + t.
    Vectorised 3-point RANSAC with a validation subset (open3d semantics:
    max_validation random correspondences checked per candidate). Stops on the
    standard confidence criterion; max_iter is the hard ceiling.
    Returns R,t,fitness,inlier_count,iters_used,n_corr.
    """
    from scipy.spatial import cKDTree
    ft = cKDTree(feat_d)
    dd, mi = ft.query(feat_s, k=1)                     # nearest feature match s->d
    fs = cKDTree(feat_s)
    _, mj = fs.query(feat_d, k=1)                      # nearest feature match d->s
    # mutual nearest-neighbour correspondences + uniqueness (standard, no frozen param touched)
    mutual = np.zeros(len(src), bool)
    arange = np.arange(len(src))
    mutual[mj[mi] == arange] = True
    _, order = np.unique(mi, return_index=True)
    m = np.zeros(len(mi), bool); m[order]=True
    valid = mutual & m
    cs, cd = src[valid], dst[mi[valid]]
    n_corr = len(cs)
    if n_corr < 8:
        return np.eye(3), np.zeros(3), 0.0, 0, 0, n_corr
    nval = min(max_validation, n_corr)
    best = (-1, None, None)
    it = 0
    while it < max_iter:
        B = min(batch, max_iter-it)
        tri = rng.integers(0, n_corr, size=(B,3))
        dup = (tri[:,0]==tri[:,1])|(tri[:,0]==tri[:,2])|(tri[:,1]==tri[:,2])
        cand = tri[~dup]
        if len(cand)==0: it+=B; continue
        A3 = cs[cand].transpose(0,2,1)                 # b,3,3 src
        B3 = cd[cand].transpose(0,2,1)
        ca = A3.mean(2,keepdims=True); cb = B3.mean(2,keepdims=True)
        Ha = A3-ca; Hb = B3-cb
        Hm = Ha @ Hb.transpose(0,2,1)
        try:
            U,_,Vt = np.linalg.svd(Hm)
        except np.linalg.LinAlgError:
            it+=B; continue
        Dm = np.tile(np.eye(3),(len(cand),1,1))
        det = np.linalg.det(Vt.transpose(0,2,1) @ U.transpose(0,2,1))
        Dm[:,2,2] = np.sign(det)
        Rb = Vt.transpose(0,2,1) @ Dm @ U.transpose(0,2,1)
        tb = cb - Rb@ca
        vi = rng.integers(0,n_corr,nval)
        Vs = cs[vi]; Vd = cd[vi]
        pred = np.einsum('bij,vj->bvi', Rb, Vs) + tb.transpose(0,2,1)
        d2 = ((pred - Vd[None])**2).sum(2)
        inl = (d2 < dist_thresh**2).sum(1)
        j = int(np.argmax(inl))
        if inl[j] > best[0]:
            best = (int(inl[j]), Rb[j], tb[j,:,0])
            p = best[0]/nval
            if p>0:
                need = np.log(1-confidence)/np.log(1-p**3 + 1e-15)
                if it+ B >= need: break
        it += B
    if best[1] is None:
        return np.eye(3), np.zeros(3), 0.0, 0, it, n_corr
    R,t = best[1], best[2]
    pred = (R@cs.T).T + t
    full = np.linalg.norm(pred-cd,axis=1) < dist_thresh
    return R, t, float(full.sum())/len(src), int(full.sum()), it, n_corr

# ---------------------------------------------------------------- point-to-point ICP
def icp_point2point(src, dst, tree_d, R0, t0, dist_thresh=0.10, max_iter=30):
    R,t = R0.copy(), t0.copy()
    last_fit = 0.0
    for _ in range(max_iter):
        pred = (R@src.T).T + t
        d, idx = tree_d.query(pred)
        m = d < dist_thresh
        if m.sum()<3: break
        R,t = kabsch(src[m].T, dst[idx[m]].T)
        fit = m.sum()/len(src)
        if abs(fit-last_fit)<1e-5: break
        last_fit = fit
    pred = (R@src.T).T+t
    d,idx = tree_d.query(pred); m=d<dist_thresh
    rmse = float(np.sqrt((d[m]**2).mean())) if m.any() else np.inf
    return R,t, float(m.sum())/len(src), int(m.sum()), rmse

def tic():
    return time.perf_counter()
def toc(t0):
    return time.perf_counter()-t0
