"""
Figure 1 (V2): Mechanism flowchart — Correction from VI history + Query registration.
180 x 116 mm. Ast 2026-09-14 revision:
  * node titles live INSIDE the node's top title band, so input arrows meet the
    node edge without crossing an external title;
  * the green corrected-geometry -> ICP link is ONE connector with a single
    arrowhead that lands exactly on the ICP top edge (no extra hand-drawn port
    triangle, hence no double arrowhead);
  * Full short note sits directly BELOW the Correction-field node and feeds it;
  * ICP schematic occupies >= half the node width (update correspondences /
    rigid pose update);
  * row band labels and an explicit fixed-correspondence note on the bottom strip.
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
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle, Circle

from colors import METHOD_COLORS, NOMINAL_MODEL_COLOR, TEXT_COLOR
from figure_style import (apply_style, save_figure,
                           fig_size_in, FONT_BODY, FONT_TITLE, FONT_SECOND)
from paths import SRC, FIG_MAIN_DIR

apply_style()

# ── Load geometry data ────────────────────────────────────────────────────
print("Loading model data...")
_model = np.load(SRC["model_cache"], allow_pickle=True)
XYZ = _model["xyz"]
_patches = np.load(SRC["patches"], allow_pickle=True)
PLAB = _patches["lab"]
_frozen = np.load(SRC["frozen_field"], allow_pickle=True)
VREP = _frozen["Vmean"][250]
_scan = np.load(os.path.join(SRC["scan_dir_vi"], "scan_0000.npz"), allow_pickle=True)
SCAN_ALIGNED = _scan["aligned"]
_scan_q = np.load(os.path.join(SRC["scan_dir_vi"], "scan_0250.npz"), allow_pickle=True)
QUERY_ALIGNED = _scan_q["aligned"]

# ── Orthographic projection ──────────────────────────────────────────────
def project(xyz, elev=25.0, azim=-60.0):
    el = np.radians(elev); az = np.radians(azim)
    Rz = np.array([[np.cos(az), -np.sin(az), 0], [np.sin(az), np.cos(az), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(el), -np.sin(el)], [0, np.sin(el), np.cos(el)]])
    R = Rx @ Rz
    return (xyz @ R.T)[:, :2]

print("Projecting model...")
MODEL_2D = project(XYZ)
x_lo, x_hi = MODEL_2D[:, 0].min() - 0.05, MODEL_2D[:, 0].max() + 0.05
y_lo, y_hi = MODEL_2D[:, 1].min() - 0.05, MODEL_2D[:, 1].max() + 0.05
_rng = np.random.default_rng(42)
disp_idx = np.sort(_rng.choice(len(XYZ), size=3000, replace=False))

# ── Figure ────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=fig_size_in("figure1"))
fig.patch.set_facecolor("white")

# Ast spec node grid (mm, origin top-left), converted to bottom-up figure frac.
FW, FH = 180.0, 116.0
NW, NH = 42.0, 32.0
COL_X = [12.0, 69.0, 126.0]            # left edge of the three columns
CAL_TOP, CAL_BOT = 104.0, 72.0         # bottom-up y of calibration row
REG_TOP, REG_BOT = 50.0, 18.0          # bottom-up y of registration row

def fx(mm):  return mm / FW
def fy(mm):  return mm / FH

def draw_node(col_idx, top_mm, bot_mm):
    x = fx(COL_X[col_idx]); w = fx(NW)
    ax = fig.add_axes([x, fy(bot_mm), w, fy(top_mm - bot_mm)])
    ax.set_facecolor("white"); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(True); sp.set_color("#B8BEC4"); sp.set_linewidth(0.6)
    ax.set_xlim(x_lo, x_hi); ax.set_ylim(y_lo, y_hi)
    return ax

def node_title(ax, text, dy=0.965):
    # title INSIDE the node, in the top title band, white pad so it stays legible
    ax.text(0.5, dy, text, transform=ax.transAxes, ha="center", va="top",
            fontsize=FONT_BODY, color=TEXT_COLOR, linespacing=1.15,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.2))

# ══════════════════════════════════════════════════════════════════════════
# ROW BAND LABELS (horizontal, left-aligned to the row)
# ══════════════════════════════════════════════════════════════════════════
fig.text(fx(COL_X[0]), fy(110.6), "Correction from VI history",
         ha="left", va="center", fontsize=FONT_TITLE, color="#525C64", fontweight="bold")
fig.text(fx(COL_X[0]), fy(53.4), "Query registration",
         ha="left", va="center", fontsize=FONT_TITLE, color="#525C64", fontweight="bold")

# ══════════════════════════════════════════════════════════════════════════
# CALIBRATION ROW
# ══════════════════════════════════════════════════════════════════════════
print("Cal Node 1...")
ax = draw_node(0, CAL_TOP, CAL_BOT)
ax.scatter(MODEL_2D[disp_idx, 0], MODEL_2D[disp_idx, 1],
           s=0.3, c=NOMINAL_MODEL_COLOR, alpha=0.5, rasterized=True)
scan2d = project(SCAN_ALIGNED)
ax.scatter(scan2d[:, 0], scan2d[:, 1], s=0.4, c=METHOD_COLORS["Raw"], alpha=0.6, rasterized=True)
node_title(ax, "Nominal model +\ncalibrated VI scans")

print("Cal Node 2...")
ax = draw_node(1, CAL_TOP, CAL_BOT)
ax.scatter(MODEL_2D[disp_idx, 0], MODEL_2D[disp_idx, 1],
           s=0.3, c=NOMINAL_MODEL_COLOR, alpha=0.25, rasterized=True)
patch_hl = {0: "#E8D5B7", 3: "#B7D4CE", 8: "#D4C5E0", 10: "#F0D0B0", 15: "#B0C4DE", 20: "#C8E6C9"}
for pidx, clr in patch_hl.items():
    mask = PLAB[disp_idx] == pidx
    if np.any(mask):
        ax.scatter(MODEL_2D[disp_idx[mask], 0], MODEL_2D[disp_idx[mask], 1],
                   s=0.5, c=clr, alpha=0.8, rasterized=True)
pc2d = project(_patches["center"])
for pidx in [3, 8, 20]:
    c2d = pc2d[pidx]
    v = VREP[pidx] * 2.0
    v2d = project(v.reshape(1, 3)).flatten()
    ax.annotate("", xy=c2d + v2d, xytext=c2d,
                arrowprops=dict(arrowstyle="->", color="#525B63", lw=0.8))
node_title(ax, "Correction field")
# fixed vs reference-view-conditioned field, small note at the node bottom
ax.text(0.5, 0.03, r"fixed $\mu_j$ (Patch) $\cdot$ $\mu_j(z_{\mathrm{ref}})$ (Full)",
        transform=ax.transAxes, ha="center", va="bottom",
        fontsize=6.3, color="#525C64",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=0.8))

print("Cal Node 3...")
ax = draw_node(2, CAL_TOP, CAL_BOT)
point_corr = VREP[PLAB]
corr_xyz = XYZ + point_corr * 1.5
corr_2d = project(corr_xyz[disp_idx])
ax.scatter(corr_2d[:, 0], corr_2d[:, 1],
           s=0.3, c=NOMINAL_MODEL_COLOR, alpha=0.5, rasterized=True)
edge_mask = PLAB[disp_idx] == 3
edge_local = np.where(edge_mask)[0]
if len(edge_local) > 5:
    pick = np.sort(_rng.choice(len(edge_local), 5, replace=False))
    for ei in pick:
        pi = disp_idx[edge_local[ei]]
        p_before = MODEL_2D[pi]
        p_after = project(corr_xyz[pi:pi+1]).flatten()
        ax.annotate("", xy=p_after, xytext=p_before,
                    arrowprops=dict(arrowstyle="->", color=METHOD_COLORS["Patch"], lw=0.7))
node_title(ax, "Corrected geometry")
ax.text(0.5, 0.03, r"$m_i^{corr}$", transform=ax.transAxes, ha="center", va="bottom",
        fontsize=7.0, color="#525C64",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=0.8))

# ══════════════════════════════════════════════════════════════════════════
# REGISTRATION ROW
# ══════════════════════════════════════════════════════════════════════════
print("Reg Node 1...")
ax = draw_node(0, REG_TOP, REG_BOT)
q2d = project(QUERY_ALIGNED)
ax.scatter(MODEL_2D[disp_idx, 0], MODEL_2D[disp_idx, 1],
           s=0.2, c=NOMINAL_MODEL_COLOR, alpha=0.2, rasterized=True)
ax.scatter(q2d[:, 0], q2d[:, 1], s=0.4, c=METHOD_COLORS["Raw"], alpha=0.6, rasterized=True)
node_title(ax, "Query scan")

# Node 2: ICP with rematching — ABSTRACT schematic in axes fraction so it fills
# >= half the node width and clearly shows correspondence update + rigid update.
print("Reg Node 2 (abstract)...")
ax = draw_node(1, REG_TOP, REG_BOT)
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("auto")
rng_s = np.random.default_rng(123)
n_p = 9
# reference (light) arc upper-left -> lower-right; query (dark) offset = misalign
rx = np.linspace(0.16, 0.62, n_p)
ry = 0.62 + 0.16 * np.sin(np.linspace(0, np.pi, n_p)) + rng_s.normal(0, 0.012, n_p)
qx = rx + 0.16 + rng_s.normal(0, 0.012, n_p)
qy = ry - 0.20 + rng_s.normal(0, 0.012, n_p)
ax.scatter(rx, ry, s=26, c=NOMINAL_MODEL_COLOR, zorder=3, edgecolors="none")
ax.scatter(qx, qy, s=26, c=METHOD_COLORS["Raw"], zorder=3, edgecolors="none")
for i in range(n_p):
    ax.annotate("", xy=(rx[i], ry[i]), xytext=(qx[i], qy[i]),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color="#525B63", lw=0.55, alpha=0.75))
# rigid pose-update cue: bold arrow moving the matched set, lower band
ax.annotate("", xy=(0.86, 0.20), xytext=(0.30, 0.20), xycoords="axes fraction",
            arrowprops=dict(arrowstyle="-|>", color=METHOD_COLORS["Patch"], lw=1.3,
                            mutation_scale=11))
ax.text(0.58, 0.10, "rigid pose update", transform=ax.transAxes, ha="center",
        va="center", fontsize=6.2, color="#525C64")
node_title(ax, "ICP with rematching")

print("Reg Node 3...")
ax = draw_node(2, REG_TOP, REG_BOT)
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("auto")
ax.text(0.5, 0.58, r"$\hat{T} = (\hat{R},\,\hat{t})$",
        ha="center", va="center", transform=ax.transAxes,
        fontsize=13, color=TEXT_COLOR)
ax.text(0.5, 0.22, "Reference-relative\nevaluation: $e_t, e_R$",
        ha="center", va="center", transform=ax.transAxes,
        fontsize=6.8, color="#888888", style="italic", linespacing=1.3)
node_title(ax, "Estimated pose")

# ══════════════════════════════════════════════════════════════════════════
# FLOW ARROWS (one overlay axes, single figure-fraction coordinate system)
# ══════════════════════════════════════════════════════════════════════════
ax_flow = fig.add_axes([0, 0, 1, 1]); ax_flow.set_xlim(0, 1); ax_flow.set_ylim(0, 1); ax_flow.axis("off")
arrow_kw = dict(arrowstyle="-|>", color="#525B63", lw=1.1, mutation_scale=9, shrinkA=2, shrinkB=2)

def node_right(col):   return fx(COL_X[col] + NW)
def node_left(col):    return fx(COL_X[col])

# Within-row horizontal arrows (cal row mid y=88, reg row mid y=34)
for ci in range(2):
    ax_flow.add_patch(FancyArrowPatch((node_right(ci), fy(88)), (node_left(ci+1), fy(88)),
                      transform=fig.transFigure, **arrow_kw))
    ax_flow.add_patch(FancyArrowPatch((node_right(ci), fy(34)), (node_left(ci+1), fy(34)),
                      transform=fig.transFigure, **arrow_kw))

# Green connector: Corrected geometry bottom -> inter-row channel -> ICP TOP edge.
# Ast route (top-down mm) (147,44)->(147,58)->(90,58)->(90,66); one arrowhead only,
# on the final segment, landing exactly on the ICP top edge.
GREEN = METHOD_COLORS["Patch"]
x_src = fx(COL_X[2] + NW / 2.0)     # 147
x_dst = fx(COL_X[1] + NW / 2.0)     # 90 = ICP centre
y_cal_bot = fy(CAL_BOT)             # 72
y_channel = fy(58.0)                # inter-row horizontal channel
y_icp_top = fy(REG_TOP)             # 50 = ICP top edge
ax_flow.plot([x_src, x_src], [y_cal_bot, y_channel], color=GREEN, lw=1.1, solid_capstyle="butt")
ax_flow.plot([x_src, x_dst], [y_channel, y_channel], color=GREEN, lw=1.1, solid_capstyle="butt")
# single arrowhead on the final vertical segment, head lands on the edge
ax_flow.add_patch(FancyArrowPatch((x_dst, y_channel), (x_dst, y_icp_top),
                                  transform=fig.transFigure, arrowstyle="-|>",
                                  color=GREEN, lw=1.1, mutation_scale=10,
                                  shrinkA=0, shrinkB=0))

# ── Full short note, directly BELOW the Correction-field node ─────────────
FULL_C = METHOD_COLORS["Full"]
fb_w = 34.0
fb_x0 = COL_X[1] + (NW - fb_w) / 2.0
fb_x1 = fb_x0 + fb_w
fb_bot, fb_top = 60.5, 68.5
ax_flow.add_patch(FancyBboxPatch(
    (fx(fb_x0), fy(fb_bot)), fx(fb_w), fy(fb_top - fb_bot),
    boxstyle="round,pad=0.004,rounding_size=0.008",
    transform=fig.transFigure, fill=True, facecolor="white",
    edgecolor=FULL_C, linewidth=0.8, linestyle="--", zorder=6))
fig.text(fx(fb_x0 + 2.0), fy(66.3), "Full: reference-view query",
         ha="left", va="center", fontsize=6.8, color=FULL_C, fontweight="bold", zorder=7)
fig.text(fx(fb_x0 + 2.0), fy(62.9), "view weighting + equal-scan mean",
         ha="left", va="center", fontsize=6.3, color=TEXT_COLOR, zorder=7)
# one short dashed arrow from the note UP to the Correction-field bottom edge
ax_flow.add_patch(FancyArrowPatch((fx(COL_X[1] + NW/2), fy(fb_top)),
                                  (fx(COL_X[1] + NW/2), fy(CAL_BOT)),
                                  transform=fig.transFigure, arrowstyle="-|>",
                                  color=FULL_C, lw=0.9, linestyle="--",
                                  mutation_scale=7, shrinkA=0, shrinkB=0, zorder=5))

# ══════════════════════════════════════════════════════════════════════════
# BOTTOM MECHANISM STRIP
# ══════════════════════════════════════════════════════════════════════════
strip_x = fx(8.0); strip_w = fx(164.0)
strip_y, strip_h = 2.5, 10.5
strip_ax = fig.add_axes([strip_x, fy(strip_y), strip_w, fy(strip_h)])
strip_ax.set_xlim(0, 1); strip_ax.set_ylim(0, 1); strip_ax.axis("off")
strip_ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, edgecolor="#D7DBE0",
                             lw=0.5, transform=strip_ax.transAxes))
strip_ax.text(0.015, 0.5, r"$\delta_{PA} = P_{J,W}\,\delta$",
              ha="left", va="center", fontsize=9.0, color=TEXT_COLOR)
strip_ax.text(0.17, 0.5,
              r"$\Delta\xi_{corr} \approx -H_{GN}^{\dagger}\,J^{\top}W(\delta - A_{\pi}\mu)$",
              ha="left", va="center", fontsize=9.0, color=TEXT_COLOR)
strip_ax.text(0.66, 0.5,
              "Fixed correspondences and fixed J, W; local approximation.\n"
              "ICP itself re-matches correspondences.",
              ha="left", va="center", fontsize=6.8, color="#6A727A", style="italic",
              linespacing=1.3)

# ── Save ─────────────────────────────────────────────────────────────────
out_paths = save_figure(fig, "figure1", FIG_MAIN_DIR, dpi=600)
plt.close(fig)
print("\nFigure 1 saved:")
for ext, p in out_paths.items():
    print(f"  {ext}: {p}")
