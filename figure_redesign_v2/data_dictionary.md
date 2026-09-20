# Data Dictionary — V2 Figure Redesign

## Source Data (read-only, under D:\doubao\)

### model_cache.npz
| Field | Shape | Dtype | Unit | Description |
|-------|-------|-------|------|-------------|
| xyz | (67870, 3) | float32 | m | Nominal model point coordinates |
| normals | (67870, 3) | float32 | — | Surface normals |
| lab | (67870,) | int32 | — | Patch assignment (0..23), zero-indexed |

### patches.npz
| Field | Shape | Dtype | Unit | Description |
|-------|-------|-------|------|-------------|
| center | (24, 3) | float32 | m | Patch centroid |
| normal | (24, 3) | float32 | — | Patch normal |
| count | (24,) | int32 | — | Points per patch |

### VI_ONLY_PREDICTOR_FROZEN.npz
| Field | Shape | Dtype | Unit | Description |
|-------|-------|-------|------|-------------|
| Vmean | (501, 24, 3) | float32 | m | Per-frame per-patch correction vector μ_j |
| vrange | (501,) | float32 | m | Per-frame sensor range (8.7–14.8) |
| blocks | (501,) | int32 | — | Block assignment (0..5) |
| Vcnt | (501, 24) | int32 | — | Observation count per frame-patch |

SHA256: `8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe`

### replay79_arms.csv (23268 rows = 1456 frames × 7 arms + headers)
| Column | Dtype | Unit | Description |
|--------|-------|------|-------------|
| trajectory | str | — | VI/IV/II/III |
| frame_id | int | — | Frame index |
| arm | str | — | Raw/Huber/Trim/Global-Vector/Patch/Full/EstFull |
| et_mm | float | mm | Translation error |
| eR_deg | float | deg | Rotation error |
| on_bound | int | — | 1 if safeguard (0.30m/15°) triggered |

### pose_active_direct_framewise.csv (2912 rows = 1456 × p2p/p2l)
| Column | Dtype | Unit | Description |
|--------|-------|------|-------------|
| trajectory | str | — | VI/IV/II/III |
| frame_id | int | — | Frame index |
| mode | str | — | p2p (point-to-point) or p2l (point-to-line) |
| residual_rms_mm | float | mm | Ordinary residual RMS |
| pa_residual_rms_mm | float | mm | Pose-active residual RMS |
| displacement_mm | float | mm | Realized translation displacement |
| fo_dircos | float | — | Fixed-correspondence direction cosine |
| fd_dircos | float | — | Rematched finite-difference direction cosine |

### dose_response.csv
| Column | Dtype | Unit | Description |
|--------|-------|------|-------------|
| geometry | str | — | GA/GB/GC |
| dtype | str | — | D1–D5 mismatch type |
| mag | float | mm or deg | Dose magnitude |
| form | str | — | Loss form (Raw/Huber/Trim) |
| n | int | — | Repetitions per cell (20) |
| et_med | float | mm | Median translation error |
| et_lo / et_hi | float | mm | IQR bounds |
| eR_med | float | deg | Median rotation error |

### ii_failure_representative_frames.csv
| Column | Dtype | Unit | Description |
|--------|-------|------|-------------|
| trajectory | str | — | IV/II |
| frame_id | int | — | Selected frame |
| bin | str | — | median/best10/worst10 |
| effect_full_minus_patch_mm | float | mm | Full − Patch effect |
| rule | str | — | Selection rule from p4_run.py |

## Derived Data (under figure_redesign_v2/data/derived/)

### figure2_residual_stats.npz
| Field | Shape | Unit | Description |
|-------|-------|------|-------------|
| block_patch_med | (6, 24) | mm | Block×patch median residual (heatmap) |
| frame_patch_med | (501, 24) | mm | Frame×patch median residual |
| patch3_bin_stats | (8, 5) | — | bin_lo, bin_hi, n, q25, median, q75 for patch 3 |
| patch20_bin_stats | (8, 5) | — | Same for patch 20 |
| patch8_bin_stats | (8, 5) | — | Same for patch 8 |

