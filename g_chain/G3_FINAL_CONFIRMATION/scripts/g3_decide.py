# -*- coding: utf-8 -*-
"""g3_decide.py -- evaluate the PRE-REGISTERED C1/C2/C3 criteria from the single-look III CSVs (no re-run,
no tuning, no frame removal) and render figures. Prints every quantity feeding the verdict."""
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

import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = _pp("g_chain/G3_FINAL_CONFIRMATION")
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures"); os.makedirs(FIG, exist_ok=True)
G0W = _pp("g_chain/G0_ROBUST_FALSIFICATION/results")
G1W = _pp("g_chain/G1_MITIGATION/results"); G2W = _pp("g_chain/G2_ESTIMATED_VIEW/results")

def med(x): return float(np.nanmedian(x))

def main():
    g0 = pd.read_csv(os.path.join(RES, "g0_iii.csv"))
    g1 = pd.read_csv(os.path.join(RES, "g1_iii.csv"))
    g2 = pd.read_csv(os.path.join(RES, "g2_iii.csv"))
    out = {}
    # ---------- C1: robust does not resolve (in-support, p2p) ----------
    p = g0[(g0.kind == "p2p")]
    real = p[p.real == 1]; selfn = p[p.real == 0]
    ins = real[real.in_support]
    c1 = {}
    for form in ["ls", "huber", "trim"]:
        c1[form] = med(ins[ins.form == form].et_mm)
    c1["selfnull_huber"] = med(selfn[(selfn.form == "huber")].et_mm)
    c1["selfnull_ls"] = med(selfn[(selfn.form == "ls")].et_mm)
    c1["huber_over_half_ls"] = c1["huber"] > 0.5 * c1["ls"]
    c1["huber_to_self_ratio"] = c1["huber"] / max(c1["selfnull_huber"], 1e-12)
    c1["frac_frames_gt10mm_huber"] = float((ins[ins.form == "huber"].et_mm > 10).mean())
    # block-level: every block median >10mm?
    blk = ins[ins.form == "huber"].groupby("block").et_mm.median()
    c1["blocks_all_gt10mm"] = bool((blk > 10).all()); c1["n_blocks"] = int(blk.size)
    c1["PASS"] = bool(c1["huber_over_half_ls"] and c1["huber_to_self_ratio"] > 10 and c1["frac_frames_gt10mm_huber"] > 0.9)
    out["C1"] = c1

    # ---------- C2: oracle mitigation actionable (in-support) ----------
    w = g1[g1.in_support].pivot_table(index="scan", columns="method", values="et_mm")
    c2 = {}
    for lvl in ["M4_patch_corr", "M5_full_corr"]:
        d = w["M0_raw_p2p"].values - w[lvl].values
        bb = G.block_boot(d, np.median, B=2000, Ls=(5, 10, 20), seed=42)
        pval = G.block_signflip_p(d, B=2000, L=5, seed=42)[1]
        c2[lvl] = dict(med_M0=med(w["M0_raw_p2p"]), med_lvl=med(w[lvl]), med_gain=med(d),
                       ci=(bb["L5_lo"], bb["L5_hi"]), signflip_p=pval, frac_improved=float((d > 0).mean()))
    def lvl_ok(d): return d["med_gain"] > 0 and d["signflip_p"] < 0.05 and d["frac_improved"] >= 0.80
    c2["patch_ok"] = lvl_ok(c2["M4_patch_corr"]); c2["full_ok"] = lvl_ok(c2["M5_full_corr"])
    c2["best_level"] = "patch" if c2["M4_patch_corr"]["med_lvl"] <= c2["M5_full_corr"]["med_lvl"] else "full"
    c2["PASS"] = bool(c2["patch_ok"] or c2["full_ok"])
    out["C2"] = c2

    # ---------- C3: estimated-view deployable (in-support) ----------
    a = g2[(g2.arm != "view_gap") & g2.in_support].pivot_table(index="scan", columns="arm", values="et_mm")
    ret = (a["T0_raw"] - a["est_warmstart"]) / (a["T0_raw"] - a["oracle"] + 1e-9)
    c3 = dict(med_T0=med(a["T0_raw"]), med_oracle=med(a["oracle"]),
              med_est_warm=med(a["est_warmstart"]), med_est_gt=med(a["est_gtstart"]),
              med_retention=med(ret), frac_warm_better=float((a["est_warmstart"] < a["T0_raw"]).mean()))
    c3["retention_ge_0.70"] = c3["med_retention"] >= 0.70
    c3["frac_ge_0.60"] = c3["frac_warm_better"] >= 0.60
    c3["PASS"] = bool(c3["retention_ge_0.70"] and c3["frac_ge_0.60"])
    out["C3"] = c3

    # ---------- verdict ----------
    nC = int(c1["PASS"]) + int(c2["PASS"]) + int(c3["PASS"])
    if c1["PASS"] and c2["PASS"] and c3["PASS"]: verdict = "CONFIRMED"
    elif c1["PASS"] and (int(c2["PASS"]) + int(c3["PASS"]) == 1): verdict = "PARTIALLY_CONFIRMED"
    else: verdict = "NOT_CONFIRMED"
    out["verdict"] = verdict

    # all-frame (secondary) context
    allins = real
    out["secondary_all1302"] = {f: med(allins[allins.form == f].et_mm) for f in ["ls", "huber", "trim"]}
    wa = g1.pivot_table(index="scan", columns="method", values="et_mm")
    out["secondary_all1302"]["M0"] = med(wa["M0_raw_p2p"]); out["secondary_all1302"]["M4"] = med(wa["M4_patch_corr"])
    out["secondary_all1302"]["M5"] = med(wa["M5_full_corr"])

    with open(os.path.join(RES, "single_look_summary.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print(json.dumps(out, indent=2, default=float))

    # ---------- figures ----------
    # F1 G0 formulations vs self
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    labs = ["ls", "huber", "trim"]; xx = np.arange(3)
    ax.bar(xx - .2, [c1[f] for f in labs], .4, label="III real (in-support)")
    ax.bar(xx + .2, [c1["selfnull_ls"], c1["selfnull_huber"], med(selfn[selfn.form=="trim"].et_mm)], .4, label="matched self-null")
    ax.set_xticks(xx); ax.set_xticklabels(["LS", "Huber", "Trim"]); ax.set_ylabel("median GT-start e_t [mm]")
    ax.set_title("G3 C1: robust formulation vs self-null on III"); ax.legend(); ax.grid(alpha=.25, axis="y")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "G3F1_robust_vs_self.png"), dpi=140); plt.close()

    # F2 G1 methods
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    meth = ["M0_raw_p2p", "M1_raw_p2l", "M2_raw_huber", "M3_global_corr", "M4_patch_corr", "M5_full_corr"]
    mm = [med(w[m]) for m in meth]
    ax.bar(range(6), mm, color=["0.5", "0.6", "0.7", "#9ecae1", "#3182bd", "#08519c"])
    ax.set_xticks(range(6)); ax.set_xticklabels(["M0", "M1", "M2", "M3glob", "M4patch", "M5full"], rotation=20)
    ax.set_ylabel("median oracle e_t [mm]"); ax.set_title("G3 C2: frozen mitigation methods on III (in-support)")
    ax.grid(alpha=.25, axis="y"); plt.tight_layout(); plt.savefig(os.path.join(FIG, "G3F2_methods.png"), dpi=140); plt.close()

    # F3 G2 arms vs other trajectories
    arms = ["T0_raw", "oracle", "est_gtstart", "est_warmstart"]
    oth = pd.read_csv(os.path.join(G2W, "oracle_vs_estimated.csv"))
    fig, ax = plt.subplots(figsize=(8.4, 4.4)); xs = np.arange(5); wd = .2
    series = {"VI": "vi", "IV": "iv", "II": "ii", "V": "v"}
    for k, arm in enumerate(arms):
        col = {"T0_raw": "et_T0", "oracle": "et_oracle", "est_gtstart": "et_est_gtstart",
               "est_warmstart": "et_est_warmstart"}[arm]
        vals = [oth[oth.traj == t][col].values[0] for t in ["vi", "iv", "ii", "v"]]
        vals.append(c3[{"T0_raw": "med_T0", "oracle": "med_oracle", "est_gtstart": "med_est_gt",
                        "est_warmstart": "med_est_warm"}[arm]])
        ax.bar(xs + (k - 1.5) * wd, vals, wd, label=arm)
    ax.set_xticks(xs); ax.set_xticklabels(["VI", "IV", "II", "V", "III (single-look)"])
    ax.set_ylabel("median e_t [mm]"); ax.set_title("G3 C3: estimated-view pipeline, III vs prior trajectories")
    ax.legend(fontsize=8); ax.grid(alpha=.25, axis="y"); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "G3F3_arms_cross.png"), dpi=140); plt.close()
    print("[g3_decide] figures + summary written; VERDICT =", verdict)

if __name__ == "__main__":
    main()
