# -*- coding: utf-8 -*-
"""TASK 1 -- DIRECT paired Patch vs Global-Vector increment (no registration re-run).

Scientific question: does the spatial Patch add value BEYOND the simplest historical state
correction (one fixed Global-Vector), measured by DIRECT per-frame pairing -- NOT by subtracting
two marginal (Patch-vs-Raw, Global-vs-Raw) medians.

  d_t = e_t(GlobalVector) - e_t(Patch)   ; positive => Patch has LOWER translation error.

Frame source : Exp.4 frozen dbs_vector_framewise.csv (columns globalvec_et_mm / patch_et_mm).
Block source : canonical master_pose_results_frame.csv (VI6/IV4/II9/III8), joined, never rebuilt.
Bootstrap    : stage3 block-unit convention (B=2000, resample paper blocks, seed=42, 2.5/97.5).
Paired p     : frozen g_common.block_signflip_p (one-sided, B=2000,L=5,seed42); no binomial sign test.
III          : post-hoc / secondary.
"""
import os
import numpy as np, pandas as pd
import ft_common as F

blok = F.paper_block_lookup()
e4 = pd.read_csv(F.E4)

# ------------------------------------------------------------ direct paired frame table
fr = e4[["trajectory", "order", "posthoc", "raw_et_mm", "globalvec_et_mm", "patch_et_mm"]].copy()
fr["block"] = [blok[(t, int(o))] for t, o in zip(fr.trajectory, fr.order)]
fr["d_t_mm"] = fr.globalvec_et_mm - fr.patch_et_mm          # >0  Patch better
fr["patch_better"] = fr.d_t_mm > 0
fr["global_better"] = fr.d_t_mm < 0
fr["tie"] = fr.d_t_mm == 0
fr = fr.sort_values(["trajectory", "order"]).reset_index(drop=True)
assert fr.block.notna().all()
fr.to_csv(os.path.join(F.OUT, "patch_vs_global_framewise.csv"), index=False)

# ------------------------------------------------------------ per-block direct paired effects
brows = []
for traj in F.TRAJS:
    g = fr[fr.trajectory == traj]
    for b, q in g.groupby("block"):
        brows.append(dict(trajectory=traj, block=int(b), n=len(q),
                          globalvec_et_med=q.globalvec_et_mm.median(),
                          patch_et_med=q.patch_et_mm.median(),
                          block_d_t_med=float(q.d_t_mm.median()),
                          block_patch_better_frac=float((q.d_t_mm > 0).mean()),
                          posthoc=int(traj in F.POSTHOC)))
bdf = pd.DataFrame(brows).sort_values(["trajectory", "block"]).reset_index(drop=True)
bdf.to_csv(os.path.join(F.OUT, "patch_vs_global_blocks.csv"), index=False)

# ------------------------------------------------------------ trajectory summary
srows = []
for traj in F.TRAJS:
    g = fr[fr.trajectory == traj]
    d = g.d_t_mm.values
    q25, q75, iqr = F.iqr_parts(d)
    bp = F.block_paired(d, g.block.values)
    boot = F.block_boot_med(d, g.block.values, B=2000, seed=42)
    obs, p = F.block_signflip_p(d, B=2000, L=5, seed=42)
    srows.append(dict(
        trajectory=traj, posthoc=int(traj in F.POSTHOC), n=len(g),
        globalvec_et_med=float(g.globalvec_et_mm.median()),
        patch_et_med=float(g.patch_et_mm.median()),
        marginal_med_gap_patch_minus_global=float(g.patch_et_mm.median() - g.globalvec_et_mm.median()),
        paired_d_t_med=float(np.median(d)), paired_d_t_q25=q25, paired_d_t_q75=q75, paired_d_t_iqr=iqr,
        patch_better_frac=float((d > 0).mean()), global_better_frac=float((d < 0).mean()),
        tie_frac=float((d == 0).mean()),
        n_blocks=bp["n_blocks"], median_block_effect=bp["median_block_effect"],
        block_boot_point=boot["point"], block_boot_lo=boot["lo"], block_boot_hi=boot["hi"],
        block_ci_crosses_zero=bool(boot["lo"] <= 0.0 <= boot["hi"]),
        blocks_positive=bp["pos"], blocks_negative=bp["neg"], blocks_zero=bp["zero"],
        signflip_p_one_sided=p))
summ = pd.DataFrame(srows)
summ.to_csv(os.path.join(F.OUT, "patch_vs_global_summary.csv"), index=False)

show = summ[["trajectory", "n", "globalvec_et_med", "patch_et_med", "paired_d_t_med",
             "paired_d_t_iqr", "patch_better_frac", "global_better_frac", "n_blocks",
             "median_block_effect", "block_boot_lo", "block_boot_hi",
             "blocks_positive", "blocks_negative", "signflip_p_one_sided"]]
print(show.round(3).to_string(index=False))