### figure3_anchor_summary.csv
| Column | Unit | Description |
|--------|------|-------------|
| trajectory | — | VI/IV/II/III |
| n | — | Frame count |
| ratio_pa_median | — | median(RMS_PA / RMS) |
| fo_dircos_median | — | Fixed-correspondence direction cosine median |
| fd_dircos_median | — | Rematched FD direction cosine median |

### figure5_v2_bootstrap_ci.csv
| Column | Unit | Description |
|--------|------|-------------|
| comparison | — | Patch vs Raw / Patch vs Global-Vector / Patch+Huber vs Huber |
| trajectory | — | VI/IV/II/III |
| median | mm | Frame-paired median benefit |
| ci_lo / ci_hi | mm | Whole-block-bootstrap 95% CI (B=2000, seed=42) |
| n | — | Common-support frame count |

### figure5_v2_rotation_iqr.csv
| Column | Unit | Description |
|--------|------|-------------|
| trajectory | — | VI/IV/II/III |
| median | deg | Paired rotation change (Patch+Huber − Huber) |
| q25 / q75 | deg | IQR bounds |
| n | — | Frame count |

### figure4_table3_verification.csv
| Column | Unit | Description |
|--------|------|-------------|
| case | — | 1–4 |
| geometry | — | GA/GB/GC |
| family_A / family_B | — | Mismatch type (D1–D5) |
| mag_A / mag_B | mm/deg | Dose magnitude |
| et_A_pub / et_B_pub | mm | Published e_t (PDF Table 3) |
| et_A_raw / et_B_raw | mm | e_t from dose_response.csv |
| et_A_diff / et_B_diff | mm | Deviation (≤0.002) |
| ratio_pub / ratio_raw | — | Published / computed max-min ratio |
| rms_A_pub / rms_B_pub | — | Published RMS (not in raw data) |

### figure6_case_{IV278,II505}_C_matrices.npz
| Field | Shape | Unit | Description |
|-------|-------|------|-------------|
| C_Raw / C_Patch / C_Full | (4, 4) | — | SE(3) correction matrix C = T_ref · T_hat^{-1} |
| et / eR | (3,) | mm/deg | Per-arm errors matching archive |

### figure6_case_{IV278,II505}_displacement.npz
| Field | Shape | Unit | Description |
|-------|-------|------|-------------|
| Q_ref | (n, 3) | m | Reference-transformed scan points |
| Q_Raw / Q_Patch / Q_Full | (n, 3) | m | Method-transformed points (= C · Q_ref) |
| displacement_Raw/Patch/Full | (n,) | mm | Per-point reference-relative displacement (diagnostic) |

### figure6_case_{IV278,II505}_display_indices.npy
| Shape | Dtype | Description |
|-------|-------|-------------|
| (5000,) | int64 | Fixed downsampling indices (seed=12345), shared across methods |

## Manifests (under manifests/)

- **source_assets.csv**: 16 source assets with SHA256 and description
- **frame_roster.csv**: 4 trajectories with common-support/raw-pool counts, coverage, blocks, role
- **figure_manifest.csv**: 9 figures with size, scripts, data sources, description
- **case_selection.csv**: Fig6 IV278/II505 provenance (median_neighborhood, effect, on_bound)

## Statistical Conventions

| Quantity | Definition | Used in |
|----------|-----------|---------|
| Marginal median + IQR | Median and 25–75 percentile across frames (descriptive) | Fig5(a)(b), Fig2 curves, S2 |
| Frame-paired median | Median of per-frame difference (same frame, two methods) | Fig5(c)(d), S3 |
| Whole-block-bootstrap 95% CI | Resample blocks (VI6/IV4/II9/III8), B=2000, seed=42 | Fig5(c) |
| Block×patch median | Within-frame median → within-block median across scans | Fig2 heatmap |
| ECDF | Empirical cumulative distribution, 0 before first sample, 1 after last | Fig3(c)(d), S1(b) |

**IQR is not a confidence interval.** Bootstrap CI is only used in Fig5(c).
