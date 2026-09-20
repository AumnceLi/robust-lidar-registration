# Exp.3 — Direct validation of the pose-active projection: decision

## What was implemented (no redefinition)

Implemented **exactly** the current paper's pose-active construction (notation.md §3,
derivation A2–A3, and the frozen operational code `t5_mechanism_link.pose_active`), which are the
paper's Eq. (12)–(16). The repository contains no separately numbered LaTeX manuscript, so the
equation-to-code mapping is stated explicitly here rather than guessed:

- fixed GT correspondence at ξ=0: δ_i = p_i − m_{j(i)} (frozen NN);
- per-point Jacobian **p2p** A_i = [I | [p_i]_×] (paper rotation-coordinate convention used in
  `t5`: g_r = mean p×δ, H_tr = mean [p]_×, H_rr = mean [p]_×ᵀ[p]_×); **p2l** a_i = [n ; p×n];
- uniform frozen weights W = 1/N; **H = JᵀWJ, g = JᵀWδ** (factor-1 normal equations);
- **Δξ_FO = −H†g**; **δ_PA = P_{J,W}δ = J H† JᵀW δ = J H† g**;
- **RMS_PA = ‖W^{1/2}δ_PA‖ = √(gᵀH†g)**; ratio ‖δ_PA‖/‖δ‖ = RMS_PA/RMS.
- Alongside, the **rematching finite-difference** quantities (NN re-queried at every probe, frozen
  `m_common.grad_hess`): g_FD, B_FD and −B_FD†g_FD; and the **actual** local displacement ξ* reached
  from the reference init (frozen `local_min_*`). g_FD is the gradient of the mean-squared objective
  and equals 2·g at ξ=0 (used as a numerical check).

**Coverage (real frames).** VI all 501; IV 156, II 428, III 371 frozen in-support frames
(III = post-hoc/secondary) → 1456 real frames × {p2p,p2l}. Cached FD is reused for VI/IV/II; III has
no objective cache, so its g_FD/B_FD/ξ* were recomputed with the unchanged frozen solver.

## Numerical self-consistency (`pose_active_numerical_checks.csv`, worst of 2912 rows)

| Check | Result |
|---|---|
| Projector idempotence P²δ = Pδ (rel.) | max 5.2e-14, median 5.7e-15 |
| δ_PA ∈ col(J): normal-equation residual ‖g−HH†g‖/‖g‖ | max 2.3e-13 |
| RMS_PA = √(gᵀH†g) identity | max abs diff 1.1e-11 mm |
| FD step −B_FD†g_FD vs shipped cached dhat | max 1.1e-13 (exact reproduction) |
| factor-2 analytic-vs-FD gradient, **p2p** | max 3.9e-4 (O(h²), as expected) |
| factor-2, p2l (secondary) | median 4.5e-3; 48/1456 >0.1 (see limitation) |
| pinv rcond 1e-10/1e-8/1e-6 vs default | FO translation direction cosine min = **1.000** |
| numerical rank | **6/6 for every frame at every rcond**; condition number median ≈ 7–8 |

The algebra closes to machine precision, rank is full everywhere, and moving the pseudoinverse
threshold by orders of magnitude does not destabilise the step.

## Closed theory chain — p2p direction & magnitude (medians by trajectory)

| Traj | n | ‖δ_PA‖/‖δ | analytic dir-cos (err °) | FD dir-cos (err °) | analytic mag ratio | FD mag ratio | cond |
|---|---|---|---|---|---|---|---|
| VI  | 501 | 0.359 | 0.942 (19.6) | 0.959 (16.5) | 0.252 | 2.18 | 7.5 |
| IV  | 156 | 0.392 | 0.946 (18.9) | 0.973 (13.2) | 0.292 | 1.46 | 6.9 |
| II  | 428 | 0.299 | 0.771 (39.5) | 0.990 (8.0) | 0.422 | 1.16 | 7.3 |
| III*| 371 | 0.346 | 0.809 (36.0) | 0.995 (5.6) | 0.406 | 1.10 | 8.4 |

