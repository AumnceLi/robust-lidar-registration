# -*- coding: utf-8 -*-
"""g1_stats.py -- aggregate ORACLE G1 mitigation: physical pose error is the primary outcome (not cosine).
Outputs all_pose_results / method_comparison / block_bootstrap / objective_vs_pose + figures."""
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

import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

RES = _pp("g_chain/G1_MITIGATION/results"); FIG = _pp("g_chain/G1_MITIGATION/figures")
os.makedirs(FIG, exist_ok=True)
TRAJ = ["vi", "iv", "ii", "v"]; METHODS = ["M0_raw_p2p", "M1_raw_p2l", "M2_raw_huber",
                                           "M3_global_corr", "M4_patch_corr", "M5_full_corr"]
SHORT = {"M0_raw_p2p": "M0 raw p2p", "M1_raw_p2l": "M1 raw p2l", "M2_raw_huber": "M2 robust",
         "M3_global_corr": "M3 global", "M4_patch_corr": "M4 patch", "M5_full_corr": "M5 full(oracle)"}
COLORS = {"M0_raw_p2p": "#d62728", "M1_raw_p2l": "#ff7f0e", "M2_raw_huber": "#9467bd",
          "M3_global_corr": "#8c564b", "M4_patch_corr": "#2ca02c", "M5_full_corr": "#1f77b4"}

def subset(df, traj):
    d = df[df.traj == traj]
    if traj == "vi": return d, "all(development)"
    if traj == "v":  return d, "all(out-of-support extrapolation)"
    return d[d.in_support], "in_support(primary)"

