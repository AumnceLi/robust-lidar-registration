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

import numpy as np, pandas as pd, os
P = _pp("structured_mismatch_phase0/scripts/cache")
for nm, p in [('VI', os.path.join(P, 'scans', 'scan_0000.npz')),
              ('IV', os.path.join(P, 'ext', 'iv', 'scan_0000.npz')),
              ('II', _pp("tj2_supplemental/cache/ii/scan_0000.npz")),
              ('III', _pp("g_chain/G3_FINAL_CONFIRMATION/iii_cache/scan_0000.npz")),
              ('V', os.path.join(P, 'ext', 'v', 'scan_0000.npz'))]:
    z = np.load(p)
    print(nm, {k: z[k].shape for k in z.files})

om = np.load(os.path.join(P, 'rescue', 'objective_main.npz'))
print('objective_main keys:', om.files, {k: om[k].shape for k in om.files})
g1 = pd.read_csv(_pp("g_chain/G1_MITIGATION/results/g1_oracle_iv.csv"), nrows=8)
print('g1 cols:', list(g1.columns)); print(g1[['method','et_mm','eR_deg','iters','on_bound','wmean','nearest_d','ndist','in_support']].head(8).to_string())
g0 = pd.read_csv(_pp("g_chain/G0_ROBUST_FALSIFICATION/results/g0_frame_iv.csv"), nrows=8)
print('g0 cols:', list(g0.columns))
g3 = pd.read_csv(_pp("g_chain/G3_FINAL_CONFIRMATION/results/g1_iii.csv"), nrows=3)
print('g1_iii cols:', list(g3.columns))
# ext_predict v keys
v = np.load(os.path.join(P, 'ext', 'ext_predict_v.npz')); print('ext_predict_v:', v.files, {k: v[k].shape for k in v.files})
