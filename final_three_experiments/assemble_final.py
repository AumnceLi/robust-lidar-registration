# -*- coding: utf-8 -*-
"""Assemble final_three_summary.csv (tidy headline results across E1/E2/E3)."""
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
rows=[]
def add(exp, scope, key, method, metric, value, note=""):
    rows.append(dict(experiment=exp, scope=scope, level_or_fold=key, method=method,
                     metric=metric, value=round(float(value),6) if pd.notna(value) else value, note=note))

# ---- E1
e1=pd.read_csv(os.path.join(F.E1_OUT,"e1_coarse_init_summary.csv"))
for _,r in e1.iterrows():
    if r.method in ("Raw","Patch"):
        for met in ["et_med","eR_med","captureA_rate","captureB_rate","safeguard_rate",
                    "itercap_rate","numfail_rate","PatchRaw_gain_t_med","PatchRaw_frac_pos"]:
            add("E1", r.trajectory, r.level, r.method, met, r[met])
# ---- E2
fold=pd.read_csv(os.path.join(F.E2_OUT,"e2_vi_lobo_fold_table.csv"))
for _,r in fold.iterrows():
    add("E2","VI_heldout",f"fold{int(r.fold)}_{r.block_range}","Raw","et_med",r.Raw_et_med)
    add("E2","VI_heldout",f"fold{int(r.fold)}_{r.block_range}","PatchOOF","et_med",r.PatchOOF_et_med)
    add("E2","VI_heldout",f"fold{int(r.fold)}_{r.block_range}","Raw-PatchOOF","paired_benefit_med",r.paired_benefit_med)
    add("E2","VI_heldout",f"fold{int(r.fold)}_{r.block_range}","Raw-PatchOOF","trans_improved_frac",r.trans_improved_frac)
s2=json.load(open(os.path.join(F.E2_OUT,"e2_vi_lobo_summary.json")))
for k in ["raw_et_med","oof_patch_et_med","fullfit_patch_et_med","oof_benefit_med","fullfit_benefit_med",
          "in_sample_optimism_benefit","oof_minus_fullfit_error_med","trans_improved_frac","rot_change_med",
          "huber_et_med","ph_oof_et_med","ph_oof_benefit_med","block_signflip_p"]:
    add("E2","VI_OOF_pooled","pooled501","-",k,s2[k])
add("E2","VI_OOF_pooled","pooled501","-","positive_blocks",int(s2["positive_blocks"].split("/")[0]))
add("E2","VI_OOF_pooled","pooled501","-","block_bootstrap_lo",s2["block_of_blocks_bootstrap"]["lo"])
add("E2","VI_OOF_pooled","pooled501","-","block_bootstrap_hi",s2["block_of_blocks_bootstrap"]["hi"])
add("E2","VI_OOF_pooled","pooled501","-","flag:"+s2["flag"],1)
# ---- E3
e3=pd.read_csv(os.path.join(F.E3_OUT,"runtime_summary.csv"))
for _,r in e3.iterrows():
    for met in ["median_total_ms","p25_ms","p75_ms","p95_ms","model_build_ms","query_ms","kdtree_ms",
                "registration1_ms","registration2_ms","peak_rss_mb"]:
        add("E3","runtime",r.trajectory,r.method,met,r[met])
cal=json.load(open(os.path.join(F.E3_OUT,"e3_calibration.json")))
for k in ["kmeans_cluster_ms_median","vi_field_build_ms_median","patch_corrected_model_build_ms",
          "patch_kdtree_build_ms","mu_patch_bytes","patches_npz_size_b","predictor_size_b"]:
    add("E3","calibration","one_time","-",k,cal[k])

out=pd.DataFrame(rows)
out.to_csv(os.path.join(F.F3,"final_three_summary.csv"),index=False)
print("wrote final_three_summary.csv rows=",len(out))
print(out.groupby("experiment").size().to_dict())
