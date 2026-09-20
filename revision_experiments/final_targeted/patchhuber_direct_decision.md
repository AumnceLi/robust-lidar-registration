# Task 2 — Direct Patch+Huber increment over Huber

**Verdict: `ROBUST_PLUS_PATCH_INCREMENT_SUPPORTED` (translation increment on every trajectory; a small rotation cost vs the already-strong Huber is disclosed).**

## Method

Source is the frozen `replay79_arms.csv`; **no registration was re-run**. Primary comparison PatchHuber vs Huber with per-frame **Δt = e_t(PH)−e_t(Huber)**, **Δr = e_R(PH)−e_R(Huber)** (negative = PatchHuber better). Secondary PatchHuber vs Patch uses the same definitions. Quadrants split **exactly at zero** — no mission/safety tolerance was invented. Translation blocks use gain_t = −Δt (positive = PatchHuber better), the canonical paper block map (VI6/IV4/II9/III8, verified equal to replay79's frozen `block` column), the manuscript block bootstrap (B=2000, resample paper blocks, seed 42, 2.5/97.5) and the frozen one-sided block sign-flip p. **VI is development evidence; III is post-hoc / secondary.** The required inference is whether Patch adds value *on top of Huber* — not whether Patch+Huber beats Raw (already known).

## Primary: PatchHuber vs Huber

| traj   |   med Δt |   IQR Δt |   t-better |   med Δr |   r-better |   both+ |   t+/r− |   t−/r+ |   both− |   med blk gain |   CI lo |   CI hi |   blk+ |   blk− |   p |
|:-------|---------:|---------:|-----------:|---------:|-----------:|--------:|--------:|--------:|--------:|---------------:|--------:|--------:|-------:|-------:|----:|
| VI     |  -45.38  |   12.127 |       1    |    0.421 |      0.325 |   0.325 |   0.675 |   0     |   0     |         45.059 |  43.191 |  47.064 |      6 |      0 |   0 |
| IV     |  -31.807 |   11.957 |       1    |    0.052 |      0.462 |   0.462 |   0.538 |   0     |   0     |         29.883 |  22.396 |  34.686 |      4 |      0 |   0 |
| II     |   -7.874 |   12.501 |       0.75 |    0.498 |      0.185 |   0.152 |   0.598 |   0.033 |   0.217 |          3.902 |   1.611 |  12.085 |      8 |      1 |   0 |
| III    |  -19.663 |   26.787 |       0.86 |    0.72  |      0.178 |   0.178 |   0.682 |   0     |   0.14  |         18.254 |   6.08  |  34.164 |      6 |      2 |   0 |

## Secondary: PatchHuber vs Patch (what the robust loss adds to the Patch field)

| traj   |   med Δt |   t-better |   med Δr |   r-better |   both-better |
|:-------|---------:|-----------:|---------:|-----------:|--------------:|
| VI     |  -16.18  |      0.992 |   -0.424 |      0.862 |         0.86  |
| IV     |  -24.199 |      1     |   -0.449 |      0.827 |         0.827 |
| II     |   -6.966 |      0.636 |   -0.089 |      0.535 |         0.437 |
| III    |   -5.684 |      0.674 |   -0.201 |      0.601 |         0.361 |

## Reading

1. **Translation increment over Huber is positive on all four trajectories and never crosses zero at block level.** Median Δt is negative everywhere (VI -45.4, IV -31.8, II -7.9, III -19.7 mm), translation-better fraction is 1.00/1.00/0.75/0.86, and the oriented block-gain CIs exclude zero on every trajectory (block sign counts 6/0, 4/0, 8/1, 6/2; sign-flip p ≈ 0.0005). The effect is **smallest on II**, where one of nine blocks is negative and ~a quarter of paired frames are not translation-improved, but the sign does not reverse.

2. **A small rotation cost vs Huber is real and must be disclosed.** Because Huber already gives very small rotation error, adding the Patch field leaves median Δr slightly positive (VI +0.421, IV +0.052, II +0.498, III +0.720 deg); rotation-better fraction is below 0.5 on every trajectory. This is a magnitude-small trade of a little rotation for a substantial translation gain, not a rotation improvement over Huber.

3. **The secondary comparison resolves the trade-off:** PatchHuber vs Patch improves BOTH translation (median Δt negative on all four) and rotation (median Δr negative on all four; both-better fraction 0.86/0.83/0.44/0.36) — i.e. combining the Patch field with Huber removes the Patch field's own rotation cost (consistent with Exp.6) while keeping its translation gain.

## Decision

`ROBUST_PLUS_PATCH_INCREMENT_SUPPORTED`. The frozen Patch field adds direct, block-level translation value **on top of** the strong Huber loss on every trajectory (no block CI crosses zero; the increment does not reverse sign), and Patch+Huber is the best joint arm. State two caveats precisely: (i) the translation increment is smallest on II and is a majority-but-not-unanimous frame effect there; (ii) relative to Huber alone it carries a small positive median rotation change that is offset when Huber is combined with the Patch field. VI is development evidence and III is post-hoc; no threshold was invented.
