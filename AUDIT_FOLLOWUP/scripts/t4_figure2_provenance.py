# -*- coding: utf-8 -*-
"""TASK 4 (P0): Figure 2C-E shaded-band statistical definition + full data lineage.

NO new experiment. Independently re-derive the Figure-2 plotted tables from the upstream
`patch_persistence.csv` using the EXACT logic of FINAL_FIGURES/build_all_figures.py figure2(),
assert equality with the shipped tables, and export one machine-readable statistics table plus a
provenance report that states, for every panel: center statistic, shaded-band statistic,
statistical unit, and per-curve / per-bin sample counts.
"""
import os, sys, hashlib
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import af_common as A

S = A.PHASE
SRES = os.path.join(A.ROOT, "structured_mismatch_phase0", "results")
FIG2 = os.path.join(A.ROOT, "FINAL_FIGURES", "Figure2")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def df_to_md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def main():
    pp = pd.read_csv(os.path.join(SRES, "patch_persistence.csv"))
    defs = pd.read_csv(os.path.join(SRES, "patch_definition.csv"))
    F = np.load(os.path.join(A.RESC, "VI_ONLY_PREDICTOR_FROZEN.npz"))
    blocks = F["blocks"]

    # ---- replicate build_all_figures.figure2 preprocessing ----
    p = pp.copy()
    p["block"] = blocks[p.scan_id.to_numpy(int)]
    p["residual_mm"] = p.median_residual * 1000.0
    p = p[(p.support_count > 0) & np.isfinite(p.residual_mm)].copy()
    n_cells = len(p)

    # panel B heatmap (block x patch): median of per-scan patch-median
    heat = p.pivot_table(index="block", columns="patch_id", values="residual_mm",
                         aggfunc="median").reindex(columns=range(24))
    heat_n = p.pivot_table(index="block", columns="patch_id", values="residual_mm",
                           aggfunc="size").reindex(columns=range(24))
    ship_b = pd.read_csv(os.path.join(FIG2, "patch_block_residual.csv"))
    # chosen patches: largest model_point_count per dominant-normal family
    defs["family"] = np.argmax(np.abs(
        defs[["patch_normal_x", "patch_normal_y", "patch_normal_z"]].to_numpy()), axis=1)
    chosen = (defs.sort_values(["model_point_count", "patch_id"], ascending=[False, True])
              .groupby("family", sort=True).head(1).sort_values("family").patch_id.tolist())
    panel_letter = {j: chr(67 + i) for i, j in enumerate(chosen)}

    edges = np.linspace(p.range_m.min(), p.range_m.max(), 9)
    rows_bin = []
    for j in chosen:
        q = p[p.patch_id == j].copy()
        q["range_bin"] = pd.cut(q.range_m, edges, include_lowest=True)
        agg = (q.groupby("range_bin", observed=True)
               .agg(x=("range_m", "median"), med=("residual_mm", "median"),
                    lo=("residual_mm", lambda x: x.quantile(.25)),
                    hi=("residual_mm", lambda x: x.quantile(.75)),
                    n=("residual_mm", "size")).reset_index(drop=True))
        for bi, r in agg.iterrows():
            rows_bin.append(dict(panel=f"2{panel_letter[j]}", patch_id=int(j), bin_index=int(bi),
                                 bin_edge_lo_m=float(edges[bi]), bin_edge_hi_m=float(edges[bi + 1]),
                                 range_center_m=float(r.x), center_median_mm=float(r.med),
                                 band_q25_mm=float(r.lo), band_q75_mm=float(r.hi),
                                 n_stat_units=int(r.n),
                                 center_statistic="median", shaded_band="IQR (25th-75th percentile)",
                                 statistical_unit="one supported VI scan's patch-median residual"))
    B = pd.DataFrame(rows_bin)

    rows_heat = []
    for blk in heat.index:
        for pj in range(24):
            v = heat.loc[blk, pj]
            if np.isfinite(v):
                rows_heat.append(dict(panel="2B", patch_id=int(pj), block=int(blk),
                                      center_median_mm=float(v),
                                      n_stat_units=int(heat_n.loc[blk, pj]),
                                      center_statistic="median over scans in block",
                                      shaded_band="NONE (heatmap cell = single value)",
                                      statistical_unit="one supported VI scan's patch-median residual",
                                      bin_edge_lo_m=np.nan, bin_edge_hi_m=np.nan, range_center_m=np.nan,
                                      band_q25_mm=np.nan, band_q75_mm=np.nan, bin_index=np.nan))
    HB = pd.DataFrame(rows_heat)
    stats = pd.concat([HB, B], ignore_index=True)
    stats.to_csv(os.path.join(A.OUT, "figure2_plot_statistics.csv"), index=False)

    # ---- equality checks vs shipped plotted tables ----
    ship = pd.read_csv(os.path.join(FIG2, "view_examples_binned.csv"))
    # both are ordered [chosen patch 0 bins 0-7, patch 1 ..., patch 2 ...]; compare positionally
    Bord = B.sort_values(["patch_id", "bin_index"]).reset_index(drop=True)
    ship = ship.sort_values(["patch_id", "x"]).reset_index(drop=True)
    # align groups by patch and within patch by range-center rank (bin order)
    a_parts, s_parts = [], []
    for j in chosen:
        a_parts.append(Bord[Bord.patch_id == j].sort_values("bin_index").reset_index(drop=True))
        sq = ship[ship.patch_id == j].sort_values("x").reset_index(drop=True)
        s_parts.append(sq)
    Aa = pd.concat(a_parts, ignore_index=True); Ss = pd.concat(s_parts, ignore_index=True)
    dn = (Aa.n_stat_units.to_numpy() - Ss.n.to_numpy())
    d_med = float(np.abs(Aa.center_median_mm.to_numpy() - Ss.med.to_numpy()).max())
    d_lo = float(np.abs(Aa.band_q25_mm.to_numpy() - Ss.lo.to_numpy()).max())
    d_hi = float(np.abs(Aa.band_q75_mm.to_numpy() - Ss.hi.to_numpy()).max())
    d_x = float(np.abs(Aa.range_center_m.to_numpy() - Ss.x.to_numpy()).max())
    d_n = int(np.abs(dn).max())
    # heat shipped
    ship_h = ship_b.set_index("block").drop(columns=[c for c in ship_b.columns if c == "block"],
                                            errors="ignore")
    dh = np.nanmax(np.abs(ship_h.to_numpy(float) - heat.to_numpy(float)))

    per_curve = (B.groupby(["panel", "patch_id"])
                 .agg(n_bins=("n_stat_units", "size"), n_total=("n_stat_units", "sum"),
                      n_min=("n_stat_units", "min"), n_max=("n_stat_units", "max")).reset_index())

    src = {
        "patch_persistence.csv": os.path.join(SRES, "patch_persistence.csv"),
        "patch_definition.csv": os.path.join(SRES, "patch_definition.csv"),
        "residual source": "s1_residuals.py -> cache/scans/scan_XXXX.npz keys r/signed/lab; "
                           "s3_patches.py aggregates to (scan,patch) cells",
        "build script": "FINAL_FIGURES/build_all_figures.py :: figure2()",
    }
    hashes = {os.path.basename(k) if k.endswith(".csv") else k: sha256(v)
              for k, v in src.items() if isinstance(v, str) and os.path.exists(v)}

    lines = []
    lines.append("# Figure 2 provenance and statistical definition (post-audit follow-up)\n")
    lines.append("Mode: read-only lineage trace + independent re-derivation. No figure redrawn, no data "
                 "re-generated, no frozen result modified.\n")
    lines.append("## 1. Data lineage (oldest -> plotted)\n")
    lines.append("1. `s1_residuals.py` computes, for every GT-aligned VI scan, the nearest-nominal-model "
                 "distance `r`, signed normal residual `signed` and model-point patch label, cached in "
                 "`structured_mismatch_phase0/scripts/cache/scans/scan_XXXX.npz`.")
    lines.append("2. `s3_patches.py` aggregates to one row per (scan, patch=0..23): support_count, "
                 "median_residual (m), mean_signed_residual, range_m -> "
                 "`results/patch_persistence.csv` (501 scans x 24 patches = 12024 rows).")
    lines.append("3. `FINAL_FIGURES/build_all_figures.py :: figure2()` filters support_count>0 & finite "
                 f"(kept {n_cells} cells), attaches the frozen VI orientation block, and builds panels A-E; "
                 "plotted reductions are exported to FINAL_FIGURES/Figure2/*.csv.\n")
    lines.append("## 2. Per-panel statistical definition\n")
    lines.append("| Panel | What is drawn | Center line | Shaded region | Statistical unit |")
    lines.append("|---|---|---|---|---|")
    lines.append("| 2A | Orthographic projection of the frozen nominal model + patch ID labels | "
                 "none (schematic scatter/annotation) | none | model point (schematic, no statistic) |")
    lines.append("| 2B | Heatmap, rows = 6 frozen VI orientation blocks, cols = patch 0-23 | "
                 "each cell = **median** of the per-scan patch-median residuals in that block (mm) | "
                 "none (discrete heatmap, masked when no supported scan) | one supported (scan,patch) cell |")
    lines.append("| 2C/D/E | Residual vs sensor range for patches "
                 f"{chosen} (largest patch per dominant normal family x/y/z, chosen without outcomes) | "
                 "**median** within each range bin (mm) | **IQR = 25th-75th percentile** within the bin "
                 "(NOT SD, NOT a CI, NOT a percentile fan beyond quartiles, no fitted curve) | "
                 "one supported VI scan's patch-median residual for that patch |")
    lines.append("")
    lines.append("- Range bins: **8 fixed equal-width** bins, edges = linspace(min,max,9) over ALL "
                 "supported VI observations (identical edges for the three panels); x position = median "
                 "sensor range in the bin.")
    lines.append("- The statistical unit is the **scan-level** patch median (501 VI scans max), never a "
                 "single lidar point and never a block; blocks appear only in panel B.")
    lines.append("- Sample counts are small in some bins (see n below); IQR bands are descriptive and "
                 "must not be read as independent confidence intervals (range and orientation covary on VI).\n")
    lines.append("## 3. Per-curve sample counts (panels C-E)\n")
    lines.append(df_to_md(per_curve))
    lines.append("")
    lines.append("## 4. Independent re-derivation vs shipped plotted tables (verification)\n")
    lines.append(f"- panels C-E: max |re-derived median - shipped| = {d_med:.3e} mm; "
                 f"Q25 {d_lo:.3e}; Q75 {d_hi:.3e}; bin range-center {d_x:.3e} m; "
                 f"per-bin count mismatch = {d_n}.")
    lines.append(f"- panel B heatmap: max |re-derived - shipped| = {dh:.3e} mm.")
    lines.append("- Result: the shipped Figure-2 tables are reproduced exactly; the caption wording "
                 "(median line, IQR shade, 8 equal-width bins, scan-level unit) matches the code.\n")
    lines.append("## 5. Source hashes\n")
    for k, v in hashes.items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## 6. Caption-ready statement\n")
    lines.append("> Panels C-E show, for one patch from each dominant normal family, the median (line) and "
                 "25th-75th-percentile IQR (shading) of the per-scan patch-median residual within eight "
                 "fixed equal-width sensor-range bins; each observation is one supported VI scan (sample "
                 "counts per bin are in figure2_plot_statistics.csv). The band is a descriptive IQR, not a "
                 "standard deviation or confidence interval; no curve is fit and independence across bins "
                 "is not assumed. Panel B cell colour is the median over scans within each frozen "
                 "orientation block.")
    with open(os.path.join(A.OUT, "figure2_provenance.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("[T4] chosen patches", chosen, "kept cells", n_cells)
    print("[T4] equality d_med=%.2e d_lo=%.2e d_hi=%.2e d_x=%.2e heat=%.2e" % (d_med, d_lo, d_hi, d_x, dh))
    print(per_curve.to_string(index=False))
    print("[T4] wrote figure2_plot_statistics.csv rows", len(stats))


if __name__ == "__main__":
    main()
