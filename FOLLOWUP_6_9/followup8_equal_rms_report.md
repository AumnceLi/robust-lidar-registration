# Follow-up Item 8 — Equal-RMS / matched-severity mechanism test

**Status: COMPLETE on frozen synthetic D1–D5 × GA/GB/GC (plus the unstructured CTRL), no tuning.**
Generated 2026-09-11.

## Data and pre-fixed rules

- **Primary severity/bias numbers are the stored frozen results**
  `g_chain/G_GENERALITY/results/geometry_results.csv` (point-to-plane, LS; 20 vantage/noise
  realizations per condition): residual_RMS = √J0 (mm), translation_bias = et (mm),
  rotation_bias = eR (deg); condition value = median over the 20 reps.
- Mechanism descriptors use frozen definitions: affected fraction **α** and resultant coherences
  **η_t, η_R** exactly as in the frozen `OPTIONAL_PHASE_MAP`; **‖g_t‖, ‖g_r‖, ‖P_JW δ‖** use the
  Item-5 analytic factor-1 normal-equation convention (gradient ×2 to match the frozen finite-
  difference convention; ‖P_JW δ‖ = √(gᵀH⁻¹g)).
- **Matching rule fixed before looking at outcomes:** within the *same* geometry, pair each
  condition with its single nearest cross-family RMS neighbour; keep the pair iff
  |RMS_A−RMS_B|/max ≤ **5% (primary)**. A **10%** match is reported only as a sensitivity check and
  was never used to chase significance. Cross-family pairs (D1–D2, D1–D4, D2–D4, D3–D5, D3–D4, …)
  isolate *spatial organization* while holding geometry and residual magnitude.

### Fidelity validation of the re-derived mechanism descriptors
The original synthetic generator seeds its RNG with Python `hash()`, whose salt is not stored, so an
exact per-realization byte-match is not recoverable. Mechanism descriptors were therefore
re-derived with the **unchanged frozen generator/solver under a declared fixed PYTHONHASHSEED=0** and
validated against frozen artifacts:

| check | result |
|---|---|
| α vs frozen phase map (270 matched cells) | max abs diff **9.0×10⁻¹⁷ (exact)** |
| η_t / η_R vs phase map | median abs diff 0.0014 / 0.0013 |
| re-derived vs **stored** translation bias | median rel diff 1.7% (90th pct 9.0%) |
| re-derived vs **stored** RMS | median rel diff 0.06% |

Severity and pose bias in every matched pair are the **stored** (authoritative) values; re-derived
quantities are used only for the within-recomputation gradient/projection trend. All requested
columns are populated — **no NEW_EXPERIMENT_REQUIRED** for Item 8.

## Headline result — fixed RMS does not fix pose bias

The pre-fixed 5% rule yields **60 cross-family matched pairs** (GA 19, GB 18, GC 23); their median
RMS difference is only **0.07 mm**, yet:

| set | N | median bias ratio (larger/smaller) | fraction >2× | fraction >5× |
|---|---:|---:|---:|---:|
| all matched pairs | 60 | **5.96×** | **0.77** | 0.53 |
| structured–structured only | 44 | 3.39× | 0.68 | 0.36 |

Named family contrasts (5%): D1–D2 n=6 median 26.6×; D1–D3 n=2 6.4×; **D3–D4 n=7 4.6×**;
D1–D4 n=6 2.25×; D3–D5 n=3 1.64×. Against the unstructured noise control, the structured side
carries the larger bias in 75% of 16 matches (median ratio ≈58×) — i.e. equal-RMS *random noise*
produces far less pose bias than organized residuals.

### Worked examples (stored condition medians, p2p LS)

