# -*- coding: utf-8 -*-
"""Exp.6 -- joint translation-rotation evaluation from EXISTING frozen per-frame results.

No registration is re-run. Source: FOLLOWUP_6_9 unified frozen replay (replay79_arms.csv), whose
Raw/Huber/Trim/Patch/PatchHuber arms are the frozen g_common.robust_icp outputs on the in-support
primary subset (VI all 501; IV/II/III in-support). III is post-hoc / secondary.

Comparisons: Patch vs Raw, Patch vs Huber, Patch vs Trim, PatchHuber vs Raw.
Per frame  dt = et(method)-et(base),  dr = eR(method)-eR(base)  (negative = better).
Four quadrants: TT/BB etc. -> (T better & R better), (T better & R worse),
(T worse & R better), (T worse & R worse). No mission-safety threshold is invented: no
pre-defined task tolerance exists in the repo, so no threshold-based analysis is performed.
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

import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))
REPLAY = _pp("FOLLOWUP_6_9/scripts/replay79_arms.csv")
TRAJS = ["VI", "IV", "II", "III"]
COMPS = [("Patch", "Raw"), ("Patch", "Huber"), ("Patch", "Trim"), ("PatchHuber", "Raw")]
QUADS = [("Tbetter_Rbetter", lambda dt, dr: (dt < 0) & (dr < 0)),
         ("Tbetter_Rworse", lambda dt, dr: (dt < 0) & (dr >= 0)),
         ("Tworse_Rbetter", lambda dt, dr: (dt >= 0) & (dr < 0)),
         ("Tworse_Rworse", lambda dt, dr: (dt >= 0) & (dr >= 0))]


def main():
    d = pd.read_csv(REPLAY)
    d = d[d.trajectory.isin(TRAJS)].copy()
    wide = d.pivot_table(index=["trajectory", "order"], columns="arm", values=["et_mm", "eR_deg"])
    rows = []; panels = {}
    for tgt, base in COMPS:
        cname = f"{tgt}_vs_{base}"
        for traj in TRAJS:
            sub_idx = wide.loc[traj]
            dt = (wide.loc[traj, ("et_mm", tgt)] - wide.loc[traj, ("et_mm", base)]).values
            dr = (wide.loc[traj, ("eR_deg", tgt)] - wide.loc[traj, ("eR_deg", base)]).values
            n = len(dt)
            panels[(cname, traj)] = (dt, dr)
            row = dict(comparison=cname, trajectory=traj, n=n,
                       dt_med=float(np.median(dt)), dr_med=float(np.median(dr)))
            for qname, fn in QUADS:
                row[f"{qname}_frac"] = float(fn(dt, dr).mean())
                row[f"{qname}_n"] = int(fn(dt, dr).sum())
            rows.append(row)
    q = pd.DataFrame(rows)
    q.to_csv(os.path.join(OUT, "translation_rotation_quadrants.csv"), index=False)
    showq = ["comparison", "trajectory", "n", "dt_med", "dr_med"] + [f"{x}_frac" for x, _ in QUADS]
    print(q[showq].round(3).to_string(index=False))

    # --------------------------------------------------------------- 4x4 paired scatter
    fig, axes = plt.subplots(len(COMPS), len(TRAJS), figsize=(15, 13), sharex=False, sharey=False)
    for i, (tgt, base) in enumerate(COMPS):
        cname = f"{tgt}_vs_{base}"
        for j, traj in enumerate(TRAJS):
            ax = axes[i, j]; dt, dr = panels[(cname, traj)]
            ax.scatter(dt, dr, s=7, alpha=0.35, color="#4C72B0", edgecolor="none")
            ax.axvline(0, color="k", lw=1); ax.axhline(0, color="k", lw=1)
            qq = q[(q.comparison == cname) & (q.trajectory == traj)].iloc[0]
            ax.set_title(f"{cname} | {traj}{' (post-hoc)' if traj=='III' else ''} n={qq.n}\n"
                         f"TT={qq.Tbetter_Rbetter_frac:.2f} Tbetter/Rworse={qq.Tbetter_Rworse_frac:.2f}",
                         fontsize=8.5)
            if i == len(COMPS) - 1: ax.set_xlabel("Δ translation (mm)  <0 better")
            if j == 0: ax.set_ylabel("Δ rotation (deg)  <0 better")
            ax.grid(alpha=.25)
    fig.suptitle("Exp.6 paired per-frame translation vs rotation change (x=Δt, y=Δr; "
                 "lower-left = both improve)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(os.path.join(OUT, "fig_translation_rotation.png"), dpi=140)
    print("[fig] fig_translation_rotation.png")

    # --------------------------------------------------------------- III call-out table
    iii = q[q.trajectory == "III"][showq]
    iii.to_csv(os.path.join(OUT, "iii_quadrant_callout.csv"), index=False)
    print("\n[III post-hoc call-out]\n", iii.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
