# Part B: Robust Loss Theory for Structured-Mismatch Registration

*THEORY shard. Companion: `robust_regime_interpretation.md` (data matching).
All formulas extend the fixed-correspondence surrogate of Part A to M-estimator
losses. No method is redeveloped; no parameter is tuned.*

---

## B1. Local gradient under a robust (M-estimator) loss

Replace the quadratic per-point weight with a robust influence function. Define

$$
J_\rho(\xi) = \sum_i \rho\!\big(r_i(\xi)\big),
$$

where $\rho:\mathbb{R}\to\mathbb{R}_+$ is the robust loss (Huber, Tukey,
trimmed, etc.). For point-to-plane we take the scalar residual
$r_i = n_{j(i)}^\top (T(\xi)p_i - m_{j(i)})$; for point-to-point the vector
residual is normed.

At the physical GT ($\xi=0$), under the same fixed-correspondence linearization
$r_i(\Delta\xi)\approx\delta_i + A_i\Delta\xi$, the gradient is

$$
g_\rho = \nabla_\xi J_\rho(0)
= \sum_i A_i^\top \,\psi(\delta_i),
\qquad
\psi(r) = \rho'(r).
$$

For the quadratic LS loss, $\psi(r)=r$ and $g_\rho = \sum_i A_i^\top \delta_i =
J^\top W\delta$, recovering the Part A pose-active gradient. The robust loss
replaces the linear influence $\delta_i$ with a non-linear, bounded
$\psi(\delta_i)$.

### Canonical forms

| Loss | $\rho(r)$ | $\psi(r)=\rho'(r)$ | Behaviour for $|r|\gg c$ |
|---|---|---|---|
| Quadratic (LS) | $\tfrac{1}{2}r^2$ | $r$ | grows unbounded |
| Huber | $\tfrac{1}{2}r^2$ if $|r|\le c$; $c|r|-\tfrac{1}{2}c^2$ otherwise | $r$ if $|r|\le c$; $c\,\mathrm{sign}(r)$ otherwise | truncated at $\pm c$ |
| Trimmed / hard reject | $r^2$ if $|r|\le c$; $0$ otherwise | $r$ if $|r|\le c$; $0$ otherwise | zero weight |

The robust objective's first-order optimum direction is

$$
\hat{\Delta\xi}_\rho \approx -H_\rho^\dagger\, g_\rho,
\qquad
H_\rho = \sum_i A_i^\top \psi'(\delta_i)\, A_i.
$$

---

## B2. Two statistical regimes of structured mismatch

The key theoretical point is that **robustification attenuates the influence of
large residuals, but it does not guarantee unbiasedness when the mismatch is
spatially coherent**. Two regimes must be distinguished.

### Regime A — Localised / gross outliers

A small number of points have $|\delta_i|\gg c$ (e.g. an entirely absent
component, a single protruding appendage, a backface return). For these points,

$$
\psi(\delta_i) \to \text{bounded or zero}
\quad\text{as}\quad |\delta_i|\to\infty.
$$

The outlier's contribution to $g_\rho=\sum_i A_i^\top\psi(\delta_i)$ is
truncated. If the inlier set $\{i:|\delta_i|\le c\}$ is approximately
structured-free (zero-mean noise), then

$$
g_\rho \approx \sum_{i:|\delta_i|\le c} A_i^\top \delta_i \approx 0,
$$

and robustification removes the bias. This is the regime where ICP with Huber /
trimming is **designed** to work.

**Empirical match (G_GENERALITY D2, missing component):** at dose $f=1.0$
(entire component absent), LS ICP hits the 300 mm basin clip (on-bound 66.7%),
while Huber drops to 11.6 mm — robust weighting successfully neutralises the
gross outlier block. *Source: `geometry_results.csv`, D2_missing_component,
mag=1.0, computed by `theory_empirics.py`.*

### Regime B — Coherent moderate mismatch

Many points have spatially correlated, same-direction residuals in the
inlier / transition region ($|\delta_i|\le c$ but with coherent sign and
direction). Here $\psi(\delta_i)\approx\delta_i$ (the Huber inlier regime is
identical to LS), and

$$
g_\rho = \sum_i A_i^\top \psi(\delta_i) \approx \sum_i A_i^\top \delta_i
= J^\top W\delta = g_{\mathrm{LS}}.
$$

$$
\boxed{\text{When mismatch is spatially coherent and moderate in amplitude,
robustification does not guarantee pose unbiasedness: } g_\rho \approx g_{\mathrm{LS}}.}
$$

The robust loss was designed to reject *isolated* gross outliers; it is not a
de-randomiser of a structured, spatially coherent residual field. If the entire
inlier patch shifts by a small but systematic amount along a pose direction,
Huber sees it as inlier-level and the same pose-active gradient persists.

**Empirical match (G_GENERALITY D1, appendage displacement):** at 50 mm dose
the endpoint translation error is LS = **39.2 mm**, Huber = **42.8 mm**,
Trim = **50.7 mm**. Robust weighting does **not** eliminate the bias, and in
this case Huber and Trim produce a *larger* displacement than LS. The coherent
appendage shift is in the inlier/transition band and is not rejected.
*Source: `geometry_results.csv`, D1_appendage_disp, mag=50, p2p; exact values
39.16 / 42.75 / 50.68 mm (two-stage cross-geometry medians) computed by `theory_empirics.py`.*

### Important framing

Robust ICP is **not "failing"** in Regime B. It addresses a different
statistical regime (isolated gross outliers) than the one structured model
mismatch presents (spatially coherent, moderate-amplitude, physically
motivated residuals). Applying a robust loss and observing persistent bias is
the *predicted* behaviour, not a contradiction. The theory predicts:

- Regime A (gross localised outliers): robust loss removes bias.
- Regime B (coherent moderate mismatch): robust loss attenuates but does not
  eliminate bias, and can occasionally increase displacement.

---

## B3. Why coherent mismatch defeats robustification (mechanistic sketch)

Under Huber, the influence function saturates only when $|\delta_i|>c$. A
coherent appendage displacement of 50 mm produces residuals of order 50 mm on
the affected sub-assembly. Whether these are above or below the threshold $c$
depends on the chosen scale (typically $c$ ≈ 1.345·MAD ≈ a few cm for
spacecraft LiDAR residuals whose median is 65 mm; see
`IDENTIFIABILITY_AUDIT.md` §2). With a 50 mm shift, a large fraction of the
affected points land **at or below** the saturation threshold, where
$\psi(r)=r$ exactly as in LS. The robust loss therefore leaves the
pose-active projection $J^\top W\delta$ largely intact.

Moreover, robustification changes the **Hessian** $H_\rho$ as well as the
gradient $g_\rho$. If $\psi'(\delta_i)<1$ on the affected patch, the
observability of the corresponding pose mode is reduced, which can *lengthen*
the Newton step $-H_\rho^\dagger g_\rho$ even when $g_\rho$ is attenuated.
This is the mechanistic reason Trim can produce a larger displacement than LS
(50.7 vs 39.2 mm): the trimmed Hessian under-weights the affected patch,
making the pose mode less observable, and the step into it grows.

This is a qualitative mechanism, not a closed-form prediction; the quantitative
numbers come from G_GENERALITY.
