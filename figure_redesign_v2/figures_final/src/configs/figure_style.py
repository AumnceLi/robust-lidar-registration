"""V2 figure redesign — matplotlib style helpers."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# ── Font sizes (actual source pt at 180 mm working width; Ast 2026-09-14) ──
FONT_AXIS    = 9.0    # axis titles
FONT_BODY    = 8.0    # legend, direct labels
FONT_TITLE   = 9.0    # short panel titles (9–9.5)
FONT_PANEL   = 10.0   # (a)(b) labels, bold, outside axes
FONT_TICK    = 8.0    # tick labels (minimum >= 7.5pt)
FONT_SECOND  = 7.5    # secondary notes (never below ~7.5pt)
FONT_CAPTION = 8.0
FONT_FORMULA = 9.5    # equations: italic variables, upright units/names

# ── Per-figure dimensions (mm, width x height), 180 mm two-column working ──
FIG_SIZES_MM = {
    "figure1": (180, 116),
    "figure2": (180, 108),
    "figure3": (180, 110),
    "figure4": (180, 106),
    "figure5": (180, 114),
    "figure6": (180, 118),
}
FIG_SIZES_MM["figureS1"] = (180, 80)
FIG_SIZES_MM["figureS2"] = (180, 160)
FIG_SIZES_MM["figureS3"] = (180, 100)

MM_PER_INCH = 25.4


def apply_style():
    """Apply publication-quality matplotlib style."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "mathtext.fontset": "dejavusans",
        "font.size": FONT_BODY,
        "axes.titlesize": FONT_TITLE,
        "axes.labelsize": FONT_AXIS,
        "axes.titleweight": "normal",
        "axes.labelweight": "normal",
        "xtick.labelsize": FONT_TICK,
        "ytick.labelsize": FONT_TICK,
        "legend.fontsize": FONT_BODY,
        "legend.frameon": False,
        "legend.numpoints": 1,
        "legend.scatterpoints": 1,
        "legend.handlelength": 1.2,
        "legend.handletextpad": 0.35,
        "axes.linewidth": 0.7,
        "axes.edgecolor": "#525C64",
        "axes.labelcolor": "#222A30",
        "text.color": "#222A30",
        "xtick.color": "#525C64",
        "ytick.color": "#525C64",
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "xtick.minor.visible": False,
        "ytick.minor.visible": False,
        # Only left/bottom spines
        "axes.spines.top": False,
        "axes.spines.right": False,
        # Light y-grid only (heatmaps turn the major grid OFF explicitly)
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": "#E5E7EB",
        "grid.linewidth": 0.35,
        "grid.linestyle": "-",
        "lines.linewidth": 1.3,
        "lines.markersize": 3.5,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "figure.dpi": 150,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def panel_label(ax, label, dx=0.0, dy=1.015, va="bottom"):
    """Place (a), (b) label OUTSIDE the axes (default: just above the top-left
    corner) so it can never occlude data points or error bars. Callers that need
    a custom clear position may pass dx/dy/va explicitly."""
    ax.text(dx, dy, label, transform=ax.transAxes,
            fontsize=FONT_PANEL, fontweight="bold", color="#222A30",
            va=va, ha="left", clip_on=False)


def fig_size_in(name_or_w, h=None):
    """Convert mm to inches.
    Two modes:
      fig_size_in("figure1")  — look up in FIG_SIZES_MM
      fig_size_in(180, 95)    — explicit mm
    """
    if h is None:
        w_mm, h_mm = FIG_SIZES_MM.get(name_or_w, (180, 100))
    else:
        w_mm, h_mm = name_or_w, h
    return (w_mm / MM_PER_INCH, h_mm / MM_PER_INCH)


def save_figure(fig, basename, out_dir, dpi=600):
    """Save figure as PDF + SVG + PNG(600dpi).
    out_dir: single directory path (or list of directories).
    """
    if isinstance(out_dir, str):
        out_dirs = [out_dir]
    else:
        out_dirs = out_dir

    paths = {}
    for d in out_dirs:
        os.makedirs(d, exist_ok=True)
        for ext in ["pdf", "svg", "png"]:
            path = os.path.join(d, f"{basename}.{ext}")
            kwargs = dict(bbox_inches="tight", pad_inches=0.02)
            if ext == "png":
                kwargs["dpi"] = dpi
            fig.savefig(path, format=ext, **kwargs)
            paths[ext] = path
    return paths
