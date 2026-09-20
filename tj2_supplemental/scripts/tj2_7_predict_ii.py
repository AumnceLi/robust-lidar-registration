# -*- coding: utf-8 -*-
"""TJ2 P3 non-circular prediction for Dataset II. Numerically identical to frozen
r8_ext_predict.py: VI frozen template + II GT geometry + nominal CAD ONLY; II current-frame
residual never enters. dxi=-pinv(H_nom) ghat. Also recomputes frozen dmin/IN_SUPPORT (validated
bitwise-identical to the Phase-1 screen and to TJ1 IV/V flags)."""
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
import s0_common as C, m_common as M

TJ = _pp("tj2_supplemental")
OD = os.path.join(TJ, "cache", "ii"); RC = M.RESCACHE; KP = 24
META = os.path.join(OD, "meta_ii.csv")
_G = {}

def _init(Vmean, Vcnt, vr, uv, sr, k, tau):
    import os as _os; _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "4"))
    _G.update(OBJ=M.Objective(), PLAB=np.load(os.path.join(M.CACHE, "patches.npz"))["lab"],
              Vmean=Vmean, Vcnt=Vcnt, vr=vr, uv=uv, sr=sr, k=k, tau=tau,
              meta=pd.read_csv(META))

def _mu(zr, zu):
    Vmean, Vcnt, vr, uv, sr, k = _G["Vmean"], _G["Vcnt"], _G["vr"], _G["uv"], _G["sr"], _G["k"]
    D = np.sqrt(((vr - zr) / sr) ** 2 + np.arccos(np.clip(uv @ zu, -1, 1)) ** 2)
    order = np.argsort(D)[:k]; dk = max(D[order[-1]], 1e-9)
    w = np.exp(-0.5 * (D[order] / dk) ** 2); wc = Vcnt[order] > 0
    num = np.einsum("k,kpj,kp->pj", w, Vmean[order], wc); den = (w[:, None] * wc).sum(0)
    mu = np.zeros((KP, 3)); ok = den > 0; mu[ok] = num[ok] / den[ok, None]
    if (~ok).any():
        aw = 1.0 / (1 + D)
        for j in np.where(~ok)[0]:
            seen = Vcnt[:, j] > 0
            if seen.any(): mu[j] = (aw[seen, None] * Vmean[seen, j]).sum(0) / aw[seen].sum()
    return mu, D.min()

def _scan(ii):
    OBJ = _G["OBJ"]; meta = _G["meta"]; i = int(meta.scan.iloc[ii])
    z = np.load(os.path.join(OD, f"scan_{i:04d}.npz")); nn = z["nnidx"]
    row = meta.iloc[ii]; zu = np.array([row.ux, row.uy, row.uz]); zr = row.range_m
    mu, dmin = _mu(zr, zu)
    m_nom = OBJ.M[nn]; Qhat = m_nom + mu[_G["PLAB"][nn]]
    gh = M.grad_hess(OBJ, Qhat); gn = M.grad_hess(OBJ, m_nom)
    dxi = np.column_stack([-np.linalg.pinv(gn["Hp"]) @ gh["gp"], -np.linalg.pinv(gn["Hl"]) @ gh["gl"]])
    s_hat = np.einsum("pj,pj->p", mu[_G["PLAB"][nn]], OBJ.nM[nn]); D1 = np.einsum("p,pj->j", s_hat, m_nom) / len(nn)
    return ii, dxi, D1, dmin, dmin <= _G["tau"]

def main(nw=int(sys.argv[1]) if len(sys.argv) > 1 else 12):
    F = np.load(os.path.join(RC, "VI_ONLY_PREDICTOR_FROZEN.npz"))
    Vmean, Vcnt, vr, uv = F["Vmean"], F["Vcnt"], F["vrange"], F["uview"]
    sr = float(F["range_std"]); k = int(F["kstar"]); tau = float(F["tau_support"])
    meta = pd.read_csv(META); n = len(meta)
    E = np.load(os.path.join(OD, "ext_objective_ii.npz")); xstar = E["raw__xistar"]; ids = E["ids"]
    dxi = np.zeros((n, 6, 2)); d1 = np.zeros((n, 3)); nd = np.zeros(n); ins = np.zeros(n, bool)
    order = []; t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=nw, initializer=_init,
                             initargs=(Vmean, Vcnt, vr, uv, sr, k, tau)) as ex:
        for ii, a, b, c, e in ex.map(_scan, range(n), chunksize=4):
            order.append(ii); dxi[ii] = a; d1[ii] = b; nd[ii] = c; ins[ii] = e
            if (ii + 1) % 200 == 0: print(f"[ii] {ii+1}/{n} {time.perf_counter()-t0:.0f}s", flush=True)
    np.savez_compressed(os.path.join(OD, "ext_predict_ii.npz"),
                        dxi=dxi, d1=d1, ndist=nd, insup=ins, tau=tau, ids=ids)
    rows = []
    for ki, kn in enumerate(["p2p", "p2l"]):
        for ii in range(n):
            a = dxi[ii, :3, ki]; b = xstar[ii, :3, ki]
            cos = M.cosine(a, b) if (np.linalg.norm(a) > 1e-12 and np.linalg.norm(b) > 1e-12) else np.nan
            rows.append(dict(scan=int(ids[ii]), obj=kn, in_support=bool(ins[ii]), ndist=nd[ii], cos_dir=cos,
                             pred_t_mm=np.linalg.norm(a) * 1000, obs_t_mm=np.linalg.norm(b) * 1000,
                             cos_D1=M.cosine(-d1[ii], b) if np.linalg.norm(d1[ii]) > 1e-12 else np.nan))
    pd.DataFrame(rows).to_csv(os.path.join(TJ, "results", "ii_prediction.csv"), index=False)
    print(f"[ii] IN_SUPPORT={ins.sum()}/{n} tau={tau:.4f} in {time.perf_counter()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
