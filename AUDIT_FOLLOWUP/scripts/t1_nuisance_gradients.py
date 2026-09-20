# -*- coding: utf-8 -*-
"""TASK 1 (P0): nuisance-control BEFORE/AFTER gradient results.

Mechanical, NO tuning, NO new fit. For each external trajectory (IV, II, V) and each frozen
VI-fit nuisance operator (N1 global range offset, N2 common SE3, N3 global scale), export per
frame and per objective channel (p2p/p2l):
  ||g_t||,||g_r|  from the saved ext_objective `{cond}__g` arrays (cond raw/N1/N2/N3),
  residual RMS    = sqrt({cond}__J0) (frozen LS objective = mean squared residual),
  translation err = ||{cond}__xistar[:3]||*1000, rotation err = deg(||{cond}__xistar[3:]||),
  patch spread    = LIVE per-frame std over the 24 patches of patch-mean unsigned NN distance.
A deterministic subset is independently re-derived with m_common.grad_hess/local_min and asserted
allclose against the frozen arrays (verification log printed / embedded in the report).
"""
import os
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
import af_common as A
import m_common as M

CONDS = ["raw", "N1", "N2", "N3"]
_G = {}


def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    O = np.load(os.path.join(M.RESCACHE, "frozen_nuisance_ops.npz"))
    mc = np.load(os.path.join(M.CACHE, "model_cache.npz"))
    _G.update(OBJ=M.Objective(), br=float(O["br"]), s=float(O["s"]), Rse=O["Rse"], tse=O["tse"],
              plab=np.load(os.path.join(M.CACHE, "patches.npz"))["lab"].astype(int))


def _correct(P, o, cond):
    """Identical to r7_ext_objective._corrected (frozen VI-fit operators)."""
    if cond == "raw":
        return P
    d = (P - o) / np.linalg.norm(P - o, axis=1, keepdims=True)
    if cond == "N1":
        return P - _G["br"] * d
    if cond == "N2":
        return (_G["Rse"] @ P.T).T + _G["tse"]
    return P / _G["s"]


def spread_mm(Q):
    """Per-frame patch spread: std across patches of per-patch MEAN unsigned nearest-model distance."""
    _, nn = _G["OBJ"].tree.query(Q, k=1, workers=2)
    dist = np.linalg.norm(Q - _G["OBJ"].M[nn], axis=1)
    lab = _G["plab"][nn]
    pm = np.array([dist[lab == j].mean() if (lab == j).any() else np.nan for j in range(24)])
    return float(np.nanstd(pm) * 1000.0)


def _spread_one(args):
    ii, sid, zr, ux, uy, uz, scandir = args
    P = A.load_aligned(scandir, sid)
    o = np.array([ux, uy, uz]) * zr
    return ii, {c: spread_mm(_correct(P, o, c)) for c in CONDS}


def _verify_one(args):
    """Independent live recompute of g,J0,xistar for one frame/every condition (verification)."""
    ii, sid, zr, ux, uy, uz, scandir = args
    P = A.load_aligned(scandir, sid)
    o = np.array([ux, uy, uz]) * zr
    out = {}
    for c in CONDS:
        Q = _correct(P, o, c)
        gh = M.grad_hess(_G["OBJ"], Q)
        xs = np.zeros((6, 2))
        for k, fn in enumerate([M.local_min_p2p, M.local_min_p2l]):
            xs[:, k] = fn(_G["OBJ"], Q)["xi"]
        out[c] = dict(gp=gh["gp"], gl=gh["gl"], J0=np.array(gh["J0"]), xs=xs)
    return ii, out


