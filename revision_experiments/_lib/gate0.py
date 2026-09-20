# -*- coding: utf-8 -*-
"""gate0.py -- feasibility + exact-reproduction gate BEFORE any sweep.

Checks:
 1. environment / cpu / git
 2. re-cluster k=24,w=0.3,seed=42 reproduces the FROZEN patches.npz partition exactly
    (test both the literal s3_patches call and an explicit max_iter=300 variant)
 3. re-aggregated view-independent mu_patch (pooled over all 501 VI scans under the
    frozen partition) equals the frozen hierarchy mu_patch numerically
 4. timing of a handful of frozen robust_icp runs to cost the sweep
Nothing is tuned. Read-only with respect to every frozen asset.
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

import os, sys, time, subprocess, hashlib
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from scipy.optimize import linear_sum_assignment

ROOT = _pp("")
PHASE = os.path.join(ROOT, "structured_mismatch_phase0", "scripts")
GCM = os.path.join(ROOT, "g_chain", "common")
for p in (PHASE, GCM, os.path.join(ROOT, "AUDIT_FOLLOWUP", "scripts")):
    sys.path.insert(0, p)
import s0_common as C  # noqa
import m_common as M  # noqa
import g_common as G  # noqa
import af_common as A  # noqa

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]

def partition_agreement(a, b):
    """fraction of points matched under optimal label permutation (Hungarian on -confusion)."""
    ka, kb = int(a.max()) + 1, int(b.max()) + 1
    conf = np.zeros((ka, kb), np.int64)
    np.add.at(conf, (a, b), 1)
    ri, ci = linear_sum_assignment(-conf)
    return conf[ri, ci].sum() / len(a), dict(zip(ci.tolist(), ri.tolist()))

def cluster(model, nmodel, k, w, seed, max_iter):
    feat = np.concatenate([model, w * nmodel], axis=1)
    kw = dict(n_clusters=k, random_state=seed, n_init=20, batch_size=4096)
    if max_iter is not None:
        kw["max_iter"] = max_iter
    return MiniBatchKMeans(**kw).fit_predict(feat)

def aggregate_mu_patch(model, plab, k):
    """pool view-independent per-patch 3-vector over ALL 501 VI scans (== hierarchy_library)."""
    vsum = np.zeros((k, 3)); vc = np.zeros(k)
    for t in range(M.N_SCANS):
        sc = M.load_scan(t); nn = sc["nnidx"]; P = sc["aligned"].astype(np.float64)
        lab = plab[nn]; v = P - model[nn]
        np.add.at(vsum, lab, v); np.add.at(vc, lab, np.ones(len(nn)))
    mu = np.zeros((k, 3)); ok = vc > 0
    mu[ok] = vsum[ok] / vc[ok, None]
    return mu, vc

def main():
    import sklearn, scipy, pandas
    print("py", sys.version.split()[0], "| numpy", np.__version__, "| sklearn", sklearn.__version__,
          "| scipy", scipy.__version__, "| pandas", pandas.__version__, "| cpu", os.cpu_count())
    try:
        gh = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True)
        print("git HEAD:", gh.stdout.strip() or "(not a git repo)")
    except Exception as e:
        print("git n/a:", e)

    mc = np.load(M.CACHE + "/model_cache.npz")
    model = mc["xyz"].astype(np.float64); nmodel = mc["normals"].astype(np.float64)
    froz = np.load(M.CACHE + "/patches.npz")
    lab_f = froz["lab"].astype(int)
    print("model", model.shape, "frozen patches.npz sha", sha(M.CACHE + "/patches.npz"),
          "k", lab_f.max() + 1)

    # --- gate 2: clustering reproduction (literal s3 call = default max_iter; explicit 300)
    for tag, mi in [("s3_literal_default_maxiter", None), ("explicit_maxiter300", 300)]:
        t0 = time.perf_counter(); lab = cluster(model, nmodel, 24, 0.3, 42, mi)
        agree, cmap = partition_agreement(lab, lab_f)
        print(f"[cluster {tag}] partition agreement = {agree:.6f}  ({time.perf_counter()-t0:.1f}s)")

    # --- gate 3: mu_patch reproduction under FROZEN partition
    fz = A.frozen_bundle()
    t0 = time.perf_counter(); mu_new, vc = aggregate_mu_patch(model, lab_f, 24)
    d = np.abs(mu_new - fz["mu_patch"]).max()
    print(f"[mu_patch re-aggregation] max|mu_rebuilt - mu_frozen| = {d:.3e}  ({time.perf_counter()-t0:.1f}s); "
          f"min patch count={vc.min():.0f}")

    # --- gate 4: timing of frozen ICP (Patch LS + Huber) on a few VI frames
    from scipy.spatial import cKDTree
    mp = model + fz["mu_patch"][lab_f]
    tr_raw, tr_pat = cKDTree(model), cKDTree(mp)
    t0 = time.perf_counter(); n = 12
    for t in range(n):
        sc = M.load_scan(t); P = sc["aligned"].astype(np.float64)
        G.robust_icp(model, fz["normals"], tr_raw, P, "p2p", "ls", s_floor=fz["s_floor"])
        G.robust_icp(mp, fz["normals"], tr_pat, P, "p2p", "ls", s_floor=fz["s_floor"])
    dt = (time.perf_counter() - t0) / n
    print(f"[timing] {dt*1000:.0f} ms per frame for (Raw+Patch) LS single-thread; "
          f"one Patch-arm over 1456 frames ~= {dt/2*1456:.0f}s single-thread")

if __name__ == "__main__":
    main()
