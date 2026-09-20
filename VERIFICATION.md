# Verification guide

This document lists the exact commands used to verify the curated bundle and the key results you
should see. **Level A requires no dataset download** (it uses the committed frozen result tables
and small artifacts). **Level B** additionally re-runs the per-scan registration after downloading
the public datasets (see [`data/README.md`](data/README.md)).

## Level A — statistics, decisions, figures (no download)

```bash
# 0) integrity (optional but recommended first)
python verify_checksums.py

# 1) every Python file compiles
python -m compileall -q .

# 2) frozen numerical core + frozen assets load (predictor SHA-256 asserted)
python - <<'PY'
import os, sys
sys.path.insert(0, os.path.join("structured_mismatch_phase0","scripts"))
sys.path.insert(0, os.path.join("g_chain","common"))
import g_common as G
fz = G.load_frozen()
print("model", fz["model"].shape, "patches", fz["plab"].shape, "Vmean", fz["Vmean"].shape)
PY

# 3) G3 confirmatory decision  ->  verdict = CONFIRMED
python g_chain/G3_FINAL_CONFIRMATION/scripts/g3_decide.py

# 4) G0/G1/G2 statistics, hierarchy and generality
python g_chain/G0_ROBUST_FALSIFICATION/scripts/g0_stats.py
python g_chain/G1_MITIGATION/scripts/g1_stats.py
python g_chain/G2_ESTIMATED_VIEW/scripts/g2_stats.py
python g_chain/HIERARCHY_TRANSFER/scripts/hierarchy_transfer.py
python g_chain/G_GENERALITY/scripts/g_generality_stats.py

# 5) final-three aggregate analyses
python final_three_experiments/01_coarse_initialization/e1_combine_analyze.py
python final_three_experiments/02_vi_leave_block_out/e2_analyze.py
python final_three_experiments/03_runtime_memory/e3_analyze.py

# 6) final figures: offline DRAW + all numerical/render gates (uses committed
#    frozen intermediates in figure_redesign_v2/data and figures_final)
python figure_redesign_v2/scripts/draw_figure1.py
python figure_redesign_v2/scripts/draw_figure2.py
python figure_redesign_v2/scripts/figure3.py
python figure_redesign_v2/scripts/figure4.py
python figure_redesign_v2/scripts/make_figure5.py
python figure_redesign_v2/scripts/plot_figure6.py
python figure_redesign_v2/scripts/figureS1.py
python figure_redesign_v2/scripts/make_figureS2.py
python figure_redesign_v2/scripts/make_figureS3.py
python figure_redesign_v2/scripts/verify_table3.py    # exit 0
python figure_redesign_v2/scripts/verify_all_v2.py    # "ALL CHECKS PASSED"
python figure_redesign_v2/scripts/verify_figure6.py   # "26/26 passed; failures=0"
```

The one-shot driver `python figure_redesign_v2/scripts/build_v2_all.py` runs the same stages in
order and then the three verifiers. **Two of its stages re-derive intermediates from per-scan
aligned caches and are therefore data-gated (Level B)**: `compute_figure2_data.py` (reads the 501
VI per-scan caches `structured_mismatch_phase0/scripts/cache/scans/`) and
`reproduce_figure6_gate.py` (reads representative frames `cache/ext/iv/scan_0278.npz` and
`tj2_supplemental/cache/ii/scan_0505.npz`). Their frozen outputs are already committed in
`figure_redesign_v2/data/{source,derived}` (and archived in `figures_final/`), so every drawing
and verification step above runs offline; only these two *recomputation* stages need the
downloaded datasets and rebuilt caches.

### Expected key results (frozen)

- **G3 single-look verdict = `CONFIRMED`** (C1 ∧ C2 ∧ C3):
  - C1 robust survives: Huber median `e_t ≈ 55.89 mm` while the matched self-null is `≈ 0`
    (`~9e-14`); Huber stays above half the LS median (`75.04 mm`); all blocks > 10 mm.
  - C2 mitigation actionable: **patch** correction median gain `≈ 28.93 mm`, block-bootstrap 95% CI
    `[25.7, 33.0]`, paired sign-flip **p ≈ 0.0005**, `99.5%` frames improved; `best_level = patch`.
  - C3 deployable: estimated-view warm-start retains `≈ 99.7%` of the oracle mitigation and beats
    raw on `64.2%` of in-support frames (thresholds 70% / 60%).
- Figure 5 frozen paired benefits (PH-H) for VI/IV/II/III: `45.38 / 31.81 / 7.87 / 19.66 mm`;
  rotation cost `0.421 / 0.052 / 0.498 / 0.72 deg`.
- `verify_all_v2.py` ends with `ALL CHECKS PASSED`; the figure archive's own gates are in
  `figure_redesign_v2/figures_final/validation.md`.

Numbers are deterministic (fixed seeds; single-thread BLAS defaults are set in the run scripts).
Bootstrap Monte-Carlo uses B = 2000 with seed 42; tiny last-digit differences across BLAS builds
are immaterial and the verdicts/gates are thresholded.

## Level B — end-to-end per-scan reproduction (after download)

```bash
python data/download_epos.py                 # VI, IV, V
python g_chain/G3_FINAL_CONFIRMATION/scripts/g3_download_cache.py   # III + cache + support
# II gated order (see data/README.md): tj2_2_fetch_poses -> tj2_3_support_screen
#                                      -> tj2_4_download_ii -> tj2_5_cache_ii

python structured_mismatch_phase0/scripts/s1_residuals.py          # then s3..s9 / m* / r* in order
python g_chain/G0_ROBUST_FALSIFICATION/scripts/g0_run.py
python g_chain/G1_MITIGATION/scripts/g1_run.py
python g_chain/G2_ESTIMATED_VIEW/scripts/g2_run.py
python g_chain/G3_FINAL_CONFIRMATION/scripts/g3_single_look.py
python g_chain/G_GENERALITY/scripts/g_generality_run.py
python final_three_experiments/01_coarse_initialization/e1_run_coarse.py
python final_three_experiments/02_vi_leave_block_out/e2_run_lobo.py
python final_three_experiments/03_runtime_memory/e3_benchmark.py
```

The single-look policy (Dataset III) forbids re-running, editing, or removing frames after the
outcome is read; follow `g_chain/G3_FINAL_CONFIRMATION/FREEZE_MANIFEST.md`.

## Notes

- Rendered figures embed a creation timestamp, so regenerated PDF/PNG bytes can differ even when
  the data are identical; the frozen published figures and their per-file hashes live in
  `figure_redesign_v2/figures_final/` (`source_manifest.json`).
- `SHA256SUMS.txt` covers source code, configs, frozen numerical artifacts and result tables
  (plus the frozen `figures_final/output`). Raw datasets and regenerated caches are not listed.
