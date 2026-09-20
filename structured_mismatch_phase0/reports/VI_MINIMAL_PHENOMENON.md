# VI MINIMAL PHENOMENON REPORT — Structured Model Mismatch on EPOS-Lid Trajectory VI

Phase-0 VI-only identifiability audit. All numbers `[computed]` by the scripts in `scripts/` on the 501 VI scans unless tagged otherwise. Baseline = frozen FPFH + RANSAC + point-to-point ICP (parameters below). No learned methods, no estimated-pose residuals, no new downloads.

---

## 0. Download / compute ledger

- Reused local assets only: `epos_dataset_vi.zip` (33.9 MB; 501 `.3d` + 501 `.pose`), `epos_target_model.3d` (67 870 pts), README. **New network downloads this round: 0 bytes** (pip wheels for scipy/pandas/sklearn/matplotlib are tooling, not dataset). IV/V/full/SpaceSense/GPU: not touched.
- Environment note: open3d has **no wheel for the installed Python 3.14** (verified against both configured mirror and pypi.org). FPFH (Rusu 2009), 3-point RANSAC and point-to-point ICP were therefore re-implemented in numpy/scipy (`s0_common.py`), algorithm semantics and the task's frozen parameters preserved. The implementation was validated: on a rigidly rotated/translated copy of the target cloud, feature matches are 94 % consistent at 5 cm and RANSAC recovers pose with 0.0° attitude / exact translation error — i.e. failures on real scans are data properties, not implementation bugs.

## 1. VI data overview (n = 501)

| quantity | mean | std | median | min | max |
|---|---|---|---|---|---|
| range ‖t‖ [m] | 12.191 | 2.066 | 12.095 | 8.747 | 14.802 |
| points/scan | 10 032 | 609 | 10 048 | 8 486 | 11 969 |
| dt [s] | 0.988 | 0.165 | 0.963 | 0.708 | 1.260 |

Duration 494.08 s; GT angular rate 7.94 °/s mean (5.40–11.00), confirming the ≈ 8 °/s fast-tumble contract. Range profile 14.79 → 12.09 → 8.75 m verified at scans 0/250/500.

## 2. GT-aligned residual statistics

Per-scan unsigned nearest-model residual (all 501 scans):
- median residual: mean **64.1 mm** (IQR 59.0–69.0, range 48.1–84.5); per-scan p95: mean **189.3 mm** (136.6–252.6).
- Global pool (508 754 pts, every 10th scan): p25 27.0 / **p50 64.8** / p90 154.1 / p95 195.2 / p99 278.9 mm.
- **85.0 % of points exceed the R1 sampling bound (16.2 mm = 2·d_model_nn, d_model_nn = 8.11 mm)**; >0.5 m excess returns are rare: per-scan excess fraction mean 0.36 % (max 0.64 %).
- Signed residual along model normals: global mean **−39.4 mm**, median −29.6 mm (systematic *inward* offset); −28.9 mm at 8–11 m vs −44.6 mm at 11–13.5 m, Pearson r(signed, range) = −0.597.
- missing_proxy (GT-visible model surface lacking a scan point within 50 mm): mean 0.601.

## 3. R1–R4 classification (operational criteria in IDENTIFIABILITY_AUDIT.md §2)

Mean scan-point fractions across 501 scans: **R1 = 15.2 %**, **R2 backface/occlusion = 13.3 %**, **R3 FOV = 0.000 (empty on VI)**, **R4 structured candidate = 71.2 %**, isolated large-noise = 0.24 %. Model-side: 50.4 % back-facing, 0 % FOV-truncated on average. Time series in `fig5_classification.png`.

Separability: R4 cleanly separated from R1 (4× bound gap) and R2 (GT visibility; 13.3 % only); R3 untestable because empty; physical causes *within* R4 not separable with VI assets. No existence-level STOP_IDENTIFIABILITY (audit §2.2).

## 4. Target-frame spatial structure and frozen-patch persistence

