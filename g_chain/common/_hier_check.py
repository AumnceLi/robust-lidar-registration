# -*- coding: utf-8 -*-
"""Scratch consistency check: do global/patch/full mu reproduce frozen VI cosines ~0.391/0.824/0.940?
Protocol B leave-block-out, stride 4 for speed. Not a deliverable; locks the hierarchy definition."""
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

import os, sys, numpy as np
sys.path.insert(0, _pp("structured_mismatch_phase0/scripts"))
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G, m_common as M

fz = G.load_frozen()
Vmean, Vcnt, vr, uv, blocks = fz["Vmean"], fz["Vcnt"], fz["vrange"], fz["uview"], fz["vi_blocks"]
PLAB = np.load(G.PATCH_NPZ)["lab"].astype(int)
OBJ = M.Objective(); MODEL = OBJ.M
OM = np.load(os.path.join(M.RESCACHE, "objective_main.npz")); xs = OM["raw__xistar"][:, :3, 0]

def cos(a, b):
    a = a[:3]; na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return a @ b / (na * nb) if na > 1e-12 and nb > 1e-12 else np.nan

cg, cp, cf = [], [], []
for t in range(0, 501, 4):
    tr = np.where(blocks != blocks[t])[0]
    Vm, Vc = Vmean[tr], Vcnt[tr]; Vs = Vm * Vc[:, :, None]
    sc = M.load_scan(t); nn = sc["nnidx"]; lab = PLAB[nn]; m = MODEL[nn]
    Hp = M.grad_hess(OBJ, m)["Hp"]
    pinvH = np.linalg.pinv(Hp)
    mu_g = np.broadcast_to(Vs.sum((0, 1)) / Vc.sum(), (len(nn), 3))
    ps = Vs.sum(0); pc = Vc.sum(0)
    mu_pj = np.divide(ps, pc[:, None], out=np.zeros_like(ps), where=pc[:, None] > 0)
    mu_f, _ = G.mu_for_view(Vm, Vc, vr[tr], uv[tr], vr[t], uv[t])
    step = lambda Q: -pinvH @ M.grad_hess(OBJ, Q)["gp"]
    cg.append(cos(step(m + mu_g), xs[t])); cp.append(cos(step(m + mu_pj[lab]), xs[t])); cf.append(cos(step(m + mu_f[lab]), xs[t]))
print("VI-B stride4 median cosine  global=%.3f patch=%.3f full=%.3f  (frozen ~0.391/0.824/0.940)"
      % (np.nanmedian(cg), np.nanmedian(cp), np.nanmedian(cf)))
