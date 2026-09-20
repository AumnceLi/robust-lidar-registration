# FINAL TARGETED EXPERIMENTS — DECISION (Phase 2.5 + small initialization sensitivity)

All new outputs are under `revision_experiments/final_targeted/`. No frozen hyperparameter was tuned, support masks were not redefined, no Phase-1/2 result was regenerated or overwritten, no baseline / Full variant / geometry / dataset / constrained permutation was added, trajectory III is kept **post-hoc / secondary** (and is not called untouched confirmation), VI is development evidence, and no mission threshold was invented. Tasks 1–2 reuse frozen framewise results with no re-registration; Task 3 runs the frozen solver (bit-identical to `g_common.robust_icp`, validated to 2.8e-14 mm vs replay79) only at perturbed LOCAL initial poses. Block statistics use the canonical paper block map (verified **VI 6 / IV 4 / II 9 / III 8**) and the manuscript bootstrap (resample paper blocks, B=2000, seed 42, 2.5/97.5) and one-sided block sign-flip paired p.

## 1. Does Patch provide direct paired incremental value beyond Global-Vector?

**Partially — trajectory-dependent (`SPATIAL_INCREMENT_TRAJECTORY_DEPENDENT`).** Using the DIRECT per-frame pairing d_t = e(GlobalVector) − e(Patch) (not a subtraction of two marginal medians):

- **VI**: median d_t +33.92 mm, Patch-better 1.000, blocks 6/6 positive, block CI [+26.69, +43.55] excludes 0, sign-flip p 0.0005.
- **IV**: median d_t +19.31 mm, Patch-better 0.981, blocks 4/4 positive, block CI [+12.09, +24.21] excludes 0, sign-flip p 0.0005.
- **II**: median d_t +0.24 mm, Patch-better 0.509, blocks 4/9 positive, block CI [-8.49, +18.02] CROSSES 0, sign-flip p 0.4463.
- **III (post-hoc)**: median d_t +25.03 mm, Patch-better 0.881, blocks 7/8 positive, block CI [+15.81, +30.36] excludes 0, sign-flip p 0.0005.

On **II** the two marginal medians make Patch's median error look 9.39 mm lower (better), but the direct paired median is only +0.24 mm with an even better/worse split and a zero-crossing block CI (p 0.446). The sentence *“Patch clearly outperforms simple historical correction on all four trajectories”* is **not supported and must be removed**: state a robust spatial increment on VI/IV (and the secondary III) and a null/uncertain increment on II, where one constant historical vector already matches Patch once frames are paired.

## 2. Does Patch+Huber provide direct incremental value beyond Huber?

**Yes for translation, on every trajectory (`ROBUST_PLUS_PATCH_INCREMENT_SUPPORTED`), with a disclosed small rotation cost.** Direct Δt = e(PH)−e(Huber) (negative = better):

- **VI (development)**: median Δt -45.38 mm, translation-better 1.000, oriented block gain +45.06 with CI [+43.19, +47.06] (excludes 0), blocks 6/6; median Δr +0.421 deg.
- **IV**: median Δt -31.81 mm, translation-better 1.000, oriented block gain +29.88 with CI [+22.40, +34.69] (excludes 0), blocks 4/4; median Δr +0.052 deg.
- **II**: median Δt -7.87 mm, translation-better 0.750, oriented block gain +3.90 with CI [+1.61, +12.09] (excludes 0), blocks 8/9; median Δr +0.498 deg.
- **III (post-hoc)**: median Δt -19.66 mm, translation-better 0.860, oriented block gain +18.25 with CI [+6.08, +34.16] (excludes 0), blocks 6/8; median Δr +0.720 deg.

No block CI crosses zero and the sign never reverses, but the increment is smallest on II and adding Patch to the already-strong Huber carries a small positive median rotation change (rotation-better fraction < 0.5). The secondary PatchHuber-vs-Patch comparison improves BOTH axes on every trajectory (median Δt and Δr negative), i.e. Huber removes the Patch field's own rotation cost — recommend Patch+Huber for joint 6-DoF and state the small vs-Huber rotation trade-off explicitly. This answers “does Patch add on top of Huber”, not the already-known Patch+Huber-vs-Raw result.

## 3. Does the Patch field materially shrink the local reference-pose initialization basin?

