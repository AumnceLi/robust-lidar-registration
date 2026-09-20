"""
Export audit CSVs for the 2026-09-17 redraw.

  figure2_heatmap_values.csv   -- 6 VI blocks x 24 patches: median residual + n
  figure2_range_bin_summary.csv -- per-patch per-bin edges, x-center, n, q25/med/q75
  figure6_run_count_audit.csv   -- unique configs / repeats / failures / safeguard
                                   and explanation of the 4000 vs 8000 figures
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

import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "figures", "redraw_20260917")
DER = os.path.join(ROOT, "data", "derived")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# Figure 2 heatmap values + per-cell n
# ---------------------------------------------------------------------------
d = np.load(os.path.join(DER, "figure2_residual_stats.npz"), allow_pickle=True)
block_patch = d["block_patch_med"]      # (6,24)
frame_patch = d["frame_patch_med"]      # (501,24)
blocks = d["blocks"]                    # (501,)

# n per (block, patch) = number of non-missing scan-level medians
n_mat = np.full_like(block_patch, 0, dtype=int)
for b in range(6):
    m = blocks == b
    for j in range(24):
        vals = frame_patch[m, j]
        n_mat[b, j] = int(np.sum(~np.isnan(vals)))

rows = []
for b in range(6):
    for j in range(24):
        rows.append({
            "vi_block": b,
            "patch_id": j,
            "median_residual_mm": round(float(block_patch[b, j]), 4),
            "n_scans": int(n_mat[b, j]),
        })
pd.DataFrame(rows).to_csv(os.path.join(OUT, "figure2_heatmap_values.csv"),
                          index=False)
print(f"heatmap CSV: {len(rows)} cells; total n scan-patch = {n_mat.sum()}")

# ---------------------------------------------------------------------------
# Figure 2 range-bin summary
# ---------------------------------------------------------------------------
edges = d["bin_edges"]
rows = []
for p in [3, 20, 8]:
    meds = d[f"bin_median_{p}"]
    q25 = d[f"bin_iqr_low_{p}"]
    q75 = d[f"bin_iqr_high_{p}"]
    cnt = d[f"bin_count_{p}"]
    for k in range(8):
        rows.append({
            "patch_id": p,
            "bin_index": k,
            "range_low_m": round(float(edges[k]), 4),
            "range_high_m": round(float(edges[k+1]), 4),
            "range_center_m": round(float((edges[k]+edges[k+1])/2), 4),
            "n_observations": int(cnt[k]),
            "q25_mm": None if np.isnan(q25[k]) else round(float(q25[k]), 3),
            "median_mm": None if np.isnan(meds[k]) else round(float(meds[k]), 3),
            "q75_mm": None if np.isnan(q75[k]) else round(float(q75[k]), 3),
            "residual_unit": "mm",
        })
pd.DataFrame(rows).to_csv(os.path.join(OUT, "figure2_range_bin_summary.csv"),
                         index=False)
print(f"range-bin CSV: {len(rows)} rows (3 patches x 8 bins)")

# ---------------------------------------------------------------------------
# Figure 6 run-count audit
# ---------------------------------------------------------------------------
fw = pd.read_csv(_pp("final_three_experiments/01_coarse_initialization/e1_coarse_init_framewise.csv"))
# All 4 methods present in the framewise file
all_methods = sorted(fw.method.unique().tolist())
n_rows = len(fw)

# Unique configs: (trajectory, frame_id, method, level, direction)
unique_all = fw[["trajectory","frame_id","method","perturbation_level","direction_id"]].drop_duplicates()
unique_raw_patch = unique_all[unique_all.method.isin(["Raw","Patch"])]

# L0 has direction 'none' (1 per frame); nonzero have v1..v4 (4 per frame)
l0 = fw[fw.perturbation_level=="L0"]
nz = fw[fw.perturbation_level!="L0"]

# Repeats: same key appearing more than once
key_cols = ["trajectory","frame_id","method","perturbation_level","direction_id"]
dup_counts = fw.groupby(key_cols).size()
n_dup_keys = int((dup_counts > 1).sum())
n_dup_rows = int((dup_counts[dup_counts>1] - 1).sum())

# Failures / safeguards
n_safeguard = int(fw.safeguard.sum())
n_numfail = int(fw.numerical_failure.sum())
n_solverinvalid = int((fw.solver_valid==0).sum())

# Per-method row counts
per_method = fw.groupby("method").size().to_dict()
per_traj_method_level = fw.groupby(["trajectory","method","perturbation_level"]).size().reset_index(name="n")

audit_rows = [
    ("total_rows_in_framewise_csv", n_rows,
     "Every row = one run (one frame x method x level x direction)."),
    ("methods_present", ", ".join(all_methods),
     "Raw, Huber, Patch, PatchHuber."),
    ("rows_Raw_Patch_only", int(fw.method.isin(['Raw','Patch']).sum()),
     "Subset used by the redrawn Figure 6."),
    ("unique_configs_all_methods", len(unique_all),
     "4 traj x 20 frames x (1 L0 + 6 levels x 4 dirs) x 4 methods = 4000 per 2 methods; x4 methods = 8000 rows."),
    ("unique_configs_Raw_Patch", len(unique_raw_patch),
     "Matches the user's 4000 formula (2 methods)."),
    ("l0_rows", len(l0), "L0: direction 'none', 20 frames x 4 methods x 4 traj = 320."),
    ("nonzero_rows", len(nz), "L1-L6: 4 directions per frame."),
    ("duplicate_keys_extra_rows", n_dup_rows,
     "Extra rows beyond one per unique key (technical repeats)."),
    ("safeguard_runs", n_safeguard,
     "Runs that hit the safeguard fallback; still carry valid finite errors and are included in medians/IQR."),
    ("numerical_failure_runs", n_numfail,
     "Runs flagged numerical failure (0 in this dataset)."),
    ("solver_invalid_runs", n_solverinvalid,
     "solver_valid==0 coincides with safeguard=1 here; excluded from error medians? No -- finite errors retained."),
    ("explanation_of_8000",
     "8000 rows = 4 traj x 20 frames x 25 level-direction combos x 4 methods. "
     "The 4000 figure = same with only Raw+Patch. '8000 evaluation cases' in the text "
     "therefore counts all four arms (Raw/Huber/Patch/PatchHuber), not technical repeats. "
     "The redrawn Figure 6 uses only Raw and Patch (4000 runs), 20 unique at L0 and 80 at "
     "each nonzero level per method and trajectory.",
     ""),
]
with open(os.path.join(OUT, "figure6_run_count_audit.csv"), "w", newline="", encoding="utf-8") as f:
    f.write("item,value,note\n")
    for k, v, note in audit_rows:
        note = note.replace('"', "'").replace("\n", " ")
        f.write(f'"{k}","{v}","{note}"\n')
    f.write("\n")
    f.write("per_method_row_count\n")
    for m, c in per_method.items():
        f.write(f"{m},{c}\n")

# safeguard breakdown table
saf = fw[fw.safeguard==1].groupby(["trajectory","method","perturbation_level"]).size().reset_index(name="safeguard_runs")
saf.to_csv(os.path.join(OUT, "figure6_safeguard_breakdown.csv"), index=False)

print(f"audit CSV written; safeguard total = {n_safeguard}")
print(f"per-method rows: {per_method}")
