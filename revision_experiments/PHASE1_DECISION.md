# PHASE-1 DECISION — pre-submission key supplementary experiments (1–3 only)

**Date:** 2026-09-12. **Scope executed:** first-priority experiments 1–3 only; Phase-2 baselines /
ablations were **not** started, per instruction. No existing main-result file was modified or
regenerated; everything new is under `revision_experiments/`. No frozen parameter (Patch/Full/DBS/
support/kernel/k/patch count/iterator/basin/tol/robust) was re-tuned. Frames/seeds were fixed before
results were seen. III is treated strictly as **post-hoc / secondary diagnostic**.

---

## 1. What the three experiments found

### Exp.1 — Scan timing / target motion / reference pose (`exp1_timing_motion/`)
- One pose timestamp per frame (line 1 `.pose`); the in-repo README only says "absolute seconds";
  scan-**END** anchoring is an upstream-EPOS assertion carried by prior audits, **not re-verifiable
  from repo assets**. **No per-point timestamps, no deskew, no pose interpolation, no separate
  extrinsic** (pose is directly target↔LiDAR; model in target frame).
- Framerate is adaptive; an isolated-dropout rule finds **0 discontinuous gaps**; all inter-frame
  motion is divided by the **real** dt (never adjacent-interval-as-scan-duration).
- Motion regimes: ω median VI 8.15, IV 4.90, II/III 1.06 °/s.
- The frozen support mask (IV 156/2428, II 428/1253, III 371/1302, VI 501/501) is a **range/viewing-
  geometry gate, not a motion-speed or low-residual gate**: selected vs unselected angular speed is
  essentially identical (e.g. II 1.063 vs 1.063, IV 5.05 vs 4.90).
- Within-trajectory association of angular speed with Raw error and with Patch−Raw gain is negligible
  (|Spearman ρ| ≤ 0.12) — no descriptive signature of a fast-motion/deskew artifact.
- **`EXACT_DESKEW_DIAGNOSTIC_BLOCKED`** (xyz-only clouds): intra-scan distortion cannot be measured
  or ruled out at point level; no scan-time model was invented.

### Exp.2 — Iteration budget 40/80/160, Raw vs Patch (`exp2_iter_budget/`)
- Pre-registered 40 equal-spaced diagnostic frames/trajectory (`diagnostic_frames.json`).
- **Fidelity:** instrumented solver reproduces shipped budget-40 results to max |Δet| = 2.8e-14 mm
  and 320/320 matching iteration counts — the frozen path is unchanged.
- **Paired-median Patch−Raw gain stays positive at every budget on every trajectory**
  (VI ≈ +43.6; IV +5.05→+6.29; II ≈ +12.0–12.2; III +10.4–12.0 mm). No direction reversal; no
  systematic ranking change; winner flips 40→160 are 0 on VI/II/III and 10% near-tie frames on IV.
- **80→160 is numerically stable** (median |Δet| 0 on VI/II/III, ≤0.15 mm on IV) →
  **`BUDGET_STABILITY_SUPPORTED`**. IV is not fully converged at 40 (90% cap-hit) but raising the
  budget moves Raw and Patch together and keeps Patch ahead; ≤10% of frames stop on the frozen
  rotation basin boundary at every budget (not budget-induced).
- The main Patch-vs-Raw result is **not an artifact of the 40-iteration truncation**. Not a global
  convergence proof.

### Exp.3 — Direct pose-active projection, Eq. (12)–(16) (`exp3_pose_active/`)
- 1456 real frames (VI 501; IV 156; II 428; III 371), p2p + p2l. Fixed-corr analytic J/W/H/g,
  Δξ_FO=−H†g, δ_PA=P_{J,W}δ, RMS_PA, alongside rematching g_FD/B_FD/−B_FD†g_FD and actual ξ*.
- Algebra closes to machine precision (P²=P ≤5e-14; normal-equation residual ≤2e-13; RMS_PA
  identity ≤1e-11 mm; FD reproduces cache ≤1e-13); **full rank 6/6 everywhere**, cond ≈ 7–8,
  rcond-insensitive (direction cosine = 1.000 across 1e-10…1e-6).
- Pose-active residual fraction RMS_PA/RMS ≈ 0.30–0.39 on every frame. Analytic fixed-corr
  translation direction vs actual ξ*: median cosine 0.94 (VI), 0.95 (IV), 0.77 (II), 0.81 (III);
  **rematching FD direction 0.96–0.995 on all trajectories**. One analytic step underestimates the
  iterated magnitude (ratio 0.25–0.42); FD magnitude ratio ≈ 1.1–1.5 (VI 2.18).
