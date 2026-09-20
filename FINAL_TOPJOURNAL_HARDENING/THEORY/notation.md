# Notation, Frames, Units, and SE(3) Conventions

*THEORY shard, Part A supporting document. All symbols used in `derivation.md`,
`assumptions.md`, `robust_loss_derivation.md`, and `AUDIT/icp_objective_math_audit.md`
are defined here. Source of truth for frames: `structured_mismatch_phase0/scripts/m_common.py`.*

---

## 1. Coordinate frames

| Symbol | Meaning |
|---|---|
| $T_{\mathrm{GT}}$ | Ground-truth rigid transform mapping the source scan cloud to the target (= nominal CAD) frame. At $\xi=0$ the source is exactly at its physical GT pose relative to $M$. |
| $M \subset \mathbb{R}^3$ | Fixed nominal model point cloud (67,870 points), target frame. |
| $P_t = \{p_i\}_{i=1}^{N_t}$ | GT-aligned source scan points in the target frame. At $\xi=0$, $p_i$ is the physically correct position of return $i$. |
| $C_{\mathrm{GT}} = \{j(i)\}$ | GT-local nearest-neighbour correspondence: $j(i) = \arg\min_{m\in M}\|p_i - m\|$, recomputed at $\xi=0$ with a $c$KD-tree over $M$. Frozen for the local surrogate. |

**Frame contract (locked, `m_common.py` lines 5–13):** every residual lives in the
**target frame**. The lidar optical axis is $+X$ in these files (verified in
`IDENTIFIABILITY_AUDIT.md` §1). Translation units are metres, rotation units are radians.

## 2. SE(3) local chart

A pose perturbation about $T_{\mathrm{GT}}$ is parameterised by a body-fixed
6-vector

$$
\xi = \begin{bmatrix} t \\ \omega \end{bmatrix} \in \mathbb{R}^6,
\qquad t \in \mathbb{R}^3 \text{ (m)}, \quad \omega \in \mathbb{R}^3 \text{ (rad)},
$$

and applied to a point as

$$
T(\xi)\,p_i = \exp\!\big([\omega]_\times\big)\,p_i + t,
$$

where $[\cdot]_\times$ is the skew-symmetric matrix. This is the left-minus local
chart; the inverse logarithm is

$$
\xi = \log\!\big(T_{\mathrm{GT}}^{-1} T^\star\big) \in \mathbb{R}^6.
$$

We use $\oplus$ / $\ominus$ informally for chart composition; **no** non-trivial
BCH expansion is required because the local theory is first-order.

### Unit scaling caveat (6-DoF arrays)

The 6-vector stacks three translations in metres and three rotations in radians.
Consequences:

- The first three components of any 6-DoF gradient $g \in \mathbb{R}^6$ have
  units of $\mathrm{m}$ (gradient of a $\mathrm{m}^2$ objective w.r.t. $\mathrm{m}$),
  while the last three have units of $\mathrm{m}^2\,\mathrm{rad}^{-1}$ (gradient
  w.r.t. a dimensionless angle). A bare Euclidean norm $\|g\|_6$ therefore mixes
  $\mathrm{m}$ and $\mathrm{m}^2/\mathrm{rad}$ and is **not** a geometrically
  homogeneous quantity.
- For dimensional checks we always report the translation block
  $\|g_{1:3}\|$ and rotation block $\|g_{4:6}\|$ separately. The 6-DoF norm is
  retained only as a rank-ordering statistic (Spearman correlation is unit-free).
- A normalised, dimensionally homogeneous pose-active index is **not** defined
  in this round (see `derivation.md` A4).

## 3. Residual, Jacobian, and weights

For a fixed correspondence $C_{\mathrm{GT}}$ and a perturbation $\Delta\xi$,

$$
r_i(\Delta\xi) = T(\Delta\xi)\,p_i - m_{j(i)},
$$

with the model point $m_{j(i)}$ and frozen PCA normal $n_{j(i)}$. At $\Delta\xi=0$,

$$
\delta_i \equiv r_i(0) = p_i - m_{j(i)} \in \mathbb{R}^3
$$

is the **structured model discrepancy at the physical GT** (the signed inward
bias, R4 clusters, etc.). The per-point residual Jacobian w.r.t. the chart is

$$
A_i = \frac{\partial r_i}{\partial \xi}\bigg|_{\xi=0} \in \mathbb{R}^{3\times 6},
\qquad
A_i = \big[\,I_3 \;\big|\; [p_i]_\times \big]
$$

