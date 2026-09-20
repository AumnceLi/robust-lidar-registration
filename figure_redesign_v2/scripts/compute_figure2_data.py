"""
Recompute Figure 2 derived data with CORRECT residual definition.
Per task spec + V1: residual = ||aligned - model[nnidx]|| (3D norm, mm).
NOT |signed| (which is only the normal projection).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs"))

import numpy as np
from paths import SRC, DATA_DERIVED_DIR

os.makedirs(DATA_DERIVED_DIR, exist_ok=True)

# ── Load static data ──────────────────────────────────────────────────────
print("Loading model...")
m = np.load(SRC["model_cache"], allow_pickle=True)
xyz = m["xyz"].astype(np.float64)  # (67870, 3) meters

_patches = np.load(SRC["patches"], allow_pickle=True)
PLAB = _patches["lab"]  # (67870,) int16

_frozen = np.load(SRC["frozen_field"], allow_pickle=True)
blocks = _frozen["blocks"]  # (501,)
vrange = _frozen["vrange"]  # (501,) meters
N_PATCH = 24
N_FRAMES = 501

# ── Compute per-frame per-patch median 3D residual norm ──────────────────
frame_patch_med = np.full((N_FRAMES, N_PATCH), np.nan, dtype=np.float64)

scan_dir = SRC["scan_dir_vi"]
print(f"Scanning {N_FRAMES} frames...")

for fi in range(N_FRAMES):
    spath = os.path.join(scan_dir, f"scan_{fi:04d}.npz")
    s = np.load(spath, allow_pickle=True)
    aligned = s["aligned"].astype(np.float64)  # (N, 3)
    nnidx = s["nnidx"].astype(int)               # (N,)

    # Assign points to patches via nearest model point
    scan_patch = PLAB[nnidx]  # (N,)

    # 3D Euclidean residual norm -> mm
    d = np.linalg.norm(aligned - xyz[nnidx], axis=1) * 1000.0

    for j in range(N_PATCH):
        mask = scan_patch == j
        if np.any(mask):
            frame_patch_med[fi, j] = np.median(d[mask])

    if (fi + 1) % 100 == 0:
        print(f"  {fi+1}/{N_FRAMES} frames")

# ── Block-level heatmap: 6 blocks x 24 patches ──────────────────────────
N_BLOCKS = 6
block_patch_med = np.full((N_BLOCKS, N_PATCH), np.nan, dtype=np.float64)
for b in range(N_BLOCKS):
    frame_mask = blocks == b
    for j in range(N_PATCH):
        vals = frame_patch_med[frame_mask, j]
        vals = vals[~np.isnan(vals)]
        if len(vals) > 0:
            block_patch_med[b, j] = np.median(vals)

# ── Bin stats for patches 3, 20, 8 (by vrange) ───────────────────────────
edges = np.linspace(vrange.min(), vrange.max(), 9)
TARGET_PATCHES = [3, 20, 8]
results = {}

for p in TARGET_PATCHES:
    obs = ~np.isnan(frame_patch_med[:, p])
    x = vrange[obs]
    y = frame_patch_med[obs, p]
    dig = np.digitize(x, edges) - 1
    dig = np.clip(dig, 0, 7)

    meds = np.full(8, np.nan)
    q25 = np.full(8, np.nan)
    q75 = np.full(8, np.nan)
    cnts = np.zeros(8, dtype=int)

    for k in range(8):
        msk = dig == k
        vals = y[msk]
        cnts[k] = len(vals)
        if len(vals) > 0:
            meds[k] = np.median(vals)
            q25[k] = np.percentile(vals, 25)
            q75[k] = np.percentile(vals, 75)

    results[p] = {"med": meds, "q25": q25, "q75": q75, "n": cnts}
    print(f"\nPatch {p}: n={cnts}, total={cnts.sum()}")
    print(f"  medians: {np.round(meds, 2)}")
    print(f"  q25:     {np.round(q25, 2)}")
    print(f"  q75:     {np.round(q75, 2)}")

# ── Save ─────────────────────────────────────────────────────────────────
out_path = os.path.join(DATA_DERIVED_DIR, "figure2_residual_stats.npz")
np.savez_compressed(
    out_path,
    block_patch_med=block_patch_med,
    frame_patch_med=frame_patch_med,
    blocks=blocks,
    vrange=vrange,
    # Bin edges (shared across patches)
    bin_edges=edges,
    # Patch 3
    bin_median_3=results[3]["med"],
    bin_iqr_low_3=results[3]["q25"],
    bin_iqr_high_3=results[3]["q75"],
    bin_count_3=results[3]["n"],
    # Patch 20
    bin_median_20=results[20]["med"],
    bin_iqr_low_20=results[20]["q25"],
    bin_iqr_high_20=results[20]["q75"],
    bin_count_20=results[20]["n"],
    # Patch 8
    bin_median_8=results[8]["med"],
    bin_iqr_low_8=results[8]["q25"],
    bin_iqr_high_8=results[8]["q75"],
    bin_count_8=results[8]["n"],
    # Frame counts
    n_frames_patch3=int(np.sum(~np.isnan(frame_patch_med[:, 3]))),
    n_frames_patch20=int(np.sum(~np.isnan(frame_patch_med[:, 20]))),
    n_frames_patch8=int(np.sum(~np.isnan(frame_patch_med[:, 8]))),
)
print(f"\nSaved: {out_path}")
