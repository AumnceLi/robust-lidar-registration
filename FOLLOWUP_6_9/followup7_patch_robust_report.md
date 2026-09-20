# Follow-up Item 7 — Patch × robust-loss complementarity

**Status: COMPLETE as a frozen, minimal mechanical combination (no new tuning, no method chosen on
II/III).** Generated 2026-09-11.

## What was actually run (and what was NOT)

Six frozen arms were evaluated on identical inputs — same aligned scan, same target frame, same
GT-local initialization (x0=0), same frozen solver `g_common.robust_icp`, same basin (0.30 m/15°):

| arm | target model | per-correspondence loss |
|---|---|---|
| Raw LS | nominal model | LS point-to-plane |
| Huber Raw | nominal model | Huber δ=1.345, MAD(1.4826) scale, raw-model NN-spacing floor |
| Trim Raw | nominal model | Trim keep=0.80 |
| Patch LS | nominal + **frozen view-independent μ_patch** (identical frozen μ_j for all three Patch arms) | LS |
| **Patch+Huber** | same corrected target | Huber with the *same* frozen δ/scale rule |
| **Patch+Trim** | same corrected target | Trim with the *same* frozen 0.80 |

The only new evaluations are the two crosses. They change **only the per-correspondence weights** on
the already-frozen corrected geometry — the minimal mechanical combination the task permits; no
parameter was fit and no II/III result entered the choice.

**Exact-reproduction gate (different code path vs the frozen master):** Raw LS / Huber / Trim /
Patch LS / Full LS reproduce the frozen g0/g1 results to **0.0 mm/deg on every used frame**
(VI 501, IV 156, II 428, III 371; `scripts/verify79_full.csv`). The crosses therefore inherit the
exact frozen machinery rather than an approximation.

Per-frame outputs (`followup7_patch_robust_frame.csv`): translation error, rotation error,
iterations, on-bound, n_points, mean weight (wmean), Σw, weight ESS = (Σw)²/Σw², retain fraction
and retained count. All arms converge (median 34–40 iterations; on-bound rate ≈0 except Raw/Patch on
II = 7.0%, which robustification removes: Patch+Huber 0.0%, Patch+Trim 0.5%). Huber mean weight
0.76–0.81; Trim retain fraction is exactly 0.80 (weight ESS ≈ 8.0–9.0 k of ≈10 k correspondences).

## Marginal medians (translation mm / rotation deg)

| arm | VI | IV | II | III |
|---|---|---|---|---|
| Raw LS | 161.41 / 4.509 | 160.42 / 4.006 | 66.15 / 1.774 | 75.04 / 1.658 |
| Huber Raw | 148.89 / 3.947 | 132.56 / 3.401 | 50.90 / 1.049 | 55.89 / 1.047 |
| Trim Raw | 144.77 / 3.773 | 125.20 / 3.222 | 47.32 / 1.051 | 55.03 / 1.153 |
| Patch LS | 116.82 / 4.667 | 126.26 / 4.000 | 41.78 / 1.269 | 41.30 / 2.116 |
| **Patch+Huber** | **102.86 / 4.308** | **102.14 / 3.535** | **40.13 / 1.531** | **32.19 / 1.733** |
| **Patch+Trim** | **96.15 / 4.476** | **89.88 / 3.455** | **40.52 / 1.629** | **37.58 / 2.161** |

## Paired BLOCK benefits (benefit = comparator − target; median [95% block-CI], k/K, exact sign p)

### Translation

| comparison (target vs comparator) | VI | IV | II | III |
|---|---|---|---|---|
| Patch+Huber vs Huber (geometry added to robust) | 45.06 [42.0,47.9] 6/6 p=.031 | 29.88 [7.3,35.1] 4/4 | 3.90 [0.92,11.8] **8/9 p=.039** | 18.25 [1.95,37.0] 6/8 |
| Patch+Huber vs Patch (robust added to patch) | 17.87 [9.8,20.4] 6/6 p=.031 | 27.73 [18.1,35.8] 4/4 | 3.92 [−2.9,22.5] 7/9 | 5.47 [−2.3,18.1] 6/8 |
| Patch+Trim vs Patch | 25.61 [13.9,30.5] 6/6 p=.031 | 40.80 [27.9,59.5] 4/4 | 3.92 [0.61,26.1] 7/9 | 2.65 [−18.3,22.4] 4/8 |
| Patch+Trim vs Trim | 47.33 [46.1,50.1] 6/6 p=.031 | 38.79 [14.3,39.5] 4/4 | 5.71 [−4.0,9.7] 7/9 | 16.55 [−1.97,19.9] 6/8 |

