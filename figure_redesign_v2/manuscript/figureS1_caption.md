Supplementary Figure S1. Diagnostics accompanying Figure 3 (p2p subset,
N = 1456 frames unless stated).

(a) Predicted versus realised translation step length on log-log axes; the
dashed diagonal is the 1:1 reference. Hollow markers denote FO (fixed-
correspondence analytic prediction, an_t_mm) and filled markers denote FD
(rematched feature-debiased prediction, fd_t_mm); point colour encodes the
trajectory as in Figure 3. FD tracks the realised step much more tightly and
never under-predicts, while FO consistently under-predicts and both methods
exhibit a few large FD outliers.

(b) ECDF of the 6x6 Hessian condition number on a log horizontal axis, plotted
separately per trajectory (VI, IV, II, III; colours shared with Figure 3).
This is the native, unscaled condition number of the 6x6 block in which
translation is measured in metres and rotation in radians (mixed m/rad
units); it is not re-scaled and should not be compared with dimensionless or
normalised condition numbers. The bulk of frames have a well-conditioned
block (median 7.5 across all frames), with trajectory II carrying the short
heavy tail out to ~84.

(c) Distribution of the switch rate, for the 66 frames in which it is defined
(VI n = 40, II n = 13, III n = 11, IV n = 2); boxplot per trajectory with
individual frames overlaid.
