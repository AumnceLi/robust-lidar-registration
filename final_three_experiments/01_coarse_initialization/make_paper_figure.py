# -*- coding: utf-8 -*-
"""Single paper figure for E1: row1 Capture-B rate, row2 median final t-error; columns = trajectories."""
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

import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F
LV=F.LEVEL_ORDER; X=list(range(len(LV)))
XLAB=[f"{l}\n{int(F.LEVELS[l][0])}/{F.LEVELS[l][1]:g}" for l in LV]
MC={"Raw":"#1f77b4","Patch":"#d62728"}
s=pd.read_csv(os.path.join(F.E1_OUT,"e1_coarse_init_summary.csv"))
fig,axes=plt.subplots(2,4,figsize=(15,6.2),sharex=True)
for j,tr in enumerate(F.TRAJS):
    a=axes[0,j]
    for m in ["Raw","Patch"]:
        g=s[(s.trajectory==tr)&(s.method==m)].set_index("level").reindex(LV)
        a.plot(X,g.captureB_rate.values,"-o",color=MC[m],lw=2.2,ms=6,label=m)
    a.set_ylim(-.03,1.03); a.set_title(tr+(" (secondary)" if tr=="III" else ""),fontsize=10); a.grid(alpha=.25)
    if j==0:a.set_ylabel("Fraction meeting error thresholds\n(e_t \u2264 50 mm, e_R \u2264 2\u00b0)",fontsize=9)
    if j==3:a.legend(fontsize=9,loc="upper right")
    b=axes[1,j]
    for m in ["Raw","Patch"]:
        g=s[(s.trajectory==tr)&(s.method==m)].set_index("level").reindex(LV)
        b.plot(X,g.et_med.values,"-o",color=MC[m],lw=2.2,ms=6,label=m)
        b.fill_between(X,g.et_p25.values,g.et_p75.values,color=MC[m],alpha=.12)
    b.set_xticks(X); b.set_xticklabels(XLAB,fontsize=8); b.grid(alpha=.25)
    if j==0:b.set_ylabel("Median final translation error (mm)\n(25th\u201375th percentile band)",fontsize=9)
fig.suptitle("Sensitivity to the tested initialization perturbations (up to 300 mm / 15\u00b0)",fontsize=11)
fig.tight_layout(rect=[0,0,1,0.96])
out=os.path.join(F.E1_OUT,"fig_e1_paper_composite.png")
fig.savefig(out,dpi=160); print("wrote",out)
