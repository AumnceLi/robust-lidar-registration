# -*- coding: utf-8 -*-
"""e3_core.py -- frozen method stage runners for the runtime/memory benchmark (E3).

NO algorithm change: every registration is g_common.robust_icp with frozen arguments; the only
instrumentation is perf_counter around the SAME stages the frozen pipelines perform, and single
thread pinning (f3 OneThreadTree / BLAS threads=1).

Stage decomposition (matches g1_run / g2_run frozen flow):
  Raw / Huber            : reusable raw model+tree; registration1 only.
  Patch / PatchHuber     : reusable corrected model+tree (built ONCE); registration1 only.
  Full                   : per-frame view query -> corrected-model build -> KD-tree -> registration1.
  EstimatedFull          : registration1 (frozen raw nominal) -> estimated-view query -> corrected
                           model build -> KD-tree -> registration2 (warm-started, clip_basin=False).
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

import os, sys, time
for _v in ["OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"]:
    os.environ[_v] = "1"
os.cpu_count = lambda: 1
import numpy as np
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F
G = F.G
METHODS = ["Raw", "Huber", "Patch", "PatchHuber", "Full", "EstimatedFull"]


def build_env():
    fz = F.Rv.frozen_bundle()
    model, normals, plab = fz["model"], fz["normals"], fz["plab"]
    Vmean, Vcnt, vr, uv = fz["Vmean"], fz["Vcnt"], fz["vrange"], fz["uview"]
    mu_global, mu_patch = G.hierarchy_library(Vmean, Vcnt)
    env = dict(fz=fz, model=model, normals=normals, plab=plab, sf=fz["s_floor"],
               Vmean=Vmean, Vcnt=Vcnt, vr=vr, uv=uv, mu_global=mu_global, mu_patch=mu_patch,
               tree_raw=F.kdtree1(model), model_patch=model + mu_patch[plab])
    env["tree_patch"] = F.kdtree1(env["model_patch"])
    return env


def _ms(t0, t1):
    return (t1 - t0) * 1000.0


def stage_run(method, P, view, env):
    """Return (stage_ms dict, result dict et/eR/iters). Timed on a single cold call."""
    model, normals, plab = env["model"], env["normals"], env["plab"]
    Vmean, Vcnt, vr, uv = env["Vmean"], env["Vcnt"], env["vr"], env["uv"]
    mu_global, mu_patch, sf = env["mu_global"], env["mu_patch"], env["sf"]
    zr, zu, t_gt, R_gt = view
    s = dict(model_build_ms=0.0, query_ms=0.0, kdtree_ms=0.0,
             registration1_ms=0.0, registration2_ms=0.0, total_ms=0.0)
    t_start = time.perf_counter()
    if method == "Raw":
        t0 = time.perf_counter(); r = G.robust_icp(model, normals, env["tree_raw"], P, "p2p", "ls", s_floor=sf)
        s["registration1_ms"] = _ms(t0, time.perf_counter())
    elif method == "Huber":
        t0 = time.perf_counter(); r = G.robust_icp(model, normals, env["tree_raw"], P, "p2p", "huber", s_floor=sf)
        s["registration1_ms"] = _ms(t0, time.perf_counter())
    elif method == "Patch":
        t0 = time.perf_counter(); r = G.robust_icp(env["model_patch"], normals, env["tree_patch"], P, "p2p", "ls", s_floor=sf)
        s["registration1_ms"] = _ms(t0, time.perf_counter())
    elif method == "PatchHuber":
        t0 = time.perf_counter(); r = G.robust_icp(env["model_patch"], normals, env["tree_patch"], P, "p2p", "huber", s_floor=sf)
        s["registration1_ms"] = _ms(t0, time.perf_counter())
    elif method == "Full":
        t0 = time.perf_counter(); mu, _ = G.mu_for_view(Vmean, Vcnt, vr, uv, zr, zu); s["query_ms"] = _ms(t0, time.perf_counter())
        t0 = time.perf_counter(); mfull = G.corrected_model(model, plab, mu_global, mu_patch, mu, "full"); s["model_build_ms"] = _ms(t0, time.perf_counter())
        t0 = time.perf_counter(); tr = F.kdtree1(mfull); s["kdtree_ms"] = _ms(t0, time.perf_counter())
        t0 = time.perf_counter(); r = G.robust_icp(mfull, normals, tr, P, "p2p", "ls", s_floor=sf)
        s["registration1_ms"] = _ms(t0, time.perf_counter())
    elif method == "EstimatedFull":
        t0 = time.perf_counter(); xi0 = G.robust_icp(model, normals, env["tree_raw"], P, "p2p", "ls", s_floor=sf)["xi"]
        s["registration1_ms"] = _ms(t0, time.perf_counter())
        r0, u0 = G.estimated_view(t_gt, R_gt, xi0)
        t0 = time.perf_counter(); mu, _ = G.mu_for_view(Vmean, Vcnt, vr, uv, r0, u0); s["query_ms"] = _ms(t0, time.perf_counter())
        t0 = time.perf_counter(); mest = G.corrected_model(model, plab, mu_global, mu_patch, mu, "full"); s["model_build_ms"] = _ms(t0, time.perf_counter())
        t0 = time.perf_counter(); tr = F.kdtree1(mest); s["kdtree_ms"] = _ms(t0, time.perf_counter())
        t0 = time.perf_counter()
        r = G.robust_icp(mest, normals, tr, P, "p2p", "ls", s_floor=sf, x0=xi0, clip_basin=False)
        s["registration2_ms"] = _ms(t0, time.perf_counter())
    else:
        raise ValueError(method)
    xi = r["xi"]
    res = dict(et_mm=float(np.linalg.norm(xi[:3]) * 1000.0),
               eR_deg=float(np.degrees(np.linalg.norm(xi[3:]))), iters=int(r["iters"]),
               on_bound=int(r["on_bound"]))
    s["total_ms"] = _ms(t_start, time.perf_counter())
    return s, res
