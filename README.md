# Reproducible verification code — structured model-mismatch robust point-cloud registration (EPOS-Lid)

This repository is the **frozen, self-contained verification bundle** for the paper on
**structured model mismatch in spacecraft / target LiDAR pose estimation and its robust
registration correction**. It contains the exact numerical cores, the pre-registered
experiments, the frozen per-frame result tables, the final figures, and the protocol/decision
records that support every headline claim.

It was curated from the authors' working directory. Only the **final, frozen analysis chain**
and its direct inputs are included; intermediate/scratch/backup folders and the multi-GB raw
point clouds are excluded (the public raw datasets can be downloaded and regenerated — see
[`data/README.md`](data/README.md)). No original working file was modified or deleted while
building this bundle; everything here is a copy.

> The code is deterministic and the statistical scripts and figures can be re-run **without
> downloading any dataset** — they read the committed frozen result tables. Downloading the raw
> trajectories is only required to reproduce the per-scan registration runs end to end.

---

## 1. What the paper claims (and where each claim is verified)

The central finding is a **view-dependent, spatially structured mismatch field** between the
nominal CAD model and the real sensor returns, which biases classical ICP even from the
ground-truth pose, together with a **robust objective + learned VI-only correction** that
diagnoses and mitigates it.

| Paper element | Verification location |
|---|---|
| Phase-0 minimal phenomenon, identifiability, nuisance/gradient audits (development trajectory VI) | [`structured_mismatch_phase0/`](structured_mismatch_phase0/) (`reports/`, `scripts/s*.py`, `scripts/m*.py`, `scripts/r*.py`) |
| **G0** — robust falsification: Huber/trimmed ICP vs least-squares, real gradient vs matched self-null | [`g_chain/G0_ROBUST_FALSIFICATION/`](g_chain/G0_ROBUST_FALSIFICATION/) |
| **G1** — mitigation: global / patch / full view-conditioned correction (oracle view) | [`g_chain/G1_MITIGATION/`](g_chain/G1_MITIGATION/) |
| **G2** — deployable estimated-view warm-start pipeline and patch fallback | [`g_chain/G2_ESTIMATED_VIEW/`](g_chain/G2_ESTIMATED_VIEW/) |
| **G3** — untouched confirmatory trajectory (Dataset III), single-look, pre-registered C1/C2/C3 | [`g_chain/G3_FINAL_CONFIRMATION/`](g_chain/G3_FINAL_CONFIRMATION/) |
| Spatial hierarchy transfer (global / patch / full) across II/IV/V | [`g_chain/HIERARCHY_TRANSFER/`](g_chain/HIERARCHY_TRANSFER/) |
| Generality: dose-response, geometry vs noise controls | [`g_chain/G_GENERALITY/`](g_chain/G_GENERALITY/) |
| Final three experiments: coarse initialization, VI leave-block-out, runtime/memory | [`final_three_experiments/`](final_three_experiments/) |
| Revision/response experiments (timing, iteration budget, pose-active, historical baselines, II failure cases, targeted tests) | [`revision_experiments/`](revision_experiments/) |
| Reviewer follow-ups 6–9 (arms replay, patch robustness, equal-RMS, view support) | [`FOLLOWUP_6_9/`](FOLLOWUP_6_9/) |
| Follow-up controls (nuisance gradients, patch-label placebo, mechanism link, III frozen replay, Figure 2/6 provenance) | [`AUDIT_FOLLOWUP/`](AUDIT_FOLLOWUP/) |
| Supplemental Dataset II metadata screen and single outcome test | [`tj2_supplemental/`](tj2_supplemental/) |
| Theory: assumptions, notation, robust-loss derivation, robust-regime interpretation | [`FINAL_TOPJOURNAL_HARDENING/THEORY/`](FINAL_TOPJOURNAL_HARDENING/THEORY/) |
| **Final paper figures (1–6 + supplementary)** and their frozen build | [`figure_redesign_v2/`](figure_redesign_v2/) (build) and [`figure_redesign_v2/figures_final/`](figure_redesign_v2/figures_final/) (frozen archive with SHA manifest) |
| Delivered figure snapshot (Figure 1–8 package) | [`FINAL_FIGURES/`](FINAL_FIGURES/) |

The single most important confirmatory artifact is the **G3 single-look verdict**, pre-registered
before Dataset III point clouds were read: [`g_chain/G3_FINAL_CONFIRMATION/FREEZE_MANIFEST.md`](g_chain/G3_FINAL_CONFIRMATION/FREEZE_MANIFEST.md)
and `FINAL_CONFIRMATION_DECISION.md`. Re-running `g3_decide.py` on the committed tables yields
**`verdict = CONFIRMED`** (C1 robust-survives, C2 mitigation actionable, C3 deployable).

---

## 2. Frozen scientific choices (do not re-tune)

- **VI-only mismatch predictor**: k = 16 nearest training views, `range_std = 2.0643`,
  support radius `tau = 0.4403`, `alpha_VI = 0.01999`, **24 model-point patches**.
