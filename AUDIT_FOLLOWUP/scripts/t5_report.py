# -*- coding: utf-8 -*-
"""Generate mechanism_compensation_link.md from T5 outputs (numbers live from CSVs)."""
import os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, os.path.dirname(__file__))
import af_common as A

L0 = pd.read_csv(os.path.join(A.OUT, "mechanism_before_after.csv"))
SP = pd.read_csv(os.path.join(A.OUT, "scripts", "t5_block_spearman.csv"))
MD = pd.read_csv(os.path.join(A.OUT, "scripts", "t5_arm_medians.csv"))
VF = pd.read_csv(os.path.join(A.OUT, "scripts", "t5_analytic_vs_fd.csv"))
ORDER = ["VI", "IV", "II", "III", "V"]


def md(df, nd=4):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = [f"{r[c]:.{nd}f}" if isinstance(r[c], (float, np.floating)) else str(r[c]) for c in cols]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def frame_spearman(d, comp):
    ra = d[d.arm == "raw"].set_index("order"); co = d[d.arm == comp].set_index("order")
    j = ra.index.intersection(co.index)
    out = {}
    for m in ["rms_delta_mm", "gt_norm", "gr_norm", "pjw_delta_mm"]:
        r_, _ = spearmanr(co.loc[j, m].values - ra.loc[j, m].values,
                          co.loc[j, "et_mm"].values - ra.loc[j, "et_mm"].values)
        out[m + "_et"] = r_
    return out


