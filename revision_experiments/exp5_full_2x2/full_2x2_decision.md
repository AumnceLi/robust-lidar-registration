# Exp.5 — Minimal 2×2 ablation of Full

**Status: COMPLETE, validation exact.** A1 (current Patch) reproduces the frozen Patch arm to **2.84e-14 mm**; B2 (current Full) reproduces the frozen Full arm to **5.68e-14 mm**. Common in-support mask; 24 patches, k=16, adaptive Gaussian, range_std, history, solver/basin/tol all frozen. III is post-hoc / secondary.

## Design

| | point-weighted (Vcnt) | scan-weighted (equal per scan) |
|---|---|---|
| **all-history** | **A1 = Patch** | A2 |
| **view-neighbor k16** | B1 | **B2 = Full** |

## Median translation error (mm)

| trajectory   |   A1 Patch (all,pt) |   A2 (all,scan) |   B1 (view,pt) |   B2 Full (view,scan) |
|:-------------|--------------------:|----------------:|---------------:|----------------------:|
| VI           |              116.82 |          138.94 |          75.61 |                 76.86 |
| IV           |              126.26 |          142.16 |          83.09 |                 82.9  |
| II           |               41.78 |           53.2  |          68.88 |                 68.86 |
| III          |               41.3  |           49.07 |          51.15 |                 51.24 |

## Paired median factor effects (mm; positive = raises error)

| traj   |   view B1−A1 (pt-w) |   view B2−A2 (scan-w) |   weight A2−A1 (all) |   weight B2−B1 (view) |   Full−Patch B2−A1 |
|:-------|--------------------:|----------------------:|---------------------:|----------------------:|-------------------:|
| VI     |              -40.79 |                -62.2  |                22.09 |                  0.18 |             -39.74 |
| IV     |              -38.91 |                -54.04 |                14.73 |                 -0.28 |             -38.9  |
| II     |               22.67 |                 13.16 |                 5    |                  0.22 |              24.55 |
| III    |               17.63 |                  5.06 |                 9.98 |                  0.02 |              20.02 |

## Findings

1. **Full's cross-trajectory reversal tracks VIEW CONDITIONING, not aggregation weighting.** The view effect changes sign across trajectories at fixed weighting — B1−A1: VI -40.8, IV -38.9, II +22.7, III +17.6; B2−A2 shows the same sign flip. This is exactly Full's reversal pattern (B2−A1).

2. **Once view-conditioned, point- vs scan-weighting is irrelevant**: B2−B1 ≈ 0 on every trajectory (+0.18/-0.28/+0.22/+0.02 mm).

3. At fixed all-history, scan-weighting is only modestly and consistently worse than point-weighting (A2−A1 always positive, +5 to +22 mm) and **never changes sign across trajectories** — it cannot explain the reversal.

4. A1 (all-history point-weighted = current Patch) is the most robust cell across all four trajectories; adding view neighbors helps only on the VI-like regimes (VI/IV) and hurts on the shifted II/III.

## Decision

**FULL_REVERSAL_IS_VIEW_CONDITIONING.** Per instruction this is a mechanism ablation, NOT a search for a new best Full: no method is re-selected on III. The paper should attribute Full's trajectory dependence to view-neighbor conditioning (distribution shift between query views and the VI view library), and keep all-history Patch as the primary transferable field.
