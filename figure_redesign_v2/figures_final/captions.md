# Figure captions (final, round 6 / Ast review 2026-09-14)

Figure 1. Mechanism overview of the patch-wise geometric correction and registration pipeline. (Top row) Calibration: starting from the nominal model (light grey) and a set of calibrated VI scans (dark grey), a fixed 24-patch correction field μ_j is estimated once and frozen. The selected patches and illustrative correction vectors are shown (not the complete quantitative 24-patch field). The resulting corrected geometry m_i^corr is used as the reference for downstream registration, with residual arrows shown on a small edge segment only. (Bottom row) Registration: a query scan (dark grey) is aligned to the corrected geometry (light grey) via ICP with rematching, illustrated as an abstract correspondence-update schematic (paired points with small arrows and an iteration symbol). The algorithm directly outputs the estimated pose T̂ = (R̂, t̂). The reference-relative evaluation (e_t, e_R) depends on the known reference pose T_ref and is shown as a downstream annotation. The corrected geometry feeds into the ICP step (green arrow); the query scan also feeds into ICP. Bottom strip: the PA residual δ_PA = P_{J,W}δ, the GN correction Δξ_corr ≈ −H_GN† JᵀW(δ − A_πμ), under fixed correspondences and local approximation. The gradient term JᵀWδ appears inside the GN correction. Point-cloud thumbnails in calibration nodes are rendered from real target geometry; the ICP node is an abstract schematic. Two correction fields are distinguished at the calibration node: the fixed, view-independent field μ_j used by Patch, and the reference-view-conditioned field μ_j(z) used by Full. The Full field is formed by view-neighbour weighting with equal-scan aggregation; it is a variant of the correction field used to *build* the corrected geometry before registration, not a processing step applied after the estimated pose. The orange dashed annotation names this field, and its arrow points into the Correction-field node, because Full is one way that field is constructed; no Full arrow appears after the estimated pose. The separate method Estimated Full is a two-stage procedure and is described here rather than drawn: stage 1 initialises from the *reference pose* (it does not assume a pre-acquired coarse pose), estimates the pose and queries the reference-view neighbourhood to obtain μ_j(z), from which the corrected geometry is built; stage 2 then runs the same ICP solve. Seed, normal weight, and the non-semantic clustering parameters are moved to this caption and are not drawn inside the panels.

---

Figure 2. Residual structure of the VI trajectory (the development/calibration
trajectory). The 24 patches are fixed zero-based geometric partitions, not
semantic parts. (a) Fixed nominal partition: the nominal model (light grey) with three representative patches highlighted — patch 3 (teal), patch 20 (blue), and patch 8 (warm orange) — shown in a fixed oblique orthogonal view. Short leader lines identify the patch indices. (b) VI residual structure heatmap: median residual magnitude (mm) for each block (rows 0–5) and patch (columns 0–23, Patch ID). Statistics are computed as the within-frame median of per-point 3D Euclidean residual magnitudes (‖aligned − model[nnidx]‖), then aggregated as the median across scans within each block. Missing (unobserved) patch-block cells are shown in light grey (not filled with zero). The colormap is monotonic Blues and the heatmap grid is drawn only at cell
boundaries (no centre gridlines). The colorbar (below panel b) is labelled
"Block median patch residual (mm)"; the shared vertical axis of (c–e) is
"Patch-median residual (mm)". Both are two-level statistics as defined above. (c–e) Residual magnitude vs. sensor range for patches 3, 20, and 8, binned into 8 equal-width view-distance bins (8.75–14.80 m). Each observation is one frame's patch-median residual. Solid lines show the cross-frame median; the light shaded bands show the interquartile range (IQR, 25th–75th percentile) — not a confidence interval and not an error band. No error bars and no fitted/trend lines are drawn; every curve is an observed cross-frame median rather than a model fit. Frame counts: patch 3, n = 501; patch 20, n = 501; patch 8, n = 484. The flat profile of patch 3 (27–32 mm across all range bins) is a genuine feature of that patch's geometry, not a plotting artifact.

---

Figure 3. Local mechanism evidence. All four panels use the point-to-point
(p2p) subset of the framewise pose-active experiment, N = 1456 common frames,
with per-trajectory counts VI n = 501 (development/calibration), IV n = 156
(external transfer), II n = 428 (difficult external transfer), III n = 371
(secondary). Trajectory is encoded by colour AND marker/line style (VI blue
circle/solid, IV orange square/dashed, II teal triangle/dash-dot, III purple
diamond/dotted) and is shown once above the figure under the title "Trajectory".

