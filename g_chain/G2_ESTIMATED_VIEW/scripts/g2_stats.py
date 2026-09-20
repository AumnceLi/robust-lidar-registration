# -*- coding: utf-8 -*-
"""g2_stats.py -- oracle-vs-estimated gap + perturbation robustness; figures."""
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

import os, sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

RES = _pp("g_chain/G2_ESTIMATED_VIEW/results"); FIG = _pp("g_chain/G2_ESTIMATED_VIEW/figures")
os.makedirs(FIG, exist_ok=True); TRAJ = ["vi", "iv", "ii", "v"]; ARMS = ["T0_raw", "oracle", "est_gtstart", "est_warmstart"]

def subset_mask(df, t):
    if t in ("vi", "v"): return np.ones(len(df), bool)
    return df.in_support.values

def main():
    frames = []
    for t in TRAJ:
        p = os.path.join(RES, f"g2_{t}.csv")
        if os.path.exists(p):
            d = pd.read_csv(p); d = d[subset_mask(d, t)]; frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    rows = []
    for t in TRAJ:
        d = df[df.traj == t]
        if not len(d): continue
        pv = d.pivot_table(index="order", columns="arm", values=["et_mm", "eR_deg"])
        gap = d[d.arm == "view_gap"]
        et = {a: pv["et_mm"][a].values for a in ARMS}
        eR = {a: pv["eR_deg"][a].values for a in ARMS}
        def med(x): return float(np.nanmedian(x))
        # mitigation retention: (T0 - est)/(T0 - oracle)
        ret_g = (et["T0_raw"] - et["est_gtstart"]) / (et["T0_raw"] - et["oracle"] + 1e-9)
        ret_w = (et["T0_raw"] - et["est_warmstart"]) / (et["T0_raw"] - et["oracle"] + 1e-9)
        rows.append(dict(traj=t, n=len(pv),
                         et_T0=med(et["T0_raw"]), et_oracle=med(et["oracle"]),
                         et_est_gtstart=med(et["est_gtstart"]), et_est_warmstart=med(et["est_warmstart"]),
                         d_oracle_to_estGT=med(et["est_gtstart"] - et["oracle"]),
                         d_oracle_to_estWARM=med(et["est_warmstart"] - et["oracle"]),
                         retention_gtstart=med(ret_g), retention_warmstart=med(ret_w),
                         eR_T0=med(eR["T0_raw"]), eR_oracle=med(eR["oracle"]),
                         eR_est_warm=med(eR["est_warmstart"]),
                         view_angle_deg=med(gap.et_mm), range_gap_mm=med(gap.eR_deg),
                         corr_dir_cos=med(gap.corr_dir_cos), disp_dir_cos=med(gap.disp_dir_cos),
                         frac_est_better_than_T0=float(np.mean(et["est_warmstart"] < et["T0_raw"]))))
    ov = pd.DataFrame(rows); ov.to_csv(os.path.join(RES, "oracle_vs_estimated.csv"), index=False)

    # perturbation aggregation
    pf = [pd.read_csv(p) for p in sorted(glob.glob(os.path.join(RES, "g2_perturb_*.csv")))]
    if pf:
        P = pd.concat(pf, ignore_index=True)
        agg = P.groupby(["traj", "ptype", "magnitude"]).agg(
            et_med=("et_mm", "median"), eR_med=("eR_deg", "median"),
            dir_cos_med=("dir_cos", "median"), n=("scan", "nunique")).reset_index()
        agg.to_csv(os.path.join(RES, "perturbation_results.csv"), index=False)
    else:
        agg = None

    # ---- figures ----
    fig, ax = plt.subplots(figsize=(9.5, 4.6)); xs = np.arange(len(ov)); w = .2
    for k, a in enumerate(ARMS):
        ax.bar(xs + (k - 1.5) * w, ov[f"et_{a}" if a != "T0_raw" else "et_T0"], w, label=a)
    ax.set_xticks(xs); ax.set_xticklabels(ov.traj.str.upper()); ax.set_ylabel("median e_t [mm]")
    ax.set_title("G2: T0 raw vs oracle vs estimated-view pipeline"); ax.legend(fontsize=8); ax.grid(alpha=.25, axis="y")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "G2F1_arms.png"), dpi=140); plt.close()

    if agg is not None:
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.3))
        for ax, ptype, xlab in zip(axes, ["translation", "rotation", "combined"],
                                   ["perturbation [mm]", "perturbation [deg]", "combined t [mm]"]):
            for t in TRAJ:
                q = agg[(agg.traj == t) & (agg.ptype == ptype)].sort_values("magnitude")
                if len(q): ax.plot(q.magnitude, q.et_med, "-o", label=t.upper(), ms=4)
            # oracle reference (et_oracle) and T0
            for t in TRAJ:
                r = ov[ov.traj == t]
                if len(r):
                    ax.axhline(r.et_oracle.values[0], ls=":", lw=.7, color="0.7")
            ax.set_title(f"{ptype} sensitivity"); ax.set_xlabel(xlab); ax.set_ylabel("median corrected e_t [mm]")
            ax.grid(alpha=.25); ax.legend(fontsize=8)
        plt.tight_layout(); plt.savefig(os.path.join(FIG, "G2F2_perturbation.png"), dpi=140); plt.close()
    print("[g2_stats] done")
    print(ov.round(3).to_string(index=False))

if __name__ == "__main__":
    main()
