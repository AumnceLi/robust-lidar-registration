# -*- coding: utf-8 -*-
"""Inspect all NPZ/CSV inputs for the THEORY shard (read-only)."""
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

import numpy as np
import pandas as pd
import os

print("=" * 70)
print("=== objective_main.npz ===")
d = np.load(_pp("structured_mismatch_phase0/scripts/cache/rescue/objective_main.npz"),
            allow_pickle=True)
for k in d.files:
    a = d[k]
    print(f"  {k:30s} shape={getattr(a,'shape',None)} dtype={getattr(a,'dtype',None)}")

print()
print("=== ext_objective_iv.npz ===")
di = np.load(_pp("structured_mismatch_phase0/scripts/cache/ext/ext_objective_iv.npz"),
             allow_pickle=True)
for k in di.files:
    a = di[k]
    print(f"  {k:30s} shape={getattr(a,'shape',None)} dtype={getattr(a,'dtype',None)}")

print()
print("=== ext_objective_v.npz ===")
dv = np.load(_pp("structured_mismatch_phase0/scripts/cache/ext/ext_objective_v.npz"),
             allow_pickle=True)
for k in dv.files:
    a = dv[k]
    print(f"  {k:30s} shape={getattr(a,'shape',None)} dtype={getattr(a,'dtype',None)}")

print()
print("=== ii ext_objective_ii.npz ===")
try:
    d2 = np.load(_pp("tj2_supplemental/cache/ii/ext_objective_ii.npz"), allow_pickle=True)
    for k in d2.files:
        a = d2[k]
        print(f"  {k:30s} shape={getattr(a,'shape',None)} dtype={getattr(a,'dtype',None)}")
except Exception as e:
    print("  ERROR:", e)

print()
print("=== G_GENERALITY CSVs ===")
base = _pp("g_chain/G_GENERALITY/results")
for fn in ["generality_summary.csv", "dose_response.csv", "geometry_results.csv"]:
    p = os.path.join(base, fn)
    if os.path.exists(p):
        df = pd.read_csv(p)
        print(f"  {fn}: shape={df.shape}, cols={list(df.columns)}")
        print(df.head(3).to_string())
        print()
    else:
        print(f"  {fn}: NOT FOUND at {p}")

print()
print("=== FROZEN predictor ===")
try:
    dp = np.load(_pp("structured_mismatch_phase0/scripts/cache/rescue/VI_ONLY_PREDICTOR_FROZEN.npz"),
                 allow_pickle=True)
    for k in dp.files:
        a = dp[k]
        print(f"  {k:20s} shape={getattr(a,'shape',None)} dtype={getattr(a,'dtype',None)}")
        if getattr(a, "shape", ()) == ():
            print(f"       value={a.item()}")
except Exception as e:
    print("  ERROR:", e)
