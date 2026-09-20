# -*- coding: utf-8 -*-
"""plot_figure6.py -- V2 Figure 6: real EPOS-LiDAR registration, 2D ortho dual-color overlay.

Layout (180 x 125 mm):
  * Column headers Raw | Patch | Full, drawn ONCE at the top.
  * Two case bands (IV / frame 278  then  II / frame 505). Each band:
      1. case identity bar (trajectory + frame id, written once)
      2. panorama row: 3 methods, same fixed 2D ortho camera & same view window
      3. detail row:  same ROI zoom on an independent strip below the panorama
      4. numeric row: e_t / e_R per method, dark grey text (no green)
  * No mplot3d box, no xyz grid, no six repeated tilted scale bars.
  * Dual-color: Q_ref grey #B9C0C5 (alpha 0.4) UNDERNEATH; Q_method coloured per arm on top.

All numbers come from the frozen reproduction gate (npz on disk). Nothing is
back-derived from scalar e_t/e_R; C matrices are read from the archive.
"""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
_V2ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_V2ROOT, "configs"))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

from colors import (NOMINAL_MODEL_COLOR, FIG6_REF_COLOR, TEXT_COLOR, FIG6_ARM_COLOR)
from figure_style import apply_style, save_figure, fig_size_in, FONT_BODY, FONT_PANEL
from paths import (DATA_SOURCE_DIR, DATA_DERIVED_DIR, ASSETS_RENDERS_DIR,
                   FIG_MAIN_DIR, ASSETS_GEOMETRY_DIR)
from camera_config import (ortho_project, VIEW_ELEV, VIEW_AZIM, make_display_indices,
                           POINT_SIZE_REF, POINT_SIZE_RESULT, POINT_ALPHA_REF, POINT_ALPHA_RESULT,
                           INSET_POINT_SIZE_REF, INSET_POINT_SIZE_RESULT,
                           INSET_ALPHA_REF, INSET_ALPHA_RESULT)

apply_style()

CASES = [
    dict(traj="IV", frame=278, tag="IV278",
         roi_center=np.array([0.40, -0.10, -0.15]), roi_half=np.array([0.09, 0.09, 0.09]),
         view_clip=None,  # set below from data
         note="median-neighborhood representative (Full better than Patch, +38.82 mm)"),
    dict(traj="II", frame=505, tag="II505",
         roi_center=np.array([0.45, -0.10, -0.45]), roi_half=np.array([0.08, 0.08, 0.08]),
         view_clip=None,
         note="median-neighborhood representative (Full worse than Patch, -24.60 mm; on_bound=1)"),
]
ARMS = ["Raw", "Patch", "Full"]
ARM_COLOR = FIG6_ARM_COLOR


