# FINAL TOP-JOURNAL AUDIT

**Paper:** Structured Model Mismatch in Spacecraft LiDAR Registration: From Pose Bias Mechanism to Bias-Aware Compensation
**Round:** Final top-journal hardening (theory + direct-bias baseline + audits)
**Date:** 2026-09-10
**Status:** METHOD DEVELOPMENT STOPPED. All four permitted task classes (THEORY, DIRECTBIAS, AUDIT, OPTIONAL) completed. This document freezes the scientific claim, contribution statements, and submission recommendation.

---

## 1. Final Scientific Claim

Structured nominal-model discrepancy in spacecraft LiDAR registration produces a **pose-active gradient** $g_{\mathrm{GT}} = J^\top W\delta$ at the ground-truth pose. The first-order Newton step $-H^\dagger g_{\mathrm{GT}}$ predicts the **direction** of the resulting GT-started local optimum for point-to-point ICP (median translation cosine 0.96–0.998 on VI, replicated 0.95–0.99 on held-out IV, $n=2428$). Pose bias is governed by the **projection of model discrepancy into the registration pose subspace**, not by residual energy alone: when $J^\top W\delta = 0$, even large $\|\delta\|$ yields zero first-order bias (demonstrated by D4 scale mismatch and D3 localized offset at matched dose).

Robust losses remove localized gross-outlier bias (Regime A: D2 whole-component absence, LS hits 300-mm basin clip, Huber recovers to 11.6 mm) but do **not** guarantee unbiasedness for spatially coherent moderate mismatch (Regime B: D1 50 mm, LS 39.2 / Huber 42.8 / Trim 50.7 mm — robust weighting can occasionally increase displacement).

A view-conditioned structured-discrepancy correction that modifies the nominal geometry / registration objective is a **mechanistic, regime-robust alternative** to direct pose-bias regression. The direct-bias-subtraction baseline reaches ~2 cm when view geometry transfers (VI/IV) but catastrophically fails when it drifts (II: 66→143 mm), because it has no guardrail against direction collapse and magnitude non-stationarity.

The problem class is formally **known nominal target geometry with historical calibrated observations** — not a generic first-encounter solution for arbitrary unknown spacecraft.

---

## 2. First-Order Theory: Validity Assessment

### 2.1 Under what assumptions it holds

The formula $\hat{\Delta\xi} = -H^\dagger J^\top W\delta$ holds under:
1. **Local correspondence stability** at $\xi=0$ (no NN flips over the step) — verified by 92.9% landscape descent agreement at ±1 cm / ±0.5°.
2. **First-order Taylor validity for direction** (not magnitude); higher-order curvature neglected.
3. **$H$ positive definite on the observable subspace**; unobservable directions handled by $H^\dagger$ (Moore–Penrose), not $H^{-1}$.
4. **Deterministic structured mismatch** $\delta_i$ (not zero-mean i.i.d. noise) — verified by spatial-shuffle null test ($\|g\|$ drops 2.5–2.8×, $p=0.010$).
5. **GT known** (probing setup, not an initialization benchmark).

### 2.2 Quantitative support

| Claim | Evidence | Source |
|---|---|---|
| $g_{\mathrm{GT}} \neq 0$ at GT | $\|g_{\mathrm{real}}\|/\|g_{\mathrm{self}}\| = 10^3$–$10^4$ | `OBJECTIVE_STATIONARITY.md` |
| Surrogate gradient predicts full-objective descent | 92.9% landscape agreement (p2p) at smallest scale | `objective_main.npz landscape` |
| Predicted direction matches measured optimum (p2p) | Translation cosine 0.959 raw → 0.998 combined; 96.6%→100% positive | `objective_main.npz` |
| Held-out replication (IV) | p2p cosine 0.946 raw → 0.988 N3, $n=2428$ | `ext_objective_iv.npz` |
| Pose-active projection dominates | D1 norm vs $\|g\|$ Spearman 0.927 ($p=5.5\times10^{-215}$) | `objective_main.npz raw__D1` |
| Same dose, different projection → different bias | D1 100 mm → 80.7 mm; D3 100 mm → 13.9 mm (LS p2p) | `geometry_results.csv` |

