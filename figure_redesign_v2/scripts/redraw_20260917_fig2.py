"""
Redraw Figure 2 (2026-09-17 specification).

174 x 146 mm, cross-column.
  Top row:    (A) Nominal geometry (~58 mm) | (B) 6x24 residual heatmap with right colorbar
  Bottom row: (C) Patch 3 | (D) Patch 20 | (E) Patch 8  -- shared range-binned axes

Data are reused from the frozen derivation (compute_figure2_data.py):
  - within-scan per-patch median residual magnitude (mm)
  - block-level median across scans (6 VI blocks x 24 patches)
  - 8 equal-width range bins over vrange [8.747, 14.802] m
No numbers are transcribed from old PNG/PDF.
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

import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.font_manager as fm

# ---------------------------------------------------------------------------
# Output / paths
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DERIVED = os.path.join(ROOT, "data", "derived")
OUT_DIR = os.path.join(ROOT, "figures", "redraw_20260917")
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_NPZ = _pp("structured_mismatch_phase0/scripts/cache/model_cache.npz")
PATCHES_NPZ = _pp("structured_mismatch_phase0/scripts/cache/patches.npz")

# ---------------------------------------------------------------------------
# Style (final printed size 174 mm width)
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "font.size": 8.0,
    "axes.titlesize": 9.0,
    "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 8.0,
    "axes.linewidth": 0.75,
    "axes.edgecolor": "#222222",
    "axes.labelcolor": "#222222",
    "text.color": "#222222",
    "xtick.color": "#222222",
    "ytick.color": "#222222",
    "xtick.major.width": 0.65,
    "ytick.major.width": 0.65,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": "#E7E7E7",
    "grid.linewidth": 0.4,
    "lines.linewidth": 1.4,
    "lines.markersize": 3.5,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})

# ---------------------------------------------------------------------------
# Colour table (per 2026-09-17 spec)
# ---------------------------------------------------------------------------
C_P3  = "#0072B2"   # blue
C_P20 = "#D55E00"   # orange-red
C_P8  = "#7B3294"   # purple
C_GRAY = "#AEB8C2"  # darker grey so main body/connectors read
C_TEXT = "#222222"

PATCH_COLOR = {3: C_P3, 20: C_P20, 8: C_P8}
PATCH_MARKER = {3: "o", 20: "s", 8: "^"}
TARGET_PATCHES = [3, 20, 8]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
derived = np.load(os.path.join(DATA_DERIVED, "figure2_residual_stats.npz"),
                  allow_pickle=True)
block_patch = derived["block_patch_med"]   # (6, 24) mm
bin_edges = derived["bin_edges"]           # (9,) m
n3  = int(derived["n_frames_patch3"])
n20 = int(derived["n_frames_patch20"])
n8  = int(derived["n_frames_patch8"])

model = np.load(MODEL_NPZ, allow_pickle=True)
XYZ = model["xyz"].astype(np.float64)
patches = np.load(PATCHES_NPZ, allow_pickle=True)
PLAB = patches["lab"].astype(int)
PCEN = patches["center"].astype(np.float64)

# ---------------------------------------------------------------------------
# 2D orthographic projection (fixed camera, identical to existing v2)
# ---------------------------------------------------------------------------
def project(xyz, elev=25.0, azim=-60.0):
    el = np.radians(elev); az = np.radians(azim)
    Rz = np.array([[np.cos(az), -np.sin(az), 0],
                   [np.sin(az),  np.cos(az), 0],
                   [0, 0, 1]])
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(el), -np.sin(el)],
                   [0, np.sin(el),  np.cos(el)]])
    R = Rx @ Rz
    return (xyz @ R.T)[:, :2]

MODEL_2D = project(XYZ)
PCEN_2D = project(PCEN)

# Deterministic display down-sample of the grey background (statistics are
# still computed on the full data; this only affects panel A rendering).
rng = np.random.default_rng(42)
bg_idx = np.sort(rng.choice(len(XYZ), size=6000, replace=False))

# Highlighted patch points kept complete (no down-sample) but capped for speed.
def patch_points_2d(pid, max_pts=3000):
    idx = np.where(PLAB == pid)[0]
    if len(idx) > max_pts:
        idx = np.sort(rng.choice(idx, size=max_pts, replace=False))
    return MODEL_2D[idx]

# ---------------------------------------------------------------------------
# Figure canvas (mm)
# ---------------------------------------------------------------------------
FW, FH = 174.0, 138.0
MM = 25.4
fig = plt.figure(figsize=(FW / MM, FH / MM))

def fx(mm): return mm / FW
def fy(mm): return mm / FH

# Margins
ML, MR = 13.0, 10.0
MT, MB = 8.0, 12.0
CW = FW - ML - MR   # content width  = 151
CH = FH - MT - MB

# Vertical: top row 62, gap ~14 for shared note, bottom row 42
TOP_H = 62.0
BOT_H = 42.0
GAP_H = CH - TOP_H - BOT_H

# y positions (mm from bottom of figure)
y_bot_lo = MB
y_bot_hi = MB + BOT_H
y_top_lo = MB + BOT_H + GAP_H
y_top_hi = MB + BOT_H + GAP_H + TOP_H

# Horizontal
GAP_AB = 9.0
W_A = 58.0
W_B = CW - W_A - GAP_AB          # 91
# B internal: plot + 2 mm gap + 3.5 mm colorbar
CB_W = 3.5
CB_GAP = 2.0
W_B_PLOT = W_B - CB_W - CB_GAP   # ~86.2

# Bottom row: 3 equal panels
GAP_C = 6.0
W_C = (CW - 2 * GAP_C) / 3.0     # ~48.7

# ---------------------------------------------------------------------------
# PANEL A — Nominal geometry
# ---------------------------------------------------------------------------
axA = fig.add_axes([fx(ML), fy(y_top_hi - TOP_H), fx(W_A), fy(TOP_H)])
axA.set_aspect("equal")
axA.set_xticks([]); axA.set_yticks([])
for s in axA.spines.values():
    s.set_visible(False)
axA.grid(False)

# background grey
axA.scatter(MODEL_2D[bg_idx, 0], MODEL_2D[bg_idx, 1],
            s=0.4, c=C_GRAY, alpha=0.55, rasterized=True, linewidths=0)
# highlighted patches
for pid in TARGET_PATCHES:
    pp = patch_points_2d(pid)
    axA.scatter(pp[:, 0], pp[:, 1], s=0.7, c=PATCH_COLOR[pid],
                alpha=0.95, rasterized=True, linewidths=0)

# Fit bounds with padding so model occupies ~75-85% of the panel
x_lo, x_hi = MODEL_2D[:, 0].min(), MODEL_2D[:, 0].max()
y_lo, y_hi = MODEL_2D[:, 1].min(), MODEL_2D[:, 1].max()
cx, cy = (x_lo + x_hi) / 2, (y_lo + y_hi) / 2
# panel aspect
panel_ar = W_A / TOP_H
data_ar = (x_hi - x_lo) / (y_hi - y_lo)
if data_ar > panel_ar:
    # width dominates
    dx = (x_hi - x_lo) * 0.55
    dy = dx / panel_ar
else:
    dy = (y_hi - y_lo) * 0.55
    dx = dy * panel_ar
axA.set_xlim(cx - dx, cx + dx)
axA.set_ylim(cy - dy, cy + dy)

# Labels: "Patch N" in dark grey, short leader lines in patch colour.
# Text placed in empty space near each patch; arrow endpoint on the patch centroid.
label_pos = {
    3:  (0.92, -0.85),    # left of patch 3 cluster, clear of B y-axis ticks
    20: (0.88,  0.45),    # left of patch 20, clear of B y-axis ticks
    8:  (-0.35, -0.15),   # left of patch 8
}
for pid in TARGET_PATCHES:
    tx, ty = label_pos[pid]
    axA.annotate(f"Patch {pid}",
                 xy=(PCEN_2D[pid, 0], PCEN_2D[pid, 1]),
                 xytext=(tx, ty),
                 fontsize=8.5, color="#222222",
                 ha="center", va="center", zorder=6,
                 arrowprops=dict(arrowstyle="-", color=PATCH_COLOR[pid],
                                 lw=0.6, shrinkA=0, shrinkB=2))

axA.set_title("Selected surface patches", fontsize=9, pad=3)
axA.text(-0.04, 1.01, "(A)", transform=axA.transAxes, fontsize=10,
         fontweight="bold", ha="left", va="bottom", color=C_TEXT)

# ---------------------------------------------------------------------------
# PANEL B — 6 x 24 residual heatmap
# ---------------------------------------------------------------------------
xB = ML + W_A + GAP_AB
axB = fig.add_axes([fx(xB), fy(y_top_hi - TOP_H + 3),
                    fx(W_B_PLOT), fy(TOP_H - 6)])

vmin = 0.0
vmax = 130.0
cmap = plt.get_cmap("Blues").copy()
# missing (none in this dataset) -> neutral grey
cmap.set_bad("#D9D9D9")
masked = np.ma.masked_invalid(block_patch)
im = axB.imshow(masked, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax,
                origin="upper", interpolation="nearest")

axB.grid(False, which="both")
# cell boundaries via minor ticks at -0.5
axB.set_xticks(np.arange(-0.5, 24, 1), minor=True)
axB.set_yticks(np.arange(-0.5, 6, 1), minor=True)
axB.grid(which="minor", color="white", linewidth=0.25)
axB.tick_params(which="minor", length=0)

# x ticks: all 24 labels (7.5 pt); 3/8/20 coloured
axB.set_xticks(range(24))
xlabels = []
for j in range(24):
    if j in PATCH_COLOR:
        xlabels.append(f"${j}$")
    else:
        xlabels.append(f"${j}$")
axB.set_xticklabels(range(24), fontsize=7.0, rotation=0)
for ticklab, j in zip(axB.get_xticklabels(), range(24)):
    if j in PATCH_COLOR:
        ticklab.set_color(PATCH_COLOR[j])
        ticklab.set_fontweight("bold")
axB.set_yticks(range(6))
axB.set_yticklabels(range(6), fontsize=7.5)
axB.set_xlabel("Patch ID", fontsize=8.5, labelpad=3)
axB.set_ylabel("VI block", fontsize=8.5)

# short coloured strip at top for patches 3, 20, 8 (outside the matrix, block 0 row)
for pid in TARGET_PATCHES:
    axB.plot([pid - 0.4, pid + 0.4], [-0.75, -0.75],
             color=PATCH_COLOR[pid], lw=2.2, clip_on=False, solid_capstyle="butt")

axB.set_title("Residuals across VI blocks", fontsize=9, pad=4)
axB.text(-0.03, 1.06, "(B)", transform=axB.transAxes, fontsize=10,
         fontweight="bold", ha="left", va="bottom", color=C_TEXT)

# Right vertical colorbar
cb_x = xB + W_B_PLOT + CB_GAP
cb_w = CB_W
cb_h = TOP_H - 8.0
cb_y = y_top_hi - TOP_H + 4.0
cax = fig.add_axes([fx(cb_x), fy(cb_y), fx(cb_w), fy(cb_h)])
cb = fig.colorbar(im, cax=cax, orientation="vertical")
cb.set_label("Median residual (mm)", fontsize=7.5, labelpad=2)
cb.set_ticks([0, 25, 50, 75, 100, 125])
cb.ax.tick_params(labelsize=7.0, length=2, width=0.65)
cb.outline.set_linewidth(0.6)
cb.outline.set_edgecolor("#999999")

# ---------------------------------------------------------------------------
# PANELS C-E — range-binned curves (shared x/y)
# ---------------------------------------------------------------------------
centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
x_lo, x_hi = 8.5, 15.0
y_lo, y_hi = 0.0, 140.0

fig.text(fx(2.5), fy((y_bot_lo + y_bot_hi) / 2),
         "Patch residual (mm)", rotation=90, ha="center", va="center",
         fontsize=8.5, color=C_TEXT)

panel_titles = {3: "Patch 3", 20: "Patch 20", 8: "Patch 8"}
panel_letters = {0: "(C)", 1: "(D)", 2: "(E)"}
patch_n = {3: n3, 20: n20, 8: n8}

for k, pid in enumerate(TARGET_PATCHES):
    ax = fig.add_axes([fx(ML + k * (W_C + GAP_C)), fy(y_bot_lo),
                      fx(W_C), fy(BOT_H)])
    meds = derived[f"bin_median_{pid}"]
    q25 = derived[f"bin_iqr_low_{pid}"]
    q75 = derived[f"bin_iqr_high_{pid}"]
    cnts = derived[f"bin_count_{pid}"]
    color = PATCH_COLOR[pid]
    mk = PATCH_MARKER[pid]
    valid = ~np.isnan(meds)

    ax.fill_between(centers[valid], q25[valid], q75[valid],
                    color=color, alpha=0.16, linewidth=0, zorder=1)
    ax.plot(centers[valid], meds[valid], color=color, lw=1.4,
            marker=mk, markersize=3.5, markerfacecolor=color,
            markeredgecolor=color, zorder=3)

    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)
    ax.set_xticks([9, 11, 13, 15])
    ax.set_yticks([0, 20, 40, 60, 80, 100, 120, 140])
    ax.tick_params(labelsize=7.5)
    if k > 0:
        ax.set_yticklabels([])
        ax.set_ylabel("")
    else:
        ax.set_ylabel("")
    ax.set_title(panel_titles[pid], fontsize=9, color=color, pad=3)
    ax.text(-0.02, 1.04, panel_letters[k], transform=ax.transAxes,
            fontsize=10, fontweight="bold", ha="left", va="bottom", color=C_TEXT)

# shared note in the gap between rows
fig.text(fx(ML + CW / 2), fy(MB + BOT_H + GAP_H / 2),
         "Lines: median; shading: IQR", ha="center", va="center",
         fontsize=7.5, color="#444444")

# common x label
fig.text(fx(ML + CW / 2), fy(4.5),
         "Sensor range (m)", ha="center", va="center",
         fontsize=8.5, color=C_TEXT)

# ---------------------------------------------------------------------------
# Save (no bbox_inches tight -> exact printed canvas size)
# ---------------------------------------------------------------------------
pdf_path = os.path.join(OUT_DIR, "figure2_final.pdf")
png_path = os.path.join(OUT_DIR, "figure2_final.png")
fig.savefig(pdf_path, format="pdf")
fig.savefig(png_path, format="png", dpi=600)
plt.close(fig)
print(f"Saved: {pdf_path}")
print(f"Saved: {png_path}")
print(f"n check: p3={n3} p20={n20} p8={n8}")
print(f"heatmap max={np.nanmax(block_patch):.1f} mm  vmax={vmax}")
print(f"bin edges={np.round(bin_edges,3)}")
