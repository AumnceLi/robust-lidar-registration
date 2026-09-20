# -*- coding: utf-8 -*-
"""debug_baseline.py -- diagnose FPFH correspondence quality under GT (analysis only)."""
import os, numpy as np
from scipy.spatial import cKDTree
import s0_common as C

def prep():
    mc=np.load(os.path.join(C.CACHE,"model_cache.npz"))
    model=mc["xyz"].astype(np.float64); nrm=mc["normals"].astype(np.float64)
    md,mn=C.voxel_downsample(model,0.05,nrm)
    tt=cKDTree(md); mn=C.pca_normals(md,tt,16); tf=C.fpfh(md,mn,tt,0.15)
    return md,mn,tf

i=250
md,mn,tf=prep()
pc=C.load_xyz(C.f3d(i)); ts,t,q=C.load_pose(i); R=C.quat_to_R(q)
sd=C.voxel_downsample(pc,0.05); st=cKDTree(sd); sn=C.pca_normals(sd,st,16); sf=C.fpfh(sd,sn,st,0.15)
print("down sizes",len(md),len(sd))
# GT-transformed target in lidar frame
tg=(R@md.T).T+t
d_sp,_=cKDTree(sd).query(tg)
print("GT target->scan nearest dist: med %.3f p90 %.3f"%(np.median(d_sp),np.percentile(d_sp,90)))
# feature matches target->scan
ft=cKDTree(sf); dd,mi=ft.query(tf,k=1)
dm=np.linalg.norm(tg-sd[mi],axis=1)
for thr in (0.05,0.1,0.2):
    print(f"FPFH match geometrically consistent <{thr}m: {(dm<thr).mean():.3f}")
# normal consistency at spatially nearest points
_,ni=st.query(tg)
dots=( (R@mn.T).T * sn[ni]).sum(1)
print("normal dot GT-aligned: med %.3f frac>0.7 %.3f frac<-0.7 %.3f"%(np.median(dots),(dots>0.7).mean(),(dots<-0.7).mean()))
# what does a correct 3-point solve look like: pick spatially-consistent feature matches
good=dm<0.1
print("good corr count",good.sum())
rng=np.random.default_rng(0)
# inlier ratio among ALL unique feature matches
_,uniq=np.unique(mi,return_index=True)
print("unique matches",len(uniq),"of which good",good[uniq].sum(),"ratio",good[uniq].mean())
