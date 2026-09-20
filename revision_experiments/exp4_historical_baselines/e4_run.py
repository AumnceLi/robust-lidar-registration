# -*- coding: utf-8 -*-
"""Exp.4 -- cheapest historical state-level baselines (FROZEN; no retuning).

Adds exactly two state-level translation-bias baselines next to the EXISTING DBS, using the SAME
VI historical samples, the SAME k=16 adaptive-Gaussian view neighbors and weights, and the SAME
frozen support mask. Nothing is re-trained or tuned.

  * DBS (existing, run_dbs.py): vhat = unit(sum_s w_s unit(b_s)); mhat = sum_s w_s ||b_s||/sum w_s;
        correction = mhat*vhat  (direction of UNIT vectors averaged then renormalised, x mean magnitude).
  * Vector-DBS (NEW): b_hat(z) = sum_s w_s(z) b_s / sum_s w_s(z)  (direct mean of FULL vectors).
  * Global-Vector (NEW): ONE fixed 3-vector = equal-frame mean over the entire VI history, applied
        to every test frame (VI: leave-own-block-out mean for non-circularity).

All three are PERTURBATION-level translation-only corrections: xi_corr = xi_raw - b_hat, rotation
UNCHANGED (eR == raw). Patch is read from the existing frozen replay (replay79_arms.csv).
III is post-hoc / secondary diagnostic; its raw bias vector (no objective cache) is computed with
the FROZEN m_common.local_min_p2p, identical to Exp.3.
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

import os, sys, time
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1"); os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rev_common as Rv
M = Rv.M

OUT = os.path.dirname(os.path.abspath(__file__))
REPLAY = _pp("FOLLOWUP_6_9/scripts/replay79_arms.csv")
III_XI_CACHE = os.path.join(OUT, "_iii_raw_xi.npz")


def raw_xi_cached(traj):
    """Return raw GT-started local-optimum perturbation xi(n,6) [m,rad] in temporal order.
    VI/IV/II from frozen objective caches; III computed once with frozen solver and cached."""
    cfg = Rv.REG[traj]
    if traj != "III":
        z = np.load(cfg["obj"])
        return z["raw__xistar"][:, :, 0]
    if os.path.exists(III_XI_CACHE):
        return np.load(III_XI_CACHE)["xi"]
    fz = Rv.frozen_bundle(); model, tree = fz["model"], fz["tree_model"]
    insup = Rv.support_mask("III"); order_list = np.where(insup)[0]
    OBJ = M.Objective(); xi = np.full((cfg["n"], 6), np.nan)
    t0 = time.perf_counter()
    for k, order in enumerate(order_list):
        P = np.asarray(Rv.load_scan_npz("III", order)["aligned"], float)
        xi[order] = M.local_min_p2p(OBJ, P)["xi"]
        if (k + 1) % 50 == 0:
            print(f"  III raw xi {k+1}/{len(order_list)}  {time.perf_counter()-t0:.0f}s", flush=True)
    np.savez_compressed(III_XI_CACHE, xi=xi)
    return xi


def views(traj, lib):
    if traj == "VI":
        return lib["vrange"], lib["uview"]
    m = Rv.meta_frame(traj)
    return m["range_m"].values.astype(float), m[["ux", "uy", "uz"]].values.astype(float)


def main():
    fz = Rv.frozen_bundle(); lib = Rv.predictor_library(fz)
    Vmean, Vcnt = lib["Vmean"], lib["Vcnt"]; blocks = lib["blocks"]
    # VI historical realized raw bias vectors (m)
    OM = np.load(Rv.REG["VI"]["obj"]); b_hist = OM["raw__xistar"][:, :, 0]
    b_global_all = b_hist[:, :3].mean(0)          # one fixed 3-vector over entire VI history
    print(f"[global-vector] fixed VI-mean bias = {np.round(b_global_all*1000,2)} mm, "
          f"|.|={np.linalg.norm(b_global_all)*1000:.2f} mm")

    rep = pd.read_csv(REPLAY)
    patch_lkp = {(r.trajectory, int(r.order)): (r.et_mm, r.eR_deg)
                 for r in rep[rep.arm == "Patch"].itertuples()}
    raw_r79 = {(r.trajectory, int(r.order)): r.et_mm
               for r in rep[rep.arm == "Raw"].itertuples()}

    rows = []
    for traj in Rv.TRAJS:
        insup = Rv.support_mask(traj); xi = raw_xi_cached(traj)
        zr_all, zu_all = views(traj, lib)
        order_list = list(range(Rv.REG[traj]["n"])) if traj == "VI" else [i for i in range(Rv.REG[traj]["n"]) if insup[i]]
        for order in order_list:
            xi_t, xi_r = xi[order, :3], xi[order, 3:]
            tr = np.where(blocks != blocks[order])[0] if traj == "VI" else np.arange(501)
            cand, w, _ = Rv.view_neighbors(float(zr_all[order]), zu_all[order], lib, train_idx=tr)
            b_dbs = Rv.dbs_state_vector(cand, w, b_hist[:, :3])
            b_vec = Rv.vector_dbs_state_vector(cand, w, b_hist[:, :3])
            b_glob = b_hist[tr, :3].mean(0) if traj == "VI" else b_global_all
            raw_et = np.linalg.norm(xi_t) * 1000.0; raw_eR = np.degrees(np.linalg.norm(xi_r))
            et = lambda b: np.linalg.norm(xi_t - b) * 1000.0
            dbs_et, vec_et, glob_et = et(b_dbs), et(b_vec), et(b_glob)
            p_et, p_eR = patch_lkp[(traj, order)]
            r79 = raw_r79[(traj, order)]
            rows.append(dict(trajectory=traj, order=int(order),
                             in_support=bool(insup[order]), posthoc=int(Rv.REG[traj].get("posthoc", False)),
                             raw_et_mm=raw_et, raw_eR_deg=raw_eR, raw_et_replay79_mm=r79,
                             dbs_et_mm=dbs_et, vecdbs_et_mm=vec_et, globalvec_et_mm=glob_et,
                             patch_et_mm=p_et, patch_eR_deg=p_eR,
                             dbs_gain=raw_et - dbs_et, vecdbs_gain=raw_et - vec_et,
                             globalvec_gain=raw_et - glob_et, patch_gain=raw_et - p_et,
                             dbs_better=bool(dbs_et < raw_et), vecdbs_better=bool(vec_et < raw_et),
                             globalvec_better=bool(glob_et < raw_et), patch_better=bool(p_et < raw_et),
                             vec_beats_dbs=bool(vec_et < dbs_et)))
        print(f"[{traj}] frames={len(order_list)}", flush=True)
    fr = pd.DataFrame(rows)
    fr.to_csv(os.path.join(OUT, "dbs_vector_framewise.csv"), index=False)

    # --------------------------------------------------------------- trajectory summary
    methods = [("DBS", "dbs_et_mm", "dbs_gain", "dbs_better"),
               ("VectorDBS", "vecdbs_et_mm", "vecdbs_gain", "vecdbs_better"),
               ("GlobalVector", "globalvec_et_mm", "globalvec_gain", "globalvec_better"),
               ("Patch", "patch_et_mm", "patch_gain", "patch_better")]
    srows = []
    for traj, sub in fr.groupby("trajectory"):
        base = dict(trajectory=traj, n=len(sub),
                    raw_et_med=sub.raw_et_mm.median(), raw_eR_med=sub.raw_eR_deg.median(),
                    patch_eR_med=sub.patch_eR_deg.median(),
                    vec_beats_dbs_frac=sub.vec_beats_dbs.mean())
        for name, etc, gainc, betc in methods:
            base[f"{name}_et_med"] = sub[etc].median()
            base[f"{name}_paired_gain_med"] = sub[gainc].median()
            base[f"{name}_improved_frac"] = sub[betc].mean()
            base[f"{name}_reversal"] = bool(sub[gainc].median() < 0)   # median makes it worse
        srows.append(base)
    summ = pd.DataFrame(srows)
    summ.to_csv(os.path.join(OUT, "dbs_vector_summary.csv"), index=False)
    cols = ["trajectory", "n", "raw_et_med", "DBS_et_med", "VectorDBS_et_med", "GlobalVector_et_med",
            "Patch_et_med", "DBS_paired_gain_med", "VectorDBS_paired_gain_med",
            "GlobalVector_paired_gain_med", "Patch_paired_gain_med",
            "DBS_improved_frac", "VectorDBS_improved_frac", "GlobalVector_improved_frac",
            "Patch_improved_frac", "vec_beats_dbs_frac"]
    print(summ[cols].round(2).to_string(index=False))

    # --------------------------------------------------------------- figure: paired gain boxplots
    order_t = ["VI", "IV", "II", "III"]; labels = ["DBS", "VectorDBS", "GlobalVector", "Patch"]
    gcols = ["dbs_gain", "vecdbs_gain", "globalvec_gain", "patch_gain"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharey=False)
    for ax, traj in zip(axes.ravel(), order_t):
        sub = fr[fr.trajectory == traj]
        data = [sub[c].values for c in gcols]
        bp = ax.boxplot(data, tick_labels=labels, showfliers=False, widths=0.55,
                        medianprops=dict(color="black", lw=1.6))
        for i, c in enumerate(gcols):
            ax.scatter(np.full(len(sub), i + 1) + np.random.default_rng(i).uniform(-0.08, 0.08, len(sub)),
                       sub[c].values, s=4, color="0.55", alpha=0.25, zorder=1)
            ax.scatter(i + 1, sub[c].median(), color="crimson", zorder=3, s=22)
        ax.axhline(0, color="k", lw=1)
        tag = " (post-hoc)" if traj == "III" else ""
        ax.set_title(f"{traj}{tag}  n={len(sub)}"); ax.set_ylabel("paired translation gain vs Raw (mm)")
        ax.grid(alpha=0.25)
    fig.suptitle("Exp.4 historical state-level baselines: paired per-frame translation gain "
                 "(positive = better than Raw)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(OUT, "fig_historical_baselines.png"), dpi=150)
    print("[fig] fig_historical_baselines.png")


if __name__ == "__main__":
    main()
