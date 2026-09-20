# -*- coding: utf-8 -*-
"""E2 provenance."""
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
 "python e2_run_lobo.py     # 6-fold LOBO, full 501 OOF registrations; --nw default=20",
 "python e2_analyze.py",
]
cfg=dict(
 design="6-fold leave-one-block-out over frozen VI contiguous blocks",
 block_ranges={0:"[0,70)",1:"[70,140)",2:"[140,219)",3:"[219,315)",4:"[315,418)",5:"[418,501)"},
 block_sizes=[70,70,79,96,103,83],
 partition="FROZEN plab k=24 (normal weight 0.30, MiniBatchKMeans seed42); NOT re-clustered per fold",
 field_rule="per-fold mu_j = g_common.hierarchy_library point-weighted mean over the 5 training blocks only",
 leakage_assertions=["set(train).isdisjoint(test)","union==all 501","mu_j == independent train-only point-weighted mean"],
 methods=["Raw","Huber","PatchOOF","PatchHuberOOF","PatchFullFit(in-sample comparator)"],
 bootstrap="block-of-6-blocks + frame moving-block L=5/10/20, B=2000, seed=42; block sign-flip L=5",
 decision_rule="OOF benefit<=0 or <3/6 positive => VI_INTERNAL_GENERALIZATION_WARNING (fixed before result)",
 seed="42 (bootstrap); deterministic registration; frozen plab seed=42",
 workers=20, blas_threads=1, kdtree_query_threads=1)
prov=F.Prov("E2_VI_leave_one_block_out", os.path.abspath(__file__), config=cfg, seed="42 bootstrap / deterministic registration",
            note="Each VI scan scored once under the fold that held its block; OOF Patch reproduces frozen g1 M4 to 2.8e-14 mm.")
for key,rel in [
 ("predictor_frozen",r"structured_mismatch_phase0\scripts\cache\rescue\VI_ONLY_PREDICTOR_FROZEN.npz"),
 ("model_cache",r"structured_mismatch_phase0\scripts\cache\model_cache.npz"),
 ("patches",r"structured_mismatch_phase0\scripts\cache\patches.npz"),
 ("g1_vi_fidelity",r"g_chain\G1_MITIGATION\results\g1_oracle_vi.csv")]:
    prov.add_input(key,os.path.join(F.ROOT,rel))
outs=sorted(p for p in glob.glob(os.path.join(F.E2_OUT,"*")) if os.path.isfile(p)
            and os.path.basename(p)!="e2_provenance.json" and not p.endswith(".py"))
prov.finish(os.path.join(F.E2_OUT,"e2_provenance.json"),outs)
print("E2 provenance:",len(outs),"outputs")
for p in outs: print("  out",os.path.basename(p))
