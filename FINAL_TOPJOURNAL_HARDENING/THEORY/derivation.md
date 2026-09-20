# Part A: First-Order Registration Bias from Structured Model Mismatch

*THEORY shard. Companion files: `notation.md` (symbols/frames/units),
`assumptions.md` (explicit assumption list), `theory_to_existing_results.csv`
(computed numbers), `figures/`. All formulas are in the fixed-correspondence
local surrogate; no claim is made that the full NN-ICP objective is globally
differentiable.*

---

## A1. Local residual linearization at the physical GT pose

Let $T_{\mathrm{GT}}$ be the ground-truth rigid transform and let
$C_{\mathrm{GT}} = \{j(i)\}$ be the nearest-neighbour correspondence evaluated
at $\xi=0$ (target frame; see `notation.md` §1). Consider a small perturbation

$$
T(\Delta\xi) = T_{\mathrm{GT}}\,\mathrm{Exp}(\widehat{\Delta\xi}),
\qquad
\Delta\xi = \begin{bmatrix}t\\ \omega\end{bmatrix}\in\mathbb{R}^6.
$$

For a fixed correspondence $C_{\mathrm{GT}}$ the per-point residual is

$$
r_i(\Delta\xi) = T(\Delta\xi)\,p_i - m_{j(i)}.
$$

Taylor-expanding about $\Delta\xi=0$ to first order,

$$
r_i(\Delta\xi) \;\approx\; \underbrace{r_i(0)}_{\delta_i} \;+\;
\underbrace{\left.\frac{\partial r_i}{\partial \xi}\right|_{0}}_{A_i}\,
\Delta\xi
\;=\; \delta_i + A_i\,\Delta\xi,
$$

where

- $\delta_i = p_i - m_{j(i)} \in\mathbb{R}^3$ is the **structured model
  discrepancy at the physical GT** (the R4 clustered residual, the signed inward
  bias, MLI/specular/multipath returns, etc.; see
  `IDENTIFIABILITY_AUDIT.md` §2);
- $A_i = [I_3 \mid [p_i]_\times] \in\mathbb{R}^{3\times 6}$ is the residual
  Jacobian w.r.t. the SE(3) perturbation (p2p). For p2l the scalar Jacobian is
  $a_i^\top = [n_{j(i)}^\top \mid (p_i\times n_{j(i)})^\top]$.

### Scope statement (critical)

This is the **fixed-local-correspondence surrogate**

$$
\tilde J(\Delta\xi \mid C_{\mathrm{GT}}) = \tfrac{1}{N}\sum_i r_i(\Delta\xi)^\top W_i\, r_i(\Delta\xi),
$$

with $C_{\mathrm{GT}}$ frozen. We **do not** claim that the full nearest-neighbour
ICP objective $J(\xi)$ (which recomputes $j(i)$ at every evaluation) is globally
differentiable, nor that the surrogate equals the full objective away from
$\xi=0$. The surrogate is a local analytical device used to predict the *direction*
of the first-order optimum; its accuracy at $\xi=0$ is verified empirically in
Part D (`AUDIT/icp_objective_math_audit.md`) via the finite-difference landscape.

---

## A2. Least-squares first-order bias

Substituting the linearized residual into the quadratic surrogate,

$$
\tilde J(\Delta\xi) = \tfrac{1}{N}\sum_i (\delta_i + A_i\Delta\xi)^\top W_i (\delta_i + A_i\Delta\xi).
$$

Expanding,

$$
\tilde J(\Delta\xi) = \tilde J(0) + g_\delta^\top \Delta\xi + \tfrac{1}{2}\Delta\xi^\top H\,\Delta\xi,
$$

with

$$
\boxed{
g_\delta = \sum_i A_i^\top W_i \delta_i \;=\; J^\top W \delta,
\qquad
H = \sum_i A_i^\top W_i A_i \;=\; J^\top W J.
}
$$

Here $J$ stacks the $A_i$, $W$ stacks the $W_i$, and $\delta$ stacks the
$\delta_i$. The first-order stationarity condition $\nabla_{\Delta\xi}\tilde J = 0$
gives

$$
g_\delta + H\,\Delta\xi^\star = 0
\quad\Longrightarrow\quad
\Delta\xi^\star \approx -H^{-1} g_\delta = -(J^\top W J)^{-1} J^\top W \delta.
$$

### Observable-subspace pseudoinverse

