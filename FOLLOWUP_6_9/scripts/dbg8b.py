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

import pandas as pd, numpy as np
c = pd.read_csv('../followup8_condition_summary.csv')
lit = 'D1_appendage_disp'
print('column pandas dtype:', c.dtype.dtype)
print('eq py-literal:', (c.dtype == lit).sum())
print('eq np.str_:', (c.dtype == np.str_(lit)).sum())
print('isin:', c.dtype.isin([lit]).sum())
# merge-style validation against phase map
pm = pd.read_csv(_pp("FINAL_TOPJOURNAL_HARDENING/OPTIONAL_PHASE_MAP/results_long.csv"))
pm = pm[pm.loss == 'ls']
print('pm dtype repr:', [(repr(x), len(x)) for x in pm.dtype.unique()])
m = c.merge(pm, left_on=['geometry', 'dtype', 'mag'], right_on=['geometry', 'dtype', 'dose'], how='inner')
print('merge rows:', len(m))
if len(m):
    print('alpha exact max diff:', (m.alpha_x - m.alpha_y).abs().max())
print(c.dtypes[['dtype','geometry','mag']])
