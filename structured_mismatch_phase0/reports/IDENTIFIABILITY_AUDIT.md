# IDENTIFIABILITY AUDIT — EPOS-Lid Trajectory VI (Structured Model Mismatch, Phase 0)

**Scope:** VI only, 501 scans, GT-aligned residuals, no learned methods, no new downloads.
**Date:** 2026-09-09. **Reproduce:** run `scripts/s0_common.py → s1 → s3 → s4 → s5 → s6 sample → s7 → s8 → s9` in order.
**Evidence labels:** `[computed]` = produced by code in this run on VI; `[verified-file]` = read from dataset files/README; `[paper/spec-claim]` = external claim not re-derivable here.

---

## 1. Coordinate-contract re-verification and transform derivation

From `epos_README.txt` `[verified-file]`:
- `.3d`: ASCII `x y z` [m], **lidar frame** (only `target_model.3d` is in target frame).
- `.pose` line 2 = position of the **target in the lidar frame** = `t`; line 3 = scalar-first Hamilton quaternion for the rotation **target → lidar** = `R`. Pose anchors the **scan-end** instant.

Therefore, with `R = quat_to_R(q)`:
```
P_lidar = R · P_target + t                    (README forward model)
=> P_target = R^T · (P_lidar − t)             (GT alignment used for every residual)
```
Runtime checks `[computed]`:
- poses 0000/0250/0500 give ‖t‖ = 14.788 / 12.095 / 8.747 m (contract said 14.79→12.09→8.75) ✓
- scan-0000 raw centroid direction = (1.000, −0.006, 0.004): the lidar optical axis is **+X in these files** (not +Z); FOV geometry below uses +X.
- angular rate from consecutive GT poses: mean **7.94 °/s**, median 8.15 °/s (contract ≈ 8 °/s) ✓; trajectory duration 494.08 s, mean dt 0.988 s.
- The forward/inverse convention was validated by the residual magnitudes: applying `R^T(P−t)` yields cm-scale residuals (correct); any transpose error yields metre-scale residuals.

---

## 2. R1–R4 operational criteria, what was actually computed, and separability verdict

Model self-sampling scale `[computed]`: nearest-neighbour distance over the 67 870 model points: **median d_model_nn = 8.11 mm** (mean 8.78, p90 16.44). R1 bound = 2·d_model_nn = **16.21 mm**.
Model normals: local-PCA (k=16) on the model cloud, oriented away from CoM (open3d has no Python-3.14 wheel; PCA normals are a deterministic classical substitute).
Per scan, each GT-aligned scan point receives unsigned residual r = distance to nearest model point (cKDTree) and signed residual s = (p−m*)·n_m* along the nearest model normal.

| Class | Operational criterion (frozen) | Computed on VI? | Result (mean fraction of scan points) |
|---|---|---|---|
| **R1 sampling** | r ≤ 2·d_model_nn = 16.21 mm | yes, all 501 | **15.2 %** (IQR 14.0–16.4 %) |
| **R2 occlusion / backface** | r > bound **and** nearest model point is back-facing: (n_l · view_dir) > 0 after transforming model+normals by GT pose (angle normal↔lidar-to-point > 90°). Model backface fraction ≈ 50.4 % | yes | **13.3 %** (IQR 12.2–14.2 %) |
| **R3 FOV truncation** | r > bound **and** nearest model point lies outside the Mid-40 cone about +X, half-angle 19.2° (38.4° circular FOV `[spec-claim]`) | yes | **0.000 — EMPTY on VI.** At the closest range (8.75 m) the target subtends ≈ 6.5° < 19.2°; the entire model is inside FOV at every scan. `model_fov_trunc_frac ≡ 0` for all 501 scans |
| **R4 candidate** | r > bound, nearest model point front-facing AND in-FOV, **and** DBSCAN-clustered in target frame (eps 0.10 m, ≥5 pts); isolated large residuals kept as "large-noise" | yes | **71.2 %** structured-candidate (IQR 70.2–72.4); only **0.24 %** unclustered large-residual noise |

