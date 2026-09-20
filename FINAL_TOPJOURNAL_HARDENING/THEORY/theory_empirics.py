# -*- coding: utf-8 -*-
"""
theory_empirics.py -- THEORY shard Part A5: connect first-order bias theory to existing data.

All inputs are READ-ONLY caches. Outputs:
  - theory_to_existing_results.csv  (dataset, condition, metric, value, note)
  - figures/g_norm_vs_bias.png
  - figures/direction_cosine.png
  - figures/pose_active_projection.png
  - figures/robust_dose_response.png (bonus, for Part B)

Fixed seed where any randomness appears (bootstrap CIs).
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

import os, json
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- paths
ROOT = _pp("")
THEORY_DIR = os.path.join(ROOT, "FINAL_TOPJOURNAL_HARDENING", "THEORY")
FIG_DIR = os.path.join(THEORY_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

VI_NPZ   = os.path.join(ROOT, "structured_mismatch_phase0", "scripts", "cache", "rescue",
                        "objective_main.npz")
IV_NPZ   = os.path.join(ROOT, "structured_mismatch_phase0", "scripts", "cache", "ext",
                        "ext_objective_iv.npz")
V_NPZ    = os.path.join(ROOT, "structured_mismatch_phase0", "scripts", "cache", "ext",
                        "ext_objective_v.npz")
II_NPZ   = os.path.join(ROOT, "tj2_supplemental", "cache", "ii", "ext_objective_ii.npz")
GEOM_CSV = os.path.join(ROOT, "g_chain", "G_GENERALITY", "results", "geometry_results.csv")

SEED = 42
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- helpers
def cosine(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na < 1e-15 or nb < 1e-15:
        return np.nan
    return float(a @ b / (na * nb))

def boot_ci(x, fn, B=2000, seed=SEED, alpha=0.05):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 5:
        return float(fn(x)), np.nan, np.nan
    r = np.random.default_rng(seed); n = len(x)
    out = np.empty(B)
    for b in range(B):
        out[b] = fn(r.choice(x, n, replace=True))
    lo, hi = np.percentile(out, [100*alpha/2, 100*(1-alpha/2)])
    return float(fn(x)), float(lo), float(hi)

rows = []  # CSV accumulator: (dataset, condition, metric, value, note)

def add(dataset, condition, metric, value, note=""):
    rows.append(dict(dataset=dataset, condition=condition, metric=metric,
                     value=float(value), note=note))

# ================================================================ load VI
print("Loading VI objective_main.npz ...")
vi = np.load(VI_NPZ, allow_pickle=True)

# last dim: 0=p2p, 1=p2l. first 3 cols = translation (m), last 3 = rotation (rad).
def per_frame_cos_metrics(g_key, dhat_key, xi_key, cond_label):
    g = vi[g_key]       # (N,6,2)
    dh = vi[dhat_key]   # (N,6,2)
    xi = vi[xi_key]     # (N,6,2)
    out = {}
    for kobj, oname in [(0, "p2p"), (1, "p2l")]:
        # direction cosine between dhat (= -H^dagger g) and xistar, full 6-DoF
        cos6 = np.array([cosine(dh[f, :, kobj], xi[f, :, kobj]) for f in range(g.shape[0])])
        # translation-only direction cosine
        cost = np.array([cosine(dh[f, :3, kobj], xi[f, :3, kobj]) for f in range(g.shape[0])])
        # rotation-only direction cosine
        cosr = np.array([cosine(dh[f, 3:, kobj], xi[f, 3:, kobj]) for f in range(g.shape[0])])
        # magnitudes
        gn = np.linalg.norm(g[:, :, kobj], axis=1)          # 6-DoF ||g|| = ||J^T W delta||
        gnt = np.linalg.norm(g[:, :3, kobj], axis=1)        # translation part only
        xit = np.linalg.norm(xi[:, :3, kobj], axis=1) * 1000.0  # mm
        out[oname] = dict(cos6=cos6, cost=cost, cosr=cosr,
                          gn=gn, gnt=gnt, xit=xit)
    return out

vi_metrics = {}
for cond in ["raw", "scale", "combined"]:
    vi_metrics[cond] = per_frame_cos_metrics(f"{cond}__g", f"{cond}__dhat", f"{cond}__xistar", cond)

# ---------------------------------------------------------------- A5(a): ||g|| vs ||xi*_t|| correlation
print("\n=== A5(a): ||J^T W delta|| vs GT-started translation bias magnitude ===")
for cond in ["raw", "scale", "combined"]:
    for oname in ["p2p", "p2l"]:
        m = vi_metrics[cond][oname]
        # 6-DoF ||g|| vs translation bias (mm)
        sp_r, sp_p = stats.spearmanr(m["gn"], m["xit"])
        pe_r, pe_p = stats.pearsonr(m["gn"], m["xit"])
        add("VI", cond, f"spearman_gn6_vs_xit_{oname}", sp_r,
            f"Spearman r between 6-DoF ||g|| and ||xi*_t||(mm); p={sp_p:.2e}")
        add("VI", cond, f"pearson_gn6_vs_xit_{oname}", pe_r,
            f"Pearson r between 6-DoF ||g|| and ||xi*_t||(mm); p={pe_p:.2e}")
        # translation-only g vs translation bias (dimensionally consistent)
        sp_r2, sp_p2 = stats.spearmanr(m["gnt"], m["xit"])
        pe_r2, pe_p2 = stats.pearsonr(m["gnt"], m["xit"])
        add("VI", cond, f"spearman_gnt_vs_xit_{oname}", sp_r2,
            f"Spearman r between ||g_t||(m) and ||xi*_t||(mm); p={sp_p2:.2e}")
        add("VI", cond, f"pearson_gnt_vs_xit_{oname}", pe_r2,
            f"Pearson r between ||g_t||(m) and ||xi*_t||(mm); p={pe_p2:.2e}")
        print(f"  {cond:9s} {oname}: spearman(gn6)={sp_r:.3f}, pearson(gn6)={pe_r:.3f}; "
              f"spearman(gnt)={sp_r2:.3f}, pearson(gnt)={pe_r2:.3f}")

# ---------------------------------------------------------------- A5(b): direction cosines
print("\n=== A5(b): direction cosine dhat vs xistar ===")
for cond in ["raw", "scale", "combined"]:
    for oname in ["p2p", "p2l"]:
        m = vi_metrics[cond][oname]
        for label, arr in [("cos6", m["cos6"]), ("cost", m["cost"]), ("cosr", m["cosr"])]:
            arr = arr[~np.isnan(arr)]
            med = np.median(arr); q25 = np.percentile(arr, 25); q75 = np.percentile(arr, 75)
            frac_pos = float(np.mean(arr > 0))
            add("VI", cond, f"cos_{label}_median_{oname}", med,
                f"median direction cosine; IQR=[{q25:.3f},{q75:.3f}]; frac positive={frac_pos:.3f}")
            print(f"  {cond:9s} {oname}: cos_{label} median={med:.3f} IQR=[{q25:.3f},{q75:.3f}] pos={frac_pos:.3f}")

# ---------------------------------------------------------------- A5(c): D1/D2/torque vs g
print("\n=== A5(c): diagnostic vectors vs pose-active gradient ===")
for diag in ["D1", "D2", "torque"]:
    v = vi[f"raw__{diag}"]
    vn = np.linalg.norm(v, axis=1)
    for oname in ["p2p", "p2l"]:
        gv = np.linalg.norm(vi[f"raw__g"][:, :, 0 if oname=="p2p" else 1], axis=1)
        sp = stats.spearmanr(vn, gv)
        add("VI", "raw", f"spearman_{diag}norm_vs_gn_{oname}", sp.statistic,
            f"Spearman r between ||{diag}|| and ||J^T W delta||; p={sp.pvalue:.2e}")
        print(f"  {diag:8s} vs g[{oname}]: spearman={sp.statistic:.3f} p={sp.pvalue:.2e}")

# Residual energy J0 vs pose-active gradient: show they are NOT the same
J0_p2p = vi["raw__J0"][:, 0]
J0_p2l = vi["raw__J0"][:, 1]
for oname, J0v in [("p2p", J0_p2p), ("p2l", J0_p2l)]:
    gv = np.linalg.norm(vi[f"raw__g"][:, :, 0 if oname=="p2p" else 1], axis=1)
    sp = stats.spearmanr(J0v, gv)
    add("VI", "raw", f"spearman_J0_vs_gn_{oname}", sp.statistic,
        f"Spearman r between residual energy J0 and pose-active ||g||; p={sp.pvalue:.2e}")
    print(f"  J0 vs g[{oname}]: spearman={sp.statistic:.3f}")

# ---------------------------------------------------------------- A5(d): IV held-out replication
print("\n=== A5(d): IV held-out replication ===")
iv = np.load(IV_NPZ, allow_pickle=True)
iv_cos_p2p_raw = []
iv_cos_p2l_raw = []
iv_gn_p2p = []
iv_xit_p2p = []
for cond in ["raw", "N1", "N2", "N3"]:
    g = iv[f"{cond}__g"]; dh = iv[f"{cond}__dhat"]; xi = iv[f"{cond}__xistar"]
    for kobj, oname in [(0, "p2p"), (1, "p2l")]:
        cost = np.array([cosine(dh[f, :3, kobj], xi[f, :3, kobj]) for f in range(g.shape[0])])
        cost = cost[~np.isnan(cost)]
        med = np.median(cost); q25 = np.percentile(cost, 25); q75 = np.percentile(cost, 75)
        add("IV", cond, f"cos_t_median_{oname}", med,
            f"IV held-out (n={g.shape[0]}); IQR=[{q25:.3f},{q75:.3f}]")
        print(f"  IV {cond:5s} {oname}: cos_t median={med:.3f} IQR=[{q25:.3f},{q75:.3f}]")

# Also V and II for robustness
for name, path in [("V", V_NPZ), ("II", II_NPZ)]:
    try:
        dd = np.load(path, allow_pickle=True)
        g = dd["raw__g"]; dh = dd["raw__dhat"]; xi = dd["raw__xistar"]
        for kobj, oname in [(0, "p2p"), (1, "p2l")]:
            cost = np.array([cosine(dh[f, :3, kobj], xi[f, :3, kobj]) for f in range(g.shape[0])])
            cost = cost[~np.isnan(cost)]
            med = np.median(cost)
            add(name, "raw", f"cos_t_median_{oname}", med,
                f"{name} held-out (n={g.shape[0]}); median translation direction cosine")
            print(f"  {name} raw {oname}: cos_t median={med:.3f}")
    except Exception as e:
        print(f"  {name}: {e}")

# ================================================================ Part D2: landscape directional-decrease check
print("\n=== Part D2: landscape verifies predicted descent decreases full NN objective ===")
ls = vi["landscape"]  # (501, 2, 3, 3, 2, 2)
J0 = vi["raw__J0"]    # (501,2)
g = vi["raw__g"]      # (501,6,2)
N = ls.shape[0]
# dim1=0 translation group (scales 0.01,0.02,0.05 m); dim1=1 rotation group (0.5,1,2 deg)
# dim2 = axis, dim3 = scale index, dim4 = 0(+)/1(-), dim5 = 0(p2p)/1(p2l)
# For each frame, each axis, objective k: check that the side predicted by g has lower J.
# g_axis = g[f, axis + (0 if trans else 3), kobj]
# If g_axis < 0, J decreases in +axis direction => J(+s e_axis) < J0.
# If g_axis > 0, J decreases in -axis direction => J(-s e_axis) < J0.
agree = {0: [], 1: []}   # p2p, p2l
agree_small = {0: [], 1: []}  # smallest scale only (most local)
for kobj in [0, 1]:
    for f in range(N):
        for group in [0, 1]:
            axoff = 0 if group == 0 else 3
            for ax in range(3):
                g_axis = g[f, axoff + ax, kobj]
                # use smallest scale (index 0) for local check
                J_plus = ls[f, group, ax, 0, 0, kobj]
                J_minus = ls[f, group, ax, 1, kobj] if False else ls[f, group, ax, 0, 1, kobj]
                J0k = J0[f, kobj]
                # predicted side: if g_axis<0, + direction descends; else - direction descends
                pred_descends_plus = (g_axis < 0)
                # actual: which side has lower J than J0?
                plus_lower = (J_plus < J0k - 1e-12)
                minus_lower = (J_minus < J0k - 1e-12)
                if pred_descends_plus:
                    ok = plus_lower
                else:
                    ok = minus_lower
                agree_small[kobj].append(float(ok))
                # also check across all 3 scales
                for sidx in range(3):
                    Jp = ls[f, group, ax, sidx, 0, kobj]
                    Jm = ls[f, group, ax, sidx, 1, kobj]
                    if g_axis < 0:
                        ok_s = (Jp < J0k - 1e-12)
                    else:
                        ok_s = (Jm < J0k - 1e-12)
                    agree[kobj].append(float(ok_s))
    frac = np.mean(agree[kobj])
    frac_s = np.mean(agree_small[kobj])
    oname = "p2p" if kobj == 0 else "p2l"
    add("VI", "raw", f"landscape_descent_agreement_{oname}", frac,
        f"fraction of (frame,axis,scale) probes where predicted descent side has lower full-NN J than J0; n={len(agree[kobj])}")
    add("VI", "raw", f"landscape_descent_agreement_small_{oname}", frac_s,
        f"same but smallest scale only (most local); n={len(agree_small[kobj])}")
    print(f"  {oname}: agreement all-scales={frac:.4f}, smallest-scale={frac_s:.4f}")

# ================================================================ G_GENERALITY: robust regime numbers
print("\n=== G_GENERALITY robust loss regime extraction ===")
geom = pd.read_csv(GEOM_CSV)
# D1 at 50mm, p2p, ls/huber/trim, median et_mm
for dtype in ["D1_appendage_disp", "D3_local_surface_off", "D5_appendage_tilt",
              "D4_appendage_scale", "D2_missing_component"]:
    sub = geom[geom["dtype"] == dtype]
    if len(sub) == 0:
        continue
    print(f"\n--- {dtype} ---")
    for form in ["ls", "huber", "trim"]:
        s = sub[sub["form"] == form]
        if len(s) == 0:
            continue
        et_med = s["et_mm"].median()
        eR_med = s["eR_deg"].median()
        onbnd = s["on_bound"].mean()
        add("G_GENERALITY", dtype, f"et_median_{form}", et_med,
            f"median endpoint translation error over doses; on_bound_frac={onbnd:.3f}")
        add("G_GENERALITY", dtype, f"eR_median_{form}", eR_med,
            f"median endpoint rotation error (deg)")
        print(f"  {form:6s}: et_median={et_med:.3f} mm, eR_median={eR_med:.4f} deg, on_bound={onbnd:.3f}")

# D1 dose-response at 50mm specifically (the cited 39.2/42.8/50.7)
d1 = geom[geom["dtype"] == "D1_appendage_disp"]
d1_50 = d1[d1["mag"] == 50.0]
print("\n--- D1 at mag=50mm (p2p only) ---")
for form in ["ls", "huber", "trim"]:
    s = d1_50[(d1_50["form"] == form) & (d1_50["kind"] == "p2p")]
    if len(s) > 0:
        et_med = s["et_mm"].median()
        print(f"  {form}: et_median={et_med:.3f} mm (n={len(s)})")
        add("G_GENERALITY", "D1_appendage_disp@50mm_p2p", f"et_median_{form}", et_med,
            f"D1 appendage displacement 50mm dose, p2p, {form} loss")

# D1 full dose-response
print("\n--- D1 dose-response (ls, p2p) ---")
d1ls = d1[(d1["form"] == "ls") & (d1["kind"] == "p2p")]
for mag in sorted(d1ls["mag"].unique()):
    s = d1ls[d1ls["mag"] == mag]
    et = s["et_mm"].median()
    print(f"  mag={mag:6.1f} mm -> et_median={et:.3f} mm")
    add("G_GENERALITY", "D1_dose_response_ls_p2p", f"et_median_mag{mag}", et,
        f"D1 appendage displacement dose-response, LS, p2p")

# D3 dose-response (pose-inactive / weak projection)
d3 = geom[geom["dtype"] == "D3_local_surface_off"]
print("\n--- D3 dose-response (ls, p2p) ---")
d3ls = d3[(d3["form"] == "ls") & (d3["kind"] == "p2p")]
for mag in sorted(d3ls["mag"].unique()):
    s = d3ls[d3ls["mag"] == mag]
    et = s["et_mm"].median()
    print(f"  mag={mag:6.1f} mm -> et_median={et:.3f} mm")
    add("G_GENERALITY", "D3_dose_response_ls_p2p", f"et_median_mag{mag}", et,
        f"D3 local surface offset dose-response, LS, p2p")

# D2 at f=1.0 (basin clip)
d2 = geom[geom["dtype"] == "D2_missing_component"]
d2_1 = d2[d2["mag"] == 1.0]
print("\n--- D2 at mag=1.0 (fully missing component) ---")
for form in ["ls", "huber", "trim"]:
    s = d2_1[(d2_1["form"] == form) & (d2_1["kind"] == "p2p")]
    if len(s) > 0:
        et = s["et_mm"].median()
        ob = s["on_bound"].mean()
        print(f"  {form}: et_median={et:.3f} mm, on_bound={ob:.3f}")
        add("G_GENERALITY", "D2_missing_component@f1.0_p2p", f"et_median_{form}", et,
            f"D2 fully missing component, p2p, {form}; on_bound_frac={ob:.3f}")

# ================================================================ write CSV
df_out = pd.DataFrame(rows)
csv_path = os.path.join(THEORY_DIR, "theory_to_existing_results.csv")
df_out.to_csv(csv_path, index=False)
print(f"\nWrote {csv_path} ({len(df_out)} rows)")

# ================================================================ FIGURES
# ---- Fig 1: g norm vs bias magnitude scatter (raw, p2p)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, (oname, kobj) in zip(axes, [("p2p", 0), ("p2l", 1)]):
    m = vi_metrics["raw"][oname]
    ax.scatter(m["gn"], m["xit"], s=8, alpha=0.4, c="steelblue")
    sp = stats.spearmanr(m["gn"], m["xit"])
    ax.set_xlabel(r"$\|\mathbf{g}\|=\|J^\top W\delta\|$ (full 6-DoF, raw)")
    ax.set_ylabel(r"GT-started local optimum displacement $\|\xi^*_t\|$ [mm]")
    ax.set_title(f"raw, {oname}: Spearman r={sp.statistic:.3f} (p={sp.pvalue:.1e})")
    ax.grid(alpha=0.3)
fig.suptitle("Fig A5a: Pose-active gradient norm vs measured GT-started bias (VI, n=501)")
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "g_norm_vs_bias.png"), dpi=140)
plt.close(fig)
print("Saved g_norm_vs_bias.png")

# ---- Fig 2: direction cosine distribution across conditions/objectives
fig, ax = plt.subplots(figsize=(10, 5.5))
conds = ["raw", "scale", "combined"]
positions = []
data = []
labels = []
colors = []
for i, cond in enumerate(conds):
    for j, oname in enumerate(["p2p", "p2l"]):
        m = vi_metrics[cond][oname]
        data.append(m["cost"][~np.isnan(m["cost"])])
        positions.append(i * 4 + j)
        labels.append(f"{cond}\n{oname}")
        colors.append("#2166ac" if oname == "p2p" else "#b2182b")
bp = ax.boxplot(data, positions=positions, widths=0.7, patch_artist=True, showfliers=False)
for patch, c in zip(bp["boxes"], colors):
    patch.set_facecolor(c); patch.set_alpha(0.6)
ax.axhline(0, color="k", lw=0.5, ls="--")
ax.axhline(1, color="k", lw=0.5, ls=":")
ax.set_xticks(positions)
ax.set_xticklabels(labels, fontsize=8)
ax.set_ylabel(r"Direction cosine $\cos(\hat{\xi}, \xi^*_t)$ (translation-only)")
ax.set_title("Fig A5b: Predicted Newton step vs measured optimum -- direction agreement")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "direction_cosine.png"), dpi=140)
plt.close(fig)
print("Saved direction_cosine.png")

# ---- Fig 3: pose-active projection -- D1 vs residual energy
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
# left: D1 norm vs g norm (high pose-active)
ax = axes[0]
D1n = np.linalg.norm(vi["raw__D1"], axis=1)
gn_p2p = np.linalg.norm(vi["raw__g"][:, :, 0], axis=1)
ax.scatter(D1n, gn_p2p, s=8, alpha=0.4, c="darkgreen")
sp = stats.spearmanr(D1n, gn_p2p)
ax.set_xlabel(r"$\|\mathbf{D}_1\|$ (structured appendage diagnostic)")
ax.set_ylabel(r"$\|J^\top W\delta\|$ (p2p)")
ax.set_title(f"High pose-active proxy: Spearman={sp.statistic:.3f}")
ax.grid(alpha=0.3)
# right: residual energy J0 vs g norm (NOT the same)
ax = axes[1]
ax.scatter(J0_p2p, gn_p2p, s=8, alpha=0.4, c="orange")
sp2 = stats.spearmanr(J0_p2p, gn_p2p)
ax.set_xlabel(r"Residual energy $J_0=\frac{1}{N}\sum\|e_i\|^2$ (p2p)")
ax.set_ylabel(r"$\|J^\top W\delta\|$ (p2p)")
ax.set_title(f"Residual energy vs pose-active gradient: Spearman={sp2.statistic:.3f}")
ax.grid(alpha=0.3)
fig.suptitle("Fig A5c: Pose-active projection -- discrepancy magnitude is NOT the same as pose-active component")
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "pose_active_projection.png"), dpi=140)
plt.close(fig)
print("Saved pose_active_projection.png")

# ---- Fig 4: D1 dose response (robust regime B)
fig, ax = plt.subplots(figsize=(8, 5))
for form, c in [("ls", "#2166ac"), ("huber", "#4dac26"), ("trim", "#d6604d")]:
    s = d1[(d1["form"] == form) & (d1["kind"] == "p2p")]
    meds = s.groupby("mag")["et_mm"].median()
    ax.plot(meds.index, meds.values, "o-", color=c, label=form.upper(), lw=2)
ax.set_xlabel("D1 appendage displacement dose [mm]")
ax.set_ylabel(r"Endpoint translation error $\|e_t\|$ [mm]")
ax.set_title("Fig B: D1 coherent-mismatch dose response -- robust weighting does NOT eliminate bias\n(LS 39.2, Huber 42.8, Trim 50.7 mm at 50 mm dose)")
ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "robust_dose_response.png"), dpi=140)
plt.close(fig)
print("Saved robust_dose_response.png")

print("\n=== DONE ===")
