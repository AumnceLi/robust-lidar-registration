"""
Figure 2 (V2): Residual structure visualization.
180 x 108 mm.
  Top row:  (a) Fixed nominal partition (~30%) | (b) VI residual heatmap (~65%)
  Bottom row: 3 equal-width curves for patches 3, 20, 8.
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from colors import METHOD_COLORS, NOMINAL_MODEL_COLOR, TEXT_COLOR, HEATMAP_CMAP
from figure_style import (apply_style, panel_label, save_figure,
                           fig_size_in, FONT_BODY, FONT_PANEL, FONT_TITLE,
                           FONT_TICK)
from paths import SRC, FIG_MAIN_DIR, DATA_DERIVED_DIR

apply_style()

# ── Load derived data ─────────────────────────────────────────────────────
derived = np.load(os.path.join(DATA_DERIVED_DIR, "figure2_residual_stats.npz"),
                  allow_pickle=True)
block_patch_med = derived["block_patch_med"]

# ── Load model geometry for panel (a) ──────────────────────────────────────
_model = np.load(SRC["model_cache"], allow_pickle=True)
XYZ = _model["xyz"]
_patches = np.load(SRC["patches"], allow_pickle=True)
PLAB = _patches["lab"]

def project(xyz, elev=25.0, azim=-60.0):
    el = np.radians(elev)
    az = np.radians(azim)
    Rz = np.array([[np.cos(az), -np.sin(az), 0],
                   [np.sin(az),  np.cos(az), 0],
                   [0, 0, 1]])
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(el), -np.sin(el)],
                   [0, np.sin(el),  np.cos(el)]])
    R = Rx @ Rz
    return (xyz @ R.T)[:, :2]

MODEL_2D = project(XYZ)
_rng = np.random.default_rng(42)
disp_idx = np.sort(_rng.choice(len(XYZ), size=4000, replace=False))
_pc2d = project(_patches["center"])

# ── Figure layout ─────────────────────────────────────────────────────────
fig = plt.figure(figsize=fig_size_in("figure2"))
fig.patch.set_facecolor("white")

FW, FH = 180.0, 108.0
ML, MR = 16.0, 4.0
MT, MB = 5.0, 11.0
content_w = FW - ML - MR
content_h = FH - MT - MB   # 92 mm

# Vertical layout (mm from bottom of figure)
# Bottom: common x-label (3mm)
# Bottom row curves
# Gap (includes colorbar)
# Top row panels

XLABEL_H = 5.0
BOT_ROW_H = 34.0
GAP_H = 16.0   # gap between top and bottom rows (holds Patch ID label + colorbar)
TOP_ROW_H = content_h - XLABEL_H - BOT_ROW_H - GAP_H

# Y positions from bottom
y_bot_0 = MB + XLABEL_H                    # bottom of curve axes
y_bot_1 = y_bot_0 + BOT_ROW_H              # top of curve axes
y_top_0 = y_bot_1 + GAP_H                  # bottom of top row (colorbar sits here)
y_top_1 = y_top_0 + TOP_ROW_H              # top of figure content

# Panel widths
GAP_AB = 6.0
W_A = (content_w - GAP_AB) * 0.32
W_B = (content_w - GAP_AB) * 0.68

# Bottom curve widths
GAP_CURVE = 5.0
W_CURVE = (content_w - 2 * GAP_CURVE) / 3.0

def fx(mm): return mm / FW
def fy(mm): return mm / FH

# ══════════════════════════════════════════════════════════════════════════
# PANEL (a): Fixed nominal partition
# ══════════════════════════════════════════════════════════════════════════
ax_a_x = ML
# Leave room for panel label at top
ax_a = fig.add_axes([fx(ax_a_x), fy(y_top_0), fx(W_A), fy(TOP_ROW_H - 3.0)])
ax_a.set_aspect("equal")
ax_a.set_xticks([]); ax_a.set_yticks([])
for sp in ax_a.spines.values():
    sp.set_visible(True); sp.set_color("#CCCCCC"); sp.set_linewidth(0.5)

# Nominal model
ax_a.scatter(MODEL_2D[disp_idx, 0], MODEL_2D[disp_idx, 1],
             s=0.3, c=NOMINAL_MODEL_COLOR, alpha=0.4, rasterized=True)

# Highlight patches 3, 20, 8
PATCH_COLORS = {3: "#2C8C7E", 20: "#386CB0", 8: "#C97A40"}
for pidx, clr in PATCH_COLORS.items():
    mask = PLAB[disp_idx] == pidx
    if np.any(mask):
        ax_a.scatter(MODEL_2D[disp_idx[mask], 0], MODEL_2D[disp_idx[mask], 1],
                     s=0.6, c=clr, alpha=0.9, rasterized=True)

# Bounds
x_lo, x_hi = MODEL_2D[:, 0].min() - 0.08, MODEL_2D[:, 0].max() + 0.08
y_lo, y_hi = MODEL_2D[:, 1].min() - 0.08, MODEL_2D[:, 1].max() + 0.08
ax_a.set_xlim(x_lo, x_hi)
ax_a.set_ylim(y_lo, y_hi)

# Three short leader lines with labels
leader_offsets = {
    3:  (0.12, -0.08),
    20: (-0.08, 0.15),
    8:  (-0.15, 0.10),
}
for pidx, (dx, dy) in leader_offsets.items():
    c2d = _pc2d[pidx]
    tx, ty = c2d[0] + dx, c2d[1] + dy
    # Draw leader line
    ax_a.plot([c2d[0], tx], [c2d[1], ty],
              color=PATCH_COLORS[pidx], lw=0.7, zorder=5)
    # Draw label with white background for readability
    ax_a.text(tx, ty, str(pidx),
              fontsize=8.0, color=PATCH_COLORS[pidx], fontweight="bold",
              ha="center", va="center", clip_on=False, zorder=6,
              bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                        edgecolor="none", alpha=0.85))

panel_label(ax_a, "(a)", dx=-0.05, dy=1.08, va="top")

# ══════════════════════════════════════════════════════════════════════════
# PANEL (b): VI residual structure heatmap
# ══════════════════════════════════════════════════════════════════════════
ax_b_x = ML + W_A + GAP_AB
ax_b = fig.add_axes([fx(ax_b_x), fy(y_top_0 + 2.5), fx(W_B), fy(TOP_ROW_H - 5.5)])

data = block_patch_med.copy()
masked_data = np.ma.masked_invalid(data)
cmap = plt.get_cmap(HEATMAP_CMAP).copy()
cmap.set_bad(color="#F0F0F0")

im = ax_b.imshow(masked_data, aspect="auto", cmap=cmap,
                 origin="lower", interpolation="nearest")

# Cell-boundary hairlines ONLY. The global style enables a major y-grid, whose
# ticks sit at cell CENTRES and would visually split every block in two; kill
# that inherited major grid and draw minor ticks placed at the -0.5 boundaries,
# so the heatmap reads as exactly 6 blocks x 24 patches.
ax_b.grid(False, which="both")
ax_b.set_xticks(np.arange(-0.5, 24, 1), minor=True)
ax_b.set_yticks(np.arange(-0.5, 6, 1), minor=True)
ax_b.grid(which="minor", color="#D8DCE0", linewidth=0.3)
ax_b.tick_params(which="minor", length=0)

ax_b.set_xticks(range(0, 24, 2))
ax_b.set_xticklabels(range(0, 24, 2), fontsize=6.5)
ax_b.set_yticks(range(6))
ax_b.set_yticklabels(range(6), fontsize=6.5)
ax_b.set_xlabel("Patch ID", fontsize=FONT_TICK, labelpad=2)
ax_b.set_ylabel("Block", fontsize=FONT_TICK)

panel_label(ax_b, "(b)", dx=-0.02, dy=1.08, va="top")

# Colorbar below heatmap, in the gap. Label BELOW the colorbar.
cbar_w = W_B * 0.5
cbar_h = 2.0
cbar_x = ax_b_x + (W_B - cbar_w) / 2.0
cbar_y = y_bot_1 + 11.5  # lift bar+label one text-line above the curve titles
cbar_ax = fig.add_axes([fx(cbar_x), fy(cbar_y), fx(cbar_w), fy(cbar_h)])
cbar = fig.colorbar(im, cax=cbar_ax, orientation="horizontal")
# Label below the colorbar (default position), separated from "Patch ID"
cbar.set_label("Block median patch residual (mm)", fontsize=6.5, color=TEXT_COLOR, labelpad=1)
cbar.ax.tick_params(labelsize=6, length=2)
cbar.outline.set_linewidth(0.4)
cbar.outline.set_edgecolor("#CCCCCC")

# ══════════════════════════════════════════════════════════════════════════
# BOTTOM ROW: 3 curves
# ══════════════════════════════════════════════════════════════════════════
curve_patches = [3, 20, 8]
curve_colors = {3: "#2C8C7E", 20: "#386CB0", 8: "#C97A40"}
# n = number of scans contributing to that patch's statistics (read from the
# derived file, not hard-coded); per-bin counts are archived separately.
_n3  = int(derived["n_frames_patch3"])
_n20 = int(derived["n_frames_patch20"])
_n8  = int(derived["n_frames_patch8"])
curve_titles = {3: f"Patch 3 (n={_n3})", 20: f"Patch 20 (n={_n20})",
                8: f"Patch 8 (n={_n8})"}

# Collect all stats for shared limits
all_med = []
shared_edges = derived["bin_edges"]  # (9,) shared across patches
for p in curve_patches:
    all_med.append(derived[f"bin_median_{p}"])
    all_med.append(derived[f"bin_iqr_low_{p}"])
    all_med.append(derived[f"bin_iqr_high_{p}"])
all_med = np.concatenate([v[~np.isnan(v)] for v in all_med])
y_max = np.nanmax(all_med) * 1.12
y_min = 0.0
x_min, x_max = shared_edges[0], shared_edges[-1]

# Common y label (far left)
fig.text(fx(3.5), fy((y_bot_0 + y_bot_1) / 2),
         "Patch-median residual (mm)", rotation=90, ha="center", va="center",
         fontsize=FONT_BODY, color=TEXT_COLOR)
# Common x label (bottom center)
fig.text(fx(ML + content_w / 2), fy(MB - 2.0),
         "Sensor range (m)", ha="center", va="bottom",
         fontsize=FONT_BODY, color=TEXT_COLOR)

panel_labels = {0: "(c)", 1: "(d)", 2: "(e)"}
for ci, p in enumerate(curve_patches):
    ax_cx = ML + ci * (W_CURVE + GAP_CURVE)
    ax_c = fig.add_axes([fx(ax_cx), fy(y_bot_0), fx(W_CURVE), fy(BOT_ROW_H)])

    meds = derived[f"bin_median_{p}"]
    iqr_lo = derived[f"bin_iqr_low_{p}"]
    iqr_hi = derived[f"bin_iqr_high_{p}"]
    centers = (shared_edges[:-1] + shared_edges[1:]) / 2.0
    color = curve_colors[p]
    valid = ~np.isnan(meds)

    ax_c.fill_between(centers[valid], iqr_lo[valid], iqr_hi[valid],
                      color=color, alpha=0.2, linewidth=0)
    ax_c.plot(centers[valid], meds[valid], "-o", color=color,
              markersize=2.5, linewidth=1.0, zorder=3)

    ax_c.set_xlim(x_min, x_max)
    ax_c.set_ylim(y_min, y_max)
    ax_c.set_title(curve_titles[p], fontsize=FONT_BODY, color=TEXT_COLOR,
                   pad=3, fontweight="normal")
    # Panel label top-left (outside axes, clear of centered title)
    panel_label(ax_c, panel_labels[ci], dx=-0.12, dy=1.04, va="top")

    if ci > 0:
        ax_c.set_yticklabels([])
    ax_c.tick_params(labelsize=FONT_TICK)

# ── Save ─────────────────────────────────────────────────────────────────
out_paths = save_figure(fig, "figure2", FIG_MAIN_DIR, dpi=600)
plt.close(fig)
print("\nFigure 2 saved:")
for ext, p in out_paths.items():
    print(f"  {ext}: {p}")

n3 = int(derived["n_frames_patch3"])
n20 = int(derived["n_frames_patch20"])
n8 = int(derived["n_frames_patch8"])
print(f"Frame counts: patch3={n3}, patch20={n20}, patch8={n8}")
