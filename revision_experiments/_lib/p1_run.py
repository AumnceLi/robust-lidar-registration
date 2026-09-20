# -*- coding: utf-8 -*-
"""p1_run.py -- P1 Patch hyperparameter STABILITY (not optimization).

Fixed grids declared BEFORE inspecting any IV/II/III outcome:
  P1-A patch count : {12,18,24,32,48}, w=0.30, seed=42
  P1-B normal weight: {0,.15,.30,.60,1.0}, k=24, seed=42   (w=0 == position-only XYZ -> answers P1-D)
  P1-C cluster seed : {0,1,2,42,20240910}, k=24, w=0.30
The frozen 24/0.30/42 cell is the paper main config and is NEVER re-selected; it is the common anchor.
Baseline Raw is REUSED from replay79 (never re-run). Per-config Patch-LS arms are cached on disk.
"""
import os, sys, json, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import revx_common as R

REV = R.REV
GRIDS = {
    "01_patch_count":  [("k12", 12, 0.30, 42), ("k18", 18, 0.30, 42), ("k24", 24, 0.30, 42),
                        ("k32", 32, 0.30, 42), ("k48", 48, 0.30, 42)],
    "02_normal_weight": [("w000", 24, 0.00, 42), ("w015", 24, 0.15, 42), ("w030", 24, 0.30, 42),
                         ("w060", 24, 0.60, 42), ("w100", 24, 1.00, 42)],
    "03_seed_sensitivity": [("s0", 24, 0.30, 0), ("s1", 24, 0.30, 1), ("s2", 24, 0.30, 2),
                            ("s42", 24, 0.30, 42), ("s20240910", 24, 0.30, 20240910)],
}
AXIS = {"01_patch_count": "patch_count", "02_normal_weight": "normal_weight",
        "03_seed_sensitivity": "clustering_seed"}


def main():
    t0 = time.perf_counter()
    raw = R.baseline_arm("Raw")
    exact = "python revision_experiments/_lib/p1_run.py"
    for exp, grid in GRIDS.items():
        outdir = os.path.join(REV, exp); os.makedirs(outdir, exist_ok=True)
        frames, summaries = [], []
        for cid, k, w, sd in grid:
            arm, tag = R.get_partition_arm(k, w, sd, kind="p2p", form="ls")
            arm = arm.copy(); arm["config"] = cid; arm[AXIS[exp]] = {
                "01_patch_count": k, "02_normal_weight": w, "03_seed_sensitivity": sd}[exp]
            frames.append(arm)
            summ = R.summarize_against(raw, arm.drop(columns=[c for c in
                                          ["k", "w", "seed", "min_patch_count", "normals_mode"]
                                          if c in arm.columns], errors="ignore"))
            summ["config"] = cid; summ[AXIS[exp]] = {"01_patch_count": k, "02_normal_weight": w,
                                                     "03_seed_sensitivity": sd}[exp]
            summaries.append(summ)
        FW = pd.concat(frames, ignore_index=True)
        SM = pd.concat(summaries, ignore_index=True)
        fw_path = os.path.join(outdir, f"{exp}_framewise.csv")
        sm_path = os.path.join(outdir, f"{exp}_summary.csv")
        FW.to_csv(fw_path, index=False); SM.to_csv(sm_path, index=False)

        # ---- seed-sensitivity extra: across-seed mean/median/range per trajectory + sign question
        extra = {}
        if exp == "03_seed_sensitivity":
            rows = []
            for tr in R.TRAJS:
                d = SM[SM.trajectory == tr]
                rows.append(dict(trajectory=tr,
                    patch_translation_med_across_seeds_mean=d.patch_translation_median_mm.mean(),
                    patch_translation_med_across_seeds_median=d.patch_translation_median_mm.median(),
                    patch_translation_med_range=(d.patch_translation_median_mm.min(), d.patch_translation_median_mm.max()),
                    paired_translation_benefit_min=d.paired_translation_benefit_mm.min(),
                    paired_translation_benefit_max=d.paired_translation_benefit_mm.max(),
                    paired_benefit_positive_in_all_5=bool((d.paired_translation_benefit_mm > 0).all()),
                    patch_rotation_med_range=(d.patch_rotation_median_deg.min(), d.patch_rotation_median_deg.max())))
            SE = pd.DataFrame(rows); SE.to_csv(os.path.join(outdir, f"{exp}_seed_spread.csv"), index=False)
            extra["all_seeds_paired_translation_benefit_positive"] = {
                r.trajectory: bool(r.paired_benefit_positive_in_all_5) for r in SE.itertuples()}
        R.write_provenance(os.path.join(outdir, f"{exp}_provenance.json"), exp, exact,
                           config={AXIS[exp]: [list(x) for x in grid], "other_params": "frozen main config",
                                   "baseline": "Raw arm reused from replay79_arms.csv"},
                           seed=42, outputs={"framewise": fw_path, "summary": sm_path},
                           note="Stability analysis only; main config 24/0.30/42 not re-selected.")
        print(f"[{exp}] wrote summary; elapsed {time.perf_counter()-t0:.0f}s\n", SM[
            ["trajectory","config","raw_translation_median_mm","patch_translation_median_mm",
             "paired_translation_benefit_mm","translation_improved_frac",
             "paired_rotation_change_deg","n_blocks"]].to_string(index=False), "\n")
        if extra:
            print(json.dumps(extra, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