24 frozen patches (k-means on xyz+0.3·normal, seed 42). Cross-scan patch-median profile spans **29.0–106.9 mm (3.69× spread, CV 0.36)**; worst patch #12, best #3 (`fig1`, `fig1b`). Per-scan agreement of the patch vector with the cross-scan mean profile (Spearman "spatial profile consistency", SPS): mean **0.369**, range −0.056–0.699.

## 5. Two-null spatial-repeatability tests (N_perm = 100 each; p = (1+#{null≥real})/101)

`results/null_tests.csv`; `fig2_null_persistence.png`. Headline values:

| metric | comparison | REAL | Null A mean (z) | Null B mean (z) | p (both) |
|---|---|---|---|---|---|
| cross-scan patch-rank Spearman | lag 1 | **0.929** | 0.002 (**z=81.7**) | 0.209 (**z=47.6**) | 0.0099 |
| cross-scan patch-rank Spearman | lag 5 | 0.535 | 0.002 (z=49.7) | 0.204 (z=21.0) | 0.0099 |
| cross-scan patch-rank Spearman | lag 10 | 0.079 | 0.001 (z=6.5) | 0.202 (z=−6.8) | 0.0099 / 1.0 |
| cross-scan patch-rank Spearman | lag 50 | 0.387 | 0.000 (z=30.5) | 0.198 (z=11.3) | 0.0099 |
| patch-median temporal autocorr | lag 1 | 0.883 | 0.451 (z=51.7) | 0.064 (z=47.7) | 0.0099 |
| patch-rank Spearman | **similar aspect <30°** (480 pairs) | **0.832** | 0.001 (z=46.1) | 0.200 (z=23.6) | 0.0099 |
| patch-rank Spearman | **different aspect >90°** (480 pairs) | **−0.112** | 0.001 (z=−6.9) | 0.206 (z=−12.5) | 1.0 / 1.0 |

Interpretation: the same surface patches are persistently bad across nearby times **and similar viewing aspects**, massively above both nulls (Null A destroys within-scan spatial assignment; Null B preserves range but destroys aspect/temporal order). Persistence collapses at lag 10 (~10 s ≈ 80° of tumble) and under >90° aspect change — the pattern is **view-geometry-dependent**, physically consistent with local surface/reflectance-driven mismatch rather than a global artefact. Null B's 0.20 baseline shows range alone induces weak patch-rank stability; real similar-aspect persistence is 4× that.

## 6. Confounding control (range / point count / FOV)

`results/confound_control.csv`.
- FOV truncation is constant zero (§3) and drops out.
- Per-scan Pearson r with range: median residual 0.199, p95 residual **0.621**, r4 fraction 0.402, SPS −0.414, missing −0.480.
- Per-scan OLS R² (range + point count): median residual 0.183, p95 0.413, r4 fraction 0.164, SPS 0.173, excess 0.068.
- **Decisive patch-level test** (10 429 scan×patch cells, support ≥20): confound-only model R² = **0.0127**; adding the 24 frozen-patch fixed effects R² = 0.1439; **partial R² of patch identity = 0.133, bootstrap 95 % CI [0.124, 0.148]**. Range/point-count/FOV explain ~1 % of patch-level residual variation; surface location explains an additional 13.3 % that confounds cannot.

## 7. Frozen baseline endpoints (FPFH + RANSAC + ICP)

Frozen parameters (untuned for every scan): voxel 0.05 m; FPFH radius 0.15 m; RANSAC dist 0.10 m, max_iter 4·10⁶, max_validation 500, confidence 0.999; ICP point-to-point 30 iters, dist 0.10 m. Converged := RANSAC fitness >0.3 **and** ICP fitness >0.5. GT used only to score.
**Sampling (declared):** every 5th scan → n = **101** stratified uniformly across range/aspect (residual and null analyses above use all 501). Mean runtime 0.86 s/scan.

