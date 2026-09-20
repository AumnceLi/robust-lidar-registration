# -*- coding: utf-8 -*-
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

import pandas as pd, numpy as np, os
OUT = _pp("FOLLOWUP_6_9")
def n(f): return len(pd.read_csv(os.path.join(OUT, f)))
files = ["followup6_primary_method_frame.csv","followup6_primary_method_block.csv","followup6_primary_method_summary.csv",
         "followup7_patch_robust_frame.csv","followup7_patch_robust_block.csv","followup7_patch_robust_summary.csv",
         "followup8_condition_summary.csv","followup8_equal_rms_pairs.csv",
         "followup9_view_support_frame.csv","followup9_view_support_block.csv","followup9_view_support_summary.csv"]
for f in files: print(f"{f:48s} rows={n(f)}")

# cross-check item7/9 replay medians vs item6 (frozen master) marginal medians
m6 = pd.read_csv(os.path.join(OUT,"followup6_primary_method_summary.csv")); m6=m6[m6.section=="marginal"]
f7 = pd.read_csv(os.path.join(OUT,"followup7_patch_robust_frame.csv"))
lab={"Raw":"Raw","Huber":"Huber","Trim":"Trim","Patch":"Patch"}
worst=0
for tr in ["VI","IV","II","III"]:
    for arm,meth in lab.items():
        a=f7[(f7.trajectory==tr)&(f7.arm==arm)].translation_error_mm.median()
        b=m6[(m6.trajectory==tr)&(m6.method==meth)&(m6.axis=="translation")]["median"].iloc[0]
        worst=max(worst,abs(a-b))
print("item7 replay vs item6 master translation median worst diff:",worst)
f9=pd.read_csv(os.path.join(OUT,"followup9_view_support_frame.csv"))
w2=0
for tr in ["VI","IV","II","III"]:
    for col,meth in [("raw_et_mm","Raw"),("patch_et_mm","Patch"),("full_et_mm","Full")]:
        a=f9[f9.trajectory==tr][col].median()
        b=m6[(m6.trajectory==tr)&(m6.method==meth)&(m6.axis=="translation")]["median"].iloc[0]
        w2=max(w2,abs(a-b))
print("item9 replay vs item6 master translation median worst diff:",w2)
# NaN audit on key item9 columns (coverage const for V expected)
key=["nearest_d","ess_kernel","coverage","cos_pred_raw_t","full_minus_patch_mm"]
print("item9 NaN counts:\n", f9[key].isna().sum().to_string())
# item8 pairs sanity
p=pd.read_csv(os.path.join(OUT,"followup8_equal_rms_pairs.csv"))
print("item8 5pct pairs:",len(p),"max reldiff:",p.reldiff.max().round(4),"families:",sorted(p.familyA.unique()))