**No (`INIT_STABLE_LOCAL`).** Across L1/L2/L3 (10 mm/0.5° → 50 mm/2°; 80 fixed frames × 12 deterministic perturbations × 4 methods = 3840 runs + 320 references):

- **VI**: Patch−Raw paired gain +45.0/+44.7/+44.6 mm and PatchHuber−Huber +50.0/+50.0/+49.9 mm across L1/L2/L3 — ordering stable, no perturbation-induced reversal.
- **IV**: Patch−Raw paired gain +5.0/+5.2/+5.8 mm and PatchHuber−Huber -3.2/-3.6/-2.8 mm across L1/L2/L3 — ordering stable, no perturbation-induced reversal.
- **II**: Patch−Raw paired gain +9.6/+9.7/+9.6 mm and PatchHuber−Huber +6.3/+3.5/+2.8 mm across L1/L2/L3 — ordering stable, no perturbation-induced reversal.
- **III (post-hoc)**: Patch−Raw paired gain +7.8/+8.1/+8.4 mm and PatchHuber−Huber +1.9/+2.1/+1.5 mm across L1/L2/L3 — ordering stable, no perturbation-induced reversal.

Median initialization degradation |Δinit_t| is 0.26 mm and median final-error drift L1→L3 is ≤3.7 mm; basin boundary-clip fractions are small and flat, and Patch clips no more than Raw (max difference 0.000) while Patch+Huber and Huber never clip — no Patch boundary/termination penalty. The local degradation tail is no wider for Patch than Raw (p99 ≈ 5.2 vs 5.4 mm); the wider moderate tail belongs to the robust-loss methods (with and without Patch) and to L3 on mostly-out-of-support IV frames. This supports **local** stability only: do not claim global convergence, a large capture basin, or deployment-ready initialization robustness, and do not label L1–L3 as tolerances or certified radii.

## 4. Is another experiment scientifically necessary for the current paper?

**No.** No new result overturns a frozen result or reveals a concrete unresolved defect: the solver is reproduced to machine precision, the Patch-over-Huber translation increment holds on every trajectory, and the local basin is stable. The one substantive consequence is a **wording refinement**, not a new experiment: the spatial Patch increment over the *simplest historical correction* must be stated as trajectory-dependent (null on II under direct pairing). Per instruction, do **not** start block-length sensitivity, new spatial permutations, new strong baselines, new initialization levels, new datasets/methods/Full variants without a new explicit instruction. The default is freeze.

## Manuscript-level verdict (exactly one)

# `READY_WITH_TRAJECTORY_DEPENDENT_INCREMENT`

Freeze after applying these targeted wording edits:
1. Patch vs the simplest historical (constant-vector) correction: **trajectory-dependent** — strong on VI/IV and the post-hoc III, null/uncertain on II (direct pairing); delete any “outperforms on all four trajectories” sentence.
2. Patch+Huber vs Huber: keep the **translation** increment (all four, block CIs exclude zero; smallest on II) and disclose the small rotation cost; present Patch+Huber as preferred for joint 6-DoF because it also removes Patch's own rotation cost.
3. Initialization: keep the claim strictly **local** around the reference pose (stable through 50 mm/2° probes); no global-convergence / capture-basin / deployment language.
4. Keep III post-hoc/secondary and VI as development evidence throughout.

## Artifacts (this folder)

- Task 1: `patch_vs_global_framewise.csv`, `patch_vs_global_blocks.csv`, `patch_vs_global_summary.csv`, `patch_vs_global_decision.md`.
- Task 2: `patchhuber_direct_framewise.csv`, `patchhuber_direct_blocks.csv`, `patchhuber_direct_summary.csv`, `fig_patchhuber_direct_increment.png`, `patchhuber_direct_decision.md`.
- Task 3: `initialization_frames.json` (fixed before runs), `initialization_sensitivity_framewise.csv` (4160 rows), `initialization_sensitivity_summary.csv`, `initialization_sensitivity_boundaries.csv`, `fig_initialization_sensitivity.png`, `fig_initialization_boundaries.png`, `initialization_sensitivity_decision.md`.
- Reproducibility: `ft_common.py`, `task1_patch_vs_global.py`, `task2_patchhuber_direct.py`, `t3_select_frames.py`, `t3_common.py`, `t3_solver_check.py`, `t3_run.py`, `t3_analyze.py`.