The Gauss-Newton Hessian $H=J^\top W J$ is positive semi-definite but, on a
surface point cloud with incomplete viewing geometry, it is generically **rank
deficient or near-singular** in the tangent-to-surface / unobserved viewing
directions (tangential sliding, unobserved rotations about surface normals).
In those directions $H^{-1}$ does not exist. We therefore use the
**Moore–Penrose pseudoinverse on the observable subspace**:

$$
\boxed{
\hat{\Delta\xi} \;=\; -H^\dagger g_\delta
\;=\; -(J^\top W J)^\dagger J^\top W \delta.
}
$$

$H^\dagger$ projects $g_\delta$ onto the column space of $J$ (the pose-observable
subspace) and discards components of $g_\delta$ that lie in the null space of
$H$. This is the correct first-order step when $H$ is singular: it is the
minimum-norm least-squares correction in the observable directions.

In the empirical cache, `raw__dhat` is exactly $-H^\dagger g$ (pre-computed),
and `raw__g` is exactly $g_\delta = J^\top W\delta$ (central-difference gradient
of the full objective at $\xi=0$, which equals the fixed-correspondence analytic
gradient at $\xi=0$; see Part D).

### Explicit assumption list

(See `assumptions.md` for the full enumerated list. The first-order formula
$\hat{\Delta\xi}=-H^\dagger g_\delta$ requires:

1. $\xi=0$ lies in a neighbourhood where $C_{\mathrm{GT}}$ is locally stable
   (no correspondence flips);
2. the residual is first-order Taylor-valid at the scale of $\hat{\Delta\xi}$;
3. $H$ is positive definite on the observable subspace;
4. higher-order terms (quadratic residual curvature, second-order correspondence
   changes) are negligible for the **direction** of the optimum;
5. $\delta_i$ is a deterministic, structured discrepancy — not zero-mean i.i.d.
   noise.

This is **never** an exact global ICP solution. It is a first-order,
local, direction-of-bias predictor.)

---

## A3. Pose-active vs pose-inactive mismatch

Define the **pose-active mismatch component**

$$
p_\delta \;\equiv\; J^\top W \delta \;=\; g_\delta \;\in\;\mathbb{R}^6.
$$

This is the projection of the structured discrepancy field $\{\delta_i\}$ into
the 6-dimensional registration pose subspace spanned by the columns of $J$.

### Core statement

$$
\boxed{\text{Pose bias is governed by the projection of model discrepancy
into the registration pose subspace.}}
$$

The decisive corollary:

$$
\text{If } J^\top W\delta = 0,\ \text{then } \hat{\Delta\xi} = -H^\dagger J^\top W\delta = 0,
$$

**even when $\|\delta\|\gg 0$.** A structured mismatch field can have large
residual energy $\sum_i\|\delta_i\|^2$ and yet produce **zero first-order pose
bias**, because its spatial pattern is orthogonal to the pose-sensitive modes of
$J$. Conversely, a small but spatially coherent discrepancy can produce a large
pose bias if it aligns with a pose mode.

### Interpretation across mismatch classes

| Class | Physical form | $J^\top W\delta$ | Expected first-order bias | Empirical evidence |
|---|---|---|---|---|
| **D1 / D5** | Appendage displacement / tilt: a coherent, spatially localised rigid shift of a sub-assembly. | **Large**: the displaced sub-assembly residuals align with a translation/rotation mode of $J$. | Large, dose-monotone displacement. | G_GENERALITY D1 dose 0→100 mm gives ete 0.02→80.7 mm (LS, p2p). D1 diagnostic norm vs $\|g\|$: Spearman 0.927 (VI, n=501). |
| **D2** | Entirely absent component: a gross, localized gross outlier block. | Large but dominated by a small outlier set; M-estimator downweights it. | Basin-clip / solver-dependent; robust loss recovers. | G_GENERALITY D2 f=1.0: LS hits 300 mm basin clip (on-bound 66.7%), Huber drops to 11.6 mm. |
| **D3** | Local surface offset: a small-amplitude local displacement that is nearly tangential to the surface normal / weakly coupled to pose. | **Small relative to dose**: same 100 mm dose as D1 but ete only 13.8 mm (vs 80.7 mm). | Weak, near-linear-in-dose bias. | G_GENERALITY D3 dose-response in `theory_to_existing_results.csv`. |
| **D4** | Appendage scale / global nuisance: a near-uniform scale factor that the rigid 6-DoF objective absorbs weakly or which is removed by global nuisance correction. | Small in the residualised condition; combined-nuisance gradient still $10^3\times$ self-floor but direction concentration collapses. | Reduced but non-zero residual bias. | `OBJECTIVE_STATIONARITY.md` §2: combined gradient still 1.4–3.7k× self-floor; `LOCAL_OPTIMUM_BIAS.md` §1: combined residual displacement 58–64 mm. |

