# REVISION_EXPERIMENT_REPORT — minimal pre-submission补实验

Date 2026-09-12. Frozen main config remains **24 patches / MiniBatchKMeans / [xyz,0.30·n] /
seed 42 / n_init 20 / batch 4096**. No sweep re-selects it; III is fixed retrospective sensitivity
only and never used for tuning. Every number below is produced by a saved script with per-frame raw
CSV, aggregate CSV, exact command/config/seed and input/output SHA256 in the matching
`*_provenance.json`. Baseline Raw/Huber/Patch/PatchHuber arms are reused from
`FOLLOWUP_6_9/scripts/replay79_arms.csv` and are never re-run.

Frame sets (joined from the frozen roster, unchanged): VI 501 (development/calibration),
IV 156 and II 428 (held-out transfer), III 371 (reserved/secondary). All registrations are GT-local
(x0=0) point-to-point ICP, basin 0.30 m/15°, identical solver; p2l is added only inside P2 as the
single channel that consumes normals.

---

## P1-A — Patch-count sensitivity (`01_patch_count/`)

- **Question.** Is the Patch translation benefit a lucky artefact of K=24, or does 24 sit in a broad stable region?
- **Protocol.** Re-cluster the target model at each K; re-aggregate the view-INDEPENDENT `mu_patch`
  over all 501 VI scans under that partition; run one Patch-LS arm on the unchanged frame roster;
  compare frame-paired against the reused Raw arm. Block bootstrap B=2000 seed42 over frozen blocks.
- **Fixed parameters.** w=0.30, seed=42, n_init=20, batch=4096, solver/frames/blocks/metric unchanged.
- **Changed parameter.** K ∈ {12,18,24,32,48}.
- **Dataset.** VI / IV / II / III.
- **Result.** Frame-paired Raw−Patch translation benefit (mm, median):

  | K | VI | IV | II | III |
  |---|---|---|---|---|
  |12|38.63|31.51|20.00|27.73|
  |18|46.04|34.76|22.31|33.55|
  |**24 (frozen)**|**43.51**|**33.63**|**19.10**|**28.93**|
  |32|52.47|36.82|24.34|31.61|
  |48|56.80|40.61|14.55|23.23|

  Sign is **positive for every K on every trajectory**. Frame-improved fraction is 1.00 on VI/IV,
  0.91–0.99 on III and 0.73–0.93 on II (only the extreme K=48 on II dips to 0.73 while the median
  benefit stays +14.55 mm). Paired rotation change stays within −0.44°…+0.47°.
- **Interpretation.** 24 lies well inside a wide plateau: even the coarsest (12) and finest (48)
  partitions retain large positive gains. No sign reversal; only the extreme K=48 shows mild
  degradation on the hardest trajectory II. This is stability, not optimization.
- **Limitation.** One physical target; K is varied over a fixed 2-octave range, not exhaustively.
- **Paper impact.** Directly answers "why 24 / is K cherry-picked": supports robustness to patch
  count; 24 is a reasonable mid-plateau choice, not a selected optimum.

## P1-B — Normal-feature weight sensitivity (`02_normal_weight/`)

- **Question.** Does the gain depend on augmenting clustering features with normals (w=0.30)?
- **Protocol / Fixed / Changed.** Same as P1-A; K=24, seed=42 fixed; w ∈ {0,0.15,0.30,0.60,1.00}.
  w=0 is pure-XYZ (position-only) clustering and **also answers P1-D** (partition strategy).
- **Result.** Paired Raw−Patch translation benefit (mm):

  | w | VI | IV | II | III |
  |---|---|---|---|---|
  |0 (position-only)|39.08|31.78|19.08|32.20|
  |0.15|39.09|32.92|17.93|31.38|
  |**0.30 (frozen)**|**43.51**|**33.63**|**19.10**|**28.93**|
  |0.60|56.21|40.75|18.39|27.54|
  |1.00|57.66|41.91|22.20|26.40|

  Positive at every w on every trajectory; rotation change within −0.66°…+0.32°.