- **Convergence: 0/101 (0 %)**. Max RANSAC fitness = 0.0024 — global FPFH registration essentially never finds a consistent hypothesis on VI. Root cause verified, not guessed: under GT, only 1.2 % of unique FPFH nearest matches are geometrically consistent within 0.1 m (0.5 % within 5 cm); the target is smooth and 120°-symmetric with cm-scale real-vs-CAD deviation, so features are non-discriminative at the frozen scale. The same pipeline is 94 % self-consistent on a transformed copy of the model (§0).
- ICP from the failed global init lands in local minima: ICP fitness >0.5 in 36/101; symmetry-equivalent k = 0/1/2 chosen 32/30/39 times (uniform across the three X-symmetry copies).
- Translation error: mean **0.770 m**, median 0.708, min 0.104, q95 2.063; **0/101 < 0.10 m**. Sym-aware attitude error: mean **65.3°**, median 62.5°, q25 18.6°, **20/101 < 10°**.
- Paper comparison: the EPOS-Lid paper is listed as "in preparation" in the README `[verified-file]`; it publishes no numerical baseline table to compare against `[paper-claim: unavailable]`. Qualitatively, total failure of feature-global initialisation at 9–15 m on a smooth symmetric target is consistent with the dataset's stated motivation (global init is the hard regime). **This baseline is deliberately weak; that is the measured deployment gap.**

## 8. Endpoint–mismatch association (`endpoint_association.csv`)

Standardised OLS on n = 101; mismatch block = excess fraction + r4 structured fraction + SPS; base = range + point count.

| endpoint | base R² | full R² | **block partial R² (95 % boot CI)** | strongest mismatch coef (95 % CI) |
|---|---|---|---|---|
| translation error [m] | 0.0145 | 0.0571 | **0.0433 [0.0097, 0.1697]** | r4 frac β=+0.126 [−0.017, +0.269], p=0.083 |
| attitude error [°] | 0.0322 | 0.0610 | **0.0297 [0.0064, 0.1593]** | SPS β=+6.96° [−2.75, +16.68], p=0.158 |

No individual mismatch coefficient has a 95 % CI excluding zero; excess-fraction coefficients are slightly negative (excess>0.5 m is near-zero on VI, median 0.36 %, a weak metric here).
Robustness on the ICP-locked subset (ICP fitness >0.5, n = 36, `endpoint_association_robust.csv`): mismatch partial R² = **0.072 [0.013, 0.343]** (translation; range alone R²=0.576) and **0.112 [0.039, 0.426]** (attitude) — larger, but a small post-hoc subset.

## 9. Bias vs variance (`bias_variance.csv`, `fig4_bias_vectors.png`)

Groups split at the per-scan mismatch median; translation error vectors expressed in the target frame; Hotelling T² for the 3-D mean vector.

| group | n | mean ‖err‖ [m] | bias-vector norm [m] | Hotelling p | rot-axis concentration |
|---|---|---|---|---|---|
| ALL | 101 | 0.770 | **0.275** | <1e-4 | 0.456 |
| HIGH (excess>med) | 50 | 0.730 | 0.284 | 0.0028 | 0.432 |
| LOW (excess≤med) | 51 | 0.810 | 0.273 | 0.0006 | 0.481 |
| HIGH half1 (scan≤250) | 34 | 0.777 | 0.359 | 0.0028 | 0.392 |
| HIGH half2 (scan>250) | 16 | 0.629 | 0.202 | 0.180 | 0.533 |
| ROBUST HIGH (r4>med) | 50 | 0.863 | **0.399** | 0.0001 | 0.429 |
| ROBUST LOW (r4≤med) | 51 | 0.679 | 0.155 | 0.0117 | 0.562 |

