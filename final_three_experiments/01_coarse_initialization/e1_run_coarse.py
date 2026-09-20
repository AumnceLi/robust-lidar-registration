# -*- coding: utf-8 -*-
"""E1 production runner -- NEW coarse levels L4/L5/L6 ONLY.

L0(reference)+L1+L2+L3 are REUSED byte-for-byte from the existing local experiment
(final_targeted/initialization_sensitivity_framewise.csv) and are NOT regenerated here. This script
adds the three coarse levels with the SAME 4 sign-balanced deterministic directions, the SAME
cyclic rotation-axis pairing and the SAME instrumented frozen solver (t3_common.inst_icp). No solver,
safeguard, iteration budget or method definition is changed. L7 (500 mm/20 deg) is deliberately not
run: its 0.50 m start already exceeds the frozen 0.30 m translation safeguard.

Output: e1_coarse_L4L6_framewise.csv  (80 frames x 4 methods x 3 levels x 4 dirs = 3840 rows)
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

import os, sys, time, argparse
for _v in ["OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F
T = F.T
NW_DEFAULT = min(20, os.cpu_count() or 4)


def _one_frame(args):
    traj, order = args
    P = F.Rv.load_aligned(traj, order)
    rows = []
    for method in F.METHODS4:
        ref = T.inst_icp(method, P, x0=None)
        for lv in F.NEW_COARSE:
            t_mm, r_deg = F.LEVELS[lv]
            for did in F.DIR_IDS:
                x0 = F.perturb_x0(lv, did)
                r = T.inst_icp(method, P, x0=x0)
                rows.append(dict(
                    trajectory=traj, frame_id=int(order), method=method, perturbation_level=lv,
                    direction_id=did, translation_init_mm=float(t_mm), rotation_init_deg=float(r_deg),
                    final_translation_error_mm=r["final_translation_error_mm"],
                    final_rotation_error_deg=r["final_rotation_error_deg"],
                    iterations=r["iterations"], termination_reason=r["termination_reason"],
                    hit_iteration_cap=int(r["hit_iteration_cap"]),
                    hit_translation_boundary=int(r["hit_translation_boundary"]),
                    hit_rotation_boundary=int(r["hit_rotation_boundary"]),
                    final_objective=r["final_objective"],
                    ref_translation_error_mm=ref["final_translation_error_mm"],
                    ref_rotation_error_deg=ref["final_rotation_error_deg"],
                    delta_init_t_mm=r["final_translation_error_mm"] - ref["final_translation_error_mm"],
                    delta_init_r_deg=r["final_rotation_error_deg"] - ref["final_rotation_error_deg"],
                    posthoc=int(traj == "III")))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nw", type=int, default=NW_DEFAULT)
    a = ap.parse_args()
    tasks = F.roster_tasks()
    assert len(tasks) == 80, len(tasks)
    t0 = time.perf_counter(); all_rows = []
    with ProcessPoolExecutor(max_workers=a.nw, initializer=F.single_thread_worker) as ex:
        for k, rows in enumerate(ex.map(_one_frame, tasks, chunksize=2)):
            all_rows.extend(rows)
            if (k + 1) % 10 == 0:
                print(f"  {k+1}/80 frames  {time.perf_counter()-t0:.0f}s", flush=True)
    df = pd.DataFrame(all_rows)
    exp = len(df)
    assert exp == 80 * 4 * 3 * 4, exp
    for lv in F.NEW_COARSE:
        assert (df.perturbation_level == lv).sum() == 1280
    out = os.path.join(F.E1_OUT, "e1_coarse_L4L6_framewise.csv")
    df.to_csv(out, index=False)
    print(f"wrote {out} rows={len(df)} in {time.perf_counter()-t0:.0f}s workers={a.nw}")


if __name__ == "__main__":
    main()
