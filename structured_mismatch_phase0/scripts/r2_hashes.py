# -*- coding: utf-8 -*-
"""Compute SHA256 + size of frozen artifacts and frozen-protocol scripts."""
import hashlib,os,json
ROOT=os.path.join(os.path.dirname(__file__),os.pardir)
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest(),os.path.getsize(p)
groups={
 "frozen_cache":["scripts/cache/model_cache.npz","scripts/cache/patches.npz",
                 "scripts/cache/patch_matrix.npz","scripts/cache/model_point_resid.npy"],
 "rescue_numeric":["scripts/cache/rescue/nuisance_params.json","scripts/cache/rescue/objective_main.npz",
                   "scripts/cache/rescue/m1_stationarity.json","scripts/cache/rescue/m2_localopt.json",
                   "scripts/cache/rescue/m3_specificity.json","scripts/cache/rescue/m4_direction_patch.json",
                   "scripts/cache/rescue/m7_quadratic.json"],
 "frozen_scripts":["scripts/s0_common.py","scripts/s1_residuals.py","scripts/s3_patches.py",
                   "scripts/m_common.py"],
 "model":["../external_dataset_scout/intermediate/samples/epos_target_model.3d"],
}
out={}
for g,files in groups.items():
    out[g]={}
    for rel in files:
        p=os.path.normpath(os.path.join(ROOT,rel))
        if os.path.exists(p):
            h,n=sha(p); out[g][os.path.basename(rel)]={"sha256":h,"bytes":n}
        else: out[g][os.path.basename(rel)]={"MISSING":p}
print(json.dumps(out,indent=1))
with open(os.path.join(ROOT,"scripts","cache","rescue","frozen_hashes.json"),"w") as f:
    json.dump(out,f,indent=1)
