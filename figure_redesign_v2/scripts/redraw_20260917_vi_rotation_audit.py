"""
figure6_VI_rotation_audit.csv -- detailed VI L5/L6 rotation distribution audit.

All values read directly from e1_coarse_init_framewise.csv; no recomputation
from poses (the CSV already stores final_rotation_error_deg in degrees).
"""
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

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "figures", "redraw_20260917")
df = pd.read_csv(_pp("final_three_experiments/01_coarse_initialization/e1_coarse_init_framewise.csv"))

# Unit check: rotation_init_deg spans 0..15 deg; final_rotation_error_deg spans
# 1.7..15 deg. Both columns are already in degrees (no rad field present), so
# there is no rad->deg double conversion.
vi = df[(df.trajectory == "VI") & (df.method.isin(["Raw", "Patch"]))].copy()

# Verify Raw and Patch use identical frame x direction configs
key = ["frame_id", "perturbation_level", "direction_id"]
raw_keys = set(map(tuple, vi[vi.method == "Raw"][key].values))
patch_keys = set(map(tuple, vi[vi.method == "Patch"][key].values))
assert raw_keys == patch_keys, "Raw/Patch frame-direction sets differ!"

# Duplicate-key check within each method (frame x level x direction must be unique)
dup = vi.groupby(["method"] + key).size()
n_dup_extra = int((dup > 1).sum())

rows = []
for lvl in ["L5", "L6"]:
    for m in ["Raw", "Patch"]:
        s = vi[(vi.perturbation_level == lvl) & (vi.method == m)]
        rot = s["final_rotation_error_deg"]
        n_total = len(s)
        n_valid = int(np.isfinite(rot).sum())
        n_invalid = n_total - n_valid
        n_unique_frames = int(s.frame_id.nunique())
        rows.append({
            "trajectory": "VI",
            "level": lvl,
            "method": m,
            "n_unique_frames": n_unique_frames,
            "n_runs_total": n_total,
            "n_runs_valid": n_valid,
            "n_runs_missing_or_invalid": n_invalid,
            "q25_deg": round(float(rot.quantile(0.25)), 3),
            "median_deg": round(float(rot.median()), 3),
            "q75_deg": round(float(rot.quantile(0.75)), 3),
            "p90_deg": round(float(rot.quantile(0.90)), 3),
            "max_deg": round(float(rot.max()), 3),
            "safeguard_runs": int(s.safeguard.sum()),
            "hit_rotation_boundary": int(s.hit_rotation_boundary.sum()),
            "numerical_failure": int(s.numerical_failure.sum()),
            "runs_at_15deg_cap": int((rot >= 14.99).sum()),
        })
out = pd.DataFrame(rows)
out.to_csv(os.path.join(OUT, "figure6_VI_rotation_audit.csv"), index=False)
print(out.to_string(index=False))
print(f"\nRaw/Patch frame-direction keys identical: {raw_keys == patch_keys}")
print(f"Duplicate extra runs (VI Raw+Patch): {n_dup_extra}")
print("Units: degrees (rotation_init_deg max=15, final error max=15.0; no rad field)")
print("IQR bands in Figure 6 use q25/q75 from this same groupby, no min/max or SE.")
