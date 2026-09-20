# -*- coding: utf-8 -*-
"""g0_stats.py -- aggregate G0 frame results into method/block/bootstrap/self-null tables + figures.
Reads g0_frame_{traj}.csv; nothing here re-runs registration or changes a parameter."""
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

import os, sys, json
import numpy as np, pandas as pd
from scipy import stats as st
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = _pp("g_chain/G0_ROBUST_FALSIFICATION/results")
FIG = _pp("g_chain/G0_ROBUST_FALSIFICATION/figures")
os.makedirs(FIG, exist_ok=True)
TRAJ = ["vi", "iv", "ii", "v"]
FORMS = ["ls", "huber", "trim"]
FORMNAME = {"ls": "R0/R1 LS-ICP", "huber": "R2 Huber (primary)", "trim": "R3 Trim80 (sensitivity)"}
KINDS = ["p2p", "p2l"]
LEAVE_MM = [1.0, 5.0, 10.0, 25.0]

def load():
    dfs = []
    for t in TRAJ:
        p = os.path.join(RES, f"g0_frame_{t}.csv")
        if os.path.exists(p):
            dfs.append(pd.read_csv(p))
    df = pd.concat(dfs, ignore_index=True)
    return df

def cohend(a, b):
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return (a.mean() - b.mean()) / (sp + 1e-15)

def subset(df, traj):
    d = df[df.traj == traj]
    if traj == "vi":
        return d, "all(development)"
    if traj == "v":
        return d, "all(out-of-support extrapolation)"   # V has zero in-support; supportive only
    return d[d.in_support], "in_support(primary)"

