# -*- coding: utf-8 -*-
"""build_outputs.py -- aggregate all revision experiments into revision_summary.csv + figures.
Reads only the saved per-experiment outputs (no new registration)."""
import os, sys, glob
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import revx_common as R

REV = R.REV
FIG = os.path.join(REV, "figures"); TAB = os.path.join(REV, "tables")
os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)
TR = R.TRAJS; COLORS = {"VI": "#1f77b4", "IV": "#2ca02c", "II": "#d62728", "III": "#9467bd"}


def load(exp):
    return pd.read_csv(os.path.join(REV, exp, f"{exp}_summary.csv"))


# --------------------------------------------------------------- 1. revision_summary.csv
def build_summary():
    rows = []
    # P1 sweeps: comparator = Raw
    meta = {"01_patch_count": ("patch_count", 42), "02_normal_weight": ("normal_weight", 42),
            "03_seed_sensitivity": ("clustering_seed", None)}
    for exp, (axis, fixed_seed) in meta.items():
        d = load(exp)
        for r in d.itertuples():
            rows.append(dict(experiment=exp, trajectory=r.trajectory,
                             configuration=f"{axis}={getattr(r, axis)}",
                             translation_median_mm=r.patch_translation_median_mm,
                             rotation_median_deg=r.patch_rotation_median_deg,
                             paired_translation_effect_mm=r.paired_translation_benefit_mm,
                             paired_rotation_effect_deg=r.paired_rotation_change_deg,
                             n_frames=r.n_frames, n_blocks=r.n_blocks,
                             seed=getattr(r, axis) if exp == "03_seed_sensitivity" else 42))
    # P2-A: comparator = Huber
    p2a = pd.read_csv(os.path.join(REV, "04_normal_recompute", "normal_recompute_summary.csv"))
    for r in p2a.itertuples():
        rows.append(dict(experiment=f"P2A_normal_recompute_{r.channel}", trajectory=r.trajectory,
                         configuration=r.arm, translation_median_mm=r.translation_median_mm,
                         rotation_median_deg=r.rotation_median_deg,
                         paired_translation_effect_mm=r.paired_translation_effect_vs_Huber_mm,
                         paired_rotation_effect_deg=r.paired_rotation_effect_vs_Huber_deg,
                         n_frames=r.n_frames, n_blocks=np.nan, seed=42))
    # P2-B if present
    p2bp = os.path.join(REV, "04_normal_recompute", "boundary_smoothing_summary.csv")
    if os.path.exists(p2bp):
        for r in pd.read_csv(p2bp).itertuples():
            rows.append(dict(experiment=f"P2B_boundary_smoothing_{r.channel}", trajectory=r.trajectory,
                             configuration=r.arm, translation_median_mm=r.translation_median_mm,
                             rotation_median_deg=r.rotation_median_deg,
                             paired_translation_effect_mm=r.paired_translation_effect_vs_Huber_mm,
                             paired_rotation_effect_deg=r.paired_rotation_effect_vs_Huber_deg,
                             n_frames=r.n_frames, n_blocks=np.nan, seed=42))
    # P3: block size
    p3 = pd.read_csv(os.path.join(REV, "05_block_sensitivity", "block_size_summary.csv"))
    for r in p3.itertuples():
        rows.append(dict(experiment=f"P3_blocksize_{r.comparison}", trajectory=r.trajectory,
                         configuration=f"block={r.block_size}", translation_median_mm=np.nan,
                         rotation_median_deg=np.nan, paired_translation_effect_mm=r.median_paired_effect,
                         paired_rotation_effect_deg=np.nan, n_frames=np.nan, n_blocks=r.n_blocks, seed=42))
    df = pd.DataFrame(rows)
    out = os.path.join(REV, "revision_summary.csv"); df.to_csv(out, index=False)
    df.to_csv(os.path.join(TAB, "revision_summary.csv"), index=False)
    return df


