# FINAL THREE EXPERIMENTS — G0 ASSET AUDIT (run before any new experiment)

**Round scope (frozen):** only E1 coarse/non-reference initialization robustness, E2 VI-internal
held-out (leave-one-block-out) validation, E3 runtime/memory/deployment cost. No new method, no
parameter tuning, no main-config change, no new comparator, no frame re-selection.

**Frozen main configuration (unchanged this round):** Patch count K=24; normal feature weight
w=0.30; MiniBatchKMeans seed=42 (`n_init=20, batch_size=4096`); support rule unchanged; registration
solver unchanged (40-iteration main budget, basin safeguard 0.30 m / 15°, p2p tol 1e-8, Huber
δ=1.345); Raw / Patch / Huber / Patch+Huber / Full / Estimated-Full definitions unchanged.
VI = development/calibration; IV/II = external transfer; III = reserved/secondary (post-hoc).

Audit method: recursive filename + full-text search of `D:\doubao` for
`coarse_init, initialization, capture_range, capture_probability, random_init, pose_perturb,
heldout/held-out, vi_cv, cross_validation, leave_block_out, leave_one_block_out, lobo, fold,
runtime, timing, profiling, memory, peak_memory, estimated_full_runtime`, plus direct reading of
every candidate runner/result.

## 1. Decision table (required format)

| Experiment / asset | Existing? | Source (path under D:\doubao) | Complete? | Reusable? | Need new run? |
|---|---|---|---|---|---|
| **E1** local init L0–L3 (0/10/30/50 mm; 0/0.5/1/2°) | **Yes** | `revision_experiments/final_targeted/` : `t3_common.py`,`t3_run.py`,`t3_analyze.py`,`initialization_frames.json`,`initialization_sensitivity_framewise.csv` (4160 rows), `..._summary.csv`,`..._boundaries.csv` | Yes, complete for L0–L3 × 4 methods × 80 frames × 4 dirs | **Yes — reuse verbatim** for reference(L0)+L1+L2+L3 after a solver-identity re-check | No (reuse) |
| E1 **coarse L4/L5/L6 (100/200/300 mm; 5/10/15°)** | **No** | only local L1–L3 exists; no run beyond 50 mm/2° anywhere (see §2) | n/a | perturbation family + instrumented solver reusable | **YES — new (L4–L6 only)** |
| E1 optional L7 (500 mm/20°) | No | — | n/a | — | **NO** — 0.50 m initial translation exceeds the frozen 0.30 m basin safeguard at x0, so the precondition "code allows AND does not violate current safeguard" is false (documented, not run) |
| E1 20-frame/traj roster (VI/IV/II/III) | Yes | `initialization_frames.json` (even positions of Exp-2 frozen 40-list; fixed before results) | Yes | **Yes, reuse; no re-selection** | No |
| E1 instrumented frozen solver + fidelity gate | Yes | `t3_common.inst_icp`, `t3_solver_check.py` (bit-identical to `g_common.robust_icp`; replay79 to 2.8e-14 mm) | Yes | Reuse solver; new runner re-validates vs existing L1–L3 rows | gate only |
| **E2** VI six-block leave-one-block-out **held-out Patch field + registration OOF** | **No deliverable** | `g_chain/common/_hier_check.py` is a **stride-4, non-deliverable** analytic step-**direction** cosine scratch check (no registration, 1/4 scans); `final_falsification/ff1_baselines.py` "B_blockout" is a **view-only** baseline fold, not the Patch field | Partial precursor only | reuse the exact train convention `train = blocks!=blocks[t]` and frozen blocks | **YES — new 6-fold LOBO, full 501 OOF registrations** |
| E2 frozen VI contiguous blocks (6) | Yes | predictor `vi_blocks` (len 501): [0,70)[70,140)[140,219)[219,315)[315,418)[418,501) = 70/70/79/96/103/83, contiguous | Yes | **Yes** | No |
| E2 frozen 24-patch partition `plab` | Yes | `cache/patches.npz` (MiniBatchKMeans frozen; never re-clustered per fold) | Yes | **Yes — frozen across folds (isolates field-history effect)** | No |
| E2 full-VI (in-sample) Patch reference result | Yes | `g_chain/G1_MITIGATION/results/g1_oracle_vi.csv` (M0_raw_p2p, M4_patch_corr × 501) | Yes | cross-check only (key comparator: full-fit vs OOF) | recompute in-runner for identical path + hash, cross-check |
| **E3** per-method computational latency (Raw/Patch/Full/Est.Full) | **No** | `exp1_timing_motion/` is scan-**timestamp/motion** semantics, **not** compute cost; `m0_bench.py` is a numerical self-test; no wall-time-per-method table exists | n/a | roster + method runners reusable | **YES — new** |
| E3 decomposed stages (build/query/KD-tree/reg1/reg2) | No | — | n/a | stage boundaries taken from frozen `g1_run`/`g2_run` flow | **YES — new** |
| E3 peak RSS / memory | No | psutil not previously used; installed this round (7.2.2) | n/a | — | **YES — new** |
| E3 one-time calibration cost (24-patch cluster + VI field build) | No | frozen recipe in `s3_patches.py` (K=24,w=0.30,seed=42,n_init=20,batch=4096) + `g_common.hierarchy_library` | recipe yes, timing no | reproduce labels == frozen `plab` as gate, time it | **YES — new (timing only; frozen outputs untouched)** |

## 2. Explicit "does it already exist?" checks requested in the brief

