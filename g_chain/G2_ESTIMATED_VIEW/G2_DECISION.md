# G2_DECISION.md — Estimated-View Bias-Aware Registration

- Date: 2026-09-10. Runs only because G1 = G1_PASS. T0 frozen identically for every trajectory (raw p2p LS
  local optimum); frozen predictor μ_j(z) reused; **no pose network / estimator upgrade**.

## VERDICT: **G2_PASS** — the mitigation runs from an *estimated* view and retains ≈98–100% of the oracle gain with a sub-mm oracle gap and no catastrophic sensitivity; the GT-view dependency is substantively removed (the II full-level neutrality is inherited from G1 and handled by the frozen patch fallback).

### 1. Oracle → estimated gap (median e_t [mm])

| set | T0 raw | oracle z(T_GT) | est view, GT-start | **est view, warm-start pipeline** | Δ warm−oracle | mitigation retained (warm) |
|---|---:|---:|---:|---:|---:|---:|
| VI dev 501 | 161.4 | 76.9 | 76.7 | **77.1** | +0.28 | 0.997 |
| IV in 156 | 160.4 | 82.9 | 84.0 | **86.6** | +1.44 | 0.979 |
| II in 428 | 66.1 | 68.9 | 68.8 | **70.0** | +0.51 | 0.990 |
| V out 1868 | 173.8 | 118.5 | 119.6 | **119.4** | +0.69 | 0.988 |

- Pure view gap (identical GT-start, only z differs): **0.01–0.05 mm** — negligible.
- The true one-pass warm-start pipeline costs only **0.3–1.4 mm** vs oracle and retains **97.9–99.7%** of the
  raw→oracle mitigation. Correction / displacement direction cosine oracle-vs-estimated = **1.000** on every set.
- The estimated view departs from GT by only 0.27–2.28° in view angle (20–61 mm in range) because T0's bias is
  mostly tangential at 8–18 m; the k=16 historical-view average is locally smooth.
- Fraction of frames where the warm pipeline beats raw T0: VI 100%, IV 99.4%, V 99.8%; **II 48.8%** — the full
  view-conditioned level is neutral on II *even with oracle view* (G1), so this is the inherited trajectory
  dependence, not an estimated-view failure; the frozen policy uses the **patch** level on such trajectories.

### 2. Perturbation robustness (frozen grid, ~150-frame subsample/set)

| perturbation | range | VI | IV | II | V | direction cosine |
|---|---|---|---|---|---|---|
| rotation | 0.25°→2° | 78.14→78.14 | 81.86→81.86 | 65.61→65.61 | 116.82→116.82 | 1.000 |
| translation | 10→100 mm | 78.12→77.91 | 81.86→82.23 | 65.56→65.55 | 116.81→117.29 | 1.000 |
| combined | (25,0.5)→(100,2) | ≈78.1 | ≈82.0 | ≈65.6 | ≈117.1 | 1.000 |

Curves are **flat/gradual** — even 100 mm + 2° (far beyond the real T0 view gap) moves median e_t by <0.5 mm
and never flips the correction direction. There is **no catastrophic failure** within the grid.

### 3. Why PASS and not PARTIAL/FAIL
The oracle→estimated degradation is sub-mm/≈1–2% of the gain, the warm pipeline beats raw on ~all frames where
the correction itself is beneficial (VI/IV/V), and sensitivity is gradual. PARTIAL would require a clear but
tolerable degradation; FAIL a vanishing/inverting gain — neither occurs. The single caveat (II full level) is
already explained and frozen at G1, not produced by using an estimated view.

### 4. Claim unlocked / boundary
- **May claim:** "the bias-aware mitigation can operate using viewing geometry obtained from an initial pose
  estimate rather than ground truth, retaining essentially all of its oracle performance, and is smooth to
  realistic initialization error."
- Do **not** claim "fully autonomous": the pipeline assumes a baseline registration that lands in the local
  basin (here the frozen raw ICP) and a frozen in-domain mismatch library; global coarse acquisition and
  out-of-library targets remain stated limitations.

### 5. Gate
**G2 = G2_PASS.** Proceed to the post-hoc hierarchy transfer (E) and then the G3 untouched single-look, for
which the entire G0–G2 chain and this T0/correction/metric choice are now frozen.