### 2.3 Limitations (honestly stated)

- **Magnitude is only partially predicted:** Spearman $\|g\|$ vs $\|\xi^\star_t\|$ = 0.44 (raw) → 0.62 (combined); Newton step over-estimates displacement by ~2× raw. Magnitude calibration requires iterative re-linearisation as correspondences re-attach.
- **Point-to-plane fails:** cosine 0.32–0.41, Hessian near-singular. p2l supports only cross-objective directional consistency (J1/J2 gradient cosine 0.988 raw).
- **No global differentiability claim:** the full NN-ICP objective is piecewise-smooth; the theory applies to the fixed-correspondence local surrogate $\tilde{J}(\xi|C_{\mathrm{GT}})$ only.
- **Normalized index $\eta$ not defined as a single scalar:** unit-mixing of translation (m) and rotation (rad) makes a dimensionless 6-DoF index unsafe without pre-registered scale. The phase-map shard uses separate $\eta_t$/$\eta_R$ as normalized residual-coherence proxies.

### 2.4 Verdict

**The first-order theory is directionally validated for point-to-point, negative on point-to-plane magnitude, and regime-aware for robust losses.** It supports recasting Contribution 1 as a pose-active mismatch characterization, provided claims are scoped to direction (p2p), the magnitude limitation is stated, and p2l / robust-loss boundaries are reported honestly.

---

## 3. Robust-Loss Explanation: Consistency with Data

The two-regime theory is consistent with G_GENERALITY:

- **Regime A (localized/gross):** D2 whole-component absence at $f=1.0$ — LS hits the 300-mm translational basin clip, Huber recovers to 11.6 mm. The influence function $\psi(\delta)$ truncates the few gross residuals, $J^\top\psi(\delta)$ drops significantly. Partial removal ($f \le 0.75$) is absorbed by the correctly-matching majority even under LS (~0 bias).
- **Regime B (coherent moderate):** D1 coherent surface offset — at 50 mm dose, LS 39.2 / Huber 42.8 / Trim 50.7 mm. Residuals are spatially correlated, same-direction, and within the inlier/transition region, so $\psi(\delta_i) \approx \delta_i$ and $\sum A_i^\top\psi(\delta_i) \neq 0$. **Robustification does not guarantee pose unbiasedness.**

**Real EPOS:** robust weighting attenuates but does not eliminate the bias (VI: LS 161.4 → Huber 148.9 mm; IV: 160.4 → 132.6 mm).
**Synthetic D1/D5:** robust weighting does not eliminate the bias and can occasionally increase the resulting displacement (39.2 → 42.8 → 50.7 mm).

The optional phase map (§6) confirms: Huber's value is strictly regime-dependent — it suppresses localized gross outliers and partially rescues a just-crossed boundary, but cannot fix large-support coherent systematic bias and can saturate once the corrupted feature dominates.

---

## 4. Direct Bias Subtraction Baseline: Results and Decision

### 4.1 Method (frozen, no retraining)

B1 view-only predictor replicated exactly: $k=16$ nearest VI neighbors, adaptive Gaussian weights, range_std = 2.0643, $\tau_{\mathrm{support}} = 0.4403$; external train = all 501 VI frames. B1 outputs a **unit translation direction only** — no magnitude, no rotation.

Magnitude frozen from VI **before** touching test data:
- **Primary:** same-weights weighted mean of VI historical $\|\xi\|$ for the selected $k=16$ neighbors.
- **Sensitivity:** global VI median = 161.4 mm.

Subtraction at perturbation level in the locked target frame: $\xi_{\mathrm{dbs}}[:3] = \xi_{\mathrm{raw}}[:3] - \hat{m}\cdot\hat{v}$, rotation unchanged. Therefore $e_R(\mathrm{DBS}) = e_R(\mathrm{raw})$ **exactly** (verified numerically on all trajectories).

