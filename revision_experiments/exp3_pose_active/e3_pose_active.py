# -*- coding: utf-8 -*-
"""Experiment 3 (Phase-1): DIRECT validation of the pose-active projection (paper Eq.12-16 ==
notation.md Sec.3 / derivation A2-A3 / t5_mechanism_link.pose_active; no mathematical redefinition).

For every analysed REAL frame we compute, on the SAME fixed GT correspondence at xi=0:
  ordinary residual RMS, RMS_PA, fixed-corr J/W/H=J^TWJ/g=J^TWd, translation & rotation gradient
  blocks, dxi_FO=-H^dag g, delta_PA=P_{J,W}delta, rank/singular values/condition/pinv threshold;
alongside the REMATCHING finite-difference quantities g_FD,B_FD,-B_FD^dag g_FD (cached for
VI/IV/II; computed with the FROZEN m_common Objective for III, which has no objective cache) and the
ACTUAL local displacement xi* reached from the reference init.
Real coverage: VI all 501; IV/II/III all frozen in-support frames. Synthetic 1920-run intermediates
are NOT cached -> documented BLOCKED (no regeneration)."""
import os
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
import sys, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import rev_common as Rv  # noqa
import m_common as M    # noqa (frozen FD objective / local solver)

KINDS = [("p2p", 0), ("p2l", 1)]
RCONDS = [1e-10, 1e-8, 1e-6]


def load_fd_cache(traj):
    cfg = Rv.REG[traj]
    if cfg["obj"] is None:
        return None
    z = np.load(cfg["obj"])
    return dict(g=z["raw__g"], H=z["raw__H"], dhat=z["raw__dhat"],
                xistar=z["raw__xistar"], iters=z["raw__iters"])


def fd_for_iii(OBJ, P):
    """Frozen rematching finite-difference g_FD/B_FD and actual local xi* (mirrors r7_ext_objective)."""
    gh = M.grad_hess(OBJ, P)
    out = {}
    out[("p2p", "g")] = gh["gp"]; out[("p2p", "H")] = gh["Hp"]
    out[("p2l", "g")] = gh["gl"]; out[("p2l", "H")] = gh["Hl"]
    out[("p2p", "xi")] = M.local_min_p2p(OBJ, P)["xi"]
    out[("p2l", "xi")] = M.local_min_p2l(OBJ, P)["xi"]
    return out


def rcond_sensitivity(H, g, dfo_default):
    res = {}
    for rc in RCONDS:
        Hinv = np.linalg.pinv(H, rcond=rc)
        d = -Hinv @ g
        res[f"fo_dircos_vs_default@rcond{rc:g}"] = Rv.cosine(d[:3], dfo_default[:3])
        res[f"rank@rcond{rc:g}"] = int(np.linalg.matrix_rank(H, tol=np.linalg.svd(H, compute_uv=False)[0] * rc))
    return res