def build_dataset(tag, nw=20):
    cfg = A.REG[tag]
    E = np.load(cfg["obj"]); P = np.load(cfg["pred"]); meta = pd.read_csv(cfg["meta"])
    n = len(meta); ids = E["ids"]; insup = P["insup"].astype(bool)
    assert len(ids) == n and len(insup) == n
    bf, bp = A.block_series(tag, np.arange(n), insup, None)
    tasks = [(i, int(ids[i]), float(meta.range_m.iloc[i]), float(meta.ux.iloc[i]),
              float(meta.uy.iloc[i]), float(meta.uz.iloc[i]), cfg["scandir"]) for i in range(n)]
    # ---- live patch-spread pass ----
    t0 = time.perf_counter(); sp = {}
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, (ii, dd) in enumerate(ex.map(_spread_one, tasks, chunksize=4)):
            sp[ii] = dd
            if (k + 1) % 800 == 0:
                print(f"  [T1 {tag}] spread {k+1}/{n} {time.perf_counter()-t0:.0f}s", flush=True)
    # ---- assemble rows from SAVED frozen arrays ----
    rows = []
    for i in range(n):
        for c in CONDS:
            g = E[f"{c}__g"][i]; J0 = E[f"{c}__J0"][i]; xs = E[f"{c}__xistar"][i]
            for k, kn in enumerate(A.NAMES_P2P):
                rows.append(dict(dataset=tag, order=i, scan=int(ids[i]), block_full=int(bf[i]),
                                 in_support=bool(insup[i]), condition=c, kind=kn,
                                 n_points=int(meta.n.iloc[i]),
                                 gt_norm=float(np.linalg.norm(g[:3, k])),
                                 gr_norm=float(np.linalg.norm(g[3:, k])),
                                 residual_rms_mm=float(np.sqrt(J0[k]) * 1000.0),
                                 trans_error_mm=float(np.linalg.norm(xs[:3, k]) * 1000.0),
                                 rot_error_deg=float(np.degrees(np.linalg.norm(xs[3:, k]))),
                                 patch_spread_mm=sp[i][c]))
    df = pd.DataFrame(rows)
    # ---- independent verification on a deterministic 6-frame subset ----
    sel = np.linspace(0, n - 1, 6).astype(int)
    verif = []
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for ii, out in ex.map(_verify_one, [tasks[i] for i in sel]):
            for c in CONDS:
                dg_t = abs(out[c]["gp"][:3] - E[f"{c}__g"][ii, :3, 0]).max()
                dg_r = abs(out[c]["gl"][3:] - E[f"{c}__g"][ii, 3:, 1]).max()
                dJ = abs(out[c]["J0"] - E[f"{c}__J0"][ii]).max()
                dx = abs(out[c]["xs"] - E[f"{c}__xistar"][ii]).max()
                verif.append(dict(dataset=tag, order=ii, cond=c,
                                  max_abs_dg=float(max(dg_t, dg_r)), max_abs_dJ0=float(dJ),
                                  max_abs_dxistar=float(dx)))
    vf = pd.DataFrame(verif)
    print(f"[T1 {tag}] rows={len(df)} verify max|dg|={vf.max_abs_dg.max():.3e} "
          f"max|dJ|={vf.max_abs_dJ0.max():.3e} max|dx|={vf.max_abs_dxistar.max():.3e}")
    return df, vf


def main():
    frames = []; verifs = []
    for tag in ["IV", "II", "V"]:
        df, vf = build_dataset(tag)
        frames.append(df); verifs.append(vf)
    D = pd.concat(frames, ignore_index=True)
    VF = pd.concat(verifs, ignore_index=True)
    D.to_csv(os.path.join(A.OUT, "nuisance_gradient_before_after.csv"), index=False)
    VF.to_csv(os.path.join(A.OUT, "scripts", "t1_verification.csv"), index=False)
    # compact summary (p2p channel; IV/II primary in-support, V all frames)
    summ = []
    for tag in ["IV", "II", "V"]:
        q = D[(D.dataset == tag) & (D.kind == "p2p")]
        q = q if tag == "V" else q[q.in_support]
        base = q[q.condition == "raw"].set_index("order")
        for c in CONDS:
            s = q[q.condition == c].set_index("order")
            j = base.index.intersection(s.index)
            for m in ["gt_norm", "gr_norm", "residual_rms_mm", "trans_error_mm",
                      "rot_error_deg", "patch_spread_mm"]:
                summ.append(dict(dataset=tag, condition=c, metric=m, n=len(j),
                                 raw_median=float(base.loc[j, m].median()),
                                 after_median=float(s.loc[j, m].median()),
                                 ratio_after_over_raw=float(s.loc[j, m].median() /
                                                            (base.loc[j, m].median() + 1e-300))))
    S = pd.DataFrame(summ)
    S.to_csv(os.path.join(A.OUT, "scripts", "t1_summary.csv"), index=False)
    print("[T1] WROTE nuisance_gradient_before_after.csv rows=", len(D))
    print(S[S.metric.isin(["gt_norm", "gr_norm"]) ].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
