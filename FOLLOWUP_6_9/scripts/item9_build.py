# -*- coding: utf-8 -*-
"""ITEM 9 -- View-support / Full-transfer diagnostic (consumes replay79_support.csv; no retraining).

Associations (NOT causal claims), stratified by trajectory:
  A. Full-Patch benefit vs nearest-view distance
  B. Full-Patch benefit vs kernel ESS
  C. Full-Patch benefit vs patch coverage
  D. translation direction cosine vs actual Full benefit
VI/IV/II/III = in-support primary scope; V = ALL frames (permanently out-of-support supportive set).
"""
import os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, os.path.dirname(__file__))
import f_common as F

OUT = F.OUT
TRAJ = ["VI", "IV", "II", "III", "V"]
S = pd.read_csv(os.path.join(OUT, "scripts", "replay79_support.csv"))
S = S[S.trajectory.isin(TRAJ)].copy()
cols = ["trajectory", "order", "scan", "block", "in_support", "range_m",
        "nearest_d", "k_min", "k_median", "k_max", "nearest_over_tau", "ess_kernel",
        "n_valid_patchobs", "coverage", "n_fallback",
        "corr_full_mean_mm", "corr_full_median_mm", "corr_patch_mean_mm",
        "pred_mag_t_mm", "cos_pred_raw_t", "cos_pred_full_t",
        "raw_et_mm", "patch_et_mm", "full_et_mm", "raw_eR_deg", "patch_eR_deg", "full_eR_deg",
        "full_minus_patch_mm", "full_minus_raw_mm"]
frame = S[cols].sort_values(["trajectory", "block", "order"]).reset_index(drop=True)
frame.to_csv(os.path.join(OUT, "followup9_view_support_frame.csv"), index=False)

# ---- block table ----
def blk_agg(q):
    return pd.Series(dict(n_frames=len(q),
        nearest_d=q.nearest_d.median(), nearest_over_tau=q.nearest_over_tau.median(),
        ess_kernel=q.ess_kernel.median(), coverage=q.coverage.median(),
        n_fallback=q.n_fallback.median(), corr_full_median_mm=q.corr_full_median_mm.median(),
        cos_pred_raw_t=q.cos_pred_raw_t.median(),
        raw_et_mm=q.raw_et_mm.median(), patch_et_mm=q.patch_et_mm.median(), full_et_mm=q.full_et_mm.median(),
        full_minus_patch_mm=q.full_minus_patch_mm.median(), full_minus_raw_mm=q.full_minus_raw_mm.median(),
        frac_full_beats_patch=(q.full_minus_patch_mm > 0).mean(),
        frac_fallback_any=(q.n_fallback > 0).mean()))
block = frame.groupby(["trajectory", "block"]).apply(blk_agg, include_groups=False).reset_index()
block.to_csv(os.path.join(OUT, "followup9_view_support_block.csv"), index=False)

# ---- trajectory summary + stratified correlations ----
sumrows, corrrows, binrows = [], [], []
for tr in TRAJ:
    q = frame[frame.trajectory == tr]
    sumrows.append(dict(section="trajectory", trajectory=tr, n=len(q), K=int(q.block.nunique()),
        nearest_d_med=q.nearest_d.median(), nearest_over_tau_med=q.nearest_over_tau.median(),
        ess_med=q.ess_kernel.median(), coverage_med=q.coverage.median(),
        fallback_rate=(q.n_fallback > 0).mean(), n_fallback_med=q.n_fallback.median(),
        cos_pred_raw_med=q.cos_pred_raw_t.median(), pred_mag_med=q.pred_mag_t_mm.median(),
        raw_et_med=q.raw_et_mm.median(), patch_et_med=q.patch_et_mm.median(), full_et_med=q.full_et_mm.median(),
        full_minus_patch_med=q.full_minus_patch_mm.median(), full_minus_raw_med=q.full_minus_raw_mm.median(),
        frac_full_beats_patch=(q.full_minus_patch_mm > 0).mean(),
        frac_full_beats_raw=(q.full_minus_raw_mm > 0).mean()))
    for tag, xcol in [("A_benefit_vs_nearest_d", "nearest_d"),
                      ("B_benefit_vs_ESS", "ess_kernel"),
                      ("C_benefit_vs_coverage", "coverage"),
                      ("D_cos_vs_full_benefit", "cos_pred_raw_t")]:
        x = q[xcol].values; y = q.full_minus_patch_mm.values
        m = np.isfinite(x) & np.isfinite(y)
        rho, p = spearmanr(x[m], y[m])
        corrrows.append(dict(section="corr", trajectory=tr, analysis=tag, n=int(m.sum()),
                             spearman_rho=float(rho), p_value=float(p)))
    # support tertiles by nearest_d/tau (pre-fixed: within-trajectory rank tertiles)
    qq = q.copy()
    ranks = qq.nearest_over_tau.rank(pct=True)
    qq["support_bin"] = np.where(ranks <= 1/3, "near", np.where(ranks <= 2/3, "mid", "far"))
    for bn, g in qq.groupby("support_bin"):
        binrows.append(dict(section="support_bin", trajectory=tr, support_bin=str(bn), n=len(g),
                            nearest_over_tau_lo=g.nearest_over_tau.min(),
                            nearest_over_tau_hi=g.nearest_over_tau.max(),
                            ess_med=g.ess_kernel.median(), coverage_med=g.coverage.median(),
                            cos_med=g.cos_pred_raw_t.median(),
                            full_minus_patch_med=g.full_minus_patch_mm.median(),
                            full_minus_raw_med=g.full_minus_raw_mm.median(),
                            frac_full_beats_patch=(g.full_minus_patch_mm > 0).mean(),
                            patch_et_med=g.patch_et_mm.median(), full_et_med=g.full_et_mm.median()))
summary = pd.concat([pd.DataFrame(sumrows), pd.DataFrame(corrrows), pd.DataFrame(binrows)], ignore_index=True)
summary.to_csv(os.path.join(OUT, "followup9_view_support_summary.csv"), index=False)

pd.set_option("display.width", 230)
print("=== trajectory summary ===")
print(pd.DataFrame(sumrows)[["trajectory", "n", "K", "nearest_over_tau_med", "ess_med", "coverage_med",
      "fallback_rate", "cos_pred_raw_med", "patch_et_med", "full_et_med", "full_minus_patch_med",
      "frac_full_beats_patch"]].round(3).to_string(index=False))
print("\n=== stratified Spearman (Full-Patch benefit) ===")
print(pd.DataFrame(corrrows).pivot_table(index="analysis", columns="trajectory", values="spearman_rho",
                                         aggfunc="first")[TRAJ].round(3).to_string())
print("\n=== support bins: Full-Patch median benefit / frac Full beats Patch ===")
bb = pd.DataFrame(binrows)
print(bb.assign(txt=lambda x: x.full_minus_patch_med.round(2).astype(str) + " / " +
                x.frac_full_beats_patch.round(2).astype(str))
      .pivot_table(index="support_bin", columns="trajectory", values="txt", aggfunc="first")[TRAJ].to_string())
print("[item9] wrote frame/block/summary")
