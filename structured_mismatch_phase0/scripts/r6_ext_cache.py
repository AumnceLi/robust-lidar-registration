# -*- coding: utf-8 -*-
"""r6_ext_cache.py -- build GT-aligned caches for IV/V with the FROZEN model + 24 patches.
Observed clouds are used for P1/P2 (the quantity being predicted) and for SECONDARY P4.
No re-clustering: scan patch = frozen model patch label of NN model point."""
import os,time,glob,sys
import numpy as np,pandas as pd
from scipy.spatial import cKDTree
import s0_common as C, m_common as M

mc=np.load(os.path.join(M.CACHE,"model_cache.npz"))
MODEL=mc["xyz"].astype(np.float64); NM=mc["normals"].astype(np.float64)
PLAB=np.load(os.path.join(M.CACHE,"patches.npz"))["lab"]
TREE=cKDTree(MODEL)
OUTROOT=os.path.join(M.CACHE,"ext"); os.makedirs(OUTROOT,exist_ok=True)
DATA=os.path.join(C.SCRIPTS,"ivv_data")

def traj(tag):
    d=os.path.join(DATA,f"epos_dataset_{tag}")
    ids=sorted(int(os.path.basename(f)[:4]) for f in glob.glob(os.path.join(d,"*.3d")))
    return d,ids

def load_pose_generic(d,i):
    with open(os.path.join(d,f"{i:04d}.pose")) as fh:
        L=[ln.strip() for ln in fh if ln.strip()]
    ts=float(L[0]); t=np.array(L[1].split(),float); q=np.array(L[2].split(),float)
    return ts,t,q

def build(tag):
    d,ids=traj(tag); od=os.path.join(OUTROOT,tag); os.makedirs(od,exist_ok=True)
    rows=[]; t0=time.perf_counter()
    for k,i in enumerate(ids):
        pc=np.loadtxt(os.path.join(d,f"{i:04d}.3d"))
        ts,t,q=load_pose_generic(d,i); R=C.quat_to_R(q)
        aligned=((R.T)@(pc-t).T).T
        dd,nn=TREE.query(aligned,k=1,workers=-1)
        signed=((aligned-MODEL[nn])*NM[nn]).sum(1)
        patch=PLAB[nn]
        o=-R.T@t; rng=np.linalg.norm(o); u=o/rng
        np.savez_compressed(os.path.join(od,f"scan_{i:04d}.npz"),
                            aligned=aligned.astype(np.float32),nnidx=nn.astype(np.int32),
                            patch=patch.astype(np.int16),signed=signed.astype(np.float32),
                            d=dd.astype(np.float32))
        rows.append(dict(scan=i,range_m=rng,n=len(pc),ux=u[0],uy=u[1],uz=u[2],ts=ts))
        if (k+1)%250==0: print(f"[{tag}] {k+1}/{len(ids)} {time.perf_counter()-t0:.0f}s",flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUTROOT,f"meta_{tag}.csv"),index=False)
    print(f"[{tag}] done n={len(ids)}",flush=True)

if __name__=="__main__":
    for tag in (sys.argv[1:] or ["iv","v"]):
        build(tag)