### 4.2 Results (median $e_{te}$, mm; block-aware CI)

| Arm | VI (dev) | IV (held-out in-sup) | II (held-out in-sup) | V (out-of-sup) |
|---|---:|---:|---:|---:|
| Raw (p2p) | 161.4 [158.8,163.8] | 160.4 [158.1,162.3] | 66.1 [63.4,83.1] | 173.8 [172.8,174.6] |
| Robust (Huber) | 148.9 [147.3,150.8] | 132.6 [131.0,135.4] | 50.9 [46.8,53.4] | 169.5 |
| **DBS (B1 direct subt.)** | **17.9** | **19.9** | **143.0** | 101.8 |
| Global correction | 157.0 | 153.4 | 55.2 | 176.0 |
| Patch correction | 116.8 [114.4,119.5] | 126.3 [120.9,132.1] | **41.8** [38.9,48.0] | 134.6 |
| Full correction | 76.9 [73.8,79.8] | 82.9 [78.6,96.8] | 68.9 [64.7,73.3] | 118.5 |

$e_R$ (deg, median): DBS = raw exactly (VI 4.51, IV 4.01, II 1.77, V 3.03). Full correction additionally lowers $e_R$ (VI 2.88, IV 2.46); DBS cannot.

Block consistency (blocks where DBS median < raw): **VI 6/6, IV 8/8, V 12/12, II only 3/12.** Per-frame improvement rate: VI 100%, IV 100%, V 86%, **II 19%**.

### 4.3 Why II fails — double mechanism

| Traj | view-dir cosine | frac $\|\cos\|>0.9$ | $\hat{m}$ (mm) | realized raw (mm) | DBS |
|---|---:|---:|---:|---:|---|
| VI | 0.996 | 1.00 | ~159 | 161 | 17.9 (win) |
| IV | 0.994 | 1.00 | ~150 | 160 | 19.9 (win) |
| II | **0.557** | **0.03** | ~161 | **66** | 143.0 (crash) |
| V | 0.826 | 0.33 | ~163 | 174 | 101.8 (fragile win) |

On II, both ingredients fail: (1) view-direction cosine collapses to 0.56 (only 3% of frames have $|\cos|>0.9$), matching the known VIEW_ONLY_BASELINE heterogeneity (IV $\Delta C = -0.145$, II $\Delta C = +0.182$); (2) the frozen ~161 mm magnitude mismatches II's realized ~66 mm bias. A direct pose-bias regressor has no guardrail — it always injects a ~16 cm vector, and when that vector points the wrong way it doubles the error.

### 4.4 Decision: DIRECTBIAS_MIXED

> *"Relative performance is regime dependent, while mismatch-mediated correction retains a mechanistic interpretation and avoids direct pose-bias regression."*

- **Not B1-dominates:** DBS loses catastrophically on II (143 vs Patch 41.8 / Raw 66.1) and cannot touch rotation.
- **Not ours-passes-outright:** on IV (primary held-out in-support), DBS at 19.9 mm is ~4× better than Full correction (82.9 mm).
- **Hence regime-dependent.** DBS quantifies both the ceiling (~2 cm when view geometry transfers) and the risk (143 mm crash when it drifts) of the direct approach.

### 4.5 III provenance

III DBS is **not computable**: G3 retains no raw perturbation vector and no view unit-vector (scan caches are point-clouds only; G0/G1/G2 CSVs store scalar $e_t$/$e_R$). If computed in future, it must be labeled **post-confirmatory supplementary baseline analysis**, never part of the original G3 prospective confirmation.

### 4.6 Implications for Contribution 2

Contribution 2 survives, **reframed**: do not claim universal correction superiority. Position as "mechanism paper + interpretable, regime-robust alternative to direct pose-bias regression." Mismatch-mediated correction (Patch = best arm on II at 41.8 mm; Full stable everywhere; $e_R$ also improved) trades peak IV accuracy for regime robustness and a physical model-correction mechanism that never regresses the pose bias itself.