- **Robust objective (primary)**: Huber IRLS, `delta = 1.345`, robust scale
  `s = max(1.4826·MAD, model median-NN-spacing = 0.00811 m)`; secondary trimmed ICP keeps `q = 0.80`.
- **Optimization**: basin clip `0.30 m / 15°`, `max_iter = 40`, tolerances `1e-8` (point-to-point)
  / `1e-9` (point-to-plane), finite-difference step `5 mm / 0.25°`, nearest **fixed-model**
  correspondence recomputed every probe.
- **Metrics**: `e_t = ||t_hat − t_GT||` in mm, `e_R = angle(R_hat R_GT^T)` in degrees;
  temporal moving-block bootstrap `L = 5/10/20`, `B = 2000`; paired block sign-flip `L = 5`.
- **Trajectories / coverage**

  | Trajectory | Raw scans | Used in support | Role |
  |---|---:|---:|---|
  | VI | 501 | 501 | Development / field estimation & calibration |
  | IV | 2,428 | 156 | External transfer |
  | II | 1,253 | 428 | Difficult external transfer (supplemental) |
  | III | 1,302 | 371 | Untouched confirmatory (single-look) |

Dataset I is permanently sealed and is not part of this bundle.

---

## 3. Repository layout

```
robust-lidar-registration/
├── structured_mismatch_phase0/      # Phase-0 core + audits (trajectory VI)
│   ├── scripts/
│   │   ├── s0_common.py             # IO, rotations, PCA normals, FPFH/RANSAC/vanilla ICP
│   │   ├── m_common.py              # SE(3) chart, objectives, vanilla solvers
│   │   ├── s*.py / m*.py / r*.py    # phase-0 analyses, external transfer, predictor build
│   │   └── cache/                   # FROZEN small artifacts (model, normals, patches, predictor)
│   ├── results/                     # frozen phase-0 tables/figures
│   └── reports/                     # phase-0 audit reports
├── g_chain/                         # FINAL confirmatory chain G0→G3 + hierarchy + generality
│   ├── common/g_common.py           # robust ICP, predictor use, bootstrap/sign-flip stats
│   ├── G0_ROBUST_FALSIFICATION/ … G3_FINAL_CONFIRMATION/
│   ├── HIERARCHY_TRANSFER/
│   └── G_GENERALITY/
├── final_three_experiments/         # E1 coarse init, E2 VI leave-block-out, E3 runtime/memory
├── revision_experiments/            # response/revision experiments + shared libs
├── FOLLOWUP_6_9/                    # reviewer follow-up analyses
├── AUDIT_FOLLOWUP/                  # follow-up controls + Figure 2/6 provenance (used by figure6 gate)
├── tj2_supplemental/                # Dataset II metadata screen + supplemental test
├── POSE_AUDIT/                      # only two frozen result CSVs referenced by diagnostic scripts
├── figure_redesign_v2/              # canonical figure build (scripts/, configs/, data/, figures/)
│   └── figures_final/               # frozen, SHA-manifested figure archive (output/ = final PDFs/PNGs)
├── FINAL_FIGURES/                   # delivered Figure 1–8 snapshot
├── FINAL_TOPJOURNAL_HARDENING/THEORY/
├── external_dataset_scout/.../epos_target_model.3d   # frozen nominal CAD point model (67,870 pts)
├── data/                            # dataset download helper + dataset license (no raw data committed)
├── REQUIREMENTS.txt
├── SHA256SUMS.txt                   # checksums of frozen code/artifacts (see VERIFICATION.md)
└── VERIFICATION.md                  # exact commands and expected results
```

Each experiment folder follows the same convention: `scripts/` (code), `frozen_config.yaml`
(pre-registered parameters), `results/` (frozen per-frame + aggregate tables and figures),
and a `*_DECISION.md` / `*_report.md` recording the pre-registered gate and verdict.

---

## 4. Setup

