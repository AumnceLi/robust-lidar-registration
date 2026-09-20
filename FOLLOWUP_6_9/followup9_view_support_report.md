# Follow-up Item 9 — View-support / Full-transfer diagnostic

**Status: COMPLETE from the frozen VI library + frozen view descriptors (no retraining).**
Generated 2026-09-11. Scope: VI/IV/II/III = in-support primary frames; **V = all 1868 frames**
(permanently out-of-support supportive set). Blocks are joined from frozen artifacts
(master frame for VI/IV/II/III; frozen g0_frame_v temporal blocks for V).

## How each descriptor was obtained
`mu_for_view` was replayed **deterministically from the frozen library** (Vmean/Vcnt/vrange/uview,
k=16 adaptive kernel, τ_support=0.25, all-library fallback) and instrumented to expose, per frame:
nearest-view distance; k=16 neighbor distances (min/median/max=d_k); kernel ESS=(Σw)²/Σw²; valid
patch-neighbor observations; patch coverage = (# patches with ≥1 valid neighbour)/24; #fallback
patches; mean/median ‖μ_j‖; nearest_d/τ_support. The replay's nearest-view distance and predicted
step reproduce the frozen g1/ext_predict outputs **exactly (0.0)** on every frame
(`scripts/verify79_full.csv`), so the instrumentation does not alter any frozen quantity.
Translation direction cosine = cosine between the predicted view-conditioned first translation step
and the realized Raw-LS translation (the Item-3 definition). "Full−Patch benefit" = Patch_err −
Full_err (>0 ⇒ Full better). All associations below are **association / consistency statements, not
causal claims**.

## Per-trajectory picture (medians)

| traj | n (K blocks) | nearest/τ | ESS | coverage | fallback rate | dir. cosine | Patch err | Full err | Full−Patch | frac Full beats Patch |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VI | 501 (6) | 0.000 | 15.57 | 1.00 | 0.27 | 0.935 | 116.8 | 76.9 | **+39.7** | **1.00** |
| IV | 156 (4) | 0.490 | 15.94 | 0.958 | 0.51 | 0.841 | 126.3 | 82.9 | **+38.9** | **1.00** |
| II | 428 (9) | 0.465 | 15.79 | 1.00 | 0.26 | 0.788 | 41.8 | 68.9 | **−24.6** | **0.22** |
| III | 371 (8) | 0.570 | 15.81 | 1.00 | 0.23 | 0.859 | 41.3 | 51.2 | **−20.0** | **0.35** |
| V | 1868 (38) | **4.982** | 15.99 | 1.00 | 0.00 | **0.902** | 134.6 | 118.5 | +19.4 | 0.75 |

Stratified Spearman ρ of Full−Patch benefit vs each descriptor:

| analysis | VI | IV | II | III | V |
|---|---:|---:|---:|---:|---:|
| A: vs nearest-view distance | 0.03 | **−0.39** | +0.16 | −0.07 | −0.08 |
| B: vs kernel ESS | −0.09 | −0.47 | +0.14 | +0.06 | +0.26 |
| C: vs patch coverage | −0.11 | +0.11 | +0.32 | +0.44 | const (1.0) |
| D: vs direction cosine | 0.06 | +0.35 | +0.56 | +0.19 | +0.60 |

Support-region medians (within-trajectory tertiles of nearest/τ; Full−Patch / frac-beats-Patch):

| traj | near | mid | far |
|---|---|---|---|
| IV | +41.5 / 1.00 (0.03–0.33) | +38.1 / 1.00 | +35.4 / 1.00 (0.65–1.00) |
| II | **−27.7 / 0.32** (0.08–0.38) | −26.0 / 0.12 | −15.5 / 0.22 (0.59–1.00) |
| III | −8.4 / 0.32 (0.08–0.46) | −20.5 / 0.37 | −30.8 / 0.36 (0.76–0.99) |
| V | +26.8 / 0.83 (1.10–3.82) | +9.1 / 0.64 | +19.3 / 0.79 (5.61–7.07) |

(VI is degenerate: it is the library itself, nearest/τ≈0 for every frame.)

## Answers to the four required questions

### 1. Why can V's high direction cosine NOT prove Full correction reliable?
V's median direction cosine is **0.902 — the second highest of all five trajectories (above IV 0.841
and II 0.788)** — yet V sits at nearest/τ ≈ **4.98**, an order of magnitude beyond every in-support
trajectory (all <0.6), and Full beats Patch in only **75%** of V frames (vs 100% on VI/IV). The
direction cosine measures sign alignment of the *local predicted first step* with the realized
correction; it does **not** certify that the borrowed view-conditioned field is valid at that
viewpoint. Within V the cosine is associated with benefit (ρ=0.60), but its *level* stays high even
for the 25% of frames where Full is worse than Patch. A high cosine is therefore necessary-ish but
not sufficient evidence of compensation reliability, and it is especially misleading far outside the
library support. Reliability must be judged against Patch (the view-independent floor) and against
support geometry, not from the cosine alone.

