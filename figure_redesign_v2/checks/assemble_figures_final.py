# -*- coding: utf-8 -*-
"""Assemble the Ast-review (2026-09-14) figures_final deliverable archive.

Layout (review §11):
  output/  final figure1-6 PDF/SVG/600dpi PNG (single adopted version)
  src/     drawing + verification scripts and shared configs
  data/    derived plotting data actually used + frozen figure-6 source scans
  assets/  no-label renders + case-selection manifests
  captions.md / source_manifest.json (SHA-256) are written at the root.
validation.md / README.md / data/DATA_DICTIONARY.md are authored separately.
"""
# ==== portable repo root (auto-added; replaces hard-coded D:\doubao) ====
import os as _os
def _repo_root():
    _d = _os.path.dirname(_os.path.abspath(__file__))
    while not _os.path.exists(_os.path.join(_d, '.repo_root')):
        _p = _os.path.dirname(_d)
        if _p == _d:
            raise RuntimeError('repo-root marker .repo_root not found')
        _d = _p
    return _d
_REPO = _repo_root()
def _pp(*_a):
    return _os.path.join(_REPO, *_a).replace('\\', '/')
# ==== end portable root ====

import os, sys, shutil, hashlib, json, glob, platform, datetime

ROOT = _pp("figure_redesign_v2")
sys.path.insert(0, os.path.join(ROOT, "configs"))
import paths  # noqa: E402

OUT = os.path.join(ROOT, "figures_final")
DIRS = ["output", "src/scripts", "src/configs", "data/derived", "data/source",
        "assets/renders", "assets/manifests"]

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
for d in DIRS:
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

records = []  # [archive_path, sha256, bytes]

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def cp(src, arc_dst):
    dst = os.path.join(OUT, arc_dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    records.append((arc_dst.replace("\\", "/"), sha256(dst), os.path.getsize(dst)))

# ── 1. final outputs (single adopted version) ───────────────────────────────
for i in range(1, 7):
    for ext in ("pdf", "svg", "png"):
        cp(os.path.join(ROOT, "figures", "main", f"figure{i}.{ext}"),
           f"output/figure{i}.{ext}")

# ── 2. source scripts + shared configs ──────────────────────────────────────
SCRIPTS = ["draw_figure1.py", "draw_figure2.py", "figure3.py", "figure4.py",
           "make_figure5.py", "plot_figure6.py", "compute_figure2_data.py",
           "reproduce_figure6_gate.py", "verify_table3.py", "verify_all_v2.py",
           "verify_figure6.py", "build_v2_all.py"]
CONFIGS = ["figure_style.py", "colors.py", "camera_config.py", "paths.py"]
for s in SCRIPTS:
    p = os.path.join(ROOT, "scripts", s)
    if os.path.exists(p):
        cp(p, f"src/scripts/{s}")
for c in CONFIGS:
    cp(os.path.join(ROOT, "configs", c), f"src/configs/{c}")

# ── 3. derived plotting data for the six main figures ───────────────────────
deriv_patterns = ["figure2_residual_stats.npz", "figure3_*", "figure4_*",
                  "figure5_*", "figure6_case_*"]
seen = set()
for pat in deriv_patterns:
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "derived", pat))):
        if os.path.basename(p) in seen:
            continue
        seen.add(os.path.basename(p))
        cp(p, f"data/derived/{os.path.basename(p)}")

# ── 4. frozen figure-6 source scans (small) ─────────────────────────────────
for p in sorted(glob.glob(os.path.join(ROOT, "data", "source", "figure6_case_*_scan.npz"))):
    cp(p, f"data/source/{os.path.basename(p)}")

# ── 5. assets: no-label renders + manifests ─────────────────────────────────
for p in sorted(glob.glob(os.path.join(ROOT, "assets", "renders", "*"))):
    cp(p, f"assets/renders/{os.path.basename(p)}")
man_dir = os.path.join(ROOT, "manifests")
if os.path.isdir(man_dir):
    for p in sorted(glob.glob(os.path.join(man_dir, "*"))):
        if os.path.isfile(p):
            cp(p, f"assets/manifests/{os.path.basename(p)}")

# ── 6. merged captions ──────────────────────────────────────────────────────
cap_parts = []
for i in range(1, 7):
    with open(os.path.join(ROOT, "manuscript", f"figure{i}_caption.md"),
              encoding="utf-8-sig") as f:
        cap_parts.append(f.read().strip())
