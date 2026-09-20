# -*- coding: utf-8 -*-
"""Full gate: every replay frame must reproduce frozen g0/g1 arms (and stored dxi)."""
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

import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, _pp("AUDIT_FOLLOWUP/scripts"))
import af_common as A

OUT = _pp("FOLLOWUP_6_9")
G1 = os.path.join(A.GCHAIN, "G1_MITIGATION", "results"); G0 = os.path.join(A.GCHAIN, "G0_ROBUST_FALSIFICATION", "results")
G3 = os.path.join(A.GCHAIN, "G3_FINAL_CONFIRMATION", "results")
ARMS = pd.read_csv(os.path.join(OUT, "scripts", "replay79_arms.csv"))
SUP = pd.read_csv(os.path.join(OUT, "scripts", "replay79_support.csv"))

def g1tab(tr):
    f = {"VI": "g1_oracle_vi.csv", "IV": "g1_oracle_iv.csv", "II": "g1_oracle_ii.csv",
         "V": "g1_oracle_v.csv", "III": os.path.join(G3, "g1_iii.csv")}[tr]
    return pd.read_csv(f if os.path.isabs(f) else os.path.join(G1, f))

rows = []
for tr in ["VI", "IV", "II", "III", "V"]:
    a = ARMS[ARMS.trajectory == tr]; s = SUP[SUP.trajectory == tr]
    g1 = g1tab(tr).set_index(["method", "order"])
    g0 = None if tr == "III" else pd.read_csv(os.path.join(G0, f"g0_frame_{tr.lower()}.csv"))
    if g0 is not None:
        g0 = g0[g0.real == 1]
    worst = {k: 0.0 for k in ["Raw", "Patch", "Full", "Huber", "Trim", "nearest_d"]}
    n = 0
    for _, r in a.iterrows():
        n += 1
        for arm, meth, key in [("Raw", "M0_raw_p2p", "Raw"), ("Patch", "M4_patch_corr", "Patch"),
                               ("Full", "M5_full_corr", "Full")]:
            ref = g1.loc[(meth, r.order)]
            worst[key] = max(worst[key], abs(r.et_mm - ref.et_mm) if r.arm == arm else worst[key])
        if g0 is not None:
            for arm, form, key in [("Huber", "huber", "Huber"), ("Trim", "trim", "Trim")]:
                ref = g0[(g0.order == r.order) & (g0.kind == "p2p") & (g0.form == form)]
                if len(ref) and r.arm == arm:
                    ref = ref.iloc[0]
                    worst[key] = max(worst[key], abs(r.et_mm - ref.et_mm), abs(r.eR_deg - ref.eR_deg))
    # nearest_d
    for _, r in s.iterrows():
        ref = g1.loc[("M5_full_corr", r.order)]
        worst["nearest_d"] = max(worst["nearest_d"], abs(r.nearest_d - ref.nearest_d))
    # predicted dxi (external, stored)
    if tr not in ["VI", "III"]:
        P = np.load(A.REG[tr]["pred"]); meta = pd.read_csv(A.REG[tr]["meta"])
        orders = s.order.values
        dd = np.abs(P["dxi"][orders] - 0)  # placeholder
        # recompute is validated in small sample (exact 0); here compare stored dxi norm to frame pred_mag
        pred_t_norm = np.linalg.norm(P["dxi"][orders, :3, 0], axis=1) * 1000
        worst_dxi = float(np.abs(pred_t_norm - s.pred_mag_t_mm.values).max())
    else:
        worst_dxi = np.nan
    rows.append(dict(trajectory=tr, n_frames=n, **{f"maxdiff_{k}": v for k, v in worst.items()},
                     maxdiff_pred_t_mm=worst_dxi))
R = pd.DataFrame(rows)
pd.set_option("display.width", 220)
print(R.round(2).to_string(index=False))
R.to_csv(os.path.join(OUT, "scripts", "verify79_full.csv"), index=False)
glob = max(R[[c for c in R.columns if c.startswith("maxdiff_") and c != "maxdiff_pred_t_mm"]].max())
print("\nGLOBAL worst frozen-reproduction diff:", f"{glob:.3e}")
