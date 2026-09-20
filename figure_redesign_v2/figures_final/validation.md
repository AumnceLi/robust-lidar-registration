# Validation record — round 6 (Ast review 2026-09-14)

Legend: **[D]** verified against source data / code (deterministic), **[V]**
visual check at the final 180 mm width (colour + greyscale). No data value, case
selection or statistic was changed to fix a visual issue.

## A. Deterministic checks [D] — all pass
Full pipeline `scripts/build_v2_all.py` exits 0 (`checks/build_v2_all_round6.log`).
1. `verify_table3.py` — **ALL PASS, 4/4 pairs within 5% RMS**; relative RMS gaps
   3.14 / 2.22 / 4.69 / 1.32 %; independently recomputed error ratios
   9.91 / 10.63 / 8.31 / 8.51 (labelled 9.9/10.6/8.3/8.5). No pair re-selected.
2. `verify_all_v2.py` — **26/26 passed, failures = 0, ALL CHECKS PASSED**;
   range-bin edges match V1.
3. `reproduce_figure6_gate.py` — max |Δe_t| = 1.42e-14 mm, max |Δe_R| = 1.78e-15°;
   all arms match archive (<1e-9); display subsets IV278 9908→5000 and
   II505 10515→5000 (seed 12345). `verify_figure6.py` — every SE(3) detR = 1,
   metrics equal archive, displacement npz == C@Q_ref (maxdiff 0), fixed ortho
   camera elev 25 / azim −60; the three arms of each case share identical x/ylim.
4. Figure 5 anchor self-checks — every locked median/benefit/rotation value
   matches (Raw/Patch/Full translation medians, paired benefits, rotation cost
   0.421/0.052/0.498/0.720°); II "Patch vs Global-Vector" 95% CI = [−8.49,
   +18.02] mm (crosses zero → not claimed significant).
5. Figure 5 interval provenance generated from the actual arrays
   (`data/derived/figure5_interval_provenance.csv`): (a)(b) descriptive IQR,
   (c) whole-block-bootstrap 95% CI, (d) descriptive IQR.
6. Figure 4 (d) runtime assertion: all controlled Raw e_t > 0, so the log
   colourbar needs no zero substitution; symlog zero-dose is a real baseline
   tick (linthresh = half the smallest non-zero dose), no epsilon.
7. Figure 3: 1456 common frames (VI 501 / IV 156 / II 428 / III 371, asserted);
   both residual classes strictly positive (min 49.1 / 11.7 mm); FD has 26
   frames >90° (max 151.0°), FO max 89.1°; 23 II frames sit at exactly 300 mm
   (26 ≥295 mm).
8. Figure 6 on_bound: II505 **Full on_bound = 1 matches `replay79_arms.csv`
   (arch=1)**, iters = 9; IV278 on_bound = 0, iters = 37. Safeguard is the
   0.30 m / 15° per-iteration accumulated-step bound (a solver-path protection,
   not a convergence/registration basin).
9. Export: every PDF embeds subset fonts (FontFile present: Arial MT/Bold/Italic
   + DejaVu Sans for math italics); every SVG keeps editable `<text>` elements
   (svg.fonttype = none). PNG rendered at 600 dpi from source (not up-sampled).

## B. Visual checks at 180 mm [V] — pass (`checks/_printproof/`)
- Figure 1: single green connector lands on the ICP node edge (no double arrow
  head); Full short box sits under Correction field with one dashed arrow to
  its edge; ICP correspondence/rigid-update schematic occupies >half the node;
  node titles inside, row labels and bottom fixed-correspondence note legible;
  μ subscripts mathematical; no text overlap or overflow.
- Figure 2: heatmap is exactly 6×24 with boundary hairlines only (centre grid
  that split each block removed); colorbar label and shared y-axis renamed;
  panel titles carry n = 501/501/484; colorbar clears the curve titles by one
  text line.
- Figure 3: shared log-x (10^1–10^4) and identical linear y in (a)(b);
  Trajectory legend with n and a second encoding (marker + ECDF line style);
  true step ECDFs; FO/FD panel titles; panel numbers outside the data area.
- Figure 4: each solver has ONE cross-geometry median main line + ONE same-hue
  min–max range band (the nine faint per-geometry lines removed; full
  per-geometry curves stay in the supplement); four panel titles; D1–D5 legend
  on its own row with ≥2 mm clearance from "Appendage tilt (°)" and panel (d).
- Figure 5: method legend restored; (d) retitled "Rotation change:
  Patch+Huber − Huber", orange up-triangle matching (c); positive-direction
  notes under (c)/(d); panel numbers outside; no large empty region.
- Figure 6: main | ROI side-by-side per arm; horizontal case titles; uniform
  "e_t = … mm  e_R = …°"; ROI reference = open grey ring / estimate = solid
  dot (same rule for all three arms); reference, estimate and local offset are
  distinguishable at column width without merging into solid blocks; ROI box and
  "ROI" tag establish main↔zoom correspondence; scale bars sit in clear strips.
- Greyscale: series remain separable through markers/line styles/open-vs-solid.

## C. Deliberately retained evidence (not swapped for visual success)
- Figure 6 keeps II frame 505 where Full degrades (152.5 mm/14.8°) alongside the
  IV 278 improvement, to state the applicability boundary.
- Figure 4 keeps the four published Table-3 pairs only; Figure 3 keeps the
  300 mm row and FD >90° tail (no point dropped).

## D. Known limits / items needing the manuscript or upstream side
1. This archive holds the plotted/derived data and frozen Figure-6 scans; the
   full raw experiment corpora remain upstream (paths + SHA-256 in
   `source_manifest.json → external_inputs`, all resolved on this machine).
2. Figure 3's framewise table has no on_bound flag; per-frame safeguard status
   cannot be asserted from that plot. The caption states this explicitly; the
   only per-frame on_bound evidence here is Figure 6 II505 (run-log verified).
3. Coverage discrepancy resolved in favour of source: the review text listed
   "IV 156/242, 86.4%" but the project authority `configs/paths.py
   COMMON_SUPPORT_COUNTS` and the data give IV = 156/2428 = 6.4% (consistent with
   II 428/1253 and III 371/1302); the figure/caption use 156/2428 (6.4%).
4. The previous manuscript Figure 3 (E,F) and Figure 5 (C,D) panels no longer
   exist; their diagnostics move to the supplement. In-text and supplementary
   cross-references must be updated on the manuscript side (image files alone
   cannot do this).
5. Font family is Arial where available with DejaVu Sans fallback for math; the
   exact embedded subset names are listed in A9. Final journal-template width,
   if not 180 mm, requires one re-render and a repeat of section B.
