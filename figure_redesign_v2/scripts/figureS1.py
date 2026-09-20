# -*- coding: utf-8 -*-
"""
Supplementary Figure S1 (V2) — Diagnostics, 180x80 mm, 1x3 wide panels.

(a) predicted vs realized translation step length, log-log, 1:1 dashed;
    FO = hollow markers (fixed correspondence, an_t_mm),
    FD = solid markers (rematched, fd_t_mm); coloured by trajectory.
(b) ECDF of the 6x6 Hessian condition number (log x; native mixed m/rad units,
    unscaled).
(c) switch-rate distribution; only 66 frames have a defined switch rate
    (VI 40 / II 13 / III 11 / IV 2).

Data: revision_experiments/exp3_pose_active/pose_active_direct_framewise.csv,
      kind == 'p2p'.
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

import sys, os
sys.path.insert(0, _pp("figure_redesign_v2/configs"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from colors import CONTINUOUS_CMAP
try:
    from colors import TRAJECTORY_ORDER
except ImportError:
    TRAJECTORY_ORDER = ["VI", "IV", "II", "III"]
TRAJ_COLORS = {"VI": "#386CB0", "IV": "#C97A40", "II": "#2C8C7E", "III": "#8A6FA8"}

from figure_style import apply_style, panel_label, save_figure, fig_size_in
from paths import DATA_DERIVED_DIR, FIG_SUPP_DIR, SRC

apply_style()

POSE_ACTIVE_CSV = SRC.get("pose_active",
    _pp("revision_experiments/exp3_pose_active/pose_active_direct_framewise.csv"))

df = pd.read_csv(POSE_ACTIVE_CSV)
p = df[df["kind"] == "p2p"].copy().reset_index(drop=True)

sw = p[p["switch_rate"].notna()].copy()
sw_counts = sw.groupby("trajectory")["switch_rate"].count().to_dict()
print("[switch-rate] n_valid =", len(sw), sw_counts)

def ygrid(ax):
    ax.grid(axis="y", color="#E8E8E8", linewidth=0.4)
    ax.grid(axis="x", visible=False)

fig, axes = plt.subplots(1, 3, figsize=fig_size_in(180, 80))
ax_a, ax_b, ax_c = axes.ravel()

# ── (a) predicted vs realized step length, log-log ───────────────────────
for tr in TRAJECTORY_ORDER:
    s = p[p["trajectory"] == tr]
    c = TRAJ_COLORS[tr]
    # FO hollow (fixed correspondence)
    ax_a.scatter(s["actual_t_mm"], s["an_t_mm"], facecolors="none",
                 edgecolors=c, linewidths=0.6, s=11, alpha=0.5, rasterized=True)
    # FD solid (rematched)
    ax_a.scatter(s["actual_t_mm"], s["fd_t_mm"], color=c, s=11, alpha=0.45,
                 linewidths=0, rasterized=True)

# 1:1 reference diagonal
lo = float(np.floor(np.log10(max(p["actual_t_mm"].min(), p["an_t_mm"].min(),
                                  p["fd_t_mm"].min())) - 0.2))
hi = float(np.ceil(np.log10(max(p["actual_t_mm"].max(), p["an_t_mm"].max(),
                               p["fd_t_mm"].max())) + 0.2))
ref = np.logspace(lo, hi, 50)
ax_a.plot(ref, ref, color="#525B63", ls="--", lw=0.8, zorder=0)
ax_a.set_xscale("log")
ax_a.set_yscale("log")
ax_a.set_xlabel("Realized step length (mm)")
ax_a.set_ylabel("Predicted step length (mm)")
h_fo = plt.Line2D([], [], marker="o", linestyle="none", markersize=5,
                  markerfacecolor="none", markeredgecolor="#525B63", label="FO (fixed)")
h_fd = plt.Line2D([], [], marker="o", linestyle="none", markersize=5,
                  markerfacecolor="#525B63", markeredgecolor="#525B63", label="FD (rematched)")
ax_a.legend(handles=[h_fo, h_fd], loc="lower right", fontsize=7.0)
ygrid(ax_a)
panel_label(ax_a, "(a)")

# ── (b) per-trajectory condition-number ECDF, log x ────────────────────
def _ecdf(vals):
    x = np.sort(np.asarray(vals, dtype=float))
    x = x[~np.isnan(x)]
    n = len(x)
    if n == 0:
        return x, x
    return np.concatenate([[x[0]], x]), np.concatenate([[0.0], (np.arange(n) + 1.0) / n])

cond_rows = []
for tr in TRAJECTORY_ORDER:
    xv, yv = _ecdf(p.loc[p["trajectory"] == tr, "cond"].values)
    ax_b.plot(xv, yv, color=TRAJ_COLORS[tr], lw=1.3, label=tr)
    for xi, yi in zip(xv, yv):
        cond_rows.append(dict(trajectory=tr, cond=round(xi, 5), ecdf=round(yi, 5)))
ax_b.set_xscale("log")
ax_b.set_xticks([5, 10, 20, 50, 100])
ax_b.set_xticklabels(["5", "10", "20", "50", "100"])
ax_b.set_xlim(4, 130)
ax_b.set_xlabel(r"6$\times$6 Hessian condition number")
ax_b.set_ylabel("ECDF")
ax_b.set_ylim(0, 1.03)
ygrid(ax_b)
panel_label(ax_b, "(b)")

# ── (c) switch-rate distribution (66 valid frames) ─────────────────────
positions = np.arange(1, len(TRAJECTORY_ORDER) + 1)
data = [sw.loc[sw["trajectory"] == tr, "switch_rate"].values for tr in TRAJECTORY_ORDER]
bp = ax_c.boxplot(data, positions=positions, widths=0.55, patch_artist=True,
                  showfliers=False,
                  medianprops=dict(color="white", lw=1.0),
                  whiskerprops=dict(color="#525B63", lw=0.7),
                  capprops=dict(color="#525B63", lw=0.7))
for patch, tr in zip(bp["boxes"], TRAJECTORY_ORDER):
    patch.set_facecolor(TRAJ_COLORS[tr])
    patch.set_alpha(0.75)
    patch.set_edgecolor("#525B63")
    patch.set_linewidth(0.6)
rng = np.random.default_rng(7)
for pos, tr, vals in zip(positions, TRAJECTORY_ORDER, data):
    jit = rng.normal(pos, 0.05, size=len(vals))
    ax_c.scatter(jit, vals, s=9, color=TRAJ_COLORS[tr],
                 edgecolors="white", linewidths=0.3, alpha=0.85, zorder=3)
ax_c.set_xticks(positions)
ax_c.set_xticklabels([f"{tr}\n(n={sw_counts.get(tr,0)})" for tr in TRAJECTORY_ORDER],
                     fontsize=7.0)
ax_c.set_xlabel("Trajectory")
ax_c.set_ylabel("Switch rate")
ax_c.set_ylim(-0.02, 0.32)
ygrid(ax_c)
panel_label(ax_c, "(c)")

# ── Shared trajectory legend on top (VI/IV/II/III), not repeated per panel ─
tr_handles = [plt.Line2D([], [], color=TRAJ_COLORS[tr], marker="o",
                         linestyle="none", markersize=5, label=tr)
              for tr in TRAJECTORY_ORDER]
fig.legend(handles=tr_handles, loc="upper center", ncol=4,
           bbox_to_anchor=(0.5, 1.005), borderaxespad=0.0)

fig.tight_layout(rect=(0, 0, 1, 0.93))
save_figure(fig, "figureS1", [FIG_SUPP_DIR])
print("[saved] figureS1.{pdf,svg,png} ->", FIG_SUPP_DIR)

# ── Derived data ────────────────────────────────────────────────────────
os.makedirs(DATA_DERIVED_DIR, exist_ok=True)
p[["trajectory", "actual_t_mm", "an_t_mm", "fd_t_mm", "cond"]].to_csv(
    os.path.join(DATA_DERIVED_DIR, "figureS1_step_cond_source.csv"), index=False)
pd.DataFrame(cond_rows).to_csv(
    os.path.join(DATA_DERIVED_DIR, "figureS1_cond_ecdf.csv"), index=False)
sw[["trajectory", "order", "switch_rate"]].to_csv(
    os.path.join(DATA_DERIVED_DIR, "figureS1_switchrate.csv"), index=False)
print("[derived] figureS1_step_cond_source.csv, figureS1_cond_ecdf.csv, figureS1_switchrate.csv")
