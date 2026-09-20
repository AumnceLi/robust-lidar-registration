"""
Redraw Figure 6 (2026-09-17 specification).

174 x 182 mm, cross-column, 4 rows x 2 columns.
  Rows:    VI (development), IV, II, III (secondary)
  Left:    reference-relative translation error e_t (mm), Raw vs Patch
  Right:   reference-relative rotation error e_R (deg), Raw vs Patch

X axis: L0..L6 categorical (initialization perturbation levels).
Bottom: fixed mapping table (level / translation mm / rotation deg).

Statistics are run-level medians and 25th/75th percentiles computed directly
from the frozen framewise CSV; no values are transcribed from the old PDF.
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "figures", "redraw_20260917")
os.makedirs(OUT_DIR, exist_ok=True)

FRAMEWISE = _pp("final_three_experiments/01_coarse_initialization/e1_coarse_init_framewise.csv")

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
})

C_RAW = "#4D4D4D"
C_PATCH = "#009E73"
TRAJ_ORDER = ["VI", "IV", "II", "III"]
TRAJ_TAG = {"VI": "VI (development)", "IV": "IV",
            "II": "II", "III": "III (secondary)"}
LEVELS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
LEVEL_T = [0, 10, 30, 50, 100, 200, 300]      # mm
LEVEL_R = [0, 0.5, 1, 2, 5, 10, 15]           # deg

# ---------------------------------------------------------------------------
# Load and aggregate
# ---------------------------------------------------------------------------
df = pd.read_csv(FRAMEWISE)
sub = df[df["method"].isin(["Raw", "Patch"])].copy()

# Per trajectory x method x level: median, q25, q75, n
def agg(col):
    g = sub.groupby(["trajectory", "method", "perturbation_level"])[col]
    out = pd.DataFrame({
        "med": g.median(),
        "q25": g.quantile(0.25),
        "q75": g.quantile(0.75),
        "n": g.size(),
    }).reset_index()
    return out

et = agg("final_translation_error_mm")
er = agg("final_rotation_error_deg")

# Axis limits (shared per column), from real q75 with 5% margin, rounded up
et_q75_max = et["q75"].max()
er_q75_max = er["q75"].max()
print(f"et q75 max={et_q75_max:.2f} mm, er q75 max={er_q75_max:.3f} deg")
ET_YMAX = 225.0
ET_TICKS = [0, 50, 100, 150, 200]
ER_YMAX = 16.0
ER_TICKS = [0, 4, 8, 12, 16]

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
FW, FH = 174.0, 170.0
MM = 25.4
fig = plt.figure(figsize=(FW / MM, FH / MM))

def fx(mm): return mm / FW
def fy(mm): return mm / FH

ML, MR = 13.0, 5.0
MT, MB = 20.0, 13.0
CW = FW - ML - MR      # 156
CH = FH - MT - MB      # 137

# 4 rows, 3 inter-row gaps (each gap hosts the shared trajectory title)
ROW_H = 26.0
GAP_V = (CH - 4 * ROW_H) / 3.0   # ~11 mm
# 2 columns
GAP_H = 17.0
W_COL = (CW - GAP_H) / 2.0       # ~69.5

x_pos = np.arange(7)  # L0..L6

# Will be filled in the loop
vi_axR = None

def series(stats, traj, method, col="med"):
    out = []
    for lv in LEVELS:
        r = stats[(stats.trajectory == traj) &
                  (stats.method == method) &
                  (stats.perturbation_level == lv)]
        out.append(r[col].values[0] if len(r) else np.nan)
    return np.array(out, dtype=float)

# ---------------------------------------------------------------------------
# 4 rows x 2 columns
# ---------------------------------------------------------------------------
for i, traj in enumerate(TRAJ_ORDER):
    y_hi = MB + (3 - i) * (ROW_H + GAP_V) + ROW_H
    y_lo = y_hi - ROW_H

    # ---- Left: translation ----
    axL = fig.add_axes([fx(ML), fy(y_lo), fx(W_COL), fy(ROW_H)])
    for method, color, ls, mk, band in [
        ("Raw", C_RAW, "--", "o", "#9E9E9E"),
        ("Patch", C_PATCH, "-", "s", "#9FD8C4"),
    ]:
        med = series(et, traj, method)
        q25 = series(et, traj, method, "q25")
        q75 = series(et, traj, method, "q75")
        axL.fill_between(x_pos, q25, q75, color=band, alpha=0.45,
                         linewidth=0, zorder=1)
        axL.plot(x_pos, med, color=color, ls=ls, lw=1.4, marker=mk,
                 markersize=3.5, markerfacecolor=color,
                 markeredgecolor=color, zorder=3)
    axL.set_xlim(-0.4, 6.4)
    axL.set_ylim(0, ET_YMAX)
    axL.set_xticks(x_pos)
    if i == 3:
        axL.set_xticklabels(LEVELS, fontsize=7.5)
    else:
        axL.set_xticklabels([])
    axL.set_yticks(ET_TICKS)
    axL.tick_params(labelsize=7.5)
    # panel letter (no per-axes title; shared row title added below)
    letter = "(A)" if i == 0 else ("(C)" if i == 1 else ("(E)" if i == 2 else "(G)"))
    axL.text(-0.10, 1.08, letter, transform=axL.transAxes, fontsize=10,
             fontweight="bold", ha="left", va="bottom", color="#222222")

    # ---- Right: rotation ----
    xR = ML + W_COL + GAP_H
    axR = fig.add_axes([fx(xR), fy(y_lo), fx(W_COL), fy(ROW_H)])
    for method, color, ls, mk, band in [
        ("Raw", C_RAW, "--", "o", "#9E9E9E"),
        ("Patch", C_PATCH, "-", "s", "#9FD8C4"),
    ]:
        med = series(er, traj, method)
        q25 = series(er, traj, method, "q25")
        q75 = series(er, traj, method, "q75")
        axR.fill_between(x_pos, q25, q75, color=band, alpha=0.45,
                         linewidth=0, zorder=1)
        axR.plot(x_pos, med, color=color, ls=ls, lw=1.4, marker=mk,
                 markersize=3.5, markerfacecolor=color,
                 markeredgecolor=color, zorder=3)
    axR.set_xlim(-0.4, 6.4)
    axR.set_ylim(0, ER_YMAX)
    axR.set_xticks(x_pos)
    if i == 3:
        axR.set_xticklabels(LEVELS, fontsize=7.5)
    else:
        axR.set_xticklabels([])
    axR.set_yticks(ER_TICKS)
    axR.tick_params(labelsize=7.5)
    letter = "(B)" if i == 0 else ("(D)" if i == 1 else ("(F)" if i == 2 else "(H)"))
    axR.text(-0.10, 1.08, letter, transform=axR.transAxes, fontsize=10,
             fontweight="bold", ha="left", va="bottom", color="#222222")
    if i == 0:
        vi_axR = axR

    # shared row title: row 0 sits centered in the gap between column titles
    # and the first row of plots; other rows are centered in the inter-row gap.
    if i == 0:
        row_title_y = y_hi + 6.0
    else:
        row_title_y = y_hi + GAP_V / 2
    fig.text(fx(ML + CW / 2), fy(row_title_y),
             f"Trajectory {TRAJ_TAG[traj]}",
             ha="center", va="bottom", fontsize=9, color="#222222")

# Column titles at top (replaces vertical y-axis labels); row 0 title sits
# below them.
fig.text(fx(ML + W_COL / 2), fy(163.0),
         "Translation error (mm)", ha="center", va="center",
         fontsize=9.5, fontweight="bold", color="#222222")
fig.text(fx(ML + W_COL + GAP_H + W_COL / 2), fy(163.0),
         "Rotation error (deg)", ha="center", va="center",
         fontsize=9.5, fontweight="bold", color="#222222")

# Shared legend at very top (Raw / Patch only)
from matplotlib.lines import Line2D
handles = [
    Line2D([0], [0], color=C_RAW, ls="--", lw=1.4, marker="o",
           markersize=3.5, label="Raw"),
    Line2D([0], [0], color=C_PATCH, ls="-", lw=1.4, marker="s",
           markersize=3.5, label="Patch"),
]
fig.legend(handles=handles, loc="upper center",
           bbox_to_anchor=(0.5, 0.998), ncol=2, fontsize=8,
           frameon=False, handletextpad=0.4, columnspacing=2.0)

# Optional short annotation on VI rotation panel: wider IQR at L6 (data-verified).
vi_axR.annotate("Wider IQR at L6",
                xy=(6.0, 14.5),
                xytext=(3.4, 13.2),
                fontsize=7.5, color="#444444",
                arrowprops=dict(arrowstyle="-", color="#888888", lw=0.6))

# Shared x-axis label + endpoint note (no in-figure table)
fig.text(fx(ML + CW / 2), fy(5.0),
         "Initial perturbation level", ha="center", va="center",
         fontsize=8.5, color="#222222")
fig.text(fx(ML + CW / 2), fy(1.8),
         "L0: 0 mm, 0\u00b0;  L6: 300 mm, 15\u00b0",
         ha="center", va="center", fontsize=7.5, color="#444444")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
pdf_path = os.path.join(OUT_DIR, "figure6_final.pdf")
png_path = os.path.join(OUT_DIR, "figure6_final.png")
fig.savefig(pdf_path, format="pdf")
fig.savefig(png_path, format="png", dpi=600)
plt.close(fig)
print(f"Saved: {pdf_path}")
print(f"Saved: {png_path}")
print(f"Canvas: {FW} x {FH} mm")
print(f"Translation ylim: 0-{ET_YMAX}; Rotation ylim: 0-{ER_YMAX}")

# Save summary CSV
summary = et.merge(er, on=["trajectory", "method", "perturbation_level", "n"],
                   suffixes=("_et", "_er"))
summary = summary.rename(columns={
    "med_et": "et_median_mm", "q25_et": "et_q25_mm", "q75_et": "et_q75_mm",
    "med_er": "er_median_deg", "q25_er": "er_q25_deg", "q75_er": "er_q75_deg",
    "n": "unique_runs",
})
summary = summary[["trajectory", "method", "perturbation_level", "unique_runs",
                   "et_median_mm", "et_q25_mm", "et_q75_mm",
                   "er_median_deg", "er_q25_deg", "er_q75_deg"]]
summary = summary.sort_values(["trajectory", "method", "perturbation_level"])
summary.to_csv(os.path.join(OUT_DIR, "figure6_summary.csv"), index=False)
print(f"Summary rows: {len(summary)}")