(a) Ordinary (uncorrected) point-to-point residual RMS on a log horizontal axis
versus the realised translation displacement on a linear vertical axis.
(b) Pose-active residual RMS on a log horizontal axis versus the same realised
displacement. Panels (a) and (b) deliberately share ONE log-x range and tick set
(10^1–10^4 mm) and one linear-y range, so the two residual scales can be
compared directly. Logging the residual axis keeps the dense low-residual bulk
visible instead of compressing it under a few large outliers; no frame was
dropped, no jitter was added, and no epsilon was inserted — both residual
classes are strictly positive (ordinary minimum 49.1 mm, pose-active minimum
11.7 mm), so the log axis is legal. A smaller pose-active RMS is not, by itself,
evidence of a more accurate pose: the pose update is further acted on by
H_GN^dagger and depends on local observability, parameter scaling and
correspondence switching, so the local claim is about direction consistency,
not about the horizontal shrinkage of these clouds.

A horizontal row of 23 trajectory-II points sits at exactly 300 mm in both (a)
and (b) (26 II frames lie at or above 295 mm). This value coincides with the
0.30 m accumulated-step safeguard on the solver path and these frames carry the
worst-conditioned blocks (highest condition numbers; shown at alpha = 0.45). We
do NOT assert per-frame bound-clamping from this plot alone: this framewise
table contains no on_bound/clip flag (only an iteration count), and a realised
final displacement is not the same quantity as a per-iteration accumulated
step. Per-frame safeguard trips are established from solver run logs where
available (e.g. the on_bound = 1 flag for Figure 6, II frame 505).

(c, d) Empirical CDF (drawn as true post-step functions) of the translation
direction error, defined as arccos(cosine) between predicted and realised
translation directions: (c) FO, the fixed-correspondence one-step analytic
(first-order) gradient direction; (d) FD, the rematched finite-difference
direction. A predicted step of zero magnitude has no defined direction and is
excluded rather than counted as 0°; here all 1456 frames are valid for both FO
and FD. Both panels share 0–160° so the FD tail beyond 90° is retained: FD
contains 26 frames above 90° (maximum 151.0°) whereas FO never exceeds 89.1°;
each ECDF starts at 0 before its first sample and holds at 1 to the common
right boundary of 160°. Direction-consistency improvement is read from these
distributions and the associated statistics, not from the (a)/(b) scatter
shape. Median FO/FD direction cosines per trajectory (VI, IV, II, III) are
0.942/0.959, 0.946/0.973, 0.771/0.990 and 0.809/0.995; the median pose-active /
ordinary RMS ratio is 0.359, 0.392, 0.299 and 0.346. The earlier amplitude /
condition-number diagnostic panels (E,F) of the previous layout are moved to the
supplement; in-text and supplementary figure references are updated to the
present (a–d) numbering.

---

## Figure 4. Controlled mismatch experiment.

**(a) D1: coherent appendage displacement.** Translation error vs. displacement
dose for the three solvers Raw (LS, hollow circles, solid line), Huber (filled
squares, dashed) and Trim (filled triangles, solid). For *each* solver one main
line connects, at every dose, the **median of that solver's three per-geometry
condition medians** (GA/GB/GC), and a single same-hue shaded band spans the
**min–max of those three condition medians**. The band is an inter-geometry
range, not a confidence interval and not the min–max of the 20 raw repeats;
each geometry–dose cell itself summarises n = 20 independent repeats. The full
per-geometry curves are not drawn as separate lines here (they are retained in
the supplementary figure) so that the three solvers stay distinguishable; no
geometry is dropped to favour a result. Both axes use a legitimate symmetric-log
scale: the zero dose is a real baseline tick (no epsilon substitution), and the
linear region spans ±1 mm on the dose axis (half the smallest non-zero dose of
2 mm) and ±0.01 mm on the error axis.

**(b) D5: coherent appendage tilt.** Rotation error vs. tilt dose, identical
line/band conventions. The linear region around zero spans ±0.05° on the dose
axis (half the smallest non-zero dose of 0.1°); the error-axis linear threshold
is half the smallest positive Raw cross-geometry median.

**(c) Matched residual RMS.** Each row pairs two conditions whose surface
residual RMS match within 5% but whose translation errors differ markedly (the
within-5% RMS match is verified automatically, see below). Filled blue =
Condition A, open orange = Condition B, grey segment = the paired connection.
The ratio label is the larger translation error divided by the smaller (A or B,
whichever is larger), showing that matched residual RMS does not imply matched
registration error. Rows: GA·D1/D3 (9.9×), GB·D4/D3 (10.6×), GB·D4/D5 (8.3×),
GC·D3/D4 (8.5×). "A/B" denotes the first/second mismatch family of each row — it
does **not** mean left/right on the axis, nor that A is always better. The
match is checked by `scripts/verify_table3.py`: the relative RMS gaps
|RMS_A−RMS_B|/max are 3.14%, 2.22%, 4.69% and 1.32% (all within 5%), and the
independently recomputed larger/smaller error ratios are 9.91×, 10.63×, 8.31×,
8.51× (labelled 9.9/10.6/8.3/8.5). These four rows are exactly the published
Table 3 pairs, read from the frozen source; no pair was re-selected to enlarge a
ratio. Translation errors e_t are cross-checked against `dose_response.csv`
(ls medians, |diff| ≤ 0.002 mm); surface RMS values are the published Table 3
condition medians (the raw CSV stores error medians but no RMS field). Records:
`data/derived/figure4_table3_verification.csv`,
`checks/figure4_table3_5pct_check.log`. The complete match set comprises 60
directed / 36 unique undirected pairs (not four); full RMS values and the
remaining pairs are in Supplementary Table S3.

