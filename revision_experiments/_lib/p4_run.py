# -*- coding: utf-8 -*-
"""p4_run.py -- P4: IV-success vs II-failure transfer diagnostic (NO new algorithm, NO hand-picking).

Pre-registered frame rule (declared before looking at any frame): effect = full_minus_patch_mm
(Full translation minus Patch translation; >0 => Full view-conditioned field improves over the
view-independent Patch). Bins per trajectory:
  best10%  : effect >= 90th percentile ; median : within +-5% rank of the median ;
  worst10% : effect <= 10th percentile.
Exactly ONE representative per bin = the frame whose effect is closest to that bin's median.
Diagnostics are the EXISTING view-support descriptors (nearest-view distance, kernel ESS, coverage,
fallback count, correction magnitude, predicted-step alignment) plus per-patch support / correction
vectors recomputed for the 6 representative frames only.
"""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import revx_common as R

OUT = os.path.join(R.REV, "06_II_failure_cases"); os.makedirs(OUT, exist_ok=True)
SUP = os.path.join(R.ROOT, "FOLLOWUP_6_9", "scripts", "replay79_support.csv")
TRAJS = ["IV", "II"]
BINNAMES = ["worst10", "median", "best10"]
DESC = ["nearest_d", "nearest_over_tau", "ess_kernel", "coverage", "n_fallback", "n_valid_patchobs",
        "corr_full_median_mm", "corr_patch_mean_mm", "cos_pred_full_t", "full_minus_patch_mm"]


def bin_of(e):
    q10, q90 = np.percentile(e, 10), np.percentile(e, 90)
    rk = pd.Series(e).rank(pct=True).values
    b = np.full(len(e), "middle", object)
    b[e >= q90] = "best10"; b[e <= q10] = "worst10"
    b[(rk >= 0.45) & (rk <= 0.55)] = "median"
    return b


def pick_representatives(d):
    reps = {}
    for bn in BINNAMES:
        sub = d[d.bin == bn]
        m = sub.full_minus_patch_mm.median()
        reps[bn] = sub.iloc[(sub.full_minus_patch_mm - m).abs().argsort()[:1]].iloc[0]
    return reps


def frame_geometry(traj, scan):
    return R.A.REG[traj]

def per_frame_patch_stats(fz, plab, traj, order, scan):
    cfg = R.A.REG[traj]
    z = np.load(os.path.join(cfg["scandir"], f"scan_{int(scan):04d}.npz"))
    P = z["aligned"].astype(np.float64); nn = z["nnidx"]
    model = fz["model"]; m_nom = model[nn]; resid = np.linalg.norm(P - m_nom, axis=1)
    lab = plab[nn]
    meta = pd.read_csv(cfg["meta"])
    mr = meta.iloc[int(order)]
    zr, zu = float(mr.range_m), np.array([float(mr.ux), float(mr.uy), float(mr.uz)])
    mu_full, _ = G_mu(fz, zr, zu)
    mu_patch = fz["mu_patch"]
    vis = np.unique(lab)
    # correction-direction consistency: mean pairwise cosine among visible-patch mu_full vectors
    v = mu_full[vis]; nv = np.linalg.norm(v, axis=1); keep = nv > 1e-9
    v = v[keep]
    if len(v) > 1:
        u = v / np.linalg.norm(v, axis=1, keepdims=True)
        cos = (u @ u.T); iu = np.triu_indices(len(u), 1)
        pair_cos = float(np.nanmean(cos[iu]))
    else:
        pair_cos = np.nan
    return dict(P=P, nn=nn, lab=lab, model=model, resid=resid, mu_patch=mu_patch, mu_full=mu_full,
                vis=vis, pair_cos=pair_cos, zr=zr, zu=zu)


def G_mu(fz, zr, zu):
    return R.G.mu_for_view(fz["Vmean"], fz["Vcnt"], fz["vrange"], fz["uview"], zr, zu, k=R.G.KSTAR)


