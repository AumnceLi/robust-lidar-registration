# -*- coding: utf-8 -*-
"""TASK 2 (P0): LITERAL patch-LABEL permutation pose placebo.

The saved falsification placebo was a bijective VIEW<->TEMPLATE cross-block shuffle; it is NOT the
literal patch-label placebo requested here. This script keeps the multiset of the 24 frozen patch
correction 3-vectors EXACTLY (magnitude distribution preserved by construction) and randomly reassigns
those vectors to the 24 spatial patch labels with a single pre-declared fixed seed (no seed selection),
then re-runs the unchanged frozen p2p LS pose solver for:
  Raw (no correction) | true Patch (correct map) | shuffled Patch (permuted map).
A fixed 8-seed ensemble (also declared up-front, never selected on outcome) gives the null band only.
No parameter is tuned; every arm is GT-started (xi=0) and uses the same solver, weights and initial model.
"""
import os, json
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys, time
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from concurrent.futures import ProcessPoolExecutor
from scipy import stats as st

sys.path.insert(0, os.path.dirname(__file__))
import af_common as A
import g_common as G

SEED_PRIMARY = 20240910          # pre-declared, used exactly once as the primary placebo
ENSEMBLE_SEEDS = [20240911 + k for k in range(4)]   # fixed null-band ensemble, no outcome selection
_G = {}


def _init(perms):
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    fz = A.frozen_bundle()
    model, normals, plab, mp = fz["model"], fz["normals"], fz["plab"], fz["mu_patch"]
    mtrue = model + mp[plab]
    trees = [cKDTree(model), cKDTree(mtrue)]
    mshuf = []
    for pm in perms:
        mm = model + mp[np.asarray(pm)[plab]]
        mshuf.append(mm); trees.append(cKDTree(mm))
    _G.update(model=model, normals=normals, sf=fz["s_floor"],
              tree_raw=trees[0], tree_true=trees[1], trees_shuf=trees[2:],
              mtrue=mtrue, mshuf=mshuf)


def _arm(P, tree, target, grad=True):
    r = G.robust_icp(target, _G["normals"], tree, P, "p2p", "ls", s_floor=_G["sf"])
    xi = r["xi"]
    gt = gr = np.nan
    if grad:
        _, gv = G.robust_grad_norm(target, _G["normals"], tree, P, "p2p", "ls", _G["sf"])
        gt, gr = float(np.linalg.norm(gv[:3])), float(np.linalg.norm(gv[3:]))
    return (float(np.linalg.norm(xi[:3]) * 1000), float(np.degrees(np.linalg.norm(xi[3:]))),
            gt, gr, int(r["iters"]), int(r["on_bound"]))


def _one(args):
    traj, order, sid, scandir = args
    P = A.load_aligned(scandir, sid)
    raw = _arm(P, _G["tree_raw"], _G["model"], True)
    true = _arm(P, _G["tree_true"], _G["mtrue"], True)
    sh0 = _arm(P, _G["trees_shuf"][0], _G["mshuf"][0], True)
    ens = [_arm(P, _G["trees_shuf"][k], _G["mshuf"][k], False) for k in range(1, len(_G["trees_shuf"]))]
    et_ens = [e[0] for e in ens]; eR_ens = [e[1] for e in ens]
    return dict(trajectory=traj, order=order, scan=int(sid),
                raw_et_mm=raw[0], raw_eR_deg=raw[1], raw_gt=raw[2], raw_gr=raw[3],
                raw_iters=raw[4], raw_onbound=raw[5],
                patch_et_mm=true[0], patch_eR_deg=true[1], patch_gt=true[2], patch_gr=true[3],
                patch_iters=true[4], patch_onbound=true[5],
                shuf_et_mm=sh0[0], shuf_eR_deg=sh0[1], shuf_gt=sh0[2], shuf_gr=sh0[3],
                shuf_iters=sh0[4], shuf_onbound=sh0[5],
                shuf_ens_et_med=float(np.median(et_ens)), shuf_ens_et_min=float(np.min(et_ens)),
                shuf_ens_et_max=float(np.max(et_ens)),
                shuf_ens_eR_med=float(np.median(eR_ens)))


def frame_list(traj):
    if traj == "VI":
        return [(traj, i, i, os.path.join(A.M.CACHE, "scans")) for i in range(501)], np.ones(501, bool)
    cfg = A.REG[traj]
    meta = pd.read_csv(cfg["meta"]); P = np.load(cfg["pred"])
    ids = meta.scan.values.astype(int); insup = P["insup"].astype(bool)
    return [(traj, i, int(ids[i]), cfg["scandir"]) for i in range(len(ids))], insup


def wilc(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b) & (a != b)
    if m.sum() < 3:
        return np.nan
    return float(st.wilcoxon(a[m], b[m]).pvalue)