- **Interpretation.** Pure position clustering (w=0) already delivers most of the gain
  (VI 39.1, IV 31.8, II 19.1, III 32.2 mm). The benefit comes primarily from **spatial partitioning
  itself**, not from normal augmentation; 0.30 sits in a flat, non-special region. We do **not** call
  0.30 "optimal" (no independent selection protocol).
- **Limitation.** Features remain [xyz, w·n]; alternative feature scalings are not explored (out of minimal scope).
- **Paper impact.** Removes the "tuned normal weighting" objection; simultaneously closes P1-D.

## P1-C — Clustering-seed sensitivity (`03_seed_sensitivity/`)

- **Question.** Does the gain survive re-randomising MiniBatchKMeans initialisation?
- **Protocol / Fixed / Changed.** K=24, w=0.30 fixed; for each seed re-fit the partition AND rebuild
  the VI calibration field; solver/frames/support/metric unchanged. seed ∈ {0,1,2,42,20240910}.
- **Result.** Paired translation benefit (mm) ranges across the five seeds:

  | traj | min | median | max | positive in all 5? |
  |---|---|---|---|---|
  |VI|43.16|47.40|48.08|**yes**|
  |IV|33.40|34.00|36.51|**yes**|
  |II|19.10|22.87|27.70|**yes**|
  |III|26.58|30.58|34.80|**yes**|

  Patch translation-median across seeds: VI 112.0–117.5, IV 120.6–126.3, II 41.8–45.9, III 28.6–41.3 mm;
  rotation-median range ≤0.62°; frame-improved fraction ≥0.84 on II and ≥0.99 on III.
- **Interpretation.** Across all five clustering seeds the frame-paired Patch-vs-Raw translation
  benefit is **strictly positive** on every trajectory, with a narrow spread — robust to seed.
- **Limitation.** Five deterministic seeds (pre-declared), not a full randomisation distribution.
- **Paper impact.** Removes the "lucky seed / random partition" objection.

## P2-A — Recomputed-normals ablation (`04_normal_recompute/`)

- **Question.** Is the Patch+Huber rotation penalty caused by not re-estimating normals after the
  piecewise correction m_corr = m + mu_patch?
- **Protocol.** Frozen 24/0.30/42 field. Re-estimate normals on the corrected geometry with the
  **exact nominal protocol** (`pca_normals`: local PCA k=16, smallest-eigenvalue eigenvector, oriented
  away from centroid). Compare Huber / Patch+Huber / Patch-ReNormal+Huber on both p2p and p2l.
- **Fixed.** All solver parameters, field, frames, blocks. **Changed.** only the normal array fed to ICP.
- **Result.**
  - **p2p (paper primary): ReNormal is bit-identical to Patch+Huber** — max per-frame difference
    1.4e-14 mm / 8.9e-16 deg. The primary rotation penalty is therefore unchanged
    (VI 0.421°, IV 0.052°, II 0.498°, III 0.720°), as expected because point-to-point Kabsch never
    reads normals.
  - **p2l (only channel using normals):** paired rotation penalty vs Huber decreases:

    | traj | Patch+Huber | Patch-ReNormal+Huber | translation gain PH | translation gain ReNormal |
    |---|---|---|---|---|
    |VI|1.118°|0.753°|47.14 mm|47.19 mm|
    |IV|0.612°|0.276°|32.22 mm|32.27 mm|
    |II|0.888°|0.656°|5.70 mm|5.38 mm|
    |III|1.059°|0.986°|20.90 mm|20.39 mm|
- **Interpretation (causal language deliberately limited).** In the point-to-point primary the
  penalty cannot be attributed to stale normals (the solver does not consume them). In point-to-plane
  the ablation is **consistent with** stale normals contributing part of the penalty (reduced on all
  four trajectories, most on VI/IV) while the translation gain is essentially preserved; a residual
  penalty remains, so recomputation does not eliminate it.
- **Limitation.** p2l is a diagnostic channel, not the paper's primary metric; the ablation does not
  isolate a unique causal mechanism.
- **Paper impact.** Lets the paper state precisely where a normal-recomputation cost does/does not
  arise, and forestalls the obvious reviewer question.

## P2-B — Boundary-smoothing ablation (OPTIONAL, `04_normal_recompute/`)