for point-to-point. For point-to-plane the scalar residual is
$\rho_i = n_{j(i)}^\top r_i$ and the Jacobian is

$$
a_i^\top = \frac{\partial \rho_i}{\partial \xi} =
\big[\,n_{j(i)}^\top \;\big|\; (p_i \times n_{j(i)})^\top \big]
\in \mathbb{R}^{1\times 6}.
$$

Weights: $W = \mathrm{diag}(w_i)$ for p2p (isotropic per-point weight; in the
frozen objectives $w_i = 1/N$), and for p2l the scalar residual already carries
the normal projection. Stacking,

$$
J = \begin{bmatrix} A_1^\top \\ \vdots \\ A_N^\top \end{bmatrix} \in \mathbb{R}^{N\times 6}
\quad\text{(p2p, stacked as $3N\times6$ after vectorising)},
$$

but in the closed-form we use the compact notation

$$
g_\delta = \sum_i A_i^\top W_i \delta_i \;=\; J^\top W \delta,
\qquad
H = \sum_i A_i^\top W_i A_i \;=\; J^\top W J,
$$

where $W_i$ is the per-point weight block.

## 4. Objectives

| Objective | Definition | Weight block |
|---|---|---|
| Point-to-point (p2p) | $\tilde J_{\mathrm{p2p}}(\xi) = \tfrac{1}{N}\sum_i \|r_i(\xi)\|^2$ | $W_i = \tfrac{1}{N} I_3$ |
| Point-to-plane (p2l) | $\tilde J_{\mathrm{p2l}}(\xi) = \tfrac{1}{N}\sum_i \big(n_{j(i)}^\top r_i(\xi)\big)^2$ | $W_i = \tfrac{1}{N} n_{j(i)}n_{j(i)}^\top$ (scalar residual) |

Both are the **fixed-correspondence surrogate** $\tilde J(\xi\mid C_{\mathrm{GT}})$.
The **full** ICP objective $J(\xi)$ recomputes $j(i)$ at every evaluation via a
$c$KD-tree; see `AUDIT/icp_objective_math_audit.md` for the surrogate/full
distinction.

## 5. Key symbols used across THEORY documents

| Symbol | Definition | Units |
|---|---|---|
| $\Delta\xi$ | Perturbation from GT in the local chart | $\mathrm{m}$ / $\mathrm{rad}$ |
| $\delta_i$ | Structured model discrepancy at GT, point $i$ | $\mathrm{m}$ |
| $A_i$ | Residual Jacobian at GT | mixed |
| $W$ | Per-point weight block | depends on objective |
| $g_\delta = J^\top W\delta$ | Pose-active gradient (pose-active mismatch component) | $\mathrm{m}$ (trans) |
| $H = J^\top W J$ | Observed (Gauss-Newton) Hessian at GT | mixed |
| $H^\dagger$ | Moore–Penrose pseudoinverse on the observable subspace | mixed |
| $\hat{\Delta\xi} = -H^\dagger g_\delta$ | First-order Newton step (predicted bias direction) | $\mathrm{m}$ / $\mathrm{rad}$ |
| $\xi^\star$ | Measured GT-started local optimum displacement $\log(T_{\mathrm{GT}}^{-1}T^\star)$ | $\mathrm{m}$ / $\mathrm{rad}$ |
| $\rho(\cdot)$ | Robust loss (Part B) | dimensionless |
| $\psi(r) = \rho'(r)$ | Influence function | same as $r$ |
| $c$ | Robust loss threshold (Huber) | $\mathrm{m}$ |

## 6. NPZ array convention (for reproducibility)

From `objective_main.npz` (and the IV/V/II external caches), the 6-DoF arrays have
shape `(N, 6, 2)` with:

- **last dim 0** = point-to-point, **last dim 1** = point-to-plane;
- **first 3 rows** of the 6-block = translation (m), **last 3 rows** = rotation (rad).

Keys used this round: `raw__g`, `scale__g`, `combined__g` (= $J^\top W\delta$),
`raw__H` (= $H$), `raw__dhat` (= $-H^\dagger g$, pre-computed Newton step),
`raw__xistar` (= $\xi^\star$), `raw__J0` (= $J(0)$), `landscape` (shape
`(501,2,3,3,2,2)`; dim1=0 translation group / 1 rotation group, dim3=grid scale,
dim4=0 positive / 1 negative perturbation, dim5=0 p2p / 1 p2l).

*Source: `structured_mismatch_phase0/scripts/cache/rescue/objective_main.npz`;
convention verified against `m_common.py` lines 72–131.*
