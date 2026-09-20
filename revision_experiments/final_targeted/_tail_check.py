# -*- coding: utf-8 -*-
"""Tail audit of initialization degradation dinit by method/level (is any large degradation Patch-specific?)."""
import pandas as pd, numpy as np
import ft_common as F
df = pd.read_csv(F.OUT + r"\initialization_sensitivity_framewise.csv")
p = df[df.perturbation_level.isin(["L1", "L2", "L3"])].copy()
print("delta_init_t_mm quantiles by method:")
for m, g in p.groupby("method"):
    q = np.percentile(g.delta_init_t_mm.abs(), [50, 90, 95, 99, 100])
    n5 = int((g.delta_init_t_mm.abs() > 5).sum()); n20 = int((g.delta_init_t_mm.abs() > 20).sum())
    print(f"  {m:11s} |dinit_t| p50/p90/p95/p99/max = {np.round(q,3)}  |>5mm|={n5}  |>20mm|={n20} (of {len(g)})")
print("\nrows with |dinit_t|>20mm:")
cols = ["trajectory","frame_id","method","perturbation_level","direction_id",
        "ref_translation_error_mm","final_translation_error_mm","delta_init_t_mm",
        "hit_translation_boundary","hit_rotation_boundary","termination_reason"]
print(p[p.delta_init_t_mm.abs() > 20][cols].round(2).to_string(index=False))
print("\n|dinit_t|>5mm counts by method x level:")
print(p.assign(big=p.delta_init_t_mm.abs()>5).groupby(["method","perturbation_level"]).big.sum().to_string())
