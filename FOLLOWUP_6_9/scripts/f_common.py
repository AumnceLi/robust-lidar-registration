# -*- coding: utf-8 -*-
"""f_common.py -- shared FROZEN statistics for follow-up items 6-9.

No parameter is tuned here. Block definitions and errors are READ from the frozen master
(POSE_AUDIT/results/master_pose_results_frame.csv, whose `block` column was built by stage3 from
the frozen VI orientation blocks and rank-in-primary//50 elsewhere). The block bootstrap matches
stage3_master_results.block_boot_med EXACTLY (resample blocks w/ replacement -> pooled median,
B=2000, percentile 2.5/97.5). Paired effects are computed at the BLOCK level (per-block median of
frame-level benefits), per the frozen block definition; sign test is exact (binomial p=0.5);
Wilcoxon signed-rank is auxiliary only.
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
import numpy as np, pandas as pd
from scipy import stats

ROOT = _pp("")
OUT = os.path.join(ROOT, "FOLLOWUP_6_9")
MASTER_FRAME = os.path.join(ROOT, "POSE_AUDIT", "results", "master_pose_results_frame.csv")
TRAJ6 = ["VI", "IV", "II", "III"]
METHODS6 = ["Raw", "Huber", "Trim", "Global", "Patch", "Full"]
B_BOOT = 2000


def block_boot_median_ci(vals, blocks, B=B_BOOT, seed=42):
    """Resample BLOCKS, pool member frames, take median; percentile CI. Identical to stage3."""
    vals = np.asarray(vals, float); blocks = np.asarray(blocks)
    ub = np.unique(blocks); mem = {b: np.where(blocks == b)[0] for b in ub}
    rng = np.random.default_rng(seed); out = np.empty(B)
    for b in range(B):
        pick = rng.choice(ub, size=len(ub), replace=True)
        samp = np.concatenate([vals[mem[p]] for p in pick])
        out[b] = np.median(samp)
    return float(np.median(vals)), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def block_boot_on_units(units, B=B_BOOT, seed=42):
    """Bootstrap the K block-level summary STATISTICS themselves (resample K units w/ replacement,
    take their median). Coarse by construction when K is small (4..9); reported honestly."""
    units = np.asarray(units, float); K = len(units)
    rng = np.random.default_rng(seed); out = np.empty(B)
    for b in range(B):
        out[b] = np.median(rng.choice(units, size=K, replace=True))
    return float(np.median(units)), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def exact_sign_p(pos, neg, zero):
    """Exact two-sided sign test p under H0: P(+) = 0.5 over non-zero block effects."""
    n = pos + neg
    if n == 0:
        return np.nan
    k = min(pos, neg)
    # two-sided = 2 * P(X <= k), X~Bin(n,0.5), capped at 1 (symmetric distribution)
    p = 2.0 * stats.binom.cdf(k, n, 0.5)
    return float(min(p, 1.0))


def wilcoxon_aux(units):
    """Wilcoxon signed-rank on block effects; AUXILIARY (does not replace block sign test)."""
    u = np.asarray(units, float); u = u[u != 0]
    if len(u) < 6 or np.all(u == u[0]):
        try:
            return float(stats.wilcoxon(u, zero_method="wilcox", alternative="two-sided").pvalue)
        except Exception:
            return np.nan
    try:
        return float(stats.wilcoxon(u, zero_method="wilcox", alternative="two-sided").pvalue)
    except Exception:
        return np.nan


def block_paired_benefit(df_traj, target, comparator, errcol, seed=42):
    """benefit = comparator_error - target_error (>0 => target better).
    Returns per-block benefit array and a frozen summary dict at BLOCK level."""
    a = df_traj[df_traj.method == comparator][["order", "block", errcol]].rename(columns={errcol: "ec"})
    b = df_traj[df_traj.method == target][["order", "block", errcol]].rename(columns={errcol: "et"})
    m = a.merge(b, on=["order", "block"], how="inner")
    assert len(m) > 0, (target, comparator, errcol)
    m["benefit"] = m.ec - m.et                       # frame-level paired benefit
    blk = m.groupby("block").benefit.median()        # BLOCK-level paired effect (frozen blocks)
    u = blk.values
    K = int(len(u)); pos = int(np.sum(u > 0)); neg = int(np.sum(u < 0)); zero = int(np.sum(u == 0))
    med, lo, hi = block_boot_on_units(u, seed=seed)
    frame_med = float(np.median(m.benefit.values))
    return dict(K=K, k_improved=pos, n_negative=neg, n_zero=zero,
                median_block_benefit=float(np.median(u)),
                q25=float(np.percentile(u, 25)), q75=float(np.percentile(u, 75)),
                ci_lo=lo, ci_hi=hi,
                sign_p=exact_sign_p(pos, neg, zero), wilcoxon_p=wilcoxon_aux(u),
                median_frame_benefit=frame_med, block_benefits=u)
