# AUDIT_REPORT — pre-submission minimal-revision experiment audit

Date: 2026-09-12. Scope: spacecraft LiDAR registration paper. Principle: audit first, reuse every
existing result, run only what is genuinely missing; frozen main config **24 patches / normal
weight 0.30 / seed 42** is never replaced or re-selected. Full item-by-item evidence is in
`00_audit_existing/audit_existing_experiments.md`.

## Status ledger

### EXISTING (reused as-is, never re-run)
| Asset | Location |
|---|---|
| Raw / Huber / Trim / Global / Patch / Full primary per-frame results | `FOLLOWUP_6_9/scripts/replay79_arms.csv`; `followup6_primary_method_frame.csv` |
| Patch+Huber / Patch+Trim combination | `FOLLOWUP_6_9/followup7_patch_robust_*` |
| Iteration budget 40/80/160 | `revision_experiments/exp2_iter_budget/` |
| Local init sensitivity L1/L2/L3 | `revision_experiments/final_targeted/initialization_sensitivity_*` |
| Structured mismatch D1–D5 | `g_chain/G_GENERALITY/` |
| Full 2×2 decomposition | `revision_experiments/exp5_full_2x2/` |
| Historical transfer-support diagnostic (aggregate) | `FOLLOWUP_6_9/followup9_view_support_*`, `replay79_support.csv` |
| Estimated-Full local diagnostic | `g_chain/G2_ESTIMATED_VIEW/` |
| Patch spatial-label placebo (single pre-declared seed 20240910) | `AUDIT_FOLLOWUP/patch_label_placebo_*` |
| Nuisance N1–N4 controls | `structured_mismatch_phase0/`, `AUDIT_FOLLOWUP/*nuisance*` |
| Frozen model / PCA normals / 24-patch labels / VI-only predictor | `structured_mismatch_phase0/scripts/cache/model_cache.npz`, `patches.npz`; `VI_ONLY_PREDICTOR_FROZEN.npz` (SHA-asserted) |

### NEW (computed this round; raw per-frame + aggregate + exact command + config + seed + input/output hashes saved)
| ID | Experiment | Folder | New registrations |
|---|---|---|---|
| P1-A | Patch count K ∈ {12,18,24,32,48} | `01_patch_count/` | 5 Patch-LS arms (Raw reused) |
| P1-B | Normal weight w ∈ {0,.15,.30,.60,1.00} | `02_normal_weight/` | 4 new Patch-LS arms (w=.30 = shared anchor) |
| P1-C | Clustering seed ∈ {0,1,2,42,20240910} | `03_seed_sensitivity/` | 4 new Patch-LS arms (seed42 = shared anchor) |
| P2-A | Recomputed-normals ablation (p2p gate + p2l) | `04_normal_recompute/` | 4 arms (p2p ReNormal-Huber; p2l Huber/PatchHuber/ReNormalHuber) |
| P2-B | Parameter-free k=16 boundary smoothing (OPTIONAL) | `04_normal_recompute/` | 3 arms |
| P3 | Block size {25,50,100} | `05_block_sensitivity/` | **0** (re-aggregation of existing per-frame deltas) |
| P4 | IV-vs-II fixed-quantile representative diagnostic | `06_II_failure_cases/` | 0 registrations (6 frames reloaded for the figure) |

### BLOCKED
- None. The nominal normal-estimation protocol was fully recoverable (`s0_common.pca_normals`,
  PCA k=16, smallest-eigenvalue eigenvector oriented away from centroid), so P2-A was **not**
  blocked (`BLOCKED_NORMAL_PROTOCOL` did not occur).

### NOT_NEEDED (deliberately not run)
- **P1-D standalone partition strategy**: position-only XYZ clustering is mathematically identical
  to the **w=0** cell of P1-B; a third "deterministic spatial partition" would introduce a new
  method, so it is answered by P1-B and not run separately.
- **Zero-perturbation L0** on the 20-frame initialization subset: no cache exists (init study has
  only L1–L3); per task rule this is low priority and the whole study was not re-run.
- Additional hyper-parameter sweeps beyond the fixed grids: stopped per the stop condition once the
  mandatory grids showed stable positive benefit.

## Reproduction / non-circularity gates (all passed before trusting any new number)
1. Re-clustering at the anchor (24, 0.30, 42) reproduces frozen `patches.npz` partition agreement **1.000000**.
2. Re-aggregated view-independent `mu_patch` equals frozen hierarchy field to **0.0** (max abs diff).
3. Anchor Patch-LS arm reproduces existing replay79 Patch arm to **2.8e-14 mm / 1.8e-15 deg** (floating-point noise).
4. P2-A p2p ReNormal equals frozen-normal PatchHuber to **1.4e-14 mm** — the mechanistic gate proving
   point-to-point ICP does not consume normals.
5. Frames, in-support filter and blocks for every new arm are JOINED from the existing replay79 Raw
   roster (VI 501 / IV 156 / II 428 / III 371); no frame was re-selected.

## Environment / provenance
Python 3.14.7, numpy 2.5.3, scipy 1.18.1, sklearn 1.9.0, pandas 3.0.5. `D:\doubao` is **not a git
repository** (git_commit recorded as `NOT_A_GIT_REPO` in every provenance JSON). Each experiment
folder contains `*_provenance.json` with exact command, config, seed, input-asset SHA256 and
output-file SHA256. Per-arm raw outputs are cached in `_lib/arm_cache/` and are never recomputed.