def main():
    df = pd.concat([pd.read_csv(os.path.join(RES, f"g1_oracle_{t}.csv")) for t in TRAJ
                    if os.path.exists(os.path.join(RES, f"g1_oracle_{t}.csv"))], ignore_index=True)
    df.to_csv(os.path.join(RES, "all_pose_results.csv"), index=False)
    comp, boot, ovp = [], [], []
    for traj in TRAJ:
        if traj not in set(df.traj): continue
        d, slab = subset(df, traj)
        base = d[d.method == "M0_raw_p2p"].set_index("order")
        for mth in METHODS:
            q = d[d.method == mth]
            et, eR = q.et_mm.values, q.eR_deg.values
            if len(et) == 0: continue
            bt = G.block_boot(et, np.median, B=2000, Ls=(5, 10, 20), seed=42)
            br = G.block_boot(eR, np.median, B=2000, Ls=(5, 10, 20), seed=43)
            row = dict(traj=traj, subset=slab, method=mth, n=len(q), et_med=float(np.median(et)),
                       et_q25=float(np.percentile(et, 25)), et_q75=float(np.percentile(et, 75)),
                       eR_med=float(np.median(eR)), g_corr_gt_med=float(q.g_corr_gt.median()),
                       et_L5lo=bt["L5_lo"], et_L5hi=bt["L5_hi"], eR_L5lo=br["L5_lo"], eR_L5hi=br["L5_hi"],
                       on_bound_pct=100 * q.on_bound.mean())
            if mth != "M0_raw_p2p":
                j = base.index.intersection(q.set_index("order").index)
                qq = q.set_index("order")
                det = base.loc[j, "et_mm"].values - qq.loc[j, "et_mm"].values     # >0 translation improves
                deR = base.loc[j, "eR_deg"].values - qq.loc[j, "eR_deg"].values    # >0 rotation improves
                obs, p = G.block_signflip_p(det, B=2000, L=5, seed=42)
                row.update(det_med=float(np.median(det)), frac_t_improved=float(np.mean(det > 0)),
                           deR_med=float(np.median(deR)), frac_R_improved=float(np.mean(deR > 0)),
                           signflip_p=p)
            comp.append(row)
            for L in (5, 10, 20):
                boot.append(dict(traj=traj, subset=slab, method=mth, block_L=L, stat="et",
                                 point=bt["point"], lo=bt[f"L{L}_lo"], hi=bt[f"L{L}_hi"]))
        # objective-vs-pose paired rows (vs M0): x = objective improvement, y = physical pose improvement
        qm = d.pivot_table(index="order", columns="method", values=["et_mm", "dJ_raw", "J_raw_final"])
        for mth in METHODS:
            tmp = pd.DataFrame({
                "traj": traj, "method": mth,
                "dJ_raw": qm[("dJ_raw", mth)].values,                      # how much raw objective lowered
                "det_vs_M0": qm[("et_mm", "M0_raw_p2p")].values - qm[("et_mm", mth)].values,
                "et": qm[("et_mm", mth)].values})
            ovp.append(tmp)
    pd.DataFrame(comp).to_csv(os.path.join(RES, "method_comparison.csv"), index=False)
    pd.DataFrame(boot).to_csv(os.path.join(RES, "block_bootstrap.csv"), index=False)
    pd.concat(ovp, ignore_index=True).to_csv(os.path.join(RES, "objective_vs_pose.csv"), index=False)

    # ---- figures ----
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.4), sharey=False)
    for ax, traj in zip(axes, TRAJ):
        if traj not in set(df.traj): ax.set_visible(False); continue
        d, _ = subset(df, traj)
        data = [d[d.method == m].et_mm.values for m in METHODS]
        bp = ax.boxplot(data, showfliers=False, widths=0.6,
                        boxprops=dict(color="#444"), medianprops=dict(color="black"))
        for i, m in enumerate(METHODS):
            ax.scatter(np.full(len(data[i]), i + 1), data[i], s=3, alpha=0.12, color=COLORS[m])
        ax.set_xticks(range(1, 7)); ax.set_xticklabels([s.split()[0] + s.split()[1][:3] for s in
                       [SHORT[m] for m in METHODS]], rotation=45, ha="right", fontsize=7)
        ax.set_title(f"{traj.upper()} e_t [mm]", fontsize=10); ax.grid(alpha=.25)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "G1F1_et_by_method.png"), dpi=140); plt.close()

    # paired improvement vs M0 with CI (M3/M4/M5 + M2)
    mc = pd.DataFrame(comp)
    fig, ax = plt.subplots(figsize=(10, 4.6))
    show = ["M2_raw_huber", "M3_global_corr", "M4_patch_corr", "M5_full_corr"]
    xs = np.arange(len(TRAJ)); w = 0.2
    for k, m in enumerate(show):
        det, lo, hi = [], [], []
        for t in TRAJ:
            r = mc[(mc.traj == t) & (mc.method == m)]
            if len(r):
                det.append(r.det_med.values[0]); lo.append(r.det_med.values[0]); hi.append(r.det_med.values[0])
            else: det.append(np.nan); lo.append(np.nan); hi.append(np.nan)
        ax.bar(xs + (k - 1.5) * w, det, w, label=SHORT[m], color=COLORS[m])
    ax.axhline(0, color="k", lw=.8); ax.set_xticks(xs); ax.set_xticklabels([t.upper() for t in TRAJ])
    ax.set_ylabel("median paired e_t(M0) - e_t(method) [mm]\n(>0 = physically closer to GT)")
    ax.set_title("G1 ORACLE: physical pose improvement vs raw p2p"); ax.legend(fontsize=8); ax.grid(alpha=.25, axis="y")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "G1F2_paired_improvement.png"), dpi=140); plt.close()

    # KEY inversion plot: x = raw-model objective at the method's final pose (common yardstick),
    # y = physical e_t. If lower J implied lower pose error all methods would line up; instead M0 reaches
    # the LOWEST raw J yet sits FARTHEST from GT, while M5 accepts a slightly larger raw residual to get closer.
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.6), sharey=False)
    showm = ["M0_raw_p2p", "M2_raw_huber", "M3_global_corr", "M4_patch_corr", "M5_full_corr"]
    for ax, traj in zip(axes, TRAJ):
        if traj not in set(df.traj): ax.set_visible(False); continue
        d, _ = subset(df, traj)
        cent = []
        for m in showm:
            q = d[d.method == m]
            ax.scatter(1000 * q.J_raw_final + np.random.default_rng(0).normal(0, 0.02, len(q)),
                       q.et_mm, s=4, alpha=0.10, color=COLORS[m])
            cent.append((1000 * q.J_raw_final.median(), q.et_mm.median(), m))
        cx = [c[0] for c in cent]; cy = [c[1] for c in cent]
        for k, (x, y, m) in enumerate(cent):
            ax.scatter(x, y, s=70, color=COLORS[m], edgecolor="k", zorder=5)
            ax.annotate(m.split("_")[0], (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8, fontweight="bold")
        ax.plot(cx, cy, "-", color="0.6", lw=.8, zorder=1)
        ax.set_xlabel("raw-model objective at final pose [x1e-3]"); ax.set_title(traj.upper())
        ax.grid(alpha=.25)
    axes[0].set_ylabel("physical e_t [mm]  (lower = closer to GT)")
    fig.suptitle("Lower geometric objective does NOT imply lower physical pose error (M0: lowest J, farthest from GT)")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "G1F3_objective_vs_pose.png"), dpi=140); plt.close()

    # translation vs rotation improvement (M4/M5) to show no rotation degradation
    fig, ax = plt.subplots(figsize=(6.6, 6))
    for m in ["M4_patch_corr", "M5_full_corr"]:
        r = mc[mc.method == m]
        ax.scatter(r.det_med, r.deR_med, s=45, label=SHORT[m], color=COLORS[m])
        for _, rr in r.iterrows(): ax.annotate(rr.traj.upper(), (rr.det_med, rr.deR_med), fontsize=8)
    ax.axhline(0, color="k", lw=.8); ax.axvline(0, color="k", lw=.8)
    ax.set_xlabel("median paired translation improvement [mm]"); ax.set_ylabel("median paired rotation improvement [deg]")
    ax.set_title("Translation gain must not cost rotation"); ax.legend(); ax.grid(alpha=.25)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "G1F4_t_vs_R.png"), dpi=140); plt.close()
    print("[g1_stats] done")

if __name__ == "__main__":
    main()