- A **non-zero mean error vector exists** (baseline-wide, mostly +x_target: 0.274 m x-component; Hotelling p < 1e-3 in both high and low groups) and rotation-error axes cluster (mean resultant 0.46; half1/half2 axis cosine **0.949**).
- But under the primary excess-fraction split the bias is **not mismatch-specific**: HIGH 0.284 m ≈ LOW 0.273 m, and HIGH-group half1/half2 translation-bias cosine = **0.527 < 0.70** repeatability bar. Under the r4-fraction split HIGH carries 2.6× the bias norm of LOW (0.399 vs 0.155 m) — suggestive but metric-dependent and without a stable direction.
- Verdict: the frozen baseline exhibits systematic bias (variance is not the whole story), yet the evidence that **structured mismatch drives a repeatable directional bias** is inconsistent across the two mismatch definitions → does not clear Level D.

## 10. K1–K4 gate decisions

| gate | criterion | measured result | decision |
|---|---|---|---|
| **K1** structure vs two nulls, meaningful effect | patch persistence > Null A **and** Null B | lag-1 rank Spearman 0.929 vs 0.002/0.209, z = 81.7/47.6; similar-aspect 0.832 (z 46.1/23.6); all p = 0.0099; different-aspect collapses to −0.112 (view-dependent, as physically expected) | **PASS** |
| **K2** not fully explained by range/point count/FOV | residual structure survives confound control | confound R² = 0.013; patch fixed-effects partial R² = 0.133, 95 % CI [0.124, 0.148]; FOV identically 0 | **PASS** (effect modest but CI excludes 0) |
| **K3** independent endpoint explanatory power | mismatch block partial R² significant **and** coefficient CIs exclude 0 | full n=101: partial R² 0.043/0.030 with bootstrap CIs just above 0, but **every individual coefficient CI contains 0**; supportive only in post-hoc ICP-locked subset (0.072/0.112, n=36); baseline converges 0/101 so endpoints are dominated by global-registration failure | **FAIL (pre-registered criterion)** — marginal signal, masked by a baseline that never initialises |
| **K4** repeatable directional bias, not only variance | significant vector mean, direction repeats halves, mismatch-specific | baseline-wide bias significant (p<1e-3) but HIGH≈LOW (0.284 vs 0.273 m); half-cosine 0.527 <0.70; r4 split gives 2.6× amplification but no stable direction | **FAIL** |

### STOP decision (VI-first discipline)

**STOP after K3.** K1 and K2 establish that a non-random, target-frame-stable, view-dependent structured residual field exists on VI and is not a sampling/occlusion/FOV/range artefact — the *minimal phenomenon is real*. But the chain from that field to downstream pose endpoints **does not close on VI with the frozen baseline**: K3 fails its pre-registered criterion (no mismatch coefficient with CI excluding 0 on the full sample), K4 fails. Per discipline this must **not** be rescued with new methods, tuning, or IV/V data inside this phase.

### What would be required to re-open (design input for a later phase, not executed)
1. A baseline that actually converges in this regime (e.g. tracking init from the previous scan — but that changes the question from global init to tracking), or a stratified sample large enough that the ICP-locked partial-R² result can be confirmed on the full sample rather than n=36.
2. Cross-trajectory replication of the **frozen 24-patch profile** (IV/V) to test whether patch #12-class anomalies are target-intrinsic (persist) rather than VI-instance-specific.
3. Channels that separate physical causes inside R4 (intensity/ring) — currently forbidden; cause-level claims remain out of reach.

---

### Deliverables index
- Scripts: `scripts/s0_common.py, s1_residuals.py, s3_patches.py, s4_null_tests.py, s5_confound.py, s6_baseline.py, s7_endpoint_bias.py, s8_figures.py, s9_summary.py`
- Tables: `results/residual_per_scan.csv` (501 rows), `results/patch_persistence.csv` (12 024), `results/null_tests.csv`, `results/baseline_endpoints.csv` (101), `results/bias_variance.csv`, plus `patch_definition.csv`, `confound_control.csv`, `endpoint_association*.csv`, `summary.json`.
- Figures: `results/figures/fig1_residual_map.png`, `fig1b_patch_profile.png`, `fig2_null_persistence.png`, `fig3_error_vs_mismatch.png`, `fig4_bias_vectors.png`, `fig5_classification.png`.
