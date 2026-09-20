# -*- coding: utf-8 -*-
"""
s3_patches.py -- Stage 3: define coarse surface patches ONCE on the target model
(frozen thereafter), assign every GT-aligned scan point via its nearest model
point, and aggregate per-scan x patch statistics.

Frozen definition: MiniBatchKMeans k=24 on [xyz(metres), 0.3*normal], seed=42.
Saved to cache/patches.npz + results/patch_definition.csv (never re-fit later).
"""
import os, time
import numpy as np, pandas as pd
from sklearn.cluster import MiniBatchKMeans
import s0_common as C

K_PATCH = 24
NORM_W  = 0.3

def build_or_load_patches(model, n_model):
    p = os.path.join(C.CACHE,"patches.npz")
    if os.path.exists(p):
        z=np.load(p); return z["lab"], z["center"], z["normal"]
    feat = np.concatenate([model, NORM_W*n_model],axis=1)
    km = MiniBatchKMeans(n_clusters=K_PATCH, random_state=C.RNG_SEED, n_init=20,
                         batch_size=4096).fit(feat)
    lab = km.labels_
    center = np.zeros((K_PATCH,3)); normal=np.zeros((K_PATCH,3)); cnt=np.zeros(K_PATCH)
    for k in range(K_PATCH):
        m = lab==k; center[k]=model[m].mean(0)
        nv = n_model[m].mean(0); normal[k]=nv/np.linalg.norm(nv); cnt[k]=m.sum()
    np.savez_compressed(p, lab=lab.astype(np.int16), center=center, normal=normal, count=cnt)
    pd.DataFrame(dict(patch_id=np.arange(K_PATCH),
                      patch_center_x=center[:,0],patch_center_y=center[:,1],patch_center_z=center[:,2],
                      patch_normal_x=normal[:,0],patch_normal_y=normal[:,1],patch_normal_z=normal[:,2],
                      model_point_count=cnt.astype(int))).to_csv(
        os.path.join(C.RESULTS,"patch_definition.csv"),index=False)
    print(f"[patch] frozen k={K_PATCH}, model points/patch min={cnt.min():.0f} max={cnt.max():.0f}")
    return lab, center, normal

def main():
    t0=time.perf_counter()
    mc=np.load(os.path.join(C.CACHE,"model_cache.npz"))
    model=mc["xyz"].astype(np.float64); n_model=mc["normals"].astype(np.float64)
    plab, center, normal = build_or_load_patches(model, n_model)
    per = pd.read_csv(os.path.join(C.RESULTS,"residual_per_scan.csv"))
    rows=[]
    for i in C.scan_ids():
        z=np.load(os.path.join(C.CACHE,"scans",f"scan_{i:04d}.npz"))
        r=z["r"].astype(np.float64); sg=z["signed"].astype(np.float64)
        lab=z["lab"]; pp=plab[z["nnidx"]]
        rng=float(per.loc[per.scan_id==i,"range_m"].iloc[0])
        for k in range(K_PATCH):
            m = pp==k; n=int(m.sum())
            if n==0:
                rows.append(dict(scan_id=i,patch_id=k,patch_center_x=center[k,0],
                    patch_center_y=center[k,1],patch_center_z=center[k,2],support_count=0,
                    median_residual=np.nan,p90_residual=np.nan,mean_signed_residual=np.nan,
                    excess_fraction=np.nan,r4_frac=np.nan,range_m=rng)); continue
            rows.append(dict(scan_id=i,patch_id=k,patch_center_x=center[k,0],
                patch_center_y=center[k,1],patch_center_z=center[k,2],support_count=n,
                median_residual=np.median(r[m]),p90_residual=np.percentile(r[m],90),
                mean_signed_residual=sg[m].mean(),
                excess_fraction=(r[m]>0.5).mean(),r4_frac=(lab[m]==4).mean(),range_m=rng))
        if i%100==0: print(f"  scan {i}  {time.perf_counter()-t0:.0f}s")
    df=pd.DataFrame(rows)
    df.to_csv(os.path.join(C.RESULTS,"patch_persistence.csv"),index=False)
    print(f"[done] {len(df)} rows in {time.perf_counter()-t0:.1f}s")
    print(df.groupby('patch_id').agg(support=('support_count','mean'),
        med=('median_residual','median'),exc=('excess_fraction','mean')).round(4))

if __name__=="__main__":
    main()
