# Figure 4 — Table 3 Verification Checks

## Summary

This document records the root cause of the V1 Figure 4(c) error, the source of the
correct Table 3 cases, and the reconciliation against raw experimental data.

---

## 1. V1 Error Root Cause

**Symptom:** V1 Figure 4(c) displayed ratio labels of **2347×, 3151×, 237×, 186×**
and used cases with RMS pairs like (51.9, 65.5) etc. These did not match the
paper's Table 3.

**Root cause:** The V1 script selected conditions from the wrong dose points and
labeled the wrong quantity. Specifically:
- It picked extreme dose magnitudes (e.g., mag=100 for D1) where the LS estimator
  had already diverged, producing astronomically large translation errors.
- It then divided two diverged values that were not the matched-RMS comparison
  intended by Table 3.
- The resulting "ratios" (2347× etc.) were artifacts of comparing two
  already-broken registrations, not the controlled matched-RMS comparison.

**Fix:** The four Table 3 cases are now taken directly from the published PDF
Table 3 (frozen experiment medians) and validated against `dose_response.csv`.

---

## 2. Correct Table 3 Cases (from PDF)

| # | Geometry | Condition A | RMS_A | e_t_A | Condition B | RMS_B | e_t_B | ratio |
|---|----------|-------------|-------|-------|-------------|-------|-------|-------|
| 1 | GA | D1 coherent displacement | 7.95 | 8.930 | D3 local mismatch | 7.70 | 0.900 | 9.9 |
| 2 | GB | D4 span growth | 4.06 | 0.058 | D3 local mismatch | 3.97 | 0.621 | 10.6 |
| 3 | GB | D4 span growth | 5.33 | 0.184 | D5 coherent tilt | 5.08 | 1.528 | 8.3 |
| 4 | GC | D3 local mismatch | 3.75 | 0.988 | D4 span growth | 3.80 | 0.116 | 8.5 |

These are defined in `configs/paths.py::TABLE3_CASES`.

---

## 3. Reconciliation Against Raw Data

**Source file:** `D:\doubao\g_chain\G_GENERALITY\results\dose_response.csv`
**Form used:** `ls` (Raw / least-squares median, 20 reps per geometry-family-dose)

### Case-by-case match (e_t medians)

| Case | Condition | dtype code | matching mag | published e_t | raw e_t_med | abs diff |
|------|-----------|------------|-------------|---------------|-------------|----------|
| 1A | GA · D1 | D1_appendage_disp | 10.0 | 8.930 | 8.9285 | 0.0015 |
| 1B | GA · D3 | D3_local_surface_off | 50.0 | 0.900 | 0.9013 | 0.0013 |
| 2A | GB · D4 | D4_appendage_scale | 0.025 | 0.058 | 0.0584 | 0.0004 |
| 2B | GB · D3 | D3_local_surface_off | 10.0 | 0.621 | 0.6206 | 0.0004 |
| 3A | GB · D4 | D4_appendage_scale | 0.050 | 0.184 | 0.1839 | 0.0001 |
| 3B | GB · D5 | D5_appendage_tilt | 0.50 | 1.528 | 1.5282 | 0.0002 |
| 4A | GC · D3 | D3_local_surface_off | 2.0 | 0.988 | 0.9885 | 0.0005 |
| 4B | GC · D4 | D4_appendage_scale | 0.100 | 0.116 | 0.1161 | 0.0001 |

**Conclusion:** All eight e_t medians match the published Table 3 values within
±0.002 mm (rounding precision). The dose magnitudes are identified unambiguously.

### Ratio check

| Case | published ratio | raw computed ratio (max/min) |
|------|-----------------|------------------------------|
| 1 | 9.9 | 9.91 |
| 2 | 10.6 | 10.71 |
| 3 | 8.3 | 8.31 |
| 4 | 8.5 | 8.52 |

All ratios agree within rounding (≤0.15).

---

## 4. RMS Data Status

**RMS values (RMS_A, RMS_B) are NOT available in the raw CSV files.**
- `dose_response.csv` contains only error medians (et_med, eR_med) by geometry,
  dtype, mag, form.
- `geometry_results.csv` contains per-rep framewise errors (et_mm, eR_deg) but
  not the matched-RMS summary.
- `generality_summary.csv` contains only self-null and max error per geometry-dtype.

**Decision:** The published RMS values from PDF Table 3 are used as-is. They are
frozen experiment condition medians and are the authoritative summary for the
matched-RMS comparison. No alternative RMS source was found in the G_GENERALITY
directory tree.

---

## 5. Figure 4(c) — V1 vs V2 Comparison

| Item | V1 (wrong) | V2 (corrected) |
|------|-----------|----------------|
| Cases | Wrong dose points at mag=100 extremes | Correct matched-RMS pairs from Table 3 |
| Ratio labels | 2347×, 3151×, 237×, 186× | 9.9×, 10.6×, 8.3×, 8.5× |
| RMS values | 51.9/65.5 etc. (wrong) | 7.95/7.70, 4.06/3.97, 5.33/5.08, 3.75/3.80 |
| Source | Misidentified conditions | PDF Table 3, validated against dose_response.csv |

---

## 6. Deliverables

- Script: `scripts/figure4.py`
- Verification script: `scripts/verify_table3.py`
- Derived data: `data/derived/figure4_matched_rms_cases.csv`,
  `data/derived/figure4_table3_verification.csv`,
  `data/derived/figure4_phase_map.csv`
- Output: `figures/main/figure4.{pdf,svg,png}` (PNG at 600 dpi)
- Caption: `manuscript/figure4_caption.md`
