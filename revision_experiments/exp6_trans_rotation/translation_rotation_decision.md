# Exp.6 — Joint translation–rotation evaluation (existing frozen results, no re-run)

**Status: COMPLETE.** Source: `FOLLOWUP_6_9/scripts/replay79_arms.csv` (frozen robust_icp, in-support primary subset; VI all 501, IV 156, II 428, III 371). Per frame Δt=et(method)−et(base), Δr=eR(method)−eR(base) (negative = better). III is post-hoc.

**No mission-safety threshold is used:** the repo defines no pre-existing task tolerance (only solver tolerances), so per instruction no threshold-based analysis was invented.

## Four-quadrant fractions (and median Δt / Δr)

### Patch_vs_Raw

| traj   |   n |   med Δt |   med Δr | T↑R↑(both better)   | T↑R↓(t-better,r-worse)   | T↓R↑   | T↓R↓(both worse)   |
|:-------|----:|---------:|---------:|:--------------------|:-------------------------|:-------|:-------------------|
| VI     | 501 |   -43.51 |    0.281 | 36.3%               | 63.7%                    | 0.0%   | 0.0%               |
| IV     | 156 |   -33.63 |   -0.006 | 50.6%               | 48.7%                    | 0.0%   | 0.6%               |
| II     | 428 |   -19.1  |   -0.389 | 69.9%               | 22.9%                    | 1.2%   | 6.1%               |
| III    | 371 |   -28.93 |    0.194 | 40.4%               | 59.0%                    | 0.0%   | 0.5%               |

### Patch_vs_Huber

| traj   |   n |   med Δt |   med Δr | T↑R↑(both better)   | T↑R↓(t-better,r-worse)   | T↓R↑   | T↓R↓(both worse)   |
|:-------|----:|---------:|---------:|:--------------------|:-------------------------|:-------|:-------------------|
| VI     | 501 |   -29.84 |    0.851 | 15.4%               | 84.2%                    | 0.0%   | 0.4%               |
| IV     | 156 |    -9.93 |    0.512 | 8.3%                | 57.1%                    | 6.4%   | 28.2%              |
| II     | 428 |     2.02 |    0.303 | 26.4%               | 22.2%                    | 7.9%   | 43.5%              |
| III    | 371 |   -14.11 |    0.854 | 3.5%                | 69.8%                    | 3.0%   | 23.7%              |

### Patch_vs_Trim

| traj   |   n |   med Δt |   med Δr | T↑R↑(both better)   | T↑R↓(t-better,r-worse)   | T↓R↑   | T↓R↓(both worse)   |
|:-------|----:|---------:|---------:|:--------------------|:-------------------------|:-------|:-------------------|
| VI     | 501 |   -24.53 |    1.042 | 12.2%               | 86.8%                    | 0.0%   | 1.0%               |
| IV     | 156 |    -3.51 |    0.745 | 1.9%                | 51.3%                    | 7.7%   | 39.1%              |
| II     | 428 |     4.99 |    0.278 | 24.1%               | 22.2%                    | 8.6%   | 45.1%              |
| III    | 371 |   -14.17 |    0.888 | 8.9%                | 58.8%                    | 3.0%   | 29.4%              |

### PatchHuber_vs_Raw

| traj   |   n |   med Δt |   med Δr | T↑R↑(both better)   | T↑R↓(t-better,r-worse)   | T↓R↑   | T↓R↓(both worse)   |
|:-------|----:|---------:|---------:|:--------------------|:-------------------------|:-------|:-------------------|
| VI     | 501 |   -58.82 |   -0.113 | 58.1%               | 41.9%                    | 0.0%   | 0.0%               |
| IV     | 156 |   -57.71 |   -0.428 | 73.1%               | 26.9%                    | 0.0%   | 0.0%               |
| II     | 428 |   -25.7  |   -0.348 | 61.2%               | 30.6%                    | 6.1%   | 2.1%               |
| III    | 371 |   -38.72 |    0.086 | 45.8%               | 54.2%                    | 0.0%   | 0.0%               |

## Findings

1. **Patch vs Raw: translation improvement essentially never reverses** (both-worse fraction VI 0.0%, IV 0.6%, II 6.1%, III 0.5%). But on VI and III the median rotation change is slightly positive (Δr +0.281/+0.194 deg) and a majority of frames trade a small rotation cost for translation gain; on II both axes improve for 69.9% of frames, IV is ~split. The rotation cost is small in magnitude but real and must be disclosed.

2. **Patch vs the strong robust baselines is NOT uniformly positive.** Median Δt vs Huber is positive (Patch worse) on II (+2.02 mm), and vs Trim on II (+4.99 mm); vs Huber/Trim rotation is worse more often than better on every trajectory. Patch's clean win is specifically vs Raw; its incremental claim over Huber/Trim must be stated as trajectory-dependent.

3. **Patch+Huber vs Raw is the strongest joint result**: both-better fraction 58.1%/73.1%/61.2%/45.8%, translation-worse ≈ 0 everywhere, and median Δr is near zero or negative (-0.113/-0.428/-0.348/+0.086 deg) — combining the patch field with a robust loss removes most of Patch's rotation cost.

## III post-hoc call-out

- Patch_vs_Raw: both-better 40.4%, t-better/r-worse 59.0%, t-worse/r-better 0.0%, both-worse 0.5%; med Δt -28.93, med Δr +0.194.

- Patch_vs_Huber: both-better 3.5%, t-better/r-worse 69.8%, t-worse/r-better 3.0%, both-worse 23.7%; med Δt -14.11, med Δr +0.854.


## Decision

**TRANSLATION_GAIN_WITH_SMALL_ROTATION_COST.** Report the trade-off explicitly; prefer Patch+Huber when joint 6-DoF accuracy is the target. Do not claim Patch dominates Huber/Trim on every trajectory. No threshold analysis (no repo-defined tolerance).
