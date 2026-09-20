# Figure 2 Data Provenance

## Overview
Figure 2 visualizes the residual structure of the VI (development/calibration) trajectory.
All numbers in the figure are computed by `scripts/compute_figure2_data.py` from frozen source data.
No values are hand-entered.

---

## X-axis: Sensor range (m)

| Field | Value |
|-------|-------|
| Source file | `D:\doubao\structured_mismatch_phase0\scripts\cache\rescue\VI_ONLY_PREDICTOR_FROZEN.npz` |
| Array key | `vrange` |
| Shape | (501,) float64 |
| Unit | metres (m) |
| Description | Sensor view distance to target center for each VI frame |
| Min | 8.7465 m |
| Median | ~12.4 m |
| Max | 14.8022 m |
| Valid frames | 501 (all) |

**Note**: The earlier (round 1–2) version of this figure incorrectly used the per-point `r` field from scan files (range 0.0002–0.65 m) and pooled all points across all frames. That version is **deprecated and removed**. The correct x-axis is the frame-level `vrange` from the frozen predictor, range 8.7465–14.8022 m.

---

## Residual magnitude

| Field | Value |
|-------|-------|
| Source files | `model_cache.npz` (xyz), `scans\scan_####.npz` (aligned, nnidx) |
| Definition | `‖aligned[i] − xyz[nnidx[i]]‖` — 3D Euclidean distance between each aligned scan point and its nearest nominal model point |
| Unit | millimetres (mm) (metres × 1000) |
| Per-frame per-patch statistic | median of per-point residual magnitudes within each patch |
| Aggregation | median across frames within each bin (or block for heatmap) |
| NOT used | `|signed|` (normal-projection residual only) — this was the round-1 bug |

---

## 8 Fixed Bin Edges

Computed as `np.linspace(vrange.min(), vrange.max(), 9)`:

| Bin | lo (m) | hi (m) | center (m) |
|-----|--------|--------|------------|
| 0 | 8.7465 | 9.5035 | 9.1250 |
| 1 | 9.5035 | 10.2604 | 9.8820 |
| 2 | 10.2604 | 11.0174 | 10.6389 |
| 3 | 11.0174 | 11.7744 | 11.3959 |
| 4 | 11.7744 | 12.5313 | 12.1529 |
| 5 | 12.5313 | 13.2883 | 12.9098 |
| 6 | 13.2883 | 14.0453 | 13.6668 |
| 7 | 14.0453 | 14.8022 | 14.4238 |

---

## Per-Patch Bin Statistics (mm)

### Patch 3 (teal #2C8C7E, n=501 frames)
| Bin | n | Q25 | Median | Q75 |
|-----|---|-----|--------|-----|
| 0 | 39 | 28.97 | 30.06 | 31.68 |
| 1 | 96 | 29.89 | 31.62 | 33.34 |
| 2 | 52 | 30.14 | 31.61 | 32.96 |
| 3 | 45 | 28.70 | 29.78 | 31.91 |
| 4 | 42 | 28.71 | 30.28 | 31.21 |
| 5 | 39 | 26.27 | 27.95 | 29.06 |
| 6 | 36 | 26.30 | 27.41 | 28.84 |
| 7 | 152 | 25.44 | 26.67 | 28.12 |

### Patch 20 (blue #386CB0, n=501 frames)
| Bin | n | Q25 | Median | Q75 |
|-----|---|-----|--------|-----|
| 0 | 39 | 37.34 | 63.59 | 83.58 |
| 1 | 96 | 33.39 | 41.78 | 79.85 |
| 2 | 52 | 33.30 | 41.54 | 81.89 |
| 3 | 45 | 38.93 | 64.75 | 96.67 |
| 4 | 42 | 30.42 | 42.03 | 84.74 |
| 5 | 39 | 30.52 | 58.28 | 80.05 |
| 6 | 36 | 28.97 | 61.04 | 74.85 |
| 7 | 152 | 25.54 | 47.44 | 71.77 |

### Patch 8 (warm orange #C97A40, n=484 frames)
| Bin | n | Q25 | Median | Q75 |
|-----|---|-----|--------|-----|
| 0 | 39 | 48.54 | 79.27 | 110.73 |
| 1 | 93 | 42.73 | 74.09 | 108.74 |
| 2 | 50 | 51.53 | 90.17 | 129.61 |
| 3 | 43 | 48.02 | 103.01 | 129.82 |
| 4 | 42 | 65.38 | 89.27 | 122.99 |
| 5 | 37 | 40.92 | 82.42 | 117.76 |
| 6 | 34 | 33.95 | 63.47 | 90.93 |
| 7 | 146 | 38.55 | 66.44 | 103.76 |

---

## Patch Assignment Consistency

| Item | Value |
|------|-------|
| Source | `patches.npz`, key `lab`, shape (67870,) int16 |
| Mapping | `scan_patch = patches.lab[scan.nnidx]` — each scan point's patch = patch of its nearest nominal model point |
| Scan `lab` field | Visibility tag {0,1,2,4}, NOT used for patch assignment |
| Consistency | Verified: 24 patch IDs (0–23), counts match `patches.count` |

---

## Heatmap Block Order

| Item | Value |
|------|-------|
| Source | `VI_ONLY_PREDICTOR_FROZEN.npz`, key `blocks` |
| Shape | (501,) int64 |
| Values | 0, 1, 2, 3, 4, 5 |
| Frame counts per block | [70, 70, 79, 96, 103, 83] |
| Heatmap rows | Bottom = block 0, top = block 5 (origin="lower") |
| Heatmap columns | Patch IDs 0–23 left to right |

---

## Deprecated Version Note

Reviewers may have seen an earlier version of this figure with x-axis 0–0.6 m and residual magnitudes up to 300–400 mm. That version incorrectly:
1. Used per-point sensor range (`scan['r']`) instead of frame-level `vrange`
2. Pooled all ~400K per-point residuals across 501 frames
3. Used `|signed|` (normal projection) instead of 3D Euclidean norm

That version has been removed. All values above are from the corrected pipeline.