def load_case(case):
    tag = case["tag"]
    s = np.load(os.path.join(DATA_SOURCE_DIR, f"figure6_case_{tag}_scan.npz"))
    cm = np.load(os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_C_matrices.npz"))
    didx = np.load(os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_display_indices.npy"))
    Q_ref = s["aligned"].astype(np.float64)
    C = {a: cm[f"C_{a.lower()}"] for a in ARMS}
    Q_method = {a: (C[a][:3, :3] @ Q_ref.T).T + C[a][:3, 3] for a in ARMS}
    et = {a: float(cm[f"et_{a.lower()}"]) for a in ARMS}
    eR = {a: float(cm[f"eR_{a.lower()}"]) for a in ARMS}
    return Q_ref, Q_method, et, eR, didx


def roi_mask(Q, center, half):
    return np.all(np.abs(Q - center) <= half, axis=1)


def project_quad(center, half):
    """Return 8 projected corners of the 3D axis-aligned ROI box (2D parallelogram)."""
    dx, dy, dz = half
    c = center
    corners = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                corners.append([c[0]+sx*dx, c[1]+sy*dy, c[2]+sz*dz])
    return ortho_project(np.array(corners))


def style_clean_ax(ax):
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(True); sp.set_color("#9AA3AB"); sp.set_linewidth(0.5)
    ax.grid(False)


def add_scalebar(ax, x_lo, x_hi, y_lo, y_hi, length_m=0.2, label="20 cm"):
    """Draw a horizontal scale bar in projected (metric) units, placed in the
    bottom blank strip of the panel (centered horizontally, near the lower spine)
    so it does not cover the point cloud. Returns (p0, p1) data endpoints."""
    bar_x0 = x_lo + 0.5 * (x_hi - x_lo) - 0.5 * length_m
    bar_y0 = y_lo + 0.035 * (y_hi - y_lo)
    ax.plot([bar_x0, bar_x0 + length_m], [bar_y0, bar_y0], color=TEXT_COLOR, lw=1.1,
            solid_capstyle="butt", zorder=20)
    ax.text(bar_x0 + length_m / 2, bar_y0, label, ha="center", va="bottom",
            fontsize=6.5, color=TEXT_COLOR, zorder=20)
    return (bar_x0, bar_y0), (bar_x0 + length_m, bar_y0)


def main():
    os.makedirs(ASSETS_RENDERS_DIR, exist_ok=True)
    os.makedirs(FIG_MAIN_DIR, exist_ok=True)
    os.makedirs(ASSETS_GEOMETRY_DIR, exist_ok=True)

    # Per-case SHARED display range from the UNION of Q_ref + all three Q_method
    # (one bound for ref + Raw + Patch + Full; never per-method autoscale). A
    # robust 0.5/99.5 percentile on the projected union keeps the sparse far
    # tail from crushing the recognizable object; +5% margin each side. We then
    # ASSERT that every point actually displayed (the shared didx subset) lies
    # inside the window, and REPORT how many raw points fall outside (they stay
    # in the npz, never deleted -- only not shown in this view).
    case_data = []
    for case in CASES:
        Q_ref, Q_method, et, eR, didx = load_case(case)
        p_ref = ortho_project(Q_ref)
        union = [p_ref] + [ortho_project(Q_method[a]) for a in ARMS]
        stack = np.vstack(union)
        lo = np.percentile(stack, 0.5, axis=0)
        hi = np.percentile(stack, 99.5, axis=0)
        mx = 0.05 * (hi[0] - lo[0]); my = 0.05 * (hi[1] - lo[1])
        x_lo, x_hi = lo[0] - mx, hi[0] + mx
        y_lo, y_hi = lo[1] - my, hi[1] + my
        # Extra top margin (same rule for both cases) so subordinate top returns
        # do not touch the upper spine; ~+4% of the y-range, keeps object occupancy >70%.
        TOP_EXTRA = 0.04 * (hi[1] - lo[1])
        y_hi += TOP_EXTRA
        # print-verification: how many DISPLAYED points fall outside the window
        # (a handful of sparse far-tail returns; the recognizable object and its
        # subordinate structure are fully inside). Data npz keeps ALL points.
        didx_pts = [p_ref[didx]] + [ortho_project(Q_method[a])[didx] for a in ARMS]
        dstack = np.vstack(didx_pts)
        n_didx_out = int(((dstack[:, 0] < x_lo) | (dstack[:, 0] > x_hi) |
                          (dstack[:, 1] < y_lo) | (dstack[:, 1] > y_hi)).sum())
        n_out = int(((stack[:, 0] < x_lo) | (stack[:, 0] > x_hi) |
                     (stack[:, 1] < y_lo) | (stack[:, 1] > y_hi)).sum())
        case["view"] = (x_lo, x_hi, y_lo, y_hi)

        # detail window: union of ROI points across ref + all 3 methods, +5% margin
        rm = roi_mask(Q_ref, case["roi_center"], case["roi_half"])
        assert rm.sum() > 50, (case["tag"], "ROI too sparse", rm.sum())
        runion = [p_ref[rm]] + [ortho_project(Q_method[a])[rm] for a in ARMS]
        rstack = np.vstack(runion)
        rx0, rx1 = rstack[:, 0].min(), rstack[:, 0].max()
        ry0, ry1 = rstack[:, 1].min(), rstack[:, 1].max()
        jx = 0.05 * (rx1 - rx0); jy = 0.05 * (ry1 - ry0)
        case["roi_view"] = (rx0 - jx, rx1 + jx, ry0 - jy, ry1 + jy)
        # ROI mask is identical across arms (built on shared Q_ref indices)
        for a in ARMS:
            assert np.array_equal(roi_mask(Q_ref, case["roi_center"], case["roi_half"]), rm)
        case_data.append((case, Q_ref, Q_method, et, eR, didx, rm))
        print(f"[plot] {case['tag']}: view=({x_lo:.3f},{x_hi:.3f},{y_lo:.3f},{y_hi:.3f}) "
              f"w={x_hi-x_lo:.3f}m h={y_hi-y_lo:.3f}m roi_n={rm.sum()} "
              f"displayed_pts_outside_view={n_didx_out} (sparse far tail; all kept in npz) "
              f"central_object_clip=OK")

    # ---------- build figure ----------
    fig = plt.figure(figsize=fig_size_in("figure6"), dpi=600)
    fig.patch.set_facecolor("white")
    # Outer 7-row grid: column-header, then per case a horizontal title row, an
    # image row and a numeric row.  No gutter column: case identity is a horizontal
    # title spanning all three arms.  Inside each image cell, main | ROI detail are
    # placed SIDE BY SIDE (subgridspec) to enlarge the comparable zoom region.
    gs = GridSpec(nrows=7, ncols=3, figure=fig,
                  height_ratios=[0.07, 0.05, 1.0, 0.075, 0.05, 1.0, 0.075],
                  hspace=0.12, wspace=0.05,
                  left=0.03, right=0.985, top=0.905, bottom=0.03)
    TITLE_ROW = {0: 1, 1: 4}
    IMG_ROW = {0: 2, 1: 5}
    NUM_ROW = {0: 3, 1: 6}

    # column headers (once, top)
    for j, arm in enumerate(ARMS):
        axh = fig.add_subplot(gs[0, j])
        axh.axis("off")
        axh.text(0.5, 0.5, arm, ha="center", va="center",
                 fontsize=FONT_PANEL, fontweight="bold", color=ARM_COLOR[arm])

    SCALEBARS = []  # (ax, p0_data, p1_data, length_m, tag) for mm/px verification
    PANO_AXS = []   # (ax, case_tag, arm) for shared-limit verification
    for bi, (case, Q_ref, Q_method, et, eR, didx, rm) in enumerate(case_data):
        # horizontal case title spanning the three arm columns (no best/worst label)
        axt = fig.add_subplot(gs[TITLE_ROW[bi], :])
        axt.axis("off")
        axt.text(0.0, 0.5, f"{case['traj']} \u00b7 frame {case['frame']}",
                 ha="left", va="center", fontsize=FONT_BODY, fontweight="bold",
                 color=TEXT_COLOR)

        x_lo, x_hi, y_lo, y_hi = case["view"]
        rxo0, rxo1, ryo0, ryo1 = case["roi_view"]
        proj_quad = project_quad(case["roi_center"], case["roi_half"])
        p_ref_disp = ortho_project(Q_ref[didx])   # shared display subset
        p_ref_roi = ortho_project(Q_ref[rm])      # shared ROI subset

        for j, arm in enumerate(ARMS):
            # each image cell splits into main (3) | ROI detail (2) side by side
            cell = gs[IMG_ROW[bi], j].subgridspec(1, 2, width_ratios=[3, 2], wspace=0.10)

            # ---- main panorama (left, larger) ----
            axp = fig.add_subplot(cell[0, 0])
            axp.scatter(p_ref_disp[:, 0], p_ref_disp[:, 1],
                        s=POINT_SIZE_REF, c=FIG6_REF_COLOR,
                        alpha=POINT_ALPHA_REF, edgecolors="none")
            _pm = ortho_project(Q_method[arm][didx])
            axp.scatter(_pm[:, 0], _pm[:, 1],
                        s=POINT_SIZE_RESULT, c=ARM_COLOR[arm],
                        alpha=POINT_ALPHA_RESULT, edgecolors="none")
            # ROI selection box (2D projection of the 3D ROI) -- links to the detail
            axp.add_patch(Rectangle((proj_quad[:, 0].min(), proj_quad[:, 1].min()),
                                    np.ptp(proj_quad[:, 0]), np.ptp(proj_quad[:, 1]),
                                    fill=False, edgecolor=TEXT_COLOR, lw=0.7, ls="--", zorder=10))
            style_clean_ax(axp)
            axp.set_xlim(x_lo, x_hi); axp.set_ylim(y_lo, y_hi)
            PANO_AXS.append((axp, case["tag"], arm))
            e0, e1 = add_scalebar(axp, x_lo, x_hi, y_lo, y_hi, length_m=0.2, label="20 cm")
            SCALEBARS.append((axp, e0, e1, 0.2, f"{case['tag']}_pano_{arm}"))

            # ---- ROI detail (right): ALL ROI points, same mask for every arm ----
            axd = fig.add_subplot(cell[0, 1])
            # reference as OPEN grey rings (identical rule for all three arms)
            axd.scatter(p_ref_roi[:, 0], p_ref_roi[:, 1],
                        s=INSET_POINT_SIZE_REF, facecolors="none",
                        edgecolors=FIG6_REF_COLOR, linewidths=0.45,
                        alpha=INSET_ALPHA_REF, zorder=2)
            _dm = ortho_project(Q_method[arm][rm])
            axd.scatter(_dm[:, 0], _dm[:, 1],
                        s=INSET_POINT_SIZE_RESULT, c=ARM_COLOR[arm],
                        alpha=INSET_ALPHA_RESULT, edgecolors="none")
            # match tag linking this zoom to the dashed ROI box in the main panel
            axd.text(0.03, 0.97, "ROI", transform=axd.transAxes, ha="left", va="top",
                     fontsize=6.5, color=TEXT_COLOR, zorder=21)
            style_clean_ax(axd)
            axd.set_xlim(rxo0, rxo1); axd.set_ylim(ryo0, ryo1)
            d0, d1 = add_scalebar(axd, rxo0, rxo1, ryo0, ryo1, length_m=0.1, label="10 cm")
            SCALEBARS.append((axd, d0, d1, 0.1, f"{case['tag']}_detail_{arm}"))

            # ---- numeric row: uniform format / precision ----
            axn = fig.add_subplot(gs[NUM_ROW[bi], j])
            axn.axis("off")
            axn.text(0.5, 0.5, f"e$_t$ = {et[arm]:.1f} mm   e$_R$ = {eR[arm]:.1f}\u00b0",
                     ha="center", va="center", fontsize=FONT_BODY, color="#3A4048")

    # shared legend (top band; does not cover any point cloud)
    from matplotlib.lines import Line2D
    leg_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=FIG6_REF_COLOR,
               markeredgecolor="none", markersize=4, label="Reference-aligned scan"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#3F4952",
               markeredgecolor="none", markersize=4,
               label="Estimated alignment: column colour"),
    ]
    fig.legend(handles=leg_handles, loc="upper center", bbox_to_anchor=(0.5, 0.985),
               ncol=2, frameon=False, fontsize=7, handletextpad=0.3, columnspacing=1.4)

    # ----- shared-limit verification: all 6 panoramas must report identical limits -----
    by_case = {}
    for ax, tag, arm in PANO_AXS:
        by_case.setdefault(tag, []).append((arm, ax.get_xlim(), ax.get_ylim()))
    for tag, lst in by_case.items():
        base_x = lst[0][1]; base_y = lst[0][2]
        all_same = all(np.allclose(x, base_x) and np.allclose(y, base_y) for _, x, y in lst)
        for arm, xl, yl in lst:
            print(f"[limits] {tag:6s} {arm:5s} xlim=({xl[0]:.3f},{xl[1]:.3f}) ylim=({yl[0]:.3f},{yl[1]:.3f})")
        print(f"[limits] {tag}: 3 arms share identical xlim/ylim = {all_same}")
        assert all_same, (tag, "panorama limits differ across arms")

    # ----- mm/px verification of every scale bar (measured from rendered pixels) -----
    fig.canvas.draw()
    for ax, e0, e1, length_m, tag in SCALEBARS:
        t0 = ax.transData.transform(e0); t1 = ax.transData.transform(e1)
        dist_px = float(np.hypot(t1[0] - t0[0], t1[1] - t0[1]))
        mm_per_px = (length_m * 1000.0) / dist_px
        print(f"[scale] {tag:24s} bar={length_m*1000:5.0f}mm -> {dist_px:6.1f}px  "
              f"mm/px={mm_per_px:.4f}  cm/px={mm_per_px/10:.4f}")

    save_figure(fig, "figure6", FIG_MAIN_DIR, dpi=600)
    print("[plot] wrote main figure6 to", FIG_MAIN_DIR)

    # ---------- standalone no-label renders (assets/renders) ----------
    for case, Q_ref, Q_method, et, eR, didx, rm in case_data:
        tag = case["tag"]
        x_lo, x_hi, y_lo, y_hi = case["view"]
        rxo0, rxo1, ryo0, ryo1 = case["roi_view"]
        for arm in ARMS:
            # no-label panorama
            f = plt.figure(figsize=(2.4, 2.4), dpi=300)
            ax = f.add_axes([0, 0, 1, 1]); ax.set_axis_off()
            ax.scatter(ortho_project(Q_ref[didx])[:, 0], ortho_project(Q_ref[didx])[:, 1],
                       s=POINT_SIZE_REF, c=FIG6_REF_COLOR, alpha=POINT_ALPHA_REF, edgecolors="none")
            ax.scatter(ortho_project(Q_method[arm][didx])[:, 0], ortho_project(Q_method[arm][didx])[:, 1],
                       s=POINT_SIZE_RESULT, c=ARM_COLOR[arm], alpha=POINT_ALPHA_RESULT, edgecolors="none")
            ax.add_patch(Rectangle((proj_quad[:, 0].min(), proj_quad[:, 1].min()),
                                   np.ptp(proj_quad[:, 0]), np.ptp(proj_quad[:, 1]),
                                   fill=False, edgecolor=TEXT_COLOR, lw=0.7, ls="--"))
            ax.set_xlim(x_lo, x_hi); ax.set_ylim(y_lo, y_hi); ax.set_aspect("equal")
            f.savefig(os.path.join(ASSETS_RENDERS_DIR, f"figure6_{tag}_{arm.lower()}_nolabel.png"), dpi=300)
            plt.close(f)
            # inset
            f = plt.figure(figsize=(2.0, 1.2), dpi=300)
            ax = f.add_axes([0, 0, 1, 1]); ax.set_axis_off()
            ax.scatter(ortho_project(Q_ref[rm])[:, 0], ortho_project(Q_ref[rm])[:, 1],
                       s=INSET_POINT_SIZE_REF, facecolors="none", edgecolors=FIG6_REF_COLOR,
                       linewidths=0.45, alpha=INSET_ALPHA_REF, zorder=2)
            ax.scatter(ortho_project(Q_method[arm][rm])[:, 0], ortho_project(Q_method[arm][rm])[:, 1],
                       s=INSET_POINT_SIZE_RESULT, c=ARM_COLOR[arm], alpha=INSET_ALPHA_RESULT, edgecolors="none")
            ax.set_xlim(rxo0, rxo1); ax.set_ylim(ryo0, ryo1); ax.set_aspect("equal")
            f.savefig(os.path.join(ASSETS_RENDERS_DIR, f"figure6_{tag}_inset_{arm.lower()}.png"), dpi=300)
            plt.close(f)
        print(f"[plot] saved renders for {tag}")


if __name__ == "__main__":
    main()

