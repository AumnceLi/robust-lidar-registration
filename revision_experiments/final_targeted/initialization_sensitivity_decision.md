# Task 3 — Small LOCAL initialization sensitivity (frozen solver; 3840 perturbed + 320 reference runs)

**Verdict: `INIT_STABLE_LOCAL`.** Scope is strictly LOCAL sensitivity around the reference pose; this is **not** evidence of global convergence, a large capture basin, or deployment-ready initialization robustness. Levels L1/L2/L3 = (10 mm,0.5°)/(30 mm,1°)/(50 mm,2°) are **sensitivity probes, not mission tolerances or certified convergence radii.** Methods: Raw, Huber, Patch, Patch+Huber only (no Full/DBS/Trim/new method). 20 pre-fixed frames/trajectory (even positions of Exp.2's 40-frame list; `initialization_frames.json`, fixed before any result), 4 sign-balanced deterministic directions with cyclically-paired rotation axes, same SE(3) local-chart (rodrigues exponential) warm start for all four methods, frozen 40-iteration main budget and all frozen settings; failed cases never got extra iterations. III is post-hoc.

## Solver fidelity (hard gate, passed before production)

The instrumented frozen solver is bit-identical to `g_common.robust_icp` at x0=None and under warm start (max |Δξ| = 0), and reproduces frozen replay79 reference results to 2.8e-14 mm with matching iteration counts on the 128 in-support selected runs; the other 192 selected frames are out-of-support (no replay row) and use the same frozen solver at x0=None as reference.

## Stability across L1→L3

- Median final translation error barely moves with perturbation size (max L1→L3 median drift 3.67 mm across every trajectory/method); median initialization degradation Δinit is negligible (median |Δinit_t| 0.262 mm).
- **Raw vs Patch:** the paired Patch−Raw translation gain is positive at every level and essentially flat: VI [np.float64(45.0), np.float64(44.7), np.float64(44.6)]; IV [np.float64(5.0), np.float64(5.2), np.float64(5.8)]; II [np.float64(9.6), np.float64(9.7), np.float64(9.6)]; III [np.float64(7.8), np.float64(8.1), np.float64(8.4)] mm.
- **Huber vs Patch+Huber:** VI strongly positive and flat; II positive at all levels but the margin attenuates with size (6.3→3.5→2.8 mm, never reverses); III small-positive and flat; on the IV diagnostic subset (19/20 frames out-of-support) Patch+Huber is a few mm BELOW Huber at **every** level including the reference start ([np.float64(-3.2), np.float64(-3.6), np.float64(-2.8)]; reference gain -3.0), i.e. a level-independent subset offset, not perturbation-induced basin shrinkage.

## Boundary / termination behavior

- Basin boundary-clip fraction is small and FLAT across L1–L3; Huber and Patch+Huber never clip; Patch clips no more often than Raw (max Patch−Raw difference +0.000) and Patch+Huber no more often than Huber (+0.000). There is **no systematic Patch boundary penalty**.
- Hitting the frozen 40-iteration cap is common for these slowly-converging scans but is a termination descriptor, not a basin escape: cap hits never translate into error growth, and Patch reaches the cap less often than Raw. The cap was never raised. On a single post-hoc III frame the first Kabsch step already exceeded the 0.30 m basin (24 runs, Raw and Patch alike); following the frozen solver those runs terminate at iteration 1 with a NaN final_objective, a recorded translation-boundary flag, and a finite clipped error — this is faithful frozen behavior, not a missing result.

## Initialization-degradation tail (|Δinit_t|, NOT a failure threshold)

The Patch field does not widen the local tail: Patch and Raw are near-identical and Patch is slightly tighter (p90/p99 |Δinit_t| — Raw 1.42/5.36 mm, Patch 1.19/5.21; runs >5 mm: Raw 11, Patch 10 of 960). The wider moderate tail belongs to the ROBUST-LOSS methods, present equally with and without Patch (Huber 4.88/17.88, Patch+Huber 6.13/15.94 mm) and concentrated at L3 on the mostly-out-of-support IV diagnostic frames; it is therefore not a Patch-field basin effect. The few >20 mm single-run degradations occur on the same hardest IV frame under BOTH Raw and Patch (rotation-boundary), again not Patch-specific.

## Tail behavior: p90 final error by trajectory × level (NOT a failure threshold)

| trajectory   | level   |   Raw_et_p90 |   Huber_et_p90 |   Patch_et_p90 |   PatchHuber_et_p90 |   Raw_eR_p90 |   Huber_eR_p90 |   Patch_eR_p90 |   PatchHuber_eR_p90 |
|:-------------|:--------|-------------:|---------------:|---------------:|--------------------:|-------------:|---------------:|---------------:|--------------------:|
| VI           | L1      |       173.2  |         159.05 |         126.25 |              113.71 |         5.11 |           4.62 |           5.68 |                5.27 |
| VI           | L2      |       173.17 |         159.06 |         126.21 |              112.84 |         5.12 |           4.71 |           5.68 |                5.34 |
| VI           | L3      |       173.2  |         158.97 |         126.04 |              112.32 |         5.15 |           4.82 |           5.77 |                5.58 |
| IV           | L1      |       178.36 |         133.72 |         177.34 |              125.62 |         5.74 |           3.22 |           5.99 |                4.24 |
| IV           | L2      |       179.46 |         133.85 |         176.13 |              129.47 |         5.81 |           3.24 |           6.01 |                4.19 |
| IV           | L3      |       179.65 |         134.2  |         176.09 |              133.95 |         5.8  |           3.67 |           6.01 |                4.26 |
| II           | L1      |        99.06 |          70.4  |          81.49 |               46.08 |         4.68 |           1.25 |           4.33 |                2.41 |
| II           | L2      |        99.51 |          70.67 |          81.49 |               46.15 |         4.77 |           1.27 |           4.43 |                2.44 |
| II           | L3      |       100.01 |          70.61 |          81.53 |               46.52 |         4.93 |           1.42 |           4.48 |                2.5  |
| III          | L1      |       102.97 |          73.17 |          77.38 |               47.2  |         2.76 |           1.53 |           3.92 |                2.9  |
| III          | L2      |       102.93 |          73.38 |          77.99 |               47.39 |         2.83 |           1.58 |           3.93 |                2.87 |
| III          | L3      |       103.29 |          73.65 |          78.16 |               49.04 |         3    |           1.65 |           3.91 |                2.93 |

## Decision

`INIT_STABLE_LOCAL`. Through L1–L3 the comparative ordering is qualitatively stable (no perturbation-induced ranking reversal), initialization degradation is sub-mm, and Patch-based methods show no systematic boundary or termination penalty. Disclose two nuances honestly: (i) the incremental Patch+Huber-over-Huber margin shrinks on II at the largest local probe but stays positive and does not reverse; (ii) on the mostly-out-of-support IV diagnostic subset Patch+Huber is a few mm below Huber at every level, an offset already present at the reference start rather than an effect of initialization. The local degradation tail is no wider for Patch than Raw; the wider moderate tail sits in the robust-loss methods (with and without Patch alike) and at L3 on out-of-support IV frames. These are LOCAL statements only; no global-convergence or deployment-robustness claim is made. III remains post-hoc / secondary.
