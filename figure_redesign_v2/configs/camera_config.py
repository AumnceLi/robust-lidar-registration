"""
V2 camera / ROI / display-subsample config for Figure 6.
Uses FIXED 2D orthographic projection matrix (not mplot3d default box).
"""
import numpy as np

# ── 2D orthographic projection ────────────────────────────────────────────
# Fixed view angles (elevation / azimuth in degrees) chosen to show the
# target's recognizable shape. Locked for ALL six panorama panels.
VIEW_ELEV = 25.0
VIEW_AZIM = -60.0

def ortho_project(xyz, elev=VIEW_ELEV, azim=VIEW_AZIM):
    """
    Project 3D points to 2D using fixed orthographic rotation.
    xyz: (N,3) array in TARGET frame (metres)
    Returns: (N,2) array of (x_2d, y_2d) in scene units.
    """
    el = np.radians(elev)
    az = np.radians(azim)
    # Rotation: azimuth around Z, then elevation around X
    Rz = np.array([[np.cos(az), -np.sin(az), 0],
                    [np.sin(az),  np.cos(az), 0],
                    [0, 0, 1]])
    Rx = np.array([[1, 0, 0],
                    [0, np.cos(el), -np.sin(el)],
                    [0, np.sin(el),  np.cos(el)]])
    R = Rx @ Rz
    rotated = xyz @ R.T
    # Orthographic: drop Z (depth), keep X,Y
    return rotated[:, :2]

def compute_scale_bars(xyz_2d, target_length_m=0.2):
    """Compute scale bar length in 2D scene units for a given real length."""
    # In orthographic projection, a known real length maps linearly.
    # We compute the 2D extent of a 0.2m segment along the horizontal axis.
    return target_length_m  # orthographic preserves scale in the projection plane

# ── ROI / zoom box ─────────────────────────────────────────────────────────
# Fixed ROI in TARGET-frame 3D coordinates. Same for all panels and both cases.
ROI_CENTER = np.array([0.25, 0.0, 0.12])
ROI_HALF_EXTENT = np.array([0.06, 0.06, 0.06])

def points_in_roi(xyz, center=ROI_CENTER, half=ROI_HALF_EXTENT):
    """Return mask of points inside the ROI box."""
    return np.all(np.abs(xyz - center) <= half, axis=1)

# ── Display subsampling ────────────────────────────────────────────────────
DISPLAY_N_POINTS = 5000
DISPLAY_SEED = 12345

def make_display_indices(n_total, n_display=DISPLAY_N_POINTS, seed=DISPLAY_SEED):
    rng = np.random.default_rng(seed)
    if n_total <= n_display:
        return np.arange(n_total)
    return rng.choice(n_total, size=n_display, replace=False)

# ── Point rendering sizes ──────────────────────────────────────────────────
# Ast review (2026-09-14) starting point. matplotlib scatter s is points^2
# (area), diameter(pt) = sqrt(s). Readability is carried mainly by the ENLARGED
# side-by-side ROI, not by ever-larger dots, so main-panel dots stay ~0.30-0.36 pt
# and ROI dots ~0.49-0.53 pt; identical rule for reference and every method.
POINT_SIZE_REF = 0.13    # reference scan (grey), ~0.36 pt diameter
POINT_SIZE_RESULT = 0.15  # method result (colored), ~0.39 pt diameter
POINT_ALPHA_REF = 0.72
POINT_ALPHA_RESULT = 0.85

# ROI detail points. In the ROI the reference layer is additionally rendered as
# OPEN rings and the estimate as solid dots (same rule for all three arms), so
# the two layers and their local offset stay separable even where hues are close.
INSET_POINT_SIZE_REF = 0.30   # open reference ring, ~0.55 pt diameter
INSET_POINT_SIZE_RESULT = 0.34  # solid estimate, ~0.58 pt diameter
INSET_ALPHA_REF = 0.85
INSET_ALPHA_RESULT = 0.90
