# E2 — VI-Internal Held-Out Validation (Six-Fold Leave-One-Block-Out) (FINAL ROUND)

**Question (pre-registered).** *Within VI, does the spatial correction survive held-out calibration
blocks, or is the apparent VI gain driven by using the same scans to construct the field?* The Patch
field is normally fit on all 501 VI scans, so VI itself is not independent evidence. This experiment
constructs, for every VI scan, a field that was **not allowed to see that scan's block**, and scores
the scan out-of-fold.

## 1. Design (isolates field-history leakage, not clustering variability)

- **Frozen blocks.** The six frozen contiguous view-travel blocks carried in the predictor
  (`vi_blocks`): [0,70), [70,140), [140,219), [219,315), [315,418), [418,501) = 70/70/79/96/103/83.
- **Fold j.** Train = the five other blocks; test = block j. The **24-patch partition `plab` is
  frozen** (MiniBatchKMeans k=24, normal weight 0.30, seed 42) and is **not** re-clustered per fold.
  Only the per-patch discrepancy mean `mu_j` is rebuilt from the training scans using the *identical*
  point-weighted rule (`g_common.hierarchy_library`). Each of the 501 scans is scored exactly once
  under the fold that holds its block → a complete 501-frame out-of-fold (OOF) result.
- **Leakage assertions (hard, every fold):** `train ∩ test = ∅`; `train ∪ test = all 501`; and
  `mu_j` equals an independent point-weighted mean computed over train rows only. Per-fold
  train/scan id lists and field hashes are in `e2_lobo_fold_provenance.json`.
- **Methods.** Raw, PatchOOF (required); Huber, PatchHuberOOF (cheap, included for symmetry);
  PatchFullFit = the deployed all-VI field, kept as the distinct in-sample comparator.
- **Fidelity.** The benchmark's Raw reproduces frozen `g1_oracle_vi` M0 and PatchFullFit reproduces
  M4 to **2.8e-14 mm**; i.e. the OOF result uses the unchanged frozen solver.
- **Inference.** Paired benefit = Raw − Patch (positive = Patch better), paired by scan; block
  bootstrap over the six blocks and frame moving-block bootstrap (L=5/10/20), B=2000, seed=42;
  frozen block sign-flip test. The decision rule was fixed before seeing the result.

## 2. Per-fold table (translation median, mm)

| Fold (block) | n | Raw | Patch OOF | paired benefit | rot. change ° | improved frac. | OOF safeguard |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 [0,70)   | 70  | 151.2 | 112.0 | **+40.6** | −0.55 | 1.00 | 0 |
| 1 [70,140) | 70  | 151.7 | 111.0 | **+38.7** | −0.81 | 1.00 | 0 |
| 2 [140,219)| 79  | 165.5 | 125.0 | **+41.9** | −0.38 | 1.00 | 0 |
| 3 [219,315)| 96  | 168.4 | 123.6 | **+45.3** | +0.09 | 1.00 | 0 |
| 4 [315,418)| 103 | 164.2 | 117.9 | **+44.5** | +0.09 | 1.00 | 0 |
| 5 [418,501)| 83  | 159.3 | 114.7 | **+44.1** | −0.39 | 1.00 | 0 |

Every held-out block improves, and **every single one of the 501 scans improves** (improved fraction
= 1.00); no held-out registration trips the safeguard.

## 3. Pooled 501-frame out-of-fold result vs in-sample field

| Quantity (VI, median mm) | Value |
|---|---:|
| Raw | 161.41 |
| **Patch OOF (held-out field)** | **117.46** |
| Patch FullFit (all-VI, in-sample) | 116.82 |
| **OOF paired benefit (Raw − PatchOOF)** | **+43.07** |
| In-sample paired benefit (Raw − FullFit) | +43.51 |
| In-sample optimism (benefit gap) | **0.44 mm (≈1.0% of the benefit)** |
| OOF-vs-FullFit error gap | 0.69 mm |
| Positive held-out blocks | **6/6** |
| Block-of-blocks bootstrap 95% CI on benefit | **[39.6, 44.9]** (excludes 0) |
| Frame moving-block 95% CI (L=20) | [41.2, 44.7] (excludes 0) |
| Block sign-flip p | 0.0005 |
| Rotation change (Raw − Patch), median | −0.28° (Patch modestly better) |

The robust variant tells the same story: Huber 148.9 mm → PatchHuber-OOF 103.6 mm (benefit +44.7 mm).

## 4. Interpretation and verdict

- The held-out Patch field retains a **+43.1 mm** median benefit — 99.0% of the in-sample +43.5 mm.
  Withholding an entire view-travel block from field construction costs only **0.44 mm of benefit /
  0.69 mm of final error**. The six block effects are tightly clustered (+38.7 to +45.3 mm) and all
  positive, and both block- and frame-level bootstrap intervals exclude zero.
- **Flag: `OOF_POSITIVE_RETAINED`** — **no `VI_OVERFIT_WARNING`**. The development-set gain is not an
  in-sample calibration artifact in any meaningful amount.
- Permitted wording for the paper: *"VI leave-one-block-out calibration retains a positive
  Patch-over-Raw effect of essentially the same magnitude (median +43 mm, 6/6 blocks positive,
  bootstrap CI excludes zero), reducing concern that the development gain is solely an in-sample
  calibration artifact."* We do **not** claim this "proves no overfitting"; it only shows the field
  generalizes across VI view-travel blocks. External transfer still rests on IV/II (and secondary III).

## 5. Artifacts (hashes in `e2_provenance.json`)

`e2_vi_lobo_framewise.csv` (2505 rows), `e2_vi_lobo_oof_framewise.csv` (501-scan wide table),
`e2_vi_lobo_fold_table.csv`, `e2_vi_lobo_summary.json`, `e2_lobo_fold_provenance.json` (per-fold
train/test ids + field hashes + leakage assertions). Runners: `e2_run_lobo.py`, `e2_analyze.py`,
`e2_provenance.py`.
