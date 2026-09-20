# -*- coding: utf-8 -*-
"""p2a_run.py -- P2-A: does recomputing normals on the corrected geometry change the rotation penalty?

Frozen 24/0.30/42 field only. Three arms per channel:
  Huber            : robust ICP on the nominal model, frozen PCA normals
  PatchHuber       : robust ICP on model + frozen mu_patch, FROZEN model normals (current method)
  PatchReNormalHub : robust ICP on model + frozen mu_patch, normals RE-ESTIMATED on the corrected
                     geometry with the SAME nominal protocol (pca_normals k=16, outward from centroid)
Channels: p2p (paper primary; point-to-point does NOT consume normals -> ReNormal must be ~identical,
a mechanistic gate) and p2l (the only channel in which stale normals could act).
Nothing is tuned; comparison is frame-paired.
"""
import os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import revx_common as R

OUT = os.path.join(R.REV, "04_normal_recompute"); os.makedirs(OUT, exist_ok=True)


def med(d, c):
    return float(np.median(d[c]))

def arm_summary(channel, hub, arm, armname):
    rows = []
    for tr in R.TRAJS:
        h = hub[hub.trajectory == tr]; a = arm[arm.trajectory == tr]
        m = h.merge(a, on=["trajectory", "order"], suffixes=("_h", "_a"))
        rows.append(dict(trajectory=tr, channel=channel, arm=armname, n_frames=len(m),
                         translation_median_mm=med(m, "et_mm_a"),
                         rotation_median_deg=med(m, "eR_deg_a"),
                         paired_translation_effect_vs_Huber_mm=float(np.median(m.et_mm_h - m.et_mm_a)),
                         paired_rotation_effect_vs_Huber_deg=float(np.median(m.eR_deg_a - m.eR_deg_h))))
    return rows


def main():
    t0 = time.perf_counter()
    exact = "python revision_experiments/_lib/p2a_run.py"
    # ---- p2p: Huber & PatchHuber REUSED from replay79 (never re-run); ReNormal is new
    hub_p2p = R.baseline_arm("Huber")
    ph_p2p = R.baseline_arm("PatchHuber")
    rn_p2p, tag_rn_p2p = R.get_partition_arm(24, 0.30, 42, "p2p", "huber", "renormal")
    # ---- p2l: all three are computed (replay79 only stored p2p)
    hub_p2l, _ = R.get_raw_arm("p2l", "huber")
    ph_p2l, _ = R.get_partition_arm(24, 0.30, 42, "p2l", "huber", "frozen")
    rn_p2l, tag_rn_p2l = R.get_partition_arm(24, 0.30, 42, "p2l", "huber", "renormal")

    rows = []
    for channel, hub, ph, rn in [("p2p", hub_p2p, ph_p2p, rn_p2p),
                                 ("p2l", hub_p2l, ph_p2l, rn_p2l)]:
        rows += arm_summary(channel, hub, hub, "Huber")
        rows += arm_summary(channel, hub, ph, "PatchHuber")
        rows += arm_summary(channel, hub, rn, "PatchReNormalHuber")
    SM = pd.DataFrame(rows)
    sm_path = os.path.join(OUT, "normal_recompute_summary.csv"); SM.to_csv(sm_path, index=False)

    # framewise bundle (the three new/reused arms, both channels)
    FW = pd.concat([
        hub_p2p.assign(channel="p2p", arm="Huber"),
        ph_p2p.assign(channel="p2p", arm="PatchHuber"),
        rn_p2p.assign(channel="p2p", arm="PatchReNormalHuber"),
        hub_p2l.assign(channel="p2l", arm="Huber"),
        ph_p2l.assign(channel="p2l", arm="PatchHuber"),
        rn_p2l.assign(channel="p2l", arm="PatchReNormalHuber")], ignore_index=True)
    fw_path = os.path.join(OUT, "normal_recompute_framewise.csv"); FW.to_csv(fw_path, index=False)

    # ---- mechanistic gate: p2p ReNormal must equal frozen-normal PatchHuber (normals unused in p2p)
    g = ph_p2p.merge(rn_p2p, on=["trajectory", "order"], suffixes=("_ph", "_rn"))
    gate = dict(p2p_renormal_vs_patchhuber_max_abs_translation_mm=float((g.et_mm_ph - g.et_mm_rn).abs().max()),
                p2p_renormal_vs_patchhuber_max_abs_rotation_deg=float((g.eR_deg_ph - g.eR_deg_rn).abs().max()))
    # ---- key question on p2l: does recomputing normals shrink the rotation penalty / keep translation?
    p2l = SM[SM.channel == "p2l"].set_index(["trajectory", "arm"])
    q = {}
    for tr in R.TRAJS:
        q[tr] = dict(
            patchhuber_rot_penalty=float(p2l.loc[(tr, "PatchHuber"), "paired_rotation_effect_vs_Huber_deg"]),
            renormal_rot_penalty=float(p2l.loc[(tr, "PatchReNormalHuber"), "paired_rotation_effect_vs_Huber_deg"]),
            patchhuber_trans_gain=float(p2l.loc[(tr, "PatchHuber"), "paired_translation_effect_vs_Huber_mm"]),
            renormal_trans_gain=float(p2l.loc[(tr, "PatchReNormalHuber"), "paired_translation_effect_vs_Huber_mm"]))
    R.write_provenance(os.path.join(OUT, "normal_recompute_provenance.json"), "P2-A-normal-recompute", exact,
                       config=dict(k=24, normal_weight=0.30, seed=42,
                                   normal_protocol="pca_normals k=16 smallest-eigenvector outward-from-centroid",
                                   channels=["p2p", "p2l"]),
                       seed=42, outputs={"framewise": fw_path, "summary": sm_path},
                       note="Recomputed-normals ablation; p2p is a mechanistic gate (normals unused).")
    print("[P2-A gate]", gate)
    print("[P2-A p2l question]"); print(pd.DataFrame(q).T.to_string())
    print(SM.to_string(index=False))
    print(f"[P2-A] done {time.perf_counter()-t0:.0f}s")


if __name__ == "__main__":
    main()
