# -*- coding: utf-8 -*-
"""Rebuild T2 block table/tests from the frame CSV (V uses block_full because V is analyzed on ALL
frames; the other trajectories use the primary in-support blocks)."""
import os, sys
import numpy as np, pandas as pd
from scipy import stats as st
sys.path.insert(0, os.path.dirname(__file__))
import af_common as A

F = pd.read_csv(os.path.join(A.OUT, "patch_label_placebo_frame.csv"))


def wilc(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b) & (a != b)
    return float(st.wilcoxon(a[m], b[m]).pvalue) if m.sum() >= 3 else np.nan


def main():
    brows = []
    for traj, d in F.groupby("trajectory"):
        prim = d if traj == "V" else d[d.in_support]
        blkcol = "block_full" if traj == "V" else "block_primary"
        for b, q in prim.groupby(blkcol):
            r = dict(trajectory=traj, block=int(b), n=len(q))
            for arm in ["raw", "patch", "shuf"]:
                r[f"{arm}_et_med"] = q[f"{arm}_et_mm"].median()
                r[f"{arm}_eR_med"] = q[f"{arm}_eR_deg"].median()
                r[f"{arm}_gt_med"] = q[f"{arm}_gt"].median()
                r[f"{arm}_gr_med"] = q[f"{arm}_gr"].median()
            r["shuf_ens_et_med"] = q.shuf_ens_et_med.median()
            r["shuf_ens_et_lo"] = q.shuf_ens_et_min.median()
            r["shuf_ens_et_hi"] = q.shuf_ens_et_max.median()
            r["d_et_patch_raw"] = q.d_et_patch_raw.median()
            r["d_et_shuf_raw"] = q.d_et_shuf_raw.median()
            r["d_et_patch_shuf"] = q.d_et_patch_shuf.median()
            r["d_eR_patch_raw"] = q.d_eR_patch_raw.median()
            r["d_eR_shuf_raw"] = q.d_eR_shuf_raw.median()
            r["d_gt_patch_raw"] = q.d_gt_patch_raw.median()
            r["d_gt_shuf_raw"] = q.d_gt_shuf_raw.median()
            brows.append(r)
    B = pd.DataFrame(brows)
    B.to_csv(os.path.join(A.OUT, "patch_label_placebo_block.csv"), index=False)
    trows = []
    for traj, b in B.groupby("trajectory"):
        trows.append(dict(trajectory=traj, K=len(b),
            patch_et_blocks_improved=int((b.d_et_patch_raw > 0).sum()),
            shuf_et_blocks_improved=int((b.d_et_shuf_raw > 0).sum()),
            patch_beats_shuf_blocks=int((b.d_et_patch_shuf > 0).sum()),
            med_block_dEt_patch_raw=float(b.d_et_patch_raw.median()),
            med_block_dEt_shuf_raw=float(b.d_et_shuf_raw.median()),
            med_block_dEt_patch_shuf=float(b.d_et_patch_shuf.median()),
            med_block_dER_patch_raw=float(b.d_eR_patch_raw.median()),
            med_block_dER_shuf_raw=float(b.d_eR_shuf_raw.median()),
            wilcoxon_p_patch_vs_shuf_et=wilc(b.patch_et_med, b.shuf_et_med),
            wilcoxon_p_patch_vs_raw_et=wilc(b.patch_et_med, b.raw_et_med),
            wilcoxon_p_shuf_vs_raw_et=wilc(b.shuf_et_med, b.raw_et_med)))
    T = pd.DataFrame(trows)
    T.to_csv(os.path.join(A.OUT, "scripts", "t2_block_tests.csv"), index=False)
    print(T.to_string(index=False))


if __name__ == "__main__":
    main()