def main():
    sup = pd.read_csv(SUP)
    sup = sup[sup.trajectory.isin(TRAJS)].copy()
    sup["bin"] = ""
    for tr, g in sup.groupby("trajectory", sort=False):
        sup.loc[g.index, "bin"] = bin_of(g.full_minus_patch_mm.values)
    # ---- bin-level diagnostic table (median of every descriptor)
    rows = []
    for tr in TRAJS:
        for bn in BINNAMES + ["middle"]:
            s = sup[(sup.trajectory == tr) & (sup.bin == bn)]
            r = dict(trajectory=tr, bin=bn, n=len(s))
            for c in DESC:
                r[c + "_med"] = float(s[c].median())
            rows.append(r)
    BIN = pd.DataFrame(rows)
    binp = os.path.join(OUT, "ii_failure_bin_diagnostics.csv"); BIN.to_csv(binp, index=False)

    # ---- deterministic representatives + per-frame patch stats
    fz = R.bundle(); plab = np.load(R.FROZEN_PATCHES)["lab"].astype(int)
    centers = np.load(R.FROZEN_PATCHES)["center"]
    rep_rows, geos = [], {}
    for tr in TRAJS:
        reps = pick_representatives(sup[sup.trajectory == tr])
        for bn, rr in reps.items():
            g = per_frame_patch_stats(fz, plab, tr, int(rr.order), int(rr.scan))
            geos[(tr, bn)] = g
            rep_rows.append(dict(trajectory=tr, bin=bn, order=int(rr.order), scan=int(rr.scan),
                                 effect_full_minus_patch_mm=float(rr.full_minus_patch_mm),
                                 nearest_d=float(rr.nearest_d), nearest_over_tau=float(rr.nearest_over_tau),
                                 ess_kernel=float(rr.ess_kernel), coverage=float(rr.coverage),
                                 n_fallback=int(rr.n_fallback), n_visible_patches=len(g["vis"]),
                                 correction_dir_pairwise_cos=g["pair_cos"],
                                 median_residual_mm=float(np.median(g["resid"]) * 1000)))
    REP = pd.DataFrame(rep_rows)
    repp = os.path.join(OUT, "ii_failure_representative_frames.csv"); REP.to_csv(repp, index=False)

    # ---- 2x3 diagnostic figure (Y-Z body plane; patch-colored matched points + correction quiver)
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    for i, tr in enumerate(TRAJS):
        for j, bn in enumerate(BINNAMES):
            ax = axes[i, j]; g = geos[(tr, bn)]; rr = REP[(REP.trajectory == tr) & (REP.bin == bn)].iloc[0]
            m = g["model"][g["nn"]]
            sc = ax.scatter(m[:, 1], m[:, 2], c=g["lab"], s=2, cmap="tab20", alpha=0.5)
            # patch correction vectors (mu_full) at visible patch centers, magnified x20 for visibility
            for pid in g["vis"]:
                c = centers[pid]; v = g["mu_full"][pid] * 20
                if np.linalg.norm(v) > 1e-9:
                    ax.quiver(c[1], c[2], v[1], v[2], angles="xy", scale_units="xy",
                              scale=1, color="crimson", width=0.003)
            ax.set_title(f"{tr} / {bn}\norder={rr.order} effect(F-P)={rr.effect_full_minus_patch_mm:.1f}mm\n"
                         f"nearest_d={rr.nearest_d:.2f} (x{rr.nearest_over_tau:.2f} tau) ESS={rr.ess_kernel:.1f} "
                         f"cov={rr.coverage:.2f} fb={rr.n_fallback}\nvisPatch={rr.n_visible_patches} "
                         f"corrDirCos={rr.correction_dir_pairwise_cos:.2f} residMed={rr.median_residual_mm:.0f}mm",
                         fontsize=8)
            ax.set_xlabel("body Y (m)"); ax.set_ylabel("body Z (m)"); ax.set_aspect("equal")
    fig.suptitle("IV-success vs II-transfer-failure representative frames (pre-registered quantile rule; "
                 "red arrows = Full per-patch correction x20)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    figp = os.path.join(OUT, "fig_II_vs_IV_representative_diagnostic.png")
    fig.savefig(figp, dpi=150); plt.close(fig)

    # ---- bin-level comparison figure: IV vs II descriptor profile
    desc_show = ["nearest_over_tau_med", "ess_kernel_med", "coverage_med", "n_fallback_med",
                 "corr_full_median_mm_med", "cos_pred_full_t_med"]
    fig2, axs = plt.subplots(2, 3, figsize=(15, 8))
    x = np.arange(3)
    for ax, c in zip(axs.ravel(), desc_show):
        iv = [BIN[(BIN.trajectory == "IV") & (BIN.bin == bn)][c].iloc[0] for bn in BINNAMES]
        ii = [BIN[(BIN.trajectory == "II") & (BIN.bin == bn)][c].iloc[0] for bn in BINNAMES]
        ax.plot(x, iv, "o-", label="IV (success transfer)"); ax.plot(x, ii, "s-", label="II (weak transfer)")
        ax.set_xticks(x); ax.set_xticklabels(BINNAMES); ax.set_title(c.replace("_med", ""), fontsize=9); ax.grid(alpha=.3)
        ax.legend(fontsize=7)
    fig2.suptitle("View-support diagnostics across Full-minus-Patch quantile bins")
    fig2.tight_layout(rect=[0, 0, 1, 0.96])
    fig2p = os.path.join(OUT, "fig_II_vs_IV_bin_diagnostics.png"); fig2.savefig(fig2p, dpi=150); plt.close(fig2)

    R.write_provenance(os.path.join(OUT, "ii_failure_provenance.json"), "P4-II-failure-diagnostic",
                       "python revision_experiments/_lib/p4_run.py",
                       config=dict(rule="best10/median+-5%/worst10 by full_minus_patch_mm; one rep=closest-to-bin-median",
                                   reps_per_traj=3, descriptors="existing replay79_support, no new model"),
                       seed=42, outputs={"bin_table": binp, "representatives": repp,
                                          "fig_representatives": figp, "fig_bins": fig2p},
                       note="Diagnostic only; no frame hand-picked; conclusion limited to transfer/view conditioning.")
    print(BIN.to_string(index=False)); print("\n", REP.to_string(index=False))


if __name__ == "__main__":
    main()
