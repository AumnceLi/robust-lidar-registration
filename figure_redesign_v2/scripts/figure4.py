"""
Figure 4 — Controlled mismatch experiment (V2 full redraw).

Layout: 180 x 100 mm, compact 2x2 grid.
  (a) D1 coherent displacement dose-response
  (b) D5 coherent tilt dose-response
  (c) Matched-RMS paired dot plot (4 Table 3 cases)
  (d) alpha-eta_t phase map (controlled samples)

All numerical values are derived from raw data at runtime.
Caption is NOT baked into the figure; it lives in manuscript/.
"""
import sys, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LogNorm, Normalize
from matplotlib.lines import Line2D

# ── Import V2 shared config ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.colors import METHOD_COLORS, METHOD_MARKERS, METHOD_LINESTYLES, CONTINUOUS_CMAP, method_props
from configs.figure_style import apply_style, panel_label, save_figure, fig_size_in
from configs.paths import SRC, DATA_DERIVED_DIR, FIG_MAIN_DIR, TABLE3_CASES

apply_style()

# ── Load data ────────────────────────────────────────────────────────────
dose = pd.read_csv(SRC["dose_response"])
phase = pd.read_csv(SRC["phase_samples"])

# Condition name → dtype code mapping
COND_DTYPE = {
    "D1": "D1_appendage_disp",
    "D2": "D2_missing_component",
    "D3": "D3_local_surface_off",
    "D4": "D4_appendage_scale",
    "D5": "D5_appendage_tilt",
}
DTYPE_LABEL = {
    "D1_appendage_disp": "D1",
    "D2_missing_component": "D2",
    "D3_local_surface_off": "D3",
    "D4_appendage_scale": "D4",
    "D5_appendage_tilt": "D5",
}

METHODS = ["Raw", "Huber", "Trim"]
FORM_MAP = {"Raw": "ls", "Huber": "huber", "Trim": "trim"}
GEOMS = ["GA", "GB", "GC"]

# ── Figure setup ────────────────────────────────────────────────────────
fig_w, fig_h = fig_size_in("figure4")  # 180 x 106 mm from the shared style table
fig = plt.figure(figsize=(fig_w, fig_h), dpi=150)

# 2x2 with a DEDICATED inter-row band: (b) x-label, then a clear gap (>=2 mm on
# both sides), then the D1–D5 shape-legend row, then the lower panels' titles.
gs = GridSpec(2, 2, figure=fig,
              left=0.07, right=0.92,
              top=0.815, bottom=0.09,
              wspace=0.30, hspace=0.72)

# ── Shared legend (top, outside panels) ──────────────────────────────────
legend_handles = []
for m in METHODS:
    props = method_props(m)
    h = Line2D([0], [0], color=props["color"], marker=props["marker"],
               linestyle=props["linestyle"], markersize=4,
               markerfacecolor=props.get("markerfacecolor", props["color"]),
               markeredgecolor=props.get("markeredgecolor", props["color"]),
               markeredgewidth=0.8, label=m)
    legend_handles.append(h)
fig.legend(handles=legend_handles, loc="upper center",
           bbox_to_anchor=(0.5, 0.96), ncol=3, frameon=False,
           fontsize=8, handlelength=1.5, columnspacing=1.2)


# ════════════════════════════════════════════════════════════════════════
# Panel (a): D1 coherent displacement
# ════════════════════════════════════════════════════════════════════════
ax_a = fig.add_subplot(gs[0, 0])
dtype_d1 = COND_DTYPE["D1"]

def crossgeo_summary(dtype_code, value_col):
    """For every method and dose, aggregate the three geometry condition
    medians: main line = their median, shaded band = their min–max.
    Returns doses, and {method: (main, lo, hi)} arrays."""
    doses_local = sorted(dose[dose.dtype == dtype_code]["mag"].unique())
    out = {}
    for m in METHODS:
        form = FORM_MAP[m]
        main, lo, hi = [], [], []
        for mag in doses_local:
            vals = []
            for g in GEOMS:
                row = dose[(dose.geometry == g) & (dose.dtype == dtype_code) &
                           (dose.mag == mag) & (dose.form == form)]
                if len(row) > 0:
                    vals.append(row[value_col].values[0])
            vals = np.array(vals, dtype=float)
            main.append(np.median(vals)); lo.append(vals.min()); hi.append(vals.max())
        out[m] = (np.array(main), np.array(lo), np.array(hi))
    return doses_local, out

