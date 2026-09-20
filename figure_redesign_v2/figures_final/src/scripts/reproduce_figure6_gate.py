# -*- coding: utf-8 -*-
"""reproduce_figure6_gate.py -- Reproduction gate for Figure 6 (V2).

For the two frozen median-neighborhood representative frames
    IV / scan 278   (effect_full_minus_patch = +38.8212 mm, in support)
    II / scan 505   (effect_full_minus_patch = -24.5975 mm, on_bound=1)
re-run the FROZEN registration path (g_common.robust_icp via the exact
replay79._one machinery) and assert the recovered et_mm / eR_deg / on_bound
match the archived replay79_arms.csv to <1e-9.

Conventions (locked):
  Q_ref = load_aligned(scandir, sid)["aligned"]            (GT-aligned source)
  C = [R t; 0 1] from robust_icp output (Racc, tacc)
  Q_method_i = R @ Q_ref_i + t
  d_i = ||Q_method_i - Q_ref_i|| * 1000 mm                 (reference-relative, full vector)

Nothing here tunes a parameter or picks a method. No pose is back-derived
from scalar e_t/e_R: the full 4x4 C matrices come straight from robust_icp.
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

import os
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys, time, json, hashlib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
V2ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, _pp("FOLLOWUP_6_9/scripts"))
sys.path.insert(0, _pp("AUDIT_FOLLOWUP/scripts"))

import af_common as A          # noqa: E402
import m_common as M            # noqa: E402
import g_common as G            # noqa: E402
import replay79 as R79          # noqa: E402

sys.path.insert(0, os.path.join(V2ROOT, "configs"))
from paths import (SRC, DATA_DERIVED_DIR, DATA_SOURCE_DIR, MANIFEST_DIR, CHECKS_DIR,  # noqa: E402
                   FROZEN_FIELD_SHA256)

CASES = [
    dict(traj="IV", scan=278, bin="median", effect=+38.82124342365168),
    dict(traj="II", scan=505, bin="median", effect=-24.597508979640565),
]
ARMS = ["Raw", "Patch", "Full"]
ET_TOL = 1e-9   # hard gate requested


def log(fh, msg):
    print(msg, flush=True)
    fh.write(msg + "\n")


def build_task(traj, sid):
    """Replicate replay79.frame_tasks() entry for one (traj, scan)."""
    cfg = A.REG[traj]
    meta = pd.read_csv(cfg["meta"])
    pred = np.load(cfg["pred"])
    insup = pred["insup"].astype(bool)
    idx = np.where(insup)[0]
    hit = [i for i in idx if int(meta.scan.iloc[i]) == int(sid)]
    assert len(hit) == 1, (traj, sid, "in-support lookup failed", hit)
    i = hit[0]
    return (traj, int(i), int(meta.scan.iloc[i]),
            float(meta.range_m.iloc[i]),
            np.array([float(meta.ux.iloc[i]), float(meta.uy.iloc[i]), float(meta.uz.iloc[i])]),
            cfg["scandir"])


def run_arm(target, tree, P, form, normals, sf):
    """Byte-identical to replay79.reg but keeps R,t,xi (the solved SE(3))."""
    r = G.robust_icp(target, normals, tree, P, "p2p", form, s_floor=sf)
    xi = r["xi"]
    return dict(R=r["R"].copy(), t=r["t"].copy(), xi=xi.copy(),
                et_mm=float(np.linalg.norm(xi[:3]) * 1000.0),
                eR_deg=float(np.degrees(np.linalg.norm(xi[3:]))),
                iters=int(r["iters"]), on_bound=int(r["on_bound"]))


def main():
    os.makedirs(CHECKS_DIR, exist_ok=True)
    os.makedirs(DATA_SOURCE_DIR, exist_ok=True)
    os.makedirs(DATA_DERIVED_DIR, exist_ok=True)
    os.makedirs(MANIFEST_DIR, exist_ok=True)
    logpath = os.path.join(CHECKS_DIR, "figure6_reproduction_gate.log")
    fh = open(logpath, "w", encoding="utf-8")
    t0 = time.perf_counter()

    # --- verify frozen predictor hash before any computation ---------------
    assert A.sha256(G.PREDICTOR) == FROZEN_FIELD_SHA256, "frozen field sha256 mismatch"
    log(fh, f"[gate] frozen predictor sha256 OK == {FROZEN_FIELD_SHA256}")

    # --- init frozen bundle exactly as replay79._init -----------------------
    R79._init()
    _G = R79._G
    model = _G["model"]; normals = _G["normals"]; plab = _G["plab"]; sf = _G["sf"]
    mpatch = model + _G["mu_patch"][plab]
    tree_raw = _G["tree_raw"]
    tree_patch = _G["tree_patch"]
    log(fh, f"[gate] frozen bundle loaded: model {model.shape}, s_floor={sf:.6e}, plab {plab.shape}")

    archive = pd.read_csv(SRC["replay79_arms"])
    max_et_diff = 0.0
    max_eR_diff = 0.0
    all_ok = True

    for case in CASES:
        traj, sid = case["traj"], case["scan"]
        args = build_task(traj, sid)
        _, order, _, zr, zu, scandir = args
        P = A.load_aligned(scandir, sid)
        z = np.load(os.path.join(scandir, f"scan_{int(sid):04d}.npz"))
        nnidx = z["nnidx"]
        log(fh, "")
        log(fh, f"=== {traj} / scan {sid}  (order={order}, range={zr:.4f} m, n={P.shape[0]}) ===")

        # view-conditioned mu_full + tree, exactly as replay79._one
        mu_full, sup = R79.view_support(zr, zu)
        mfull = model + mu_full[plab]
        tree_full = cKDTree(mfull)

        arms = {}
        arms["Raw"] = run_arm(model, tree_raw, P, "ls", normals, sf)
        arms["Patch"] = run_arm(mpatch, tree_patch, P, "ls", normals, sf)
        arms["Full"] = run_arm(mfull, tree_full, P, "ls", normals, sf)

        # --- assert against archive ----------------------------------------
        for name in ARMS:
            row = archive[(archive.trajectory == traj) & (archive.scan == sid) & (archive.arm == name)]
            assert len(row) == 1, (traj, sid, name, "archive row missing")
            aet = float(row.et_mm.iloc[0]); aeR = float(row.eR_deg.iloc[0]); aob = int(row.on_bound.iloc[0])
            det = abs(arms[name]["et_mm"] - aet)
            deR = abs(arms[name]["eR_deg"] - aeR)
            dob = int(arms[name]["on_bound"] != aob)
            max_et_diff = max(max_et_diff, det)
            max_eR_diff = max(max_eR_diff, deR)
            ok = (det < ET_TOL) and (deR < ET_TOL * 1e-3) and (dob == 0)
            all_ok = all_ok and ok
            log(fh, f"  {name:5s} et={arms[name]['et_mm']:10.4f} mm (arch {aet:10.4f}, d={det:.2e}) "
                  f"eR={arms[name]['eR_deg']:7.3f} deg (arch {aeR:7.3f}, d={deR:.2e}) "
                  f"on_bound={arms[name]['on_bound']} arch={aob}  {'OK' if ok else 'FAIL'}")

        # --- SE(3) validity checks ----------------------------------------
        for name in ARMS:
            R = arms[name]["R"]; t = arms[name]["t"]
            assert R.shape == (3, 3) and t.shape == (3,), (name, "shape")
            assert abs(np.linalg.det(R) - 1.0) < 1e-9, (name, "det R != 1", np.linalg.det(R))
            assert np.allclose(R @ R.T, np.eye(3), atol=1e-9), (name, "R not orthogonal")
            C = np.eye(4); C[:3, :3] = R; C[:3, 3] = t
            arms[name]["C"] = C

        # --- reference-relative per-point displacement d_i (full vector) --
        Q_ref = P.astype(np.float64)
        displ = {}
        for name in ARMS:
            Qm = (arms[name]["R"] @ Q_ref.T).T + arms[name]["t"]
            di = np.linalg.norm(Qm - Q_ref, axis=1) * 1000.0   # mm
            displ[name] = di

        # --- save source scan + C matrices + displacement + display idx -----
        tag = f"{traj}{sid}"
        np.savez(os.path.join(DATA_SOURCE_DIR, f"figure6_case_{tag}_scan.npz"),
                 aligned=P.astype(np.float32), nnidx=nnidx, patch=z["patch"],
                 signed=z["signed"], d=z["d"],
                 traj=traj, scan=np.int32(sid), order=np.int32(order),
                 range_m=np.float64(zr))
        np.savez(os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_C_matrices.npz"),
                 C_raw=arms["Raw"]["C"], C_patch=arms["Patch"]["C"], C_full=arms["Full"]["C"],
                 et_raw=np.float64(arms["Raw"]["et_mm"]), et_patch=np.float64(arms["Patch"]["et_mm"]),
                 et_full=np.float64(arms["Full"]["et_mm"]),
                 eR_raw=np.float64(arms["Raw"]["eR_deg"]), eR_patch=np.float64(arms["Patch"]["eR_deg"]),
                 eR_full=np.float64(arms["Full"]["eR_deg"]),
                 on_bound_full=np.int32(arms["Full"]["on_bound"]))
        np.savez(os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_displacement.npz"),
                 d_raw=displ["Raw"], d_patch=displ["Patch"], d_full=displ["Full"],
                 note="reference-relative per-point displacement ||C Qref_i - Qref_i||*1000 mm")
        log(fh, f"  [saved] scan/C/displacement npz for {tag}")

    # --- display indices (shared 5000-pt subsample, seed 12345) -----------
    from camera_config import make_display_indices, DISPLAY_N_POINTS, DISPLAY_SEED
    for case in CASES:
        traj, sid = case["traj"], case["scan"]
        tag = f"{traj}{sid}"
        src = np.load(os.path.join(DATA_SOURCE_DIR, f"figure6_case_{tag}_scan.npz"))
        n_total = src["aligned"].shape[0]
        didx = make_display_indices(n_total)
        np.save(os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_display_indices.npy"), didx)
        log(fh, f"[gate] display indices {tag}: n_total={n_total} -> {len(didx)} (seed {DISPLAY_SEED})")

    # --- manifest: case selection provenance ------------------------------
    rep = pd.read_csv(SRC["rep_frames"])
    rows = []
    for case in CASES:
        tr = rep[(rep.trajectory == case["traj"]) & (rep.bin == case["bin"]) & (rep.scan == case["scan"])]
        assert len(tr) == 1
        tag = f"{case['traj']}{case['scan']}"
        cm = np.load(os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_C_matrices.npz"))
        onb = int(cm["on_bound_full"])
        rows.append(dict(
            trajectory=case["traj"], frame_id=int(case["scan"]), bin=case["bin"],
            selection_source="median_neighborhood",
            selection_source_path=SRC["rep_frames"],
            rule="p4_run.py: rank 0.45-0.55, effect=full_minus_patch closest to bin median",
            effect_full_minus_patch_mm=float(tr.effect_full_minus_patch_mm.iloc[0]),
            nearest_d=float(tr.nearest_d.iloc[0]), ess_kernel=float(tr.ess_kernel.iloc[0]),
            coverage=float(tr.coverage.iloc[0]), n_fallback=int(tr.n_fallback.iloc[0]),
            in_support=True,
            reference_pose="GT-aligned measured scan Q_ref (not error-free ground truth)",
            c_matrix_npz=os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_C_matrices.npz"),
            c_matrices_stored=True,
            on_bound_full=onb,
            protocol_note=("II505 Full trips the solve-path step safeguard: a per-iteration bound of "
                           "0.30 m / 15 deg on the ACCUMULATED step is reached at iteration 9, so that "
                           "step is clipped to the bound and ICP terminates early (on_bound=1, iters=9). "
                           "on_bound is reproduced here by re-running the frozen solver and matches the "
                           "archived replay79_arms.csv log exactly; it is an optimisation outcome (a "
                           "protection threshold on the solve path), NOT a convergence basin and NOT a "
                           "protocol error. The frame is one median-bin snapshot, not a chosen worst case."
                           if case["effect"] < 0 else
                           "IV278 Full stays inside the solve-path safeguard (on_bound=0, iters=37); "
                           "reproduced here and matched to the archived replay79_arms.csv log."),
            description=("Full improves over Patch in this median bin (positive effect)" if case["effect"] > 0
                         else "Full degrades vs Patch in this median bin (negative effect; on_bound=1)"),
        ))
    pd.DataFrame(rows).to_csv(os.path.join(MANIFEST_DIR, "case_selection.csv"), index=False)
    log(fh, f"[gate] wrote manifests/case_selection.csv")

    log(fh, "")
    log(fh, f"[gate] MAX |et diff|  = {max_et_diff:.3e} mm  (tol {ET_TOL:.0e})")
    log(fh, f"[gate] MAX |eR diff|  = {max_eR_diff:.3e} deg")
    log(fh, f"[gate] ALL ARMS MATCH ARCHIVE (<{ET_TOL:.0e}): {all_ok}")
    log(fh, f"[gate] elapsed {time.perf_counter()-t0:.1f}s")
    fh.close()
    print("REPRO GATE:", "PASS" if all_ok else "FAIL", "max_et_diff=", max_et_diff)
    assert all_ok, "reproduction gate FAILED -- see log"


if __name__ == "__main__":
    main()
