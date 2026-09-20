# -*- coding: utf-8 -*-
import numpy as np
from scipy.spatial import cKDTree
import g_generality_run as GX
GX._init()
geom = "GA"; d = GX._G[geom]; M, Nm, comp, spec = d["M"], d["Nm"], d["comp"], d["spec"]
for f in [.5, .75, .9, 1.0]:
    ets = []
    for rep in range(6):
        Ptrue, Ntrue, mk = GX.apply_discrepancy(M, Nm, comp, spec, "D2_missing_component", f)
        Mreg = M[mk]; tree = cKDTree(Mreg)
        vant = spec["vants"][rep % 3]
        rng = np.random.default_rng(123 + rep)
        P = GX._observe(Ptrue, Ntrue, vant, rng)
        r = GX.G.robust_icp(Mreg, Nm[mk], tree, P, "p2p", "ls", s_floor=d["sfloor"])
        ets.append(np.linalg.norm(r["xi"][:3]) * 1000)
    print("f=%.2f CAD_keep=%.3f n_scan~%d  LS et mm=%s" %
          (f, mk.mean(), int(P.shape[0]), np.round(ets, 2)))
