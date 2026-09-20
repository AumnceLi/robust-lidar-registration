# G0 protocol — Robust Registration Falsification

## Scientific question
The existing M1/M2 evidence (objective non-stationarity at GT; GT-started local optimum displaced
~160 mm along +target-x, self-floor 0.0000 mm) was obtained **only under vanilla point-to-point /
point-to-plane least-squares ICP with no robust loss**. G0 asks whether a *standard robust
registration* removes that biased optimum. If it does, the mechanism is a least-squares artifact and
the paper must contract to a failure-analysis paper; if a clear physical displacement remains above
the matched self-null, the mechanism survives a genuine falsification attempt.

## Formulations (frozen in `frozen_config.yaml`, sealed before the first outcome run)
- **R0** point-to-point least-squares ICP; **R1** point-to-plane least-squares ICP (vanilla baselines).
- **R2 = Huber-weighted ICP — the single primary robust method.** IRLS, δ=1.345, robust scale
  s=max(1.4826·MAD, model NN spacing 8.11 mm), weights recomputed each iteration; weighted Kabsch
  (p2p) / weighted Gauss–Newton (p2l). Chosen because it is the textbook standard robust registration
  and needs the least new code (one weight function on the frozen solver).
- **R3 = trimmed ICP, keep 0.80** — one pre-registered *secondary sensitivity*, reported alongside;
  it can corroborate but never replace/cherry-pick the Huber decision. No other robust loss is tried.

All four are special cases of **one shared weighted solver** with identical correspondences (nearest
fixed model point, recomputed every probe), frozen PCA normals, basin 0.30 m/15°, max 40 iters,
tolerance 1e-8/1e-9, FD step 5 mm/0.25°. A pre-run check proves R0/R1 reproduce the frozen
`raw__xistar` to ≤2e-16, so robust weighting is the *only* changed factor.

## Controlled GT-started protocol
Every formulation starts at ξ=0 (=T_GT) and runs only the local basin. Per frame/formulation/objective
we record ‖∇J(T_GT)‖, e_t^GT (mm), e_R^GT (deg), ΔJ=J(T_GT)−J(T*), iterations, on-bound flag, mean
weight/keep fraction. Real clouds: VI (all 501), IV, II, V (all frames, tagged by frozen support;
external primary subset = in-support, IV 156 / II 428; V is out-of-support and supportive only).

## Matched self-null (B3)
For each frame an equal-point-count subset of the nominal model is drawn with the frozen seed-42
scan-order policy and registered to the full model with the **same** formulation from ξ=0; a correct
robust solver must leave it at ~0 displacement. This is the numerical floor the real displacement is
measured against.

## Statistics (frames are not independent)
Trajectory/block-aware median + IQR; temporal moving-block bootstrap of the median (L=5/10/20,
B=2000); paired block sign-flip (L=5); real-vs-self effect size (Cohen d, MWU). VI additionally uses
its six frozen orientation blocks.

## Decision (no preset mm threshold; three joint criteria)
Combine (i) real-vs-self effect size, (ii) block-aware uncertainty, (iii) engineering magnitude of the
residual physical GT displacement under Huber:
- **G0_PASS_STRONG** — Huber barely changes the GT non-stationarity / displacement.
- **G0_PASS_ATTENUATED** — Huber significantly reduces bias but a stable block-level residual remains
  clearly above self/null and is still engineering-relevant.
- **G0_FAIL_ROBUST_RESOLVES** — Huber restores GT stationarity and drives displacement to a
  numerically/practically negligible level → STOP mitigation development, write the Acta failure-analysis paper,
  and do NOT try other robust losses looking for a formulation that still fails.

Only G0_PASS_STRONG / G0_PASS_ATTENUATED unlocks G1.
