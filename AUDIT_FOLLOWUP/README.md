# Post code-audit follow-up (frozen replay batch: items 1–5)

Everything here is a **frozen, non-tuning** replay of the existing repository. No parameter was
refit, no seed/frame was selected on outcome, Dataset III stays an **appended frozen diagnostic**
(not reopened as development data). All code reuses the frozen predictor
`VI_ONLY_PREDICTOR_FROZEN.npz` (SHA256 asserted), the frozen model/PCA-normals/24 patches, and the
exact solvers in `s0_common.py / m_common.py / g_common.py`.

## Deliverables (the requested file names, this folder)

| Item | Request | Outputs |
|---|---|---|
| 1 (P0) | nuisance control before/after gradients | `nuisance_gradient_before_after.csv`, `nuisance_gradient_report.md` |
| 2 (P0) | literal patch-label permutation placebo | `patch_label_placebo_frame.csv`, `patch_label_placebo_block.csv`, `patch_label_placebo_report.md` |
| 3 (P0) | III deterministic frozen replay + III-DBS | `iii_frozen_replay_frame.csv`, `iii_direction_cosine.csv`, `iii_dbs.csv` |
| 4 (P0) | Figure 2C–E real statistical definition / lineage | `figure2_provenance.md`, `figure2_plot_statistics.csv` |
| 5 (P1) | pose-active mechanism before/after closed loop | `mechanism_before_after.csv`, `mechanism_compensation_link.md` |

Reproduction scripts and their verification logs are under `scripts/` (t1_*.py … t5_*.py; rerun in
that directory, Python with numpy/pandas/scipy/scikit-style deps already used by the repo).

## Conventions used everywhere (locked to the shipped code)

- Pose chart `xi = [tx,ty,tz,rx,ry,rz]` (m, rad; translation then rotation); error norms reported as
  translation mm and rotation degrees. Channel `p2p` is point-to-point LS, `p2l` point-to-plane LS;
  the manuscript primary is **p2p**, both channels are exported wherever relevant.
- Gradients are the frozen central-difference gradient of `robust_objective = mean(residual^2)`
  (FD step 5 mm / 0.25 deg). This equals **2×** the analytic Gauss-Newton normal `mean Jᵀδ` that
  drives `kabsch_step` (the Figure-4 note on the factor-2 relationship); item 5 reports ‖g‖ in this
  frozen convention and computes `‖P_{J,W}δ‖ = sqrt(gᵀH⁻¹g)` from the factor-1 normal equations.
- Scope: "primary" = in-support frames for VI/IV/II/III; **V is analyzed on ALL 1868 frames**
  (permanently out-of-support, supportive role). Blocks: VI = 6 frozen orientation blocks; external
  primary blocks = rank within in-support subset //50 (matches master/Figure 7); V uses temporal
  order//50 over all frames.
- Pose errors are never re-solved in items 1/5/2's comparison columns: they are taken from the
  frozen solver outputs and match the shipped master results exactly.

## Verification evidence (all pass)

- Item 1: 6 frames × dataset × 4 conditions independently re-derived with `grad_hess`+ICP vs saved
  `ext_objective` arrays → max abs diff **0.0** (gradient, J0, realized xi).
- Item 2: Raw/true-Patch arms reproduce shipped g1 `M0_raw_p2p`/`M4_patch_corr` to machine
  precision; primary permutation preserves the 24-vector multiset and its norm histogram **exactly**
  (max diff 0.0); one pre-declared seed (20240910) + a fixed 4-seed null band, no seed selection.
- Item 3: predicted-`dxi` replica matches saved `ext_predict_ii` to **0.0** (validation on II before
  use on III); III realized 6-vector matches saved `g1_iii` M0 to **5.7e-14 mm / 1.8e-15 deg**; the
  B1/DBS rule reproduces shipped IV/II `frame_results.csv` mhat/dbs_ete to **0.0**.
- Item 4: independent re-derivation matches the shipped Figure-2 plotted tables to ≤1.4e-14; the
  band is **IQR (25–75%)**, the line is the **median**, the unit is one supported VI scan's
  patch-median, bins are 8 fixed equal-width range bins (no SD/CI/fit).
- Item 5: analytic xi=0 gradient vs frozen FD gradient agrees to the expected O(h²)=~3e-4 truncation
  (p2p translation FD objective is quadratic → exact); attached pose errors match master medians.

## Headline results

- **Item 1.** Frozen VI-fit nuisance operators cut translation gradient on in-support IV/II
  (‖g_t‖ ×0.50/0.57/0.80 and ×0.37/0.34/0.63 for N1/N2/N3) but RAISE it on out-of-support V
  (×1.20/1.28/1.15); N2 trades translation for rotation. Residual RMS changes little (×0.87–1.08),
  again gradient responds more than raw mismatch size.
- **Item 2.** The correctly labelled Patch map lowers translation error in **every** block
  (II 9/9, III 8/8, IV 4/4, V 38/38, VI 6/6); a label-scrambled map of the SAME vectors is weak or
  null (V 18/38 blocks, median block effect ≈0). True Patch beats shuffled: II 7/9 (p=.039),
  III 7/8 (p=.016), V 38/38 (p≈0), VI 6/6 (p=.031). The effect is carried by spatial assignment, not
  by the correction-magnitude multiset.
- **Item 3.** III per-frame predicted/realized 6-vectors and both direction cosines are now stored.
  In-support translation predicted↔realized cosine median 0.86. Frozen **III-DBS does not help**:
  median ETE 75.04 → 108.83 mm, only 26.4% of frames improve (rotation unchanged by construction) —
  consistent with the prior "III out of support" conclusion; a high view-direction cosine (0.94)
  does not make subtraction beneficial.
- **Item 4.** Figure 2 caption can now state exact statistics; see `figure2_provenance.md` §6 for the
  caption-ready sentence and `figure2_plot_statistics.csv` for every cell/bin sample count.
- **Item 5.** On II, Raw→Full lowers RMS(δ) (84.7→77.4 mm), ‖g_t‖ (0.0516→0.0307) and
  ‖P_{J,W}δ‖ (28.3→20.7 mm) at xi=0 yet realized translation is flat-to-worse (66.15→68.86 mm) and
  rotation worse (1.77→2.25°); Raw→Patch lowers these more selectively and realizes 66.15→41.78 mm /
  1.77→1.27°. Across II blocks, Δ‖g_t‖ / Δ‖P_{J,W}δ‖ correlate with Δtranslation error (rho 0.87 /
  0.85): pose-actionable signal tracks benefit, but an over-smoothed view field yields no beneficial
  level shift — mismatch magnitude alone is not sufficient.

## Deliberately NOT produced here (avoid fabrication; per instruction)

These are absent from the repository and must not be invented; they are out of scope of files:
*why exactly 24 patches* (only the frozen procedure k=24, MiniBatchKMeans seed 42 is documented),
*task-level translation/rotation success thresholds*, *commit-level git history of the main project*,
and any *CAD mesh / face count* — the frozen model is a **67,870-point `.3d` point cloud, not a
mesh**. Items 6–9 (fair paired comparison vs Huber/Trim/Global, Patch+robust combinations,
equal-RMS matching, view-support diagnostics) and item 10 (non-GT initialization) were not run in
this batch, per "do 1–5 first".
