# figures_final — Ast review round 6 (2026-09-14), final adopted six-figure set

Frozen, reproducible archive of the six main figures for the spacecraft
LiDAR scan-to-model registration paper. Working width 180 mm (double column).
Experimental results are frozen; visual edits never alter data, cases or
statistical definitions.

## Layout
```
figures_final/
├─ output/                 figure1–6 .pdf (vector, fonts embedded) / .svg
│                          (editable text) / .png (600 dpi) — the adopted set
├─ src/
│  ├─ scripts/             six drawing scripts + data computation + 3 verifiers
│  │                       + build_v2_all.py (single entry point)
│  └─ configs/             figure_style.py, colors.py, camera_config.py, paths.py
├─ data/
│  ├─ derived/             exact plotted values / statistics (see DATA_DICTIONARY)
│  ├─ source/              frozen Figure-6 reference scans Q_ref
│  └─ DATA_DICTIONARY.md   columns, units, two-level statistic definitions
├─ assets/
│  ├─ renders/             no-label panorama / ROI assets (2 cases × 3 arms)
│  └─ manifests/           case-selection / source-asset / frame-roster tables
├─ captions.md             final English captions for Figure 1–6 in one file
├─ source_manifest.json    per-file SHA-256, sizes, seeds, conventions, software
│                          and upstream-input paths + hashes
├─ validation.md           [D] data-verified vs [V] visual checks + known limits
└─ README.md               this file
```

## One-command rebuild
The `src/` here is a frozen snapshot. To regenerate everything from the archived
inputs, run inside the project root `D:\doubao\figure_redesign_v2` (the snapshot
keeps the same relative layout under `scripts/` and `configs/`):

```powershell
python scripts/build_v2_all.py
```

This runs, in order: Figure-2 data computation → the six figure scripts → the
three supplementary figures → `verify_table3.py`, `verify_all_v2.py`,
`reproduce_figure6_gate.py` + `verify_figure6.py`, and writes
PDF/SVG/600-dpi PNG to `figures/main`. A clean run prints `BUILD OK` and exits 0.

To re-assemble this archive after a rebuild:
```powershell
python checks/assemble_figures_final.py
```

## Requirements
Python 3.14 (3.10+ should work), matplotlib 3.11, numpy 2.5, pandas 3.0,
scipy 1.18, Pillow. No network access needed; upstream read-only inputs listed
in `source_manifest.json → external_inputs` must exist at those paths
(hashes recorded). Randomness is seeded (Figure-6 display subset 12345;
Figure-5 block bootstrap 42; Figure-2 panel-a subsample 42).

## What each figure establishes
Fig 2 spatial/view-dependent residual pattern → Fig 3 local pose-active
mechanism → Fig 4 controlled matched-RMS evidence → Fig 5 marginal/paired
benefits and rotation cost (the statistical result) → Fig 6 two fixed spatial
cases (one improvement, one Full degradation). Figure 6 is illustrative and
does not replace the Figure-5 statistics.
