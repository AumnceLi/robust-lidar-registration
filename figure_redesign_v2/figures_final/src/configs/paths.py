"""V2 figure redesign — path constants and shared data."""

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

import os

# Source data paths (frozen, read-only)
SRC = {
    "replay79_arms": _pp("FOLLOWUP_6_9/scripts/replay79_arms.csv"),
    "dbs_vector": _pp("revision_experiments/exp4_historical_baselines/dbs_vector_framewise.csv"),
    "e1_framewise": _pp("final_three_experiments/01_coarse_initialization/e1_coarse_init_framewise.csv"),
    "e1_summary": _pp("final_three_experiments/01_coarse_initialization/e1_coarse_init_summary.csv"),
    "dose_response": _pp("g_chain/G_GENERALITY/results/dose_response.csv"),
    "geometry_results": _pp("g_chain/G_GENERALITY/results/geometry_results.csv"),
    "phase_samples": _pp("FINAL_FIGURES/Figure8/phase_samples_ls_translation.csv"),
    # ── Figure 1 & 2 source data ──────────────────────────────────────
    "model_cache":  _pp("structured_mismatch_phase0/scripts/cache/model_cache.npz"),
    "patches":      _pp("structured_mismatch_phase0/scripts/cache/patches.npz"),
    "frozen_field": _pp("structured_mismatch_phase0/scripts/cache/rescue/VI_ONLY_PREDICTOR_FROZEN.npz"),
    "scan_dir_vi":  _pp("structured_mismatch_phase0/scripts/cache/scans"),
    # ── Figure 6 source data (frozen, read-only) ───────────────────────
    "rep_frames":   _pp("revision_experiments/06_II_failure_cases/ii_failure_representative_frames.csv"),
    "scan_cache_iv": _pp("structured_mismatch_phase0/scripts/cache/ext/iv"),
    "scan_cache_ii": _pp("tj2_supplemental/cache/ii"),
}

# SHA256 of the frozen VI-only predictor field (hard-asserted before any recompute)
FROZEN_FIELD_SHA256 = "8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe"

# V1 derived data (reusable)
V1_DERIVED_DIR = _pp("figure_redesign_20260913/data/derived")

# V2 output dirs
ROOT = _pp("figure_redesign_v2")
DELIVERY_ROOT = ROOT
DATA_SOURCE_DIR = os.path.join(ROOT, "data", "source")
DATA_DERIVED_DIR = os.path.join(ROOT, "data", "derived")
FIG_MAIN_DIR = os.path.join(ROOT, "figures", "main")
FIG_SUPP_DIR = os.path.join(ROOT, "figures", "supplementary")
ASSETS_GEOMETRY_DIR = os.path.join(ROOT, "assets", "geometry")
ASSETS_ILLUSTRATIONS_DIR = os.path.join(ROOT, "assets", "illustrations")
ASSETS_RENDERS_DIR = os.path.join(ROOT, "assets", "renders")
MANUSCRIPT_DIR = os.path.join(ROOT, "manuscript")
MANIFEST_DIR = os.path.join(ROOT, "manifests")
CHECKS_DIR = os.path.join(ROOT, "checks")

# Coverage statistics (per trajectory)
COMMON_SUPPORT_COUNTS = {
    "VI": {"total": 501, "used": 501, "pct": 100.0, "role": "Development/calibration"},
    "IV": {"total": 2428, "used": 156, "pct": 6.4, "role": "External transfer"},
    "II": {"total": 1253, "used": 428, "pct": 34.2, "role": "Difficult external transfer"},
    "III": {"total": 1302, "used": 371, "pct": 28.5, "role": "Secondary"},
}

# Bootstrap block counts per trajectory (block sizes for block bootstrap)
BOOTSTRAP_BLOCKS = {
    "VI": 6,
    "IV": 4,
    "II": 9,
    "III": 8,
}

# Raw pool counts (for coverage denominator context)
RAW_POOL_COUNTS = {
    "VI": 501,
    "IV": 2428,
    "II": 1253,
    "III": 1302,
}

# Trajectory display order
TRAJECTORY_ORDER = ["VI", "IV", "II", "III"]

# Correct Table 3 cases from PDF (for Fig4 verification)
# These are frozen experiment published condition medians.
# RMS values are not available in raw CSV files; they are published medians from PDF Table 3.
TABLE3_CASES = [
    {"geometry": "GA", "family_A": "D1 coherent displacement", "rms_A": 7.95, "et_A": 8.930,
     "family_B": "D3 local mismatch", "rms_B": 7.70, "et_B": 0.900, "delta_et": 8.030, "ratio": 9.9},
    {"geometry": "GB", "family_A": "D4 span growth", "rms_A": 4.06, "et_A": 0.058,
     "family_B": "D3 local mismatch", "rms_B": 3.97, "et_B": 0.621, "delta_et": 0.563, "ratio": 10.6},
    {"geometry": "GB", "family_A": "D4 span growth", "rms_A": 5.33, "et_A": 0.184,
     "family_B": "D5 coherent tilt", "rms_B": 5.08, "et_B": 1.528, "delta_et": 1.344, "ratio": 8.3},
    {"geometry": "GC", "family_A": "D3 local mismatch", "rms_A": 3.75, "et_A": 0.988,
     "family_B": "D4 span growth", "rms_B": 3.80, "et_B": 0.116, "delta_et": 0.872, "ratio": 8.5},
]