---

## 5. Actual Method Value of "Ours"

The mismatch-mediated correction's value is **not** raw peak accuracy (DBS beats it 4× on IV translation). Its value is:

1. **Regime robustness:** does not crash on view-heterogeneous trajectories (II: Patch 41.8 vs DBS 143.0 vs Raw 66.1).
2. **Full 6-DoF correction:** lowers both $e_t$ and $e_R$ (VI Full: $e_t$ 76.9, $e_R$ 2.88° vs Raw $e_R$ 4.51°); DBS is translation-only.
3. **Mechanistic interpretability:** modifies the nominal geometry / registration objective based on a physically-grounded mismatch field, rather than regressing and subtracting an empirical pose-bias vector. The correction direction is derived from $J^\top W\delta$, the same quantity the theory identifies as causal.
4. **No magnitude non-stationarity risk:** does not inject a fixed-magnitude vector; correction scale is determined by the local mismatch field.
5. **Positive evidence for the mechanism:** the near-oracle DBS on VI/IV (cos 0.99) confirms the view/mismatch structure is physically real and highly predictive. The II crash isolates *why* direct regression is unsafe — exactly the failure mode model-mismatch correction is designed to avoid.

---

## 6. Optional Phase Map: Quantitative Failure-Regime Boundary

**Executed (not skipped).** One frozen sweep reusing `g_generality_run.py` unchanged (import + call; no training, no tuning). 300 cells across 3 synthetic geometries, 10 reps, LS vs Huber.

### Three regimes confirmed

- **R1 — systematic bias (large support + high $\eta$):** D1 coherent displacement ($\eta_t \approx 0.88$, $\alpha \approx 0.35$) → LS $e_t \approx 18.6$ mm; Huber does **not** remove it. D5 tilt biases rotation only where $\eta_R$ is high.
- **R2 — robust-suppressible (localized/gross):** D2 removal at $f=0.1$–$0.75$ → LS $e_t \approx 0.015$–$0.43$ mm (noise floor). **Sharp boundary at $f=1.0$:** $\eta_t$ jumps to 0.92–0.96, LS blows to 300-mm basin clip; Huber rescues where corrupted support is still a minority (GA 325→11.6 mm) but saturates where it dominates (GB ~300 mm).
- **R3 — limited pose bias (large residual energy, low $\eta$):** D4 scale ($\alpha \approx 0.16$, $\eta_t \approx 0.03$–$0.12$) → LS $e_t \approx 0.07$–$0.63$ mm despite real residual energy.

### Key finding

**$\eta$ (pose-active projection), not $\alpha$ (affected fraction) alone, is the discriminator.** Two conditions can share $\alpha \approx 0.17$–$0.20$ (D2 $f=0.75$ vs $f=1.0$): the low-$\eta$ one is harmless, the high-$\eta$ one catastrophic. LS bias is confined to the $\eta \gtrsim 0.3$ band; within that band, support magnitude scales the bias.

---

## 7. Operating Assumptions

The mismatch field $\mu_j(z)$ is established under these conditions (audited, not assumed):

1. **Historical scans are GT-aligned:** every scan used to build $\mu$ is transformed to the target frame with the dataset ground-truth pose ($P_{\mathrm{target}} = R_{\mathrm{GT}}^\top(P_{\mathrm{lidar}} - t_{\mathrm{GT}})$). Cached clouds are stored as `scan_XXXX.npz["aligned"]`.
2. **Mismatch vectors are in the target/CAD frame:** $v = P - \mathrm{MODEL}[nn]$ in the frame of `target_model.3d` (67,870 points, sampled from the CAD of the same physical mockup).
3. **Nominal CAD is known:** the target model is explicitly provided; the 24 frozen patches are a partition of this known model.
4. **Deployment requires historical calibrated observations:** at inference, the system queries a frozen VI historical library (`Vmean` 501×24×3, `Vcnt` 501×24) using the test scan's viewing geometry only. It never uses the test scan's own residual.
5. **New target requires rebuilding:** $\mu$ is indexed by patch labels defined on this target's CAD; a different spacecraft needs its own CAD + its own GT-aligned historical scan library. Zero zero-shot transfer.

