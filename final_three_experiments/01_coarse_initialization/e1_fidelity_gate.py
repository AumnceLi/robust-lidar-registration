# -*- coding: utf-8 -*-
"""E1 FIDELITY GATE (run before combining): reproduce EVERY reused L0-L3 row with the new code path
(f3_common.perturb_x0 + the same instrumented frozen solver t3_common.inst_icp) and assert bit-exact
equality with the shipped final_targeted/initialization_sensitivity_framewise.csv.

This is a VERIFICATION artifact: the canonical E1 framewise table REUSES the shipped L0-L3 bytes;
this gate only proves the new runner uses an identical solver / perturbation family before L4-L6
are appended. Writes e1_fidelity_gate.json + .txt; raises (non-zero exit) on any mismatch.
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

import os, sys, time, json
for _v in ["OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F
T = F.T
REUSED = os.path.join(F.ROOT, "revision_experiments", "final_targeted",
                      "initialization_sensitivity_framewise.csv")


def _one_frame(args):
    traj, order, levels = args
    P = F.Rv.load_aligned(traj, order)
    out = []
    for method in F.METHODS4:
        # reference (L0)
        r = T.inst_icp(method, P, x0=None)
        out.append((traj, order, method, "reference", "none", r))
        for lv in levels:
            for did in F.DIR_IDS:
                r = T.inst_icp(method, P, x0=F.perturb_x0(lv, did))
                out.append((traj, order, method, lv, did, r))
    return out


def main():
    reused = pd.read_csv(REUSED)
    levels = ["L1", "L2", "L3"]
    tasks = [(tr, int(o), levels) for tr in F.TRAJS
             for o in F.load_roster()["trajectories"][tr]["selected_order"]]
    t0 = time.perf_counter(); recs = []
    with ProcessPoolExecutor(max_workers=min(20, os.cpu_count() or 4), initializer=F.single_thread_worker) as ex:
        for k, rows in enumerate(ex.map(_one_frame, tasks, chunksize=2)):
            recs.extend(rows)
            if (k + 1) % 20 == 0: print(f"  {k+1}/80 {time.perf_counter()-t0:.0f}s", flush=True)
    nr = pd.DataFrame([dict(trajectory=t, frame_id=o, method=m, perturbation_level=lv, direction_id=d,
                            et=r["final_translation_error_mm"], eR=r["final_rotation_error_deg"],
                            it=r["iterations"], term=r["termination_reason"],
                            bT=int(r["hit_translation_boundary"]), bR=int(r["hit_rotation_boundary"]),
                            cap=int(r["hit_iteration_cap"]), obj=r["final_objective"])
                       for (t, o, m, lv, d, r) in recs])
    m = reused.merge(nr, on=["trajectory","frame_id","method","perturbation_level","direction_id"],
                     suffixes=("_old","_new"), validate="one_to_one")
    assert len(m) == len(reused) == len(nr), (len(m), len(reused), len(nr))
    max_et = float(np.nanmax(np.abs(m.final_translation_error_mm - m.et)))
    max_eR = float(np.nanmax(np.abs(m.final_rotation_error_deg - m.eR)))
    max_obj = float(np.nanmax(np.abs(m.final_objective.fillna(0) - m.obj.fillna(0))))
    it_mis = int((m.iterations != m.it).sum())
    term_mis = int((m.termination_reason != m.term).sum())
    bT_mis = int((m.hit_translation_boundary != m.bT).sum())
    bR_mis = int((m.hit_rotation_boundary != m.bR).sum())
    cap_mis = int((m.hit_iteration_cap != m.cap).sum())
    gate = dict(compared_rows=int(len(m)), max_abs_et_diff=max_et, max_abs_eR_diff=max_eR,
                max_abs_objective_diff=max_obj, iter_mismatches=it_mis, termination_mismatches=term_mis,
                boundT_mismatches=bT_mis, boundR_mismatches=bR_mis, cap_mismatches=cap_mis,
                rerun_seconds=round(time.perf_counter()-t0, 2))
    # cross-process float reproducibility tolerance (repo replay gate uses 1e-6; we demand 1e-9 mm/deg);
    # iteration count / termination / safeguard / cap flags must match EXACTLY.
    passed = (max_et < 1e-9 and max_eR < 1e-9 and max_obj < 1e-9 and it_mis == 0 and term_mis == 0 and
              bT_mis == 0 and bR_mis == 0 and cap_mis == 0)
    gate["tolerance"] = "float <1e-9 mm/deg (observed ~1e-14); categorical exact"
    gate["PASSED"] = bool(passed)
    with open(os.path.join(F.E1_OUT, "e1_fidelity_gate.json"), "w") as f:
        json.dump(gate, f, indent=2)
    lines = ["E1 FIDELITY GATE — new path vs shipped L0-L3 framewise",
             f"compared rows: {gate['compared_rows']}",
             f"max |delta et| = {max_et:.3e} mm ; max |delta eR| = {max_eR:.3e} deg ; "
             f"max |delta objective| = {max_obj:.3e}",
             f"mismatches iters={it_mis} termination={term_mis} boundT={bT_mis} boundR={bR_mis} cap={cap_mis}",
             f"PASSED = {passed}  ({gate['rerun_seconds']}s)"]
    txt = "\n".join(lines)
    open(os.path.join(F.E1_OUT, "e1_fidelity_gate.txt"), "w").write(txt + "\n")
    print(txt)
    if not passed:
        raise SystemExit("E1 FIDELITY GATE FAILED — refusing to extend")


if __name__ == "__main__":
    main()
