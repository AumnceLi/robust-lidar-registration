# Task 1 — Direct paired Patch vs Global-Vector increment

**Verdict: `SPATIAL_INCREMENT_TRAJECTORY_DEPENDENT`.**

## Method (what makes this direct)

Per matched frame we pair the two frozen Exp.4 arms and form **d_t = e_t(GlobalVector) − e_t(Patch)** (positive = Patch has lower translation error). We do **not** subtract a Patch-vs-Raw marginal median from a Global-vs-Raw marginal median (that operation is invalid for an incremental claim). Frame values come from the frozen `exp4/dbs_vector_framewise.csv`; no registration was re-run. Blocks are JOINED from the canonical paper map `master_pose_results_frame.csv` (VI 6 / IV 4 / II 9 / III 8) and were not reconstructed. The block CI uses the manuscript block-unit convention (resample paper blocks with replacement, pool member frames, median; B=2000, seed 42, 2.5/97.5 percentiles). The paired p is the frozen one-sided block sign-flip permutation (`g_common.block_signflip_p`, B=2000, L=5, seed 42); a classical binomial sign test is **not** part of the frozen convention, so none was added. **III is post-hoc / secondary.**

## Direct paired result by trajectory

| traj   |   n |   med d_t |    IQR |   P(better) |   G(better) |   ties |   blocks |   med block eff |   CI lo |   CI hi |   blk+ |   blk− |   signflip p |
|:-------|----:|----------:|-------:|------------:|------------:|-------:|---------:|----------------:|--------:|--------:|-------:|-------:|-------------:|
| VI     | 501 |    33.917 | 18.504 |       1     |       0     |      0 |        6 |          33.701 |  26.691 |  43.555 |      6 |      0 |        0     |
| IV     | 156 |    19.31  |  9.725 |       0.981 |       0.019 |      0 |        4 |          17.838 |  12.086 |  24.211 |      4 |      0 |        0     |
| II     | 428 |     0.24  | 26.546 |       0.509 |       0.491 |      0 |        9 |          -1.635 |  -8.493 |  18.015 |      4 |      5 |        0.446 |
| III    | 371 |    25.035 | 17.11  |       0.881 |       0.119 |      0 |        8 |          22.767 |  15.809 |  30.358 |      7 |      1 |        0     |

## The II contrast that motivated this task (marginal vs direct)

On II the two MARGINAL medians make Patch look clearly better (median Patch − median Global = -9.39 mm). The DIRECT paired result is essentially zero: median d_t = +0.24 mm, Patch-better fraction 0.509 vs Global-better 0.491 (an even split), per-block effects split 4 positive / 5 negative, the block CI [-8.49, +18.02] CROSSES ZERO, and the sign-flip p = 0.446. On II, Patch therefore provides no demonstrable increment over the single constant historical vector.

## Trajectory-by-trajectory reading

- **VI**: median d_t +33.92 mm (IQR 18.50), Patch-better 1.000, blocks 6/6 positive, block CI [+26.69, +43.55] (excludes 0), sign-flip p 0.0005.
- **IV**: median d_t +19.31 mm (IQR 9.73), Patch-better 0.981, blocks 4/4 positive, block CI [+12.09, +24.21] (excludes 0), sign-flip p 0.0005.
- **II**: median d_t +0.24 mm (IQR 26.55), Patch-better 0.509, blocks 4/9 positive, block CI [-8.49, +18.02] (crosses 0), sign-flip p 0.4463.
- **III (post-hoc / secondary)**: median d_t +25.03 mm (IQR 17.11), Patch-better 0.881, blocks 7/8 positive, block CI [+15.81, +30.36] (excludes 0), sign-flip p 0.0005.

## Decision

Direct Patch-vs-Global evidence is clearly positive on **VI / IV** and on the post-hoc **III**, but on **II** it is weak and the block bootstrap interval crosses zero. Hence the increment of the spatial Patch over the simplest historical correction is **trajectory dependent**. The stronger sentence *“Patch clearly outperforms simple historical correction on all four trajectories”* is **not supported by the direct paired evidence and must not be retained**. State the spatial increment as robust on VI/IV (and the secondary III) and null/uncertain on II, where a single constant historical vector is already as good at the median once frames are paired.