Python **3.14** was used (the code is standard NumPy/SciPy and also runs on 3.11+).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -r REQUIREMENTS.txt
```

Dependencies: NumPy, SciPy, pandas, Matplotlib (core); scikit-learn (k-means patch partition /
some analyses), psutil (E3 memory benchmark), Pillow + PyMuPDF (a few figure/PDF checks).
PyYAML is **not** required.

> Windows note: the original dataset downloaders shell out to `curl.exe` (present on Windows 10/11).
> On Linux/macOS `curl` is likewise available; the helper in `data/` uses pure-Python urllib.

---

## 5. Reproducing the results

### 5.1 Statistics, decisions and figures — no dataset download needed

The committed `results/*.csv` are the frozen per-frame outputs; the `*_stats*` / `*_analyze*`
scripts and the figure scripts recompute every aggregate, confidence interval, p-value and plot
from them.

```bash
# G3 confirmatory decision on the untouched trajectory (prints C1/C2/C3 and verdict)
python g_chain/G3_FINAL_CONFIRMATION/scripts/g3_decide.py        # -> verdict = CONFIRMED

# G0/G1/G2 statistics, hierarchy and generality (recompute tables + figures from CSVs)
python g_chain/G0_ROBUST_FALSIFICATION/scripts/g0_stats.py
python g_chain/G1_MITIGATION/scripts/g1_stats.py
python g_chain/G2_ESTIMATED_VIEW/scripts/g2_stats.py
python g_chain/HIERARCHY_TRANSFER/scripts/hierarchy_transfer.py
python g_chain/G_GENERALITY/scripts/g_generality_stats.py

# Final three experiments (aggregate analyses from frozen framewise tables)
python final_three_experiments/01_coarse_initialization/e1_combine_analyze.py
python final_three_experiments/02_vi_leave_block_out/e2_analyze.py
python final_three_experiments/03_runtime_memory/e3_analyze.py

# Final figures: draw every figure from the committed frozen intermediates
# (writes figure_redesign_v2/figures/main from figure_redesign_v2/data)
python figure_redesign_v2/scripts/draw_figure1.py
python figure_redesign_v2/scripts/draw_figure2.py
python figure_redesign_v2/scripts/figure3.py
python figure_redesign_v2/scripts/figure4.py
python figure_redesign_v2/scripts/make_figure5.py
python figure_redesign_v2/scripts/plot_figure6.py
python figure_redesign_v2/scripts/make_figureS2.py
# numerical / rendering gates (offline, against committed frozen data)
python figure_redesign_v2/scripts/verify_table3.py
python figure_redesign_v2/scripts/verify_all_v2.py              # "ALL CHECKS PASSED"
python figure_redesign_v2/scripts/verify_figure6.py             # "26/26 passed"
```

The one-shot driver `build_v2_all.py` runs all stages in order; two of them
(`compute_figure2_data.py`, `reproduce_figure6_gate.py`) re-derive intermediates from per-scan
aligned caches and so are data-gated (Level B). Their outputs are already frozen here, so all
drawing and verification above works offline. Full commands and expected numbers are in
[`VERIFICATION.md`](VERIFICATION.md).

The frozen, SHA-pinned figure archive (with the exact published PDFs/PNGs and per-file hashes) is
under [`figure_redesign_v2/figures_final/`](figure_redesign_v2/figures_final/); see its
`README.md`, `validation.md` and `source_manifest.json`.

### 5.2 End-to-end per-scan runs — requires downloading the public datasets

Raw point clouds (~3 GB total) are **not** committed. Download/regenerate them first
(see [`data/README.md`](data/README.md)):

```bash
python data/download_epos.py            # trajectories VI (dev), IV and V (external transfer)
python g_chain/G3_FINAL_CONFIRMATION/scripts/g3_download_cache.py   # III: download + cache + support screen
# Dataset II (supplemental), in the designed gated order:
python tj2_supplemental/scripts/tj2_2_fetch_poses.py
python tj2_supplemental/scripts/tj2_3_support_screen.py
python tj2_supplemental/scripts/tj2_4_download_ii.py
python tj2_supplemental/scripts/tj2_5_cache_ii.py
```

Then the per-scan `*_run*.py` scripts regenerate the framewise tables from scratch, e.g.
`g0_run.py`, `g1_run.py`, `g2_run.py`, `g3_single_look.py`, `g_generality_run.py`,
`final_three_experiments/01_coarse_initialization/e1_run_coarse.py`,
`02_vi_leave_block_out/e2_run_lobo.py`, `03_runtime_memory/e3_benchmark.py`.

---

## 6. Integrity and provenance

- Frozen artifacts are hash-pinned and asserted at runtime (e.g. the VI-only predictor SHA-256 in
  `g_common.py`, and the full table in `g_chain/G3_FINAL_CONFIRMATION/FREEZE_MANIFEST.md`).
- `SHA256SUMS.txt` lists hashes for the frozen code and small artifacts shipped here; run
  `python verify_checksums.py` to check them.
- Every confirmatory script records command, config, seed, input/output SHA-256, framewise raw
  results and a provenance JSON (`*_provenance.json`, `FINAL_MANIFEST.json`,
  `SUPPLEMENTAL_FROZEN_MANIFEST.yaml`).
- The raw EPOS-Lid trajectories are shared under **CDLA-Sharing-1.0** (see
  [`data/LICENSE_EPOS_DATASET.md`](data/LICENSE_EPOS_DATASET.md)). Please consult
  `data/README.md` for source URLs, sizes, counts and the sealed/single-look policy.

## 7. Portability note

The original scripts contained absolute working-directory paths (`D:\doubao\...`). The curated
copies were mechanically ported: each affected `.py` resolves the repository root at runtime via
a small marker file (`.repo_root`) and a `_pp(...)` helper, so the bundle runs from any clone
location on Windows, Linux or macOS. Scientific logic, parameters and frozen numbers are
unchanged. **The port necessarily changes the bytes (and thus hashes) of the 97 ported source
files, while the frozen numerical artifacts (predictor / model / patches) remain byte-identical
and hash-asserted at runtime — see [`PORTABILITY.md`](PORTABILITY.md) for the exact change and
the full file list.**
