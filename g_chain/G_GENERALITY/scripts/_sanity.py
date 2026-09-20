# -*- coding: utf-8 -*-
import numpy as np, g_generality_run as GX
GX._init()
def get(rows, form, kind="p2p"):
    return [r for r in rows if r["kind"] == kind and r["form"] == form][0]
cases = [("D1_appendage_disp", 25, "mm"), ("D2_missing_component", 1.0, "f"),
         ("D3_local_surface_off", 25, "mm"), ("D4_appendage_scale", .05, "f"),
         ("D5_appendage_tilt", 1.0, "deg")]
for geom in GX.GEOMS:
    # self null
    r0 = GX._one((geom, "D1_appendage_disp", 0, "mm", 0)); l0 = get(r0, "ls")
    print(geom, "selfnull et=%.4f nobs=%d" % (l0["et_mm"], l0["n_obs"]))
    for dt, mg, u in cases:
        rows = GX._one((geom, dt, mg, u, 0)); ls, hu = get(rows, "ls"), get(rows, "huber")
        print("   %-22s mag=%-4s LS et=%7.3f eR=%6.4f grad=%.2e | Hub et=%7.3f"
              % (dt, mg, ls["et_mm"], ls["eR_deg"], ls["grad_gt"], hu["et_mm"]))
    cn = GX._one_noise((geom, 25, 0)); cl = get(cn, "ls")
    print("   CTRL-noise25 et=%.3f" % cl["et_mm"])
