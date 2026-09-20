"""
Supplementary S2 (V2 redesign) — Initialization sensitivity.

Layout: 180 x 160 mm, 4 rows (trajectories) x 2 columns.
  Left:  Fraction meeting error thresholds (e_t <= 50 mm AND e_R <= 2 deg)
  Right: Final translation error, median + IQR

X-axis: discrete initialization levels (not equally spaced).
  L0 = reference (0/0), L1 = 10/0.5, L2 = 30/1, L3 = 50/2,
  L4 = 100/5, L5 = 200/10, L6 = 300/15
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

from colors import METHOD_COLORS, METHOD_MARKERS
from figure_style import apply_style, panel_label, save_figure, fig_size_in
from paths import SRC, FIG_SUPP_DIR, DATA_DERIVED_DIR, TRAJECTORY_ORDER

apply_style()

FIG_W_MM, FIG_H_MM = 180, 160

LEVEL_LABELS = ["ref\n0/0", "10/0.5", "30/1", "50/2", "100/5", "200/10", "300/15"]
LEVEL_KEYS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
METHODS = ["Raw", "Huber", "Patch", "PatchHuber"]

# Offset per method within each level group (for dodged bars/points)
METHOD_OFFSETS = {
    "Raw": -0.24, "Huber": -0.08, "Patch": 0.08, "PatchHuber": 0.24
}


def main():
    os.makedirs(DATA_DERIVED_DIR, exist_ok=True)

    df = pd.read_csv(SRC["e1_framewise"])

    # ── Compute per-trajectory, per-method, per-level stats ──────────
    rows = []
    for traj in TRAJECTORY_ORDER:
        for method in METHODS:
            for level in LEVEL_KEYS:
                sub = df[(df["trajectory"] == traj) &
                         (df["method"] == method) &
                         (df["perturbation_level"] == level)]
                n = len(sub)
                meet = ((sub["final_translation_error_mm"] <= 50) &
                        (sub["final_rotation_error_deg"] <= 2)).sum()
                frac = meet / n if n > 0 else 0.0
                et_med = sub["final_translation_error_mm"].median()
                et_q25 = sub["final_translation_error_mm"].quantile(0.25)
                et_q75 = sub["final_translation_error_mm"].quantile(0.75)
                rows.append({
                    "trajectory": traj, "method": method, "level": level,
                    "n": n, "frac_meet": frac, "meet_count": meet,
                    "et_med": et_med, "et_q25": et_q25, "et_q75": et_q75
                })

    stats_df = pd.DataFrame(rows)
    stats_df.to_csv(os.path.join(DATA_DERIVED_DIR, "figureS2_v2_stats.csv"),
                    index=False)

    # ── Build figure ──────────────────────────────────────────────────
    fig_w, fig_h = fig_size_in(FIG_W_MM, FIG_H_MM)
    fig = plt.figure(figsize=(fig_w, fig_h))

    # Increased left margin to accommodate trajectory labels outside y-axis
    gs = fig.add_gridspec(
        4, 2,
        hspace=0.55, wspace=0.30,
        left=0.12, right=0.97, top=0.90, bottom=0.10
    )

    x_pos = np.arange(len(LEVEL_KEYS))

    for row_idx, traj in enumerate(TRAJECTORY_ORDER):
        # ── Left panel: Fraction meeting thresholds ────────────────────
        ax_l = fig.add_subplot(gs[row_idx, 0])

        for method in METHODS:
            off = METHOD_OFFSETS[method]
            color = METHOD_COLORS[method]
            marker = METHOD_MARKERS[method]
            sub = stats_df[(stats_df["trajectory"] == traj) &
                           (stats_df["method"] == method)]
            fracs = [sub[sub["level"] == lv]["frac_meet"].values[0]
                     if len(sub[sub["level"] == lv]) > 0 else 0
                     for lv in LEVEL_KEYS]
            ax_l.plot(x_pos + off, fracs, marker=marker, color=color,
                      markersize=2.5, lw=0.8, label=method)

        ax_l.set_xticks(x_pos)
        ax_l.set_xticklabels(LEVEL_LABELS, fontsize=6)
        ax_l.set_ylim(-0.03, 1.05)
        # No per-row ylabel; shared figure-level label instead
        ax_l.grid(axis="y", color="#e8e8e8", lw=0.4)

        # Only put column title on first row
        if row_idx == 0:
            ax_l.set_title("Threshold compliance", fontsize=8, fontweight="bold")

        # Trajectory label on far left (outside y-axis area)
        ax_l.text(-0.28, 0.5, traj, transform=ax_l.transAxes,
                  fontsize=9, fontweight="bold", va="center", ha="right")

        # Panel label on first row
        if row_idx == 0:
            panel_label(ax_l, "a", dx=-0.32, dy=0.98, va="top")

        # ── Right panel: Final translation error ──────────────────────
        ax_r = fig.add_subplot(gs[row_idx, 1])

        for method in METHODS:
            off = METHOD_OFFSETS[method]
            color = METHOD_COLORS[method]
            marker = METHOD_MARKERS[method]
            sub = stats_df[(stats_df["trajectory"] == traj) &
                           (stats_df["method"] == method)]
            meds = [sub[sub["level"] == lv]["et_med"].values[0]
                    if len(sub[sub["level"] == lv]) > 0 else np.nan
                    for lv in LEVEL_KEYS]
            q25s = [sub[sub["level"] == lv]["et_q25"].values[0]
                    if len(sub[sub["level"] == lv]) > 0 else np.nan
                    for lv in LEVEL_KEYS]
            q75s = [sub[sub["level"] == lv]["et_q75"].values[0]
                    if len(sub[sub["level"] == lv]) > 0 else np.nan
                    for lv in LEVEL_KEYS]

            meds_arr = np.array(meds, dtype=float)
            q25_arr = np.array(q25s, dtype=float)
            q75_arr = np.array(q75s, dtype=float)
            x_arr = x_pos + off

            yerr_lower = meds_arr - q25_arr
            yerr_upper = q75_arr - meds_arr

            ax_r.errorbar(x_arr, meds_arr,
                          yerr=np.vstack([yerr_lower, yerr_upper]),
                          fmt=marker, color=color, markersize=2.5,
                          capsize=2, elinewidth=0.6, capthick=0.6,
                          label=method)

        ax_r.set_xticks(x_pos)
        ax_r.set_xticklabels(LEVEL_LABELS, fontsize=6)
        ax_r.grid(axis="y", color="#e8e8e8", lw=0.4)

        if row_idx == 0:
            ax_r.set_title("Final translation error (median + IQR)",
                          fontsize=8, fontweight="bold")
            panel_label(ax_r, "b", dx=-0.12, dy=0.98, va="top")

    # Shared y-axis label on far left of figure
    fig.text(0.02, 0.5, "Fraction",
             va="center", rotation="vertical", fontsize=8, fontweight="bold")

    # Shared legend at top (above first row titles)
    handles = [plt.Line2D([0], [0], marker=METHOD_MARKERS[m], color="w",
                          markerfacecolor=METHOD_COLORS[m], markersize=3.5,
                          label=m)
               for m in METHODS]
    fig.legend(handles=handles, loc="upper center",
               bbox_to_anchor=(0.55, 0.985), ncol=4, fontsize=7,
               handletextpad=0.3, columnspacing=1.2)

    # X-axis label at bottom
    fig.text(0.5, 0.025, "Initialization perturbation (translation mm / rotation deg)",
             ha="center", fontsize=8)

    save_figure(fig, "figureS2", [FIG_SUPP_DIR])
    print(f"Figure S2 saved to {FIG_SUPP_DIR}")

    # Quick checks
    print("\n=== S2 Quick Checks ===")
    for traj in TRAJECTORY_ORDER:
        for method in ["Raw", "Patch"]:
            sub = stats_df[(stats_df["trajectory"] == traj) &
                           (stats_df["method"] == method)]
            frac0 = sub[sub["level"] == "L0"]["frac_meet"].values[0]
            print(f"{traj} {method:12s} L0 frac_meet={frac0:.3f} n={sub[sub['level']=='L0']['n'].values[0]}")


if __name__ == "__main__":
    main()