Supporting quantities `[computed]`:
- Global residual distribution (508 754 points, every 10th scan): p25 = 27.0 mm, **median 64.8 mm**, p90 154.1, p95 195.2, p99 278.9 mm; **85.0 % of all points exceed the 16.2 mm R1 sampling bound**; only 0.36 % exceed the 0.5 m excess threshold.
- Signed residual global mean **−39.4 mm**, median −29.6 mm (scan surface lies systematically *inside* the model along outward normals); per-scan signed mean correlates with range (Pearson r = −0.597; −28.9 mm at 8–11 m vs −44.6 mm at 11–13.5 m).
- missing_proxy (fraction of GT-visible model surface with no scan point within 50 mm): mean 0.601, IQR 0.562–0.639.

### 2.1 Can R4 be separated from R1/R2/R3?

- **R4 vs R1 — YES, cleanly.** The R1 bound is set by the model's own sampling distribution (8.11 mm) and 85 % of observed residuals lie above 2·d_nn; the global residual mode (~30–40 mm) is 4× the R1 bound. R1 is therefore far too small to explain the residual mass. R1 points are spatially diffuse by construction; R4 points form dense contiguous clusters by construction.
- **R4 vs R2 — YES at the label level, with a stated boundary.** Back-facing model surface is identified per scan from GT pose + model normals; only 13.3 % of large residuals attach to backface/silhouette model points. **Boundary that cannot be removed on VI alone:** silhouette-adjacent front points whose nearest model neighbour is a backface edge point inherit ambiguous class; this is a thin shell (few %), not the bulk.
- **R4 vs R3 — VACUOUS on VI.** R3 is identically empty (target never leaves the FOV cone); we can *assert* no R3 contamination, but VI provides **no empirical test** of FOV-truncation separation — that test requires a closer trajectory where the target overfills the FOV (out of scope this round).
- **Within R4, physical causes (MLI/specular/multipath/thin-structure/CAD-vs-real) CANNOT be separated** with current assets: no intensity/ring/RGB/material labels exist (and are forbidden this round). The signed inward bias (−39 mm, range-dependent) is *consistent with* range bias / beam-footprint / CAD shrink but cannot be uniquely attributed. This is a **cause-level**, not a **existence-level**, identifiability limit.

### 2.2 STOP_IDENTIFIABILITY decision

**No STOP at the existence level:** R4 (large, front-facing, in-FOV, spatially clustered residual) is separable from R1 by a data-derived bound and from R2 by GT visibility, and R3 is demonstrably absent. The question "is there structured, non-sampling, non-occlusion residual?" is identifiable on VI.
**Explicit non-identifiability:** (i) R3 separation is untested (empty regime); (ii) the *physical attribution* inside R4 is non-identifiable without forbidden channels; (iii) R2 silhouette-shell labelling has a residual few-% ambiguity. These bound, but do not block, the minimal-phenomenon test.

---

## 3. Frozen patch definition (one-time, never re-fit)

- Inputs: 67 870 target-frame model points with PCA normals.
- Features `[x, y, z, 0.3·nx, 0.3·ny, 0.3·nz]`, **MiniBatchKMeans k = 24, random_state = 42, n_init = 20** → `cache/patches.npz`, `results/patch_definition.csv`.
- Model points per patch: min 1 693 / max 4 387 (balanced). Every scan point inherits the patch of its nearest model point; per-scan × patch stats frozen in `results/patch_persistence.csv` (12 024 rows).
- Cross-scan patch median profile `[computed]`: best patch #3 = 29.0 mm, worst #12 = 106.9 mm, **ratio 3.69×**, std 22.0 mm (CV 0.36). The worst patches are small-support edge/antenna-region patches; the best are large flat body panels (see `fig1b_patch_profile.png`).
- **This exact partition is the only one used in every downstream statistic and must be reused unchanged on any future trajectory.**

---

## 4. Honest identifiability boundary of existing assets (VI-only)

1. **Identifiable now:** (a) residual magnitude vs sampling floor; (b) front/back separation per GT pose; (c) target-frame spatial clustering and its cross-time/cross-aspect repeatability against two explicit nulls; (d) signed inward bias and its range dependence; (e) classical-baseline endpoint distributions scored against GT.
2. **Not identifiable on VI (do not overclaim):** physical cause within R4; FOV-truncation behaviour (regime absent); whether the inward signed bias is sensor range bias, beam footprint, or CAD scale — its range correlation (r=−0.60) favours a range-dependent mechanism but is not proof.
3. **Asset gaps that would change identifiability (not fetched this round, per discipline):** closer-range trajectories for R3; intensity/ring channels for specular/multipath separation; IV/V cross-trajectory replication of the frozen patch profile (the designed next gate).
