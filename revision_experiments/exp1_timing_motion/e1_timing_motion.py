# -*- coding: utf-8 -*-
"""
Experiment 1 (Phase-1, first priority): scan timing / target motion / reference-pose diagnostics.
Association diagnostics ONLY -- never a motion-distortion causal claim.
Outputs (this folder):
  motion_frame_metrics.csv, support_selected_vs_unselected.csv, fig_timing_motion.png
All velocities divide by the REAL inter-pose dt; isolated temporal gaps are flagged and NOT
finite-differenced across. Adjacent-frame interval is never interpreted as single-scan duration.
"""
import os
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import rev_common as Rv  # noqa: E402

COLORS = {"VI": "#1f77b4", "IV": "#d62728", "II": "#2ca02c", "III": "#9467bd"}


def geodesic_deg(Ra, Rb):
    c = np.clip((np.trace(Ra.T @ Rb) - 1.0) / 2.0, -1.0, 1.0)
    return float(np.degrees(np.arccos(c)))


def frame_table(traj):
    cfg = Rv.REG[traj]
    n = cfg["n"]
    ts, tt, RR = Rv.all_poses(traj)
    dt, gap = Rv.gap_flags(ts)
    insup = Rv.support_mask(traj)
    real = Rv.realized_pose_errors(traj)
    rows = []
    for i in range(n):
        row = dict(trajectory=traj, order=i, scan=i, ts=ts[i],
                   in_support=bool(insup[i]), posthoc=bool(cfg.get("posthoc", False)))
        # sensor origin / view geometry in TARGET frame (frozen convention o=-R^T t)
        o = -RR[i].T @ tt[i]; rng = np.linalg.norm(o); u = o / rng
        row["range_m"] = rng
        row["view_u_x"] = u[0]; row["view_u_y"] = u[1]; row["view_u_z"] = u[2]
        row["view_angle_from_plusX_deg"] = float(np.degrees(np.arccos(np.clip(u[0], -1, 1))))
        # per-frame raw residual RMS at xi=0 vs raw nominal model + valid point count
        z = Rv.load_scan_npz(traj, i)
        keys = z.files
        if "d" in keys:
            d = np.asarray(z["d"], float)
        elif "r" in keys:
            d = np.asarray(z["r"], float)
        else:
            P = np.asarray(z["aligned"], float)
            fz = Rv.frozen_bundle()
            _, nn = fz["tree_model"].query(P, k=1, workers=-1)
            d = np.linalg.norm(P - fz["model"][nn], axis=1)
        row["n_valid_points"] = int(len(d))
        row["raw_residual_rms_mm"] = float(1000.0 * np.sqrt(np.mean(d ** 2)))
        # realized frozen pose errors (for panels C/D)
        rl = real.get(i, {})
        row["raw_pose_et_mm"] = rl.get("raw_et", np.nan)
        row["patch_pose_et_mm"] = rl.get("patch_et", np.nan)
        row["patch_raw_gain_mm"] = (rl.get("raw_et", np.nan) - rl.get("patch_et", np.nan))
        # inter-frame motion (real dt; gap edges left NaN)
        if i < n - 1:
            row["dt_s"] = float(dt[i]); row["is_gap"] = bool(gap[i])
            if not gap[i] and dt[i] > 0:
                dtt = tt[i + 1] - tt[i]
                v_body = RR[i].T @ dtt / dt[i]          # local (target-frame) linear velocity
                trans_incr = float(np.linalg.norm(dtt))
                rot_incr = geodesic_deg(RR[i], RR[i + 1])
                row["trans_incr_mm"] = trans_incr * 1000.0
                row["rot_incr_deg"] = rot_incr
                row["trans_speed_mm_s"] = trans_incr * 1000.0 / dt[i]
                row["ang_speed_deg_s"] = rot_incr / dt[i]
                row["local_vx_mm_s"] = v_body[0] * 1000.0
                row["local_vy_mm_s"] = v_body[1] * 1000.0
                row["local_vz_mm_s"] = v_body[2] * 1000.0
            # view-direction change
            on = -RR[i + 1].T @ tt[i + 1]; un = on / np.linalg.norm(on)
            row["view_dir_change_deg"] = float(np.degrees(np.arccos(np.clip(u @ un, -1, 1))))
        else:
            row["dt_s"] = np.nan; row["is_gap"] = False
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_support(df):
    metrics = ["range_m", "view_angle_from_plusX_deg", "view_dir_change_deg",
               "trans_speed_mm_s", "ang_speed_deg_s", "raw_residual_rms_mm", "n_valid_points"]
    out = []
    for tr, g in df.groupby("trajectory"):
        nall = len(g)
        for sel, sub in [(True, g[g.in_support]), (False, g[~g.in_support])]:
            if len(sub) == 0:
                continue
            r = dict(trajectory=tr, selected=sel, n_frames=len(sub),
                     coverage_pct=100.0 * len(sub) / nall)
            for m in metrics:
                x = sub[m].dropna()
                r[f"{m}__median"] = float(np.median(x))
                r[f"{m}__q1"] = float(np.percentile(x, 25))
                r[f"{m}__q3"] = float(np.percentile(x, 75))
            out.append(r)
    return pd.DataFrame(out)


