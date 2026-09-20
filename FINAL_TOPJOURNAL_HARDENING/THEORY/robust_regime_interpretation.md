# Part B (cont.): Robust Regime Interpretation — Matching Theory to G_GENERALITY

*THEORY shard. This document matches the two-regime theory in
`robust_loss_derivation.md` to the controlled G_GENERALITY synthetic
experiments. Every number is computed by `theory_empirics.py` from
`g_chain/G_GENERALITY/results/geometry_results.csv` (9120 rows). No number is
estimated.*

---

## 1. The two regimes, restated

- **Regime A (gross / localised outlier):** few points with $|\delta_i|\gg c$.
  Robust loss truncates / downweights them; $g_\rho\to 0$; bias removed.
- **Regime B (coherent moderate mismatch):** many spatially-correlated
  same-direction residuals at $|\delta_i|\lesssim c$. $\psi(\delta_i)\approx
  \delta_i$; $g_\rho\approx g_{\mathrm{LS}}$; bias persists (and can grow).

---

## 2. Real EPOS (VI) interpretation

The real spacecraft LiDAR mismatch is predominantly **Regime B**: R4 structured
clusters occupy 71.2% of points (`IDENTIFIABILITY_AUDIT.md` §2), with a
signed inward mean of −39 mm and p95 ≈ 190 mm. These are not isolated gross
outliers; they are spatially coherent, physically motivated residual fields
covering the majority of the cloud. The robust-loss theory therefore predicts:

> **Robust weighting attenuates but does not eliminate the bias.**

This is consistent with the VI result that the GT-started local optimum
displaces 160 mm raw (`LOCAL_OPTIMUM_BIAS.md` §1) and 58–64 mm even after
maximal global nuisance removal — a residual, directionally coherent bias that
is not a few isolated outliers.

---

## 3. Synthetic D1 / D5 (coherent appendage mismatch)

D1 = appendage displacement (rigid translation of a sub-assembly); D5 =
appendage tilt. Both produce a spatially localised but **rigid, coherent**
residual patch whose residuals are moderate in amplitude (mm–cm) and therefore
land in the Huber inlier / transition band.

### D1 dose-response (LS, p2p)

| Dose [mm] | ete median [mm] |
|---:|---:|
| 0 | 0.02 |
| 2 | 0.91 |
| 5 | 2.30 |
| 10 | 8.88 |
| 25 | 17.57 |
| 50 | **39.16** |
| 100 | 80.73 |

*Source: `geometry_results.csv`, D1_appendage_disp, form=ls, kind=p2p, median
over 60 repetitions per dose.*

### D1 at 50 mm dose — robust vs LS (p2p)

| Loss | ete median [mm] |
|---|---:|
| LS | 39.16 |
| Huber | 42.75 |
| Trim | 50.68 |

*Source: same file, mag=50.0. Values are TWO-STAGE cross-geometry medians
(median of the GA/GB/GC per-geometry medians: LS 39.163 / Huber 42.753 / Trim 50.684),
matching the project-canonical dose_response.csv aggregation and the brief's 39.2 / 42.8 / 50.7 mm.*

The theoretical statement for D1/D5 is therefore:

> **Robust weighting does not eliminate the bias and can occasionally increase
> the resulting displacement.**

The Huber ete (42.8 mm) is 9% larger than LS (39.2 mm); Trim (50.7 mm) is 29%
larger. This is the Regime B prediction: the coherent appendage shift is not a
gross outlier, robustification does not see it as such, and the Hessian
de-weighting lengthens the step.

**Negative result preserved:** we do not claim robust loss "fixes" D1. The
numbers 39.2 / 42.8 / 50.7 are reported as-is, including the increase.

---

## 4. Synthetic D3 (weakly pose-coupled local offset)

D3 = local surface offset at a single patch. At 100 mm dose:

| Loss | ete median [mm] |
|---|---:|
| LS | 13.85 |
| Huber | 0.53 |
| Trim | 0.04 |

*Source: `geometry_results.csv`, D3_local_surface_off, mag=100, p2p.*

This is the cleanest Regime-B-but-weak-projection case: D3 has the same nominal
dose as D1 but the local offset is nearly tangential to the surface, so its
pose-active projection $J^\top W\delta$ is small (Part A3). Robustification
then easily removes the residual pose bias. This demonstrates that the
*combination* of (i) coherent residuals **and** (ii) alignment with a pose mode
is what defeats robust loss — not residual amplitude alone.

---

## 5. Synthetic D2 (gross absent component — Regime A)

D2 = entire component removed. At dose $f=1.0$:

| Loss | ete median [mm] | on-bound fraction |
|---|---:|---:|
| LS | 300.00 (basin clip) | 0.667 |
| Huber | 11.60 | 0.333 |
| Trim | 132.75 | 0.433 |

*Source: `geometry_results.csv`, D2_missing_component, mag=1.0, p2p.*

LS is dominated by the absent component's gross outliers and hits the 300 mm
basin clip. Huber successfully truncates the gross outlier block and recovers
to 11.6 mm. Trim's performance is mixed (132.7 mm, 43% on-bound) — hard
trimming can discard too much of the inlier cloud when the absent component is
large. This is Regime A: robust loss **does** address the bias.

---

## 6. Summary table: regime → prediction → observed

| Class | Regime | Prediction | Observed (p2p) |
|---|---|---|---|
| D1 appendage disp | B (coherent moderate) | Bias persists; robust may increase it | LS 39.2, Huber 42.8, Trim 50.7 mm @50 mm dose |
| D5 appendage tilt | B (coherent moderate) | Bias persists | LS 0.13 mm median over doses (small effect) |
| D3 local surface off | B but weak projection | Small pose bias; robust removes residual | LS 13.9, Huber 0.53, Trim 0.04 mm @100 mm dose |
| D2 missing component | A (gross localised) | Robust removes bias | LS 300 mm clip, Huber 11.6 mm @f=1.0 |
| D4 appendage scale | near-nuisance | Weak / absorbed by global correction | LS 0.065 mm median over doses |
| Real EPOS (VI) | B (predominantly) | Attenuates but does not eliminate | 160 mm raw, 58–64 mm combined |

*All G_GENERALITY numbers: `geometry_results.csv`, medians computed by
`theory_empirics.py`. Real EPOS numbers: `LOCAL_OPTIMUM_BIAS.md` §1.*

---

## 7. Figure

`figures/robust_dose_response.png` plots D1 ete vs dose for LS / Huber / Trim,
showing that the three curves are close at every dose and that Huber/Trim are
not below LS at 50 mm. This is the visual evidence for "robust weighting does
not eliminate the bias" in Regime B.
