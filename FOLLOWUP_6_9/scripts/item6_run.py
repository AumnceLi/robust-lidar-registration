# -*- coding: utf-8 -*-
"""ITEM 6 -- Fair primary-method paired comparison (FROZEN; no re-run, no tuning).

Methods: Raw Huber Trim Global Patch Full ; trajectories VI IV II III ; axes translation/rotation.
A. marginal summaries: median, IQR, block-aware 95% CI (identical convention to frozen stage3).
B. paired BLOCK effects with benefit = comparator_error - target_error (>0 => target better).
   Comparisons: Patch vs {Raw,Huber,Trim,Global}; Full vs {Raw,Huber,Trim}.
Self-check: marginal medians/CIs must reproduce frozen master_summary.csv.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import f_common as F

mf = pd.read_csv(F.MASTER_FRAME)
mf = mf[mf.trajectory.isin(F.TRAJ6) & mf.method.isin(F.METHODS6)].copy()
mf["in_support"] = mf.in_support.astype(str)

# ---- frame-level output (full provenance) ----
frame = mf[["trajectory", "order", "scan", "method", "block", "in_support",
            "translation_error_mm", "rotation_error_deg"]].sort_values(
            ["trajectory", "block", "order", "method"]).reset_index(drop=True)
frame.to_csv(os.path.join(F.OUT, "followup6_primary_method_frame.csv"), index=False)

# ---- block-level output ----
block = frame.groupby(["trajectory", "method", "block"]).agg(
    n_frames=("order", "nunique"),
    translation_median_mm=("translation_error_mm", "median"),
    rotation_median_deg=("rotation_error_deg", "median")).reset_index()
block.to_csv(os.path.join(F.OUT, "followup6_primary_method_block.csv"), index=False)

# ---- A. marginal ----
marg_rows = []
for traj in F.TRAJ6:
    d = mf[mf.trajectory == traj]
    for m in F.METHODS6:
        s = d[d.method == m]
        tm, tlo, thi = F.block_boot_median_ci(s.translation_error_mm, s.block, seed=42)
        rm, rlo, rhi = F.block_boot_median_ci(s.rotation_error_deg, s.block, seed=43)
        marg_rows.append(dict(section="marginal", trajectory=traj, method=m, axis="translation",
                              n=len(s), K=int(s.block.nunique()), median=tm, q25=s.translation_error_mm.quantile(.25),
                              q75=s.translation_error_mm.quantile(.75), ci_lo=tlo, ci_hi=thi))
        marg_rows.append(dict(section="marginal", trajectory=traj, method=m, axis="rotation",
                              n=len(s), K=int(s.block.nunique()), median=rm, q25=s.rotation_error_deg.quantile(.25),
                              q75=s.rotation_error_deg.quantile(.75), ci_lo=rlo, ci_hi=rhi))

# ---- B. paired block effects (benefit = comparator - target) ----
COMPS = [("Patch", c) for c in ["Raw", "Huber", "Trim", "Global"]] + \
        [("Full", c) for c in ["Raw", "Huber", "Trim"]]
pair_rows = []
detail = {}
for traj in F.TRAJ6:
    d = mf[mf.trajectory == traj]
    for tgt, cmp in COMPS:
        for axis, col, seed in [("translation", "translation_error_mm", 42),
                                ("rotation", "rotation_error_deg", 43)]:
            r = F.block_paired_benefit(d, tgt, cmp, col, seed=seed)
            detail[(traj, tgt, cmp, axis)] = r.pop("block_benefits")
            pair_rows.append(dict(section="paired", trajectory=traj, method=f"{tgt}_vs_{cmp}",
                                  target=tgt, comparator=cmp, axis=axis, **r))
summary = pd.concat([pd.DataFrame(marg_rows), pd.DataFrame(pair_rows)], ignore_index=True)
summary.to_csv(os.path.join(F.OUT, "followup6_primary_method_summary.csv"), index=False)

# ---- self-check vs frozen master_summary ----
ms = pd.read_csv(os.path.join(F.ROOT, "POSE_AUDIT", "results", "master_summary.csv"))
mg = pd.DataFrame(marg_rows)
worst = 0.0
for _, r in mg.iterrows():
    ref = ms[(ms.trajectory == r["trajectory"]) & (ms.method == r["method"])].iloc[0]
    if r["axis"] == "translation":
        d = max(abs(r["median"] - ref.t_median), abs(r["ci_lo"] - ref.t_ci_lo), abs(r["ci_hi"] - ref.t_ci_hi))
    else:
        d = max(abs(r["median"] - ref.r_median), abs(r["ci_lo"] - ref.r_ci_lo), abs(r["ci_hi"] - ref.r_ci_hi))
    worst = max(worst, d)
print(f"[item6] self-check vs frozen master_summary: max|median/CI diff| = {worst:.3e}")

# console digest of the headline paired effects
piv = pd.DataFrame(pair_rows)
pd.set_option("display.width", 200)
for axis in ["translation", "rotation"]:
    print(f"\n===== {axis}: median block benefit (k/K, sign p) =====")
    q = piv[piv.axis == axis].copy()
    q["txt"] = [f"{r.median_block_benefit:7.3f} [{r.ci_lo:7.3f},{r.ci_hi:7.3f}] {int(r.k_improved)}/{int(r.K)} p={r.sign_p:.3f}"
                for _, r in q.iterrows()]
    print(q.pivot_table(index="method", columns="trajectory", values="txt", aggfunc="first")[F.TRAJ6].to_string())
np.savez(os.path.join(F.OUT, "scripts", "item6_block_benefits.npz"),
         **{f"{a}|{b}|{c}|{d}": v for (a, b, c, d), v in detail.items()})
print("\n[item6] wrote frame/block/summary csv")