### 2. Is II's Full negative transfer associated with support distance / ESS / coverage?
**No — those descriptors cannot separate II (fails) from IV (works).** II and IV are essentially
identical on every view-support metric: nearest/τ 0.465 vs 0.490, ESS 15.79 vs 15.94, coverage 1.00
vs 0.958, and II even has *fewer* fallback patches (0.26 vs 0.51). Yet Full is +38.9 mm and beats
Patch 100% on IV but −24.6 mm and beats Patch only 22% on II. Kernel ESS is ≈15.6–16.0 for **all**
trajectories (the 16-neighbor kernel saturates) and IV has the highest fallback rate while being the
best external transfer, so neither ESS nor fallback count predicts failure. Within II the association
with proximity is, if anything, slightly *adverse* (A ρ=+0.16; the geometrically **nearest** bin is
the most negative, −27.7 mm), with a weak positive coverage association (ρ=0.32) that cannot gate
because coverage is saturated at 1.0. This pattern is **consistent with a content mismatch** — the
VI-specific structured field being borrowed does not match II's discrepancy organization even at
geometrically close views — rather than with insufficient view coverage. This is an association, not
a causal proof.

### 3. Why is Patch more stable in the poor-view-support regime?
Patch uses the **view-independent pooled μ_patch**; no nearest-view distance, ESS, coverage or
fallback quantity enters its correction, so it has no negative-transfer channel from a distant or
content-mismatched view match. Where Full degrades, Patch holds the floor: II 41.8 vs Full 68.9,
III 41.3 vs Full 51.2; in far-support V, Patch 134.6 is the stable reference and Full improves on it
only 75% of the time. Patch is therefore the robust default whenever view support is distant or
structurally inconsistent; Full is an *add-on* whose marginal benefit can be negative.

### 4. In which support regions does view conditioning add value?
- **Library self (VI):** +39.7 mm, beats Patch 100%.
- **Geometrically near AND structurally consistent (IV):** +38.9 mm, 100%, and within IV the gain is
  ordered by proximity (near +41.5 → far +35.4; A ρ=−0.39).
- **III (partial):** benefit is least negative near support (−8.4) and most negative far out
  (−30.8) — proximity helps but never crosses to a net gain.
- **Far outside support (V):** modest, non-monotone +19.4 mm overall (near +26.8/83%, mid +9.1/64%,
  far +19.3/79%).
- **II: net negative at every support distance** (−27.7/−26.0/−15.5).

The extra return of view conditioning thus appears in the *near-support, structurally-consistent*
regime and in the library itself. Geometric proximity alone is **not** sufficient (II is as near as
IV but fails), and the gain is non-monotone and partial far outside support (V).

## Synthesis
View-support geometry (distance, ESS, coverage, fallback) explains *within-trajectory* gradation on
IV/III/V but does **not** explain the cross-trajectory II failure, because II is geometrically as
well supported as IV. The Full transfer boundary is therefore set by **both** view proximity **and**
structural-content compatibility with the VI library; Patch, being view-independent, is the stable
estimator when either is in doubt; and a high V-style direction cosine must not be read as evidence
that Full compensation is reliable.

## Files / provenance
`followup9_view_support_frame.csv` (per-frame descriptors + errors + cosine, with
trajectory/order/scan/block provenance), `..._block.csv`, `..._summary.csv` (trajectory table,
stratified correlations A–D, support tertiles). Raw replay `scripts/replay79_support.csv`; exact
frozen-reproduction gate `scripts/verify79_full.csv`.
