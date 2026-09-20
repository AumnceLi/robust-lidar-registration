# G0 — Existing-asset & existing-experiment audit (pre-submission minimal revision)

Generated 2026-09-12. Rule: **audit first, run second.** Every EXISTING result below is reused
(read-only) with its generating script/config/seed traced; only items marked NEED-RUN enter new
computation. No existing cache/CSV/NPZ/JSON/pickle/log/figure-source-data was regenerated.

## 0. Frozen main configuration (locked, never replaced by a sweep)

| Item | Frozen value | Source of truth |
|---|---|---|
| patch count | 24 | `structured_mismatch_phase0/scripts/s3_patches.py` `K_PATCH=24`; `POSE_AUDIT/audit/patch_definition.json` |
| clustering | sklearn `MiniBatchKMeans` | same |
| feature | `column_stack([xyz_m, 0.30*unit_normal])` | same |
| normal weight w | 0.30 | `NORM_W=0.3` |
| random_state | 42 (`s0_common.RNG_SEED=42`) | same |
| n_init / batch_size / max_iter | 20 / 4096 / sklearn default (== explicit 300 partition, verified) | same |
| model normals | PCA local k=16, smallest-eigenvalue eigenvector, oriented away from centroid | `s0_common.pca_normals`; `s1_residuals` builds `model_cache.npz` |
| registration | GT-local (x0=0) point-to-point ICP, basin 0.30 m / 15°, Huber δ=1.345, MAD×1.4826 scale w/ raw NN-spacing floor | `g_chain/common/g_common.py robust_icp` |
| VI calibration field for **Patch** | view-INDEPENDENT `mu_patch` = pooled per-patch 3-vector over ALL 501 VI scans | `g_common.hierarchy_library` |
| external primary blocks | in-support rank // 50 (IV 4, II 9, III 8 blocks); VI = 6 frozen orientation blocks | `af_common.block_series`; `POSE_AUDIT/results/master_pose_results_frame.csv` |
| in-support frame counts | VI 501, IV 156, II 428, III 371 | `FOLLOWUP_6_9/scripts/replay79_arms.csv` |

**Reproduction gates passed before any new run (`_lib/gate0.py`, `_lib/gate_anchor.py`):**
- Re-clustering at (24, 0.30, 42) reproduces the frozen `patches.npz` partition with agreement
  1.000000 (both literal-s3 call and explicit max_iter=300).
- Re-aggregated view-independent `mu_patch` equals the frozen hierarchy `mu_patch` to **0.0** (max abs diff).
- The anchor Patch-LS arm re-run through the new sweep machinery reproduces the existing replay79
  Patch arm (result recorded in `01_patch_count/`, gate table).

## 1. Targeted experiments A–I

