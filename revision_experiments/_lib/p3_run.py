# -*- coding: utf-8 -*-
"""p3_run.py -- P3 statistical block-size sensitivity (NO new registration).

Same frozen in-support frames; only the external-trajectory moving/block aggregation convention
changes: primary block = rank-within-in-support // L for L in {25,50,100}. VI keeps its frozen
orientation blocks (not count-based) and is reported once. Comparisons:
  Patch vs Raw, Patch+Huber vs Huber (from replay79 p2p); Patch vs Global (from followup6 primary).
Question is sign STABILITY only -- block counts are small (4..15), p-values are not emphasised.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import revx_common as R

OUT = os.path.join(R.REV, "05_block_sensitivity"); os.makedirs(OUT, exist_ok=True)
LS = [25, 50, 100]
EXT = ["IV", "II", "III"]


def rank_blocks(order, L):
    rank = np.argsort(np.argsort(np.asarray(order)))  # 0..n-1 by temporal order
    return rank // L


def block_table(delta, blocks):
    ub = np.unique(blocks)
    block_med = np.array([np.median(delta[blocks == b]) for b in ub])
    pt, lo, hi, nb = R.A.block_bootstrap_median(delta, blocks, B=2000, seed=42)
    return dict(n_blocks=int(nb), median_paired_effect=float(pt),
                median_block_effect=float(np.median(block_med)),
                ci_lo=float(lo), ci_hi=float(hi),
                sign=("positive" if pt > 0 else ("negative" if pt < 0 else "zero")),
                ci_crosses_zero=bool(lo <= 0 <= hi),
                frac_blocks_positive=float((block_med > 0).mean()))


def comparison_frames():
    a = pd.read_csv(R.REPLAY_ARMS)
    def arm(name):
        return a[a.arm == name][["trajectory", "order", "et_mm", "eR_deg"]].copy()
    raw, patch, hub, ph = arm("Raw"), arm("Patch"), arm("Huber"), arm("PatchHuber")
    pr = raw.merge(patch, on=["trajectory", "order"], suffixes=("_raw", "_patch"))
    pr["d_trans"] = pr.et_mm_raw - pr.et_mm_patch
    hh = hub.merge(ph, on=["trajectory", "order"], suffixes=("_hub", "_ph"))
    hh["d_trans"] = hh.et_mm_hub - hh.et_mm_ph
    f6 = pd.read_csv(os.path.join(R.ROOT, "FOLLOWUP_6_9", "followup6_primary_method_frame.csv"))
    g = f6[f6.method == "Global"][["trajectory", "order", "translation_error_mm"]].rename(
        columns={"translation_error_mm": "et_global"})
    p = f6[f6.method == "Patch"][["trajectory", "order", "translation_error_mm"]].rename(
        columns={"translation_error_mm": "et_patch6"})
    pg = g.merge(p, on=["trajectory", "order"])
    pg["d_trans"] = pg.et_global - pg.et_patch6
    return {"Patch_vs_Raw": pr[["trajectory", "order", "d_trans"]],
            "PatchHuber_vs_Huber": hh[["trajectory", "order", "d_trans"]],
            "Patch_vs_Global": pg[["trajectory", "order", "d_trans"]]}


def main():
    comps = comparison_frames()
    rows = []
    for cname, df in comps.items():
        for tr in EXT:
            d0 = df[df.trajectory == tr].sort_values("order")
            d = d0.d_trans.values
            for L in LS:
                blk = rank_blocks(d0.order.values, L)
                r = dict(comparison=cname, trajectory=tr, block_size=L, **block_table(d, blk))
                rows.append(r)
        # VI: frozen orientation blocks are fixed (independent of L) -> report once
        d0 = df[df.trajectory == "VI"].sort_values("order")
        # join frozen VI blocks
        bl = R.baseline_arm("Raw")[["trajectory", "order", "block"]]
        d0 = d0.merge(bl, on=["trajectory", "order"])
        r = dict(comparison=cname, trajectory="VI", block_size="frozen_orientation",
                 **block_table(d0.d_trans.values, d0.block.values))
        rows.append(r)
    SM = pd.DataFrame(rows)
    sm = os.path.join(OUT, "block_size_summary.csv"); SM.to_csv(sm, index=False)
    fw = os.path.join(OUT, "block_size_paired_deltas.csv")
    pd.concat([df.assign(comparison=c) for c, df in comps.items()], ignore_index=True).to_csv(fw, index=False)
    R.write_provenance(os.path.join(OUT, "block_size_provenance.json"), "P3-block-size",
                       "python revision_experiments/_lib/p3_run.py",
                       config=dict(block_sizes=LS, frame_set="frozen in-support, unchanged",
                                   bootstrap="block resample B=2000 seed=42", vi="fixed orientation blocks"),
                       seed=42, outputs={"summary": sm, "paired_deltas": fw},
                       note="Aggregation-convention sensitivity; no frame re-selection, no new registration.")
    piv = SM.pivot_table(index=["comparison", "trajectory"], columns="block_size",
                        values="median_paired_effect", aggfunc="first")
    print(piv.to_string())
    print("\nsign-stability (Patch_vs_Raw) across 25/50/100:")
    print(SM[SM.comparison == "Patch_vs_Raw"][["trajectory", "block_size", "n_blocks",
          "median_paired_effect", "ci_crosses_zero", "frac_blocks_positive"]].to_string(index=False))


if __name__ == "__main__":
    main()
