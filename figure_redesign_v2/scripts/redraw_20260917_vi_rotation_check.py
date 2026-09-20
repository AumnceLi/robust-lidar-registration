"""VI L5/L6 rotation distribution check (2026-09-17 second-round)."""
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

import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "figures", "redraw_20260917")
df = pd.read_csv(_pp("final_three_experiments/01_coarse_initialization/e1_coarse_init_framewise.csv"))
vi = df[(df.trajectory=="VI") & (df.method.isin(["Raw","Patch"]))].copy()

rows=[]
for lvl in ["L5","L6"]:
    for m in ["Raw","Patch"]:
        s = vi[(vi.perturbation_level==lvl)&(vi.method==m)]["final_rotation_error_deg"]
        rows.append({
            "trajectory":"VI","level":lvl,"method":m,
            "unique_runs":len(s),
            "q25_deg":round(s.quantile(.25),3),
            "median_deg":round(s.median(),3),
            "q75_deg":round(s.quantile(.75),3),
            "p90_deg":round(s.quantile(.90),3),
            "max_deg":round(s.max(),3),
            "safeguard_runs":int(vi[(vi.perturbation_level==lvl)&(vi.method==m)].safeguard.sum()),
            "hit_rotation_boundary":int(vi[(vi.perturbation_level==lvl)&(vi.method==m)].hit_rotation_boundary.sum()),
            "numerical_failure":int(vi[(vi.perturbation_level==lvl)&(vi.method==m)].numerical_failure.sum()),
            "runs_at_15deg_cap":int((s>=14.99).sum()),
        })
pd.DataFrame(rows).to_csv(os.path.join(OUT,"vi_L5L6_rotation_check.csv"),index=False)
for r in rows: print(r)