### Why the predictor is $-H^\dagger g_\delta$, not $-H^{-1}\delta$

The formula $\hat{\Delta\xi}=-H^\dagger J^\top W\delta$ makes explicit that the
bias direction is determined by **both** the discrepancy $\delta$ and the
observation geometry $J$. Two scans with identical $\|\delta\|$ but different
viewing geometry (different $J$) will have different $p_\delta$ and therefore
different bias. This is precisely why the frozen patch/view predictor in
`VI_ONLY_PREDICTOR_FROZEN.npz` (k*=16, `vrange`, `uview`, `blocks`) conditions
on view geometry, not on raw residual magnitude.

---

## A4. Normalised pose-active index — rigor-first, unit check

### Why a normalised index is tempting

$\|p_\delta\|_6 = \|J^\top W\delta\|_6$ mixes metres (translation block) and
$\mathrm{m}^2/\mathrm{rad}$ (rotation block). Calling it "the pose-active
magnitude" without a unit caveat is not rigorous. A dimensionless,
geometrically interpretable index is desirable for cross-scan comparison.

### Unit check and decision

Let $g_t\in\mathbb{R}^3$ be the translation block and $g_R\in\mathbb{R}^3$ the
rotation block of $p_\delta=J^\top W\delta$. Their units are

$$
[g_t] = \mathrm{m}, \qquad [g_R] = \mathrm{m}^2\,\mathrm{rad}^{-1}.
$$

A single norm $\sqrt{\|g_t\|^2+\|g_R\|^2}$ is therefore dimensionally invalid.
Options:

1. **Block-separate indices (recommended).** Define
   $$
   \eta_t = \frac{\|g_t\|}{\sigma_{g_t,\mathrm{self}}},
   \qquad
   \eta_R = \frac{\|g_R\|}{\sigma_{g_R,\mathrm{self}}},
   $$
   normalised by the model-self null gradient scale (the `self_gnorm` column in
   the IV/V caches). Each is dimensionless, has a clear geometric meaning
   ("how many self-floor sigmas of translation/rotation gradient"), and is
   computed independently for translation and rotation.
2. **Weighted Riemannian metric.** Use a block-diagonal metric
   $M=\mathrm{diag}(s_t^2 I_3, s_R^2 I_3)$ with $s_t$ a characteristic range
   (≈10 m) and $s_R$ dimensionless; $\eta_M=\sqrt{g^\top M g}$. This collapses
   to option 1 with $s_R = s_t^2 / (\mathrm{range})$. It is more elegant but
   introduces a choice of $s_t$.
3. **Do not define a normalised index.** Keep $p_\delta=J^\top W\delta$ as the
   theoretical quantity and report block norms separately.

### Decision for this round

We adopt **option 3** for the main theoretical claim and report block norms
separately in `theory_to_existing_results.csv`. Rationale:

- The core claim (A3) is about **projection structure**, not scalar magnitude;
  no dimensionless index is required to make it.
- Options 1–2 require choosing a normalisation scale ($\sigma_{\mathrm{self}}$ or
  $s_t$), which risks being chosen by the data rather than by a pre-registered
  geometric rule. The hard rules forbid tuning by results.
- The empirical direction-cosine evidence (A5(b)) is scale-invariant and
  block-resolved; it does not need a normalised index.

If a normalised index is added in a later round, it must be pre-registered with
an independent geometric definition (e.g. $s_t$ = mean lidar range from the
trajectory manifest, not fitted to the bias).

---

## A5. Connection to existing data (computed, not estimated)

All numbers below are produced by `theory_empirics.py` from the frozen caches;
the CSV is `theory_to_existing_results.csv`. Figures are in `figures/`.

### A5(a) Pose-active gradient norm vs measured bias magnitude

For each of 501 VI scans we compute $\|g_\delta\|$ (raw__g, 6-DoF and
translation-block) and compare with $\|\xi^\star_t\|$ (raw__xistar, first 3
components, in mm). Spearman correlation (unit-free, robust) and Pearson
correlation:

