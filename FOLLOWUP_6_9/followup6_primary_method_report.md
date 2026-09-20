# Follow-up Item 6 — Fair primary-method paired comparison

**Status: COMPLETE (frozen analysis; no re-run, no tuning, no II/III-based selection).**
**Generated:** 2026-09-11. **Inputs:** `POSE_AUDIT/results/master_pose_results_frame.csv` (the frozen
master; its `block` column is the existing frozen block definition and is used verbatim).
**Scope:** primary = in-support frames, VI (501, 6 frozen orientation blocks), IV (156, 4 blocks),
II (428, 9 blocks), III (371, 8 blocks). Methods: Raw, Huber, Trim, Global, Patch, Full
(Estimated Full excluded — not a primary method).

## Convention (locked before analysis)

- **benefit = comparator_error − target_method_error**, so benefit > 0 means the *target* method is
  better. "Patch vs Huber" therefore reports `Huber − Patch`.
- **Paired unit = the frozen block.** Frame-level paired benefits are first computed on matched
  frames, then reduced to one median benefit per block; across-block inference uses these K block
  effects (median, IQR, block bootstrap 95% CI resampling the K block effects, B=2000, seed 42
  translation / 43 rotation), an **exact two-sided sign test** (binomial p=0.5), and Wilcoxon
  signed-rank **only as an auxiliary** (it never replaces the block effect/sign test).
- Marginal block-aware CI uses the identical stage-3 block bootstrap (resample blocks → pool →
  median). **Self-check: every marginal median/CI reproduces the frozen `master_summary.csv` to
  ≤ 1.4×10⁻¹⁴**, so no statistic here comes from a new pipeline.

## A. Marginal medians (primary scope)

Translation median error, mm:

| method | VI | IV | II | III |
|---|---:|---:|---:|---:|
| Raw | 161.41 | 160.42 | 66.15 | 75.04 |
| Huber | 148.89 | 132.56 | 50.90 | 55.89 |
| Trim | 144.77 | 125.20 | 47.32 | 55.03 |
| Global | 157.00 | 153.38 | 55.15 | 65.40 |
| **Patch** | **116.82** | **126.26** | **41.78** | **41.30** |
| Full | 76.86 | 82.90 | 68.86 | 51.24 |

Rotation median error, deg:

| method | VI | IV | II | III |
|---|---:|---:|---:|---:|
| Raw | 4.509 | 4.006 | 1.774 | 1.658 |
| Huber | 3.947 | 3.401 | 1.049 | 1.047 |
| Trim | 3.773 | 3.222 | 1.051 | 1.153 |
| Global | 4.506 | 4.008 | 1.775 | 1.655 |
| Patch | 4.667 | 4.000 | 1.269 | 2.116 |
| Full | 2.881 | 2.464 | 2.248 | 2.641 |

(Full IQR/CI and all per-method block-aware CIs are in `followup6_primary_method_summary.csv`.)

## B. Paired BLOCK effects — translation (median block benefit, [95% CI], k/K, exact sign p)

| comparison | VI | IV | II | III |
|---|---|---|---|---|
| Patch vs Raw | 60.85 [56.3,65.1] 6/6 p=.031 | 29.71 [12.9,54.6] 4/4 p=.125 | 16.71 [3.5,34.4] 7/9 p=.180 | 27.29 [12.4,47.5] 8/8 p=.008 |
| **Patch vs Huber** | 29.37 [26.7,32.1] 6/6 p=.031 | **0.62 [−20.5,24.4] 2/4 p=1.000** | 5.56 [−2.9,13.1] 5/9 p=1.000 | 12.21 [−2.0,27.7] 6/8 p=.289 |
| Patch vs Trim | 22.21 [18.9,24.7] 6/6 p=.031 | −7.63 [−30.3,13.4] 2/4 p=1.000 | 2.62 [−4.5,9.5] 5/9 p=1.000 | 7.72 [−4.3,20.4] 6/8 p=.289 |
| Patch vs Global | 38.19 [33.3,43.4] 6/6 p=.031 | 24.43 [11.4,35.1] 4/4 p=.125 | 5.21 [−2.2,13.0] 5/9 p=1.000 | 24.29 [12.4,37.0] 8/8 p=.008 |
| Full vs Raw | 82.81 [78.9,86.3] 6/6 | 73.06 [57.0,88.2] 4/4 | 1.67 [−17.8,17.1] 5/9 | 22.60 [8.0,38.5] 7/8 |
| Full vs Huber | 70.33 [67.1,73.5] 6/6 | 43.96 [27.3,58.5] 4/4 | **−14.20 [−35.0,2.7] 3/9 p=.289** | 7.52 [−7.3,22.7] 5/8 |
| Full vs Trim | 66.17 [63.0,69.2] 6/6 | 36.72 [20.2,51.4] 4/4 | **−18.79 [−39.0,−2.0] 2/9 p=.039** | 3.03 [−11.7,18.2] 5/8 |

## B'. Paired BLOCK effects — rotation