captions = ("# Figure captions (final, round 6 / Ast review 2026-09-14)\n\n"
            + "\n\n---\n\n".join(cap_parts) + "\n")
with open(os.path.join(OUT, "captions.md"), "w", encoding="utf-8") as f:
    f.write(captions)
records.append(("captions.md", sha256(os.path.join(OUT, "captions.md")),
                os.path.getsize(os.path.join(OUT, "captions.md"))))

# ── 6b. authored docs (staged under checks/_final_authored so a clean rebuild
#        re-adds them and their hashes land in the manifest) ──────────────────
AUTHORED = os.path.join(ROOT, "checks", "_final_authored")
for ap in sorted(glob.glob(os.path.join(AUTHORED, "**", "*"), recursive=True)):
    if os.path.isfile(ap):
        rel = os.path.relpath(ap, AUTHORED)
        cp(ap, rel)

# ── 7. external (upstream, read-only) inputs: record path + hash, not copied ─
def ext_record(label, p):
    if p and os.path.exists(p):
        return {"label": label, "path": p, "exists": True,
                "sha256": sha256(p), "bytes": os.path.getsize(p)}
    return {"label": label, "path": p, "exists": False}

V1 = getattr(paths, "V1_DERIVED_DIR", "")
external = [
    ext_record("fig4_dose_response_csv",
               _pp("g_chain/G_GENERALITY/results/dose_response.csv")),
    ext_record("fig3_pose_active_framewise_csv",
               _pp("revision_experiments/exp3_pose_active/pose_active_direct_framewise.csv")),
    ext_record("fig6_replay79_arms_log_on_bound",
               _pp("FOLLOWUP_6_9/scripts/replay79_arms.csv")),
    ext_record("fig1_2_model_cache", paths.SRC.get("model_cache")),
    ext_record("fig1_2_patches", paths.SRC.get("patches")),
    ext_record("fig5_marginal_medians_iqr",
               os.path.join(V1, "figure5_marginal_medians_iqr.csv")),
    ext_record("fig5_paired_benefits_perframe",
               os.path.join(V1, "figure5_paired_benefits_perframe.csv")),
    ext_record("fig5_rotation_cost_perframe",
               os.path.join(V1, "figure5_rotation_cost_perframe.csv")),
]

# ── 8. source_manifest.json ─────────────────────────────────────────────────
import numpy, pandas, matplotlib
try:
    import scipy; scipy_v = scipy.__version__
except Exception:
    scipy_v = None

manifest = {
    "archive": "figures_final",
    "created_local": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "review": "Ast six-figure review, 2026-09-14, round 6",
    "working_size_mm": {"double_column_width": 180,
                        "figure1": [180, 116], "figure2": [180, 108],
                        "figure3": [180, 110], "figure4": [180, 106],
                        "figure5": [180, 114], "figure6": [180, 118]},
    "export": {"pdf_fonttype": 42, "svg_fonttype": "none (editable <text>)",
               "png_dpi": 600, "vector": "axes/text/lines/arrows/equations",
               "rasterised": "point clouds / dense scatter"},
    "random_seeds": {"fig6_display_subsample": 12345,
                     "fig5_block_bootstrap": 42, "fig2_panel_a_subsample": 42},
    "locked_cases": {
        "fig6": ["IV frame 278 (improvement)", "II frame 505 (Full degradation, on_bound=1)"],
        "fig4_table3_pairs": ["GA D1/D3", "GB D4/D3", "GB D4/D5", "GC D3/D4"]},
    "statistics_conventions": {
        "fig2": "within-frame patch median -> block/range-bin median; band=IQR(Q25-Q75); 8 fixed bins",
        "fig4_ab": "main=median of 3 geometry condition medians; band=min-max of those; 20 reps/geometry-dose",
        "fig5_ab": "descriptive IQR (Q25/Q75)",
        "fig5_c": "whole-block bootstrap 95% percentile CI (B=2000, seed 42)",
        "fig5_d": "descriptive IQR (not CI)",
    },
    "software": {"python": platform.python_version(), "matplotlib": matplotlib.__version__,
                 "numpy": numpy.__version__, "pandas": pandas.__version__, "scipy": scipy_v,
                 "platform": platform.platform()},
    "external_inputs": external,
    "files": [{"path": r[0], "sha256": r[1], "bytes": r[2]} for r in records],
}
with open(os.path.join(OUT, "source_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"archived {len(records)} files to {OUT}")
miss = [e['label'] for e in external if not e['exists']]
print("external inputs missing:", miss if miss else "none (all resolved)")