def main():
    cache = os.path.join(HERE, "_frame_table_cache.pkl")
    if os.path.exists(cache):
        df = pd.read_pickle(cache)
        print("[E1] reusing cached frame table")
    else:
        tabs = []
        for tr in Rv.TRAJS:
            print(f"[E1] {tr} ...", flush=True)
            tabs.append(frame_table(tr))
        df = pd.concat(tabs, ignore_index=True)
        df.to_pickle(cache)
    df.to_csv(os.path.join(HERE, "motion_frame_metrics.csv"), index=False)
    sup = summarize_support(df)
    sup.to_csv(os.path.join(HERE, "support_selected_vs_unselected.csv"), index=False)

    # ------------------------------------------------------------ 4-panel diagnostic figure
    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    order = Rv.TRAJS
    # A: angular speed distribution per trajectory
    a = ax[0, 0]
    data = [df[(df.trajectory == t) & df.ang_speed_deg_s.notna()].ang_speed_deg_s.values for t in order]
    a.boxplot(data, tick_labels=order, showfliers=False)
    for i, t in enumerate(order):
        x = df[(df.trajectory == t) & df.ang_speed_deg_s.notna()].ang_speed_deg_s.values
        a.scatter(np.random.RandomState(0).normal(i + 1, 0.05, len(x)), x, s=3, alpha=0.18,
                  color=COLORS[t])
    a.set_ylabel("local angular speed (deg/s, real dt)"); a.set_title("A. Angular-speed distribution by trajectory")
    a.grid(alpha=.3)
    # B: selected vs unselected angular speed
    b = ax[0, 1]; w = 0.35; xs = np.arange(len(order))
    for k, (sel, lab) in enumerate([(True, "support-selected"), (False, "unselected")]):
        meds, lo, hi, used_x, used_t = [], [], [], [], []
        for j, t in enumerate(order):
            x = df[(df.trajectory == t) & (df.in_support == sel)].ang_speed_deg_s.dropna().values
            if len(x) == 0:
                continue  # VI has no unselected frames
            meds.append(np.median(x)); lo.append(np.percentile(x, 25)); hi.append(np.percentile(x, 75))
            used_x.append(j); used_t.append(t)
        off = -w / 2 if k == 0 else w / 2
        b.bar(np.array(used_x) + off, meds, w, yerr=[np.array(meds) - np.array(lo), np.array(hi) - np.array(meds)],
              capsize=3, label=lab, color="#4c78a8" if sel else "#bbbfc4", alpha=.9)
    b.set_xticks(xs); b.set_xticklabels(order); b.set_ylabel("median [IQR] angular speed (deg/s)")
    b.set_title("B. Angular speed: support-selected vs unselected"); b.legend(); b.grid(alpha=.3, axis="y")
    # C: Raw translation error vs angular speed
    c = ax[1, 0]
    for t in order:
        x = df[(df.trajectory == t)]
        c.scatter(x.ang_speed_deg_s, x.raw_pose_et_mm, s=5, alpha=.25, color=COLORS[t], label=t)
        m = x.ang_speed_deg_s.notna() & x.raw_pose_et_mm.notna()
        if m.sum() > 5:
            rho, p = spearmanr(x.ang_speed_deg_s[m], x.raw_pose_et_mm[m])
            c.text(0.02, 0.96 - 0.055 * order.index(t), f"{t}: Spearman ρ={rho:+.2f}",
                   transform=c.transAxes, color=COLORS[t], fontsize=9, va="top")
    c.set_xlabel("local angular speed (deg/s)"); c.set_ylabel("Raw translation error (mm)")
    c.set_title("C. Raw pose error vs angular speed (association only)"); c.legend(markerscale=2); c.grid(alpha=.3)
    # D: Patch-Raw paired gain vs angular speed
    d = ax[1, 1]
    for t in order:
        x = df[(df.trajectory == t)]
        d.scatter(x.ang_speed_deg_s, x.patch_raw_gain_mm, s=5, alpha=.25, color=COLORS[t], label=t)
        m = x.ang_speed_deg_s.notna() & x.patch_raw_gain_mm.notna()
        if m.sum() > 5:
            rho, _ = spearmanr(x.ang_speed_deg_s[m], x.patch_raw_gain_mm[m])
            d.text(0.02, 0.96 - 0.055 * order.index(t), f"{t}: Spearman ρ={rho:+.2f}",
                   transform=d.transAxes, color=COLORS[t], fontsize=9, va="top")
    d.axhline(0, color="k", lw=1)
    d.set_xlabel("local angular speed (deg/s)"); d.set_ylabel("Patch−Raw paired gain (mm, >0 better)")
    d.set_title("D. Patch−Raw gain vs angular speed (association only)"); d.legend(markerscale=2); d.grid(alpha=.3)
    fig.suptitle("Exp.1 timing / motion / reference-pose diagnostics (association, not causal)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(HERE, "fig_timing_motion.png"), dpi=150)
    print("[E1] saved csvs + figure")
    # console summary
    print(sup.to_string())
    print("\nGap counts / dt summary:")
    for t in order:
        x = df[df.trajectory == t]
        print(f"  {t}: gaps={int(x.is_gap.sum())}, dt med={x.dt_s.median():.3f} "
              f"[{x.dt_s.min():.3f},{x.dt_s.max():.3f}], ang med={x.ang_speed_deg_s.median():.3f} deg/s")


if __name__ == "__main__":
    main()