**Formally defined problem class (boxed in manuscript Problem Formulation, not just Limitations):**

> **Known nominal target geometry with historical calibrated observations.**

This is explicitly **not** a generic first-encounter solution for an arbitrary unknown spacecraft.

---

## 8. Calibration / Ground-Truth Uncertainty Boundary

### 8.1 Can the 50–160 mm bias be calibration/GT error?

**No.** The decisive argument is structural, not a tolerance budget:

1. **Self-null is ~0:** p2p $\approx 7.8\times10^{-14}$ mm, p2l exactly 0. The estimator injects nothing.
2. **Same bias reproduces with exact, zero-uncertainty GT:** in G_GENERALITY, target pose is fixed to identity on synthetic geometries — no metrology, no hand-eye, no timing, no facility error. Yet coherent mismatch drives the GT-started optimum to 80.7 mm (D1, 100 mm), monotonically dose-responsive. At mismatch magnitude 0, solver returns 0.014–0.051 mm.
3. **Bias is structured and directional, not random:** 24-patch residual field with 3.69× spread; global signed mean −39.4 mm (inward, range-dependent, Pearson $r=-0.597$); view-conditionable (B1 cos 0.994–0.999 on VI/IV); repeats across all blocks on all trajectories.
4. **Equal-RMS unstructured noise produces 3–28× smaller bias** than structured mismatch at matched magnitude.

### 8.2 Auditable uncertainty scale

Real-hardware terms ($\sigma_{\mathrm{GT},t}$, $\sigma_{\mathrm{GT},R}$, $\sigma_{\mathrm{range}}$, $\sigma_{\mathrm{extrinsic}}$, $\sigma_{\mathrm{timing}}$, CAD/frame alignment) are **not independently quantified** in the audited project files. Per the hard rule, these are recorded as "not independently quantified" in `calibration_uncertainty_budget.csv` — no number is guessed.

**No RSS is formed:** the terms are of different natures (systematic vs random, translation vs rotation, sensor vs metrology vs CAD), not all in the same unit, and several unknown. The correct comparison is structural (§8.1), which is decisive without needing the exact GT tolerance.

**Caveat (transparency gap, not a loophole):** the absolute EPOS facility metrology tolerance is not quantified. The manuscript should report this as a limitation while relying on self-null + perfect-GT synthetic control to establish that the measured displacement is genuine structured mismatch.

---

## 9. Statistical Inference Unit

**Rule:** contiguous 501 frames are NOT 501 iid replicates. Primary inference uses orientation/tumble blocks, trajectory-level medians, and contiguous block bootstrap.

| Trajectory | Blocks | Definition |
|---|---|---|
| VI | 6 | Frozen orientation blocks (cumulative view-direction travel) |
| IV | 4 (in-support) / 8 (DBS) | External trajectory, per-frame order |
| II | 12 | External trajectory (TJ2 passes) |
| III | 8 | G3 confirmatory blocks (371 in-support) |
| V | 12 | Out-of-support, contiguous blocks |

All major results report: median, IQR, block-aware 95% CI (L=5/10/20, B=2000, seed=42), number of blocks with consistent effect, trajectory-level result. The MWU $p \sim 10^{-165}$ in `method_table.csv` is flagged as an $n_{\mathrm{frames}}$ artifact and must **not** be quoted. The correct paired test is block sign-flip (e.g., VI LS−Huber reduction 14.4 mm, $p=0.0005$).

Weak/negative cells preserved: II Full correction (68.9) worse than II Raw (66.1); II DBS catastrophic; V global correction collapses (176.0 vs Raw 173.8); p2l direction prediction fails.

---

## 10. Synthetic Generality: True Evidence Level

