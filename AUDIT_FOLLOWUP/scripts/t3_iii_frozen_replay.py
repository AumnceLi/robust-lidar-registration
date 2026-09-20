# -*- coding: utf-8 -*-
"""TASK 3 (P0): deterministic FROZEN replay of Dataset III.

III's frozen artifacts stored only error NORMS (et_mm/eR_deg); the predicted dxi and the realized
6-vector were never saved, so III translation-direction cosine and III-DBS could not be formed.
This is an APPENDED FROZEN DIAGNOSTIC: every parameter stays frozen, III is NOT reopened as
development data and nothing is tuned or selected on III outcomes.

Outputs:
  iii_frozen_replay_frame.csv : per frame predicted_dxi[6] & realized_xi[6] (p2p AND p2l), norms, iters
  iii_direction_cosine.csv    : pred-vs-realized cosine for translation and rotation (both channels)
  iii_dbs.csv                 : B1/DBS translation subtraction using the SAME frozen VI library/rule as
                                FINAL_TOPJOURNAL_HARDENING/DIRECT_BIAS_BASELINE/run_dbs.py
Verification: realized p2p must reproduce saved g1_iii M0_raw_p2p; the r8-equivalent prediction path is
validated bit-for-bit on Dataset II against ext_predict_ii.npz before being applied to III.
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
import g_common as G

K = 16
_G = {}


def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    fz = A.frozen_bundle()
    OBJ = M.Objective()
    OM = np.load(os.path.join(M.RESCACHE, "objective_main.npz"))
    vi_xi = OM["raw__xistar"][:, :, 0]
    vi_t = vi_xi[:, :3]
    d_vi = vi_t / np.linalg.norm(vi_t, axis=1, keepdims=True)
    m_vi = np.linalg.norm(vi_t, axis=1)
    _G.update(model=fz["model"], normals=fz["normals"], plab=fz["plab"], sf=fz["s_floor"],
              Vmean=fz["Vmean"], Vcnt=fz["Vcnt"], vrange=fz["vrange"], uview=fz["uview"],
              OBJ=OBJ, d_vi=d_vi, m_vi=m_vi, m_global=float(np.median(m_vi)))


def cos3(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 1e-12 and nb > 1e-12 else np.nan


def b1_view(r, u, train=np.arange(501)):
    """Exact replica of run_dbs.view_predict_mag (k=16 adaptive Gaussian, train=all 501 VI)."""
    vr, uv = _G["vrange"], _G["uview"]
    dd = np.sqrt(((r - vr[train]) / G.RANGE_STD) ** 2 +
                 np.arccos(np.clip(u @ uv[train].T, -1, 1)) ** 2)
    order = np.argsort(dd)[:K]; cand = train[order]
    dk = max(dd[order[-1]], 1e-9); w = np.exp(-0.5 * (dd[order] / dk) ** 2)
    vhat = (w[:, None] * _G["d_vi"][cand]).sum(0)
    vhat /= np.linalg.norm(vhat)
    mhat = float((w * _G["m_vi"][cand]).sum() / w.sum())
    return vhat, mhat


def predicted_dxi(P, nnidx, zr, zu):
    """Exact replica of r8_ext_predict._scan: dxi=-pinv(H_nom) g_corr on GT-local nominal correspondence."""
    mu, dmin = G.mu_for_view(_G["Vmean"], _G["Vcnt"], _G["vrange"], _G["uview"], zr, zu)
    lab = _G["plab"][nnidx]
    m_nom = _G["OBJ"].M[nnidx]
    Qhat = m_nom + mu[lab]
    gh = M.grad_hess(_G["OBJ"], Qhat)
    gn = M.grad_hess(_G["OBJ"], m_nom)
    dxi = np.column_stack([-np.linalg.pinv(gn["Hp"]) @ gh["gp"],
                           -np.linalg.pinv(gn["Hl"]) @ gh["gl"]])
    return dxi, dmin


def _one(args):
    order, sid, zr, ux, uy, uz = args
    zu = np.array([ux, uy, uz])
    z = np.load(os.path.join(A.III, f"scan_{int(sid):04d}.npz"))
    P = z["aligned"].astype(np.float64); nnidx = z["nnidx"]
    dxi, dmin = predicted_dxi(P, nnidx, zr, zu)
    r_p = G.robust_icp(_G["model"], _G["normals"], _G["OBJ"].tree, P, "p2p", "ls", s_floor=_G["sf"])
    r_l = G.robust_icp(_G["model"], _G["normals"], _G["OBJ"].tree, P, "p2l", "ls", s_floor=_G["sf"])
    xp, xl = r_p["xi"], r_l["xi"]
    vhat, mhat = b1_view(zr, zu)
    dbs_t = xp[:3] - mhat * vhat
    dbs_t_sens = xp[:3] - _G["m_global"] * vhat
    fr = dict(order=order, scan=int(sid), range_m=zr, nearest_d=float(dmin),
              pred_et_mm_p2p=float(np.linalg.norm(dxi[:3, 0]) * 1000),
              pred_eR_deg_p2p=float(np.degrees(np.linalg.norm(dxi[3:, 0]))),
              pred_et_mm_p2l=float(np.linalg.norm(dxi[:3, 1]) * 1000),
              pred_eR_deg_p2l=float(np.degrees(np.linalg.norm(dxi[3:, 1]))),
              real_et_mm_p2p=float(np.linalg.norm(xp[:3]) * 1000),
              real_eR_deg_p2p=float(np.degrees(np.linalg.norm(xp[3:]))),
              real_et_mm_p2l=float(np.linalg.norm(xl[:3]) * 1000),
              real_eR_deg_p2l=float(np.degrees(np.linalg.norm(xl[3:]))),
              iters_p2p=int(r_p["iters"]), iters_p2l=int(r_l["iters"]),
              onbound_p2p=int(r_p["on_bound"]))
    for a in range(6):
        fr[f"pred_dxi{a}_p2p"] = float(dxi[a, 0]); fr[f"pred_dxi{a}_p2l"] = float(dxi[a, 1])
        fr[f"real_xi{a}_p2p"] = float(xp[a]); fr[f"real_xi{a}_p2l"] = float(xl[a])
    co = dict(order=order, scan=int(sid),
              cos_translation_p2p=cos3(dxi[:3, 0], xp[:3]), cos_rotation_p2p=cos3(dxi[3:, 0], xp[3:]),
              cos_translation_p2l=cos3(dxi[:3, 1], xl[:3]), cos_rotation_p2l=cos3(dxi[3:, 1], xl[3:]),
              pred_et_mm_p2p=fr["pred_et_mm_p2p"], real_et_mm_p2p=fr["real_et_mm_p2p"],
              pred_eR_deg_p2p=fr["pred_eR_deg_p2p"], real_eR_deg_p2p=fr["real_eR_deg_p2p"])
    db = dict(order=order, scan=int(sid), dbs_mhat_m=float(mhat),
              raw_ete_mm=float(np.linalg.norm(xp[:3]) * 1000),
              dbs_ete_mm=float(np.linalg.norm(dbs_t) * 1000),
              dbs_ete_sens_globalmed_mm=float(np.linalg.norm(dbs_t_sens) * 1000),
              raw_eR_deg=float(np.degrees(np.linalg.norm(xp[3:]))),
              dbs_eR_deg=float(np.degrees(np.linalg.norm(xp[3:]))),
              dir_cos_vhat_realized=cos3(vhat, xp[:3]),
              improved_primary=bool(np.linalg.norm(dbs_t) < np.linalg.norm(xp[:3])))
    return fr, co, db


def validate_prediction_path_on_II(n_check=24):
    """Bit-level check that this r8 replica reproduces the SAVED Dataset-II predicted dxi."""
    II = A.REG["II"]; P = np.load(II["pred"]); meta = pd.read_csv(II["meta"])
    rng = np.random.default_rng(7); sel = np.sort(rng.choice(len(meta), n_check, replace=False))
    worst = 0.0
    for i in sel:
        sid = int(meta.scan.iloc[i]); zr = float(meta.range_m.iloc[i]); zu = meta[["ux", "uy", "uz"]].iloc[i].values
        z = np.load(os.path.join(II["scandir"], f"scan_{sid:04d}.npz"))
        dxi, _ = predicted_dxi(z["aligned"].astype(np.float64), z["nnidx"], zr, zu)
        worst = max(worst, float(np.abs(dxi - P["dxi"][i]).max()))
    return worst, n_check


def run(nw=22):
    meta = pd.read_csv(os.path.join(A.III, "meta_iii.csv"))
    P3 = np.load(os.path.join(A.III, "ext_predict_iii.npz"))
    insup = P3["insup"].astype(bool)
    assert len(meta) == 1302 and int(insup.sum()) == 371
    tasks = [(i, int(meta.scan.iloc[i]), float(meta.range_m.iloc[i]), float(meta.ux.iloc[i]),
              float(meta.uy.iloc[i]), float(meta.uz.iloc[i])) for i in range(len(meta))]
    # prediction-path validation on II (single process init)
    _init(); wII, nII = validate_prediction_path_on_II()
    print(f"[T3] r8-replica vs saved ext_predict_ii dxi: max|diff|={wII:.3e} over {nII} frames")
    F, C, D = [], [], []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, (fr, co, db) in enumerate(ex.map(_one, tasks, chunksize=3)):
            fr["in_support"] = bool(insup[k]); co["in_support"] = bool(insup[k]); db["in_support"] = bool(insup[k])
            F.append(fr); C.append(co); D.append(db)
            if (k + 1) % 400 == 0:
                print(f"  [T3] {k+1}/{len(tasks)} {time.perf_counter()-t0:.0f}s", flush=True)
    Fdf = pd.DataFrame(F); Cdf = pd.DataFrame(C); Ddf = pd.DataFrame(D)
    bf, bp = A.block_series("III", Fdf.order.values, insup)
    for dd in (Fdf, Cdf, Ddf):
        dd["block_full"] = bf; dd["block_primary"] = bp
    Fdf.to_csv(os.path.join(A.OUT, "iii_frozen_replay_frame.csv"), index=False)
    Cdf.to_csv(os.path.join(A.OUT, "iii_direction_cosine.csv"), index=False)
    Ddf.to_csv(os.path.join(A.OUT, "iii_dbs.csv"), index=False)
    # verification vs saved g1_iii M0_raw_p2p
    g1 = pd.read_csv(os.path.join(A.GCHAIN, "G3_FINAL_CONFIRMATION", "results", "g1_iii.csv"))
    m0 = g1[g1.method == "M0_raw_p2p"].sort_values("order").reset_index(drop=True)
    det = (m0.et_mm.values - Fdf.sort_values("order").real_et_mm_p2p.values)
    der = (m0.eR_deg.values - Fdf.sort_values("order").real_eR_deg_p2p.values)
    log = [f"III frozen replay verification",
           f"r8-replica vs saved ext_predict_ii dxi max|diff| = {wII:.3e} over {nII} sampled II frames",
           f"realized p2p et vs saved g1_iii M0_raw_p2p max|diff| = {np.abs(det).max():.3e} mm over 1302",
           f"realized p2p eR vs saved g1_iii M0_raw_p2p max|diff| = {np.abs(der).max():.3e} deg over 1302",
           f"in-support = {int(insup.sum())}/1302 (matches metadata screen 371)",
           f"III-DBS primary median mm: raw {Ddf[Ddf.in_support].raw_ete_mm.median():.3f} -> "
           f"dbs {Ddf[Ddf.in_support].dbs_ete_mm.median():.3f}; improved-frame rate "
           f"{Ddf[Ddf.in_support].improved_primary.mean():.3f}",
           f"translation dir cosine p2p in-support median = "
           f"{Cdf[Cdf.in_support].cos_translation_p2p.median():.4f}"]
    open(os.path.join(A.OUT, "scripts", "t3_verification.log"), "w").write("\n".join(log) + "\n")
    print("\n".join(log))
    print("[T3] wrote three III csvs")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--nw", type=int, default=22)
    run(ap.parse_args().nw)
