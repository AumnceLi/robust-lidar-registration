# -*- coding: utf-8 -*-
"""g_generality_stats.py -- aggregate cross-geometry controlled study + figures/decision inputs."""
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

import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = _pp("g_chain/G_GENERALITY"); RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
DTYPES = ["D1_appendage_disp", "D2_missing_component", "D3_local_surface_off", "D4_appendage_scale", "D5_appendage_tilt"]
DTLAB = {"D1_appendage_disp": "D1 appendage displacement", "D2_missing_component": "D2 unmodeled component",
         "D3_local_surface_off": "D3 local surface offset", "D4_appendage_scale": "D4 one-sided scale",
         "D5_appendage_tilt": "D5 appendage tilt", "CTRL_random_noise": "matched-RMS isotropic noise"}
GEOMS = ["GA", "GB", "GC"]; GC_ = {"GA": "#1f77b4", "GB": "#d62728", "GC": "#2ca02c"}

def boot_med(x, B=2000, seed=42):
    x = np.asarray(x); rng = np.random.default_rng(seed); n = len(x)
    v = np.array([np.median(x[rng.integers(0, n, n)]) for _ in range(B)])
    return np.median(x), np.percentile(v, 2.5), np.percentile(v, 97.5)

def main():
    df = pd.read_csv(os.path.join(RES, "geometry_results.csv"))
    p2p = df[df.kind == "p2p"]
    rows = []
    for (geom, dtype, mag, form), g in p2p.groupby(["geometry", "dtype", "mag", "form"]):
        m, lo, hi = boot_med(g.et_mm.values)
        _, rlo, rhi = boot_med(g.eR_deg.values); gm, glo, ghi = boot_med(g.grad_gt.values)
        rows.append(dict(geometry=geom, dtype=dtype, mag=mag, form=form, n=len(g), et_med=m, et_lo=lo, et_hi=hi,
                         eR_med=np.median(g.eR_deg), eR_lo=rlo, eR_hi=rhi, grad_med=gm, grad_lo=glo, grad_hi=ghi,
                         on_bound=g.on_bound.mean()))
    dose = pd.DataFrame(rows); dose.to_csv(os.path.join(RES, "dose_response.csv"), index=False)
    # noise control (p2p ls)
    ctrl = p2p[(p2p.condition == "unstructured_noise") & (p2p.form == "ls")].groupby(["geometry", "mag"]).et_mm.median().reset_index()
    ctrl.to_csv(os.path.join(RES, "noise_control.csv"), index=False)

    # ---------- F1 dose-response (LS), 5 panels, control overlay for linear types ----------
    fig, axes = plt.subplots(2, 3, figsize=(15, 8)); axes = axes.ravel()
    for k, dt in enumerate(DTYPES):
        ax = axes[k]
        for geom in GEOMS:
            q = dose[(dose.geometry == geom) & (dose.dtype == dt) & (dose.form == "ls")].sort_values("mag")
            ax.errorbar(q.mag, q.et_med, yerr=[q.et_med - q.et_lo, q.et_hi - q.et_med], fmt="-o", ms=4,
                        color=GC_[geom], label=geom, capsize=2)
        if dt in ("D1_appendage_disp", "D3_local_surface_off"):
            for geom in GEOMS:
                c = ctrl[ctrl.geometry == geom].sort_values("mag")
                ax.plot(c.mag, c.et_mm, ":", color=GC_[geom], lw=1.2, alpha=.8)
            ax.plot([], [], "k:", label="matched-RMS noise")
        xunit = {"D1_appendage_disp": "mm", "D2_missing_component": "fraction unmodeled", "D3_local_surface_off": "mm",
                 "D4_appendage_scale": "scale frac", "D5_appendage_tilt": "deg"}[dt]
        ax.set_title(DTLAB[dt], fontsize=10); ax.set_xlabel(xunit)
        ax.set_ylabel("median GT e_t [mm]"); ax.grid(alpha=.25); ax.legend(fontsize=7)
    axes[5].axis("off")
    axes[5].text(.02, .9, "Solid = structured discrepancy (LS p2p)\nDotted = equal-RMS isotropic noise\n"
                          "(D1/D3). Error bars = 95% bootstrap over 20 reps.\nGT=identity; bias = ICP displacement from GT.",
                 fontsize=10, va="top")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "GF1_dose_response.png"), dpi=140); plt.close()

    # ---------- F2 gradient-at-GT vs resulting bias (mechanism link) ----------
    ls = dose[dose.form == "ls"]
    fig, ax = plt.subplots(figsize=(7.2, 5.6)); mk = {"GA": "o", "GB": "s", "GC": "^"}
    for dt in DTYPES:
        q = ls[(ls.dtype == dt) & (ls.et_med > 1e-3)]
        ax.scatter(q.grad_med, q.et_med, label=DTLAB[dt].split(" ")[0], s=34, alpha=.8,
                   marker="o")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(r"$\|\nabla J(T_{GT})\|$ at ground truth (LS p2p)"); ax.set_ylabel("median GT-start e_t [mm]")
    ax.set_title("Mechanism link across 3 geometries x 5 discrepancy types"); ax.grid(alpha=.25, which="both"); ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "GF2_gradient_vs_bias.png"), dpi=140); plt.close()

    # ---------- F3 LS vs Huber vs Trim attenuation (D1 at 50mm, D5 at 1deg, D2 at .75, D3 at 50) ----------
    pick = {"D1_appendage_disp": 50, "D2_missing_component": 1.0, "D3_local_surface_off": 50,
            "D4_appendage_scale": .10, "D5_appendage_tilt": 2.0}
    fig, ax = plt.subplots(figsize=(10, 4.6)); xs = np.arange(len(DTYPES)); w = .25
    for fi, form in enumerate(["ls", "huber", "trim"]):
        vals = []
        for dt in DTYPES:
            q = ls if False else dose
            sub = q[(q.dtype == dt) & (q.form == form) & (np.isclose(q.mag, pick[dt]))]
            vals.append(sub.et_med.median())  # median across 3 geometries
        ax.bar(xs + (fi - 1) * w, vals, w, label=form.upper())
    ax.set_xticks(xs); ax.set_xticklabels([d.split("_")[0] for d in DTYPES])
    ax.set_ylabel("median GT e_t [mm] (avg over geometries)")
    ax.set_title("Robust formulations only attenuate (gross-outlier D2 excepted)"); ax.legend(); ax.grid(alpha=.25, axis="y")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "GF3_formulations.png"), dpi=140); plt.close()

    # ---------- F4 structured/noise ratio at matched linear magnitude ----------
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    for geom in GEOMS:
        for dt, ls_ in [("D1_appendage_disp", "-"), ("D3_local_surface_off", "--")]:
            s = dose[(dose.geometry == geom) & (dose.dtype == dt) & (dose.form == "ls")].set_index("mag").et_med
            c = ctrl[ctrl.geometry == geom].set_index("mag").et_mm
            common = s.index.intersection(c.index).difference([0])
            ax.plot(common, [s[m] / max(c[m], 1e-6) for m in common], ls_, color=GC_[geom],
                    label=f"{geom} {dt.split('_')[0]}")
    ax.axhline(1, color="k", lw=.8); ax.set_xlabel("magnitude [mm]"); ax.set_ylabel("structured e_t / equal-RMS noise e_t")
    ax.set_title("Coherent structure biases more than equal-RMS random noise"); ax.grid(alpha=.25); ax.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "GF4_struct_vs_noise.png"), dpi=140); plt.close()

    # ---------- decision inputs ----------
    summ = []
    for geom in GEOMS:
        for dt in DTYPES:
            q = dose[(dose.geometry == geom) & (dose.dtype == dt) & (dose.form == "ls")].sort_values("mag")
            y = q.eR_med.values if dt == "D5_appendage_tilt" else q.et_med.values
            mono = bool(np.all(np.diff(y) >= -0.05))     # non-decreasing (tiny tol); D5 judged on rotation
            e0 = q[q.mag == q.mag.min()].et_med.iloc[0]; eMax = q.et_med.max()
            summ.append(dict(geometry=geom, dtype=dt, selfnull_et=e0, max_et=eMax,
                             max_eR=q.eR_med.max(), monotone=mono))
    sd = pd.DataFrame(summ); sd.to_csv(os.path.join(RES, "generality_summary.csv"), index=False)
    print(sd.round(3).to_string(index=False))
    print("\nDose table (LS, median over geometries):")
    print(ls.groupby(["dtype", "mag"]).et_med.median().round(2).to_string())

    # robust attenuation at representative magnitudes (median over geometries), incl D2 gross-outlier rescue
    print("\nRobust formulation medians (median over geometries, mm):")
    rt = dose.groupby(["dtype", "mag", "form"]).et_med.median().reset_index()
    for dt, mg in pick.items():
        sub = rt[(rt.dtype == dt) & (np.isclose(rt.mag, mg))]
        print(dt, "mag", mg, dict(zip(sub.form, sub.et_med.round(2))))

    # structured/noise ratio at matched linear magnitude (median over geometries)
    print("\nStructured/equal-RMS-noise ratio (LS, median over geometries):")
    for dt in ["D1_appendage_disp", "D3_local_surface_off"]:
        s = ls[ls.dtype == dt].groupby("mag").et_med.median()
        cn = ctrl.groupby("mag").et_cm if False else ctrl.groupby("mag").et_mm.median()
        common = s.index.intersection(cn.index).difference([0])
        ratio = {m: round(s[m] / max(cn[m], 1e-6), 2) for m in common}
        print(dt, ratio)

if __name__ == "__main__":
    main()
