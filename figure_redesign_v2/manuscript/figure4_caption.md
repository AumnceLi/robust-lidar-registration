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
