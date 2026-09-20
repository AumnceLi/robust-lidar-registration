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