**(d) Controlled mismatch patterns.** α–η_t map of the controlled samples; each
marker is one geometry–family combination at a representative dose (10
replicates per cell, aggregated separately from panels a/b). Marker shape
encodes family D1–D5 (dedicated legend row); colour encodes the Raw LS
translation error on a logarithmic colorbar (cividis). η_t is a descriptive
*translation coherence proxy*, not a loss and not a proven phase boundary; the
absence of a clean separating surface in α–η_t space shows that no single
threshold on either quantity predicts failure. All controlled-sample Raw e_t
values are strictly positive (asserted at runtime), so the log colorbar needs no
zero substitution; should a true zero ever occur it is to be marked with a
distinct neutral symbol rather than mapped to half the minimum.

Inter-geometric shaded bands in (a,b) are ranges (min–max across GA/GB/GC), not
confidence intervals; n = 20 repeats per geometry–dose, and 10 repeats per
phase-map cell in (d).

---

Figure 5. Effect of estimation method on trajectory error, paired translation benefit, and rotation cost.

(a) Translation error (mm) and (b) rotation error (°) by method and trajectory. Markers show marginal median; whiskers show interquartile range (IQR, descriptive). Methods: Raw (gray circle), Huber (blue square), Global-Vector (purple triangle), Patch (green diamond), Full (orange inverted triangle). Global-Vector rotation error is identical to Raw (it does not modify rotation estimation), so it is not plotted in (b). (c) Frame-paired translation benefit (positive = error reduction) for three comparisons: Patch vs Raw (green circle), Patch vs Global-Vector (purple square), and Patch+Huber vs Huber (orange triangle). Centers show frame-paired median; horizontal segments show whole-block-bootstrap 95% CI (B=2000, archived seed=42; block counts per trajectory: VI=6, IV=4, II=9, III=8). The Patch vs Global-Vector CI on trajectory II crosses zero [−8.49, +18.02] mm. (d) Paired rotation change (Patch+Huber − Huber) per trajectory, shown as frame-paired median with descriptive IQR. Positive values indicate increased rotation error when Patch is added on top of Huber. Dashed vertical lines at zero in (c) and (d) mark no-change.

Statistics hierarchy: (a)(b) marginal median + IQR (descriptive); (c) frame-paired median + whole-block-bootstrap 95% CI (whole blocks of within-frame baseline−method differences resampled together, never assembled from two marginal CIs); (d) frame-paired median + IQR (descriptive, not CI, so no significance is read from whether it crosses zero). The center/lower/upper, interval type, sampling unit, n and block count of every panel are generated from the actual arrays and archived in `data/derived/figure5_interval_provenance.csv`. Panel (d) is explicitly "Rotation change: Patch+Huber − Huber" and uses the same orange up-triangle as that comparison in (c); positive values mean a larger rotation error after adding Patch, whereas positive values in (c) mean improvement.

Trajectories: VI (501/501 frames, 100.0%, development/calibration); IV (156/2428, 6.4%, external transfer); II (428/1253, 34.2%, difficult external transfer); III (371/1302, 28.5%, secondary). All statistics are frame-level on common-support frames only.

---

# Figure 6 — real EPOS-LiDAR registration, dual-color overlay (V2)

**Caption (for manuscript).**

We show two fixed single-scan registrations of the EPOS-LiDAR pipeline,
rendered from the real experimental point clouds (not synthetic, not
hand-placed, not a controlled simulation). Each horizontal case block is one
scan; the three columns are the three frozen arms — **Raw** (uncorrected
nominal target), **Patch** (view-independent patch-level geometry correction)
and **Full** (reference-view-conditioned correction) — all run from the same
GT-localized start, with the same solve-path step safeguard (a per-iteration
bound of 30 cm / 15° on the *accumulated* translation/rotation step; this is a
protection threshold on the optimisation path — a *safeguard*, not a proven
convergence/registration basin), the same Huber-robust point-to-point ICP, and
the same input points, point indices, point count and display subsample (5000
points, fixed seed 12345). The first case shows improvement; the second is
retained deliberately to show a Full degradation and thereby state the method's
applicability boundary — it is not replaced by an all-success case.