- **Question.** Does the piecewise-constant patch boundary contribute to the rotation penalty?
- **Protocol.** Parameter-FREE single-step blend: each model point's correction is averaged over the
  same frozen k=16 self-neighbourhood used by the nominal normal estimator (interior points unchanged;
  25.7% of points near a boundary change, p90 19.6 mm). Frozen normals retained, so only the field changes.
- **Result.** p2p Patch-Smooth+Huber rotation penalty vs Huber: VI 0.503°, IV 0.075°, II 0.543°,
  III 0.853° (vs 0.421/0.052/0.498/0.720 unsmoothed) — **not reduced**; translation gain retained
  (46.1/33.6/6.7/20.6 mm). p2l penalty is partly reduced (VI 1.118→0.830, IV 0.612→0.377,
  II 0.888→0.662, III 1.059→1.071).
- **Interpretation.** Boundary smoothing does not remove the primary (p2p) rotation cost; like
  ReNormal it only trims the p2l channel. Together P2-A/P2-B indicate the p2p rotation cost is the
  intrinsic price of shifting target geometry before a point-to-point solve, not an artefact of
  stale normals or hard patch boundaries.
- **Limitation / Paper impact.** Diagnostic only, explicitly not a proposed method; optional mention.

## P3 — Statistical block-size sensitivity (`05_block_sensitivity/`, zero new registration)

- **Question.** Does the headline effect direction depend on the external block convention (50)?
- **Protocol.** Same frozen in-support frames; external primary block = in-support rank // L for
  L∈{25,50,100}; VI keeps its fixed orientation blocks. Block-resample bootstrap B=2000 seed42.
- **Result.** The frame-paired median is L-invariant by construction; block count and block-level CI
  change. **Patch vs Raw stays positive at every L on IV/II/III with the 95% block-CI above 0**
  (fraction of positive blocks 0.94–1.00). Patch+Huber vs Huber likewise stays positive. **Patch vs
  Global on II remains unresolved**: pooled median +7.47 mm but the block CI still crosses zero at
  L=50/100 (positive-block fraction only 0.56–0.61) — reported as-is, with no adjustment to make it
  significant.
- **Interpretation / Paper impact.** Core conclusions are insensitive to the aggregation convention;
  the II Patch-vs-Global contrast is honestly retained as "directionally positive, block-unresolved".

## P4 — II transfer-failure diagnostic (`06_II_failure_cases/`, no new model)

- **Question.** Why does the view-conditioned Full/Patch spatial increment fail to help on II despite working on IV?
- **Protocol.** Pre-registered rule on effect = Full−Patch translation: best10% / median±5% / worst10%;
  one representative per bin = frame closest to the bin median (no hand-picking). Existing support
  descriptors (nearest-view distance, distance/τ, kernel ESS, coverage, fallback count, correction
  magnitude, predicted-step alignment) + per-patch support/correction vectors for the 6 reps.
- **Result.** II is **not** poorer in historical-view support: nearest_d 0.11–0.26 (IV 0.08–0.26),
  coverage 1.00 (IV 0.96), ESS ≈15.7–15.9 both, fallback 0 on II; visible patches 21–24 both. The
  discriminator is predicted-step direction alignment cos(pred,Raw): IV +0.71…+0.85 vs II
  median/worst −0.38/−0.70 (II best10 +0.76). On II the learned view→mismatch correction points the
  wrong way relative to the actually-needed step even though nearby training views exist.
- **Interpretation.** The available diagnostics localize the failure to **transfer/view conditioning
  (a learned mapping that mis-fires on II), not to lack of views, coverage, patch visibility or
  extrapolation distance**; they do **not uniquely identify a physical cause**.
- **Limitation / Paper impact.** Descriptive, six representative frames; supports an honest
  limitation paragraph rather than a new mechanism claim.

---

## Overall robustness verdict
No sign reversal and no large/trajectory-specific instability appears in any mandatory grid: the
Patch translation benefit is positive for every tested K, w and seed on all four trajectories. The
rotation penalty is small, is shown not to stem from stale normals or hard boundaries in the p2p
primary, and is partially consistent with both in the p2l diagnostic channel.
