"""
verify_all_v2.py — Consistency checks for V2 derived data.
Compares recomputed Figure 2 bin stats against V1 reference CSVs.
Tolerance: 0.5 mm.
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

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs"))
import numpy as np
from paths import DATA_DERIVED_DIR

V1_CSV_DIR = _pp("figure_redesign_20260913/data/derived")
TOL_MM = 0.5

print("=" * 60)
print("V2 Derived Data Verification")
print("=" * 60)

# ── Load V2 derived ──────────────────────────────────────────────────────
v2 = np.load(os.path.join(DATA_DERIVED_DIR, "figure2_residual_stats.npz"),
             allow_pickle=True)

# ── Check bin medians against V1 ────────────────────────────────────────
TARGET = {
    3: os.path.join(V1_CSV_DIR, "figure2_bin_stats_patch3.csv"),
    20: os.path.join(V1_CSV_DIR, "figure2_bin_stats_patch20.csv"),
    8: os.path.join(V1_CSV_DIR, "figure2_bin_stats_patch8.csv"),
}

all_pass = True
for p, csv_path in TARGET.items():
    # Read V1 CSV: columns = bin_lo_m, bin_hi_m, n, q25_mm, median_mm, q75_mm
    v1_data = np.genfromtxt(csv_path, delimiter=",", skip_header=1)
    v1_med = v1_data[:, 4]   # median_mm column
    v1_q25 = v1_data[:, 3]
    v1_q75 = v1_data[:, 5]
    v1_n = v1_data[:, 2].astype(int)

    v2_med = v2[f"bin_median_{p}"]
    v2_q25 = v2[f"bin_iqr_low_{p}"]
    v2_q75 = v2[f"bin_iqr_high_{p}"]
    v2_n = v2[f"bin_count_{p}"]

    # Compare
    med_diff = np.abs(v2_med - v1_med)
    n_match = np.array_equal(v2_n, v1_n)

    print(f"\nPatch {p}:")
    print(f"  n per bin match: {n_match}  (V2={v2_n}, V1={v1_n})")
    print(f"  median diff max: {np.nanmax(med_diff):.4f} mm (tol={TOL_MM})")
    print(f"  V2 medians: {np.round(v2_med, 2)}")
    print(f"  V1 medians: {np.round(v1_med, 2)}")

    if np.nanmax(med_diff) > TOL_MM:
        print(f"  FAIL: median diff exceeds tolerance!")
        all_pass = False
    if not n_match:
        print(f"  FAIL: bin counts don't match!")
        all_pass = False

# ── Check bin edges ──────────────────────────────────────────────────────
v1_edges = np.genfromtxt(TARGET[3], delimiter=",", skip_header=1)
v1_edge_lo = v1_edges[0, 0]   # bin_lo_m of first row
v1_edge_hi = v1_edges[-1, 1]  # bin_hi_m of last row
v2_edges = v2["bin_edges"]
print(f"\nBin edges: V2=[{v2_edges[0]:.4f}, {v2_edges[-1]:.4f}], "
      f"V1=[{v1_edge_lo:.4f}, {v1_edge_hi:.4f}]")
if abs(v2_edges[0] - v1_edge_lo) > 0.01 or abs(v2_edges[-1] - v1_edge_hi) > 0.01:
    print("  FAIL: bin edges don't match V1!")
    all_pass = False
else:
    print("  OK: bin edges match V1")

# ── Check frame counts ───────────────────────────────────────────────────
print(f"\nFrame counts:")
print(f"  patch3: n={v2['n_frames_patch3']} (expected 501)")
print(f"  patch20: n={v2['n_frames_patch20']} (expected 501)")
print(f"  patch8: n={v2['n_frames_patch8']} (expected 484)")

# ── Check heatmap shape ─────────────────────────────────────────────────
print(f"\nHeatmap shape: {v2['block_patch_med'].shape} (expected (6, 24))")
if v2["block_patch_med"].shape != (6, 24):
    print("  FAIL: wrong heatmap shape!")
    all_pass = False

# ── Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if all_pass:
    print("ALL CHECKS PASSED ✓")
else:
    print("SOME CHECKS FAILED ✗")
print("=" * 60)
