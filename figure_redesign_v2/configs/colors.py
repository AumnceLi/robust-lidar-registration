"""V2 figure redesign — method colours, markers, trajectory colours."""

# Method colours (hex, from spec)
METHOD_COLORS = {
    "Raw": "#525B63",
    "Huber": "#386CB0",
    "Trim": "#5C879F",  # Ast 2026-09-14: deepened from light blue for legibility
    "Global-Vector": "#8A6FA8",
    "Patch": "#2C8C7E",
    "Full": "#C97A40",
    "PatchHuber": "#D4A040",  # derived warm gold for Patch+Huber
}

# Markers per method
METHOD_MARKERS = {
    "Raw": "o",
    "Huber": "s",
    "Trim": "^",
    "Global-Vector": "^",
    "Patch": "D",
    "Full": "v",
    "PatchHuber": "P",
}

# Linestyles per method
METHOD_LINESTYLES = {
    "Raw": "-",
    "Huber": "--",
    "Trim": "-",
    "Global-Vector": "-",
    "Patch": "-",
    "Full": "-",
    "PatchHuber": "-.",
}

# Raw hollow when overlapping with Huber
METHOD_FACECOLORS = {"Raw": "none", "Estimated Full": "none"}
METHOD_EDGECOLORS = {"Raw": "#525B63", "Estimated Full": "#C97A40"}

# Colormaps
CONTINUOUS_CMAP = "cividis"
HEATMAP_CMAP = "Blues"
DIVERGING_CMAP = "RdBu_r"

# Trajectory colours (V2 spec: VI blue, IV warm orange, II teal-green, III purple)
TRAJECTORY_COLORS = {
    "VI":  "#386CB0",
    "IV":  "#C97A40",
    "II":  "#2C8C7E",
    "III": "#8A6FA8",
}
TRAJECTORY_ORDER = ["VI", "IV", "II", "III"]

# Comparison markers for paired forest plot
COMPARISON_MARKERS = {
    "Patch vs Raw": "o",
    "Patch vs Global-Vector": "s",
    "Patch+Huber vs Huber": "^",
}

# Comparison colours (muted, distinct)
COMPARISON_COLORS = {
    "Patch vs Raw": "#2C8C7E",
    "Patch vs Global-Vector": "#8A6FA8",
    "Patch+Huber vs Huber": "#C97A40",
}

# ── Reference / nominal geometry / text (V2 spec) ─────────────────────────
NOMINAL_MODEL_COLOR = "#B9C0C5"   # light grey-blue for nominal geometry
REFERENCE_SCAN_COLOR = "#B9C0C5"
TEXT_COLOR = "#20262D"             # primary text colour


# ── Figure 6 dual-color overlay palette (no displacement heatmap) ─────────
NOMINAL_MODEL_COLOR = "#B9C0C5"   # nominal model M, light grey-blue, optional faint backdrop
FIG6_REF_COLOR      = "#8D979F"   # reference scan Q_ref, neutral mid-grey (Ast 2026-09-14)
FIG6_RESULT_COLOR    = "#386CB0"   # generic method-result blue (per-arm colours below)
FIG6_RAW_COLOR       = "#3F4952"   # Raw result, darker slate to separate from grey ref
FIG6_PATCH_COLOR     = "#2C8C7E"   # Patch result (teal)
FIG6_FULL_COLOR      = "#C97A40"   # Full result (orange)
TEXT_COLOR           = "#20262D"   # near-black body text / numeric labels

# Per-arm result colour lookup for Figure 6 columns
FIG6_ARM_COLOR = {"Raw": "#3F4952", "Patch": "#2C8C7E", "Full": "#C97A40"}


def method_props(method):
    """Return dict of plot props for a given method name."""
    kw = dict(
        color=METHOD_COLORS.get(method, "#333333"),
        marker=METHOD_MARKERS.get(method, "o"),
        linestyle=METHOD_LINESTYLES.get(method, "-"),
    )
    if method in METHOD_FACECOLORS:
        kw["markerfacecolor"] = METHOD_FACECOLORS[method]
    if method in METHOD_EDGECOLORS:
        kw["markeredgecolor"] = METHOD_EDGECOLORS[method]
    return kw