| Experiment | Existing? | Script | Config | Result file | Complete? | Need rerun? |
|---|---|---|---|---|---|---|
| **A. Patch-count sweep** {12,18,24,32,48} | **NO** | only frozen k=24 in `s3_patches.py`; audit explicitly flags the gap | k=24 only | `POSE_AUDIT/audit/patch_definition.json` field `why_24="NOT_FOUND: no patch-count sweep"`; `stage5_parameter_table.py` `why_exactly_24=NOT_FOUND` | n/a | **YES → P1-A (NEW)** |
| **B. normal-weight sweep** {0,.15,.30,.60,(1.0)} | **NO** | `NORM_W=0.3` hard-coded; no grid anywhere | w=0.30 only | — | n/a | **YES → P1-B (NEW)** |
| **C. clustering-seed sweep** (5 seeds) | **NO** | only `random_state=42`; seed 20240910 elsewhere is a *label-permutation placebo*, not a re-cluster | seed 42 only | `AUDIT_FOLLOWUP/scripts/t2_patch_label_placebo.py` (placebo, different operation) | n/a | **YES → P1-C (NEW)** |
| **D. partition-strategy comparison** | **NO standalone** | no XYZ-only clustering run | — | — | n/a | **NO EXTRA RUN**: position-only XYZ clustering == normal-weight **w=0** cell of P1-B; answered there. Deterministic third partition = NOT_NEEDED (would add a new method) |
| **E. recompute normals after Patch correction** | **NO** | `stage5_parameter_table.py`: `normals_recomputed_after="NO (frozen PCA normals reused)"`; `audit/geometry_correction_parameters.md`: "N/A — not recomputed" | frozen normals reused | — | n/a | **YES → P2-A (NEW)**; normal protocol IS known (`pca_normals k=16`) → **not blocked** |
| **F. patch-boundary smoothing / interpolation** | **NO** | `stage5`: `smoothing="NONE"/NOT_FOUND`, `boundary_interpolation="NONE (piecewise constant per patch)"` | none | — | n/a | **OPTIONAL → P2-B**; only if a clean fixed (no tuning) KNN blend exists, else NOT_NEEDED |
| **G. block-size sensitivity** {25,50,100} | **NO** | external block fixed at rank//50; only sign-flip L=5 and adaptive DBS blocks exist | L=50 only | `af_common.block_series`; `g_common.block_signflip_p(L=5)` | n/a | **YES → P3 (NEW, zero new registration: re-aggregate existing per-frame deltas)** |
| **H. II transfer failure visualization** | **PARTIAL (aggregate only)** | `FOLLOWUP_6_9/scripts/item9_build.py` gives *aggregate* view-support stats; no fixed-quantile representative-frame figure w/ patch IDs, correction & residual vectors | aggregate | `followup9_view_support_*`, `scripts/replay79_support.csv` | aggregate complete; requested per-frame diagnostic missing | **YES → P4 (NEW, low cost from existing support table + handful of frames)** |
| **I. zero-perturbation L0 on existing 20-frame init subset** | **NO** | init study has only L1/L2/L3 (10mm/.5°, 30mm/1°, 50mm/2°) | L1–L3 | `revision_experiments/final_targeted/initialization_sensitivity_summary.csv` | no L0 | **NOT_NEEDED per task rule** (low priority; do not re-run the whole study) |

## 2. "Do not redo" ledger — EXISTING, reused, never re-run

| Existing experiment | Status | Primary result / script (reused as-is) |
|---|---|---|
| Iteration-budget sensitivity 40/80/160 | EXISTING_RESULT | `revision_experiments/exp2_iter_budget/` (framewise+summary+decision) |
| Local initialization sensitivity L1/L2/L3 | EXISTING_RESULT | `revision_experiments/final_targeted/initialization_sensitivity_*` |
| Patch+Huber / Patch+Trim combination | EXISTING_RESULT | `FOLLOWUP_6_9/followup7_patch_robust_*`; per-frame `scripts/replay79_arms.csv` |
| Structured mismatch D1–D5 | EXISTING_RESULT | `g_chain/G_GENERALITY/` |
| Full 2×2 decomposition | EXISTING_RESULT | `revision_experiments/exp5_full_2x2/` |
| Historical transfer-support diagnostics | EXISTING_RESULT | `FOLLOWUP_6_9/followup9_view_support_*` |
| Estimated-Full local diagnostic | EXISTING_RESULT | `g_chain/G2_ESTIMATED_VIEW/` |
| Patch spatial-label placebo (single pre-declared seed) | EXISTING_RESULT | `AUDIT_FOLLOWUP/patch_label_placebo_*` |
| Raw/Huber/Trim/Global/Patch/Full primary comparison | EXISTING_RESULT | `FOLLOWUP_6_9/followup6_primary_method_*`; `replay79_arms.csv` |
| Nuisance N1–N4 controls | EXISTING_RESULT | `structured_mismatch_phase0` + `AUDIT_FOLLOWUP/*nuisance*` |

## 3. Decision

New computation is required **only** for: **P1-A, P1-B, P1-C** (one new Patch-LS arm per fixed-grid
config; baseline Raw reused), **P2-A** (recomputed-normals Huber, p2p gate + p2l channel),
**P3** (re-aggregation only), **P4** (diagnostic figure from existing tables). P1-D is answered by
the P1-B w=0 cell; P2-B is OPTIONAL; L0 is NOT_NEEDED. No held-out trajectory (IV/II/III) is used to
choose any parameter; 24 / 0.30 / seed42 remains the sole paper main configuration.