G_GENERALITY is classified as a **post-development controlled mechanistic generality study**, NOT prospective external confirmation.

- It runs on **three synthetic, known-GT (identity) geometries** with a single synthetic 2 mm noise model.
- It establishes **geometry-class-level mechanism generality**, not sensor-level performance or arbitrary-real-hardware validation.
- The real EPOS G0–G3 evidence remains the empirical backbone.

**Provenance corrections applied:**
- D2 sweep: protocol.md listed $\{0, .25, .5, .75\}$ but frozen_config.yaml executed $\{0, .25, .5, .75, .9, 1.0\}$. The $f=0.9/1.0$ complete-absence endpoints were added as **exploratory boundary cases after partial-removal inspection**. Required wording: *"Initial D2 sweeps covered partial component mismatch. The complete-component-absence endpoint was subsequently added as an exploratory boundary case after the partial-removal regime had been inspected."*
- D2 = 300 mm is the **imposed translational basin limit** (`BASIN_T = 0.30` m in `g_common.py`), not a physical bias. Required wording: *"LS optimization reached the imposed 300-mm translational basin limit."* Huber rescues this to ~11.6 mm, which is the actual reported contrast.

---

## 11. Unresolved Limitations

1. **Real-hardware calibration tolerances not quantified** ($\sigma_{\mathrm{GT}}$, $\sigma_{\mathrm{extrinsic}}$, etc.) — transparency gap; mechanism settled by perfect-GT synthetic arm.
2. **p2l not quantitatively supported** — first-order direction prediction fails for point-to-plane (Hessian near-singular). The paper's strong claims are p2p-only.
3. **Magnitude prediction is partial** — Newton step over-estimates ~2×; no closed-form magnitude calibration without iterative re-linearisation.
4. **III DBS not computable** — no raw perturbation vector retained in G3; direct-bias baseline on prospective data is a gap.
5. **Single target / single facility** — all real data is one EPOS 2.0 mockup with one Livox Mid-40; generality across targets/sensors is synthetic-only.
6. **Historical calibrated observations required** — not a first-encounter solution; deployment cost includes building a GT-aligned scan library per target.
7. **Robust-loss regime boundary is qualitative** — no closed-form $\eta$ threshold separating Regime A/B; Huber threshold $c$ not pre-registered.
8. **V out-of-support behavior is fragile** — DBS median win (101.8) has wide IQR [65,149] and only 33% $|\cos|>0.9$; not a support-robust guarantee.

---

## 12. Reviewer #2 Style Assessment

| Dimension | Score /10 | Rationale |
|---|---:|---|
| **Novelty** | 8 | First-order pose-active projection theory for structured model mismatch is a genuinely new framing; direct-bias-subtraction falsification baseline is unusual and honest. Incremental on ICP-robustness literature but the mechanism characterization is distinct. |
| **Theory** | 8 | Rigorous fixed-correspondence surrogate derivation, $H^\dagger$ handling, pose-active/inactive distinction, two-regime robust-loss theory. Docked for p2l failure and magnitude partial-prediction (honestly reported, but limits scope). |
| **Technical depth** | 8 | Multi-trajectory real + synthetic, GT-started probing, landscape finite-perturbation verification, block-aware statistics, phase-map boundary analysis. Strong reproducibility (frozen configs, scripts). |
| **Experimental rigor** | 9 | Frozen pipelines, untouched prospective III (G3), held-out cross-trajectory IV/II, out-of-support V, self-null controls, spatial-shuffle null, dose-response, direct-bias baseline with pre-frozen magnitude. Provenance audit is exemplary. Docked only for III DBS gap and unquantified real-hardware tolerances. |
| **Engineering relevance** | 7 | Spacecraft rendezvous LiDAR registration is high-relevance; known-CAD + historical-observations problem class is realistic for on-orbit servicing. Docked for single-facility/single-target and deployment cost (per-target library build). |
| **Generalization** | 6 | Real data = one target; synthetic generality = 3 geometries with one noise model. The mechanism generalizes across geometry classes (synthetic) but cross-target/cross-sensor real validation is absent. G_GENERALITY correctly classified as post-development mechanistic, not prospective. |
| **Overall** | **7.8** | Strong mechanism paper with honest boundaries. The three reviewer-killer questions are now answerable. Not a universal-method paper; positioning must reflect this. |

