# -*- coding: utf-8 -*-
"""Step 2b: iteration-budget sensitivity, Raw and Patch ONLY (first round).
Everything frozen except max_iterations in {40,80,160}: same frames/init (GT xi=0)/correspondence
(NN)/distance rule/boundary rule/Patch field/robust (LS)/stopping tolerance. Instrumented solver is
bit-faithful to g_common.robust_icp (verified xi diff = 0 at budget 40)."""
import os, json
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import rev_common as Rv  # noqa

BUDGETS = [40, 80, 160]
METHODS = ["Raw", "Patch"]


def main():
    fz = Rv.frozen_bundle()
    model, tree = fz["model"], fz["tree_model"]
    mpatch, tp = fz["model_patch"], fz["tree_patch"]
    plan = json.load(open(os.path.join(HERE, "diagnostic_frames.json")))
    rows, hist = [], {}
    for tr in Rv.TRAJS:
        sel = plan["trajectories"][tr]["selected_order"]
        real = Rv.realized_pose_errors(tr)
        for order in sel:
            P = Rv.load_aligned(tr, order)
            for method in METHODS:
                tgt, tr_ = (model, tree) if method == "Raw" else (mpatch, tp)
                for b in BUDGETS:
                    r = Rv.instrumented_p2p_icp(tgt, tr_, P, b)
                    sh = real.get(order, {})
                    ship_et = sh.get("raw_et" if method == "Raw" else "patch_et", np.nan)
                    ship_it = sh.get("raw_iters" if method == "Raw" else "patch_iters", np.nan)
                    rows.append(dict(
                        trajectory=tr, frame_id=order, scan_id=order, method=method,
                        max_iterations=b, actual_iterations=r["actual_iterations"],
                        termination_reason=r["termination_reason"],
                        hit_iteration_cap=int(r["hit_iteration_cap"]),
                        hit_translation_boundary=int(r["hit_translation_boundary"]),
                        hit_rotation_boundary=int(r["hit_rotation_boundary"]),
                        final_objective=r["final_objective"],
                        objective_change_last_step=r["objective_change_last_step"],
                        pose_change_last_step_translation_mm=r["pose_change_last_step_translation_mm"],
                        pose_change_last_step_rotation_deg=r["pose_change_last_step_rotation_deg"],
                        translation_error_mm=r["translation_error_mm"],
                        rotation_error_deg=r["rotation_error_deg"],
                        correspondence_switch_count=r["correspondence_switch_count"],
                        correspondence_switch_rate=r["correspondence_switch_rate"],
                        posthoc=int(Rv.REG[tr].get("posthoc", False)),
                        shipped_et_mm=ship_et, shipped_iters=ship_it))
                    hist[f"{tr}|{order}|{method}|{b}"] = np.array(
                        [r["hist_J"], r["hist_xi_t"], r["hist_xi_r"]], dtype=object)
            print(f"  {tr} frame {order} done", flush=True)
        print(f"[E2] {tr} done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(HERE, "iteration_budget_framewise.csv"), index=False)
    np.savez_compressed(os.path.join(HERE, "_histories.npz"), **hist)
    # ---- validation that budget=40 reproduces shipped frozen results ----
    b40 = df[df.max_iterations == 40].copy()
    b40["et_diff"] = (b40.translation_error_mm - b40.shipped_et_mm).abs()
    print("\n[VALIDATE budget=40 vs shipped frozen]")
    print("max |et diff| mm =", b40.et_diff.max(),
          " median =", b40.et_diff.median(),
          " n with diff>1e-6 =", int((b40.et_diff > 1e-6).sum()))
    itm = (b40.actual_iterations != b40.shipped_iters)
    print("iters mismatch count =", int(itm.sum()), "of", len(b40))


if __name__ == "__main__":
    main()
