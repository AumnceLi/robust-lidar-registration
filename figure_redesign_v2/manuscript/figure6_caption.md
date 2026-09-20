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
