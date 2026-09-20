# -*- coding: utf-8 -*-
"""revx_common.py -- shared core for the MINIMAL pre-submission revision experiments.

Hard rules baked in here:
  * READ-ONLY reuse of every frozen asset (model, PCA normals, frozen predictor, frozen blocks).
  * Evaluation frame roster + blocks are JOINED from the existing replay79 Raw arm
    (== frozen master in-support frames); frames are never re-filtered.
  * Baseline arms (Raw / Huber / frozen Patch / frozen PatchHuber / Full) are REUSED from
    replay79_arms.csv -- they are never re-run. We run a NEW registration only for a genuinely
    new configuration (a new patch partition, or recomputed normals).
  * The frozen anchor (k=24, normal weight 0.3, seed 42) is re-run as a GATE and must match the
    existing Patch arm to ~0; it is never used to "re-select" anything.
  * No outcome-driven choice: the swept grids are fixed before any IV/II/III result is inspected.
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
import sys, json, time, hashlib, platform
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from concurrent.futures import ProcessPoolExecutor

ROOT = _pp("")
PHASE = os.path.join(ROOT, "structured_mismatch_phase0", "scripts")
GCM = os.path.join(ROOT, "g_chain", "common")
AFS = os.path.join(ROOT, "AUDIT_FOLLOWUP", "scripts")
REV = os.path.join(ROOT, "revision_experiments")
for _p in (PHASE, GCM, AFS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import s0_common as C  # noqa
import m_common as M  # noqa
import g_common as G  # noqa
import af_common as A  # noqa
from sklearn.cluster import MiniBatchKMeans  # noqa

TRAJS = ["VI", "IV", "II", "III"]
REPLAY_ARMS = os.path.join(ROOT, "FOLLOWUP_6_9", "scripts", "replay79_arms.csv")
FROZEN_PATCHES = os.path.join(M.CACHE, "patches.npz")
FROZEN_MODEL = os.path.join(M.CACHE, "model_cache.npz")
NW = 16  # worker count (24 logical CPUs, BLAS single-threaded per worker)
ARM_CACHE = os.path.join(REV, "_lib", "arm_cache")
os.makedirs(ARM_CACHE, exist_ok=True)


# ------------------------------------------------------------- provenance
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_head():
    import subprocess
    try:
        r = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True)
        return r.stdout.strip() or "NOT_A_GIT_REPO"
    except Exception as e:
        return f"git_unavailable:{e}"


def input_fingerprints():
    return {
        "frozen_predictor_npz": {"path": G.PREDICTOR.replace("\\", "/"), "sha256": G.PREDICTOR_SHA},
        "model_cache_npz": {"path": FROZEN_MODEL.replace("\\", "/"), "sha256": sha256(FROZEN_MODEL)},
        "patches_npz": {"path": FROZEN_PATCHES.replace("\\", "/"), "sha256": sha256(FROZEN_PATCHES)},
        "replay79_arms_csv": {"path": REPLAY_ARMS.replace("\\", "/"), "sha256": sha256(REPLAY_ARMS)},
    }


def write_provenance(out_json, experiment, exact_command, config, seed, outputs, note=""):
    import sklearn, scipy
    prov = {
        "experiment": experiment,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "host": platform.node(),
        "python": sys.version.split()[0],
        "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__,
        "pandas": pd.__version__,
        "git_commit": git_head(),
        "exact_command": exact_command,
        "config": config,
        "random_seed": seed,
        "input_assets": input_fingerprints(),
        "note": note,
        "outputs": {k: ({"path": v.replace("\\", "/"), "sha256": sha256(v)} if os.path.exists(v)
                        else {"path": v, "MISSING": True}) for k, v in outputs.items()},
    }
    with open(out_json, "w") as f:
        json.dump(prov, f, indent=1, ensure_ascii=False, default=str)
    return prov


# ------------------------------------------------------------- frozen assets
_BUNDLE = None
def bundle():
    global _BUNDLE
    if _BUNDLE is None:
        _BUNDLE = A.frozen_bundle()
    return _BUNDLE


def model_and_normals():
    mc = np.load(FROZEN_MODEL)
    return mc["xyz"].astype(np.float64), mc["normals"].astype(np.float64), float(mc["dnn"])


# ------------------------------------------------------------- partition + VI re-aggregation
def make_partition(k, norm_w, seed, model=None, nmodel=None):
    """Exact frozen clustering rule, with only k / normal weight / seed changed.
    feature = column_stack([xyz, w*unit_normal]); MiniBatchKMeans n_init=20 batch=4096 (literal s3)."""
    if model is None or nmodel is None:
        model, nmodel, _ = model_and_normals()
    feat = np.concatenate([model, norm_w * nmodel], axis=1)
    km = MiniBatchKMeans(n_clusters=k, random_state=seed, n_init=20, batch_size=4096).fit(feat)
    return km.labels_.astype(int)


def vi_view_independent_mu(plab, k, model=None):
    """Pool the per-point 3D mismatch over ALL 501 VI scans per new patch (== hierarchy_library,
    view-INDEPENDENT). Identical math to g_common.hierarchy_library but under an arbitrary partition."""
    if model is None:
        model, _, _ = model_and_normals()
    vsum = np.zeros((k, 3)); vc = np.zeros(k)
    for t in range(M.N_SCANS):
        sc = M.load_scan(t); nn = sc["nnidx"]
        v = sc["aligned"].astype(np.float64) - model[nn]
        lab = plab[nn]
        np.add.at(vsum, lab, v); np.add.at(vc, lab, np.ones(len(nn)))
    mu = np.zeros((k, 3)); ok = vc > 0
    mu[ok] = vsum[ok] / vc[ok, None]
    return mu, vc


# ------------------------------------------------------------- frozen evaluation roster
def roster():
    """(trajectory,order,scan,block) for VI(all 501) + IV/II/III in-support, JOINED from replay79 Raw."""
    a = pd.read_csv(REPLAY_ARMS)
    r = a[a.arm == "Raw"][["trajectory", "order", "scan", "block", "in_support"]].copy()
    r = r[r.trajectory.isin(TRAJS)].reset_index(drop=True)
    scandir = {"VI": os.path.join(M.CACHE, "scans")}
    for tr in ["IV", "II", "III"]:
        scandir[tr] = A.REG[tr]["scandir"]
    r["scandir"] = r.trajectory.map(scandir)
    return r


def baseline_arm(arm_name):
    """Existing frozen per-frame arm from replay79 (never re-run)."""
    a = pd.read_csv(REPLAY_ARMS)
    return a[a.arm == arm_name][["trajectory", "order", "et_mm", "eR_deg", "iters", "on_bound",
                                 "block", "in_support"]].copy()


# ------------------------------------------------------------- parallel registration of one arm
_W = {}
def _arm_init(target, normals, s_floor, kind, form):
    _W["target"] = target; _W["normals"] = normals; _W["s_floor"] = s_floor
    _W["tree"] = cKDTree(target); _W["kind"] = kind; _W["form"] = form

def _arm_one(args):
    traj, order, scan, block, scandir = args
    P = A.load_aligned(scandir, scan)
    r = G.robust_icp(_W["target"], _W["normals"], _W["tree"], P, _W["kind"], _W["form"],
                     s_floor=_W["s_floor"])
    xi = r["xi"]
    return (traj, order, scan, block,
            float(np.linalg.norm(xi[:3]) * 1000.0), float(np.degrees(np.linalg.norm(xi[3:]))),
            int(r["iters"]), int(r["on_bound"]), len(P))

def run_arm(target, normals, s_floor, kind, form, rost=None, nw=NW, label=""):
    if rost is None:
        rost = roster()
    rows = [(r.trajectory, int(r.order), int(r.scan), int(r.block), r.scandir)
            for r in rost.itertuples(index=False)]
    out = []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=nw, initializer=_arm_init,
                             initargs=(target, normals, s_floor, kind, form)) as ex:
        for k, res in enumerate(ex.map(_arm_one, rows, chunksize=4)):
            out.append(res)
            if (k + 1) % 500 == 0:
                print(f"    [{label}] {k+1}/{len(rows)} {time.perf_counter()-t0:.0f}s", flush=True)
    df = pd.DataFrame(out, columns=["trajectory", "order", "scan", "block",
                                    "et_mm", "eR_deg", "iters", "on_bound", "n_points"])
    print(f"  [{label}] {len(df)} frames in {time.perf_counter()-t0:.0f}s", flush=True)
    return df


# ------------------------------------------------------------- cached arm for one clustering config
def _tag(kind, form, k, w, seed):
    return f"{kind}_{form}_k{int(k)}_w{float(w):.4f}_s{int(seed)}".replace(".", "p")

def get_partition_arm(k, w, seed, kind="p2p", form="ls", normals_mode="frozen",
                      force=False, nw=NW, verbose=True):
    """Build (or load cached) the per-frame arm for ONE clustering configuration.

    Corrected target = model + mu_patch(plab), where plab is re-clustered at (k,w,seed) and mu_patch
    is re-aggregated view-independently over all 501 VI scans under THAT partition. Normals default to
    the frozen model normals (p2p does not consume them); normals_mode='renormal' recomputes PCA k=16
    normals on the corrected geometry (P2-A only). Cached on disk so the shared anchor is never rerun.
    """
    tag = _tag(kind, form, k, w, seed) + ("_RENORMAL" if normals_mode == "renormal" else "")
    path = os.path.join(ARM_CACHE, tag + ".csv")
    if os.path.exists(path) and not force:
        return pd.read_csv(path), tag
    model, nmodel, sf = model_and_normals()
    plab = make_partition(k, w, seed, model, nmodel)
    mu, vc = vi_view_independent_mu(plab, k, model)
    target = model + mu[plab]
    if normals_mode == "frozen":
        normals = nmodel
    elif normals_mode == "renormal":
        normals = C.pca_normals(target, cKDTree(target), k=16)
    else:
        raise ValueError(normals_mode)
    df = run_arm(target, normals, sf, kind, form, nw=nw, label=tag)
    df["k"] = int(k); df["w"] = float(w); df["seed"] = int(seed)
    df["min_patch_count"] = int(vc.min()); df["normals_mode"] = normals_mode
    df.to_csv(path, index=False)
    if verbose:
        print(f"  [cache] wrote {os.path.basename(path)}")
    return df, tag


# ------------------------------------------------------------- cached arm over the RAW nominal model
def get_raw_arm(kind, form, force=False, nw=NW):
    """Registration against the UN-corrected nominal model (frozen normals). p2p ls/huber reproduce
    replay79 Raw/Huber (gate); p2l forms are the new channel needed for the normal-recompute ablation."""
    tag = f"raw_{kind}_{form}"
    path = os.path.join(ARM_CACHE, tag + ".csv")
    if os.path.exists(path) and not force:
        return pd.read_csv(path), tag
    model, nmodel, sf = model_and_normals()
    df = run_arm(model, nmodel, sf, kind, form, nw=nw, label=tag)
    df.to_csv(path, index=False)
    return df, tag


# ------------------------------------------------------------- paired / aggregate statistics
def paired_frame(target_df, comp_df, metric):
    """frame-paired target - comparator on (trajectory,order). Positive translation = target BETTER
    (lower error) when metric is error and we report comp-target; here return target-comp deltas."""
    j = target_df.merge(comp_df, on=["trajectory", "order"], suffixes=("_t", "_c"))
    j["delta"] = j[f"{metric}_t"] - j[f"{metric}_c"]
    return j

def benefit_comp_minus_targ(target_df, comp_df, metric):
    """benefit = comparator - target (positive => target improves over comparator)."""
    j = target_df.merge(comp_df, on=["trajectory", "order"], suffixes=("_t", "_c"))
    return j[f"{metric}_c"] - j[f"{metric}_t"]

def summarize_against(raw_df, patch_df, block_boot=True, B=2000, seed=42):
    """Per-trajectory Raw/Patch medians + frame-paired translation benefit & rotation change."""
    rows = []
    for tr in TRAJS:
        rw = raw_df[raw_df.trajectory == tr]; pa = patch_df[patch_df.trajectory == tr]
        m = rw.merge(pa, on=["trajectory", "order"], suffixes=("_raw", "_patch"))
        ben_t = m.et_mm_raw - m.et_mm_patch           # >0 => Patch improves translation
        dRot = m.eR_deg_patch - m.eR_deg_raw          # >0 => Patch pays rotation cost
        row = dict(trajectory=tr, n_frames=len(m),
                   raw_translation_median_mm=float(np.median(m.et_mm_raw)),
                   patch_translation_median_mm=float(np.median(m.et_mm_patch)),
                   raw_rotation_median_deg=float(np.median(m.eR_deg_raw)),
                   patch_rotation_median_deg=float(np.median(m.eR_deg_patch)),
                   paired_translation_benefit_mm=float(np.median(ben_t)),
                   translation_improved_frac=float((ben_t > 0).mean()),
                   paired_rotation_change_deg=float(np.median(dRot)),
                   patch_boundary_trigger_rate=float(m.on_bound_patch.mean()))
        if block_boot:
            blocks = m.block.values
            pt, lo, hi, nb = A.block_bootstrap_median(ben_t.values, blocks, B=B, seed=seed)
            pr, rlo, rhi, _ = A.block_bootstrap_median(dRot.values, blocks, B=B, seed=seed)
            row.update(n_blocks=nb, trans_benefit_blockCI=(round(lo, 3), round(hi, 3)),
                       rot_change_blockCI=(round(rlo, 3), round(rhi, 3)))
        rows.append(row)
    return pd.DataFrame(rows)
