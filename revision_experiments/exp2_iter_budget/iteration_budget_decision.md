# Exp.2 — Iteration-budget sensitivity (40 / 80 / 160): decision

**What was varied:** `max_iterations ∈ {40,80,160}` only. Identical input frames, GT/reference
init (ξ=0), NN correspondence, distance rule, frozen basin boundary (0.30 m / 15°), frozen Patch
field, LS robust setting, and stopping tolerance (p2p tol = 1e-8). First round runs **Raw and
Patch only**. Diagnostic frames were fixed **before** any run (`diagnostic_frames.json`):
40 equal-spaced frames per trajectory in original time order (VI/IV/II/III; III labelled
post-hoc/secondary). No frame was chosen by error or method outcome.

**Fidelity check.** The instrumented solver is bit-faithful to frozen `g_common.robust_icp`:
at budget 40, max |Δ translation error| vs shipped master results = **2.8e-14 mm**, median 0,
0/320 rows differ by >1e-6 mm; iteration counts match on **320/320**. Hence budget 40 here is
exactly the published 40-cap state.

## Headline numbers (40 diagnostic frames/trajectory)

| Traj | budget | Raw et med mm | Patch et med mm | **paired gain med mm** | Patch-better frac | Raw/Patch cap frac |
|---|---|---|---|---|---|---|
| VI  | 40 | 162.40 | 116.99 | **+43.56** | 1.000 | .40/.40 |
| VI  | 80 | 162.61 | 117.04 | **+43.58** | 1.000 | .025/0 |
| VI  | 160 | 162.61 | 117.04 | **+43.58** | 1.000 | 0/0 |
| IV  | 40 | 150.25 | 140.95 | **+5.05** | .775 | .90/.90 |
| IV  | 80 | 158.16 | 148.32 | **+6.03** | .700 | .575/.575 |
| IV  | 160 | 158.60 | 148.63 | **+6.29** | .675 | .025/.025 |
| II  | 40 | 53.75 | 40.74 | **+11.98** | .850 | .625/.65 |
| II  | 80 | 53.97 | 41.11 | **+12.24** | .850 | .075/.05 |
| II  | 160 | 53.97 | 41.11 | **+12.24** | .850 | 0/0 |
| III* | 40 | 52.02 | 40.95 | **+12.04** | .700 | .45/.65 |
| III* | 80 | 52.02 | 40.92 | **+10.41** | .700 | .025/.025 |
| III* | 160 | 52.02 | 40.92 | **+10.53** | .700 | 0/0 |

\* III = post-hoc / secondary diagnostic, never an untouched confirmation.

### Terminal-pose change when budget is raised (median absolute |Δet| mm; full table in summary CSV)

| Traj | 40→80 Raw/Patch | 80→160 Raw/Patch | 40→160 Raw/Patch | winner-flip frac 40→160 |
|---|---|---|---|---|
| VI  | 0 / 0 | 0 / 0 | 0 / 0 | 0.000 |
| IV  | 8.18 / 6.93 | 0.15 / 0.06 | 8.28 / 6.95 | 0.100 |
| II  | 0.07 / 0.03 | 0 / 0 | 0.07 / 0.03 | 0.000 |
| III | 0 / 0.03 | 0 / 0 | 0 / 0.03 | 0.000 |

Termination at 40 is often cap-limited (VI 40%, IV 90%, II ~63%, III 45–65%); by 160 virtually
all frames terminate on tolerance (≤2.5% cap). Boundary triggers are **rotation**-boundary only,
small (VI 0, IV 10%, II/III 5%), and identical across budgets and methods (same frames), i.e. not
induced by the budget change.

## GATE evaluation

1. **Does the Patch-vs-Raw improvement direction reverse at 80/160 on a main trajectory?**
   **No.** The paired-median translation gain stays positive at every budget on every trajectory
   (VI ≈ +43.6; IV +5.1→+6.3; II ≈ +12.0–12.2; III ≈ +10.4–12.0). The method ordering
   (Patch below Raw in translation error) is preserved.
2. **Does the ranking change systematically?** **No.** Patch-better fraction is stable (VI 1.00;
   II .85; III .70); IV drifts .775→.675 but stays a majority, and its median gain does not shrink
   (slightly grows). IV has 10% individual near-tie winner flips 40→160, with **zero** flips on
   VI/II/III; these are tie-level frame changes, not a systematic reordering.
3. **Is 80→160 stable?** **Yes to numerical precision on VI/II/III** (median |Δet| ≤ 0.03 mm) and
   negligible on IV (≤0.15 mm).

## Decision: `BUDGET_STABILITY_SUPPORTED`

- The main Patch-vs-Raw result is **not an artifact of the 40-iteration truncation**: removing the
  cap preserves the direction, the ordering, and (on VI/II/III) the exact terminal pose.
- IV is the one trajectory not fully converged at 40 (90% cap); extending the budget moves both
  Raw and Patch by ~7–8 mm while keeping Patch ahead. This should be reported transparently (IV
  numbers move slightly with budget) but it does **not** trigger the reversal gate.
- Because the GATE did not trip, we are **not** forced to relabel the effect as merely
  "different local optima under a fixed computational budget"; the fixed-budget framing remains a
  valid, conservative description.
- This is **not** a global-convergence proof: ≤10% of frames stop on the frozen rotation basin
  boundary at every budget, and the statement is local (GT/reference-started) by design.

Artifacts: `iteration_budget_framewise.csv`, `iteration_budget_summary.csv`,
`fig_iteration_budget.png`, `diagnostic_frames.json` (pre-registered), `_histories.npz`.
