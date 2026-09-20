# Manuscript Changes for V2 Figure Redesign

## Section 5.3 — Controlled mismatch experiment (Figure 4)
- Figure 4(c) now uses the four correct Table 3 matched-RMS cases (GA·D1/D3 ratio 9.9; GB·D4/D3 ratio 10.6; GB·D4/D5 ratio 8.3; GC·D3/D4 ratio 8.5). The previous V1 version incorrectly used extreme dose points (mag=100 where LS had diverged), producing spurious ratios (2347×, 3151×, 237×, 186×). These labels have been removed.
- The GA/GB/GC schematic inset that occluded the D1/D5 dose-response curves has been removed.
- Table 3 has been moved to Supplementary Material (Table S1); in-text references now point to Figure 4(c) and Table S1.

## Section 5.4 — Real EPOS-LiDAR registration (Figure 6)
- Figure 6 is re-rendered using fixed 2D orthographic projection (elev 25°, azim −60°) with dual-color overlay (reference scan in grey, method result in method color), replacing the previous mplot3d 3D coordinate box and displacement heatmap.
- Each case band (IV frame 278, II frame 505) contains: case ID bar → panorama row (three methods, same camera/range) → independent detail strip (same ROI, below panorama, not overlaid) → numeric row (e_t, e_R per method).
- Frame selection: both frames are median-neighborhood representative frames from `ii_failure_representative_frames.csv` (p4_run.py rule: rank 0.45–0.55, effect closest to bin median). IV278: effect=+38.82 mm (Full improves over Patch). II505: effect=−24.60 mm (Full degrades vs Patch, on_bound=1). The previous "Full best / Full worse*" labels have been removed; ordering is conveyed by numeric values and explained in caption.
- Reproduction gate: all six arms (Raw/Patch/Full × IV278/II505) reproduce the archived `replay79_arms.csv` values with max |Δe_t| = 1.42×10⁻¹⁴ mm.

## Section 5.2 — Local mechanism (Figure 3)
- Log scale is now applied to the residual RMS x-axis (not the displacement y-axis). The y-axis is linear 0–400 mm (true max displacement 378.6 mm), so the main point cloud is no longer compressed.
- The unexplained vertical dashed line at ~95° has been removed.
- FD direction error tail (>90°, 26 frames, max 151.0°) is preserved.

## Coverage statement (Figure 5)
- Coverage fractions are stated in the caption only, not on the figure: VI 501/501=100.0% (development/calibration); IV 156/2428=6.4% (external transfer); II 428/1253=34.2% (difficult external transfer); III 371/1302=28.5% (secondary). Subplot n= labels remain common-support sample sizes.