# --------------------------------------------------------------- 2. parameter sensitivity overview
def fig_sensitivity():
    specs = [("01_patch_count", "patch_count", [12, 18, 24, 32, 48], "Patch count K", 24),
             ("02_normal_weight", "normal_weight", [0.0, 0.15, 0.30, 0.60, 1.00], "Normal feature weight w", 0.30),
             ("03_seed_sensitivity", "clustering_seed", [0, 1, 2, 42, 20240910], "Clustering seed", 42)]
    fig, axes = plt.subplots(3, 2, figsize=(13, 12), sharex=False)
    for i, (exp, axis, grid, xlab, anchor) in enumerate(specs):
        d = load(exp)
        xpos = np.arange(len(grid))
        for tr in TR:
            dd = d[d.trajectory == tr].set_index(axis).reindex(grid)
            axes[i, 0].plot(xpos, dd.paired_translation_benefit_mm, "o-", color=COLORS[tr], label=tr)
            axes[i, 1].plot(xpos, dd.paired_rotation_change_deg, "o-", color=COLORS[tr], label=tr)
        ai = grid.index(anchor)
        for j, (yl, ttl) in enumerate([("Paired translation benefit (mm)\nRaw - Patch (>0 = Patch better)",
                                         f"{xlab}: translation benefit"),
                                        ("Paired rotation change (deg)\nPatch - Raw",
                                         f"{xlab}: rotation change")]):
            ax = axes[i, j]; ax.axhline(0, color="k", lw=.8); ax.axvline(ai, color="grey", ls="--", lw=.8)
            ax.set_xticks(xpos); ax.set_xticklabels([str(g) for g in grid], rotation=30)
            ax.set_title(ttl, fontsize=10); ax.grid(alpha=.3); ax.legend(fontsize=8)
    fig.suptitle("Patch hyperparameter stability (frozen anchor 24 / w=0.30 / seed42 marked) — "
                 "no parameter is re-selected", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    p = os.path.join(FIG, "fig_parameter_sensitivity_overview.png"); fig.savefig(p, dpi=150); plt.close(fig)
    return p


# --------------------------------------------------------------- 3. rotation ablation figure
def fig_rotation():
    p2a = pd.read_csv(os.path.join(REV, "04_normal_recompute", "normal_recompute_summary.csv"))
    p2bp = os.path.join(REV, "04_normal_recompute", "boundary_smoothing_summary.csv")
    arms = ["Huber", "PatchHuber", "PatchReNormalHuber"]
    labels = ["Huber", "Patch+Huber", "Patch-ReNormal+Huber"]
    colors = ["#7f7f7f", "#d62728", "#1f77b4"]
    if os.path.exists(p2bp):
        arms += ["PatchSmoothHuber"]; labels += ["Patch-Smooth+Huber"]; colors += ["#ff7f0e"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    for ci, ch in enumerate(["p2p", "p2l"]):
        dd = p2a[p2a.channel == ch]
        if os.path.exists(p2bp):
            dd = pd.concat([dd, pd.read_csv(p2bp)[lambda x: x.channel == ch]])
        x = np.arange(len(TR)); w = 0.2
        for k, (arm, lab, col) in enumerate(zip(arms, labels, colors)):
            a = dd[dd.arm == arm].set_index("trajectory").reindex(TR)
            axes[0, ci].bar(x + (k - 1.5) * w, a.paired_rotation_effect_vs_Huber_deg, w, label=lab, color=col)
            axes[1, ci].bar(x + (k - 1.5) * w, a.paired_translation_effect_vs_Huber_mm, w, label=lab, color=col)
        axes[0, ci].axhline(0, color="k", lw=.8); axes[1, ci].axhline(0, color="k", lw=.8)
        axes[0, ci].set_title(f"{ch.upper()}: paired rotation change vs Huber (deg)", fontsize=10)
        axes[1, ci].set_title(f"{ch.upper()}: paired translation gain vs Huber (mm)", fontsize=10)
        for r in range(2):
            axes[r, ci].set_xticks(x); axes[r, ci].set_xticklabels(TR); axes[r, ci].grid(alpha=.3, axis="y")
            axes[r, ci].legend(fontsize=8)
    fig.suptitle("Rotation-penalty ablation. p2p = paper primary (normals unused -> ReNormal is bit-identical); "
                 "p2l = only channel consuming normals", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    p = os.path.join(FIG, "fig_rotation_ablation.png"); fig.savefig(p, dpi=150); plt.close(fig)
    return p


# --------------------------------------------------------------- 4. block-size figure
def fig_blocksize():
    d = pd.read_csv(os.path.join(REV, "05_block_sensitivity", "block_size_summary.csv"))
    ext = d[d.trajectory.isin(["IV", "II", "III"])].copy()
    ext["L"] = ext.block_size.astype(int)
    comps = ["Patch_vs_Raw", "PatchHuber_vs_Huber", "Patch_vs_Global"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=False)
    for ax, comp in zip(axes, comps):
        c = ext[ext.comparison == comp]
        for tr in ["IV", "II", "III"]:
            cc = c[c.trajectory == tr].sort_values("L")
            ax.errorbar(cc.L, cc.median_block_effect,
                        yerr=[cc.median_block_effect - cc.ci_lo, cc.ci_hi - cc.median_block_effect],
                        marker="o", capsize=3, color=COLORS[tr], label=tr)
            ax.plot(cc.L, cc.median_paired_effect, ":", color=COLORS[tr], alpha=.6)
        ax.axhline(0, color="k", lw=.8); ax.set_title(comp.replace("_", " "), fontsize=10)
        ax.set_xlabel("external block size (frames)"); ax.set_ylabel("block effect (mm)"); ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    fig.suptitle("Block-size sensitivity (solid=median block effect w/ 95% block-bootstrap CI; "
                 "dotted=frame-paired median, invariant to L)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    p = os.path.join(FIG, "fig_block_size_sensitivity.png"); fig.savefig(p, dpi=150); plt.close(fig)
    return p


def main():
    s = build_summary(); print("[summary] rows", len(s))
    print("[fig]", fig_sensitivity()); print("[fig]", fig_rotation()); print("[fig]", fig_blocksize())


if __name__ == "__main__":
    main()
