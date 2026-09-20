# -*- coding: utf-8 -*-
"""E2 production runner -- VI six-fold LEAVE-ONE-BLOCK-OUT held-out validation of the Patch field.

Question: does the spatial correction survive when the held-out view-travel block's scans are
withheld from field construction? The 24-patch PARTITION (`plab`) is FROZEN (MiniBatchKMeans k=24,
normal weight 0.30, seed 42) and is NOT re-clustered per fold -- only the per-patch discrepancy mean
mu_j is rebuilt from the five training blocks. This isolates field-calibration-history leakage from
clustering variability.

Fold j: train = VI scans with vi_blocks != j ; test = vi_blocks == j.
  mu_j = hierarchy_library(Vmean[train], Vcnt[train])  (identical point-weighted math as the
           deployed field); corrected model = model + mu_j[plab].
Leakage is asserted: train/test disjoint, union == all 501, and mu_j equals an explicit
point-weighted mean computed only over train rows. Every VI scan is scored exactly once under the
fold that holds its block -> full 501-frame out-of-fold (OOF) result.

Methods: Raw, Huber (field-independent); PatchOOF, PatchHuberOOF (held-out field); PatchFullFit
(deployed all-VI field; the in-sample comparator, kept distinct from OOF).
Output: e2_vi_lobo_framewise.csv ; e2_lobo_fold_provenance.json
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

import os, sys, time, json, argparse, hashlib
for _v in ["OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F
G, M = F.G, F.M

_G = {}

def _build_folds(fz):
    model, plab = fz["model"], fz["plab"]
    Vmean, Vcnt, blocks = fz["Vmean"], fz["Vcnt"], fz["vi_blocks"]
    folds = {}
    prov = {}
    all_idx = np.arange(len(blocks))
    for j in range(6):
        train = np.where(blocks != j)[0]
        test = np.where(blocks == j)[0]
        # ---- leakage assertions (hard) ----
        assert set(train.tolist()).isdisjoint(set(test.tolist())), f"fold {j}: train/test overlap"
        assert sorted(np.concatenate([train, test]).tolist()) == all_idx.tolist(), f"fold {j}: not a partition"
        _, mu_j = G.hierarchy_library(Vmean[train], Vcnt[train])
        # explicit independent recomputation over TRAIN ONLY (must match hierarchy_library)
        vs = (Vmean[train] * Vcnt[train][:, :, None]); pc = Vcnt[train].sum(0)
        mu_ref = np.divide(vs.sum(0), pc[:, None], out=np.zeros_like(vs.sum(0)), where=pc[:, None] > 0)
        assert np.array_equal(mu_j, mu_ref), f"fold {j}: field math mismatch"
        # held-out scan residuals provably absent: mu_j uses rows `train` only by construction
        m_j = model + mu_j[plab]
        folds[j] = dict(model=m_j, tree=F.kdtree1(m_j), train=train, test=test, mu=mu_j)
        prov[j] = dict(n_train=int(len(train)), n_test=int(len(test)),
                       train_scan_ids=[int(x) for x in train], test_scan_ids=[int(x) for x in test],
                       train_ids_sha256=F.sha256_bytes(np.asarray(train, np.int64).tobytes()),
                       field_mu_sha256=F.sha256_bytes(np.ascontiguousarray(mu_j).tobytes()),
                       field_mu_norm_per_patch=np.linalg.norm(mu_j, axis=1).round(6).tolist())
    return folds, prov


def init_worker():
    os.cpu_count = lambda: 1           # pin cKDTree query to 1 thread/process (fair, deterministic)
    fz = F.Rv.frozen_bundle()
    folds, prov = _build_folds(fz)
    _G.update(fz=fz, model=fz["model"], normals=fz["normals"], s_floor=fz["s_floor"],
              blocks=fz["vi_blocks"], tree_raw=F.kdtree1(fz["model"]),
              model_patch_full=fz["model_patch"], tree_patch_full=F.kdtree1(fz["model_patch"]), folds=folds)


def _reg(target, tree, P, form):
    r = G.robust_icp(target, _G["normals"], tree, P, "p2p", form, s_floor=_G["s_floor"])
    xi = r["xi"]
    return (float(np.linalg.norm(xi[:3]) * 1000.0), float(np.degrees(np.linalg.norm(xi[3:]))),
            int(r["iters"]), int(r["on_bound"]))


def _one_scan(scan):
    P = F.Rv.load_aligned("VI", int(scan))
    j = int(_G["blocks"][scan])
    fd = _G["folds"][j]
    out = []
    def push(method, et, eR, it, ob):
        out.append(dict(scan=int(scan), fold=j, method=method, et_mm=et, eR_deg=eR, iters=it, on_bound=ob))
    push("Raw",            *_reg(_G["model"], _G["tree_raw"], P, "ls"))
    push("Huber",          *_reg(_G["model"], _G["tree_raw"], P, "huber"))
    push("PatchOOF",       *_reg(fd["model"], fd["tree"], P, "ls"))
    push("PatchHuberOOF",  *_reg(fd["model"], fd["tree"], P, "huber"))
    push("PatchFullFit",   *_reg(_G["model_patch_full"], _G["tree_patch_full"], P, "ls"))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--nw", type=int, default=min(20, os.cpu_count() or 4))
    a = ap.parse_args()
    # build provenance + folds in main too (deterministic), and assert worker/main field identity later
    fz = F.Rv.frozen_bundle()
    folds_main, prov = _build_folds(fz)
    t0 = time.perf_counter(); rows = []
    with ProcessPoolExecutor(max_workers=a.nw, initializer=init_worker) as ex:
        for k, rr in enumerate(ex.map(_one_scan, range(501), chunksize=4)):
            rows.extend(rr)
            if (k + 1) % 100 == 0: print(f"  {k+1}/501 {time.perf_counter()-t0:.0f}s", flush=True)
    df = pd.DataFrame(rows)
    assert len(df) == 501 * 5, len(df)
    # every scan scored once per method, each under its own held-out fold
    for mth in df.method.unique():
        sub = df[df.method == mth]; assert len(sub) == 501 and sub.scan.is_unique
    out_csv = os.path.join(F.E2_OUT, "e2_vi_lobo_framewise.csv")
    df.to_csv(out_csv, index=False)
    # ---- fidelity cross-check vs frozen g1 VI (Raw M0, full-fit Patch M4) ----
    g1 = pd.read_csv(os.path.join(F.ROOT, "g_chain", "G1_MITIGATION", "results", "g1_oracle_vi.csv"))
    g1raw = g1[g1.method == "M0_raw_p2p"].set_index("order").sort_index()
    g1pat = g1[g1.method == "M4_patch_corr"].set_index("order").sort_index()
    d = df.pivot_table(index="scan", columns="method", values="et_mm")
    d = d.sort_index()
    max_raw = float(np.abs(d.Raw.values - g1raw.et_mm.values).max())
    max_pat = float(np.abs(d.PatchFullFit.values - g1pat.et_mm.values).max())
    fid = dict(max_abs_et_diff_raw_vs_g1_M0=max_raw, max_abs_et_diff_fullfit_vs_g1_M4=max_pat)
    assert max_raw < 1e-6 and max_pat < 1e-6, ("E2 fidelity vs frozen g1 failed", fid)
    block_sizes = {int(j): int((fz["vi_blocks"] == j).sum()) for j in range(6)}
    prov_doc = dict(block_ranges={0:"[0,70)",1:"[70,140)",2:"[140,219)",3:"[219,315)",4:"[315,418)",5:"[418,501)"},
                    block_sizes=block_sizes, folds=prov, fidelity=fid,
                    frozen_partition="patches.npz plab (k=24,w=0.30,seed=42); NOT re-clustered per fold",
                    field_rule="hierarchy_library point-weighted mu over the 5 training blocks",
                    runtime_seconds=round(time.perf_counter()-t0, 2))
    with open(os.path.join(F.E2_OUT, "e2_lobo_fold_provenance.json"), "w") as f:
        json.dump(prov_doc, f, indent=2)
    print(f"wrote {out_csv} rows={len(df)}; fidelity {fid}; {time.perf_counter()-t0:.0f}s")


if __name__ == "__main__":
    main()
