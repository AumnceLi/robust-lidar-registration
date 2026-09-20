# -*- coding: utf-8 -*-
"""p2b_run.py -- P2-B (OPTIONAL): minimal, parameter-FREE patch-boundary smoothing ablation.

The current correction field is piecewise constant: c_i = mu_patch[plab_i]. We apply exactly ONE
surface-neighbour averaging step using the SAME frozen k=16 model self-neighbourhood that the nominal
normal estimator uses (s0_common.pca_normals k=16). There is no bandwidth/weight/iteration to tune and
no outcome is used to choose it: c_smooth_i = mean_{j in NN16(i)} mu_patch[plab_j]. Interior points of
a patch are unchanged; only points straddling a patch boundary blend with their neighbours.
Frozen model normals are kept so the ONLY difference from PatchHuber is boundary smoothing.
This is a diagnostic ablation, NOT a proposed replacement method.
"""
import os, sys, time
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
import revx_common as R

OUT = os.path.join(R.REV, "04_normal_recompute")  # share the rotation-ablation folder


def smoothed_target(k=16):
    model, nmodel, sf = R.model_and_normals()
    plab = R.make_partition(24, 0.30, 42, model, nmodel)
    mu, _ = R.vi_view_independent_mu(plab, 24, model)
    tree = cKDTree(model)
    _, nn16 = tree.query(model, k=k)                 # identical neighbourhood rule to pca_normals(k=16)
    c_piece = mu[plab]
    c_smooth = c_piece[nn16].mean(axis=1)
    # quantify how much the field actually changes (only near boundaries)
    moved = np.linalg.norm(c_smooth - c_piece, axis=1) * 1000
    print(f"[smooth] k={k}; per-point |c_smooth-c_piece| mm  median={np.median(moved):.3f} "
          f"p90={np.percentile(moved,90):.3f} max={moved.max():.3f}; "
          f"frac changed >1e-6m = {(moved>1e-3).mean():.3f}")
    return model + c_smooth, nmodel, sf


def get_smooth_arm(kind, form, nw=R.NW):
    tag = f"smooth_{kind}_{form}"; path = os.path.join(R.ARM_CACHE, tag + ".csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    target, normals, sf = smoothed_target()
    df = R.run_arm(target, normals, sf, kind, form, nw=nw, label=tag)
    df.to_csv(path, index=False)
    return df


def summ(channel, hub, arm, name):
    rows = []
    for tr in R.TRAJS:
        m = hub[hub.trajectory == tr].merge(arm[arm.trajectory == tr], on=["trajectory", "order"],
                                            suffixes=("_h", "_a"))
        rows.append(dict(trajectory=tr, channel=channel, arm=name, n_frames=len(m),
                         translation_median_mm=float(np.median(m.et_mm_a)),
                         rotation_median_deg=float(np.median(m.eR_deg_a)),
                         paired_translation_effect_vs_Huber_mm=float(np.median(m.et_mm_h - m.et_mm_a)),
                         paired_rotation_effect_vs_Huber_deg=float(np.median(m.eR_deg_a - m.eR_deg_h))))
    return rows


def main():
    t0 = time.perf_counter()
    sm_ls = get_smooth_arm("p2p", "ls")
    sm_hub_p2p = get_smooth_arm("p2p", "huber")
    sm_hub_p2l = get_smooth_arm("p2l", "huber")
    raw = R.baseline_arm("Raw"); hub = R.baseline_arm("Huber")
    hub_p2l = R.get_raw_arm("p2l", "huber")[0]
    # Patch LS vs Raw (translation gain / rotation change for the smoothed field, p2p)
    rows = []
    for tr in R.TRAJS:
        m = raw[raw.trajectory == tr].merge(sm_ls[sm_ls.trajectory == tr], on=["trajectory", "order"],
                                            suffixes=("_raw", "_sm"))
        rows.append(dict(trajectory=tr, channel="p2p", arm="PatchSmooth_vs_Raw", n_frames=len(m),
                         translation_median_mm=float(np.median(m.et_mm_sm)),
                         rotation_median_deg=float(np.median(m.eR_deg_sm)),
                         paired_translation_effect_vs_Huber_mm=float(np.median(m.et_mm_raw - m.et_mm_sm)),
                         paired_rotation_effect_vs_Huber_deg=float(np.median(m.eR_deg_sm - m.eR_deg_raw))))
    rows += summ("p2p", hub, sm_hub_p2p, "PatchSmoothHuber")
    rows += summ("p2l", hub_p2l, sm_hub_p2l, "PatchSmoothHuber")
    SM = pd.DataFrame(rows)
    path = os.path.join(OUT, "boundary_smoothing_summary.csv"); SM.to_csv(path, index=False)
    for a in ["smooth_p2p_ls", "smooth_p2p_huber", "smooth_p2l_huber"]:
        pass
    R.write_provenance(os.path.join(OUT, "boundary_smoothing_provenance.json"), "P2-B-boundary-smoothing",
                       "python revision_experiments/_lib/p2b_run.py",
                       config=dict(k_neighbor=16, steps=1, rule="mean of frozen per-patch correction over the "
                                   "same k=16 self-neighbourhood as pca_normals; frozen normals retained",
                                   tuned=False),
                       seed=42, outputs={"summary": path},
                       note="Parameter-free diagnostic ablation of piecewise-constant boundaries; not a method.")
    print(SM.to_string(index=False)); print(f"[P2-B] done {time.perf_counter()-t0:.0f}s")


if __name__ == "__main__":
    main()