| Condition | Obj | Spearman $\|g\|_6$ vs $\|\xi^\star_t\|$ | Pearson |
|---|---|---:|---:|
| raw | p2p | 0.439 | 0.495 |
| raw | p2l | 0.420 | −0.574 (unit-mixing artefact; translation-only Pearson 0.285) |
| scale | p2p | 0.264 | 0.353 |
| combined | p2p | **0.620** | **0.681** |

*Source: `objective_main.npz`, computed by `theory_empirics.py` A5(a).*

**Interpretation (honest):** the magnitude correlation is **moderate**, not
strong. After global nuisance removal (combined), Spearman rises to 0.62. This
is consistent with `QUADRATIC_BIAS_PREDICTION.md` §2: the first-order Newton
step gives the right **direction** but over-estimates the **magnitude** by
~2.1–2.4× raw (dhat median 345 mm vs xistar 161 mm); magnitude calibration
requires re-linearising as correspondences re-attach, which is outside the
first-order local claim. We therefore claim direction prediction, not
quantitative magnitude prediction.

Figure: `figures/g_norm_vs_bias.png`.

### A5(b) Direction cosine: predicted step vs measured optimum

Per-frame direction cosine between $\hat{\Delta\xi}=-H^\dagger g$
(`raw__dhat`) and $\xi^\star$ (`raw__xistar`), translation block:

| Condition | Obj | median cos | IQR | fraction positive |
|---|---|---:|---|---:|
| raw | p2p | **0.959** | [0.895, 0.978] | 0.966 |
| raw | p2l | 0.386 | [−0.184, 0.726] | 0.685 |
| scale | p2p | **0.970** | [0.916, 0.987] | 0.978 |
| combined | p2p | **0.998** | [0.996, 0.999] | 1.000 |
| combined | p2l | 0.409 | [−0.237, 0.748] | 0.671 |

*Source: `objective_main.npz`, computed by `theory_empirics.py` A5(b). Matches
`QUADRATIC_BIAS_PREDICTION.md` §1 (raw p2p 0.959, combined p2p 0.998; p2l
fails).*

**Held-out replication (IV, n=2428):** p2p translation cosine median 0.946
(raw) rising to 0.988 (N3 nuisance-removed); p2l remains 0.26–0.38. The
p2p directional prediction replicates on a held-out trajectory; p2l does not.

**Negative result preserved:** point-to-plane does **not** satisfy the
first-order direction predictor. The p2l Hessian is near-singular in tangential
directions (`raw__eigmin`/`raw__cond`), and $H^\dagger g$ is dominated by
ill-conditioned tangential modes. We report this honestly; p2l supports only
the qualitative claim that both objectives move in the same direction
(`OBJECTIVE_STATIONARITY.md` §4: J1/J2 gradient cosine median 0.988 raw), not
the quantitative direction prediction.

Figure: `figures/direction_cosine.png`.

### A5(c) Pose-active projection: structured mismatch vs residual energy

The key A3 corollary is that **residual energy ≠ pose-active component**. We
verify this two ways:

1. **VI diagnostic vectors.** The structured appendage diagnostic `raw__D1`
   correlates with $\|g_\delta\|$ at Spearman **0.927** (p2p, p=5.5e-215).
   The residual energy $J_0$ correlates at 0.90 — both are high because the VI
   real mismatch is dominated by R4 structured clusters that happen to be
   pose-active. The clean distinction comes from synthetic G_GENERALITY.

2. **G_GENERALITY controlled dose (cleaner).** At a **100 mm dose**:
   - D1 (appendage displacement, pose-active): LS ete = **80.7 mm**.
   - D3 (local surface offset, weak pose coupling): LS ete = **13.8 mm**.

   Same nominal residual dose, ~6× different pose bias. This is the direct
   empirical demonstration of A3: the same $\|\delta\|$ produces very
   different $J^\top W\delta$ depending on whether the residual pattern aligns
   with a pose mode.

Figure: `figures/pose_active_projection.png`.

### A5(d) Summary of what the data supports

- **Strong (quantitative):** p2p direction cosine 0.96→0.998 (raw→combined),
  replicates on IV held-out (0.946→0.988). The first-order formula predicts
  *which way* the GT-started local optimum moves.
- **Moderate (qualitative-to-partial):** magnitude correlation Spearman 0.44
  raw, 0.62 combined; Newton step over-estimates distance by ~2× raw.
- **Negative (preserved):** p2l direction prediction fails (cos 0.32–0.41);
  magnitude Pearson for mixed 6-DoF norms is unreliable due to unit mixing.
