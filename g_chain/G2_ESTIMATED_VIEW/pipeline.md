# G2 pipeline.md — Estimated-View Bias-Aware Registration (deployable)

## Goal
Remove G1's dependency on ground-truth viewing geometry. No pose network is trained; the frozen VI-only
mismatch library μ_j(z) and the frozen baseline registration are reused unchanged.

## One-pass pipeline (frozen)
```
P, M  --Step1-->  T0 = Reg_raw(P, M)                 # frozen raw point-to-point LS ICP (identical for every trajectory)
        --Step2--> z0 = z(T0)                        # range + target-frame view dir from the ESTIMATED pose
        --Step3--> mu_j(z0)                          # frozen k=16 adaptive-Gaussian VI library query
        --Step4--> M_corr[i] = M[i] + mu_{j(i)}(z0)  # corrected nominal geometry
        --Step5--> T_hat = Reg(P, M_corr(z0))        # re-register
```
**T0 source is frozen before any external evaluation and is the same for all trajectories** (raw p2p LS
local optimum). No per-trajectory T0 choice is allowed.

## Three paired arms (same scan, same frozen correction library)
- **T0_raw**: baseline output (no correction) — the deployed starting point.
- **oracle**: correction view z(T_GT), second registration GT-started — G1 M5, the mechanistic upper bound.
- **est_gtstart**: correction view z(T0), second registration GT-started — isolates the *pure* oracle→estimated
  view gap (identical start; only z differs).
- **est_warmstart**: correction view z(T0), second registration warm-started from T0 — the true one-pass pipeline.

View from an estimated pose: with local chart ξ0 mapping the GT-aligned scan to the T0 optimum, the estimated
lidar pose is R_est=Rξ R_GT, t_est=Rξ t_GT+tξ and the target-frame sensor origin is
o_est = o_GT − R_GT^T Rξ^T tξ, giving z0=(‖o_est‖, o_est/‖o_est‖). GT is used only to score the final error.

## Oracle-gap metrics (D2)
Δe_t, Δe_R between oracle and each estimated arm; fraction of the raw→oracle mitigation **retained** under
estimated view, (e_T0−e_est)/(e_T0−e_oracle); view-angle / range gap; cosine between oracle and estimated
correction directions (`oracle_vs_estimated.csv`).

## Decision
- **G2_PASS**: estimated-view keeps a clear mitigation gain; oracle→estimated drop is small; no sudden collapse
  under moderate perturbation.
- **G2_PARTIAL**: estimated view degrades clearly but still beats raw overall.
- **G2_FAIL**: mitigation vanishes or systematically worsens with estimated view → keep oracle as a mechanism
  experiment, state the limitation, and do NOT build a fancier estimator.