def main():
    fz = Rv.frozen_bundle()
    model, NM, tree = fz["model"], fz["normals"], fz["tree_model"]
    # correspondence-switch rate from Exp.2 diagnostic frames (Raw, budget 40)
    sw = pd.read_csv(os.path.join(Rv.OUTROOT, "exp2_iter_budget", "iteration_budget_framewise.csv"))
    sw = sw[(sw.method == "Raw") & (sw.max_iterations == 40)][["trajectory", "frame_id", "correspondence_switch_rate"]]
    swmap = {(r.trajectory, int(r.frame_id)): r.correspondence_switch_rate for r in sw.itertuples()}

    rows, checks = [], []
    t_iii = None
    for traj in Rv.TRAJS:
        insup = Rv.support_mask(traj)
        fd = load_fd_cache(traj)
        obj_iii = None
        if fd is None:
            obj_iii = M.Objective()
            t_iii = time.perf_counter()
        # VI: all frames (FD cache present); IV/II/III: frozen in-support frames only
        if traj == "VI":
            order_list = list(range(Rv.REG[traj]["n"]))
        else:
            order_list = [i for i in range(Rv.REG[traj]["n"]) if insup[i]]
        for k, order in enumerate(order_list):
            z = Rv.load_scan_npz(traj, order)
            P = np.asarray(z["aligned"], float); nn = np.asarray(z["nnidx"], int)
            pa = Rv.fixed_corr_pose_active(P, model, tree, NM, nn=nn)
            fdiii = fd_for_iii(obj_iii, P) if fd is None else None
            for kind, ch in KINDS:
                b = pa[kind]
                g_an, H_an = b["g"], b["H"]; dfo = b["dfo"]
                # --- rematching FD quantities
                if fd is not None:
                    g_fd = fd["g"][order, :, ch]; H_fd = fd["H"][order, :, :, ch]
                    xi_star = fd["xistar"][order, :, ch]; fd_iters = int(fd["iters"][order, ch])
                    d_fd_cached = fd["dhat"][order, :, ch]
                else:
                    g_fd = fdiii[(kind, "g")]; H_fd = fdiii[(kind, "H")]
                    xi_star = fdiii[(kind, "xi")]; fd_iters = -1; d_fd_cached = None
                d_fd = -np.linalg.pinv(H_fd) @ g_fd
                # factor-2 analytic-vs-FD gradient check (FD of mean-squared objective = 2 J^TWd)
                fac2 = float(np.max(np.abs(2 * g_an - g_fd)))
                idem = (Rv.projector_idempotence_p2p(P, b["Hpinv"], g_an) if kind == "p2p"
                        else Rv.projector_idempotence_p2l(P, NM[nn], b["Hpinv"], g_an))
                pjw_diff = float(abs(b["rms_pa"] - b["pjw_check"]))
                at, ar = xi_star[:3], xi_star[3:]
                row = dict(trajectory=traj, order=order, kind=kind, n_points=len(P),
                           in_support=bool(insup[order]), posthoc=int(Rv.REG[traj].get("posthoc", False)),
                           rms_mm=b["rms"] * 1000, rms_pa_mm=b["rms_pa"] * 1000,
                           ratio_pa=b["ratio_pa"],
                           grad_t_norm_mm=b["gt_norm"] * 1000, grad_r_norm=b["gr_norm"],
                           rank=b["rank_default"], cond=b["cond"],
                           sv_min=b["sv"][-1], sv_max=b["sv"][0],
                           actual_t_mm=np.linalg.norm(at) * 1000, actual_r_deg=np.degrees(np.linalg.norm(ar)),
                           an_t_mm=np.linalg.norm(dfo[:3]) * 1000, an_r_deg=np.degrees(np.linalg.norm(dfo[3:])),
                           fd_t_mm=np.linalg.norm(d_fd[:3]) * 1000, fd_r_deg=np.degrees(np.linalg.norm(d_fd[3:])),
                           an_dircos_t=Rv.cosine(dfo[:3], at), fd_dircos_t=Rv.cosine(d_fd[:3], at),
                           an_dircos_r=Rv.cosine(dfo[3:], ar), fd_dircos_r=Rv.cosine(d_fd[3:], ar),
                           an_magratio_t=(np.linalg.norm(dfo[:3]) / (np.linalg.norm(at) + 1e-15)),
                           fd_magratio_t=(np.linalg.norm(d_fd[:3]) / (np.linalg.norm(at) + 1e-15)),
                           fd_iters=fd_iters,
                           switch_rate=swmap.get((traj.upper() if traj != "III" else "III", order), np.nan))
                row.update(rcond_sensitivity(H_an, g_an, dfo))
                rows.append(row)
                chk = dict(trajectory=traj, order=order, kind=kind,
                           idempotence_P2_rel=idem, normal_eq_resid_rel=b["ne_resid"],
                           pjw_identity_abs_diff_mm=pjw_diff * 1000,
                           factor2_grad_maxdiff=fac2,
                           fd_step_vs_cached_maxdiff=(float(np.max(np.abs(d_fd - d_fd_cached)))
                                                      if d_fd_cached is not None else np.nan))
                checks.append(chk)
        if fd is None:
            print(f"[E3] {traj}: FD computed for {len(order_list)} frames in {time.perf_counter()-t_iii:.0f}s", flush=True)
        else:
            print(f"[E3] {traj}: {len(order_list)} frames (cached FD)", flush=True)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(HERE, "pose_active_direct_framewise.csv"), index=False)
    ck = pd.DataFrame(checks); ck.to_csv(os.path.join(HERE, "pose_active_numerical_checks.csv"), index=False)
    print("\n=== numerical self-consistency (worst case across all frames) ===")
    for c in ["idempotence_P2_rel", "normal_eq_resid_rel", "pjw_identity_abs_diff_mm",
              "factor2_grad_maxdiff", "fd_step_vs_cached_maxdiff"]:
        print(f"  {c}: max={ck[c].max():.3e} median={ck[c].median():.3e}")
    print("\n=== p2p direction-cosine / magnitude summary by trajectory ===")
    p = df[df.kind == "p2p"]
    print(p.groupby("trajectory")[["ratio_pa", "an_dircos_t", "fd_dircos_t", "an_magratio_t",
                                   "fd_magratio_t", "cond"]].median().to_string())


if __name__ == "__main__":
    main()
