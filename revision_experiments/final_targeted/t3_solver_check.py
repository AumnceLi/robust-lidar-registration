# -*- coding: utf-8 -*-
"""Hard gate BEFORE Task-3 production runs: instrumented solver == frozen robust_icp == replay79."""
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
import numpy as np, pandas as pd
import t3_common as T
import rev_common as Rv
M, G = Rv.M, Rv.G

T.init_worker()
rep = pd.read_csv(Rv.FOLLOWUP if hasattr(Rv, "FOLLOWUP") else
                  _pp("FOLLOWUP_6_9/scripts/replay79_arms.csv"))
rlk = {(r.trajectory, int(r.order), r.arm): (r.et_mm, r.eR_deg, int(r.iters), int(r.on_bound))
       for r in rep.itertuples()}

def frozen_call(method, P, x0=None):
    target, tree, form = T._target(method)
    r = G.robust_icp(target, T._G["normals"], tree, P, "p2p", form,
                     s_floor=T._G["s_floor"], x0=x0)
    return r

# ---- check 1: x0=None identical to G.robust_icp on a spread of frames ----
sel = T.load_selection()
max_xi = 0.0; max_it_mismatch = 0; nchk = 0
frames = [(tr, o) for tr in Rv.TRAJS for o in sel["trajectories"][tr]["selected_order"][:6]]
for tr, o in frames:
    P = Rv.load_aligned(tr, o)
    for method in T.METHODS:
        a = T.inst_icp(method, P, x0=None)
        b = frozen_call(method, P, x0=None)
        max_xi = max(max_xi, float(np.abs(a["xi"] - b["xi"]).max()))
        max_it_mismatch += int(a["iterations"] != int(b["iters"]))
        nchk += 1
print(f"[1] inst vs G.robust_icp x0=None: n={nchk}  max|xi diff|={max_xi:.3e}  iter-mismatch={max_it_mismatch}")

# ---- check 2: warm-start path identical to robust_icp x0=xi0 on random probes ----
max_ws = 0.0
rng = np.random.default_rng(0)
for tr, o in frames[:10]:
    P = Rv.load_aligned(tr, o)
    for lv in T.LEVELS:
        for d in T.DIR_IDS:
            x0 = T.perturb_x0(lv, d)
            for method in T.METHODS[:2]:
                a = T.inst_icp(method, P, x0=x0); b = frozen_call(method, P, x0=x0)
                max_ws = max(max_ws, float(np.abs(a["xi"] - b["xi"]).max()))
print(f"[2] inst vs G.robust_icp WARM-start: max|xi diff|={max_ws:.3e}")

# ---- check 3: reference (x0=None) reproduces frozen replay79 on in-support selected frames ----
max_et, max_eR, it_mis, nrep = 0.0, 0.0, 0, 0
missing = 0
for tr in Rv.TRAJS:
    for o in sel["trajectories"][tr]["selected_order"]:
        P = Rv.load_aligned(tr, o)
        for method in T.METHODS:
            key = (tr, int(o), method)
            if key not in rlk: missing += 1; continue
            ret, reR, rit, rob = rlk[key]
            a = T.inst_icp(method, P, x0=None)
            max_et = max(max_et, abs(a["final_translation_error_mm"] - ret))
            max_eR = max(max_eR, abs(a["final_rotation_error_deg"] - reR))
            it_mis += int(a["iterations"] != rit); nrep += 1
print(f"[3] reference vs replay79: matched={nrep} missing(out-of-support)={missing}  "
      f"max|d_et|={max_et:.3e} mm  max|d_eR|={max_eR:.3e} deg  iter-mismatch={it_mis}")

# ---- timing ----
P = Rv.load_aligned("VI", 26); t0 = time.perf_counter(); K = 20
for _ in range(K): T.inst_icp("PatchHuber", P, x0=T.perturb_x0("L3", "v4"))
dt = (time.perf_counter() - t0) / K
print(f"[4] one PatchHuber L3 registration = {dt*1000:.1f} ms; est 4160 runs 1 proc = {dt*4160/60:.1f} min")
assert max_xi < 1e-9 and max_ws < 1e-9 and max_it_mismatch == 0, "frozen-solver fidelity gate FAILED"
assert max_et < 1e-6 and max_eR < 1e-6 and it_mis == 0, "replay reproduction gate FAILED"
print("ALL SOLVER FIDELITY GATES PASSED")