| comparison | VI | IV | II | III |
|---|---|---|---|---|
| Patch vs Raw | −0.001 | 0.000 | +0.231 [0.02,0.50] 8/8 p=.008 | 0.000 |
| Patch vs Huber | −0.885 [−1.0,−0.75] 0/6 p=.031 | −0.636 [−1.0,−0.25] 0/4 | −0.303 [−0.6,0.05] 2/9 | −0.846 [−1.2,−0.45] 0/8 p=.008 |
| Patch vs Trim | −0.671 0/6 | −0.483 0/4 | −0.306 2/9 | −0.787 0/8 p=.008 |
| Patch vs Global | 0.000 | 0.000 | +0.231 8/8 p=.008 | 0.000 |
| Full vs Raw | +1.615 6/6 | +1.543 4/4 | −0.231 2/9 | −0.692 0/8 p=.008 |
| Full vs Huber | +1.101 6/6 | +0.938 4/4 | −1.099 1/9 p=.039 | −1.538 0/8 p=.008 |
| Full vs Trim | +0.887 6/6 | +0.786 4/4 | −1.102 1/9 p=.039 | −1.479 0/8 p=.008 |

Auxiliary Wilcoxon p-values are in the summary CSV and are consistently *less* decisive than the
exact block sign test (as expected with K=4…9); they never override a sign-test conclusion.

## The three flagged marginal contrasts — marginal gap vs paired block increment

The marginal-median ordering overstates Patch's paired increment because blocks differ in severity:

| contrast | marginal medians | marginal gap | **paired block benefit** |
|---|---|---:|---|
| IV: Huber 132.6 vs Patch 126.3 | 132.56 / 126.26 | 6.30 mm | **+0.62 mm, only 2/4 blocks, CI crosses 0** |
| II: Huber 50.9 vs Patch 41.8 | 50.90 / 41.78 | 9.12 mm | **+5.56 mm, 5/9 blocks, CI [−2.9,13.1]** |
| III: Huber 55.9 vs Patch 41.3 | 55.89 / 41.30 | 14.59 mm | **+12.21 mm, 6/8 blocks, CI [−2.0,27.7]** |

On IV the apparent 6.3 mm marginal gain is essentially block composition; the fair paired increment
is ≈0.6 mm and is not directionally robust. On II/III the paired increment is real in direction but
smaller than the marginal gap and, with only 9/8 blocks, its CI includes 0.

## Answers to the five required questions

**1. Patch relative to Huber — true increment?** Translation block benefit: VI +29.4 mm (6/6,
p=.031, large and resolved); IV +0.6 mm (2/4, unresolved); II +5.6 mm (5/9); III +12.2 mm (6/8).
So Patch adds a *large, resolved* gain only on the development trajectory VI; on the three external
trajectories the direction is positive on all three but the magnitude is modest (0.6–12 mm) and not
block-significant at K=4…9. It is **not** the 6–15 mm the marginal medians suggest.

**2. Patch relative to Trim?** VI +22.2 mm (6/6); IV **−7.6 mm (2/4 — Patch is slightly worse)**;
II +2.6 mm (5/9); III +7.7 mm (6/8). Patch does not uniformly beat the trimmed estimator: on IV
Trim is at least as good, and only VI shows a clear Patch advantage.

**3. Patch relative to Global?** This is the most consistent contrast: +38.2 (VI, 6/6), +24.4
(IV, 4/4), +5.2 (II, 5/9), +24.3 (III, 8/8, p=.008). Patch beats the single global correction on
**all four** trajectories, resolved on VI and III. The local/patch structure is clearly superior to
one global vector; the contest with *robust losses* is much closer.

**4. Does the translation gain carry a rotation cost?** Relative to **Raw**, Patch is
rotation-neutral (≈0 on VI/IV/III, +0.23° better on II). Relative to the **robust losses Huber/Trim,
yes** — Patch gives back rotation on every trajectory: vs Huber −0.89/−0.64/−0.30/−0.85° (VI/IV/II/
III), vs Trim −0.67/−0.48/−0.31/−0.79°, with 0/6, 0/4, 2/9, 0/8 improved blocks. The robust
estimators are rotation-accurate; Patch's translation improvement over them is bought with a small
(≈0.3–0.9°) rotation cost. (Item 7 tests whether a robust loss on the corrected target recovers it.)

**5. Directionally consistent across the three non-development trajectories IV/II/III?**
- Patch > Global (translation): **consistent (+ on all three; 4/4, 5/9, 8/8 blocks).**
- Patch > Huber (translation): positive on all three but weak/unresolved (2/4, 5/9, 6/8).
- Patch > Trim (translation): **not consistent** (− on IV, + on II/III).
- Patch rotation cost vs Huber/Trim: **consistent (negative on all three).**
- Full vs robust baselines: **not consistent** — translation + on IV, − on II, small + on III;
  rotation + on IV but − on II and III. Full's view-conditioned gain does not transfer in direction
  the way Patch's local correction does (analysed mechanistically in Item 9).

## Bottom line
Against the single global correction Patch is a consistent, block-supported improvement. Against the
strong *robust-loss* baselines the fair paired increment is smaller than marginal medians imply, is
trajectory-dependent (large only on VI), is absent vs Trim on IV, and is accompanied by a small but
consistent rotation cost. Full adds a large, reliable gain only on VI/IV and is a **net negative on
II** (Full vs Trim −18.8 mm, 2/9 blocks, p=.039).

## Provenance & verification
- Frame/block rows carry `trajectory, order, scan, block, in_support` (frame- and block-level
  provenance); blocks are the frozen master blocks, never recomputed.
- Marginal pipeline reproduces frozen `master_summary.csv` to 1.4×10⁻¹⁴.
- No parameter was changed; no method/contrast was chosen using II/III outcomes; no seed/condition/
  subset selection. Files: `followup6_primary_method_frame.csv`, `..._block.csv`, `..._summary.csv`.
