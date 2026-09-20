# Explicit Assumptions for the First-Order Bias Formula

*THEORY shard, companion to `derivation.md`. This file enumerates every
assumption under which
$\hat{\Delta\xi}=-H^\dagger J^\top W\delta$ is claimed to hold, and the
empirical status of each. No assumption is hidden in a "standard practice"
formulation.*

---

## A. Geometric / local-surrogate assumptions

| # | Assumption | Why needed | Empirical status |
|---|---|---|---|
| A1 | $\xi=0$ lies in a neighbourhood where the nearest-neighbour correspondence $C_{\mathrm{GT}}$ is locally stable (no point jumps to a different model surface patch over the step $\hat{\Delta\xi}$). | The fixed-correspondence surrogate $\tilde J(\Delta\xi\mid C_{\mathrm{GT}})$ is only meaningful if $j(i)$ does not flip. | Verified by the landscape check (Part D2): at the smallest perturbation scale (±10 mm translation, ±0.5° rotation) the predicted descent side lowers the full recomputed-correspondence objective 92.9% (p2p) / 84.0% (p2l) of the time. At larger scales agreement drops (84.9% / 78.3%), confirming the local-neighbourhood scope. |
| A2 | The residual is first-order Taylor-valid at the scale of $\hat{\Delta\xi}$; higher-order terms in $r_i(\Delta\xi)=\delta_i+A_i\Delta\xi+O(\|\Delta\xi\|^2)$ are negligible for the **direction** of the optimum. | The linearization $r_i\approx\delta_i+A_i\Delta\xi$ must hold on the sphere of radius $\|\hat{\Delta\xi}\|$. | Partially supported: direction cosine 0.96–0.998 (p2p) confirms direction; magnitude over-estimation by ~2× (`QUADRATIC_BIAS_PREDICTION.md` §2) confirms that **higher-order curvature is not negligible for magnitude**. The claim is explicitly direction-only. |
| A3 | $H=J^\top W J$ is positive definite on the pose-observable subspace; unobservable directions are handled by $H^\dagger$, not $H^{-1}$. | p2l is near-singular in tangent-to-surface directions; using $H^{-1}$ would amplify null-space noise. | Verified: p2l direction cosine collapses to 0.32–0.41 precisely because $H$ is ill-conditioned (`raw__eigmin`, `raw__cond`); p2p is better conditioned and gives 0.96–0.998. The pseudoinverse is the correct (and used) operator. |

## B. Statistical / model-discrepancy assumptions

| # | Assumption | Why needed | Empirical status |
|---|---|---|---|
| B1 | $\delta_i$ is a **deterministic, structured** discrepancy field (R4 clusters, signed inward bias, appendage misplacement), not zero-mean i.i.d. sensor noise. | If $\delta_i$ were zero-mean i.i.d., $\mathbb{E}[J^\top W\delta]=0$ and there would be no first-order pose bias — the classic unbiased-LS setting. | Verified by `OBJECTIVE_STATIONARITY.md`: real $\|g\|$ is 1.4×10³–1.0×10⁴× the model-self null, and spatial shuffling of $\delta_i$ reduces $\|g\|$ by ~2.5–2.8× (p=0.010), proving the gradient depends on *spatial structure*, not residual magnitude. |
| B2 | The structured discrepancy is present at $\xi=0$ (i.e. the GT pose is known and the scan is physically aligned to the model). This is a probing setup, not a pose-initialisation benchmark. | The formula computes bias *of the objective at GT*. It is not a claim about ICP starting from arbitrary initialisation. | Stated explicitly in `LOCAL_OPTIMUM_BIAS.md` §1: GT is used to probe whether the objective is unbiased; L-BFGS on-bound rate = 0; two independent optimisers agree. |
| B3 | Higher-order terms (quadratic residual curvature, correspondence re-attachment, second-order NN boundary crossings) are neglected in the **direction** but not claimed negligible in **magnitude**. | Honest scope: direction prediction is strong; magnitude prediction is weak. | `QUADRATIC_BIAS_PREDICTION.md` §2: raw Newton step median 345 mm vs measured 161 mm (2.1× over-estimate); combined-nuisance slope 0.286 (CI excludes 0 but ≪1). We claim direction, not quantitative magnitude. |

## C. What the formula is **not**

1. **Not an exact global ICP solution.** $\hat{\Delta\xi}=-H^\dagger g_\delta$ is a
   first-order local predictor. It is not claimed to equal $\xi^\star$ in
   magnitude.
2. **Not a statement that the NN objective is globally differentiable.** The
   surrogate $\tilde J$ is quadratic and smooth; the full $J(\xi)$ is
   piecewise-smooth (NN reassignment is discontinuous at Voronoi boundaries).
   The equality $g_{\mathrm{full}}(0)=J^\top W\delta$ holds **at $\xi=0$**
   because (i) at $\xi=0$ the correspondences are exactly $C_{\mathrm{GT}}$,
   and (ii) the NN assignment map is a.e. constant, so its derivative vanishes
   in expectation. This is verified numerically in Part D, not assumed.
3. **Not a p2l result.** p2l direction prediction fails (cos 0.32–0.41). The
   formula is quantitatively supported for p2p only; p2l enters only as
   cross-objective directional consistency.
4. **Not a magnitude-unbiased estimator.** The 6-DoF norm mixes metres and
   $\mathrm{m}^2/\mathrm{rad}$; magnitude claims must use block-resolved norms
   and are explicitly partial (Spearman 0.44→0.62 after nuisance removal).

## D. Nuisance-condition assumptions

The cache provides three nuisance-removal conditions:

- **raw**: no global nuisance removed;
- **scale** (N3): global scale factor corrected;
- **combined** (N4): global scale + global signed-mean inward bias corrected.

The directional prediction **strengthens** as nuisance is removed (p2p cos
0.959→0.970→0.998). This is expected: global nuisance components (uniform
inward shrinkage, scale) contribute a common-mode gradient that partially masks
the local pose-active signal. The theory does **not** require nuisance removal;
it says the local pose-active projection is what governs direction.
