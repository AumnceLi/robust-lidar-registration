# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
pd.set_option("display.width", 250)
P = pd.read_csv("../followup8_equal_rms_pairs.csv")
C = pd.read_csv("../followup8_condition_summary.csv")
print("5% pairs:", len(P), "by geometry:", P.geometry.value_counts().to_dict())
# cross-family (exclude CTRL as either side for the 'spatial organization' core, but report both)
P["pairfam"] = ["-".join(sorted([a, b])) for a, b in zip(P.familyA, P.familyB)]
print("\npair family composition:\n", P.pairfam.value_counts().to_string())
# how often does equal-RMS give >2x / >5x bias difference?
for label, q in [("all pairs", P), ("structured-structured", P[(P.familyA!="CTRL")&(P.familyB!="CTRL")])]:
    print(f"\n[{label}] N={len(q)}: median bias_ratio={q.bias_ratio.median():.2f}  "
          f">2x: {(q.bias_ratio>2).mean():.2f}  >5x: {(q.bias_ratio>5).mean():.2f}  "
          f"median |bias_diff|={q.bias_diff.median():.3f} mm; median rms_diff={P.rms_diff.median():.3f}")
# named family contrasts requested by user
for key in [("D1","D2"),("D1","D4"),("D2","D4"),("D3","D5"),("D3","D4"),("D1","D3")]:
    q = P[P.pairfam == "-".join(sorted(key))]
    if len(q):
        print(f"  {key}: n={len(q)} median bias_ratio={q.bias_ratio.median():.2f} "
              f"max={q.bias_ratio.max():.1f}; >2x frac={(q.bias_ratio>2).mean():.2f}")
# D4 specifically: side with larger RMS-matched bias
d4 = P[(P.familyA=="D4")|(P.familyB=="D4")].copy()
d4["d4_is_low"] = np.where(d4.familyA=="D4", d4.etA < d4.etB, d4.etB < d4.etA)
print(f"\nD4 matched pairs n={len(d4)}; D4 is the LOWER-bias side in {d4.d4_is_low.mean():.2f}; "
      f"median other/D4 bias ratio={d4.bias_ratio.median():.2f}")
# CTRL (unstructured) matched to structured: structured usually more biased at equal RMS?
ct = P[(P.familyA=="CTRL")|(P.familyB=="CTRL")].copy()
ct["struct_high"] = np.where(ct.familyA=="CTRL", ct.etB>ct.etA, ct.etA>ct.etB)
print(f"CTRL pairs n={len(ct)}; structured side higher-bias fraction={ct.struct_high.mean():.2f}, median ratio={ct.bias_ratio.median():.2f}")
# eta / gradient contrast: higher-bias side also higher gt / eta_t?
P["hi"] = np.where(P.etA>=P.etB,"A","B")
P["gt_hi"]=np.where(P.gtA>=P.gtB,"A","B"); P["pjw_hi"]=np.where(P.pjwA>=P.pjwB,"A","B")
print("sign-agree higher-bias side = higher ||g_t||:", (P.hi==P.gt_hi).mean().round(3),
      " = higher PJW:", (P.hi==P.pjw_hi).mean().round(3))
