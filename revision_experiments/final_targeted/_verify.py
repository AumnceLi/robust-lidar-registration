# -*- coding: utf-8 -*-
"""Final pre-delivery verification of every required artifact and internal consistency."""
import os, json
import pandas as pd, numpy as np
import ft_common as F
O = F.OUT
need = ["patch_vs_global_framewise.csv","patch_vs_global_blocks.csv","patch_vs_global_summary.csv",
        "patch_vs_global_decision.md","patchhuber_direct_framewise.csv","patchhuber_direct_blocks.csv",
        "patchhuber_direct_summary.csv","fig_patchhuber_direct_increment.png","patchhuber_direct_decision.md",
        "initialization_frames.json","initialization_sensitivity_framewise.csv",
        "initialization_sensitivity_summary.csv","initialization_sensitivity_boundaries.csv",
        "fig_initialization_sensitivity.png","fig_initialization_boundaries.png",
        "initialization_sensitivity_decision.md","FINAL_TARGETED_EXPERIMENTS_DECISION.md"]
print("== required files ==")
for f in need:
    p = os.path.join(O, f); print(f"  [{'OK' if os.path.exists(p) else 'MISSING'}] {f}  {os.path.getsize(p) if os.path.exists(p) else 0}")

print("\n== Task1 ==")
s1 = pd.read_csv(O+r"\patch_vs_global_summary.csv").set_index("trajectory")
assert s1.loc[["VI","IV","II","III"],"n_blocks"].tolist() == [6,4,9,8]
f1 = pd.read_csv(O+r"\patch_vs_global_framewise.csv")
assert len(f1)==501+156+428+371 and f1.d_t_mm.notna().all()
# direct pairing identity: d_t == global - patch
assert np.allclose(f1.d_t_mm, f1.globalvec_et_mm - f1.patch_et_mm)
print("  frame rows", len(f1), "blocks 6/4/9/8 OK; d_t identity OK; II med", round(s1.loc['II','paired_d_t_med'],3))

print("\n== Task2 ==")
s2 = pd.read_csv(O+r"\patchhuber_direct_summary.csv").set_index("trajectory")
assert s2.loc[["VI","IV","II","III"],"primary_n_blocks"].tolist()==[6,4,9,8]
f2 = pd.read_csv(O+r"\patchhuber_direct_framewise.csv")
assert set(f2.comparison)=={"PH_vs_Huber","PH_vs_Patch"}
assert len(f2)==2*(501+156+428+371)
assert np.allclose(f2.Dt_mm, f2.et_target-f2.et_base)
# quadrant fractions sum to 1 for primary
for t in F.TRAJS:
    q=[s2.loc[t,f"primary_PH_Huber_quad_{q}_frac"] for q in
       ["tbetter_rbetter","tbetter_rworse","tworse_rbetter","tworse_rworse"]]
    assert abs(sum(q)-1)<1e-9,(t,q)
print("  frame rows",len(f2),"blocks 6/4/9/8 OK; Dt identity OK; quadrants sum=1 OK")

print("\n== Task3 ==")
f3 = pd.read_csv(O+r"\initialization_sensitivity_framewise.csv")
req3=["trajectory","frame_id","method","perturbation_level","direction_id","translation_init_mm",
      "rotation_init_deg","final_translation_error_mm","final_rotation_error_deg","iterations",
      "termination_reason","hit_iteration_cap","hit_translation_boundary","hit_rotation_boundary",
      "final_objective","delta_init_t_mm","delta_init_r_deg"]
miss=[c for c in req3 if c not in f3.columns]; assert not miss, miss
pert=f3[f3.perturbation_level.isin(["L1","L2","L3"])]; ref=f3[f3.perturbation_level=="reference"]
assert len(pert)==3840 and len(ref)==320, (len(pert),len(ref))
# 80 frames x 3 lv x 4 dir x 4 methods ; every cell has all 4 methods
g=pert.groupby(["trajectory","frame_id","perturbation_level","direction_id"]).method.nunique()
assert (g==4).all()
assert set(pert.method)=={"Raw","Huber","Patch","PatchHuber"}
assert pert.final_translation_error_mm.notna().all() and pert.final_rotation_error_deg.notna().all()
# objective may be NaN only when the FIRST Kabsch step already clips the basin (frozen robust_icp Jlast=NaN)
objnan = pert[pert.final_objective.isna()]
assert (objnan.iterations.eq(1) & objnan.termination_reason.eq("boundary")).all()
print("  (first-iteration basin clips with frozen NaN objective:", len(objnan),
      "frames:", sorted(set(zip(objnan.trajectory,objnan.frame_id))), ")")
# reference delta exactly 0
assert (ref.delta_init_t_mm.abs()<1e-12).all() and (ref.delta_init_r_deg.abs()<1e-12).all()
s3=pd.read_csv(O+r"\initialization_sensitivity_summary.csv")
assert len(s3)==4*3
b3=pd.read_csv(O+r"\initialization_sensitivity_boundaries.csv")
assert len(b3)==4*3*4
sel=json.load(open(O+r"\initialization_frames.json")); assert sel["n_unique_frames"]==80
print("  framewise rows",len(f3),"(pert 3840 / ref 320); all 4 methods/cell; columns complete; summary 12 rows; boundaries 48 rows; frames=80 OK")
print("\nALL VERIFICATION CHECKS PASSED")
