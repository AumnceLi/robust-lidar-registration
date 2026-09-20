"""
Supplementary S3 (V2 redesign) — Estimated Full gap and Raw-minus-method distributions.

Layout: 180 x 100 mm, 1 row x 2 columns.
  (a) Estimated Full - Full local gap (reference-initialized), per trajectory
  (b) Raw-minus-method paired distributions, per trajectory grouped boxplots

Notes:
  - Estimated Full = G2 est_warmstart arm
  - First-pass reference pose initialization; view query and warm start both change
  - Not globally acquired
  - (a) uses median + IQR (descriptive)
  - (b) boxplots show full paired distribution per trajectory (IQR, not CI)
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
from matplotlib.patches import Patch

from colors import METHOD_COLORS, METHOD_MARKERS
from figure_style import apply_style, panel_label, save_figure, fig_size_in
from paths import V1_DERIVED_DIR, FIG_SUPP_DIR, DATA_DERIVED_DIR, TRAJECTORY_ORDER

apply_style()

FIG_W_MM, FIG_H_MM = 180, 100

# Methods to show in (b): Full and Est.Full per trajectory
B_METHODS = ["Full", "EstFull"]
B_METHOD_LABELS = ["Full", "Est. Full"]
B_COLORS = [METHOD_COLORS["Full"], "#D4A040"]
BOX_WIDTH = 0.32
GROUP_OFFSET = BOX_WIDTH / 2 + 0.05


def main():
    os.makedirs(DATA_DERIVED_DIR, exist_ok=True)

    # Load data
    gap = pd.read_csv(os.path.join(V1_DERIVED_DIR, "figureS3_estimated_gap_perframe.csv"))
    rmm = pd.read_csv(os.path.join(V1_DERIVED_DIR, "figureS3_raw_minus_method_perframe.csv"))

    # ── (a) Estimated Full - Full gap ────────────────────────────────
    gap_rows = []
    for traj in TRAJECTORY_ORDER:
        vals = gap[gap["trajectory"] == traj]["estfull_minus_full_mm"].values
        gap_rows.append({
            "trajectory": traj,
            "median": np.median(vals),
            "q25": np.percentile(vals, 25),
            "q75": np.percentile(vals, 75),
            "n": len(vals)
        })
    gap_df = pd.DataFrame(gap_rows)
    gap_df.to_csv(os.path.join(DATA_DERIVED_DIR, "figureS3_v2_gap_stats.csv"),
                  index=False)

    # ── Build figure ──────────────────────────────────────────────────
    fig_w, fig_h = fig_size_in(FIG_W_MM, FIG_H_MM)
    fig = plt.figure(figsize=(fig_w, fig_h))

    gs = fig.add_gridspec(
        1, 2,
        wspace=0.28,
        left=0.08, right=0.97, top=0.88, bottom=0.14
    )

    # ═══════════════════════════════════════════════════════════════════
    # (a) Estimated Full - Full gap
    # ═══════════════════════════════════════════════════════════════════
    ax_a = fig.add_subplot(gs[0, 0])

    x_pos = np.arange(len(TRAJECTORY_ORDER))
    colors_gap = METHOD_COLORS["Full"]

    for i, traj in enumerate(TRAJECTORY_ORDER):
        row = gap_df[gap_df["trajectory"] == traj].iloc[0]
        med = row["median"]
        q25 = row["q25"]
        q75 = row["q75"]
        ax_a.errorbar(x_pos[i], med,
                      yerr=[[med - q25], [q75 - med]],
                      fmt="D", color=colors_gap, markersize=3.5,
                      capsize=3, elinewidth=0.9, capthick=0.9,
                      zorder=3)

    # Zero line
    ax_a.axhline(y=0, color="#999999", lw=0.8, ls="--", zorder=1)

    ax_a.set_xticks(x_pos)
    ax_a.set_xticklabels(TRAJECTORY_ORDER)
    ax_a.set_ylabel("Estimated Full − Full (mm)")
    ax_a.grid(axis="y", color="#e8e8e8", lw=0.4)
    panel_label(ax_a, "(a)")

    # ═══════════════════════════════════════════════════════════════════
    # (b) Raw-minus-method boxplots, per trajectory grouped
    # ═══════════════════════════════════════════════════════════════════
    ax_b = fig.add_subplot(gs[0, 1])

    # Build box data: for each trajectory group, 2 boxes (Full, Est.Full)
    all_data = []
    all_positions = []
    all_colors = []
    group_centers = []

    for t_idx, traj in enumerate(TRAJECTORY_ORDER):
        center = t_idx + 1  # 1, 2, 3, 4
        group_centers.append(center)
        for m_idx, method in enumerate(B_METHODS):
            vals = rmm[(rmm["method"] == method) &
                       (rmm["trajectory"] == traj)]["raw_minus_method_mm"].values
            offset = -GROUP_OFFSET if m_idx == 0 else GROUP_OFFSET
            all_data.append(vals)
            all_positions.append(center + offset)
            all_colors.append(B_COLORS[m_idx])

    bp = ax_b.boxplot(all_data, positions=all_positions,
                      widths=BOX_WIDTH, patch_artist=True,
                      showfliers=False,
                      medianprops=dict(color="black", lw=0.8),
                      whiskerprops=dict(color="#666666", lw=0.6),
                      capprops=dict(color="#666666", lw=0.6))

    for patch, color in zip(bp["boxes"], all_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor(color)
        patch.set_linewidth(0.6)

    # Zero line
    ax_b.axhline(y=0, color="#999999", lw=0.8, ls="--", zorder=1)

    ax_b.set_xticks(group_centers)
    ax_b.set_xticklabels(TRAJECTORY_ORDER, fontsize=7.5)
    ax_b.set_ylabel("Raw − method (mm)")
    ax_b.grid(axis="y", color="#e8e8e8", lw=0.4)
    panel_label(ax_b, "(b)")

    # Legend for methods (small, above panel)
    legend_handles = [
        Patch(facecolor=B_COLORS[i], alpha=0.7, edgecolor=B_COLORS[i],
              label=B_METHOD_LABELS[i])
        for i in range(len(B_METHODS))
    ]
    ax_b.legend(handles=legend_handles, loc="upper center",
                bbox_to_anchor=(0.5, 1.12), ncol=2, fontsize=6.5,
                handletextpad=0.3, columnspacing=0.8)

    # Save
    save_figure(fig, "figureS3", [FIG_SUPP_DIR])
    print(f"Figure S3 saved to {FIG_SUPP_DIR}")

    # ── Checks ────────────────────────────────────────────────────────
    print("\n=== S3 Gap Stats ===")
    print(gap_df.to_string())
    print("\n=== S3 Raw-minus-method per-trajectory medians ===")
    for method in B_METHODS:
        for traj in TRAJECTORY_ORDER:
            vals = rmm[(rmm["method"] == method) &
                       (rmm["trajectory"] == traj)]["raw_minus_method_mm"].values
            print(f"{method:8s} {traj}: n={len(vals)}, med={np.median(vals):.2f}, "
                  f"q25={np.percentile(vals,25):.2f}, q75={np.percentile(vals,75):.2f}")


if __name__ == "__main__":
    main()
