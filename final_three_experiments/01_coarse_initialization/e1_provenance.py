# -*- coding: utf-8 -*-
"""E1 provenance: exact commands, frozen config, seed, input SHA-256, output SHA-256."""
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

import os, sys, glob
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F

commands = [
    "$env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; $env:OPENBLAS_NUM_THREADS=1",
    "python e1_fidelity_gate.py",
    "python e1_run_coarse.py            # NEW L4/L5/L6 only; --nw default=20",
    "python e1_combine_analyze.py",
]
cfg = dict(
    levels_mm_deg={l: F.LEVELS[l] for l in F.LEVEL_ORDER},
    reused_local_levels=["L0(ref)","L1","L2","L3"], new_coarse_levels=F.NEW_COARSE,
    L7_excluded="500mm start exceeds frozen 0.30m translation safeguard at x0 -> precondition fails",
    directions_per_level=list(F.DIR_IDS), n_directions=4,
    perturbation_family="identical t3_common DIRS + cyclic ROT_PAIR (max diff vs shipped L1-L3 = 0.0)",
    frames="frozen 20/traj roster (initialization_frames.json); NOT re-selected",
    methods=F.METHODS4, primary_comparison=("Raw","Patch"),
    capture_A="final t < init t AND final r < init r (relative)",
    capture_B="final t<=50mm AND final r<=2deg (recovery into tested local basin; experimental, not mission tol)",
    safeguard="frozen basin clip 0.30m/15deg", solver="frozen g_common.robust_icp via t3_common.inst_icp (unchanged)",
    seed="no RNG in ICP/perturbation (deterministic sign-balanced); frozen plab from MiniBatchKMeans seed=42",
    workers=20, blas_threads=1, kdtree_query_threads=1,
)
prov = F.Prov("E1_coarse_initialization", os.path.abspath(__file__), config=cfg, seed="deterministic (no RNG)",
              note="L0-L3 reused byte-for-byte from final_targeted; fidelity gate reproduces them to 5.7e-14 mm with 0 categorical mismatches.")
for key, rel in [
    ("predictor_frozen", r"structured_mismatch_phase0\scripts\cache\rescue\VI_ONLY_PREDICTOR_FROZEN.npz"),
    ("model_cache", r"structured_mismatch_phase0\scripts\cache\model_cache.npz"),
    ("patches", r"structured_mismatch_phase0\scripts\cache\patches.npz"),
    ("roster", r"revision_experiments\final_targeted\initialization_frames.json"),
    ("reused_L0L3_framewise", r"revision_experiments\final_targeted\initialization_sensitivity_framewise.csv")]:
    prov.add_input(key, os.path.join(F.ROOT, rel))
outs = sorted(glob.glob(os.path.join(F.E1_OUT, "*")))
outs = [p for p in outs if os.path.isfile(p) and os.path.basename(p)!="e1_provenance.json" and not p.endswith(".py")]
prov.finish(os.path.join(F.E1_OUT, "e1_provenance.json"), outs)
print("E1 provenance written with", len(outs), "outputs")
for p in outs: print("  out", os.path.basename(p))
