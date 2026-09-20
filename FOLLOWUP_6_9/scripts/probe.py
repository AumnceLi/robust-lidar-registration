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

def keys(p):
    z = np.load(p)
    return {k: (z[k].shape, str(z[k].dtype)) for k in z.files}

for f in [r'ext\ext_predict_iv.npz', r'ext\ext_objective_iv.npz']:
    print('###', f)
    for k, v in keys(os.path.join(P, f)).items():
        print('   ', k, v)

iii = _pp("g_chain/G3_FINAL_CONFIRMATION/iii_cache/ext_predict_iii.npz")
print('### iii pred')
for k, v in keys(iii).items():
    print('   ', k, v)

ii = _pp("tj2_supplemental/cache/ii/ext_predict_ii.npz")
print('### ii pred')
for k, v in keys(ii).items():
    print('   ', k, v)

F = np.load(os.path.join(P, 'rescue', 'VI_ONLY_PREDICTOR_FROZEN.npz'))
print('### FROZEN predictor')
for k in F.files:
    print('   ', k, F[k].shape, F[k].dtype)
print('    alpha_VI', float(F['alpha_VI']) if 'alpha_VI' in F.files else 'NA')

mc = np.load(os.path.join(P, 'model_cache.npz'))
print('### model_cache', mc.files, {k: mc[k].shape for k in mc.files})
pa = np.load(os.path.join(P, 'patches.npz'))
print('### patches', {k: pa[k].shape for k in pa.files})

miv = pd.read_csv(os.path.join(P, 'ext', 'meta_iv.csv'))
print('### meta_iv cols:', list(miv.columns), 'n=', len(miv))
m3 = pd.read_csv(_pp("g_chain/G3_FINAL_CONFIRMATION/iii_cache/meta_iii.csv"))
print('### meta_iii cols:', list(m3.columns), 'n=', len(m3))

gr = pd.read_csv(_pp("g_chain/G_GENERALITY/results/geometry_results.csv"))
print('### geometry_results cols:', list(gr.columns), 'n=', len(gr))
print('   dtypes:', sorted(gr.dtype.unique()) if hasattr(gr.dtype,'unique') else '')
for c in ['dtype','geometry','amp','rep']:
    if c in gr.columns:
        u = gr[c].unique()
        print('   uniq', c, len(u), u[:12])
print(gr.head(3).to_string())

fp = _pp("POSE_AUDIT/audit/frozen_equal_rms_pairs.csv")
if os.path.exists(fp):
    e = pd.read_csv(fp)
    print('### frozen_equal_rms_pairs cols:', list(e.columns), 'n=', len(e))
    print(e.head(4).to_string())