def plot_summary(ax, doses_local, summ):
    # one shaded range band per method (min–max of the 3 geometry medians)
    for m in METHODS:
        props = method_props(m)
        _, lo, hi = summ[m]
        ax.fill_between(doses_local, lo, hi, color=props["color"],
                        alpha=0.12, linewidth=0, zorder=1)
    # one main cross-geometry median line per method (colour + linestyle + marker)
    for m in METHODS:
        props = method_props(m)
        main, _, _ = summ[m]
        ax.plot(doses_local, main, color=props["color"], linestyle=props["linestyle"],
                marker=props["marker"], markersize=3.8, linewidth=1.4, zorder=3,
                markerfacecolor=props.get("markerfacecolor", props["color"]),
                markeredgecolor=props.get("markeredgecolor", props["color"]),
                markeredgewidth=0.8)

doses_mag, summ_a = crossgeo_summary(dtype_d1, "et_med")
plot_summary(ax_a, doses_mag, summ_a)

# Legal symlog: zero dose is a real baseline tick; linear region is half the
# smallest non-zero dose (no epsilon substitution).
nz_doses = [d for d in doses_mag if d > 0]
linthresh_x_a = min(nz_doses) / 2.0
ax_a.set_xlabel("Appendage displacement (mm)")
ax_a.set_ylabel("Translation error (mm)")
ax_a.set_title("D1: coherent displacement", fontsize=9, pad=4)
ax_a.set_xscale("symlog", linthresh=linthresh_x_a)
ax_a.set_yscale("symlog", linthresh=0.01)
panel_label(ax_a, "(a)")


# ════════════════════════════════════════════════════════════════════════
# Panel (b): D5 coherent tilt
# ════════════════════════════════════════════════════════════════════════
ax_b = fig.add_subplot(gs[0, 1])
dtype_d5 = COND_DTYPE["D5"]

doses_d5, summ_b = crossgeo_summary(dtype_d5, "eR_med")
plot_summary(ax_b, doses_d5, summ_b)

# Legal symlog (same zero-dose convention as panel a); y linthresh from real data
nz_doses_b = [d for d in doses_d5 if d > 0]
linthresh_x_b = min(nz_doses_b) / 2.0
nz_err_b = [v for v in summ_b["Raw"][0] if v > 0]
linthresh_y_b = min(nz_err_b) / 2.0

ax_b.set_xlabel("Appendage tilt (deg)")
ax_b.set_ylabel("Rotation error (deg)")
ax_b.set_title("D5: coherent tilt", fontsize=9, pad=4)
ax_b.set_xscale("symlog", linthresh=linthresh_x_b)
ax_b.set_yscale("symlog", linthresh=linthresh_y_b)
panel_label(ax_b, "(b)")


# ════════════════════════════════════════════════════════════════════════
# Panel (c): Matched RMS paired dots
# ════════════════════════════════════════════════════════════════════════
ax_c = fig.add_subplot(gs[1, 0])

# Short y labels for 4 cases
Y_LABELS = [
    "GA · D1/D3",
    "GB · D4/D3",
    "GB · D4/D5",
    "GC · D3/D4",
]
y_pos = np.arange(len(TABLE3_CASES))[::-1]  # top to bottom

# Condition A color (filled), Condition B color (open)
COL_A = "#386CB0"
COL_B = "#C97A40"

for i, case in enumerate(TABLE3_CASES):
    y = y_pos[i]
    et_a = case["et_A"]
    et_b = case["et_B"]
    ratio = case["ratio"]

    # Gray connecting line
    ax_c.plot([et_a, et_b], [y, y], color="#AAAAAA", linewidth=0.8, zorder=1)

    # Condition A: filled circle
    ax_c.scatter(et_a, y, s=35, color=COL_A, zorder=3, edgecolors="none", marker="o")
    # Condition B: open circle
    ax_c.scatter(et_b, y, s=35, facecolors="white", edgecolors=COL_B,
                 linewidths=1.2, zorder=3, marker="o")

    # Ratio label on right
    ax_c.text(max(et_a, et_b) * 1.15, y, f"×{ratio:.1f}",
              va="center", ha="left", fontsize=7.5, color="#20262D")

ax_c.set_yticks(y_pos)
ax_c.set_yticklabels(Y_LABELS, fontsize=7.5)
ax_c.set_xlabel("Translation error (mm)")
ax_c.set_title("Matched residual RMS", fontsize=9, pad=4)
ax_c.set_xscale("log")
ax_c.set_xlim(0.03, 25)
ax_c.invert_yaxis() if False else None  # keep top-to-bottom as y_pos already reversed
panel_label(ax_c, "(c)")

# Condition A/B legend (small, top-right of panel)
leg_c = [
    Line2D([0], [0], marker="o", color="none", markerfacecolor=COL_A,
           markeredgecolor=COL_A, markersize=5, label="Condition A"),
    Line2D([0], [0], marker="o", color="none", markerfacecolor="white",
           markeredgecolor=COL_B, markeredgewidth=1.2, markersize=5, label="Condition B"),
]
ax_c.legend(handles=leg_c, loc="lower right", fontsize=7, frameon=False)