**Case selection (fixed display cases).** The two frames are the *median-bin*
representative frames from
`revision_experiments/06_II_failure_cases/ii_failure_representative_frames.csv`,
selected by the frozen `p4_run.py` rule (within the rank 0.45–0.55 band, the
frame whose effect `Full − Patch` is closest to the bin median). They are
**not** best/worst frames; absent an independent representativeness proof we
refer to them only as fixed display cases.
* **IV · frame 278** (external-transfer trajectory IV): effect = +38.82 mm
  (Full improves over Patch); e_t/e_R = Raw 151.7 mm/4.5°, Patch 108.8/4.1°,
  Full 70.0/1.7°; the solver stays inside the safeguard (`on_bound = 0`,
  iters = 37).
* **II · frame 505** (difficult external-transfer trajectory II): effect =
  −24.60 mm (Full degrades relative to Patch); e_t/e_R = Raw 141.4 mm/12.7°,
  Patch 127.9/12.8°, Full 152.5/14.8°. The solver trips the step safeguard at
  iteration 9 (`on_bound = 1`): the accumulated step would cross the 30 cm/15°
  bound, so that step is clipped and ICP terminates early. `on_bound` is **not**
  inferred from the displayed 14.8° — it is reproduced by re-running the frozen
  solver in `scripts/reproduce_figure6_gate.py` and matches the archived
  `replay79_arms.csv` log exactly (e_t/e_R within 1e-9, same flag); it is an
  optimisation outcome, not a protocol error.

**Reference coordinate and two-layer overlay.** The common reference is the
aligned source cloud `Q_ref = T_ref^{−1} P` (the measured scan in the EPOS
reference pose); it is **not** an error-free CAD/GT surface, and all quoted
errors are defined *relative to this EPOS reference*. For every arm we read one
full SE(3) rigid transform `C = [R t; 0 1]` from the frozen archive and plot
`Q_method = T̂^{−1} P = C Q_ref` over `Q_ref` (poses are never back-derived from
the two scalars e_t/e_R). The legend reads "Reference-aligned scan" and
"Estimated alignment: column colour": neutral grey is the reference layer and
the estimate uses the colour of its column (Raw `#3F4952`, Patch `#2C8C7E`, Full
`#C97A40`); the column title names the arm so each result colour has one meaning.
On the panoramas the reference is drawn as solid medium-grey points (`#8D979F`,
alpha 0.72) beneath the estimate (alpha 0.85). In the ROI zoom only, the same
role encoding is strengthened **identically for all three arms** by drawing the
reference as open grey rings and the estimate as solid dots (reference
alpha 0.85, estimate alpha 0.90), so the two layers and their local offset read
clearly even where hues are close; no arm receives a favourable-only
enhancement. The reference-relative per-point displacement
`d_i = ‖C Q_ref_i − Q_ref_i‖·1000 [mm]` is a distinct diagnostic (closest-point
residual and global translation error are different quantities) and is retained
only as a side artefact (`data/derived/figure6_case_*_displacement.npz`); it is
not the visual encoding, and no per-point error colorbar is shown. The 2-D
projection is for display only; e_t/e_R are computed in 3-D from the solved C.

**Projection, shared camera and side-by-side zoom.** Within a case the three
arms share one fixed 2-D orthographic projection (elevation 25°, azimuth −60°)
and one shared display window (union of Q_ref and the three Q_method clouds
with equal margins, asserted identical across arms); no arm is re-centred
separately and the display indices, seed, axis limits and ROI are fixed across
arms. Each arm cell places the main panorama (left) and its ROI magnification
(right) **side by side**; a single dashed rectangle on the panorama marks the
selection and a matching "ROI" tag on the zoom establishes the correspondence
(leader lines do not cross the cloud). The ROI mask is the same fixed index set
for every arm. Final print point sizes are ≈0.36/0.39 pt (reference/estimate)
on panoramas and ≈0.55/0.58 pt on the ROI (matplotlib `s = diameter²`); they are
starting values tuned at the final column width so both layers and their offset
stay visible without merging into solid blocks. Scale bars are computed from
the projected metric scale (20 cm per panorama, 10 cm per ROI) and sit in a
clear lower strip, never on the points; if an ROI cannot contain 10 cm its bar
length follows the true scale. The numeric line under each column reports
`e_t = … mm   e_R = …°` at uniform precision.

**Descriptive, not confirmatory.** The two cases are illustrative fixed
snapshots that show what solved poses look like on real data (one improvement,
one Full degradation). They are not a quantitative comparison — that is carried
by the paired block-bootstrap statistics in Figure 5 and the paper text.