def run(nw=22):
    rng = np.random.default_rng(SEED_PRIMARY)
    perm0 = rng.permutation(24)
    perms = [perm0] + [np.random.default_rng(s).permutation(24) for s in ENSEMBLE_SEEDS]
    perm_record = dict(seed_primary=SEED_PRIMARY, permutation_primary=perm0.tolist(),
                       ensemble_seeds=ENSEMBLE_SEEDS,
                       permutations=[p.tolist() for p in perms[1:]],
                       note="permutation maps spatial patch label -> correction-vector index; "
                            "multiset of 24 mu_patch 3-vectors preserved exactly")
    with open(os.path.join(A.OUT, "scripts", "t2_permutations.json"), "w") as f:
        json.dump(perm_record, f, indent=1)
    print("[T2] primary permutation", perm0.tolist())

    allf = []
    for traj in ["VI", "IV", "II", "III", "V"]:
        tasks, insup = frame_list(traj)
        t0 = time.perf_counter(); rows = []
        with ProcessPoolExecutor(max_workers=nw, initializer=_init, initargs=(perms,)) as ex:
            for k, r in enumerate(ex.map(_one, tasks, chunksize=2)):
                r["in_support"] = bool(insup[k])
                rows.append(r)
                if (k + 1) % 1000 == 0:
                    print(f"  [T2 {traj}] {k+1}/{len(tasks)} {time.perf_counter()-t0:.0f}s", flush=True)
        df = pd.DataFrame(rows)
        bf, bp = A.block_series(traj, df.order.values, insup,
                                A.frozen_bundle()["F"]["blocks"] if traj == "VI" else None)
        df["block_full"] = bf; df["block_primary"] = bp
        # paired frame deltas (positive = that arm has LOWER error / lower gradient than raw)
        df["d_et_patch_raw"] = df.raw_et_mm - df.patch_et_mm
        df["d_et_shuf_raw"] = df.raw_et_mm - df.shuf_et_mm
        df["d_et_patch_shuf"] = df.shuf_et_mm - df.patch_et_mm
        df["d_eR_patch_raw"] = df.raw_eR_deg - df.patch_eR_deg
        df["d_eR_shuf_raw"] = df.raw_eR_deg - df.shuf_eR_deg
        df["d_gt_patch_raw"] = df.raw_gt - df.patch_gt
        df["d_gt_shuf_raw"] = df.raw_gt - df.shuf_gt
        allf.append(df)
        print(f"[T2 {traj}] done {len(df)} in {time.perf_counter()-t0:.0f}s", flush=True)
    F = pd.concat(allf, ignore_index=True)
    F.to_csv(os.path.join(A.OUT, "patch_label_placebo_frame.csv"), index=False)

    # ---------- block-level paired comparison on primary scope ----------
    brows = []
    for traj, d in F.groupby("trajectory"):
        prim = d if traj == "V" else d[d.in_support]
        blkcol = "block_primary"
        for b, q in prim.groupby(blkcol):
            r = dict(trajectory=traj, block=int(b), n=len(q))
            for arm in ["raw", "patch", "shuf"]:
                r[f"{arm}_et_med"] = q[f"{arm}_et_mm"].median()
                r[f"{arm}_eR_med"] = q[f"{arm}_eR_deg"].median()
                r[f"{arm}_gt_med"] = q[f"{arm}_gt"].median()
                r[f"{arm}_gr_med"] = q[f"{arm}_gr"].median()
            r["shuf_ens_et_med"] = q.shuf_ens_et_med.median()
            r["shuf_ens_et_lo"] = q.shuf_ens_et_min.median()
            r["shuf_ens_et_hi"] = q.shuf_ens_et_max.median()
            # paired deltas at frame level then median within block
            r["d_et_patch_raw"] = q.d_et_patch_raw.median()
            r["d_et_shuf_raw"] = q.d_et_shuf_raw.median()
            r["d_et_patch_shuf"] = q.d_et_patch_shuf.median()
            r["d_eR_patch_raw"] = q.d_eR_patch_raw.median()
            r["d_eR_shuf_raw"] = q.d_eR_shuf_raw.median()
            brows.append(r)
    B = pd.DataFrame(brows)
    # trajectory-level paired tests across blocks
    trows = []
    for traj, b in B.groupby("trajectory"):
        trows.append(dict(trajectory=traj, K=len(b),
            patch_et_blocks_improved=int((b.d_et_patch_raw > 0).sum()),
            shuf_et_blocks_improved=int((b.d_et_shuf_raw > 0).sum()),
            patch_beats_shuf_blocks=int((b.d_et_patch_shuf > 0).sum()),
            med_block_dEt_patch_raw=float(b.d_et_patch_raw.median()),
            med_block_dEt_shuf_raw=float(b.d_et_shuf_raw.median()),
            med_block_dEt_patch_shuf=float(b.d_et_patch_shuf.median()),
            wilcoxon_p_patch_vs_shuf_et=wilc(b.patch_et_med, b.shuf_et_med),
            wilcoxon_p_patch_vs_raw_et=wilc(b.patch_et_med, b.raw_et_med),
            wilcoxon_p_shuf_vs_raw_et=wilc(b.shuf_et_med, b.raw_et_med)))
    T = pd.DataFrame(trows)
    B.to_csv(os.path.join(A.OUT, "patch_label_placebo_block.csv"), index=False)
    T.to_csv(os.path.join(A.OUT, "scripts", "t2_block_tests.csv"), index=False)
    print(T.to_string(index=False))
    print("[T2] wrote frame/block csv")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--nw", type=int, default=22)
    a = ap.parse_args(); run(a.nw)
