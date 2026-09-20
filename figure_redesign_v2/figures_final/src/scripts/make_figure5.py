"""
Figure 5 (V2 redesign) — Effect, baselines, and rotation cost.

Layout: 180 x 112 mm
  Top row:    (a) Translation error (mm)   (b) Rotation error (deg)
  Bottom row: (c) Paired translation benefit (forest plot)  (d) Paired rotation change

Statistics hierarchy:
  (a)(b) marginal median + IQR (descriptive)
  (c)    frame-paired median + whole-block-bootstrap 95% CI
  (d)    frame-paired median + IQR (descriptive)
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
from matplotlib.lines import Line2D

from colors import METHOD_COLORS, METHOD_MARKERS, COMPARISON_COLORS, COMPARISON_MARKERS
from figure_style import apply_style, panel_label, save_figure, fig_size_in
from paths import (
    V1_DERIVED_DIR, FIG_MAIN_DIR, DATA_DERIVED_DIR,
    TRAJECTORY_ORDER, BOOTSTRAP_BLOCKS, COMMON_SUPPORT_COUNTS
)

apply_style()

# ── Parameters ──────────────────────────────────────────────────────────
B_BOOT = 2000
SEED = 42
FIG_W_MM, FIG_H_MM = 180, 114

METHODS_TRANS = ["Raw", "Huber", "Global-Vector", "Patch", "Full"]
METHODS_ROT = ["Raw", "Huber", "Patch", "Full"]
COMPARISONS = ["Patch vs Raw", "Patch vs Global-Vector", "Patch+Huber vs Huber"]

# Vertical offset per method on top-row panels
METHOD_OFFSETS = {
    "Raw": -0.28, "Huber": -0.14, "Global-Vector": 0.0,
    "Patch": 0.14, "Full": 0.28
}

# Vertical offset per comparison on bottom-left forest plot
COMP_OFFSETS = {
    "Patch vs Raw": 0.22,
    "Patch vs Global-Vector": 0.0,
    "Patch+Huber vs Huber": -0.22
}


def load_marginal():
    """Load marginal median/IQR from V1 derived data."""
    df = pd.read_csv(os.path.join(V1_DERIVED_DIR, "figure5_marginal_medians_iqr.csv"))
    return df


def load_paired_benefits():
    """Load per-frame paired benefits."""
    df = pd.read_csv(os.path.join(V1_DERIVED_DIR, "figure5_paired_benefits_perframe.csv"))
    return df


def load_rotation_cost():
    """Load per-frame rotation cost (PatchHuber - Huber)."""
    df = pd.read_csv(os.path.join(V1_DERIVED_DIR, "figure5_rotation_cost_perframe.csv"))
    return df


def block_bootstrap_ci(values, blocks, n_boot=B_BOOT, seed=SEED):
    """
    Whole-block bootstrap: resample blocks with replacement, concatenate,
    compute median, return 2.5/97.5 percentile CI.

    blocks: array of block indices for each value (same length as values).
    """
    rng = np.random.default_rng(seed)
    unique_blocks = np.unique(blocks)
    block_indices = {b: np.where(blocks == b)[0] for b in unique_blocks}
    n_blocks = len(unique_blocks)

    medians = np.empty(n_boot)
    for i in range(n_boot):
        chosen = rng.choice(unique_blocks, size=n_blocks, replace=True)
        sampled = np.concatenate([block_indices[b] for b in chosen])
        medians[i] = np.median(values[sampled])

    return np.percentile(medians, 2.5), np.percentile(medians, 97.5)


# ── Main ────────────────────────────────────────────────────────────────
def main():
    os.makedirs(DATA_DERIVED_DIR, exist_ok=True)

    marginal = load_marginal()
    benefits = load_paired_benefits()
    rotcost = load_rotation_cost()

    traj_x = {t: i for i, t in enumerate(TRAJECTORY_ORDER)}

    # ── Compute bootstrap CIs for (c) ──────────────────────────────────
    bootstrap_rows = []
    for comp in COMPARISONS:
        for traj in TRAJECTORY_ORDER:
            sub = benefits[(benefits["comparison"] == comp) &
                           (benefits["trajectory"] == traj)].sort_values("order")
            vals = sub["benefit_mm"].values
            blocks = sub["block"].values
            med = np.median(vals)
            lo, hi = block_bootstrap_ci(vals, blocks)
            bootstrap_rows.append({
                "comparison": comp, "trajectory": traj,
                "median": med, "ci_lo": lo, "ci_hi": hi,
                "n": len(vals)
            })
    boot_df = pd.DataFrame(bootstrap_rows)
    boot_df.to_csv(os.path.join(DATA_DERIVED_DIR, "figure5_v2_bootstrap_ci.csv"),
                   index=False)
    print("Bootstrap CIs computed:")
    print(boot_df.to_string())

    # ── Compute rotation cost IQR for (d) ───────────────────────────────
    rot_rows = []
    for traj in TRAJECTORY_ORDER:
        sub = rotcost[rotcost["trajectory"] == traj]
        vals = sub["rot_change_PatchHuber_minus_Huber_deg"].values
        rot_rows.append({
            "trajectory": traj,
            "median": np.median(vals),
            "q25": np.percentile(vals, 25),
            "q75": np.percentile(vals, 75),
            "n": len(vals)
        })
    rot_df = pd.DataFrame(rot_rows)
    rot_df.to_csv(os.path.join(DATA_DERIVED_DIR, "figure5_v2_rotation_iqr.csv"),
                  index=False)

    # ── Interval provenance (review §8.3): document, from the ACTUAL arrays,
    # exactly what every error bar represents — never named by appearance ──
    nb_benefit = {t: int(benefits.loc[benefits.trajectory == t, "block"].nunique())
                  for t in TRAJECTORY_ORDER}
    nb_rot = {t: int(rotcost.loc[rotcost.trajectory == t, "block"].nunique())
              for t in TRAJECTORY_ORDER}
    prov = []
    for _, r in marginal.iterrows():
        panel = "(a)" if r["field"] == "et_mm" else "(b)"
        prov.append(dict(panel=panel, series=f"{r['method']} / {r['trajectory']}",
                         center=round(float(r["median"]), 4),
                         lower=round(float(r["q25"]), 4), upper=round(float(r["q75"]), 4),
                         interval_type="descriptive IQR (Q25-Q75)",
                         sampling_unit="frame on the retained common-support subset",
                         n=int(r["n"]), n_blocks=nb_benefit[r["trajectory"]]))
    for _, r in boot_df.iterrows():
        prov.append(dict(panel="(c)", series=f"{r['comparison']} / {r['trajectory']}",
                         center=round(float(r["median"]), 4),
                         lower=round(float(r["ci_lo"]), 4), upper=round(float(r["ci_hi"]), 4),
                         interval_type="whole-block bootstrap 95% percentile CI",
                         sampling_unit="block; within-frame baseline-method differences resampled by whole block",
                         n=int(r["n"]), n_blocks=nb_benefit[r["trajectory"]]))
    for _, r in rot_df.iterrows():
        prov.append(dict(panel="(d)", series=f"Patch+Huber - Huber / {r['trajectory']}",
                         center=round(float(r["median"]), 4),
                         lower=round(float(r["q25"]), 4), upper=round(float(r["q75"]), 4),
                         interval_type="descriptive IQR (Q25-Q75)",
                         sampling_unit="paired frame (Patch+Huber minus Huber rotation error)",
                         n=int(r["n"]), n_blocks=nb_rot[r["trajectory"]]))
    prov_df = pd.DataFrame(prov)
    prov_df.to_csv(os.path.join(DATA_DERIVED_DIR, "figure5_interval_provenance.csv"),
                   index=False)
    print(f"[interval provenance] {len(prov_df)} rows -> figure5_interval_provenance.csv")

    # ── Build figure ────────────────────────────────────────────────────
    fig_w, fig_h = fig_size_in(FIG_W_MM, FIG_H_MM)
    fig = plt.figure(figsize=(fig_w, fig_h))

    # Grid: 2 rows, 2 cols, with space for top legend
    gs = fig.add_gridspec(
        2, 2,
        height_ratios=[1.0, 1.05],
        hspace=0.85, wspace=0.30,
        left=0.08, right=0.97, top=0.84, bottom=0.13
    )

    # ═══════════════════════════════════════════════════════════════════
    # (a) Translation error
    # ═══════════════════════════════════════════════════════════════════
    ax_a = fig.add_subplot(gs[0, 0])
    ax_a.axhline(y=0, color="#cccccc", lw=0.5, zorder=0)

    for method in METHODS_TRANS:
        off = METHOD_OFFSETS[method]
        color = METHOD_COLORS[method]
        marker = METHOD_MARKERS[method]
        for traj in TRAJECTORY_ORDER:
            row = marginal[(marginal["trajectory"] == traj) &
                           (marginal["method"] == method) &
                           (marginal["field"] == "et_mm")]
            if len(row) == 0:
                continue
            med = row["median"].values[0]
            q25 = row["q25"].values[0]
            q75 = row["q75"].values[0]
            x = traj_x[traj] + off
            ax_a.errorbar(x, med, yerr=[[med - q25], [q75 - med]],
                          fmt=marker, color=color, markersize=3,
                          capsize=2.5, elinewidth=0.7, capthick=0.7,
                          zorder=3)

    ax_a.set_xticks(range(len(TRAJECTORY_ORDER)))
    ax_a.set_xticklabels(TRAJECTORY_ORDER)
    ax_a.set_ylabel("Error (mm)")
    ax_a.set_xlim(-0.5, len(TRAJECTORY_ORDER) - 0.5)
    ax_a.grid(axis="y", color="#e8e8e8", lw=0.4, zorder=0)
    ax_a.set_title("Translation error", fontsize=9, pad=6)
    panel_label(ax_a, "(a)")

    # ═══════════════════════════════════════════════════════════════════
    # (b) Rotation error
    # ═══════════════════════════════════════════════════════════════════
    ax_b = fig.add_subplot(gs[0, 1])
    ax_b.axhline(y=0, color="#cccccc", lw=0.5, zorder=0)

    for method in METHODS_ROT:
        off = METHOD_OFFSETS[method]
        color = METHOD_COLORS[method]
        marker = METHOD_MARKERS[method]
        for traj in TRAJECTORY_ORDER:
            row = marginal[(marginal["trajectory"] == traj) &
                           (marginal["method"] == method) &
                           (marginal["field"] == "eR_deg")]
            if len(row) == 0:
                continue
            med = row["median"].values[0]
            q25 = row["q25"].values[0]
            q75 = row["q75"].values[0]
            x = traj_x[traj] + off
            ax_b.errorbar(x, med, yerr=[[med - q25], [q75 - med]],
                          fmt=marker, color=color, markersize=3,
                          capsize=2.5, elinewidth=0.7, capthick=0.7,
                          zorder=3)

    ax_b.set_xticks(range(len(TRAJECTORY_ORDER)))
    ax_b.set_xticklabels(TRAJECTORY_ORDER)
    ax_b.set_ylabel("Error (°)")
    ax_b.set_xlim(-0.5, len(TRAJECTORY_ORDER) - 0.5)
    ax_b.grid(axis="y", color="#e8e8e8", lw=0.4, zorder=0)
    ax_b.set_title("Rotation error", fontsize=9, pad=6)
    panel_label(ax_b, "(b)")

    # ═══════════════════════════════════════════════════════════════════
    # (c) Paired translation benefit — horizontal forest plot
    # ═══════════════════════════════════════════════════════════════════
    ax_c = fig.add_subplot(gs[1, 0])

    # Y positions: trajectories, reversed so VI on top
    y_pos_map = {t: len(TRAJECTORY_ORDER) - 1 - i for i, t in enumerate(TRAJECTORY_ORDER)}

    for comp in COMPARISONS:
        off = COMP_OFFSETS[comp]
        color = COMPARISON_COLORS[comp]
        marker = COMPARISON_MARKERS[comp]
        for traj in TRAJECTORY_ORDER:
            row = boot_df[(boot_df["comparison"] == comp) &
                          (boot_df["trajectory"] == traj)]
            if len(row) == 0:
                continue
            med = row["median"].values[0]
            lo = row["ci_lo"].values[0]
            hi = row["ci_hi"].values[0]
            y = y_pos_map[traj] + off
            ax_c.errorbar(med, y, xerr=[[med - lo], [hi - med]],
                          fmt=marker, color=color, markersize=3.5,
                          capsize=2.5, elinewidth=0.8, capthick=0.8,
                          zorder=3)

    # Zero line
    ax_c.axvline(x=0, color="#999999", lw=0.8, ls="--", zorder=1)

    ax_c.set_yticks(range(len(TRAJECTORY_ORDER)))
    ax_c.set_yticklabels([TRAJECTORY_ORDER[::-1][i] for i in range(len(TRAJECTORY_ORDER))])
    ax_c.set_xlabel("Translation benefit (mm)\nbaseline − method; positive = improvement",
                    fontsize=8)
    ax_c.grid(axis="x", color="#e8e8e8", lw=0.4, zorder=0)
    ax_c.set_title("Paired translation benefit", fontsize=9, pad=6)
    panel_label(ax_c, "(c)")

    # Comparison legend in the gap between rows (figure-level, centered)
    comp_handles = [
        Line2D([0], [0], marker=COMPARISON_MARKERS[c], color="w",
               markerfacecolor=COMPARISON_COLORS[c], markersize=4,
               label=c)
        for c in COMPARISONS
    ]
    fig.legend(handles=comp_handles, loc="lower center",
               bbox_to_anchor=(0.38, 0.48), ncol=3, fontsize=6.5,
               handletextpad=0.3, columnspacing=0.8)

    # ═══════════════════════════════════════════════════════════════════
    # (d) Paired rotation change — horizontal interval
    # ═══════════════════════════════════════════════════════════════════
    ax_d = fig.add_subplot(gs[1, 1])

    for _, row in rot_df.iterrows():
        traj = row["trajectory"]
        med = row["median"]
        q25 = row["q25"]
        q75 = row["q75"]
        y = y_pos_map[traj]
        # Same orange up-triangle as the "Patch+Huber vs Huber" series in (c),
        # so the comparison object is unambiguous.
        ax_d.errorbar(med, y, xerr=[[med - q25], [q75 - med]],
                      fmt=COMPARISON_MARKERS["Patch+Huber vs Huber"],
                      color=COMPARISON_COLORS["Patch+Huber vs Huber"],
                      markersize=3.8, capsize=2.5, elinewidth=0.9, capthick=0.9,
                      zorder=3)

    # Zero line
    ax_d.axvline(x=0, color="#999999", lw=0.8, ls="--", zorder=1)

    ax_d.set_yticks(range(len(TRAJECTORY_ORDER)))
    ax_d.set_yticklabels([TRAJECTORY_ORDER[::-1][i] for i in range(len(TRAJECTORY_ORDER))])
    ax_d.set_xlabel("Rotation error change (°)\npositive = larger error", fontsize=8)
    ax_d.grid(axis="x", color="#e8e8e8", lw=0.4, zorder=0)
    ax_d.set_title("Rotation change: Patch+Huber − Huber", fontsize=9, pad=6)
    panel_label(ax_d, "(d)")

    # ═══════════════════════════════════════════════════════════════════
    # Shared method legend at top of figure
    # ═══════════════════════════════════════════════════════════════════
    method_handles = [
        Line2D([0], [0], marker=METHOD_MARKERS[m], color="w",
               markerfacecolor=METHOD_COLORS[m], markersize=4,
               label=m)
        for m in METHODS_TRANS
    ]
    fig.legend(handles=method_handles, loc="upper center",
               bbox_to_anchor=(0.5, 0.97), ncol=5, fontsize=7,
               handletextpad=0.3, columnspacing=1.0)
    # Save
    save_figure(fig, "figure5", [FIG_MAIN_DIR])
    print(f"\nFigure 5 saved to {FIG_MAIN_DIR}")

    # ── Anchor checks ──────────────────────────────────────────────────
    checks = []
    # Raw translation medians
    for traj, expected in [("VI", 161.4), ("IV", 160.4), ("II", 66.1), ("III", 75.0)]:
        row = marginal[(marginal["trajectory"] == traj) &
                       (marginal["method"] == "Raw") &
                       (marginal["field"] == "et_mm")]
        got = row["median"].values[0]
        ok = abs(got - expected) < 0.5
        checks.append(f"Raw et {traj}: expected ~{expected}, got {got:.1f} {'OK' if ok else 'MISMATCH'}")

    # Patch translation medians
    for traj, expected in [("VI", 116.8), ("IV", 126.3), ("II", 41.8), ("III", 41.3)]:
        row = marginal[(marginal["trajectory"] == traj) &
                       (marginal["method"] == "Patch") &
                       (marginal["field"] == "et_mm")]
        got = row["median"].values[0]
        ok = abs(got - expected) < 0.5
        checks.append(f"Patch et {traj}: expected ~{expected}, got {got:.1f} {'OK' if ok else 'MISMATCH'}")

    # Full translation medians
    for traj, expected in [("VI", 76.9), ("IV", 82.9), ("II", 68.9), ("III", 51.2)]:
        row = marginal[(marginal["trajectory"] == traj) &
                       (marginal["method"] == "Full") &
                       (marginal["field"] == "et_mm")]
        got = row["median"].values[0]
        ok = abs(got - expected) < 0.5
        checks.append(f"Full et {traj}: expected ~{expected}, got {got:.1f} {'OK' if ok else 'MISMATCH'}")

    # GV translation medians
    for traj, expected in [("VI", 155.94), ("IV", 146.61), ("II", 51.16), ("III", 62.35)]:
        row = marginal[(marginal["trajectory"] == traj) &
                       (marginal["method"] == "Global-Vector") &
                       (marginal["field"] == "et_mm")]
        got = row["median"].values[0]
        ok = abs(got - expected) < 0.3
        checks.append(f"GV et {traj}: expected ~{expected}, got {got:.2f} {'OK' if ok else 'MISMATCH'}")

    # Patch vs GV median benefits
    for traj, expected in [("VI", 33.92), ("IV", 19.31), ("II", 0.24), ("III", 25.03)]:
        row = boot_df[(boot_df["comparison"] == "Patch vs Global-Vector") &
                      (boot_df["trajectory"] == traj)]
        got = row["median"].values[0]
        ok = abs(got - expected) < 0.3
        checks.append(f"Patch-GV benefit {traj}: expected ~{expected}, got {got:.2f} {'OK' if ok else 'MISMATCH'}")

    # II Patch vs GV CI crosses zero
    row = boot_df[(boot_df["comparison"] == "Patch vs Global-Vector") &
                  (boot_df["trajectory"] == "II")]
    lo, hi = row["ci_lo"].values[0], row["ci_hi"].values[0]
    crosses = lo < 0 < hi
    checks.append(f"II Patch-GV CI: [{lo:.2f}, {hi:.2f}] crosses zero: {crosses}")

    # PatchHuber-Huber translation benefits
    for traj, expected in [("VI", 45.38), ("IV", 31.81), ("II", 7.87), ("III", 19.66)]:
        row = boot_df[(boot_df["comparison"] == "Patch+Huber vs Huber") &
                      (boot_df["trajectory"] == traj)]
        got = row["median"].values[0]
        ok = abs(got - expected) < 0.3
        checks.append(f"PH-H benefit {traj}: expected ~{expected}, got {got:.2f} {'OK' if ok else 'MISMATCH'}")

    # Rotation cost medians
    for traj, expected in [("VI", 0.421), ("IV", 0.052), ("II", 0.498), ("III", 0.720)]:
        row = rot_df[rot_df["trajectory"] == traj]
        got = row["median"].values[0]
        ok = abs(got - expected) < 0.01
        checks.append(f"Rot cost {traj}: expected ~{expected}, got {got:.3f} {'OK' if ok else 'MISMATCH'}")

    check_text = "\n".join(checks)
    print("\n=== ANCHOR CHECKS ===")
    print(check_text)

    with open(_pp("figure_redesign_v2/checks/figure5_anchor_checks.txt"), "w") as f:
        f.write(check_text + "\n")


if __name__ == "__main__":
    main()
