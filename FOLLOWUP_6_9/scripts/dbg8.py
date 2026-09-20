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

import pandas as pd
c = pd.read_csv('../followup8_condition_summary.csv')
pm = pd.read_csv(_pp("FINAL_TOPJOURNAL_HARDENING/OPTIONAL_PHASE_MAP/results_long.csv"))
pm = pm[pm.loss == 'ls']
print('cond dtype repr:', [repr(x) for x in sorted(c.dtype.unique())])
print('pm   dtype repr:', [repr(x) for x in sorted(pm.dtype.unique())])
print('cond D1 mags', sorted(c[c.dtype == 'D1_appendage_disp'].mag.unique()))
print(pm[['geometry', 'dtype', 'dose']].drop_duplicates().to_string())
r = pm.iloc[0]
print('probe:', repr(r.geometry), repr(r.dtype), r.dose)
print('geom eq', (c.geometry == r.geometry).sum(), 'dtype eq', (c.dtype == r.dtype).sum(),
      'mag eq', (c.mag == r.dose).sum())
q = c[(c.geometry == r.geometry) & (c.dtype == r.dtype) & (c.mag == r.dose)]
print(q.to_string())
v = c.dtype.dropna().iloc[1]
print('value repr', repr(v), 'len', len(v), [ord(ch) for ch in v[:6]])
print('contains', c.dtype.str.contains('D1_appendage_disp').sum())
print('lens', c.dtype.str.len().value_counts().to_dict())
w = pm.dtype.iloc[0]; print('pm value repr', repr(w), 'len', len(w), [ord(ch) for ch in w[:6]])
print('eq direct', (v == w), type(v), type(w))
print('strip eq', (c.dtype.str.strip() == w.strip()).sum())
