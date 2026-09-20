# -*- coding: utf-8 -*-
"""probe_rotpen.py -- locate the source of the stated Patch+Huber vs Huber rotation penalty
   (VI +0.421, IV +0.052, II +0.498, III +0.720) and identify the primary solver channel."""
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
ROOT = _pp("")
def paired(df, targ, comp, metric="eR_deg"):
    a = df[df.arm == targ].set_index(["trajectory", "order"])[metric]
    b = df[df.arm == comp].set_index(["trajectory", "order"])[metric]
    j = pd.concat([a.rename("t"), b.rename("c")], axis=1).dropna()
    return float(np.median(j["t"] - j["c"]))   # positive = target has MORE rotation error

arms = pd.read_csv(os.path.join(ROOT, "FOLLOWUP_6_9", "scripts", "replay79_arms.csv"))
print("=== replay79 (hardcoded p2p) paired median rotation PatchHuber-Huber, Patch-Raw ===")
for tr in ["VI", "IV", "II", "III"]:
    d = arms[arms.trajectory == tr]
    print(f"{tr}: PH-Hub={paired(d,'PatchHuber','Huber'):+.3f}  Patch-Raw={paired(d,'Patch','Raw'):+.3f}  "
          f"PH-Patch={paired(d,'PatchHuber','Patch'):+.3f}")

print("\n=== followup6 primary_method methods present ===")
f6 = pd.read_csv(os.path.join(ROOT, "FOLLOWUP_6_9", "followup6_primary_method_frame.csv"))
print(list(f6.columns)); print(f6.groupby(['trajectory','method']).size().unstack(fill_value=0))
# paired rotation delta in followup6 if rotation col exists
rcand = [c for c in f6.columns if 'rot' in c.lower() or 'eR' in c]
tcand = [c for c in f6.columns if 'trans' in c.lower() or 'et' in c.lower()]
print("rot col:", rcand, "trans col:", tcand)
if rcand:
    rc = rcand[0]
    pv = f6.pivot_table(index=["trajectory","order"], columns="method", values=rc)
    for tr in ["VI","IV","II","III"]:
        sub = pv.loc[tr].dropna() if tr in pv.index.get_level_values(0) else None
        if sub is not None and "PatchHuber" in sub and "Huber" in sub:
            print(f"{tr}: f6 PH-Hub rotation = {np.median(sub.PatchHuber-sub.Huber):+.3f}")
