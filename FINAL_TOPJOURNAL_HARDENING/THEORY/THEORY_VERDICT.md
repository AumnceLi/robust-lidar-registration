# THEORY VERDICT

*THEORY shard final verdict. This document answers the four required questions:
(1) under what assumptions the first-order formula holds; (2) which results
quantitatively support it; (3) which are only qualitative; (4) whether
Contribution 1 can be rewritten as a pose-active mismatch characterization.*

---

## Q1. Under what assumptions does the first-order formula hold?

The formula $\hat{\Delta\xi}=-H^\dagger J^\top W\delta$ predicts the **direction**
of the GT-started local optimum under these assumptions (full list in
`assumptions.md`):

1. **Local correspondence stability** at $\xi=0$ (no NN flips over the step);
   verified by 92.9% landscape descent agreement at ±1 cm / ±0.5°.
2. **First-order Taylor validity** for the *direction* (not magnitude);
   higher-order curvature neglected.
3. **$H$ observable-subspace positive definiteness**; unobservable directions
   handled by $H^\dagger$, not $H^{-1}$.
4. **Deterministic structured mismatch** $\delta_i$ (not zero-mean i.i.d.
   noise); verified by spatial-shuffle null test.
5. **GT known** (probing setup, not initialization benchmark).

It holds **quantitatively in direction for p2p only**, and only in the
neighbourhood of $\xi=0$. It does not hold in magnitude (Newton step ~2×
over-estimate) and does not hold for p2l.

---

## Q2. Which results quantitatively support the theory?

| Claim | Quantitative evidence | Source |
|---|---|---|
| $g_{\mathrm{GT}}=J^\top W\delta$ is non-zero at GT | $\|g_{\mathrm{real}}\|/\|g_{\mathrm{self}}\|$ = 1.4×10³–1.0×10⁴; Hotelling $p\le 10^{-3}$ | `OBJECTIVE_STATIONARITY.md` §2 |
| Gradient depends on spatial structure of mismatch | Spatial shuffle reduces $\|g\|$ by 2.5–2.8× (p=0.010) | `OBJECTIVE_STATIONARITY.md` §3 |
| Surrogate gradient predicts full-objective descent | Landscape agreement 92.9% (p2p) at smallest scale | `objective_main.npz` `landscape`; computed by `theory_empirics.py` |
| Predicted direction matches measured optimum (p2p) | Translation cosine 0.959 (raw) → 0.998 (combined); 96.6%→100% positive | `objective_main.npz`; `QUADRATIC_BIAS_PREDICTION.md` §1 |
| Result replicates on held-out IV | p2p cosine 0.946 (raw) → 0.988 (N3), n=2428 | `ext_objective_iv.npz`; `theory_to_existing_results.csv` |
| Structured appendage diagnostic dominates pose-active gradient | D1 norm vs $\|g\|$ Spearman 0.927 (p=5.5e-215) | `objective_main.npz` `raw__D1`; computed |
| Same dose, different pose projection → different bias | D1 100 mm → 80.7 mm; D3 100 mm → 13.9 mm (LS, p2p) | `geometry_results.csv` |
| Robust loss attenuates but does not eliminate coherent bias | D1 50 mm: LS 39.2, Huber 42.8, Trim 50.7 mm | `geometry_results.csv` |
| Robust loss removes gross-outlier bias (Regime A) | D2 f=1.0: LS 300 mm clip, Huber 11.6 mm | `geometry_results.csv` |

These are **quantitative** in the sense that the numbers are computed, not
estimated, and reproduced across VI / IV / V / II caches.

---

## Q3. Which results are only qualitative?

| Claim | Status | Reason |
|---|---|---|
| First-order formula predicts **magnitude** of bias | Qualitative-to-partial | Spearman $\|g\|$ vs $\|\xi^\star_t\|$ only 0.44 (raw) → 0.62 (combined); Newton step over-estimates by ~2× raw. Magnitude calibration requires re-linearising as correspondences re-attach. |
| Point-to-plane direction prediction | Negative / qualitative only | p2l cosine 0.32–0.41; Hessian near-singular. p2l supports only cross-objective directional consistency (J1/J2 gradient cosine 0.988 raw). |
| Robust loss regime boundary | Qualitative | The Regime A/B distinction is mechanistic, not a closed-form boundary. The Huber threshold $c$ is not pre-registered here. |
| Physical attribution of R4 residuals | Not claimed | MLI/specular/multipath/CAD-vs-real cannot be separated on VI alone (`IDENTIFIABILITY_AUDIT.md` §2.2). The theory is agnostic to physical cause. |
| Normalised pose-active index | Not defined | Unit-mixing of 6-DoF norms makes a single dimensionless index unsafe without pre-registered scale; we report block norms instead. |

---

## Q4. Can Contribution 1 be rewritten as a pose-active mismatch characterization?

**Yes.** The theory supports recasting Contribution 1 from "the ICP objective
is biased at GT" (a finding) to the more mechanistic:

> **Structured model mismatch produces a pose-active gradient
> $g_{\mathrm{GT}}=J^\top W\delta$ at the true pose; the first-order
> Newton step $-H^\dagger g_{\mathrm{GT}}$ predicts the direction of the
> resulting GT-started local optimum for point-to-point registration.
> The bias is governed by the projection of discrepancy into the pose
> subspace, not by residual energy alone. Robust losses address localized
> gross outliers (Regime A) but do not guarantee unbiasedness for
> spatially coherent moderate mismatch (Regime B).**

This rewriting is supported because:

- the core statement (pose bias = projection of $\delta$ onto the pose
  subspace) is quantitatively verified: D1 vs g Spearman 0.927, direction
  cosine 0.96→0.998, held-out replication on IV;
- the A3 corollary ($J^\top W\delta=0 \Rightarrow$ zero first-order bias)
  is demonstrated by D3 (same 100 mm dose, 6× less bias than D1);
- the robust-loss distinction (Regime A vs B) matches G_GENERALITY cleanly
  (D2 Huber recovers, D1 Huber does not);
- the negative results (p2l failure, magnitude over-estimation, robust
  increasing displacement) are preserved, so the contribution does not
  overclaim.

### Recommended scope language for the rewritten Contribution 1

- **Claim direction (strong):** "For point-to-point ICP, the local pose-active
  gradient at the GT pose predicts the direction of the GT-started local
  optimum (median translation cosine 0.96–0.998; replicates on held-out
  IV/V/II trajectories)."
- **Claim magnitude (partial):** "The first-order Newton step over-estimates
  displacement by ~2× raw; magnitude calibration requires iterative
  re-linearisation."
- **Claim robust loss (regime-qualified):** "Robust weighting removes
  localized gross-outlier bias (Regime A) but attenuates without eliminating
  spatially coherent moderate mismatch (Regime B), and may increase
  displacement."
- **Disclaimers:** p2l not quantitatively supported; no global
  differentiability claim; no physical-cause attribution.

---

## Overall theory verdict

The first-order registration-bias theory is **directionally validated for
point-to-point**, **negative on point-to-plane magnitude**, and **regime-aware
for robust losses**. It supports recasting Contribution 1 as a pose-active
mismatch characterization, provided the claims are scoped to direction
(p2p), the magnitude limitation is stated, and the p2l / robust-loss
boundaries are reported honestly.
