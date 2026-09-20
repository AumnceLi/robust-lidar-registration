# -*- coding: utf-8 -*-
"""E1 combine + analyze.

Canonical framewise = REUSED L0(reference)+L1+L2+L3 bytes concatenated with the NEW L4/L5/L6 rows
(identical schema). Capture criteria are FIXED BEFORE this run (f3_common.capture_A / capture_B):
  * Capture-A (relative): final t-error < injected t-error AND final r-error < injected r-error.
  * Capture-B (threshold pass) : final pose within e_t \u2264 50 mm and e_R \u2264 2\u00b0;
                           an experimental threshold criterion, NOT a mission tolerance.
  * safeguard trigger   : frozen 0.30 m / 15 deg boundary clip (translation OR rotation boundary).
  * numerical failure   : non-finite final pose error.
  * solver-valid        : finite final pose AND no safeguard trigger (iteration cap is allowed).
Writes canonical framewise, aggregate summary, key-numbers JSON, and three per-trajectory figures.
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

import os, sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F

REUSED = os.path.join(F.ROOT, "revision_experiments", "final_targeted",
                      "initialization_sensitivity_framewise.csv")
METHOD_COLOR = {"Raw": "#1f77b4", "Patch": "#d62728", "Huber": "#9e9e9e", "PatchHuber": "#ffb26b"}
LV = F.LEVEL_ORDER
X = list(range(len(LV)))
XLAB = [f"{lv}\n{int(F.LEVELS[lv][0])}mm/{F.LEVELS[lv][1]:g}°" for lv in LV]


def standardize(df):
    df = df.copy()
    df["perturbation_level"] = df["perturbation_level"].replace({"reference": "L0"})
    fin_t, fin_r = df.final_translation_error_mm, df.final_rotation_error_deg
    df["safeguard"] = ((df.hit_translation_boundary == 1) | (df.hit_rotation_boundary == 1)).astype(int)
    df["numerical_failure"] = (~np.isfinite(fin_t) | ~np.isfinite(fin_r)).astype(int)
    df["solver_valid"] = ((df.numerical_failure == 0) & (df.safeguard == 0)).astype(int)
    df["capture_A"] = [F.capture_A(ti, ri, ft, fr) for ti, ri, ft, fr in
                       zip(df.translation_init_mm, df.rotation_init_deg, fin_t, fin_r)]
    df["capture_B"] = [F.capture_B(ft, fr) for ft, fr in zip(fin_t, fin_r)]
    return df


def main():
    old = standardize(pd.read_csv(REUSED))
    new = standardize(pd.read_csv(os.path.join(F.E1_OUT, "e1_coarse_L4L6_framewise.csv")))
    keep = ["trajectory","frame_id","method","perturbation_level","direction_id",
            "translation_init_mm","rotation_init_deg","final_translation_error_mm",
            "final_rotation_error_deg","iterations","termination_reason","hit_iteration_cap",
            "hit_translation_boundary","hit_rotation_boundary","final_objective",
            "ref_translation_error_mm","ref_rotation_error_deg","delta_init_t_mm","delta_init_r_deg",
            "posthoc","safeguard","numerical_failure","solver_valid","capture_A","capture_B"]
    fw = pd.concat([old[keep], new[keep]], ignore_index=True)
    # exact count assertions
    assert (fw.perturbation_level == "L0").sum() == 320
    for lv in LV[1:]:
        assert (fw.perturbation_level == lv).sum() == 1280, (lv, (fw.perturbation_level==lv).sum())
    assert len(fw) == 8000, len(fw)
    fw.to_csv(os.path.join(F.E1_OUT, "e1_coarse_init_framewise.csv"), index=False)

    # ------------------------------------------------------------ aggregate traj x method x level
    rows = []
    for (tr, m, lv), g in fw.groupby(["trajectory","method","perturbation_level"]):
        rows.append(dict(trajectory=tr, method=m, level=lv,
            n=len(g),
            et_med=float(g.final_translation_error_mm.median()),
            et_iqr=float(F.iqr(g.final_translation_error_mm)),
            et_p25=float(F.pct(g.final_translation_error_mm,25)),
            et_p75=float(F.pct(g.final_translation_error_mm,75)),
            eR_med=float(g.final_rotation_error_deg.median()),
            eR_iqr=float(F.iqr(g.final_rotation_error_deg)),
            captureA_rate=float(g.capture_A.mean()),
            captureB_rate=float(g.capture_B.mean()),
            safeguard_rate=float(g.safeguard.mean()),
            itercap_rate=float(g.hit_iteration_cap.mean()),
            numfail_rate=float(g.numerical_failure.mean()),
            solvervalid_rate=float(g.solver_valid.mean()),
            posthoc=int(tr=="III")))
    summ = pd.DataFrame(rows)
    # paired Patch-Raw / PH-Huber (pair by frame x direction)
    def paired(base, patched):
        out = {}
        for tr in F.TRAJS:
            for lv in LV:
                g = fw[(fw.trajectory==tr)&(fw.perturbation_level==lv)]
                w = g.pivot_table(index=["frame_id","direction_id"], columns="method",
                                  values="final_translation_error_mm")
                if base in w and patched in w:
                    d = (w[base]-w[patched]).dropna()
                    out[(tr,lv)] = (float(d.median()), float((d>0).mean()), int(d.shape[0]))
        return out
    pr = paired("Raw","Patch"); ph = paired("Huber","PatchHuber")
    summ["PatchRaw_gain_t_med"] = [pr.get((t,l),(np.nan,np.nan,np.nan))[0] for t,l in zip(summ.trajectory,summ.level)]
    summ["PatchRaw_frac_pos"]  = [pr.get((t,l),(np.nan,np.nan,np.nan))[1] for t,l in zip(summ.trajectory,summ.level)]
    summ["PHHuber_gain_t_med"] = [ph.get((t,l),(np.nan,np.nan,np.nan))[0] for t,l in zip(summ.trajectory,summ.level)]
    summ["PHHuber_frac_pos"]  = [ph.get((t,l),(np.nan,np.nan,np.nan))[1] for t,l in zip(summ.trajectory,summ.level)]
    summ["_li"] = summ.level.map({l: i for i, l in enumerate(LV)})
    summ = summ.sort_values(["trajectory","method","_li"]).drop(columns="_li").reset_index(drop=True)
    summ.to_csv(os.path.join(F.E1_OUT,"e1_coarse_init_summary.csv"), index=False)

    # ------------------------------------------------------------ figures (one panel per trajectory)
    def panel_grid(title, fname, draw, ylabel, sharey=True):
        fig, axes = plt.subplots(2, 2, figsize=(12, 8.4), sharex=True, sharey=sharey)
        for ax, tr in zip(axes.ravel(), F.TRAJS):
            draw(ax, tr)
            ax.set_xticks(X); ax.set_xticklabels([l.replace("\n","\n") for l in XLAB], fontsize=8)
            ax.set_title(tr + (" (post-hoc/secondary)" if tr=="III" else ""), fontsize=10)
            ax.grid(alpha=.25)
        axes[0,0].set_ylabel(ylabel); axes[1,0].set_ylabel(ylabel)
        fig.suptitle(title, fontsize=11); fig.tight_layout(rect=[0,0,1,0.96])
        fig.savefig(os.path.join(F.E1_OUT,fname), dpi=150); plt.close(fig)

    def draw_capB(ax, tr):
        for m in ["Huber","PatchHuber","Raw","Patch"]:
            s = summ[(summ.trajectory==tr)&(summ.method==m)].set_index("level").reindex(LV)
            lw = 2.4 if m in ("Raw","Patch") else 1.3
            ls = "-" if m in ("Raw","Patch") else "--"
            ms = 7 if m in ("Raw","Patch") else 4
            ax.plot(X, s.captureB_rate.values, ls, marker="o", color=METHOD_COLOR[m], lw=lw, ms=ms, label=m)
        ax.set_ylim(-0.03,1.03); ax.legend(fontsize=8, ncol=2, loc="best")
    panel_grid("Fig.E1-1  Fraction meeting error thresholds (e_t \u2264 50 mm, e_R \u2264 2\u00b0) by initialization level",
               "fig_e1_captureB.png", draw_capB, "Fraction meeting thresholds")

    def draw_et(ax, tr):
        for m in ["Huber","PatchHuber","Raw","Patch"]:
            s = summ[(summ.trajectory==tr)&(summ.method==m)].set_index("level").reindex(LV)
            lw = 2.4 if m in ("Raw","Patch") else 1.2
            ls = "-" if m in ("Raw","Patch") else "--"
            ax.plot(X, s.et_med.values, ls, marker="o", color=METHOD_COLOR[m], lw=lw,
                    ms=6 if m in ("Raw","Patch") else 3.5, label=m)
            if m in ("Raw","Patch"):
                ax.fill_between(X, s.et_p25.values, s.et_p75.values, color=METHOD_COLOR[m], alpha=.12)
        ax.set_yscale("log"); ax.legend(fontsize=8, ncol=2, loc="best")
    panel_grid("Fig.E1-2  Median final translation error (band = 25th\u201375th percentile for Raw/Patch) by initialization level",
               "fig_e1_median_et.png", draw_et, "Median final translation error (mm, log scale)", sharey=False)

    def draw_fail(ax, tr):
        for m in ["Raw","Patch"]:
            s = summ[(summ.trajectory==tr)&(summ.method==m)].set_index("level").reindex(LV)
            ax.plot(X, s.safeguard_rate.values, "-", marker="o", color=METHOD_COLOR[m], lw=2.2, ms=6,
                    label=f"{m}: safeguard clip")
        for m in ["Raw","Patch"]:
            s = summ[(summ.trajectory==tr)&(summ.method==m)].set_index("level").reindex(LV)
            ax.plot(X, s.numfail_rate.values, ":", marker="x", color=METHOD_COLOR[m], lw=1.4, ms=6,
                    label=f"{m}: numerical fail")
        ax.set_ylim(-0.03,1.03); ax.legend(fontsize=7.5, loc="best")
    panel_grid("Fig.E1-3  Path-safeguard trigger rate (solid) and numerical-failure rate (dotted)",
               "fig_e1_boundary_fail.png", draw_fail, "rate")

    # ------------------------------------------------------------ key numbers JSON
    key = {"levels": {l: F.LEVELS[l] for l in LV}, "capture_B_threshold": dict(t_mm=F.CAPTURE_B_T_MM, r_deg=F.CAPTURE_B_R_DEG)}
    pivB = summ.pivot_table(index=["trajectory","level"], columns="method", values="captureB_rate")
    pivS = summ.pivot_table(index=["trajectory","level"], columns="method", values="safeguard_rate")
    pivE = summ.pivot_table(index=["trajectory","level"], columns="method", values="et_med")
    key["captureB"] = {f"{t}|{l}": {"Raw": float(pivB.loc[(t,l),"Raw"]), "Patch": float(pivB.loc[(t,l),"Patch"])}
                       for t in F.TRAJS for l in LV}
    key["safeguard"] = {f"{t}|{l}": {"Raw": float(pivS.loc[(t,l),"Raw"]), "Patch": float(pivS.loc[(t,l),"Patch"])}
                        for t in F.TRAJS for l in LV}
    key["median_et"] = {f"{t}|{l}": {"Raw": float(pivE.loc[(t,l),"Raw"]), "Patch": float(pivE.loc[(t,l),"Patch"])}
                        for t in F.TRAJS for l in LV}
    # degradation onset: first level where Patch Capture-B drops >0.10 below Raw, or safeguard Patch-Raw >0.10
    onset = {}
    for t in F.TRAJS:
        on = None
        for l in LV[1:]:
            if (pivB.loc[(t,l),"Raw"]-pivB.loc[(t,l),"Patch"]) > 0.10 or \
               (pivS.loc[(t,l),"Patch"]-pivS.loc[(t,l),"Raw"]) > 0.10:
                on = l; break
        onset[t] = on
    key["patch_relative_degradation_onset"] = onset
    with open(os.path.join(F.E1_OUT,"e1_key_numbers.json"),"w") as f:
        json.dump(key, f, indent=2)

    # ------------------------------------------------------------ console digest
    print("=== Capture-B rate (Raw / Patch) by traj x level ===")
    print(pivB[["Raw","Patch"]].round(3).to_string())
    print("\n=== Safeguard-clip rate (Raw / Patch) ===")
    print(pivS[["Raw","Patch"]].round(3).to_string())
    print("\n=== Median final t error mm (Raw / Patch) ===")
    print(pivE[["Raw","Patch"]].round(2).to_string())
    print("\nPatch-relative degradation onset:", onset)
    print("\nwrote: e1_coarse_init_framewise.csv (8000), e1_coarse_init_summary.csv, 3 figures, e1_key_numbers.json")


if __name__ == "__main__":
    main()