- Verdict **DIRECT_SUPPORT_IN_LOCAL_WORKING_DOMAIN**: supported as a local, correspondence-stable,
  first-order statement; the fixed-corr single step is weaker on far-held II/III (correspondence
  re-matching is the gap, not conditioning). p2l is the weaker secondary arm.
- **`SYNTHETIC_DIRECT_VALIDATION_BLOCKED`**: the 1920 synthetic runs cache only scalar outcomes (no
  J/W/δ/δ_PA/SVD/displacement vectors) and regeneration is `hash()`-seeded/non-reproducible; not
  regenerated per instruction.

---

## 2. VERDICT

# ✅ GO_WITH_REFRAMING

The three critical evidence gaps are closed well enough to **proceed to Phase-2** (cheap historical
baselines, Full 2×2 ablation, translation–rotation joint evaluation), **but the claim must stay
framed as a *structured scan-to-model discrepancy under a fixed computational budget, corrected by
frozen historical compensation***. The evidence does **not** license upgrading the paper to a pure
geometry-only causal mechanism or a universal pose-active theory.

### Why not STOP
- No budget-induced reversal or systematic ranking change (Exp.2); the comparative result survives
  removing the iteration cap and is numerically stable 80→160.
- The pose-active chain is algebraically exact and directly supported in-domain (Exp.3).
- Timing/motion does not overturn the explanation and the support mask is not a motion/low-residual
  selection (Exp.1).

### Why not unconditional GO (the required reframing constraints)
1. **Pose-active theory is local/first-order only.** State the working domain explicitly:
   reference-started, well-conditioned (full rank, cond ≈ 7–8), correspondence-stable; predicts
   *direction/local tendency*, not converged magnitude; on far-held views the single fixed-corr step
   is noisier and the iterated/rematching (FD) prediction is the one that stays near-exact. Do not
   claim universality or exact magnitude prediction.
2. **Keep "fixed computational budget" language.** Report that IV is partly cap-limited at the frozen
   40 (comparative conclusion unchanged; 80→160 stable). Do not call 40-cap results "converged";
   `BUDGET_STABILITY_SUPPORTED` ≠ global convergence proof.
3. **Motion/deskew caveat stays in.** State xyz-only data, single timestamp/frame (scan-END per
   upstream source, not independently verifiable here), `EXACT_DESKEW_DIAGNOSTIC_BLOCKED`; present
   Exp.1 as association only, never as a motion-distortion causal proof or disproof.
4. **III remains post-hoc / secondary diagnostic** — never relabel it an untouched confirmation.
5. **Disclose the two BLOCKED items honestly** (point-level deskew; synthetic direct-validation
   intermediates) instead of substituting regenerated/modelled data.
6. Phase-1 does **not** change any published result number or conclusion; the reframing is wording /
   claim-scope only.

### Gate for Phase-2
Proceed with the second-priority experiments as written (Direct-Vector DBS, Global-Vector Bias,
Full 2×2 ablation, translation–rotation joint evaluation), keeping every frozen parameter and the
III/post-hoc and fixed-budget constraints. Stop again for review if any Phase-2 result contradicts
the three supports above (in particular if a trivial vector baseline removes the Patch advantage or
the Full reversal tracks aggregation weighting rather than view conditioning).

---

## 3. Artifact index (all new, under `revision_experiments/`)
- `rev_common.py` — read-only reuse of frozen cores; faithful instrumented ICP; analytic pose-active.
- `exp1_timing_motion/`: `timing_semantics.md`, `motion_frame_metrics.csv`,
  `support_selected_vs_unselected.csv`, `fig_timing_motion.png`.
- `exp2_iter_budget/`: `diagnostic_frames.json` (pre-registered), `iteration_budget_framewise.csv`,
  `iteration_budget_summary.csv`, `fig_iteration_budget.png`, `iteration_budget_decision.md`.
- `exp3_pose_active/`: `pose_active_direct_framewise.csv`, `pose_active_numerical_checks.csv`,
  `fig_pose_active_direct_validation.png`, `pose_active_decision.md`.
- (`_*.pkl/npz` are local intermediates that reproduce the listed outputs.)

**Stopping here for review as requested — experiments 1–3 complete; Phase-2 not started.**
