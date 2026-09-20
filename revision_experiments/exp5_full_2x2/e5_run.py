# -*- coding: utf-8 -*-
"""Exp.5 -- minimal 2x2 ablation of the current Full (FROZEN; no new Full, no retuning).

Decomposes the two factors that change SIMULTANEOUSLY between current Patch and current Full:
  factor view : all-history  vs  k=16 adaptive-Gaussian view-neighbor
  factor weight: point-weighted (Vcnt) vs scan-weighted (each scan one equal vote)

  A1 = current Patch : all-history + point-weighted  (== frozen mu_patch; must reproduce g1 M4)
  A2                 : all-history + scan-weighted
  B1                 : view-neighbor + point-weighted
  B2 = current Full  : view-neighbor + scan-weighted (== frozen mu_for_view; must reproduce g1 M5)

patch count (24), k (16), kernel (adaptive Gaussian), range_std, support mask, history library,
solver, basin, tol are ALL frozen. Runs on the COMMON in-support mask of VI/IV/II/III. Mechanism
ablation only -- no method is re-selected on III (post-hoc / secondary).
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

import os, sys, time
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1"); os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rev_common as Rv
G = Rv.G

OUT = os.path.dirname(os.path.abspath(__file__))
REPLAY = _pp("FOLLOWUP_6_9/scripts/replay79_arms.csv")
LEVELS = ["A1_patch", "A2_allhist_scanw", "B1_view_pointw", "B2_full"]


def views(traj, lib):
    if traj == "VI":
        return lib["vrange"], lib["uview"]
    m = Rv.meta_frame(traj)
    return m["range_m"].values.astype(float), m[["ux", "uy", "uz"]].values.astype(float)


def run_field(target, tree, fz, P):
    r = G.robust_icp(target, fz["normals"], tree, P, "p2p", "ls", s_floor=fz["s_floor"])
    xi = r["xi"]
    return (np.linalg.norm(xi[:3]) * 1000.0, np.degrees(np.linalg.norm(xi[3:])),
            int(r["iters"]), int(r["on_bound"]))


def main():
    fz = Rv.frozen_bundle(); lib = Rv.predictor_library(fz)
    Vmean, Vcnt = lib["Vmean"], lib["Vcnt"]; model, plab, NM = fz["model"], fz["plab"], fz["normals"]
    A1 = Rv.field_allhistory_point(Vmean, Vcnt)
    A2 = Rv.field_allhistory_scan(Vmean, Vcnt)
    assert np.allclose(A1, fz["mu_patch"])

    rep = pd.read_csv(REPLAY)
    ref_patch = {(r.trajectory, int(r.order)): r.et_mm for r in rep[rep.arm == "Patch"].itertuples()}
    ref_full = {(r.trajectory, int(r.order)): r.et_mm for r in rep[rep.arm == "Full"].itertuples()}

    rows = []; maxerr = {"A1_patch": 0.0, "B2_full": 0.0}; t0 = time.perf_counter()
    for traj in Rv.TRAJS:
        insup = Rv.support_mask(traj); zr_all, zu_all = views(traj, lib)
        order_list = list(range(Rv.REG[traj]["n"])) if traj == "VI" else [i for i in range(Rv.REG[traj]["n"]) if insup[i]]
        for order in order_list:
            P = np.asarray(Rv.load_scan_npz(traj, order)["aligned"], float)
            zr, zu = float(zr_all[order]), zu_all[order]
            cand, w, _, Dv_full = Rv.view_neighbors(zr, zu, lib, keep_full=True)
            B2 = Rv.field_view_scan(cand, w, Dv_full, Vmean, Vcnt)
            B2_ref, _ = G.mu_for_view(Vmean, Vcnt, lib["vrange"], lib["uview"], zr, zu)
            assert np.allclose(B2, B2_ref), "B2 diverged from frozen mu_for_view"
            B1 = Rv.field_view_point(cand, w, Dv_full, Vmean, Vcnt)
            fields = {"A1_patch": A1, "A2_allhist_scanw": A2, "B1_view_pointw": B1, "B2_full": B2}
            for lv in LEVELS:
                mu = fields[lv]; target = model + mu[plab]; tree = cKDTree(target)
                et, eR, it, ob = run_field(target, tree, fz, P)
                rows.append(dict(trajectory=traj, order=int(order), level=lv,
                                 in_support=bool(insup[order]), posthoc=int(Rv.REG[traj].get("posthoc", False)),
                                 et_mm=et, eR_deg=eR, iters=it, on_bound=ob))
            maxerr["A1_patch"] = max(maxerr["A1_patch"], abs(rows[-4]["et_mm"] - ref_patch[(traj, order)]))
            maxerr["B2_full"] = max(maxerr["B2_full"], abs(rows[-1]["et_mm"] - ref_full[(traj, order)]))
        print(f"[{traj}] {len(order_list)} frames, elapsed {time.perf_counter()-t0:.0f}s", flush=True)
    fr = pd.DataFrame(rows); fr.to_csv(os.path.join(OUT, "full_2x2_framewise.csv"), index=False)
    print("[validation] max |A1 - frozen Patch| et = %.3e mm ; |B2 - frozen Full| et = %.3e mm"
          % (maxerr["A1_patch"], maxerr["B2_full"]))

    # --------------------------------------------------------------- summary: medians + factor effects
    pv = fr.pivot_table(index=["trajectory", "order"], columns="level", values="et_mm").reset_index()
    srows = []
    for traj, sub in fr.groupby("trajectory"):
        med = {lv: sub[sub.level == lv].et_mm.median() for lv in LEVELS}
        medR = {lv: sub[sub.level == lv].eR_deg.median() for lv in LEVELS}
        q = pv[pv.trajectory == traj]
        srows.append(dict(trajectory=traj, n=int((fr.trajectory == traj).sum() / 4),
                          **{f"{lv}_et_med": med[lv] for lv in LEVELS},
                          **{f"{lv}_eR_med": medR[lv] for lv in LEVELS},
                          # view effect at FIXED weighting (positive = view-neighbor raises error)
                          view_effect_pointw_B1minusA1=(q.B1_view_pointw - q.A1_patch).median(),
                          view_effect_scanw_B2minusA2=(q.B2_full - q.A2_allhist_scanw).median(),
                          # weighting effect at FIXED view set (positive = scan-weighting raises error)
                          weight_effect_allhist_A2minusA1=(q.A2_allhist_scanw - q.A1_patch).median(),
                          weight_effect_view_B2minusB1=(q.B2_full - q.B1_view_pointw).median(),
                          full_minus_patch_B2minusA1=(q.B2_full - q.A1_patch).median()))
    summ = pd.DataFrame(srows); summ.to_csv(os.path.join(OUT, "full_2x2_summary.csv"), index=False)
    show = ["trajectory"] + [f"{lv}_et_med" for lv in LEVELS] + \
           ["view_effect_pointw_B1minusA1", "view_effect_scanw_B2minusA2",
            "weight_effect_allhist_A2minusA1", "weight_effect_view_B2minusB1", "full_minus_patch_B2minusA1"]
    print(summ[show].round(2).to_string(index=False))

    # --------------------------------------------------------------- figure
    order_t = ["VI", "IV", "II", "III"]; colors = ["#4C72B0", "#9ecae1", "#fdae6b", "#C44E52"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    ax = axes[0]; x = np.arange(len(order_t)); w = 0.2
    for i, lv in enumerate(LEVELS):
        vals = [summ.loc[summ.trajectory == t, f"{lv}_et_med"].iloc[0] for t in order_t]
        ax.bar(x + (i - 1.5) * w, vals, w, label=lv, color=colors[i])
    ax.set_xticks(x); ax.set_xticklabels([t + (" (post-hoc)" if t == "III" else "") for t in order_t])
    ax.set_ylabel("median translation error (mm)"); ax.set_title("2x2 cell medians"); ax.legend(fontsize=8); ax.grid(alpha=.25, axis="y")
    ax = axes[1]
    eff = ["view_effect_pointw_B1minusA1", "view_effect_scanw_B2minusA2",
           "weight_effect_allhist_A2minusA1", "weight_effect_view_B2minusB1"]
    elab = ["view effect (point-w)\nB1-A1", "view effect (scan-w)\nB2-A2",
            "weight effect (all-hist)\nA2-A1", "weight effect (view)\nB2-B1"]
    for i, t in enumerate(order_t):
        row = summ[summ.trajectory == t].iloc[0]
        ax.plot(np.arange(len(eff)), [row[e] for e in eff], "-o", label=t + ("*" if t == "III" else ""))
    ax.axhline(0, color="k", lw=1); ax.set_xticks(np.arange(len(eff))); ax.set_xticklabels(elab, fontsize=8)
    ax.set_ylabel("paired median et delta (mm)"); ax.set_title("Factor decomposition (positive = raises error)")
    ax.legend(fontsize=8); ax.grid(alpha=.25)
    fig.suptitle("Exp.5 Full 2x2 ablation: does Full's cross-trajectory reversal track view conditioning or aggregation weighting?")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(OUT, "fig_full_2x2.png"), dpi=150)
    print("[fig] fig_full_2x2.png")


if __name__ == "__main__":
    main()
