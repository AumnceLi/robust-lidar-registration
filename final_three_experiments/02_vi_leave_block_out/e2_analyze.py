# -*- coding: utf-8 -*-
"""E2 analysis -- per-fold table + pooled 501-frame out-of-fold result + in-sample vs OOF comparison.

Convention: paired benefit = Raw - Patch (POSITIVE = Patch better), paired by scan (each scan scored
once under the fold that held its block). Block bootstrap seed=42 (frozen convention). No parameter
is chosen from the result; the warning rule is fixed here.
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
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F
G = F.G
B_BOOT = 2000; SEED = 42


def block_of_blocks_ci(block_vals, B=B_BOOT, seed=SEED):
    """Bootstrap the SIX block-level statistics (resample blocks with replacement)."""
    bv = np.asarray(block_vals, float); rng = np.random.default_rng(seed); out = np.empty(B)
    for b in range(B):
        pick = rng.integers(0, len(bv), size=len(bv))
        out[b] = np.median(bv[pick])
    return dict(point=float(np.median(bv)), lo=float(np.percentile(out,2.5)), hi=float(np.percentile(out,97.5)))


def main():
    fw = pd.read_csv(os.path.join(F.E2_OUT, "e2_vi_lobo_framewise.csv"))
    prov = json.load(open(os.path.join(F.E2_OUT, "e2_lobo_fold_provenance.json")))
    w = fw.pivot_table(index=["scan","fold"], columns="method", values=["et_mm","eR_deg","on_bound","iters"])
    w.columns = [f"{s}_{m}" for s, m in w.columns]; w = w.reset_index()
    w["benefit_oof"] = w["et_mm_Raw"] - w["et_mm_PatchOOF"]
    w["benefit_fullfit"] = w["et_mm_Raw"] - w["et_mm_PatchFullFit"]
    w["benefit_ph"] = w["et_mm_Huber"] - w["et_mm_PatchHuberOOF"]
    w["rot_change_oof"] = w["eR_deg_Raw"] - w["eR_deg_PatchOOF"]
    w["oof_minus_fullfit_error"] = w["et_mm_PatchOOF"] - w["et_mm_PatchFullFit"]
    w.to_csv(os.path.join(F.E2_OUT,"e2_vi_lobo_oof_framewise.csv"), index=False)

    # ------------------------------------------------ per-fold table
    folds = []
    for j in range(6):
        g = w[w.fold == j]
        folds.append(dict(
            fold=j, n=len(g), block_range=prov["block_ranges"][str(j)],
            Raw_et_med=float(g.et_mm_Raw.median()), PatchOOF_et_med=float(g.et_mm_PatchOOF.median()),
            paired_benefit_med=float(g.benefit_oof.median()),
            rot_change_med=float(g.rot_change_oof.median()),
            trans_improved_frac=float((g.benefit_oof > 0).mean()),
            patch_boundary_rate=float(g.on_bound_PatchOOF.mean()),
            Huber_et_med=float(g.et_mm_Huber.median()), PatchHuberOOF_et_med=float(g.et_mm_PatchHuberOOF.median()),
            PH_benefit_med=float(g.benefit_ph.median())))
    ftab = pd.DataFrame(folds)
    ftab.to_csv(os.path.join(F.E2_OUT,"e2_vi_lobo_fold_table.csv"), index=False)

    # ------------------------------------------------ pooled OOF (501)
    n = len(w)
    block_meds = [float(w[w.fold==j].benefit_oof.median()) for j in range(6)]
    bci = block_of_blocks_ci(block_meds)
    # frame-level moving-block bootstrap on ordered scans (frozen g_common.block_boot, L=5/10/20)
    wsort = w.sort_values("scan")
    fb = G.block_boot(wsort.benefit_oof.values, stat=np.median, B=B_BOOT, Ls=(5,10,20), seed=SEED)
    raw_med = float(w.et_mm_Raw.median()); oof_med = float(w.et_mm_PatchOOF.median.mean()) if False else float(w.et_mm_PatchOOF.median())
    full_med = float(w.et_mm_PatchFullFit.median())
    ben_med = float(w.benefit_oof.median()); ben_mean = float(w.benefit_oof.mean())
    ben_full = float(w.benefit_fullfit.median())
    pos_blocks = int(sum(1 for x in block_meds if x > 0)); neg_blocks = int(sum(1 for x in block_meds if x < 0))
    # one-sided paired block sign-flip p (frozen)
    _, p_sign = G.block_signflip_p(wsort.benefit_oof.values, B=B_BOOT, L=5, seed=SEED)
    summary = dict(
        n_scans=n,
        raw_et_med=raw_med, oof_patch_et_med=oof_med, fullfit_patch_et_med=full_med,
        oof_benefit_med=ben_med, oof_benefit_mean=ben_mean,
        fullfit_benefit_med=ben_full,
        in_sample_optimism_benefit=float(ben_full-ben_med),
        oof_minus_fullfit_error_med=float(w.oof_minus_fullfit_error.median()),
        trans_improved_frac=float((w.benefit_oof>0).mean()),
        rot_change_med=float(w.rot_change_oof.median()),
        block_benefit_meds=block_meds, positive_blocks=f"{pos_blocks}/6", negative_blocks=f"{neg_blocks}/6",
        block_of_blocks_bootstrap=bci,
        frame_moving_block_bootstrap=fb,
        block_signflip_p=p_sign,
        patch_oof_boundary_rate=float(w.on_bound_PatchOOF.mean()),
        raw_boundary_rate=float(w.on_bound_Raw.mean()),
        huber_et_med=float(w.et_mm_Huber.median()), ph_oof_et_med=float(w.et_mm_PatchHuberOOF.median()),
        ph_oof_benefit_med=float(w.benefit_ph.median()),
        fidelity=prov["fidelity"],
    )
    # fixed decision rule (NOT tuned to outcome)
    if ben_med <= 0 or pos_blocks < 3:
        flag = "VI_INTERNAL_GENERALIZATION_WARNING"
    elif summary["in_sample_optimism_benefit"] > 0.25 * abs(ben_full):
        flag = "OOF_POSITIVE_BUT_INSAMPLE_OPTIMISTIC"
    else:
        flag = "OOF_POSITIVE_RETAINED"
    summary["flag"] = flag
    with open(os.path.join(F.E2_OUT,"e2_vi_lobo_summary.json"),"w") as f:
        json.dump(summary, f, indent=2, default=float)

    # ------------------------------------------------ console
    print("=== per-fold table ===")
    print(ftab[["fold","n","Raw_et_med","PatchOOF_et_med","paired_benefit_med","rot_change_med",
                "trans_improved_frac","patch_boundary_rate"]].round(3).to_string(index=False))
    print("\n=== OOF pooled (501) ===")
    for k in ["raw_et_med","oof_patch_et_med","fullfit_patch_et_med","oof_benefit_med","oof_benefit_mean",
              "fullfit_benefit_med","in_sample_optimism_benefit","oof_minus_fullfit_error_med",
              "trans_improved_frac","positive_blocks","block_signflip_p","flag"]:
        print(f"  {k}: {summary[k]}")
    print("  block-of-blocks bootstrap:", bci)
    print("  frame moving-block bootstrap:", {k:fb[k] for k in fb if k!='n'})
    print("\nwrote fold_table, oof_framewise, summary.")


if __name__ == "__main__":
    main()