### Rotation

| comparison | VI | IV | II | III |
|---|---|---|---|---|
| Patch+Huber vs Huber | −0.434 [−0.63,−0.20] 0/6 p=.031 | −0.318 [−0.65,0.27] 1/4 | −0.449 [−1.04,−0.04] 1/9 p=.039 | −0.689 [−1.02,−0.03] 1/8 |
| **Patch+Huber vs Patch** (rotation recovered?) | **+0.425 [0.31,0.54] 6/6 p=.031** | **+0.304 [0.19,0.65] 4/4** | +0.120 [−1.19,0.42] 5/9 | +0.032 [−0.19,0.53] 4/8 |
| Patch+Trim vs Patch | +0.291 [0.14,0.45] 6/6 p=.031 | +0.346 [0.26,1.00] 4/4 | −0.202 [−1.66,0.51] 3/9 | −0.073 [−0.51,0.07] 3/8 |
| Patch+Trim vs Trim | −0.769 [−0.91,−0.69] 0/6 p=.031 | −0.557 [−0.97,0.39] 1/4 | −0.391 [−1.55,−0.09] 1/9 p=.039 | −1.029 [−1.49,−0.37] 0/8 p=.008 |

## Interpretation — complementary, not redundant (but the synergy is trajectory-dependent)

1. **The two mechanisms act additively on translation.** Adding Patch geometry to a robust loss
   helps (Patch+Huber vs Huber: +45.1/+29.9/+3.9/+18.3 mm; Patch+Trim vs Trim:
   +47.3/+38.8/+5.7/+16.6 mm), and adding a robust loss to Patch also helps (Patch+Huber vs Patch:
   +17.9/+27.7/+3.9/+5.5 mm; Patch+Trim vs Patch: +25.6/+40.8/+3.9/+2.6 mm). Both directions are
   positive on **all four** trajectories. This is complementarity: structured geometry correction
   and robust per-correspondence weighting attack different error components.

2. **The synergy is strong on VI/IV, weak/unresolved on II/III.** On VI and IV every block improves
   and the combined arms are decisively best (Patch+Trim IV 89.9 mm vs Patch 126.3 and Trim 125.2;
   Patch+Huber III 32.2 mm vs Patch 41.3 and Huber 55.9). On II the combined arms (40.1/40.5) are
   essentially tied with Patch alone (41.8) — block CIs cross 0; on III only Patch+Huber shows a
   clear extra gain. With K=4…9 the external-trajectory increments are directionally positive but
   mostly not block-significant.

3. **"Patch improves translation while robustification recovers rotation" — partially YES.**
   Item 6 showed Patch pays a small rotation cost vs Huber. Applying Huber **on the corrected
   target** recovers ≈0.43° (VI, 6/6) and ≈0.30° (IV, 4/4) of that cost (Patch+Huber vs Patch
   rotation positive). The recovery is incomplete: Patch+Huber is still 0.32–0.69° worse than pure
   Huber Raw, and on II/III the rotation recovery is ≈0 and unresolved. Trim behaves similarly but
   its residual rotation cost vs Trim Raw is larger.

4. **"Robustification destroys useful patch structure" — NO.** No cross arm is worse than Patch LS
   in translation on any trajectory (all four paired contrasts ≥0 in block median), and
   robustification additionally removes the II basin-bound hits (7.0%→0–0.5%). The structured
   correction is preserved, not eroded.

5. **This is not a new method.** Per the task, Patch+Huber/Patch+Trim are reported as frozen
   diagnostic combinations using existing parameters. They should be described in the manuscript as
   evidence that geometry correction and robust estimation are **complementary operators**, with the
   honest caveat that the extra benefit of stacking them is large on VI/IV but small and unresolved
   on II/III. There is **no basis here to promote a stacked estimator as a headline contribution**,
   and no parameter was tuned to produce these numbers.

## Provenance & verification
- Frame/block provenance (`trajectory, order, scan, block, in_support`) retained throughout; blocks
  are the frozen master blocks joined by `(trajectory, order)`, never recomputed.
- Constituent arms reproduce frozen g0/g1 exactly (0.0) on every used frame.
- Files: `followup7_patch_robust_frame.csv`, `..._block.csv`, `..._summary.csv`; raw replay
  `scripts/replay79_arms.csv`; gate `scripts/verify79_full.csv`.