---

## 13. Submission Recommendation

### **READY_TAES** (IEEE Transactions on Aerospace and Electronic Systems)

**Rationale:**
- The mechanism characterization (pose-active projection theory + robust-loss regimes + direct-bias falsification) is a strong fit for TAES's aerospace-systems scope.
- Experimental rigor (frozen pipelines, prospective G3, block-aware stats, provenance audit) meets TAES expectations.
- The single-target/single-facility limitation and the "known CAD + historical observations" problem class are appropriately scoped for a specialized aerospace venue rather than a broad general-robotics/AI venue.
- **Not READY_AST (Acta Astronautica):** the theory/method depth exceeds typical Acta scope, and the direct-bias baseline + phase map are more computational than Acta's usual applied-engineering focus.
- **Not READY_ACTA (Automatica):** the first-order theory is not a full control/estimation theorem; p2l failure and magnitude partial-prediction limit the formal contribution. The experimental system identification flavor is strong but the theoretical guarantee is directional-only.
- **Not NOT_READY:** all three reviewer-killer questions are addressed; no fatal gaps; limitations are transparent rather than hidden.

**Pre-submission checklist:**
1. Insert the boxed problem-class statement in Problem Formulation (§7), not just Limitations.
2. Replace any "ICP objective is differentiable / $\nabla J(T_{\mathrm{GT}})$" language with the surrogate-vs-full-objective distinction (§2, `icp_objective_math_audit.md`).
3. Add the DBS baseline table (§4) with the DIRECTBIAS_MIXED framing and $e_R(\mathrm{DBS})=e_R(\mathrm{raw})$ honesty note.
4. Rewrite G_GENERALITY as "post-development controlled mechanistic generality study" with the D2 provenance note and basin-limit wording (§10).
5. State p2p-only scope for the first-order direction claim; report p2l failure explicitly.
6. Report real-hardware calibration tolerances as "not independently quantified" with the perfect-GT synthetic control argument (§8).

---

## 14. Three Reviewer-Killer Questions: Answers

### Q1: "Model is wrong, therefore optimum is biased — isn't that obvious?"

**No.** The trivial statement "wrong model → wrong pose" is not the contribution. The contribution is the **pose-active projection characterization**: only mismatch that projects onto the registration pose subspace ($J^\top W\delta \neq 0$) produces first-order bias. Mismatch with large residual energy but zero pose projection ($J^\top W\delta = 0$) yields zero first-order bias — demonstrated by D4 scale mismatch (real residual energy, ~0 pose error) and D3 localized offset (same 100 mm dose as D1, 6× less bias: 13.9 vs 80.7 mm). The theory gives a computable quantity ($J^\top W\delta$) that predicts bias *direction* (cosine 0.96–0.998) and explains why some mismatches are harmless. This is a mechanistic characterization, not a tautology.

### Q2: "Since B1 predicts bias direction so well, why not just subtract it directly?"

**We did, and the answer is regime-dependent.** Direct Bias Subtraction reaches ~2 cm on VI/IV (where view geometry transfers, cos 0.99) but catastrophically fails on II (66→143 mm, worse than raw) because (a) view-direction cosine collapses to 0.56 and (b) the frozen ~161 mm magnitude mismatches II's realized ~66 mm bias. A direct pose-bias regressor has no guardrail — it always injects a full-magnitude vector and doubles the error when wrong. Mismatch-mediated correction is more stable on view-heterogeneous regimes (II Patch 41.8 mm), corrects full 6-DoF (including rotation, which DBS cannot), and has a physical mechanism derived from the same $J^\top W\delta$ the theory identifies as causal. The paper positions as a mechanism paper + interpretable regime-robust alternative, not a universally superior correction.

