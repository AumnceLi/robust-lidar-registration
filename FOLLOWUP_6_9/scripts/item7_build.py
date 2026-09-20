# -*- coding: utf-8 -*-
"""ITEM 7 -- Patch + robust-loss complementarity (consumes replay79_arms.csv; no new tuning)."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import f_common as F

OUT = F.OUT
ARMS = ["Raw", "Huber", "Trim", "Patch", "PatchHuber", "PatchTrim"]
LABEL = {"Raw": "Raw LS", "Huber": "Huber Raw", "Trim": "Trim Raw", "Patch": "Patch LS",
         "PatchHuber": "Patch+Huber", "PatchTrim": "Patch+Trim"}
TRAJ = ["VI", "IV", "II", "III"]
COMPS = [("PatchHuber", "Patch"), ("PatchHuber", "Huber"),
         ("PatchTrim", "Patch"), ("PatchTrim", "Trim")]

A = pd.read_csv(os.path.join(OUT, "scripts", "replay79_arms.csv"))
A = A[A.trajectory.isin(TRAJ) & A.arm.isin(ARMS)].copy()       # primary scope only (no V), all in-support
A["method"] = A.arm.map(LABEL)
frame = A[["trajectory", "order", "scan", "block", "in_support", "method", "arm",
           "et_mm", "eR_deg", "iters", "on_bound", "n_points", "wmean", "sumw",
           "ess_w", "keep_ratio", "n_retain"]].rename(columns=dict(
    et_mm="translation_error_mm", eR_deg="rotation_error_deg")).sort_values(
    ["trajectory", "block", "order", "arm"]).reset_index(drop=True)
frame.to_csv(os.path.join(OUT, "followup7_patch_robust_frame.csv"), index=False)

# ---- block medians ----
blk = frame.groupby(["trajectory", "method", "arm", "block"]).agg(
    n_frames=("order", "nunique"),
    median_translation_mm=("translation_error_mm", "median"),
    median_rotation_deg=("rotation_error_deg", "median")).reset_index()

# ---- per-block paired differences (benefit = comparator - target) ----
pair_block_rows, pair_sum_rows, marg_rows = [], [], []
for traj in TRAJ:
    d = A[A.trajectory == traj].copy()
    d["method"] = d["arm"]            # f_common pairs on column `method`; key by frozen arm id
    for m in ARMS:
        s = d[d.arm == m]
        tm, tlo, thi = F.block_boot_median_ci(s.et_mm, s.block, seed=42)
        rm, rlo, rhi = F.block_boot_median_ci(s.eR_deg, s.block, seed=43)
        marg_rows.append(dict(section="marginal", trajectory=traj, method=LABEL[m], arm=m,
                              n=len(s), K=int(s.block.nunique()),
                              t_median=tm, t_q25=s.et_mm.quantile(.25), t_q75=s.et_mm.quantile(.75),
                              t_ci_lo=tlo, t_ci_hi=thi, r_median=rm, r_q25=s.eR_deg.quantile(.25),
                              r_q75=s.eR_deg.quantile(.75), r_ci_lo=rlo, r_ci_hi=rhi,
                              med_iters=s.iters.median(), on_bound_rate=s.on_bound.mean(),
                              med_wmean=s.wmean.median(), med_ess_w=s.ess_w.median(),
                              med_keep=s.keep_ratio.median()))
    for tgt, cmp in COMPS:
        for axis, col, seed in [("translation", "et_mm", 42), ("rotation", "eR_deg", 43)]:
            r = F.block_paired_benefit(d, tgt, cmp, col, seed=seed)
            r.pop("block_benefits")
            pair_sum_rows.append(dict(section="paired", trajectory=traj,
                                      comparison=f"{LABEL[tgt]} vs {LABEL[cmp]}",
                                      target=tgt, comparator=cmp, axis=axis, **r))
            # per-block rows
            dd_t = d[d.arm == tgt][["order", "block", col]].rename(columns={col: "vt"})
            dd_c = d[d.arm == cmp][["order", "block", col]].rename(columns={col: "vc"})
            mm = dd_t.merge(dd_c, on=["order", "block"]); mm["ben"] = mm.vc - mm.vt
            for b, q in mm.groupby("block"):
                row = dict(table="paired", trajectory=traj, block=int(b),
                           method=f"{LABEL[tgt]} vs {LABEL[cmp]}", axis=axis, n_frames=len(q),
                           median_translation_mm=np.nan, median_rotation_deg=np.nan,
                           block_benefit=float(q.ben.median()))
                pair_block_rows.append(row)
blk_marg = blk[["trajectory", "method", "block", "n_frames", "median_translation_mm",
                "median_rotation_deg"]].copy()
blk_marg.insert(0, "table", "marginal"); blk_marg["axis"] = "both"; blk_marg["block_benefit"] = np.nan
block_out = pd.concat([blk_marg, pd.DataFrame(pair_block_rows)], ignore_index=True)
block_out.to_csv(os.path.join(OUT, "followup7_patch_robust_block.csv"), index=False)

summary = pd.concat([pd.DataFrame(marg_rows).assign(comparison="", axis="both", target="", comparator="",
                                                   k_improved=np.nan, K=np.nan),
                     pd.DataFrame(pair_sum_rows)], ignore_index=True)
summary.to_csv(os.path.join(OUT, "followup7_patch_robust_summary.csv"), index=False)

# digest
pd.set_option("display.width", 230)
mg = pd.DataFrame(marg_rows)
print("=== marginal medians (t / r) ===")
print(mg.assign(txt=lambda x: x.t_median.round(2).astype(str) + " / " + x.r_median.round(3).astype(str))
      .pivot_table(index="arm", columns="trajectory", values="txt", aggfunc="first")[TRAJ].to_string())
ps = pd.DataFrame(pair_sum_rows)
for axis in ["translation", "rotation"]:
    print(f"\n=== paired block benefit: {axis} (median [CI] k/K signp) ===")
    q = ps[ps.axis == axis]
    q["txt"] = [f"{r.median_block_benefit:7.3f} [{r.ci_lo:7.3f},{r.ci_hi:7.3f}] {int(r.k_improved)}/{int(r.K)} p={r.sign_p:.3f}"
                for _, r in q.iterrows()]
    print(q.pivot_table(index="comparison", columns="trajectory", values="txt", aggfunc="first")[TRAJ].to_string())
print("[item7] wrote frame/block/summary")
