# -*- coding: utf-8 -*-
"""TJ2 P1+P2 for Dataset II. Numerically identical to frozen r7_ext_objective.py (same FD,
same frozen nuisance ops, same basin 0.30m/15deg, same self-null draw seed42); only paths differ."""
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
os.environ.setdefault("QTHREADS", "4")
import sys, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
PHASE0 = _pp("structured_mismatch_phase0/scripts"); sys.path.insert(0, PHASE0)
import m_common as M

CONDS = ["raw", "N1", "N2", "N3"]
TJ = _pp("tj2_supplemental")
OD = os.path.join(TJ, "cache", "ii")
META = os.path.join(OD, "meta_ii.csv")
_G = {}

def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "4"))
    O = np.load(os.path.join(M.RESCACHE, "frozen_nuisance_ops.npz"))
    _G["OBJ"] = M.Objective(); _G["br"] = float(O["br"]); _G["s"] = float(O["s"])
    _G["Rse"] = O["Rse"]; _G["tse"] = O["tse"]
    _G["meta"] = pd.read_csv(META)

def _corrected(P, o, cond):
    d = (P - o) / np.linalg.norm(P - o, axis=1, keepdims=True)
    if cond == "raw": return P
    if cond == "N1": return P - _G["br"] * d
    if cond == "N2": return (_G["Rse"] @ P.T).T + _G["tse"]
    return P / _G["s"]

def _scan(args):
    ii, selfidx = args; OBJ = _G["OBJ"]; meta = _G["meta"]; i = int(meta.scan.iloc[ii])
    z = np.load(os.path.join(OD, f"scan_{i:04d}.npz")); P = z["aligned"].astype(np.float64)
    row = meta.iloc[ii]; o = np.array([row.ux, row.uy, row.uz]) * row.range_m
    gh_s = M.grad_hess(OBJ, OBJ.M[selfidx])
    sg = np.array([np.linalg.norm(gh_s["gp"]), np.linalg.norm(gh_s["gl"])])
    out = {"sg": sg, "S": {}}
    for c in CONDS:
        Q = _corrected(P, o, c); gh = M.grad_hess(OBJ, Q)
        d = np.column_stack([-np.linalg.pinv(gh["Hp"]) @ gh["gp"], -np.linalg.pinv(gh["Hl"]) @ gh["gl"]])
        rec = dict(J0=np.array(gh["J0"]), g=np.column_stack([gh["gp"], gh["gl"]]),
                   Hp=gh["Hp"], Hl=gh["Hl"], dhat=d)
        xs = np.zeros((6, 2)); js = np.zeros(2); it = np.zeros(2); ob = np.zeros(2)
        for k, fn in enumerate([M.local_min_p2p, M.local_min_p2l]):
            r = fn(OBJ, Q); xs[:, k] = r["xi"]; js[k] = OBJ.values(Q, r["xi"])[k]
            it[k] = r["iters"]; ob[k] = float(r["on_bound"])
        rec.update(xistar=xs, Jstar=js, iters=it, onbnd=ob); out["S"][c] = rec
    return ii, out

def main(nw=int(sys.argv[1]) if len(sys.argv) > 1 else 12):
    meta = pd.read_csv(META); n = len(meta)
    rng = np.random.default_rng(M.RNG_SEED)
    modeln = len(M.Objective().M)
    selfidx = [rng.choice(modeln, int(meta.n.iloc[ii]), replace=False) for ii in range(n)]
    S = {c: {k: [] for k in ["J0", "g", "Hp", "Hl", "dhat", "xistar", "Jstar", "iters", "onbnd"]} for c in CONDS}
    sg = []; order = []; t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for ii, out in ex.map(_scan, [(q, selfidx[q]) for q in range(n)], chunksize=4):
            order.append(ii); sg.append(out["sg"])
            for c in CONDS:
                for k in S[c]: S[c][k].append(out["S"][c][k])
            if (ii + 1) % 200 == 0: print(f"[ii] {ii+1}/{n} {time.perf_counter()-t0:.0f}s", flush=True)
    idx = np.argsort(order)
    def stack(c, k): a = np.array(S[c][k]); return a[idx]
    pack = {"ids": meta.scan.values, "self_gnorm": np.array(sg)[idx]}
    for c in CONDS:
        pack[f"{c}__J0"] = stack(c, "J0"); pack[f"{c}__g"] = stack(c, "g")
        pack[f"{c}__H"] = np.stack([stack(c, "Hp"), stack(c, "Hl")], axis=-1)
        pack[f"{c}__dhat"] = stack(c, "dhat"); pack[f"{c}__xistar"] = stack(c, "xistar")
        pack[f"{c}__Jstar"] = stack(c, "Jstar"); pack[f"{c}__iters"] = stack(c, "iters")
        pack[f"{c}__onbnd"] = stack(c, "onbnd")
    np.savez_compressed(os.path.join(OD, "ext_objective_ii.npz"), **pack)
    print(f"[ii] saved ext_objective_ii.npz in {time.perf_counter()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
