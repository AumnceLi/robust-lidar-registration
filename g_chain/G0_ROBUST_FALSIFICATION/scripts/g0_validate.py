# -*- coding: utf-8 -*-
"""g0_validate.py -- BEFORE any G0 outcome: (1) ls arm reproduces frozen vanilla xistar;
(2) robust solver timing; (3) robust self-null stays at ~0. No result is used to tune anything."""
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

import os, sys, time
import numpy as np
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G
import m_common as M

fz = G.load_frozen()
model, normals, plab, sfloor = fz["model"], fz["normals"], fz["plab"], fz["s_floor"]
tree = __import__("scipy.spatial", fromlist=["cKDTree"]).cKDTree(model)
print("model n=%d s_floor(MAD floor)=%.5f m" % (len(model), sfloor))

OM = np.load(os.path.join(M.RESCACHE, "objective_main.npz"))
xs_frozen = OM["raw__xistar"]                 # (501,6,2)
test = [0, 40, 100, 200, 300, 400, 500]
print("\n== R0/R1 ls reproduction vs frozen raw__xistar ==")
maxerr = 0.0
for i in test:
    P = M.load_scan(i)["aligned"].astype(np.float64)
    rp = G.robust_icp(model, normals, tree, P, "p2p", "ls", s_floor=sfloor)
    rl = G.robust_icp(model, normals, tree, P, "p2l", "ls", s_floor=sfloor)
    ep = np.abs(rp["xi"] - xs_frozen[i, :, 0]).max()
    el = np.abs(rl["xi"] - xs_frozen[i, :, 1]).max()
    maxerr = max(maxerr, ep, el)
    print(f"scan {i:4d} |dxi_p2p|max={ep:.2e} |dxi_p2l|max={el:.2e} iters {rp['iters']}/{rl['iters']}")
print("MAX ls reproduction error across probes = %.3e" % maxerr)

print("\n== timing + displacement for one scan (all formulations) ==")
i = 200
P = M.load_scan(i)["aligned"].astype(np.float64)
for form in ["ls", "huber", "trim"]:
    for kind in ["p2p", "p2l"]:
        t0 = time.perf_counter()
        r = G.robust_icp(model, normals, tree, P, kind, form, s_floor=sfloor)
        dt = time.perf_counter() - t0
        gn, _ = G.robust_grad_norm(model, normals, tree, P, kind, form, sfloor)
        print(f"{form:6s} {kind} | et={np.linalg.norm(r['xi'][:3])*1000:7.2f}mm "
              f"eR={np.degrees(np.linalg.norm(r['xi'][3:])):6.3f}deg gGT={gn:.4e} "
              f"wmean={r['wmean']:.3f} it={r['iters']} {dt*1000:.0f}ms")

print("\n== robust SELF-NULL (model-derived equal-count cloud, seed42) ==")
rng = np.random.default_rng(42)
for i in [0, 200, 400]:
    n = len(M.load_scan(i)["aligned"])
    selfcloud = model[rng.choice(len(model), n, replace=False)]
    row = []
    for form in ["ls", "huber", "trim"]:
        r = G.robust_icp(model, normals, tree, selfcloud, "p2p", form, s_floor=sfloor)
        row.append(f"{form}:et={np.linalg.norm(r['xi'][:3])*1000:.4f}mm")
    print("self scan", i, "n=", n, " ".join(row))
