# -*- coding: utf-8 -*-
"""af_common.py -- shared FROZEN-REPLAY utilities for the post-audit follow-up.

Read-only reuse of the frozen code path. Nothing here re-tunes a parameter:
  * frozen library VI_ONLY_PREDICTOR_FROZEN.npz (hard-asserted SHA256, as in g_common)
  * frozen model / PCA normals / 24 patches
  * SE(3) chart and solvers from s0_common / m_common / g_common (byte-identical calls)
Conventions: xi=[tx,ty,tz,rx,ry,rz] (m, rad); objective channels: 0=p2p, 1=p2l.
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

import os, sys, hashlib
import numpy as np, pandas as pd

ROOT = _pp("")
PHASE = os.path.join(ROOT, "structured_mismatch_phase0", "scripts")
RESC = os.path.join(PHASE, "cache", "rescue")
EXT = os.path.join(PHASE, "cache", "ext")
IIP = os.path.join(ROOT, "tj2_supplemental", "cache", "ii")
GCHAIN = os.path.join(ROOT, "g_chain")
III = os.path.join(GCHAIN, "G3_FINAL_CONFIRMATION", "iii_cache")
OUT = os.path.join(ROOT, "AUDIT_FOLLOWUP")

sys.path.insert(0, PHASE)
sys.path.insert(0, os.path.join(GCHAIN, "common"))
import s0_common as C  # noqa: E402
import m_common as M  # noqa: E402
import g_common as G  # noqa: E402

PREDICTOR_SHA = "8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe"

# external-trajectory registry (objective + non-circular prediction + meta + aligned scans)
REG = {
    "IV": dict(obj=os.path.join(EXT, "ext_objective_iv.npz"),
               pred=os.path.join(EXT, "ext_predict_iv.npz"),
               meta=os.path.join(EXT, "meta_iv.csv"),
               scandir=os.path.join(EXT, "iv")),
    "V":  dict(obj=os.path.join(EXT, "ext_objective_v.npz"),
               pred=os.path.join(EXT, "ext_predict_v.npz"),
               meta=os.path.join(EXT, "meta_v.csv"),
               scandir=os.path.join(EXT, "v")),
    "II": dict(obj=os.path.join(IIP, "ext_objective_ii.npz"),
               pred=os.path.join(IIP, "ext_predict_ii.npz"),
               meta=os.path.join(IIP, "meta_ii.csv"),
               scandir=IIP),
    "III": dict(obj=None,
                pred=os.path.join(III, "ext_predict_iii.npz"),
                meta=os.path.join(III, "meta_iii.csv"),
                scandir=III),
}

NAMES_P2P = ["p2p", "p2l"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def frozen_bundle():
    """Load and hash-verify every frozen asset; return model/normals/plab/library + hierarchy."""
    assert sha256(G.PREDICTOR) == PREDICTOR_SHA, "frozen predictor hash mismatch"
    fz = G.load_frozen()
    mu_global, mu_patch = G.hierarchy_library(fz["Vmean"], fz["Vcnt"])
    fz.update(mu_global=mu_global, mu_patch=mu_patch)
    return fz


def load_aligned(scandir, sid):
    return np.load(os.path.join(scandir, f"scan_{int(sid):04d}.npz"))["aligned"].astype(np.float64)


def vi_view_geometry():
    """Per-VI-frame oracle view (range m, unit dir) from frozen GT poses."""
    zr = np.zeros(501); zu = np.zeros((501, 3))
    for i in range(501):
        _, t, q = C.load_pose(i)
        zr[i], zu[i], _ = G.view_geometry_from_pose(t, q)
    return zr, zu


def block_series(trajectory, orders, in_support=None, vi_blocks=None):
    """Return (block_full, block_primary).
    block_full: VI=frozen orientation blocks; external=temporal order//50 over ALL frames.
    block_primary: rank within the in-support (primary) subset //50 (matches master/Figure7 blocks)."""
    orders = np.asarray(orders)
    n = len(orders)
    if trajectory == "VI":
        bf = np.asarray(vi_blocks)[orders.astype(int)].astype(int)
    else:
        bf = (orders // 50).astype(int)
    bp = np.full(n, -1, int)
    if in_support is None:
        in_support = np.ones(n, bool)
    in_support = np.asarray(in_support, bool)
    prim_idx = np.where(in_support)[0]
    for rank, pos in enumerate(prim_idx):
        bp[pos] = rank // 50 if trajectory != "VI" else int(bf[pos])
    return bf, bp


def block_bootstrap_median(vals, blocks, B=2000, seed=42):
    """Resample BLOCKS with replacement; percentile 2.5/97.5 of pooled median (matches stage3)."""
    vals = np.asarray(vals, float); blocks = np.asarray(blocks)
    ub = np.unique(blocks); mem = {b: np.where(blocks == b)[0] for b in ub}
    rng = np.random.default_rng(seed); out = np.empty(B)
    for b in range(B):
        pick = rng.choice(ub, size=len(ub), replace=True)
        samp = np.concatenate([vals[mem[p]] for p in pick])
        out[b] = np.median(samp)
    return float(np.median(vals)), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), int(len(ub))
