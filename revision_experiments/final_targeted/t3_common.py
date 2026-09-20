# -*- coding: utf-8 -*-
"""t3_common.py -- frozen-solver plumbing for the LOCAL initialization sensitivity (Task 3).

The instrumented solver below is operationally IDENTICAL to the frozen g_common.robust_icp
(same correspondence NN, same per-correspondence weights, same weighted Kabsch, same basin clip
rule/order, same objective definition, same tol, same 40-iteration main budget); it only (a) accepts
an SE(3) local-chart warm start x0=[t(m), r(rad)] via the SAME rodrigues exponential used by the
frozen solver (no ad-hoc Euler addition), and (b) records iterations / termination reason / which
basin bound was active. A hard validation gate (t3_solver_check.py) checks it against robust_icp and
the frozen replay79 at x0=None before any perturbed run is trusted.
"""
import os
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys, json, time
import numpy as np
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))   # revision_experiments (for rev_common)
import rev_common as Rv
M = Rv.M; G = Rv.G

METHODS = ["Raw", "Huber", "Patch", "PatchHuber"]
LEVELS = {"L1": (10.0, 0.5), "L2": (30.0, 1.0), "L3": (50.0, 2.0)}     # (mm, deg)
DIR_IDS = ["v1", "v2", "v3", "v4"]
DIRS = {"v1": np.array([1., 1., 1.]), "v2": np.array([1., -1., -1.]),
        "v3": np.array([-1., 1., -1.]), "v4": np.array([-1., -1., 1.])}
DIRS = {k: v / np.linalg.norm(v) for k, v in DIRS.items()}
ROT_PAIR = {"v1": "v2", "v2": "v3", "v3": "v4", "v4": "v1"}

_G = {}
def init_worker():
    fz = Rv.frozen_bundle()
    _G.update(model=fz["model"], normals=fz["normals"], s_floor=fz["s_floor"],
              tree_raw=fz["tree_model"], mpatch=fz["model_patch"], tree_patch=fz["tree_patch"])

def _target(method):
    if method in ("Raw", "Huber"):
        return _G["model"], _G["tree_raw"], "huber" if method == "Huber" else "ls"
    return _G["mpatch"], _G["tree_patch"], "huber" if method == "PatchHuber" else "ls"


def inst_icp(method, P, x0=None, max_iter=G.MAX_ITER):
    """Instrumented copy of g_common.robust_icp(kind='p2p') with warm start + diagnostics."""
    target, tree, formulation = _target(method)
    normals = _G["normals"]; s_floor = _G["s_floor"]
    bound_t, bound_r_deg = G.BASIN_T, G.BASIN_R_DEG
    br = np.deg2rad(bound_r_deg)
    if x0 is None:
        Racc, tacc = np.eye(3), np.zeros(3)
    else:
        tacc = np.asarray(x0[:3], float).copy()
        Racc = M.rodrigues(np.asarray(x0[3:], float))
    tol = G.TOL_P2P
    hit_t = hit_r = False; termination = "cap"; hist = []
    for it in range(max_iter):
        Q = (Racc @ P.T).T + tacc
        _, idx = tree.query(Q, k=1, workers=-1)
        m = target[idx]; e = Q - m
        metric = np.linalg.norm(e, axis=1)
        if formulation == "ls":
            w = np.ones(len(P))
        elif formulation == "huber":
            w, _ = G.huber_weights(metric, G.HUBER_DELTA, s_floor)
        else:
            raise ValueError(formulation)
        Rd, vd = G.weighted_kabsch(Q, m, w)
        Rn = Rd @ Racc; tn = Rd @ tacc + vd
        nt = np.linalg.norm(tn); nr = np.linalg.norm(M.rodrigues_log(Rn)); f = 1.0
        if nt > bound_t: f = min(f, bound_t / nt); hit_t = True
        if nr > br:      f = min(f, br / nr);      hit_r = True
        if f < 1.0:
            tacc = tacc + f * (tn - tacc)           # frozen rule: partial t move, R not updated, break
            termination = "boundary"; break
        Racc, tacc = Rn, tn
        Qn = (Rd @ Q.T).T + vd; en = Qn - target[idx]
        r2 = np.einsum("ij,ij->i", en, en)
        J = float((w * r2).sum() / w.sum()); hist.append(J)
        if it > 0 and abs(hist[-2] - J) < tol * max(1, hist[-2]):
            termination = "tol"; break
    actual = it + 1
    xi = M.se3_log(Racc, tacc)
    return dict(final_translation_error_mm=float(np.linalg.norm(xi[:3]) * 1000.0),
                final_rotation_error_deg=float(np.degrees(np.linalg.norm(xi[3:]))),
                iterations=int(actual), termination_reason=termination,
                hit_iteration_cap=bool(termination == "cap" and actual == max_iter),
                hit_translation_boundary=bool(hit_t and termination == "boundary"),
                hit_rotation_boundary=bool(hit_r and termination == "boundary"),
                final_objective=float(hist[-1]) if hist else np.nan, xi=xi)


def perturb_x0(level, dir_id):
    t_mm, r_deg = LEVELS[level]
    tv = DIRS[dir_id]; rv = DIRS[ROT_PAIR[dir_id]]
    x0 = np.concatenate([(t_mm / 1000.0) * tv, np.deg2rad(r_deg) * rv])
    return x0


def load_selection():
    return json.load(open(os.path.join(_HERE, "initialization_frames.json")))
