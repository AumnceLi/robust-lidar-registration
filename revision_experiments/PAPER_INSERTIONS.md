# PAPER_INSERTIONS — factual, drop-in results (no change to main conclusions)

All numbers are produced by the saved revision scripts (framewise CSV + provenance in
`revision_experiments/`). Wording respects the evidence: 24/0.30/seed42 remains the frozen main
configuration and is never called an "optimum"; causal language is limited to "consistent with".

## 1. Hyperparameter stability (recommended for the Implementation/Robustness section)

> **Patch-count stability.** Varying the number of surface patches over K∈{12,18,24,32,48} (all
> other settings frozen) leaves the frame-paired translation improvement of Patch over Raw positive
> on every trajectory: median benefit ranges 38.6–56.8 mm (VI), 31.5–40.6 mm (IV), 14.5–24.3 mm (II)
> and 23.2–33.5 mm (III). The chosen K=24 lies within this plateau; only the extreme K=48 shows a
> mild reduction on the hardest held-out trajectory II, with no sign reversal. The paired rotation
> change stays within ±0.47°.

> **Normal-feature-weight stability.** With K=24 fixed and the clustering normal-feature weight w
> varied over {0,0.15,0.30,0.60,1.00}, the translation benefit remains positive on all trajectories
> (VI 39.1–57.7, IV 31.8–41.9, II 17.9–22.2, III 26.4–32.2 mm). Pure position-only clustering
> (w=0) already attains most of the gain (39.1/31.8/19.1/32.2 mm), indicating that the benefit is
> carried primarily by spatial partitioning rather than by normal-augmented features; w=0.30 is a
> fixed design value within a stable range, not a tuned optimum.

> **Clustering-seed stability.** Re-running MiniBatchKMeans with five pre-declared seeds
> {0,1,2,42,20240910} (rebuilding both the partition and the VI calibration field each time) keeps
> the paired Patch-over-Raw translation benefit strictly positive on all four trajectories for every
> seed, with narrow across-seed ranges (VI 43.2–48.1, IV 33.4–36.5, II 19.1–27.7, III 26.6–34.8 mm).

## 2. Rotation-penalty ablation (recommended for the discussion of Patch+Huber)

> The small rotation cost of applying Patch geometry before robust ICP is not removed by two
> implementation-level ablations in the point-to-point formulation used for the main results.
> Re-estimating surface normals on the corrected geometry (identical local-PCA k=16 protocol) leaves
> the point-to-point result bit-for-bit unchanged (max per-frame difference 1.4×10⁻¹⁴ mm), because
> point-to-point Kabsch does not consume normals; a parameter-free single-step k=16 neighbour
> smoothing of the piecewise-constant correction field likewise leaves the point-to-point rotation
> cost essentially unchanged. In the point-to-plane channel, where normals enter the linear system,
> recomputing them reduces the paired rotation cost on all trajectories (e.g. VI 1.12°→0.75°,
> IV 0.61°→0.28°, II 0.89°→0.66°) without materially changing the translation gain, which is
> *consistent with* stale-normals contributing there, although a residual cost remains and the
> experiment does not isolate a unique causal mechanism.

## 3. Statistical aggregation robustness (recommended for the statistics paragraph)

> The direction of the primary contrasts is insensitive to the external-trajectory block length:
> with blocks of 25, 50 and 100 frames (identical frame set), Patch-vs-Raw and Patch+Huber-vs-Huber
> remain positive with 95% block-bootstrap intervals above zero (≥94% of blocks positive) on IV, II
> and III. The Patch-vs-Global-Vector contrast on II stays directionally positive but block-CIs
> still cross zero at 50/100 frames; we therefore report it as unresolved rather than significant.

## 4. II transfer-failure diagnostic (recommended as a limitation / transfer-boundary paragraph)

> On II, the view-conditioned correction is not limited by historical-view availability: nearest
> training-view distance, kernel effective sample size, patch coverage and fallback counts are
> comparable to (or better than) those on the successful IV transfer. The separating quantity is
> predicted-step alignment: the median cosine between the view-predicted and actually-required
> translation step is +0.71 to +0.85 across IV quantile bins but −0.38 (median) to −0.70 (worst
> decile) on II. The available diagnostics therefore localize the II transfer failure to
> transfer/view conditioning — a learned view-to-mismatch mapping that mis-directs the correction
> despite adequate nearby views — but do not uniquely identify its physical cause.

## What NOT to claim
- Do not call 24 / w=0.30 / seed42 "optimal" (no independent development-only selection protocol).
- Do not write that recomputed normals or smoothing *cause*/eliminate the rotation penalty; the p2p
  primary is unchanged and the p2l reduction is partial.
- Do not promote Patch-Smooth or a stacked estimator as a contribution; both are diagnostics only.
- Do not upgrade II Patch-vs-Global to "significant"; its block interval crosses zero.