# ════════════════════════════════════════════════════════════════════════
# Panel (d): alpha–eta_t phase map
# ════════════════════════════════════════════════════════════════════════
ax_d = fig.add_subplot(gs[1, 1])

# Marker shapes for D1–D5
D_MARKERS = {
    "D1_appendage_disp": "o",
    "D2_missing_component": "s",
    "D3_local_surface_off": "^",
    "D4_appendage_scale": "D",
    "D5_appendage_tilt": "v",
}

# Color by Raw LS translation error (log scale). All controlled samples are
# strictly positive (verified at runtime); if a true zero appears it must be
# marked with a distinct neutral symbol rather than mapped to min/2.
et_vals = phase["ete_med"].values
assert np.all(et_vals > 0), "unexpected zero Raw e_t in phase samples"
et_safe = et_vals
norm = LogNorm(vmin=np.nanmin(et_safe), vmax=np.nanmax(et_safe))
cmap = plt.get_cmap(CONTINUOUS_CMAP)

for dtype_code, marker in D_MARKERS.items():
    sub = phase[phase.dtype == dtype_code]
    if len(sub) == 0:
        continue
    colors = [cmap(norm(e)) for e in sub["ete_med"].values]
    ax_d.scatter(sub["alpha"], sub["eta_t"], c=colors, marker=marker,
                 s=22, edgecolors="#20262D", linewidths=0.4, zorder=3)

ax_d.set_xlabel(r"$\alpha$ (mismatch fraction)")
ax_d.set_ylabel(r"Translation coherence $\eta_t$")
ax_d.set_title("Controlled mismatch patterns", fontsize=9, pad=4)
ax_d.set_xlim(-0.02, 0.42)
ax_d.set_ylim(-0.02, 1.02)
panel_label(ax_d, "(d)")

# D1-D5 shape legend (above panel, outside data area)
shape_leg = []
for dc, mk in D_MARKERS.items():
    label = DTYPE_LABEL[dc]
    shape_leg.append(Line2D([0], [0], marker=mk, color="#525B63",
                           markerfacecolor="none", markeredgecolor="#525B63",
                           linestyle="None", markersize=5, label=label))
# Dedicated D1–D5 legend row, placed in figure-fraction coordinates in the LOWER
# part of the widened inter-row band so it has >=2 mm clearance from the (b)
# x-label above and the panel-(d) title below (0.735 = centre of the right col).
fig.legend(handles=shape_leg, loc="center", ncol=5, fontsize=7.5,
           bbox_to_anchor=(0.735, 0.432), bbox_transform=fig.transFigure,
           handletextpad=0.35, columnspacing=1.1, borderpad=0.3, frameon=False)

# Colorbar on right side
cax = fig.add_axes([0.948, 0.14, 0.011, 0.30])  # narrow strip, right side
sm = ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])
cbar = fig.colorbar(sm, cax=cax, orientation="vertical")
cbar.set_label(r"Raw LS $e_t$ (mm)", fontsize=7, labelpad=3)
cbar.ax.tick_params(labelsize=6.5, width=0.4, length=2)
cbar.outline.set_linewidth(0.5)

# ── Save ────────────────────────────────────────────────────────────────
os.makedirs(FIG_MAIN_DIR, exist_ok=True)
save_figure(fig, "figure4", [FIG_MAIN_DIR])
print("Figure 4 saved to:", FIG_MAIN_DIR)

# ── Also save derived data for transparency ─────────────────────────────
os.makedirs(DATA_DERIVED_DIR, exist_ok=True)

# Save Table 3 verification summary
verify_rows = []
for i, case in enumerate(TABLE3_CASES):
    verify_rows.append({
        "case": i + 1,
        "y_label": Y_LABELS[i],
        "geometry": case["geometry"],
        "family_A": case["family_A"],
        "rms_A": case["rms_A"],
        "et_A": case["et_A"],
        "family_B": case["family_B"],
        "rms_B": case["rms_B"],
        "et_B": case["et_B"],
        "ratio_published": case["ratio"],
    })
pd.DataFrame(verify_rows).to_csv(
    os.path.join(DATA_DERIVED_DIR, "figure4_matched_rms_cases.csv"), index=False)

# Save phase map data
phase_export = phase[["geometry", "dtype", "dose", "alpha", "eta_t",
                       "eta_R", "ete_med", "eR_med"]].copy()
phase_export.to_csv(os.path.join(DATA_DERIVED_DIR, "figure4_phase_map.csv"),
                     index=False)

print("Derived data saved to:", DATA_DERIVED_DIR)
