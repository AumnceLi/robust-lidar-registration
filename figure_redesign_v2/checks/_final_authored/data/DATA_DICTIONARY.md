# Data dictionary — figures_final/data

All lengths are in **millimetres (mm)** unless a column name says `_m` (metres)
or `_deg`/`_de`/`eR` (degrees). "median" is always the 50th percentile; Q25/Q75
are the 25th/75th. Nothing here is back-derived from the rendered PNGs.

## derived/  (values actually plotted)

### figure2_residual_stats.npz  (Figure 2)
Two-level residual statistics on the VI (development/calibration) trajectory.
- `block_patch_med` : 6 blocks × 24 patches array of **block median patch
  residual (mm)** — first the within-scan median of per-point 3-D residual
  magnitudes, then the median across scans of that block/patch.
- per-patch range-bin arrays for patches 3/20/8: 8 fixed equal-width sensor-range
  bins (8.75–14.80 m); each holds bin median and Q25/Q75 across scans (the curve
  = median, the shaded band = IQR, never a CI, never a fit).
- `n_frames_patch3/20/8` = 501 / 501 / 484 scans contributing per patch (NOT the
  per-bin count; per-bin counts are computed in the drawing script).
- Missing (unobserved) block/patch cells are masked, never filled with 0.

### figure3_scatter_ecdf_source.csv  (Figure 3 a,b)
One row per common frame (N = 1456).
- `trajectory` VI/IV/II/III; `rms_mm` ordinary residual RMS; `rms_pa_mm`
  pose-active residual RMS (both strictly positive, no epsilon); `actual_t_mm`
  realised translation displacement (linear y).
### figure3_ecdf.csv  (Figure 3 c,d)
Step ECDF coordinates of translation **direction error (°)** for FO
(fixed-correspondence first-order) and FD (rematched finite-difference).
### figure3_anchor_summary.csv
Per-trajectory median FO/FD direction cosines and pose-active/ordinary ratio.
- NOTE: this table has **no on_bound/clip column** (only `fd_iters`); the 23
  II frames at exactly 300 mm are not asserted as safeguard trips from this
  file — see validation.md.

### figure4_matched_rms_cases.csv / figure4_table3_verification.csv (Figure 4c)
The four locked Table-3 pairs (GA D1/D3, GB D4/D3, GB D4/D5, GC D3/D4):
condition RMS, translation error, relative RMS gap (all ≤5%) and larger/smaller
error ratio 9.91/10.63/8.31/8.51 (labelled 9.9/10.6/8.3/8.5). Verified by
`verify_table3.py`.
### figure4_phase_map.csv (Figure 4d)
Controlled-mismatch samples: geometry, family D1–D5, mismatch fraction α,
translation-coherence proxy η_t, Raw LS translation error (all >0, log colour).
10 reps per cell, aggregated separately from panels a/b.

### figure5_interval_provenance.csv  (Figure 5 — review §8.3)
One row per plotted series: `panel, series, center, lower, upper,
interval_type, sampling_unit, n, n_blocks`.
- (a)(b) descriptive IQR (Q25–Q75); (c) whole-block-bootstrap 95% percentile CI;
  (d) descriptive IQR (not a CI).
### figure5_v2_bootstrap_ci.csv  (Figure 5c)
Per comparison × trajectory paired median and block-bootstrap CI (B=2000,
seed 42; whole blocks of within-frame baseline−method differences).
### figure5_v2_rotation_iqr.csv  (Figure 5d)
Per-trajectory median/Q25/Q75 of paired rotation change
(Patch+Huber − Huber, °; positive = larger rotation error).

### figure6_case_<IV278|II505>_C_matrices.npz  (Figure 6)
Frozen full SE(3) `C_raw/C_patch/C_full` and archive `et_*`/`eR_*`;
Q_method = C Q_ref (never back-derived from scalars).
### figure6_case_*_display_indices.npy
Fixed 5000-point display subset (seed 12345), identical across the three arms.
### figure6_case_*_displacement.npz
Diagnostic per-point displacement d_i = ‖C Q_ref_i − Q_ref_i‖·1000 (mm); kept for
audit, NOT used as the figure's visual encoding.

## source/  (frozen Figure-6 inputs)
`figure6_case_<tag>_scan.npz` — aligned measured scan Q_ref (the "aligned"
array) in the EPOS reference pose; not an error-free CAD/GT surface.

## Upstream, read-only (not copied; paths + SHA-256 in ../source_manifest.json)
- Fig 4: `g_chain/G_GENERALITY/results/dose_response.csv` (20 reps/geometry-dose).
- Fig 3: `revision_experiments/exp3_pose_active/pose_active_direct_framewise.csv`.
- Fig 5 V1 derived: marginal IQR, per-frame paired benefits, rotation cost.
- Fig 6 on_bound evidence: `FOLLOWUP_6_9/scripts/replay79_arms.csv`.
