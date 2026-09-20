# -*- coding: utf-8 -*-
"""ITEM 8 -- Equal-RMS / matched-severity mechanism test (FROZEN; no tuning).

PRIMARY evidence uses the STORED frozen synthetic results geometry_results.csv (p2p LS):
  residual_RMS=sqrt(J0)*1000 mm, translation_bias=et_mm, rotation_bias=eR_deg (median over 20 reps).
Mechanism descriptors ||g_t||,||g_r||,||P_JW delta|| (t5 analytic factor-1 normal-equation
convention, gradient x2 to match the frozen FD convention), eta_t,eta_R (phase_map _eta) and
affected fraction alpha (phase_map _alpha, pure geometry) are MECHANICALLY RE-DERIVED with the
frozen generator g_generality_run + frozen solver under a declared fixed PYTHONHASHSEED=0; they are
validated against (i) phase_map results_long alpha (must be exact) and (ii) stored condition medians.
Matching rule pre-fixed: within the SAME geometry, pair each condition with its NEAREST cross-family
RMS neighbor; keep if relative RMS diff <= 5% (primary). 10% reported as sensitivity only.
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

import os
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys, importlib.util
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, _pp("g_chain/common"))
sys.path.insert(0, _pp("g_chain/G_GENERALITY/scripts"))
import g_common as G
spec = importlib.util.spec_from_file_location("ggr", _pp("g_chain/G_GENERALITY/scripts/g_generality_run.py"))
GG = importlib.util.module_from_spec(spec); spec.loader.exec_module(GG)

OUT = _pp("FOLLOWUP_6_9"); GG_RES = _pp("g_chain/G_GENERALITY/results")
PM = _pp("FINAL_TOPJOURNAL_HARDENING/OPTIONAL_PHASE_MAP/results_long.csv")
GEOMS = ["GA", "GB", "GC"]
DTYPES = {
 "D1_appendage_disp": ([0, 2, 5, 10, 25, 50, 100], "mm", "coherent_extensive"),
 "D2_missing_component": ([0, .25, .5, .75, .9, 1.0], "frac", "localized_gross"),
 "D3_local_surface_off": ([0, 2, 5, 10, 25, 50, 100], "mm", "localized_gross_small"),
 "D4_appendage_scale": ([0, .005, .01, .025, .05, .10], "frac", "low_projection_nuisance"),
 "D5_appendage_tilt": ([0, .1, .25, .5, 1, 2], "deg", "coherent_extensive_rot"),
 "CTRL_random_noise": ([2, 5, 10, 25, 50, 100], "mm", "unstructured_noise"),
}
N_REP = 20
_G = {}


def _hat(w):
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])


def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    for g in GEOMS:
        M, Nm, comp, specd = GG.build_geometry(g)
        _G[g] = dict(M=M, Nm=Nm, comp=comp, spec=specd, tree=cKDTree(M),
                     sf=float(np.median(cKDTree(M).query(M, k=2)[0][:, 1])))


def _alpha(M, comp, Ptrue, model_keep):
    if not model_keep.all():
        return float((~model_keep).mean())
    return float((np.linalg.norm(Ptrue - M, axis=1) > 1e-9).mean())


def _eta(Mreg, tree, P):
    _, idx = tree.query(P, k=1, workers=1)
    q = Mreg[idx]; r = P - q; nr = np.linalg.norm(r, axis=1)
    eta_t = float(np.linalg.norm(r.sum(0)) / nr.sum()) if nr.sum() > 1e-12 else 0.0
    cr = np.cross(q, r); ncr = np.linalg.norm(cr, axis=1)
    eta_R = float(np.linalg.norm(cr.sum(0)) / ncr.sum()) if ncr.sum() > 1e-12 else 0.0
    return eta_t, eta_R


def pose_active(Mreg, tree, P):
    """t5 analytic factor-1 normal equations at xi=0 (p2p). Gradient reported x2 (FD convention);
    PJW = sqrt(g H^-1 g) in mm. Returns rms_mm, gt(2x), gr(2x), pjw_mm and translation/rotation PJW."""
    _, nn = tree.query(P, k=1, workers=1)
    q = Mreg[nn]; delta = P - q; N = len(P)
    gt = delta.mean(0); gr = np.cross(P, delta).mean(0)
    Htr = _hat(P.mean(0))                                   # mean [p_i]_x = [mean p_i]_x
    Hrr = np.eye(3) * (P ** 2).sum(1).mean() - (P.T @ P) / N   # mean [p]_x^T[p]_x, vectorized
    H = np.block([[np.eye(3), Htr], [Htr.T, Hrr]])
    g6 = np.concatenate([gt, gr])
    d = np.linalg.solve(H, g6)
    pjw = float(np.sqrt(max(g6 @ d, 0)))
    pjw_t = float(np.linalg.norm(d[:3])); pjw_r = float(np.linalg.norm(d[3:]))
    rms = float(np.sqrt((delta ** 2).sum(1).mean()))
    return rms * 1000, 2 * float(np.linalg.norm(gt)), 2 * float(np.linalg.norm(gr)), pjw * 1000, pjw_t * 1000, pjw_r * 1000


def _one(args):
    geom, dtype, mag, rep = args
    Gd = _G[geom]; M, Nm, comp, specd, tree0, sf0 = Gd["M"], Gd["Nm"], Gd["comp"], Gd["spec"], Gd["tree"], Gd["sf"]
    vant = specd["vants"][rep % 3]
    if dtype == "CTRL_random_noise":     # unstructured isotropic-noise control on NOMINAL model
        rng = np.random.default_rng(40_000 + (hash(geom) % 100000) + rep)
        P = GG._observe(M, Nm, vant, rng, extra_noise_mm=mag)
        Mreg, tree, alpha = M, tree0, 0.0
    else:                                # structured discrepancy families D1-D5
        rng = np.random.default_rng(10_000 + (hash((geom, dtype)) % 100000) + rep)
        Ptrue, Ntrue, model_keep = GG.apply_discrepancy(M, Nm, comp, specd, dtype, mag)
        alpha = _alpha(M, comp, Ptrue, model_keep)
        if model_keep.all():
            Mreg, tree = M, tree0
        else:
            Mreg = M[model_keep]; tree = cKDTree(Mreg)
        P = GG._observe(Ptrue, Ntrue, vant, rng)
    eta_t, eta_R = _eta(Mreg, tree, P)
    rms, gt, gr, pjw, pjw_t, pjw_r = pose_active(Mreg, tree, P)
    r = G.robust_icp(Mreg, Nm, tree, P, "p2p", "ls", s_floor=sf0)
    return dict(geometry=geom, dtype=dtype, family=dtype.split("_")[0], mag=mag, rep=rep,
                alpha=alpha, eta_t=eta_t, eta_R=eta_R, rms_re_mm=rms, gt=gt, gr=gr, pjw=pjw,
                pjw_t=pjw_t, pjw_r=pjw_r, et_mm=float(np.linalg.norm(r["xi"][:3]) * 1000),
                eR_deg=float(np.degrees(np.linalg.norm(r["xi"][3:]))))


def stored_condition():
    gr = pd.read_csv(os.path.join(GG_RES, "geometry_results.csv"))
    d = gr[(gr.kind == "p2p") & (gr.form == "ls")].copy()
    d["rms_mm"] = np.sqrt(d.J0) * 1000; d["family"] = d.dtype.str.split("_").str[0]
    agg = d.groupby(["geometry", "dtype", "family", "mag"]).agg(
        res_RMS_mm=("rms_mm", "median"), rms_q25=("rms_mm", lambda x: x.quantile(.25)),
        rms_q75=("rms_mm", lambda x: x.quantile(.75)),
        translation_bias_mm=("et_mm", "median"), tb_q25=("et_mm", lambda x: x.quantile(.25)),
        tb_q75=("et_mm", lambda x: x.quantile(.75)),
        rotation_bias_deg=("eR_deg", "median"),
        grad_total=("grad_gt", "median"), n_rep=("rep", "nunique")).reset_index()
    return agg


def run(nw=16):
    tasks = [(g, dt, mag, rep) for g in GEOMS for dt, (mags, _, _) in DTYPES.items()
             for mag in mags for rep in range(N_REP)]
    rows = []
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, r in enumerate(ex.map(_one, tasks, chunksize=8)):
            rows.append(r)
    R = pd.DataFrame(rows)
    mech = R.groupby(["geometry", "dtype", "family", "mag"]).agg(
        alpha=("alpha", "median"), eta_t=("eta_t", "median"), eta_R=("eta_R", "median"),
        gt_norm=("gt", "median"), gr_norm=("gr", "median"), pjw_mm=("pjw", "median"),
        pjw_t_mm=("pjw_t", "median"), pjw_r_mm=("pjw_r", "median"),
        re_rms_mm=("rms_re_mm", "median"), re_et_mm=("et_mm", "median"), re_eR_deg=("eR_deg", "median")).reset_index()
    cond = stored_condition().merge(mech, on=["geometry", "dtype", "family", "mag"], how="left")
    cond["organization"] = cond.dtype.map(lambda x: DTYPES[x][2])
    cond.to_csv(os.path.join(OUT, "followup8_condition_summary.csv"), index=False)

    # ---- validation vs frozen artifacts (robust merge; alpha must be exact) ----
    pm = pd.read_csv(PM); pm = pm[pm.loss == "ls"]
    vm = cond.merge(pm, left_on=["geometry", "dtype", "mag"], right_on=["geometry", "dtype", "dose"], how="inner")
    v_alpha = (vm.alpha_x - vm.alpha_y).abs().values
    v_eta_t = (vm.eta_t_x - vm.eta_t_y).abs().values
    v_eta_r = (vm.eta_R_x - vm.eta_R_y).abs().values
    nz = cond[cond.mag > 0]
    rel_et = ((nz.re_et_mm - nz.translation_bias_mm).abs() / nz.translation_bias_mm.replace(0, np.nan)).dropna()
    rel_rms = ((nz.re_rms_mm - nz.res_RMS_mm).abs() / nz.res_RMS_mm).dropna()
    val = dict(alpha_max_abs_diff_vs_phasemap=float(np.max(v_alpha)),
               eta_t_median_abs_diff=float(np.median(v_eta_t)), eta_R_median_abs_diff=float(np.median(v_eta_r)),
               re_vs_stored_et_median_rel_diff=float(rel_et.median()),
               re_vs_stored_et_p90_rel_diff=float(rel_et.quantile(.9)),
               re_vs_stored_rms_median_rel_diff=float(rel_rms.median()))
    pd.Series(val).to_csv(os.path.join(OUT, "scripts", "item8_validation.csv"))
    print("[item8 validation]", val)

    # ---- matched-RMS cross-family pairs (within geometry), 5% primary / 10% sensitivity ----
    def build_pairs(thr):
        rows = []
        for geom in GEOMS:
            q = cond[(cond.geometry == geom) & (cond.mag > 0)].reset_index(drop=True)
            for i, a in q.iterrows():
                cand = q[q.family != a.family].copy()
                cand["reldiff"] = (cand.res_RMS_mm - a.res_RMS_mm).abs() / np.maximum(cand.res_RMS_mm, a.res_RMS_mm)
                cand = cand.sort_values("reldiff")
                if not len(cand):
                    continue
                b = cand.iloc[0]                       # single NEAREST cross-family neighbor (pre-fixed)
                if b.reldiff > thr:
                    continue
                rows.append(_pair_row(geom, a, b, thr))
        return pd.DataFrame(rows)
    P5 = build_pairs(.05); P10 = build_pairs(.10)
    P5["threshold"] = "primary_5pct"
    P5.to_csv(os.path.join(OUT, "followup8_equal_rms_pairs.csv"), index=False)
    P10["threshold"] = "sensitivity_10pct"
    P10.to_csv(os.path.join(OUT, "scripts", "item8_pairs_10pct.csv"), index=False)
    print(f"[item8] 5% pairs={len(P5)}  10% pairs={len(P10)}")
    aggregate_trend(P5, "5pct")
    aggregate_trend(P10, "10pct")
    d4 = P5[(P5.dtypeA == "D4_appendage_scale") | (P5.dtypeB == "D4_appendage_scale")]
    print("\n[item8] D4 matched pairs (5%):\n",
          d4[["geometry", "dtypeA", "rmsA", "dtypeB", "rmsB", "reldiff", "etA", "etB", "bias_ratio"]].round(3).to_string(index=False))
    return cond, P5, P10, val


def _pair_row(geom, a, b, thr):
    da = b.translation_bias_mm - a.translation_bias_mm
    return dict(geometry=geom, dtypeA=a["dtype"], familyA=a.family, orgA=a.organization, magA=a.mag,
                dtypeB=b["dtype"], familyB=b.family, orgB=b.organization, magB=b.mag,
                rmsA=a.res_RMS_mm, rmsB=b.res_RMS_mm, rms_diff=abs(a.res_RMS_mm - b.res_RMS_mm),
                reldiff=abs(a.res_RMS_mm - b.res_RMS_mm) / max(a.res_RMS_mm, b.res_RMS_mm),
                gradA=a.grad_total, gradB=b.grad_total, grad_diff=abs(a.grad_total - b.grad_total),
                gtA=a.gt_norm, gtB=b.gt_norm, d_gt=abs(a.gt_norm - b.gt_norm),
                pjwA=a.pjw_mm, pjwB=b.pjw_mm, d_pjw=abs(a.pjw_mm - b.pjw_mm),
                eta_tA=a.eta_t, eta_tB=b.eta_t, alphaA=a.alpha, alphaB=b.alpha,
                etA=a.translation_bias_mm, etB=b.translation_bias_mm,
                eRA=a.rotation_bias_deg, eRB=b.rotation_bias_deg,
                bias_diff=abs(a.translation_bias_mm - b.translation_bias_mm),
                bias_ratio=max(a.translation_bias_mm, b.translation_bias_mm) /
                           max(min(a.translation_bias_mm, b.translation_bias_mm), 1e-6),
                rot_bias_diff=abs(a.rotation_bias_deg - b.rotation_bias_deg))


def aggregate_trend(P, tag):
    P = P[np.isfinite(P.d_gt) & np.isfinite(P.d_pjw)]
    r1 = spearmanr(P.bias_diff, P.d_gt); r2 = spearmanr(P.bias_diff, P.d_pjw)
    r3 = spearmanr(P.bias_diff, P.rms_diff)
    # direction: how often larger-bias side also has larger ||g_t|| / PJW
    same_gt = np.mean(np.sign(P.etB - P.etA) == np.sign(P.gtB - P.gtA))
    print(f"[aggregate {tag}] N={len(P)}  Spearman |dbias|~|dgt| rho={r1.statistic:.3f} p={r1.pvalue:.3g}; "
          f"~|dPJW| rho={r2.statistic:.3f} p={r2.pvalue:.3g}; ~|dRMS| rho={r3.statistic:.3f}; "
          f"sign-agree(bias,gt)={same_gt:.2f}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--nw", type=int, default=16)
    run(ap.parse_args().nw)
