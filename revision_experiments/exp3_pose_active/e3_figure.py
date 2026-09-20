# -*- coding: utf-8 -*-
"""Exp.3 six-panel direct-validation figure (p2p primary; p2l reported in csv/decision)."""
import os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__))
COL = {"VI": "#1f77b4", "IV": "#d62728", "II": "#2ca02c", "III": "#9467bd"}
TRAJS = ["VI", "IV", "II", "III"]


def ecdf(ax, x, color, label):
    xs = np.sort(x); y = np.arange(1, len(xs) + 1) / len(xs)
    ax.plot(xs, y, color=color, lw=1.8, label=f"{label} (med {np.median(x):.1f}°)")


def main():
    df = pd.read_csv(os.path.join(HERE, "pose_active_direct_framewise.csv"))
    p = df[df.kind == "p2p"].copy()
    p["an_err"] = np.degrees(np.arccos(np.clip(p.an_dircos_t, -1, 1)))
    p["fd_err"] = np.degrees(np.arccos(np.clip(p.fd_dircos_t, -1, 1)))
    fig, AX = plt.subplots(2, 3, figsize=(18, 10))
    # A: residual RMS vs actual translation error
    ax = AX[0, 0]
    for t in TRAJS:
        x = p[p.trajectory == t]; ax.scatter(x.rms_mm, x.actual_t_mm, s=7, alpha=.3, color=COL[t], label=t)
    ax.set_xlabel("Ordinary residual RMS (mm)"); ax.set_ylabel("Realized local translation displacement (mm)")
    ax.set_title("A. Residual RMS versus realized translation displacement"); ax.legend(markerscale=2); ax.grid(alpha=.3)
    # B: RMS_PA vs actual
    ax = AX[0, 1]
    for t in TRAJS:
        x = p[p.trajectory == t]; ax.scatter(x.rms_pa_mm, x.actual_t_mm, s=7, alpha=.3, color=COL[t], label=t)
    ax.set_xlabel("Pose-active residual RMS (RMS_PA) (mm)"); ax.set_ylabel("Realized local translation displacement (mm)")
    ax.set_title("B. Pose-active residual RMS versus realized translation displacement"); ax.legend(markerscale=2); ax.grid(alpha=.3)
    # C: analytic fixed-corr FO direction error ECDF
    ax = AX[0, 2]
    for t in TRAJS: ecdf(ax, p[p.trajectory == t].an_err.values, COL[t], t)
    ax.set_xlabel("First-order vs realized direction error (deg)"); ax.set_ylabel("ECDF"); ax.set_xlim(0, 90)
    ax.set_title("C. First-order direction with fixed correspondences"); ax.legend(fontsize=8); ax.grid(alpha=.3)
    # D: FD rematching direction error ECDF
    ax = AX[1, 0]
    for t in TRAJS: ecdf(ax, p[p.trajectory == t].fd_err.values, COL[t], t)
    ax.set_xlabel("Rematching FD step vs realized direction error (deg)"); ax.set_ylabel("ECDF"); ax.set_xlim(0, 90)
    ax.set_title("D. Rematching finite-difference direction"); ax.legend(fontsize=8); ax.grid(alpha=.3)
    # E: predicted magnitude vs actual magnitude
    ax = AX[1, 1]
    m = 0; Mx = np.percentile(p.actual_t_mm, 99)
    ax.plot([m, Mx], [m, Mx], "k--", lw=1, label="y=x")
    ax.scatter(p.actual_t_mm, p.an_t_mm, s=6, alpha=.25, color="#ff7f0e", label="First-order (fixed corr.)")
    ax.scatter(p.actual_t_mm, p.fd_t_mm, s=6, alpha=.18, color="#1f77b4", label="Rematching FD")
    ax.set_xlim(0, Mx); ax.set_ylim(0, Mx); ax.set_xlabel("Realized translation displacement (mm)"); ax.set_ylabel("Predicted step magnitude (mm)")
    ax.set_title("E. Predicted versus realized translation-step magnitude"); ax.legend(fontsize=8); ax.grid(alpha=.3)
    # F: condition / switch rate vs prediction error
    ax = AX[1, 2]
    for t in TRAJS:
        x = p[p.trajectory == t]
        ax.scatter(x.cond, x.an_err, s=8, alpha=.25, color=COL[t], label=t)
    diag = p[p.switch_rate.notna()]
    ax.scatter(diag.cond, diag.an_err, s=10 + 120 * diag.switch_rate, facecolors="none",
               edgecolors="black", linewidths=.8, label="Diagnostic (marker area ∝ correspondence-switch rate)")
    rho = spearmanr(p.cond, p.an_err)[0]
    ax.set_xlabel("Normal-equation condition number (6×6 H_GN)"); ax.set_ylabel("First-order direction error (deg)")
    ax.set_title(f"F. Condition number / correspondence switching vs prediction error (ρ_cond={rho:+.2f})",
                 fontsize=9.5)  # slightly smaller only so the longer new title + rho value fits within fig width (figsize unchanged)
    ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.suptitle("Comparison of local predictions on the same analyzed frames (p2p; fixed reference-pose correspondences at ξ=0)", fontsize=13)
    # Note (caption-level facts, no data change):
    #  - rho = Spearman rank correlation (scipy.stats.spearmanr) between cond and an_err.
    #  - cond is sv_max/sv_min of the full 6x6 H = J^T W J (rev_common.fixed_corr_pose_active),
    #    with translation/rotation in native m/rad (no coordinate rescaling).
    #  - switch_rate comes from exp2_iter_budget correspondence_switch_rate (Raw, max_iter=40),
    #    denominator = number of correspondences; marker s = 10 + 120*switch_rate (scatter s = area in pts^2).
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(HERE, "fig_pose_active_direct_validation.png"), dpi=150)
    # Same figure exported as vector PDF for submission (no change to size/dpi/data).
    fig.savefig(os.path.join(HERE, "fig_pose_active_direct_validation.pdf"))
    print("saved figure; n p2p =", len(p))


if __name__ == "__main__":
    main()
