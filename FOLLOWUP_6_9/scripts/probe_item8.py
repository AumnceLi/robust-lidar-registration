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

import numpy as np, pandas as pd
pd.set_option("display.width",220); pd.set_option("display.max_rows",200)
gr = pd.read_csv(_pp("g_chain/G_GENERALITY/results/geometry_results.csv"))
d = gr[(gr.kind=="p2p")&(gr.form=="ls")].copy()
d["rms_mm"]=np.sqrt(d.J0)*1000
fam = {x:x.split("_")[0] for x in d.dtype.unique()}
d["family"]=d.dtype.map(fam)
# condition medians over reps
cond = d.groupby(["geometry","dtype","family","mag"]).agg(
    rms=("rms_mm","median"), et=("et_mm","median"), eR=("eR_deg","median"),
    grad=("grad_gt","median"), n=("rep","nunique")).reset_index()
nz = cond[cond.mag>0]
print("families:", sorted(nz.family.unique()))
print("condition slots (nonzero):", len(nz))
for geom in ["GA","GB","GC"]:
    print(f"\n=== {geom} condition medians (rms_mm / et_mm / eR_deg) ===")
    q=nz[nz.geometry==geom]
    for dt in sorted(q.dtype.unique()):
        rr=q[q.dtype==dt].sort_values("mag")
        print(dt)
        print("  mag:", " ".join(f"{m:g}" for m in rr.mag))
        print("  rms:", " ".join(f"{v:7.2f}" for v in rr.rms))
        print("  et :", " ".join(f"{v:7.3f}" for v in rr.et))
# cross-family nearest-RMS matching within geometry
def match(thr):
    rows=[]
    for geom in ["GA","GB","GC"]:
        q=nz[nz.geometry==geom].reset_index(drop=True)
        for i,a in q.iterrows():
            cand=q[(q.family!=a.family)].copy()
            cand["reldiff"]=(cand.rms-a.rms).abs()/np.maximum(cand.rms,a.rms)
            cand=cand.sort_values("reldiff")
            for _,b in cand.head(3).iterrows():
                if b.reldiff<=thr:
                    rows.append((geom,a.dtype,a.mag,b.dtype,b.mag,a.rms,b.rms,b.reldiff,a.et,b.et,a.eR,b.eR))
    return pd.DataFrame(rows,columns=["geom","dA","mA","dB","mB","rmsA","rmsB","reldiff","etA","etB","eRA","eRB"])
for thr in [0.05,0.10]:
    m=match(thr)
    print(f"\nthr={thr}: total ordered-neighbor pairs={len(m)}; unique A-conditions with a partner={m.groupby(['geom','dA','mA']).ngroups}")
    print(m.dA.value_counts().to_string())
