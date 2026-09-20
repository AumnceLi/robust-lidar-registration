# -*- coding: utf-8 -*-
"""gate_anchor.py -- validate the sweep machinery on the FROZEN anchor (24/0.3/42).
The newly run Patch-LS arm must reproduce the existing replay79 Patch arm ~exactly."""
import os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import revx_common as R
from scipy.optimize import linear_sum_assignment


def main():
    t0 = time.perf_counter()
    model, nmodel, sf = R.model_and_normals()
    plab = R.make_partition(24, 0.3, 42, model, nmodel)
    mu, vc = R.vi_view_independent_mu(plab, 24, model)
    lab_f = np.load(R.FROZEN_PATCHES)["lab"].astype(int)
    conf = np.zeros((24, 24), np.int64); np.add.at(conf, (plab, lab_f), 1)
    ri, ci = linear_sum_assignment(-conf); agree = conf[ri, ci].sum() / len(plab)
    fz = R.bundle()
    perm = dict(zip(ri.tolist(), ci.tolist()))
    mu_in_frozen = np.zeros_like(mu)
    for a, b in perm.items():
        mu_in_frozen[b] = mu[a]
    dmu = float(np.abs(mu_in_frozen - fz["mu_patch"]).max())
    print(f"[anchor] partition agreement={agree:.6f}  max|mu-mu_frozen|={dmu:.3e}  min count={vc.min():.0f}")

    target = model + mu[plab]
    new = R.run_arm(target, nmodel, sf, "p2p", "ls", label="anchor-PatchLS")
    old = R.baseline_arm("Patch").rename(columns={"et_mm": "et_old", "eR_deg": "eR_old"})
    m = new.merge(old, on=["trajectory", "order"])
    m["det"] = (m.et_mm - m.et_old).abs(); m["deR"] = (m.eR_deg - m.eR_old).abs()
    print("[anchor] per-frame |d translation| mm  max=%.3e median=%.3e" % (m.det.max(), m.det.median()))
    print("[anchor] per-frame |d rotation| deg    max=%.3e median=%.3e" % (m.deR.max(), m.deR.median()))
    print("[anchor] n frames", len(m), "wall %.1fs" % (time.perf_counter() - t0))
    print(m.groupby("trajectory")[["det", "deR"]].max())


if __name__ == "__main__":
    main()