1. **Initialization runs larger than 50 mm / 2°?** **None for ICP pose initialization.**
   - `final_targeted/t3_*` is the only ICP-initialization sweep and stops at L3 = 50 mm/2°.
   - `g_chain/G2_ESTIMATED_VIEW` ("perturbation to 100 mm/2°" in `FINAL_REVIEWER_VERDICT.md`) perturbs the
     **estimated-view descriptor z** feeding the view library, **not** the ICP start pose — different object.
   - `FINAL_TOPJOURNAL_HARDENING/THEORY` "D1=100 mm / D2=300 mm" are synthetic **mismatch doses**
     injected into the model, not initialization error. They are not coarse-init runs and are not reused as such.
   - ⇒ Coarse ICP levels L4–L6 are genuinely new.

2. **VI six-block leave-one-block-out / held-out field?** **No qualifying deliverable.**
   - `_hier_check.py` does Protocol-B leave-block-out but only every 4th scan and only compares analytic
     predicted-step **direction cosines** (global/patch/full); it explicitly labels itself
     "Not a deliverable". It contains no ICP registration and no out-of-fold pose-error result.
   - `final_falsification/*blockout*` tests whether **viewing geometry alone** predicts the objective
     (B0/B1/B2 view-only baseline); it does not hold out the Patch discrepancy field from registration.
   - ⇒ A proper 6-fold LOBO of the Patch field with all-501 out-of-fold **registration** is new.

3. **Raw/Patch/Full/Estimated-Full timing logs?** **None.** No file reports per-frame wall time,
   decomposed stages, throughput, or peak memory for the registration methods. `exp1_timing_motion`
   concerns inter-pose dt / motion, and `m0_bench` is a correctness micro-benchmark. ⇒ E3 is new.

## 3. Frozen INPUT assets and hashes (SHA-256; asserted at load / recorded in each provenance JSON)

| Role | File | Size B | SHA-256 |
|---|---|---:|---|
| VI-only predictor (Vmean,Vcnt,vrange,uview,blocks) | `structured_mismatch_phase0/scripts/cache/rescue/VI_ONLY_PREDICTOR_FROZEN.npz` | 288502 | `8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe` (asserted by `g_common.load_frozen`) |
| nominal model + PCA normals + NN spacing | `…/cache/model_cache.npz` | 1373771 | `7e53cd544227ba1e8f5c7326a1c23ca5bae6273af275c5a9488eb2a9e42dad6e` |
| frozen 24-patch partition | `…/cache/patches.npz` | 26129 | `6b4ffd09c6895abfecd1ed1dde1765eeb2d43f5f8e74e0c27dacbf7b6e5f9fe1` |
| frozen 20-frame/traj roster | `revision_experiments/final_targeted/initialization_frames.json` | 5724 | `e8ed60d4cd42b7cf0e3d914fdc2242f8fd17d0b16414fcab948b1a0d3482b77e` |

## 4. REUSED results (not re-run for L0–L3; hashed; re-validated)

| Reused asset | Size B | SHA-256 | Reuse scope |
|---|---:|---|---|
| `initialization_sensitivity_framewise.csv` (4160 rows = 320 reference + 3×1280 L1–L3; Raw/Huber/Patch/PatchHuber; 4 dirs) | 745330 | `4d2d16570a4503727be0681f1335a4767b6d5b0b13356c6d5f0b65c6dc37add4` | E1 L0(reference)+L1+L2+L3 |
| `…_summary.csv` | 10171 | `8e8880babb431b658a9021cde6e6d43e39ebb3a542f34d0d6490ec00389cdbc8` | continuity check vs new aggregation |
| `…_boundaries.csv` | 1947 | `beb18a889d71dd504febff5d5bea47917618937015d6348daf3c05db0796f77f` | continuity check |
| `g1_oracle_vi.csv` (3006 rows; M0..M5 × 501) | 547514 | `d7ed869b8282c891b26066d3fc949a4bcd51b36a1298532871c99f7f2bed6a06` | E2 full-VI comparator; E3 method-definition cross-ref |
| `g2_vi.csv` (T0_raw/oracle/est_gtstart/**est_warmstart** × 501) | 190861 | `063926ac32728d8a1ca8b121034ac0f8d38732493639e9603e3dc55c275ec0aa` | Estimated-Full definition = `est_warmstart` (nominal reg → estimated view → corrected-model reg warm-started) |
| `FOLLOWUP_6_9/scripts/replay79_arms.csv` | 2770535 | `9098162bfa9c9df0ea12515ccb53ab588fdb32831386392a731fd033c9a4e148` | solver-fidelity reference |

## 5. What this round WILL and WILL NOT run

- **WILL run (new):** E1 L4/L5/L6 only (identical 4-direction sign-balanced family, identical
  instrumented frozen solver; all four methods for continuity with Raw-vs-Patch primary); E2 6-fold
  VI leave-one-block-out with frozen `plab`, train-only `mu_patch`, leakage assertions, full-501 OOF;
  E3 single-process/single-thread latency of six methods over the same 80-frame roster (3 warm-up +
  10 timed), decomposed stages, isolated per-method peak RSS, plus one-time calibration cost.
- **WILL NOT do:** L7 (safeguard violation at x0); any new method/global initializer (no TEASER/FPFH);
  re-clustering per E2 fold; re-selecting frames; raising the iteration cap; tuning K/w/seed/solver/
  support; changing any frozen artifact; any new experiment beyond E1–E3.

**Audit conclusion:** reuse is maximal (E1 L0–L3 verbatim; frozen blocks/partition/roster/field
recipe verbatim). New compute is limited to E1 L4–L6, the E2 OOF registrations, and E3 timing/memory.
