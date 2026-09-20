# Figure 2 provenance and statistical definition (post-audit follow-up)

Mode: read-only lineage trace + independent re-derivation. No figure redrawn, no data re-generated, no frozen result modified.

## 1. Data lineage (oldest -> plotted)

1. `s1_residuals.py` computes, for every GT-aligned VI scan, the nearest-nominal-model distance `r`, signed normal residual `signed` and model-point patch label, cached in `structured_mismatch_phase0/scripts/cache/scans/scan_XXXX.npz`.
2. `s3_patches.py` aggregates to one row per (scan, patch=0..23): support_count, median_residual (m), mean_signed_residual, range_m -> `results/patch_persistence.csv` (501 scans x 24 patches = 12024 rows).
3. `FINAL_FIGURES/build_all_figures.py :: figure2()` filters support_count>0 & finite (kept 11209 cells), attaches the frozen VI orientation block, and builds panels A-E; plotted reductions are exported to FINAL_FIGURES/Figure2/*.csv.

## 2. Per-panel statistical definition

| Panel | What is drawn | Center line | Shaded region | Statistical unit |
|---|---|---|---|---|
| 2A | Orthographic projection of the frozen nominal model + patch ID labels | none (schematic scatter/annotation) | none | model point (schematic, no statistic) |
| 2B | Heatmap, rows = 6 frozen VI orientation blocks, cols = patch 0-23 | each cell = **median** of the per-scan patch-median residuals in that block (mm) | none (discrete heatmap, masked when no supported scan) | one supported (scan,patch) cell |
| 2C/D/E | Residual vs sensor range for patches [3, 20, 8] (largest patch per dominant normal family x/y/z, chosen without outcomes) | **median** within each range bin (mm) | **IQR = 25th-75th percentile** within the bin (NOT SD, NOT a CI, NOT a percentile fan beyond quartiles, no fitted curve) | one supported VI scan's patch-median residual for that patch |

- Range bins: **8 fixed equal-width** bins, edges = linspace(min,max,9) over ALL supported VI observations (identical edges for the three panels); x position = median sensor range in the bin.
- The statistical unit is the **scan-level** patch median (501 VI scans max), never a single lidar point and never a block; blocks appear only in panel B.
- Sample counts are small in some bins (see n below); IQR bands are descriptive and must not be read as independent confidence intervals (range and orientation covary on VI).

## 3. Per-curve sample counts (panels C-E)

| panel | patch_id | n_bins | n_total | n_min | n_max |
|---|---|---|---|---|---|
| 2C | 3 | 8 | 501 | 36 | 152 |
| 2D | 20 | 8 | 501 | 36 | 152 |
| 2E | 8 | 8 | 484 | 34 | 146 |

## 4. Independent re-derivation vs shipped plotted tables (verification)

- panels C-E: max |re-derived median - shipped| = 3.553e-15 mm; Q25 7.105e-15; Q75 1.421e-14; bin range-center 1.776e-15 m; per-bin count mismatch = 0.
- panel B heatmap: max |re-derived - shipped| = 1.421e-14 mm.
- Result: the shipped Figure-2 tables are reproduced exactly; the caption wording (median line, IQR shade, 8 equal-width bins, scan-level unit) matches the code.

## 5. Source hashes

- patch_persistence.csv: `ce16526f146922fa9d1ebe83a98d79ad9732443b76a00c923ed352e79535b572`
- patch_definition.csv: `e1aa5ead8317971f1ab23afbf71e333793bb044fc592ff37115fb1c6ad4d9973`

## 6. Caption-ready statement

> Panels C-E show, for one patch from each dominant normal family, the median (line) and 25th-75th-percentile IQR (shading) of the per-scan patch-median residual within eight fixed equal-width sensor-range bins; each observation is one supported VI scan (sample counts per bin are in figure2_plot_statistics.csv). The band is a descriptive IQR, not a standard deviation or confidence interval; no curve is fit and independence across bins is not assumed. Panel B cell colour is the median over scans within each frozen orientation block.