def main():
    L = []
    L.append("# Pose-active mechanism -> compensation effectiveness link (P1 follow-up)\n")
    L.append("## 1. Identical-comparison design\n")
    L.append("For every frame and each target **Raw / Patch / Full**, all quantities are evaluated at the "
             "SAME reference pose (xi=0, GT-aligned), with the SAME frozen LS weights (w=1/N) and the SAME "
             "correspondence convention (GT-local k=1 nearest point of that arm's frozen target):\n")
    L.append("- **RMS(delta)** (mm): RMS pointwise mismatch delta_i = source_i - target(source_i).")
    L.append("- **||g_t||, ||g_r||**: translation / rotation block of the frozen objective gradient at "
             "xi=0 (reported in the frozen FD-of-mean-squared-residual convention, matching `__g`; the "
             "analytic Gauss-Newton normal is exactly one half of this -- see verification below).")
    L.append("- **||P_{J,W} delta||** (mm): weighted-RMS of the mismatch projected onto the pose-Jacobian "
             "column space, = sqrt(g' H^{-1} g) with the factor-1 normal equations; this is the part of "
             "mismatch a 6-DOF pose move can act on (its complement is pose-orthogonal structured error).")
    L.append("- Realized translation/rotation error is the unchanged frozen ICP result (M0/M4/M5), not "
             "re-solved here.\n")
    L.append("Patch = frozen 24-patch mean map; Full = frozen k=16 view+patch interpolation at the frame's "
             "true view (oracle view; the deployed predictor is outside this mechanism diagnostic). "
             "Primary scope = in-support frames (V analyzed on all frames, as shipped).\n")
    L.append("## 2. Primary-scope arm medians\n")
    MDx = MD.set_index("trajectory").loc[ORDER].reset_index()
    MDx.columns = ["traj", "arm", "n", "RMS(delta) mm", "||g_t||", "||g_r||",
                   "||P_JW delta|| mm", "trans err mm", "rot err deg"]
    L.append(md(MDx, 3))
    L.append("")
    L.append("## 3. Block-level coupling: change in mechanism vs change in pose error\n")
    L.append("Spearman rho across blocks between (arm - Raw) change in each mechanism quantity and the "
             "(arm - Raw) change in translation / rotation error. Positive rho = blocks where the mechanism "
             "quantity drops more also improve more.\n")
    show = SP.pivot_table(index=["trajectory", "comparison"], columns=["metric", "error"],
                          values="spearman_rho").round(3)
    show = show.reindex(ORDER, level=0)
    L.append("```")
    L.append(show.to_string())
    L.append("```")
    L.append("")
    # II Full focus
    ii_full = MD[(MD.trajectory == "II")].set_index("arm")
    ii_b = SP[(SP.trajectory == "II") & (SP.comparison == "raw_to_full")]
    L.append("## 4. Why Full does not improve II translation and worsens rotation (data statement)\n")
    g = lambda a, m: float(ii_full.loc[a, m])
    L.append(f"- On II, Raw -> Full changes median RMS(delta) {g('raw','rms_delta_mm'):.2f} -> "
             f"{g('full','rms_delta_mm'):.2f} mm, ||g_t|| {g('raw','gt_norm'):.4f} -> "
             f"{g('full','gt_norm'):.4f}, ||g_r|| {g('raw','gr_norm'):.4f} -> {g('full','gr_norm'):.4f}, "
             f"||P_JW delta|| {g('raw','pjw_delta_mm'):.2f} -> {g('full','pjw_delta_mm'):.2f} mm, "
             f"while realized translation error moves {g('raw','et_mm'):.2f} -> {g('full','et_mm'):.2f} mm "
             f"and rotation {g('raw','eR_deg'):.3f} -> {g('full','eR_deg'):.3f} deg.")
    L.append(f"- For comparison Raw -> Patch on II: RMS(delta) {g('raw','rms_delta_mm'):.2f} -> "
             f"{g('patch','rms_delta_mm'):.2f}, ||g_t|| {g('raw','gt_norm'):.4f} -> "
             f"{g('patch','gt_norm'):.4f}, ||g_r|| {g('raw','gr_norm'):.4f} -> "
             f"{g('patch','gr_norm'):.4f}, ||P_JW delta|| {g('raw','pjw_delta_mm'):.2f} -> "
             f"{g('patch','pjw_delta_mm'):.2f}, translation {g('raw','et_mm'):.2f} -> "
             f"{g('patch','et_mm'):.2f} mm, rotation {g('raw','eR_deg'):.3f} -> "
             f"{g('patch','eR_deg'):.3f} deg.")
    for em in ["et_mm", "eR_deg"]:
        q = ii_b[ii_b.error == em].set_index("metric").spearman_rho
        L.append(f"- block Spearman (Full-Raw) vs {em}: "
                 f"RMS(delta) {q.get('rms_delta_mm', np.nan):.3f}, ||g_t|| {q.get('gt_norm', np.nan):.3f}, "
                 f"||g_r|| {q.get('gr_norm', np.nan):.3f}, ||P_JW delta|| {q.get('pjw_delta_mm', np.nan):.3f}.")
    def rh(comp, metric, em):
        q = SP[(SP.trajectory == "II") & (SP.comparison == comp) &
               (SP.metric == metric) & (SP.error == em)].spearman_rho
        return float(q.iloc[0]) if len(q) else np.nan
    L.append("- Interpretation follows the data: on II the block-level correlation of (Full-Raw) "
             f"||g_t|| reduction with translation-error change is positive "
             f"(rho {rh('raw_to_full','gt_norm','et_mm'):.2f}) and "
             f"likewise for ||P_JW delta|| "
             f"(rho {rh('raw_to_full','pjw_delta_mm','et_mm'):.2f}) "
             "-- i.e. blocks where Full removes more pose-actionable signal do improve more -- yet at the "
             "AGGREGATE level Full still nets a slightly worse translation median and a worse rotation "
             "median. A weak II view map (neighbor views far from the VI support; interpolated field is an "
             "over-smoothed average) lowers the xi=0 gradient (including ||g_r||) everywhere by roughly "
             "the same amount without matching the true per-block bias; the realized local optimum "
             "nevertheless shifts to a worse rotation (a subtracted field need not be rotation-neutral at "
             "the optimum). RMS(delta) reduction is therefore neither necessary nor "
             "sufficient for pose benefit: the pose-actionable projection and its rotation block, not the "
             "raw mismatch size, track realized error, and the map must be spatially/view-specific enough "
             "for that coupling to convert into a level shift -- which Patch achieves on II but Full does "
             "not.")
    L.append("")
    L.append("## 5. Verification\n")
    L.append("- Analytic gradient vs the frozen central-difference `raw__g` (the analytic normal is 1/2 of "
             "the frozen mean-squared-objective FD gradient; accounted for):")
    L.append(md(VF.assign(max_abs_dgt=VF.max_abs_dgt.round(5), max_abs_dgr=VF.max_abs_dgr.round(5)), 5))
    L.append("- Residual differences are the O(h^2)=6.25e-4 (translation FD step) truncation error of the "
             "saved numeric gradient, as documented in Figure4 notes; the analytic values are exact at xi=0.")
    L.append("- Pose errors attached without re-solving, so they match the shipped frozen master results.")
    L.append("")
    L.append("## 6. Files\n")
    L.append("- `mechanism_before_after.csv` -- per-frame Raw/Patch/Full x p2p/p2l mechanism quantities + "
             "realized errors (block/in-support flags included).")
    L.append("- `scripts/t5_block_spearman.csv` -- full block-level Spearman table (rho, p, K).")
    L.append("- `scripts/t5_arm_medians.csv`, `scripts/t5_analytic_vs_fd.csv` -- summary/verification tables.")
    with open(os.path.join(A.OUT, "mechanism_compensation_link.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("[T5 report] wrote mechanism_compensation_link.md")


if __name__ == "__main__":
    main()
