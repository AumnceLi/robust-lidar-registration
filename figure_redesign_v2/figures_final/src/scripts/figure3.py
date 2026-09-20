# -*- coding: utf-8 -*-
"""
Figure 3 (V2) — Local mechanism evidence.
2x2 compact layout, 180x110 mm.

(a) ordinary residual RMS (x, log)  vs realized translation displacement (y, linear)
(b) pose-active residual RMS (x, log) vs realized translation displacement (y, linear)
(c) FO (fixed correspondence) direction error (deg) ECDF
(d) FD (rematched) direction error (deg) ECDF

Data: revision_experiments/exp3_pose_active/pose_active_direct_framewise.csv
      kind == 'p2p' only (1456 frames: VI 501 / IV 156 / II 428 / III 371).
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
# Trajectory palette mandated by the V2 Fig3/S1 spec:
# VI blue, IV warm orange, II teal, III purple. Pinned locally so concurrent
# edits to the shared palette cannot silently recolor these panels.
TRAJ_COLORS = {"VI": "#386CB0", "IV": "#C97A40", "II": "#2C8C7E", "III": "#8A6FA8"}
# Second encoding (shape / line style) so colour is never the only cue.
TRAJ_MARKERS = {"VI": "o", "IV": "s", "II": "^", "III": "D"}
TRAJ_LINESTYLES = {"VI": "-", "IV": "--", "II": "-.", "III": ":"}
TRAJ_N = {"VI": 501, "IV": 156, "II": 428, "III": 371}  # asserted against data below

from figure_style import (apply_style, panel_label, save_figure, fig_size_in,
                          FONT_TITLE, FONT_BODY)
from paths import DATA_DERIVED_DIR, FIG_MAIN_DIR

apply_style()

# pose_active source path (robust to concurrent SRC edits in the shared config)
from paths import SRC
POSE_ACTIVE_CSV = SRC.get("pose_active",
    _pp("revision_experiments/exp3_pose_active/pose_active_direct_framewise.csv"))

# ── Load ────────────────────────────────────────────────────────────────
df = pd.read_csv(POSE_ACTIVE_CSV)
p = df[df["kind"] == "p2p"].copy().reset_index(drop=True)
assert len(p) == 1456, f"expected 1456 p2p frames, got {len(p)}"
# verify per-trajectory n (these labels must never be hard-coded against stale data)
_actual_n = p["trajectory"].value_counts().to_dict()
assert all(_actual_n[t] == TRAJ_N[t] for t in TRAJ_N), (_actual_n, TRAJ_N)
# Both residual classes are strictly positive here (verified: no zeros), so a
# shared log axis is legal; compute ONE common log range for direct (a)/(b) compare.
_pos = np.concatenate([p.loc[p["rms_mm"] > 0, "rms_mm"],
                       p.loc[p["rms_pa_mm"] > 0, "rms_pa_mm"]])
RESID_XLO = float(np.floor(np.log10(_pos.min())))        # decade floor
RESID_XHI = float(np.ceil(np.log10(_pos.max())))         # decade ceil

# Direction error = arccos(dircos). A predicted step of zero magnitude has NO
# direction, so it is flagged invalid rather than counted as 0 deg.
def _direrr(dircos_col, mag_col):
    dc = pd.to_numeric(p[dircos_col], errors="coerce")
    mg = pd.to_numeric(p[mag_col], errors="coerce")
    valid = (mg > 0) & dc.notna()
    err = np.full(len(p), np.nan)
    err[valid.values] = np.degrees(np.arccos(np.clip(dc[valid].values, -1.0, 1.0)))
    return err, valid.values

p["fo_err_deg"], fo_valid = _direrr("an_dircos_t", "an_t_mm")
p["fd_err_deg"], fd_valid = _direrr("fd_dircos_t", "fd_t_mm")

# ── Anchor report (printed; also dumped to derived CSV) ─────────────────
anchor_rows = []
for tr in TRAJECTORY_ORDER:
    s = p[p["trajectory"] == tr]
    anchor_rows.append(dict(
        trajectory=tr, n=len(s),
        ratio_pa_median=round(s["ratio_pa"].median(), 3),
        fo_dircos_median=round(s["an_dircos_t"].median(), 3),
        fd_dircos_median=round(s["fd_dircos_t"].median(), 3),
    ))
anchor_df = pd.DataFrame(anchor_rows)
fo_over90 = int((p.loc[fo_valid, "fo_err_deg"] > 90).sum())
fd_over90 = int((p.loc[fd_valid, "fd_err_deg"] > 90).sum())
fd_max = float(np.nanmax(p.loc[fd_valid, "fd_err_deg"]))
print("[anchors]")
print(anchor_df.to_string(index=False))
print(f"[counts] fo_valid={fo_valid.sum()} (>90 deg: {fo_over90}), "
      f"fd_valid={fd_valid.sum()} (>90 deg: {fd_over90}, max={fd_max:.1f} deg)")
print(f"[displacement] actual_t_mm min={p['actual_t_mm'].min():.1f} max={p['actual_t_mm'].max():.1f}")
print(f"[residual zeros] rms_mm==0: {(p['rms_mm']==0).sum()}, "
      f"rms_pa_mm==0: {(p['rms_pa_mm']==0).sum()}")

# ── ECDF helper ──────────────────────────────────────────────────────────
def ecdf(x):
    x = np.sort(np.asarray(x, dtype=float))
    x = x[~np.isnan(x)]
    n = len(x)
    if n == 0:
        return x, np.full(n, np.nan)
    y = (np.arange(n) + 1.0) / n          # reaches 1.0 after the last sample
    return np.concatenate([[x[0]], x]), np.concatenate([[0.0], y])

def ygrid(ax):
    ax.grid(axis="y", color="#E8E8E8", linewidth=0.4)
    ax.grid(axis="x", visible=False)

# ── Figure ──────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=fig_size_in(180, 110))
ax_a, ax_b, ax_c, ax_d = axes.ravel()

# shared y for (a)(b): linear displacement, identical limits from real data
y_top = float(np.ceil(p["actual_t_mm"].max() / 25.0) * 25.0)  # round up to next 25 mm
y_lo, y_hi = 0.0, y_top

SCAT_KW = dict(s=9.5, alpha=0.45, linewidths=0, edgecolors="none", rasterized=True)

# Shared log-x limits/ticks for (a) and (b), so numeric scales compare directly.
resid_xlim = (10 ** RESID_XLO, 10 ** RESID_XHI)

# (a) ordinary residual RMS (log x) vs displacement (linear y)
for tr in TRAJECTORY_ORDER:
    s = p[p["trajectory"] == tr]
    ax_a.scatter(s["rms_mm"], s["actual_t_mm"], color=TRAJ_COLORS[tr],
                 marker=TRAJ_MARKERS[tr], **SCAT_KW)
ax_a.set_xscale("log")
ax_a.set_xlim(*resid_xlim)
ax_a.set_xlabel("Ordinary residual RMS (mm)")
ax_a.set_ylabel("Realized translation displacement (mm)")
ax_a.set_ylim(y_lo, y_hi)
ygrid(ax_a)
panel_label(ax_a, "(a)")

# (b) pose-active residual RMS (log x) vs same displacement
for tr in TRAJECTORY_ORDER:
    s = p[p["trajectory"] == tr]
    ax_b.scatter(s["rms_pa_mm"], s["actual_t_mm"], color=TRAJ_COLORS[tr],
                 marker=TRAJ_MARKERS[tr], **SCAT_KW)
ax_b.set_xscale("log")
ax_b.set_xlim(*resid_xlim)
ax_b.set_xlabel("Pose-active residual RMS (mm)")
ax_b.set_ylim(y_lo, y_hi)
ygrid(ax_b)
panel_label(ax_b, "(b)")

# ECDF x range: shared common right edge 160 deg (covers FO tail ~89 and FD
# tail 151 deg). After the last sample each curve holds y=1 out to 160 deg.
ECDF_X_MAX = 160.0

derived_rows = []
def plot_ecdf(ax, err_col, valid_mask, name):
    for tr in TRAJECTORY_ORDER:
        s = p[(p["trajectory"] == tr) & valid_mask]
        xv, yv = ecdf(s[err_col].values)
        # horizontal hold at ECDF=1 from the last sample to the common edge
        xv = np.concatenate([xv, [ECDF_X_MAX]])
        yv = np.concatenate([yv, [1.0]])
        # true step ECDF (steps-post), with a per-trajectory line style
        ax.step(xv, yv, where="post", color=TRAJ_COLORS[tr], lw=1.4,
                linestyle=TRAJ_LINESTYLES[tr])
        for xi, yi in zip(xv, yv):
            derived_rows.append(dict(panel=name, trajectory=tr,
                                     x_deg=round(xi, 4), ecdf=round(yi, 5)))
    ax.set_xlim(0, ECDF_X_MAX)
    ax.set_ylim(0, 1.03)
    ax.set_ylabel("ECDF")
    ax.set_xlabel("Direction error (°)")
    ygrid(ax)

plot_ecdf(ax_c, "fo_err_deg", fo_valid, "FO")
ax_c.set_title("Fixed-correspondence FO", fontsize=FONT_TITLE, pad=4)
plot_ecdf(ax_d, "fd_err_deg", fd_valid, "FD")
ax_d.set_title("Rematching FD", fontsize=FONT_TITLE, pad=4)
panel_label(ax_c, "(c)")
panel_label(ax_d, "(d)")

# ── Single shared horizontal legend on top of the whole figure ──────────
handles = [plt.Line2D([], [], color=TRAJ_COLORS[tr], marker=TRAJ_MARKERS[tr],
                      linestyle="none", markersize=5,
                      label=f"{tr} (n={TRAJ_N[tr]})")
           for tr in TRAJECTORY_ORDER]
fig.legend(handles=handles, loc="upper center", ncol=4, title="Trajectory",
           bbox_to_anchor=(0.5, 1.008), borderaxespad=0.0, columnspacing=1.4,
           title_fontsize=FONT_BODY, fontsize=FONT_BODY)

fig.tight_layout(rect=(0, 0, 1, 0.93))

# ── Save (PDF + SVG + PNG 600dpi) ───────────────────────────────────────
save_figure(fig, "figure3", [FIG_MAIN_DIR])
print("[saved] figure3.{pdf,svg,png} ->", FIG_MAIN_DIR)

# ── Derived data ────────────────────────────────────────────────────────
os.makedirs(DATA_DERIVED_DIR, exist_ok=True)
pd.DataFrame(derived_rows).to_csv(
    os.path.join(DATA_DERIVED_DIR, "figure3_ecdf.csv"), index=False)
anchor_df.to_csv(os.path.join(DATA_DERIVED_DIR, "figure3_anchor_summary.csv"),
                 index=False)
p[["trajectory", "rms_mm", "rms_pa_mm", "actual_t_mm",
   "fo_err_deg", "fd_err_deg"]].to_csv(
    os.path.join(DATA_DERIVED_DIR, "figure3_scatter_ecdf_source.csv"), index=False)
print("[derived] figure3_ecdf.csv, figure3_anchor_summary.csv, figure3_scatter_ecdf_source.csv")
