# -*- coding: utf-8 -*-
"""ft_common.py -- shared helpers for the FINAL TARGETED round (revision_experiments/final_targeted).

READ-ONLY on every frozen artifact; writes nothing outside final_targeted/.
Statistical conventions are copied VERBATIM from the frozen manuscript pipeline:

  * canonical paper block/time map  : POSE_AUDIT/results/master_pose_results_frame.csv
                                      (VI 6 / IV 4 / II 9 / III 8; replay79 joins the same file)
  * block-unit paired bootstrap     : stage3_master_results.block_boot_med  (B=2000, resample
                                      unique paper blocks with replacement, pool member frames,
                                      median, percentile 2.5/97.5, translation seed=42)
  * paired p                        : g_common.block_signflip_p (one-sided block sign-flip,
                                      B=2000, L=5, seed=42) -- the frozen "paired p"; NO classical
                                      binomial sign test is added because that is NOT in the convention
  * per-block paired effect         : median of framewise paired gains inside the block (stage3)
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
import numpy as np
import pandas as pd

ROOT = _pp("")
REV = os.path.join(ROOT, "revision_experiments")
OUT = os.path.join(REV, "final_targeted")
E4 = os.path.join(REV, "exp4_historical_baselines", "dbs_vector_framewise.csv")
REPLAY = os.path.join(ROOT, "FOLLOWUP_6_9", "scripts", "replay79_arms.csv")
BLOCKMAP = os.path.join(ROOT, "POSE_AUDIT", "results", "master_pose_results_frame.csv")
DIAG_FRAMES = os.path.join(REV, "exp2_iter_budget", "diagnostic_frames.json")
TRAJS = ["VI", "IV", "II", "III"]
POSTHOC = {"III"}

# ---------------------------------------------------------------- canonical paper block map
def paper_block_lookup():
    """(trajectory, order) -> paper block id, from the canonical master frame file (never recomputed)."""
    bm = pd.read_csv(BLOCKMAP)
    return {(r.trajectory, int(r.order)): int(r.block) for r in bm.itertuples()}


# ---------------------------------------------------------------- frozen block-unit bootstrap (verbatim of stage3_master_results.block_boot_med)
def block_boot_med(vals, blocks, B=2000, seed=42):
    vals = np.asarray(vals, float)
    blocks = np.asarray(blocks)
    ub = np.unique(blocks)
    mem = {b: np.where(blocks == b)[0] for b in ub}
    rng = np.random.default_rng(seed)
    out = np.empty(B)
    for b in range(B):
        pick = rng.choice(ub, size=len(ub), replace=True)
        samp = np.concatenate([vals[mem[p]] for p in pick])
        out[b] = np.median(samp)
    return dict(point=float(np.median(vals)), n=int(len(vals)), n_blocks=int(len(ub)),
                lo=float(np.percentile(out, 2.5)), hi=float(np.percentile(out, 97.5)))


# ---------------------------------------------------------------- frozen one-sided block sign-flip paired p (verbatim of g_common.block_signflip_p)
def block_signflip_p(delta, B=2000, L=5, seed=42):
    delta = np.asarray(delta, float)
    n = len(delta)
    obs = np.median(delta)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / L))
    null = np.empty(B)
    for b in range(B):
        signs = np.where(rng.random(nb) < 0.5, -1.0, 1.0)
        d = np.concatenate([np.full(L, signs[j]) for j in range(nb)])[:n] * delta
        null[b] = np.median(d)
    p = (1 + np.sum(null >= obs)) / (B + 1)
    return float(obs), float(p)


# ---------------------------------------------------------------- per-frame descriptive stats
def iqr_parts(x):
    x = np.asarray(x, float)
    q25, q75 = np.percentile(x, [25, 75])
    return float(q25), float(q75), float(q75 - q25)


def block_paired(gain, blocks):
    """Per-block paired effect (median framewise gain), median block effect, sign counts (exact zero)."""
    df = pd.DataFrame({"g": np.asarray(gain, float), "b": np.asarray(blocks)})
    per = df.groupby("b").g.median().sort_index()
    return dict(per_block=per,
                median_block_effect=float(per.median()),
                pos=int((per > 0).sum()), neg=int((per < 0).sum()), zero=int((per == 0).sum()),
                n_blocks=int(len(per)))