# sanity: block counts must be 6/4/9/8
counts = summ.set_index("trajectory").n_blocks.to_dict()
assert counts == {"VI": 6, "IV": 4, "II": 9, "III": 8}, counts
print("\nblock-count check 6/4/9/8 OK:", counts)
print("\nII marginal gap vs DIRECT paired median:")
r2 = summ.set_index("trajectory").loc["II"]
print(f"  marginal (median Patch - median Global) = {r2.marginal_med_gap_patch_minus_global:+.3f} mm")
print(f"  DIRECT paired median d_t                = {r2.paired_d_t_med:+.3f} mm")

# ------------------------------------------------------------ decision note (numbers pulled from CSV)
S = summ.set_index("trajectory")
def row(t): return S.loc[t]
L = []
L.append("# Task 1 — Direct paired Patch vs Global-Vector increment\n")
L.append("**Verdict: `SPATIAL_INCREMENT_TRAJECTORY_DEPENDENT`.**\n")
L.append("## Method (what makes this direct)\n")
L.append("Per matched frame we pair the two frozen Exp.4 arms and form "
         "**d_t = e_t(GlobalVector) − e_t(Patch)** (positive = Patch has lower translation error). "
         "We do **not** subtract a Patch-vs-Raw marginal median from a Global-vs-Raw marginal median "
         "(that operation is invalid for an incremental claim). Frame values come from the frozen "
         "`exp4/dbs_vector_framewise.csv`; no registration was re-run. Blocks are JOINED from the "
         "canonical paper map `master_pose_results_frame.csv` (VI 6 / IV 4 / II 9 / III 8) and were not "
         "reconstructed. The block CI uses the manuscript block-unit convention (resample paper blocks "
         "with replacement, pool member frames, median; B=2000, seed 42, 2.5/97.5 percentiles). The "
         "paired p is the frozen one-sided block sign-flip permutation "
         "(`g_common.block_signflip_p`, B=2000, L=5, seed 42); a classical binomial sign test is **not** "
         "part of the frozen convention, so none was added. **III is post-hoc / secondary.**\n")
L.append("## Direct paired result by trajectory\n")
tb = summ[["trajectory", "n", "paired_d_t_med", "paired_d_t_iqr", "patch_better_frac",
           "global_better_frac", "tie_frac", "n_blocks", "median_block_effect",
           "block_boot_lo", "block_boot_hi", "blocks_positive", "blocks_negative",
           "signflip_p_one_sided"]].copy()
tb.columns = ["traj", "n", "med d_t", "IQR", "P(better)", "G(better)", "ties", "blocks",
              "med block eff", "CI lo", "CI hi", "blk+", "blk−", "signflip p"]
L.append(tb.round(3).to_markdown(index=False) + "\n")
L.append("## The II contrast that motivated this task (marginal vs direct)\n")
L.append(f"On II the two MARGINAL medians make Patch look clearly better "
         f"(median Patch − median Global = {row('II').marginal_med_gap_patch_minus_global:+.2f} mm). "
         f"The DIRECT paired result is essentially zero: median d_t = {row('II').paired_d_t_med:+.2f} mm, "
         f"Patch-better fraction {row('II').patch_better_frac:.3f} vs Global-better "
         f"{row('II').global_better_frac:.3f} (an even split), per-block effects split "
         f"{int(row('II').blocks_positive)} positive / {int(row('II').blocks_negative)} negative, the block "
         f"CI [{row('II').block_boot_lo:+.2f}, {row('II').block_boot_hi:+.2f}] CROSSES ZERO, and the "
         f"sign-flip p = {row('II').signflip_p_one_sided:.3f}. On II, Patch therefore provides no "
         "demonstrable increment over the single constant historical vector.\n")
L.append("## Trajectory-by-trajectory reading\n")
for t, tag in [("VI", ""), ("IV", ""), ("II", ""), ("III", " (post-hoc / secondary)")]:
    r = row(t)
    L.append(f"- **{t}{tag}**: median d_t {r.paired_d_t_med:+.2f} mm (IQR {r.paired_d_t_iqr:.2f}), "
             f"Patch-better {r.patch_better_frac:.3f}, blocks {int(r.blocks_positive)}/"
             f"{int(r.n_blocks)} positive, block CI [{r.block_boot_lo:+.2f}, {r.block_boot_hi:+.2f}]"
             f"{' (crosses 0)' if r.block_ci_crosses_zero else ' (excludes 0)'}, "
             f"sign-flip p {r.signflip_p_one_sided:.4f}.")
L.append("")
L.append("## Decision\n")
L.append("Direct Patch-vs-Global evidence is clearly positive on **VI / IV** and on the post-hoc "
         "**III**, but on **II** it is weak and the block bootstrap interval crosses zero. Hence the "
         "increment of the spatial Patch over the simplest historical correction is **trajectory "
         "dependent**. The stronger sentence *“Patch clearly outperforms simple historical correction "
         "on all four trajectories”* is **not supported by the direct paired evidence and must not be "
         "retained**. State the spatial increment as robust on VI/IV (and the secondary III) and "
         "null/uncertain on II, where a single constant historical vector is already as good at the "
         "median once frames are paired.\n")
open(os.path.join(F.OUT, "patch_vs_global_decision.md"), "w", encoding="utf-8").write("\n".join(L))
print("[wrote] patch_vs_global_decision.md")
