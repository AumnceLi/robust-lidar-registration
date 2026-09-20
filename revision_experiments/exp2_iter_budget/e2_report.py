# -*- coding: utf-8 -*-
"""Step 2c: summaries + figure for the iteration-budget experiment."""
import os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
TRAJS = ["VI", "IV", "II", "III"]; BUDGETS = [40, 80, 160]
COLORS = {"Raw": "#d62728", "Patch": "#1f77b4"}


def pivot_method(df, col):
    return df.pivot_table(index=["trajectory", "frame_id", "max_iterations"],
                          columns="method", values=col).reset_index()


def main():
    df = pd.read_csv(os.path.join(HERE, "iteration_budget_framewise.csv"))
    et = pivot_method(df, "translation_error_mm").rename(
        columns={"Raw": "raw_et", "Patch": "patch_et"})
    eR = pivot_method(df, "rotation_error_deg").rename(
        columns={"Raw": "raw_eR", "Patch": "patch_eR"})
    m = et.merge(eR)
    m["gain_et"] = m.raw_et - m.patch_et
    m["gain_eR"] = m.raw_eR - m.patch_eR

    srows = []
    for tr in TRAJS:
        g = m[m.trajectory == tr]
        for b in BUDGETS:
            gb = g[g.max_iterations == b]
            dfb = df[(df.trajectory == tr) & (df.max_iterations == b)]
            srows.append(dict(
                trajectory=tr, budget=b, n=len(gb),
                raw_et_median=gb.raw_et.median(), patch_et_median=gb.patch_et.median(),
                raw_eR_median=gb.raw_eR.median(), patch_eR_median=gb.patch_eR.median(),
                paired_gain_et_median=gb.gain_et.median(),
                patch_better_fraction=float((gb.gain_et > 0).mean()),
                raw_cap_fraction=float(dfb[dfb.method == "Raw"].hit_iteration_cap.mean()),
                patch_cap_fraction=float(dfb[dfb.method == "Patch"].hit_iteration_cap.mean()),
                raw_boundary_fraction=float(dfb[dfb.method == "Raw"]
                                            .eval("hit_translation_boundary+hit_rotation_boundary > 0").mean()),
                patch_boundary_fraction=float(dfb[dfb.method == "Patch"]
                                              .eval("hit_translation_boundary+hit_rotation_boundary > 0").mean()),
                raw_iters_median=dfb[dfb.method == "Raw"].actual_iterations.median(),
                patch_iters_median=dfb[dfb.method == "Patch"].actual_iterations.median()))
        # terminal pose changes & winner flips
        for lo, hi in [(40, 80), (80, 160), (40, 160)]:
            a = g[g.max_iterations == lo].set_index("frame_id")
            z = g[g.max_iterations == hi].set_index("frame_id").loc[a.index]
            flip = ((np.sign(a.gain_et) != np.sign(z.gain_et)) & (a.gain_et.abs() > 1e-9)
                    & (z.gain_et.abs() > 1e-9))
            srows.append(dict(trajectory=tr, budget=f"{lo}->{hi}", n=len(a),
                              raw_abs_dEt_median=(z.raw_et - a.raw_et).abs().median(),
                              patch_abs_dEt_median=(z.patch_et - a.patch_et).abs().median(),
                              raw_abs_dER_median=(z.raw_eR - a.raw_eR).abs().median(),
                              patch_abs_dER_median=(z.patch_eR - a.patch_eR).abs().median(),
                              winner_flip_fraction=float(flip.mean())))
    summ = pd.DataFrame(srows)
    summ.to_csv(os.path.join(HERE, "iteration_budget_summary.csv"), index=False)

    # --------------------------------------------------------------- figure
    hist = np.load(os.path.join(HERE, "_histories.npz"), allow_pickle=True)
    fig, AX = plt.subplots(4, 5, figsize=(23, 15))
    for r, tr in enumerate(TRAJS):
        g = m[m.trajectory == tr]
        # col1 et vs budget
        ax = AX[r, 0]
        for method, col in [("Raw", "raw_et"), ("Patch", "patch_et")]:
            pos = np.array(BUDGETS) + (8 if method == "Raw" else -8)
            data = [g[g.max_iterations == b][col].values for b in BUDGETS]
            bp = ax.boxplot(data, positions=pos, widths=14, patch_artist=True,
                            boxprops=dict(facecolor=COLORS[method], alpha=.3), showfliers=False)
            for j, b in enumerate(BUDGETS):
                xx = np.full(len(data[j]), pos[j]) + np.random.RandomState(j).normal(0, 2, len(data[j]))
                ax.scatter(xx, data[j], s=8, color=COLORS[method], alpha=.6)
        ax.set_xticks(BUDGETS); ax.set_xlim(20, 180)
        ax.set_title(f"{tr}: translation error vs budget"); ax.set_ylabel("et (mm)"); ax.grid(alpha=.3)
        if r == 0: ax.legend(["Raw", "Patch"])
        # col2 paired gain vs budget
        ax = AX[r, 1]
        gd = [g[g.max_iterations == b].gain_et.values for b in BUDGETS]
        ax.boxplot(gd, tick_labels=BUDGETS, showfliers=False)
        for j, b in enumerate(BUDGETS):
            ax.scatter(np.full(len(gd[j]), j + 1) + np.random.RandomState(j).normal(0, .05, len(gd[j])),
                       gd[j], s=8, alpha=.5, color="#2ca02c")
        ax.axhline(0, color="k", lw=1); ax.set_title(f"{tr}: Patch−Raw paired gain"); ax.grid(alpha=.3)
        ax.set_ylabel("gain (mm, >0 better)")
        # col3 objective vs iteration: median over frames STILL ACTIVE at iteration k
        ax = AX[r, 2]
        for method, cc in [("Raw", COLORS["Raw"]), ("Patch", COLORS["Patch"])]:
            curves = []
            for fid in g.frame_id.unique():
                h = hist[f"{tr}|{fid}|{method}|160"]
                J = np.asarray(h[0], float)
                if len(J): curves.append(J / J[0])
            xs, ys = [], []
            for k in range(160):
                vals = [c[k] for c in curves if len(c) > k]
                if len(vals) < 3:
                    break
                xs.append(k + 1); ys.append(np.median(vals))
            ax.plot(xs, ys, color=cc, label=method)
        for b in (40, 80): ax.axvline(b, color="grey", ls=":", lw=1)
        ax.set_yscale("log"); ax.set_title(f"{tr}: median objective/J0 (active frames)")
        ax.set_xlabel("iteration"); ax.grid(alpha=.3); ax.legend(fontsize=8)
        # col4 et vs iteration (active-frame median)
        ax = AX[r, 3]
        for method, cc in [("Raw", COLORS["Raw"]), ("Patch", COLORS["Patch"])]:
            curves = []
            for fid in g.frame_id.unique():
                h = hist[f"{tr}|{fid}|{method}|160"]
                etr = np.asarray(h[1], float)
                if len(etr): curves.append(etr)
            xs, ys = [], []
            for k in range(160):
                vals = [c[k] for c in curves if len(c) > k]
                if len(vals) < 3:
                    break
                xs.append(k + 1); ys.append(np.median(vals))
            ax.plot(xs, ys, color=cc, label=method)
        for b in (40, 80): ax.axvline(b, color="grey", ls=":", lw=1)
        ax.set_title(f"{tr}: median et (active frames)"); ax.set_xlabel("iteration"); ax.grid(alpha=.3)
        ax.legend(fontsize=8)
        # col5 terminal change bars
        ax = AX[r, 4]
        rows = summ[summ.trajectory == tr]
        labels = ["40→80", "80→160", "40→160"]
        keys = ["40->80", "80->160", "40->160"]
        x = np.arange(3); w = .35
        rawv = [rows[rows.budget == k].raw_abs_dEt_median.values[0] for k in keys]
        patv = [rows[rows.budget == k].patch_abs_dEt_median.values[0] for k in keys]
        ax.bar(x - w / 2, rawv, w, label="Raw", color=COLORS["Raw"], alpha=.7)
        ax.bar(x + w / 2, patv, w, label="Patch", color=COLORS["Patch"], alpha=.7)
        ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel("median |Δet| (mm)")
        ax.set_title(f"{tr}: terminal pose change"); ax.grid(alpha=.3, axis="y"); ax.legend(fontsize=8)
    fig.suptitle("Exp.2 iteration-budget sensitivity (Raw vs Patch; 40 fixed diagnostic frames/trajectory)", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(os.path.join(HERE, "fig_iteration_budget.png"), dpi=140)
    print(summ.to_string())
    # console gate diagnostics
    print("\nPaired median gain by budget:")
    piv = summ[summ.budget.isin(BUDGETS)].pivot_table(index="trajectory", columns="budget",
                                                      values="paired_gain_et_median")
    print(piv.to_string())
    print("\nPatch-better fraction by budget:")
    print(summ[summ.budget.isin(BUDGETS)].pivot_table(index="trajectory", columns="budget",
                                                      values="patch_better_fraction").to_string())


if __name__ == "__main__":
    main()