| geometry | family A (RMS, t-bias) | family B (RMS, t-bias) | RMS rel-diff | bias ratio |
|---|---|---|---:|---:|
| GA | D1 disp (7.95 mm, 8.93 mm) | D3 local (7.70 mm, 0.90 mm) | 3.2% | **9.9×** |
| GB | D4 scale (4.06 mm, 0.058 mm) | D3 local (3.97 mm, 0.621 mm) | 2.2% | **10.6×** |
| GB | D4 scale (5.33 mm, 0.184 mm) | D5 tilt (5.08 mm, 1.528 mm) | 4.7% | 8.3× |
| GC | D3 local (3.75 mm, 0.988 mm) | D4 scale (3.80 mm, 0.116 mm) | 1.2% | 8.5× |

### The D4 check (large residual, low pose-active effect)
D4 (appendage scaling = low-projection nuisance) participates in 25 matched pairs and is the
**lower-bias side in 84%** of them (median counterpart/D4 ratio 2.29×; up to 10.6×). At matched
residual magnitude a coherent/extensive (D1) or localized (D3) mismatch produces several-fold more
translation bias than D4 scaling — direct evidence that a large residual RMS with weak pose-active
projection is comparatively benign.

## Matched-pair aggregate (Step 3) — bias tracks gradient *organization*, not RMS

Across the 60 primary pairs (10% sensitivity in parentheses):

| relationship | Spearman ρ | p |
|---|---:|---:|
| ‖Δ translation bias‖ vs ‖Δ ‖g_t‖‖ | **0.907 (0.907)** | 1.9×10⁻²³ (3.1×10⁻³⁰) |
| ‖Δ translation bias‖ vs ‖Δ ‖P_JW δ‖‖ | 0.739 (0.745) | 1.5×10⁻¹¹ |
| ‖Δ translation bias‖ vs ‖Δ RMS‖ | 0.771 (0.708) | — |

The side with the larger pose bias is also the side with the larger translational gradient ‖g_t‖ in
**88% (91% at 10%)** of pairs, and with the larger Gauss–Newton projection ‖P_JW δ‖ in 82%. Because
RMS is matched by construction, the residual correlation of bias with RMS is a by-product of
organization; the gradient/projection quantities — which encode *spatial organization* — separate
the two sides more cleanly. Given the designed (non-random) synthetic grid and modest per-family
pair counts, these ρ/p are reported as descriptive trend evidence, not as population inference.

## Answer to the required question

> **"With residual magnitude approximately fixed, does changing the spatial organization of the
> mismatch still change pose bias?" — YES.**
> Within a 5% RMS band, 77% of cross-organization pairs differ in translation bias by >2× (median
> ≈6×, up to ≈10×); the low-projection family D4 is the lower-bias member in 84% of its matches; and
> the side with the larger bias is identified by its organized pose-active gradient (88% agreement,
> ρ(bias, ‖g_t‖)=0.91) rather than by residual size. Residual magnitude alone is therefore not
> predictive of pose bias; spatial organization (coherence / projection onto pose) is. This is a
> core piece of mechanistic evidence for the paper's novelty claim.

## Caveats (stated, not hidden)
- Matching is on condition medians over 20 realizations; some named family pairs have small n
  (D1–D3 n=2, D3–D5 n=3) and are shown for completeness, not as standalone proof.
- D2 (missing component) is non-monotone and catastrophic only at extreme removal; its few matches
  (n=6) show very large ratios and are retained without trimming.
- Mechanism columns are a fixed-seed re-derivation (validated above); RMS and bias are stored frozen
  values. No threshold was widened after seeing results (5% primary; 10% only as sensitivity, with
  the same conclusion: ρ=0.907).

## Files / provenance
`followup8_condition_summary.csv` (per geometry×family×dose: RMS, ‖g_t‖, ‖g_r‖, ‖P_JW δ‖,
translation/rotation bias, α, η_t, η_R, stored + re-derived columns),
`followup8_equal_rms_pairs.csv` (60 primary pairs with all deltas),
`scripts/item8_pairs_10pct.csv` (78 sensitivity pairs), `scripts/item8_validation.csv`.