def main():
    df = load()
    df.to_csv(os.path.join(RES, "frame_results.csv"), index=False)
    method_rows, block_rows, boot_rows, self_rows = [], [], [], []
    for traj in TRAJ:
        if traj not in set(df.traj):
            continue
        dprim, slab = subset(df, traj)
        for kind in KINDS:
            for form in FORMS:
                real_ref = None
                for source, tag in [(1, "real"), (0, "self")]:
                    q = dprim[(dprim.kind == kind) & (dprim.form == form) & (dprim.real == source)]
                    et = q.et_mm.values; eR = q.eR_deg.values; gg = q.g_gt.values
                    if len(et) == 0:
                        continue
                    bb = G.block_boot(et, np.median, B=2000, Ls=(5, 10, 20), seed=42)
                    row = dict(traj=traj, subset=slab, kind=kind, form=form, source=tag, n=len(et),
                               et_med=float(np.median(et)), et_q25=float(np.percentile(et, 25)),
                               et_q75=float(np.percentile(et, 75)), et_mean=float(et.mean()),
                               eR_med=float(np.median(eR)), g_gt_med=float(np.median(gg)),
                               L5_lo=bb["L5_lo"], L5_hi=bb["L5_hi"], L10_lo=bb["L10_lo"], L10_hi=bb["L10_hi"],
                               L20_lo=bb["L20_lo"], L20_hi=bb["L20_hi"], on_bound_pct=100 * q.on_bound.mean())
                    for thr in LEAVE_MM:
                        row[f"leave_gt_{thr:g}mm_pct"] = 100 * np.mean(et > thr)
                    if source == 1:
                        method_rows.append(row); real_ref = row
                    else:
                        self_rows.append(row)
                    for L in (5, 10, 20):
                        boot_rows.append(dict(traj=traj, subset=slab, kind=kind, form=form, source=tag,
                                              block_L=L, point_median=bb["point"],
                                              lo=bb[f"L{L}_lo"], hi=bb[f"L{L}_hi"]))
                # paired real-vs-self effect (real only) on the held real row
                qr = dprim[(dprim.kind == kind) & (dprim.form == form) & (dprim.real == 1)].sort_values("order")
                qs = dprim[(dprim.kind == kind) & (dprim.form == form) & (dprim.real == 0)].sort_values("order")
                a, b = qr.et_mm.values, qs.et_mm.values
                if real_ref is not None and len(a) == len(b) and len(a) > 5:
                    d_ = cohend(a, b)
                    try:
                        mw = st.mannwhitneyu(a, b, alternative="greater").pvalue
                    except Exception:
                        mw = np.nan
                    real_ref.update(real_self_ratio=float(np.median(a) / (np.median(b) + 1e-12)),
                                    cohens_d=float(d_), mwu_p=float(mw))
                # per-block medians (real)
                for blk, gq in qr.groupby("block"):
                    block_rows.append(dict(traj=traj, subset=slab, kind=kind, form=form, block=int(blk),
                                           n=len(gq), et_med=float(gq.et_mm.median()),
                                           eR_med=float(gq.eR_deg.median()), g_gt_med=float(gq.g_gt.median())))
        # paired attenuation: ls -> huber / trim on real, per-scan paired delta + block signflip
        for kind in KINDS:
            base = dprim[(dprim.kind == kind) & (dprim.form == "ls") & (dprim.real == 1)].set_index("order")
            for form in ["huber", "trim"]:
                cmp = dprim[(dprim.kind == kind) & (dprim.form == form) & (dprim.real == 1)].set_index("order")
                j = base.index.intersection(cmp.index)
                delta = base.loc[j, "et_mm"].values - cmp.loc[j, "et_mm"].values   # >0 = robust reduces bias
                obs, p = G.block_signflip_p(delta, B=2000, L=5, seed=42)
                method_rows.append(dict(traj=traj, subset=slab, kind=kind, form=f"ls_minus_{form}", source="paired",
                                        n=len(j), et_med=float(np.median(delta)), et_mean=float(delta.mean()),
                                        frac_reduced=float(np.mean(delta > 0)), signflip_p=p,
                                        note="median paired mm by which robust reduces e_t vs ls"))
    pd.DataFrame(method_rows).to_csv(os.path.join(RES, "method_table.csv"), index=False)
    pd.DataFrame(block_rows).to_csv(os.path.join(RES, "block_results.csv"), index=False)
    pd.DataFrame(boot_rows).to_csv(os.path.join(RES, "bootstrap_summary.csv"), index=False)
    pd.DataFrame(self_rows).to_csv(os.path.join(RES, "self_null_results.csv"), index=False)

    # ---------- figures ----------
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.2), sharey=False)
    for ax, traj in zip(axes, TRAJ):
        if traj not in set(df.traj):
            ax.set_visible(False); continue
        dprim, _ = subset(df, traj)
        data, labs, cols = [], [], []
        cmap = {"ls": "#d62728", "huber": "#1f77b4", "trim": "#2ca02c"}
        for form in FORMS:
            q = dprim[(dprim.kind == "p2p") & (dprim.form == form)]
            data.append(q[q.real == 1].et_mm.values); labs.append(FORMNAME[form].split()[0] + " real")
            cols.append(cmap[form])
            data.append(q[q.real == 0].et_mm.values); labs.append(FORMNAME[form].split()[0] + " self"); cols.append("0.7")
        pos = np.arange(len(data))
        ax.boxplot(data, positions=pos, showfliers=False, widths=0.6,
                   medianprops=dict(color="black"))
        ax.set_xticks(pos); ax.set_xticklabels(["LS r", "LS s", "Hub r", "Hub s", "Trim r", "Trim s"], fontsize=8)
        ax.set_title(f"{traj.upper()}  p2p e_t^GT [mm]", fontsize=10)
        ax.grid(alpha=.25)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "G0F1_et_by_formulation.png"), dpi=140); plt.close()

    # median e_t with L5 CI across formulation/trajectory (p2p)
    mt = pd.DataFrame(method_rows)
    real = mt[(mt.source == "real") & (mt.kind == "p2p") & (mt.form.isin(FORMS))]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    width = 0.25; xs = np.arange(len(TRAJ))
    for k, form in enumerate(FORMS):
        sub = [real[real.traj == t] for t in TRAJ]
        med = np.array([s.et_med.values[0] if len(s) else np.nan for s in sub])
        lo = np.array([s.L5_lo.values[0] if len(s) else np.nan for s in sub])
        hi = np.array([s.L5_hi.values[0] if len(s) else np.nan for s in sub])
        ax.bar(xs + (k - 1) * width, med, width, yerr=[med - lo, hi - med], capsize=3,
               label=FORMNAME[form], color=cmap[form])
    ax.set_xticks(xs); ax.set_xticklabels([f"{t.upper()}" for t in TRAJ])
    ax.set_ylabel("median GT-started translation displacement [mm]\n(L5 block bootstrap 95% CI)")
    ax.set_title("G0: does robust registration remove the GT-started displacement? (p2p)")
    ax.legend(fontsize=8); ax.grid(alpha=.25, axis="y")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "G0F2_median_et_ci.png"), dpi=140); plt.close()

    # gradient at GT real vs self (log)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    gr = mt[(mt.source == "real") & (mt.kind == "p2p") & (mt.form.isin(FORMS))]
    gs = mt[(mt.source == "self") & (mt.kind == "p2p") & (mt.form.isin(FORMS))]
    for k, form in enumerate(FORMS):
        rr = [gr[gr.traj == t].g_gt_med.values[0] if len(gr[gr.traj == t]) else np.nan for t in TRAJ]
        ss = [gs[gs.traj == t].g_gt_med.values[0] if len(gs[gs.traj == t]) else np.nan for t in TRAJ]
        ax.semilogy(xs + (k - 1) * width - 0.06, rr, "o", color=cmap[form], label=FORMNAME[form] + " real")
        ax.semilogy(xs + (k - 1) * width + 0.06, ss, "x", color=cmap[form], alpha=.6, label=FORMNAME[form] + " self")
    ax.set_xticks(xs); ax.set_xticklabels([t.upper() for t in TRAJ])
    ax.set_ylabel("median ||grad J(T_GT)||  (log scale)")
    ax.set_title("G0: objective non-stationarity at GT, real vs model-self (p2p)")
    ax.legend(fontsize=7, ncol=2); ax.grid(alpha=.25, which="both")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "G0F3_gradient_real_vs_self.png"), dpi=140); plt.close()
    print("[g0_stats] tables + figures written")

def source_tag(s):
    return s == "real"

if __name__ == "__main__":
    main()
