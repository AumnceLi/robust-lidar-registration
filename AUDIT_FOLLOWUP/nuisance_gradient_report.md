# Nuisance-control gradient before/after (P0 follow-up)

**Mechanical recompute only. No parameter was tuned, no operator was re-fit, no frame was removed.** The three nuisance controls are VI-only frozen operators (`frozen_nuisance_ops.npz`, verified to match `nuisance_params.json`):

- **N1 global range offset** (1 dof): source moved along the sensor ray by `br=58.3318 mm`, `Q = P - br (P-o)/|P-o|`.
- **N2 common SE(3)** (6 dof): frozen rigid transform `Q = Rse P + tse` (|t|=46.04 mm, 2.4136 deg), a 12-iteration point-to-plane fit pooled over VI.
- **N3 global scale** (1 dof): `Q = P/s`, `s=0.9655788` (-3.44%).

## Definitions (identical to `r7_ext_objective.py` / `m_common.grad_hess`)

- `condition=raw` is the uncorrected GT-aligned scan; N1/N2/N3 apply the frozen operator.
- **||g_t||, ||g_r||**: translation/rotation block of the six-component central-difference gradient of the frozen LS objective at xi=0 (FD step 5 mm / 0.25 deg; objective is the mean, so g is already 1/N). p2p and p2l channels both exported; tables below use **p2p** (consistent with the primary M0/Raw estimator).
- **residual RMS (mm)**: sqrt(J0)*1000 at xi=0.
- **translation / rotation error**: ||xistar[:3]||*1000 and deg(||xistar[3:]||) of the GT-started frozen ICP local optimum.
- **patch spread (mm)**: within each frame, std across the 24 patches of the per-patch MEAN unsigned nearest-model distance at xi=0 -- the per-frame analogue of the pooled `patch_profile_std` in nuisance_params.json.

## Coverage and scope

- One row per (dataset, frame, condition, objective channel). IV 2428 frames (156 in-support primary), II 1253 (428 primary), V 1868 (all analyzed; V is permanently out-of-support).
- Summary medians below use the **primary in-support subset** for IV/II and **all frames** for V, matching the shipped master/Figure-7 scope. Full all-frame values are in the CSV.
- These controls are VI-fit diagnostics. They are applied frozen to IV/II/V and are **not** pose-correction methods.

## Verification (independent live recompute vs frozen ext_objective arrays)

Six deterministic frames per dataset x four conditions were re-derived from scratch with `m_common.grad_hess` and the frozen ICP solvers. Maximum absolute discrepancy: gradient 0.00e+00, J0 0.00e+00, realized xi 0.00e+00 (i.e. bit-exact).

## Median ratio after/raw (p2p, primary scope)

| dataset | control | n | ||gt|| | ||gr|| | resid RMS | trans err | rot err | patch spread |
|---|---|---|---|---|---|---|---|---|
| IV | N1 | 156 | 0.496 | 1.045 | 0.867 | 0.798 | 0.995 | 1.106 |
| IV | N2 | 156 | 0.572 | 1.299 | 0.924 | 0.934 | 1.460 | 1.040 |
| IV | N3 | 156 | 0.798 | 1.287 | 0.988 | 0.872 | 0.897 | 1.064 |
| II | N1 | 428 | 0.373 | 0.710 | 0.901 | 0.579 | 0.986 | 1.389 |
| II | N2 | 428 | 0.343 | 0.509 | 0.915 | 0.717 | 1.762 | 1.260 |
| II | N3 | 428 | 0.630 | 0.884 | 1.000 | 0.630 | 1.013 | 1.122 |
| V | N1 | 1868 | 1.202 | 1.456 | 0.988 | 0.889 | 1.009 | 0.932 |
| V | N2 | 1868 | 1.276 | 1.395 | 1.082 | 1.048 | 1.497 | 0.892 |
| V | N3 | 1868 | 1.151 | 1.249 | 1.041 | 0.936 | 0.933 | 1.054 |

## Raw baseline medians (denominators above)

| dataset | n | gt_norm | gr_norm | resid_rms_mm | trans_mm | rot_deg | patch_spread_mm |
|---|---|---|---|---|---|---|---|
| IV | 156 | 0.0658 | 0.0085 | 99.4370 | 160.4239 | 4.0061 | 63.6778 |
| II | 428 | 0.0516 | 0.0081 | 84.6723 | 66.1492 | 1.7743 | 99.6265 |
| V | 1868 | 0.0685 | 0.0170 | 106.5644 | 173.7605 | 3.0260 | 80.4647 |

## Findings

1. **The frozen nuisance operators reduce the translation GT-gradient ||g_t|| on the two in-support held-out trajectories (IV: x0.50/0.57/0.80; II: x0.37/0.34/0.63 for N1/N2/N3), consistent with removing part of a GLOBAL, view-coherent bias.**
2. **On permanently out-of-support V they instead INCREASE ||g_t|| (x1.20/1.28/1.15)** and inflate ||g_r|| (up to x1.46): a VI-fit global operator does not transfer there -- another reason V stays supportive/out-of-support rather than confirmatory.
3. **Translation and rotation do not move together.** N2 (common SE3) cuts ||g_t|| most on II but inflates the rotation gradient (IV x1.30) and the realized rotation error (II x1.76, IV x1.46, V x1.50): a global rigid absorb trades translation for rotation.
4. **Residual-RMS change is small relative to gradient change** (RMS x0.87-1.08 everywhere). The pose-active gradient responds more strongly and more selectively than raw mismatch size, which is the same gradient-not-RMS point made elsewhere in the audit.
5. Patch spread is reduced by N1/N2 on V (x0.93/0.89) but slightly enlarged on IV/II -- the global operators are not spatial patch corrections and do not flatten the patch profile the way the structured patch correction does.

## Files

- `nuisance_gradient_before_after.csv` -- per-frame/per-channel/per-condition full table.
- `scripts/t1_verification.csv` -- independent-recompute discrepancy log (all ~0).
- `scripts/t1_summary.csv` -- long summary used above.