(dir-cos = cosine of predicted vs actual translation block; analytic = fixed-correspondence
first-order; FD = rematching finite-difference; mag ratio = predicted/actual translation magnitude;
\*III post-hoc.)

**Reading.**
1. A definite **pose-active residual fraction exists** on every real frame (RMS_PA/RMS ≈ 0.30–0.39):
   about a third of the raw mismatch energy lies in the pose-Jacobian column space and is therefore
   capable of moving the pose.
2. The **fixed-correspondence analytic first-order step points toward the actual local optimum**:
   translation direction cosine median 0.94 on VI/IV (cos>0.9 for 81%/93% of frames), 0.77–0.81 on
   the far-held II/III (cos>0.7 for 61%/87%).
3. The **rematching FD step — which includes NN re-matching — is near-exact in direction on all
   trajectories** (median cos 0.96–0.995; cos>0.9 for 74–95%). The gap between analytic-fixed-corr
   and FD on II/III is therefore attributable to **correspondence re-matching during real ICP**, not
   to a wrong pose-active mechanism.
4. **Magnitude.** A single analytic GN step underestimates the *iterated* local optimum
   (ratio 0.25–0.42), which is expected (one Newton/GN step vs a converged ICP trajectory); the
   rematching FD step magnitude is close to unity (1.10–1.46) except VI (2.18). First-order analysis
   predicts direction/local tendency, not the converged step length.
5. **Conditioning is not the limiting factor** (full rank, cond ≈ 7–8, rcond-insensitive;
   Spearman ρ(cond, direction error)=+0.10). Limitations concentrate on far-held views and
   correspondence switching, exactly where fixed-corr ≠ rematching.
6. **p2l (secondary).** Analytic p2l translation direction is very high (median cos 0.99), but its
   rematching-FD agreement is weaker (cos 0.33–0.75) and 48 frames show a large fixed-corr/FD
   gradient gap — consistent with the paper's existing finding that p2l is the weaker, less reliable
   arm; p2p remains the primary arm and is the one that passes cleanly.

## Stated working domain (required, not hidden)

The direct evidence supports the pose-active mechanism as a **local, correspondence-stable,
first-order** statement: it is strongest near the development view distribution (VI) and the
intermediate IV, well-conditioned everywhere, and predicts the *direction* of the reference-started
local optimum. It should **not** be claimed as (i) an exact magnitude predictor of the converged
optimum, (ii) universally accurate under a single fixed correspondence on far-held views (II/III),
or (iii) a global result. When NN re-matching is included (FD), direction agreement becomes
near-exact on all trajectories, which is the correct bridge to the iterated solver.

## Synthetic 1920 runs — `SYNTHETIC_DIRECT_VALIDATION_BLOCKED`

The original sweep has exactly **1920 structured runs** (`geometry_results.csv`, ×4 arms = 7680
rows) but stores only **scalar outcomes** (grad_gt, et/eR norms, J0/Jstar/dJ, on_bound, n_obs). The
required fixed-correspondence intermediates — J, W, δ, δ_PA, singular/eigen values, FO step vector,
actual displacement **vector** — are **not cached**. Regenerating them would not reproduce the
original runs deterministically (the run RNG is seeded with Python `hash()` of strings, which is
process-dependent unless PYTHONHASHSEED is fixed), and the instruction forbids re-randomising. Per
protocol we therefore report **BLOCKED** rather than fabricate or regenerate; the direct validation
rests on 1456 real frames above.

## Decision

**DIRECT_SUPPORT_IN_LOCAL_WORKING_DOMAIN.** The pose-active projection closes the theory chain
numerically (machine-precision self-consistency, full rank, rcond-robust), a nonzero pose-active
residual fraction is present on every real frame, and the first-order analytic step — and even more
so the rematching FD step — points to the actual reference-started local displacement. Claims must
be bounded to the local / correspondence-stable / first-order working domain stated above; this is
sufficient to support, but not to universalise, the pose-active theory.

Artifacts: `pose_active_direct_framewise.csv`, `pose_active_numerical_checks.csv`,
`fig_pose_active_direct_validation.png`.
