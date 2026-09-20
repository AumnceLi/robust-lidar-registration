# -*- coding: utf-8 -*-
"""E3 memory worker: run ONE method in a FRESH process over the 80-frame roster once, and report
process RSS baseline/peak/delta plus tracemalloc Python-allocation peak. A fresh process per method
gives a clean, comparable peak without cross-method object contamination."""
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

import os, sys, gc, json, argparse, tracemalloc
for _v in ["OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"]:
    os.environ[_v] = "1"
os.cpu_count = lambda: 1
import psutil
sys.path.insert(0, _pp("final_three_experiments/03_runtime_memory"))
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F
import e3_core as E


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--method", required=True)
    a = ap.parse_args()
    proc = psutil.Process(os.getpid())
    env = E.build_env()
    gc.collect()
    baseline_mb = proc.memory_info().rss / 1e6
    tracemalloc.start()
    peak_mb = baseline_mb
    tasks = F.roster_tasks()
    for traj, order in tasks:
        P = F.Rv.load_aligned(traj, order)
        view = F.view_geometry(traj, order)
        _, _ = E.stage_run(a.method, P, view, env)
        cur = proc.memory_info().rss / 1e6
        peak_mb = max(peak_mb, cur)
    _, py_peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    out = dict(method=a.method, n_frames=len(tasks),
               baseline_after_common_load_mb=round(baseline_mb, 2),
               peak_rss_mb=round(peak_mb, 2), delta_rss_mb=round(peak_mb - baseline_mb, 2),
               tracemalloc_python_peak_mb=round(py_peak / 1e6, 3))
    print("JSON_RESULT " + json.dumps(out))


if __name__ == "__main__":
    main()
