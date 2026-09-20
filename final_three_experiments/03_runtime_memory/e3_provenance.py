# -*- coding: utf-8 -*-
"""E3 provenance."""
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
commands=[
 "$env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; $env:OPENBLAS_NUM_THREADS=1",
 "python e3_benchmark.py   # single process/thread; warmup=1 repeat=5; spawns 6 isolated memory workers",
 "python e3_analyze.py",
]
cfg=dict(
 methods=["Raw","Huber","Patch","PatchHuber","Full","EstimatedFull"],
 estimated_full_definition="est_warmstart: frozen raw nominal reg -> estimated view -> corrected-model reg warm-started (2 registrations)",
 frames="frozen 20/traj roster = 80 frames (same as E1); NOT the full 1456",
 warmup=1, repeat=5, per_frame_stat="median over repeats", deployment_distribution="across 80 frames median/p25/p75/p95",
 stages=["model_build","view_query","kdtree","registration1","registration2","total"],
 thread_fairness="BLAS threads=1; os.cpu_count pinned 1; cKDTree query workers=1 for EVERY method",
 reusable_assets="Raw/Huber/Patch/PatchHuber cache model+tree once; Full builds query-dependent model+tree per frame; EstFull 2nd model query-dependent",
 memory="fresh subprocess per method; psutil RSS baseline/peak/delta + tracemalloc python peak",
 calibration_cost="frozen MiniBatchKMeans k=24 seed42 n_init20 batch4096 (labels verified == frozen plab) + VI mu_patch hierarchy build",
 seed="deterministic; frozen plab seed=42")
prov=F.Prov("E3_runtime_memory", os.path.abspath(__file__), config=cfg, seed="deterministic (frozen plab seed=42)",
            note="Timed methods reproduce frozen g1 M0/M2/M4/M5 and g2 est_warmstart to <1e-6 mm (correctness gate in e3_calibration.json).")
for key,rel in [
 ("predictor_frozen",r"structured_mismatch_phase0\scripts\cache\rescue\VI_ONLY_PREDICTOR_FROZEN.npz"),
 ("model_cache",r"structured_mismatch_phase0\scripts\cache\model_cache.npz"),
 ("patches",r"structured_mismatch_phase0\scripts\cache\patches.npz"),
 ("roster",r"revision_experiments\final_targeted\initialization_frames.json"),
 ("g1_fidelity",r"g_chain\G1_MITIGATION\results\g1_oracle_vi.csv"),
 ("g2_fidelity",r"g_chain\G2_ESTIMATED_VIEW\results\g2_vi.csv")]:
    prov.add_input(key,os.path.join(F.ROOT,rel))
outs=sorted(p for p in glob.glob(os.path.join(F.E3_OUT,"*")) if os.path.isfile(p)
            and os.path.basename(p)!="e3_provenance.json" and not p.endswith(".py"))
prov.finish(os.path.join(F.E3_OUT,"e3_provenance.json"),outs)
print("E3 provenance:",len(outs),"outputs")
for p in outs: print("  out",os.path.basename(p))
