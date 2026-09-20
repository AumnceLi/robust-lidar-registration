"""
Supplementary figure: initialization threshold compliance (2x2).

Preserves the original Figure 6 joint-threshold pass rates:
  e_t <= 50 mm AND e_R <= 2 deg
across VI / IV / II / III, Raw vs Patch, L0..L6.
VI/IV zero curves are kept (not dropped). No error bars (directions are
correlated per frame). 174 x 104 mm.
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
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "figures", "redraw_20260917")
os.makedirs(OUT_DIR, exist_ok=True)

FRAMEWISE = _pp("final_three_experiments/01_coarse_initialization/e1_coarse_init_framewise.csv")

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "font.size": 8.0, "axes.titlesize": 9.0, "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.linewidth": 0.75, "axes.edgecolor": "#222222",
    "axes.labelcolor": "#222222", "text.color": "#222222",
    "xtick.color": "#222222", "ytick.color": "#222222",
    "xtick.major.width": 0.65, "ytick.major.width": 0.65,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": "#E7E7E7", "grid.linewidth": 0.4,
    "lines.linewidth": 1.4, "lines.markersize": 3.5,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

C_RAW = "#4D4D4D"; C_PATCH = "#009E73"
TRAJ_ORDER = ["VI", "IV", "II", "III"]
TRAJ_TAG = {"VI": "VI (development)", "IV": "IV",
            "II": "II", "III": "III (secondary)"}
LEVELS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]

df = pd.read_csv(FRAMEWISE)
sub = df[df.method.isin(["Raw", "Patch"])].copy()
sub["joint"] = ((sub.final_translation_error_mm <= 50) &
                (sub.final_rotation_error_deg <= 2))

FW, FH = 174.0, 104.0
MM = 25.4
fig = plt.figure(figsize=(FW/MM, FH/MM))
def fx(m): return m/FW
def fy(m): return m/FH

ML, MR = 14.0, 4.0
MT, MB = 14.0, 13.0
CW = FW-ML-MR; CH = FH-MT-MB
GAP_H, GAP_V = 8.0, 10.0
W = (CW-GAP_H)/2.0
H = (CH-GAP_V)/2.0
x_pos = np.arange(7)

for i, traj in enumerate(TRAJ_ORDER):
    col = i % 2; row = i // 2
    x0 = ML + col*(W+GAP_H)
    y0 = MB + (1-row)*(H+GAP_V)
    ax = fig.add_axes([fx(x0), fy(y0), fx(W), fy(H)])
    for method, color, ls, mk, mfc in [
        ("Raw", C_RAW, "--", "o", "none"),
        ("Patch", C_PATCH, "-", "s", C_PATCH)]:
        fracs = []
        for lv in LEVELS:
            s = sub[(sub.trajectory==traj)&(sub.method==method)&(sub.perturbation_level==lv)]
            fracs.append(s.joint.mean() if len(s) else np.nan)
        fracs = np.array(fracs)
        ax.plot(x_pos, fracs, color=color, ls=ls, lw=1.4, marker=mk,
                markersize=4.0, markerfacecolor=mfc,
                markeredgecolor=color, markeredgewidth=1.2)
    ax.set_xlim(-0.4, 6.4)
    ax.set_ylim(-0.025, 1.025)
    ax.set_xticks(x_pos); ax.set_xticklabels(LEVELS, fontsize=7.5)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0", "0.25", "0.5", "0.75", "1.0"], fontsize=7.5)
    ax.set_title(TRAJ_TAG[traj], fontsize=9, pad=3)
    # annotate zero curves
    if traj in ("VI", "IV"):
        ax.text(0.5, 0.5, "Both methods: 0", transform=ax.transAxes,
                fontsize=7.5, ha="center", va="center", color="#666666")
    letter = "(A)" if i==0 else ("(B)" if i==1 else ("(C)" if i==2 else "(D)"))
    ax.text(-0.10, 1.04, letter, transform=ax.transAxes, fontsize=10,
            fontweight="bold", ha="left", va="bottom")

fig.text(fx(3.0), fy(MB+CH/2), "Fraction meeting criterion",
         rotation=90, ha="center", va="center", fontsize=8.5)
fig.text(fx(ML+CW/2), fy(3.5), "Initialization level",
         ha="center", va="center", fontsize=8.5)

handles = [
    Line2D([0],[0], color=C_RAW, ls="--", lw=1.4, marker="o", markersize=4.0,
           markerfacecolor="none", markeredgecolor=C_RAW, markeredgewidth=1.2, label="Raw"),
    Line2D([0],[0], color=C_PATCH, ls="-", lw=1.4, marker="s", markersize=4.0,
           markerfacecolor=C_PATCH, markeredgecolor=C_PATCH, label="Patch"),
]
fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.99),
           ncol=2, fontsize=8, frameon=False, handletextpad=0.4, columnspacing=2.0)

out_pdf = os.path.join(OUT_DIR, "figS_initialization_threshold.pdf")
out_png = os.path.join(OUT_DIR, "figS_initialization_threshold.png")
fig.savefig(out_pdf, format="pdf")
fig.savefig(out_png, format="png", dpi=600)
plt.close(fig)
print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")

# print pass-rate table for notes
print("\nPass rates (joint e_t<=50mm & e_R<=2deg):")
for traj in TRAJ_ORDER:
    for method in ["Raw","Patch"]:
        row=[]
        for lv in LEVELS:
            s=sub[(sub.trajectory==traj)&(sub.method==method)&(sub.perturbation_level==lv)]
            row.append(f"{s.joint.mean():.2f}")
        print(f"  {traj} {method:6s} " + " ".join(row))
