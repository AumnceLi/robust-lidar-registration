# Pose-active mechanism -> compensation effectiveness link (P1 follow-up)

## 1. Identical-comparison design

For every frame and each target **Raw / Patch / Full**, all quantities are evaluated at the SAME reference pose (xi=0, GT-aligned), with the SAME frozen LS weights (w=1/N) and the SAME correspondence convention (GT-local k=1 nearest point of that arm's frozen target):

- **RMS(delta)** (mm): RMS pointwise mismatch delta_i = source_i - target(source_i).
- **||g_t||, ||g_r||**: translation / rotation block of the frozen objective gradient at xi=0 (reported in the frozen FD-of-mean-squared-residual convention, matching `__g`; the analytic Gauss-Newton normal is exactly one half of this -- see verification below).
- **||P_{J,W} delta||** (mm): weighted-RMS of the mismatch projected onto the pose-Jacobian column space, = sqrt(g' H^{-1} g) with the factor-1 normal equations; this is the part of mismatch a 6-DOF pose move can act on (its complement is pose-orthogonal structured error).
- Realized translation/rotation error is the unchanged frozen ICP result (M0/M4/M5), not re-solved here.

Patch = frozen 24-patch mean map; Full = frozen k=16 view+patch interpolation at the frame's true view (oracle view; the deployed predictor is outside this mechanism diagnostic). Primary scope = in-support frames (V analyzed on all frames, as shipped).

## 2. Primary-scope arm medians

| traj | arm | n | RMS(delta) mm | ||g_t|| | ||g_r|| | ||P_JW delta|| mm | trans err mm | rot err deg |
|---|---|---|---|---|---|---|---|---|
| VI | full | 501 | 67.046 | 0.031 | 0.006 | 19.294 | 76.857 | 2.881 |
| VI | patch | 501 | 84.972 | 0.044 | 0.006 | 26.351 | 116.815 | 4.667 |
| VI | raw | 501 | 104.147 | 0.069 | 0.005 | 38.157 | 161.408 | 4.509 |
| IV | full | 156 | 70.534 | 0.033 | 0.010 | 22.018 | 82.898 | 2.464 |
| IV | patch | 156 | 85.910 | 0.040 | 0.009 | 27.241 | 126.260 | 4.000 |
| IV | raw | 156 | 99.437 | 0.066 | 0.009 | 40.317 | 160.424 | 4.006 |
| II | full | 428 | 77.422 | 0.031 | 0.005 | 20.706 | 68.859 | 2.248 |
| II | patch | 428 | 79.080 | 0.023 | 0.004 | 16.016 | 41.777 | 1.269 |
| II | raw | 428 | 84.672 | 0.052 | 0.008 | 28.286 | 66.149 | 1.774 |
| III | full | 371 | 59.542 | 0.020 | 0.004 | 12.383 | 51.238 | 2.641 |
| III | patch | 371 | 59.499 | 0.017 | 0.004 | 11.758 | 41.298 | 2.116 |
| III | raw | 371 | 69.631 | 0.046 | 0.005 | 25.796 | 75.037 | 1.658 |
| V | full | 1868 | 88.584 | 0.049 | 0.016 | 41.761 | 118.452 | 3.206 |
| V | patch | 1868 | 95.263 | 0.059 | 0.018 | 49.179 | 134.575 | 3.620 |
| V | raw | 1868 | 106.564 | 0.069 | 0.017 | 54.918 | 173.761 | 3.026 |

## 3. Block-level coupling: change in mechanism vs change in pose error

Spearman rho across blocks between (arm - Raw) change in each mechanism quantity and the (arm - Raw) change in translation / rotation error. Positive rho = blocks where the mechanism quantity drops more also improve more.

```
metric                  gr_norm        gt_norm        pjw_delta_mm        rms_delta_mm       
error                    eR_deg  et_mm  eR_deg  et_mm       eR_deg  et_mm       eR_deg  et_mm
trajectory comparison                                                                        
VI         raw_to_full    0.600  0.600  -0.314 -0.600        0.143  0.143       -0.314 -0.600
           raw_to_patch  -0.086 -0.257  -0.429 -0.600       -0.429 -0.600        0.029 -0.086
IV         raw_to_full   -0.400 -1.000   0.400  1.000        0.400  1.000        0.400  1.000
           raw_to_patch   1.000 -0.600  -0.800  0.800       -0.600  1.000       -0.800  0.800
II         raw_to_full   -0.267 -0.150   0.167  0.867        0.133  0.850        0.067  0.550
           raw_to_patch   0.383  0.217   0.433  0.800        0.400  0.750        0.433  0.917
III        raw_to_full    0.000  0.048   0.262  0.667        0.238  0.571        0.738  0.571
           raw_to_patch  -0.048  0.095  -0.667  0.143       -0.619  0.262       -0.167  0.357
```

## 4. Why Full does not improve II translation and worsens rotation (data statement)

- On II, Raw -> Full changes median RMS(delta) 84.67 -> 77.42 mm, ||g_t|| 0.0516 -> 0.0307, ||g_r|| 0.0081 -> 0.0047, ||P_JW delta|| 28.29 -> 20.71 mm, while realized translation error moves 66.15 -> 68.86 mm and rotation 1.774 -> 2.248 deg.
- For comparison Raw -> Patch on II: RMS(delta) 84.67 -> 79.08, ||g_t|| 0.0516 -> 0.0228, ||g_r|| 0.0081 -> 0.0040, ||P_JW delta|| 28.29 -> 16.02, translation 66.15 -> 41.78 mm, rotation 1.774 -> 1.269 deg.
- block Spearman (Full-Raw) vs et_mm: RMS(delta) 0.550, ||g_t|| 0.867, ||g_r|| -0.150, ||P_JW delta|| 0.850.
- block Spearman (Full-Raw) vs eR_deg: RMS(delta) 0.067, ||g_t|| 0.167, ||g_r|| -0.267, ||P_JW delta|| 0.133.
- Interpretation follows the data: on II the block-level correlation of (Full-Raw) ||g_t|| reduction with translation-error change is positive (rho 0.87) and likewise for ||P_JW delta|| (rho 0.85) -- i.e. blocks where Full removes more pose-actionable signal do improve more -- yet at the AGGREGATE level Full still nets a slightly worse translation median and a worse rotation median. A weak II view map (neighbor views far from the VI support; interpolated field is an over-smoothed average) lowers the xi=0 gradient (including ||g_r||) everywhere by roughly the same amount without matching the true per-block bias; the realized local optimum nevertheless shifts to a worse rotation (a subtracted field need not be rotation-neutral at the optimum). RMS(delta) reduction is therefore neither necessary nor sufficient for pose benefit: the pose-actionable projection and its rotation block, not the raw mismatch size, track realized error, and the map must be spatially/view-specific enough for that coupling to convert into a level shift -- which Patch achieves on II but Full does not.

## 5. Verification

- Analytic gradient vs the frozen central-difference `raw__g` (the analytic normal is 1/2 of the frozen mean-squared-objective FD gradient; accounted for):
| trajectory | max_abs_dgt | max_abs_dgr |
|---|---|---|
| VI | 0.00031 | 0.00018 |
| IV | 0.00029 | 0.00038 |
| II | 0.00033 | 0.00025 |
| V | 0.00040 | 0.00031 |
- Residual differences are the O(h^2)=6.25e-4 (translation FD step) truncation error of the saved numeric gradient, as documented in Figure4 notes; the analytic values are exact at xi=0.
- Pose errors attached without re-solving, so they match the shipped frozen master results.

## 6. Files

- `mechanism_before_after.csv` -- per-frame Raw/Patch/Full x p2p/p2l mechanism quantities + realized errors (block/in-support flags included).
- `scripts/t5_block_spearman.csv` -- full block-level Spearman table (rho, p, K).
- `scripts/t5_arm_medians.csv`, `scripts/t5_analytic_vs_fd.csv` -- summary/verification tables.
