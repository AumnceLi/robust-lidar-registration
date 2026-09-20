# -*- coding: utf-8 -*-
"""Small-sample gate: replay must reproduce frozen g0/g1 arms and stored ext_predict dxi."""
import os, sys
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import replay79 as R
R._init()
import af_common as A, g_common as G

G1 = os.path.join(A.GCHAIN, "G1_MITIGATION", "results")
G0 = os.path.join(A.GCHAIN, "G0_ROBUST_FALSIFICATION", "results")
G3 = os.path.join(A.GCHAIN, "G3_FINAL_CONFIRMATION", "results")

def g1tab(tr):
    f = {"VI": "g1_oracle_vi.csv", "IV": "g1_oracle_iv.csv", "II": "g1_oracle_ii.csv",
         "V": "g1_oracle_v.csv", "III": os.path.join(G3, "g1_iii.csv")}[tr]
    return pd.read_csv(f if os.path.isabs(f) else os.path.join(G1, f))

def g0tab(tr):
    return pd.read_csv(os.path.join(G0, f"g0_frame_{tr.lower()}.csv"))

tasks_all = R.frame_tasks()
worst = {"Raw": 0, "Huber": 0, "Trim": 0, "Patch": 0, "Full": 0, "dxi": 0, "nd": 0}
for tr in ["VI", "IV", "II", "III", "V"]:
    tk = tasks_all[tr]
    sel = list(np.linspace(0, len(tk) - 1, 6, dtype=int))
    g1 = g1tab(tr).set_index(["method", "order"])
    if tr != "III":
        g0 = g0tab(tr); g0 = g0[g0.real == 1]
    for i in sel:
        arows, srow = R._one(tk[i]); order = tk[i][1]
        ad = {r["arm"]: r for r in arows}
        for arm, meth, key in [("Raw", "M0_raw_p2p", "Raw"), ("Patch", "M4_patch_corr", "Patch"),
                               ("Full", "M5_full_corr", "Full")]:
            ref = g1.loc[(meth, order)]
            worst[key] = max(worst[key], abs(ad[arm]["et_mm"] - ref.et_mm),
                             abs(ad[arm]["eR_deg"] - ref.eR_deg))
            worst["nd"] = max(worst["nd"], abs(srow["nearest_d"] - ref.nearest_d))
        if tr != "III":
            for arm, form, key in [("Huber", "huber", "Huber"), ("Trim", "trim", "Trim")]:
                ref = g0[(g0.order == order) & (g0.kind == "p2p") & (g0.form == form)].iloc[0]
                worst[key] = max(worst[key], abs(ad[arm]["et_mm"] - ref.et_mm),
                                 abs(ad[arm]["eR_deg"] - ref.eR_deg))
    # predicted dxi vs stored ext_predict (external)
    if tr != "VI" and tr != "III":
        P = np.load(A.REG[tr]["pred"]); meta = pd.read_csv(A.REG[tr]["meta"])
        insup = P["insup"].astype(bool)
        idx = np.arange(len(meta)) if tr == "V" else np.where(insup)[0]   # V: ALL frames
        for i in sel:
            o = idx[i]; sid = int(meta.scan.iloc[o]); zr = float(meta.range_m.iloc[o])
            zu = meta[["ux", "uy", "uz"]].iloc[o].values.astype(float)
            z = np.load(os.path.join(A.REG[tr]["scandir"], f"scan_{sid:04d}.npz"))
            mu, _ = G.mu_for_view(R._G["Vmean"], R._G["Vcnt"], R._G["vrange"], R._G["uview"], zr, zu)
            dxi = R.predicted_dxi(z["aligned"].astype(float), z["nnidx"], mu)
            worst["dxi"] = max(worst["dxi"], float(np.abs(dxi - P["dxi"][o]).max()))
    print(f"{tr}: checked {len(sel)} frames")
print("WORST abs diffs:", {k: f"{v:.3e}" for k, v in worst.items()})