### Q3: "What exactly is 'coherent structured mismatch' mathematically?"

**It is mismatch whose residuals are spatially correlated, same-direction, and project onto a rigid pose mode** — formally, $\delta$ such that $J^\top W\delta \neq 0$ with $\|\delta\|$ concentrated in the pose-active subspace. The phase map quantifies this with $\eta_t$/$\eta_R$ (normalized pose-active residual coherence) and shows: (R1) large support + high $\eta$ → systematic bias that robust losses cannot remove; (R2) localized/gross (low $\eta$, small $\alpha$) → robust-suppressible; (R3) large residual energy + low $\eta$ → near-zero pose bias. The discriminator is $\eta$, not $\alpha$ alone: two conditions at the same affected fraction ($\alpha \approx 0.17$) can be harmless vs catastrophic depending on pose-active projection.

---

## 15. Frozen Contribution Statements

### Contribution 1
> Establish a first-order bias characterization linking structured nominal-model discrepancy to its pose-active projection in the registration objective and the resulting SE(3) optimum displacement.
>
> Core chain: $\delta \rightarrow J^\top W\delta \rightarrow -H^\dagger J^\top W\delta$.
>
> Scope: directionally validated for point-to-point (cosine 0.96–0.998, held-out replicated); magnitude partially predicted; p2l not supported. Robust-loss regime distinction included.

### Contribution 2
> Develop a view-conditioned structured-discrepancy correction that modifies the nominal geometry / registration objective rather than directly regressing and subtracting pose bias.
>
> Framing: mechanism paper + interpretable, regime-robust alternative to direct pose-bias regression. **No claim of universal superiority.** The DBS baseline quantifies both the ceiling (~2 cm on favorable regimes) and the risk (143 mm crash on view-heterogeneous II) of direct subtraction; ours trades peak IV accuracy for regime robustness, full 6-DoF correction, and physical interpretability.

### Contribution 3
> Identify and validate the boundary between coherent model-mismatch bias and conventional localized/gross-outlier regimes using real spacecraft trajectories, robust-estimator falsification, estimated-view mitigation, untouched evaluation, and controlled cross-geometry analysis.
>
> Evidence: G0 robust falsification (real EPOS), G1 mitigation, G2 estimated-view, G3 prospective untouched III, G_GENERALITY synthetic cross-geometry (post-development mechanistic), optional $\alpha\times\eta$ phase map.

---

## 16. Title

**Primary:**
> Structured Model Mismatch in Spacecraft LiDAR Registration: From Pose Bias Mechanism to Bias-Aware Compensation

**Alternative:**
> Model-Mismatch-Induced Pose Bias in Spacecraft LiDAR Registration: Analysis and Compensation

(Avoid: "A Novel Improved ICP...")

---

## 17. STOP RULE Confirmation

**METHOD DEVELOPMENT IS STOPPED.** This round completed exactly the four permitted task classes:
- ✅ THEORY (first-order bias theory + robust loss theory + ICP objective math audit)
- ✅ DIRECTBIAS (frozen B1 direct subtraction baseline, DIRECTBIAS_MIXED)
- ✅ AUDIT (operating assumptions, calibration budget, statistical unit, generality provenance)
- ✅ OPTIONAL (phase map executed, one frozen sweep)

**No** B2-v3, B3, neural correction, B1+B2 fusion, new shrinkage, new Hessian damping, new synthetic geometry, new selector, or re-tuning was performed. No method will be developed further. The next phase is **manuscript writing** using the frozen claims, numbers, and boundaries in this document.

---

*All artifacts under `D:\doubao\FINAL_TOPJOURNAL_HARDENING\`: THEORY/ (8 docs + 4 figures + script), DIRECT_BIAS_BASELINE/ (8 docs + 3 figures + 2 scripts), AUDIT/ (8 docs + 2 CSVs + script), OPTIONAL_PHASE_MAP/ (4 docs + figure + 2 scripts). No frozen input files were modified.*
