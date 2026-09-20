# -*- coding: utf-8 -*-
"""TASK 3 production -- 80 frames x (3 levels x 4 directions) x 4 methods = 3840 perturbed runs,
plus 80 x 4 = 320 reference (GT-init) runs. Frozen solver, frozen settings; only the LOCAL initial
pose changes. Identical x0 is used for all four methods at a frame/level/direction. Deterministic
(no RNG in the ICP); no iteration budget is raised for failed cases. Writes the framewise CSV."""
import os, sys, time, json
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd
import t3_common as T
import rev_common as Rv

NW = min(8, os.cpu_count() or 4)


def _one_frame(args):
    traj, order = args
    P = Rv.load_aligned(traj, order)
    rows = []
    for method in T.METHODS:
        ref = T.inst_icp(method, P, x0=None)
        rows.append(dict(trajectory=traj, frame_id=int(order), method=method,
                         perturbation_level="reference", direction_id="none",
                         translation_init_mm=0.0, rotation_init_deg=0.0,
                         final_translation_error_mm=ref["final_translation_error_mm"],
                         final_rotation_error_deg=ref["final_rotation_error_deg"],
                         iterations=ref["iterations"], termination_reason=ref["termination_reason"],
                         hit_iteration_cap=int(ref["hit_iteration_cap"]),
                         hit_translation_boundary=int(ref["hit_translation_boundary"]),
                         hit_rotation_boundary=int(ref["hit_rotation_boundary"]),
                         final_objective=ref["final_objective"],
                         ref_translation_error_mm=ref["final_translation_error_mm"],
                         ref_rotation_error_deg=ref["final_rotation_error_deg"],
                         delta_init_t_mm=0.0, delta_init_r_deg=0.0,
                         posthoc=int(traj in Rv.TRAJS and traj == "III")))
        for lv in ["L1", "L2", "L3"]:
            t_mm, r_deg = T.LEVELS[lv]
            for did in T.DIR_IDS:
                x0 = T.perturb_x0(lv, did)
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
    sel = T.load_selection()
    tasks = [(tr, int(o)) for tr in Rv.TRAJS
             for o in sel["trajectories"][tr]["selected_order"]]
    assert len(tasks) == 80, len(tasks)
    t0 = time.perf_counter(); all_rows = []
    with ProcessPoolExecutor(max_workers=NW, initializer=T.init_worker) as ex:
        for k, rows in enumerate(ex.map(_one_frame, tasks, chunksize=2)):
            all_rows.extend(rows)
            if (k + 1) % 10 == 0:
                print(f"  {k+1}/80 frames  {time.perf_counter()-t0:.0f}s", flush=True)
    df = pd.DataFrame(all_rows)
    # exact expected counts
    pert = df[df.perturbation_level != "reference"]
    ref = df[df.perturbation_level == "reference"]
    assert len(pert) == 3840, len(pert)
    assert len(ref) == 320, len(ref)
    df.to_csv(os.path.join(T._HERE, "initialization_sensitivity_framewise.csv"), index=False)
    print(f"wrote initialization_sensitivity_framewise.csv rows={len(df)} "
          f"(perturbed {len(pert)}, reference {len(ref)}) in {time.perf_counter()-t0:.0f}s, workers={NW}")


if __name__ == "__main__":
    main()
