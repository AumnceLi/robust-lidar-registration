# -*- coding: utf-8 -*-
"""TJ2 Phase-1 (part C): FROZEN support-distance screen for EPOS datasets I/II/III.

INPUTS ALLOWED IN PHASE 1 (no point clouds, no residuals, no objective/registration outcome):
  * candidate .pose files only (GT pose -> range + target-frame view direction)
  * the FROZEN VI-only predictor arrays (vrange, uview, blocks, range_std, tau_support)
NO .3d file is read here. Support distance is the SAME frozen metric used in TJ1 (r8):
    d(z,VI) = min_i sqrt( ((vr_i - zr)/range_std)^2 + arccos(clip(uview_i . u))^2 )
    IN_SUPPORT  <=>  d <= tau_support = 0.4403305559611483
Everything here is geometry/metadata only; predictor is NOT refit and tau is NOT changed.
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

import os, sys, glob, json, csv
import numpy as np

PHASE0_SCRIPTS = _pp("structured_mismatch_phase0/scripts")
sys.path.insert(0, PHASE0_SCRIPTS)
import s0_common as C  # frozen, hash-verified; used ONLY for quat_to_R (rotation convention)

ROOT = _pp("tj2_supplemental")
META = os.path.join(ROOT, "metadata"); RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)
FROZ = os.path.join(PHASE0_SCRIPTS, "cache", "rescue", "VI_ONLY_PREDICTOR_FROZEN.npz")
TAGS = ["i", "ii", "iii"]; TAGNAME = {"i": "Dataset_I", "ii": "Dataset_II", "iii": "Dataset_III"}

def load_pose(path):
    with open(path) as fh:
        L = [ln.strip() for ln in fh if ln.strip()]
    ts = float(L[0]); t = np.array(L[1].split(), float); q = np.array(L[2].split(), float)
    return ts, t, q

def view_geom(path):
    ts, t, q = load_pose(path); R = C.quat_to_R(q)
    o = -R.T @ t
    rng = float(np.linalg.norm(o)); u = o / rng
    return ts, rng, u

def runs(flag):
    """maximal contiguous True runs over ordered index; return (n_blocks, lengths, starts)."""
    idx = np.where(np.diff(np.concatenate(([0], flag.view(np.int8), [0]))) != 0)[0]
    starts = idx[0::2]; ends = idx[1::2]; lens = ends - starts
    return len(lens), lens, starts

def main():
    F = np.load(FROZ)
    vr = F["vrange"].astype(np.float64); uv = F["uview"].astype(np.float64)
    vblocks = F["blocks"].astype(int)
    sr = float(F["range_std"]); tau = float(F["tau_support"]); kstar = int(F["kstar"])
    assert abs(tau - 0.4403305559611483) < 1e-12 and kstar == 16 and sr > 0
    vi_rmin, vi_rmax = float(vr.min()), float(vr.max())
    summary = {"_frozen": dict(tau_support=tau, range_std_m=sr, kstar=kstar,
                               vi_n=len(vr), vi_range_min=round(vi_rmin, 4),
                               vi_range_max=round(vi_rmax, 4),
                               vi_n_orientation_blocks=int(len(np.unique(vblocks)))),
               "trajectories": {}}
    per_scan_rows = []
    for tag in TAGS:
        pdir = os.path.join(META, f"poses_{tag}")
        files = sorted(glob.glob(os.path.join(pdir, "*.pose")))
        n = len(files); ts = np.empty(n); rg = np.empty(n); U = np.empty((n, 3))
        for j, fp in enumerate(files):
            ts[j], rg[j], U[j] = view_geom(fp)
        # frozen support distance to all 501 VI training views
        ang = np.arccos(np.clip(U @ uv.T, -1, 1))         # n x 501
        dr = (rg[:, None] - vr[None, :]) / sr
        D = np.sqrt(dr * dr + ang * ang)
        dmin = D.min(1); nn_vi = D.argmin(1)
        ins = dmin <= tau
        # temporal blocks (contiguous runs over ordered scan index)
        nb, blens, bstarts = runs(ins)
        # temporal decile spread (10 equal index bins)
        dec = np.minimum((np.arange(n) * 10 // n), 9)
        dec_hit = sorted(set(dec[ins].tolist()))
        dec_counts = [int(((dec == q) & ins).sum()) for q in range(10)]
        # orientation coverage: distinct frozen VI orientation blocks reached by nearest VI view
        vi_blocks_hit = sorted(set(vblocks[nn_vi[ins]].tolist()))
        # angular gap to nearest VI view (orientation-only component) and range gap component
        nearest_ang = ang[np.arange(n), nn_vi]
        nearest_dr = (rg - vr[nn_vi]) / sr
        # in-support range coverage
        rg_in = rg[ins]
        def pct(a, q):
            return float(np.percentile(a, q)) if len(a) else None
        s = dict(
            tag=TAGNAME[tag], n_scans=n,
            N_IN_SUPPORT=int(ins.sum()),
            in_support_fraction=float(ins.mean()),
            tau_support=tau,
            # temporal
            n_support_blocks=int(nb),
            support_block_lengths=[int(x) for x in blens],
            support_block_max_len=int(blens.max()) if nb else 0,
            support_block_median_len=float(np.median(blens)) if nb else 0.0,
            temporal_deciles_with_support=int(len(dec_hit)),
            temporal_decile_in_counts=dec_counts,
            # orientation
            n_distinct_VI_orientation_blocks_hit=int(len(vi_blocks_hit)),
            vi_orientation_blocks_hit=vi_blocks_hit,
            # range coverage (all + in-support)
            range_min_all=float(rg.min()), range_max_all=float(rg.max()),
            range_mean_all=float(rg.mean()), range_median_all=float(np.median(rg)),
            range_min_ins=float(rg_in.min()) if ins.any() else None,
            range_max_ins=float(rg_in.max()) if ins.any() else None,
            range_median_ins=float(np.median(rg_in)) if ins.any() else None,
            vi_range_overlay_frac_all=float(((rg >= vi_rmin) & (rg <= vi_rmax)).mean()),
            # distance diagnostics
            dmin_p50=float(np.median(dmin)), dmin_p05=pct(dmin, 5), dmin_p95=pct(dmin, 95),
            nearest_view_angle_deg_median=float(np.degrees(np.median(nearest_ang))),
            nearest_scaled_range_gap_median=float(np.median(nearest_dr)),
        )
        summary["trajectories"][tag] = s
        for j in range(n):
            per_scan_rows.append(dict(trajectory=TAGNAME[tag], scan=int(os.path.basename(files[j])[:4]),
                                      ts=ts[j], range_m=rg[j], ux=U[j, 0], uy=U[j, 1], uz=U[j, 2],
                                      dmin=dmin[j], in_support=bool(ins[j]),
                                      nearest_vi=int(nn_vi[j]),
                                      nearest_vi_block=int(vblocks[nn_vi[j]]),
                                      nearest_angle_deg=float(np.degrees(nearest_ang[j]))))
        print(f"[{tag}] n={n} IN={ins.sum()} ({ins.mean()*100:.1f}%) blocks={nb} "
              f"deciles={len(dec_hit)}/10 viOrientBlocks={len(vi_blocks_hit)} "
              f"range(all)=[{rg.min():.2f},{rg.max():.2f}] dmin_med={np.median(dmin):.3f}")
    # write per-trajectory summary CSV (required deliverable)
    cols = ["trajectory", "n_scans", "N_IN_SUPPORT", "in_support_fraction",
            "n_support_blocks", "support_block_max_len", "support_block_median_len",
            "temporal_deciles_with_support", "n_distinct_VI_orientation_blocks_hit",
            "range_min_all", "range_max_all", "range_median_all",
            "range_min_ins", "range_max_ins", "range_median_ins",
            "vi_range_overlay_frac_all", "dmin_p50", "nearest_view_angle_deg_median",
            "nearest_scaled_range_gap_median", "tau_support"]
    with open(os.path.join(RES, "SUPPLEMENTAL_METADATA_SCREEN.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for tag in TAGS:
            s = summary["trajectories"][tag]
            w.writerow({c: (s["tag"] if c == "trajectory" else s.get(c)) for c in cols})
    # per-scan audit table (geometry only)
    with open(os.path.join(RES, "SUPPLEMENTAL_support_perscan.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(per_scan_rows[0].keys())); w.writeheader()
        w.writerows(per_scan_rows)
    with open(os.path.join(META, "support_screen_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("[saved] SUPPLEMENTAL_METADATA_SCREEN.csv + per-scan audit + json")

if __name__ == "__main__":
    main()
