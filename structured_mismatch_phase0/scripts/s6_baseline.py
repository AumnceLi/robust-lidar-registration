# -*- coding: utf-8 -*-
"""
s6_baseline.py -- Stage 6: FROZEN classical baseline FPFH + RANSAC + point-to-point ICP.

open3d has no wheel for Python 3.14 on this machine, so FPFH (Rusu et al. 2009),
3-point RANSAC global registration and point-to-point ICP are re-implemented in
numpy/scipy in s0_common.py, following the same algorithm semantics. Parameters
are FROZEN for every scan (no tuning, GT never enters init/features/filtering):
  voxel 0.05 m | FPFH radius 0.15 m | RANSAC max_iter 4e6, max_validation 500,
  confidence 0.999, dist 0.10 m | ICP 30 iters point-to-point, dist 0.10 m
Converged := RANSAC fitness>0.3 AND ICP fitness>0.5.
GT is used ONLY to score the endpoint (translation + symmetry-aware attitude).

Usage: python s6_baseline.py pilot | python s6_baseline.py all
"""
import os, sys, time
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
import s0_common as C

VOXEL=0.05; FPFH_R=0.15
RANSAC_D=0.10; ICP_D=0.10

def prep_target():
    mc=np.load(os.path.join(C.CACHE,"model_cache.npz"))
    model=mc["xyz"].astype(np.float64); nrm=mc["normals"].astype(np.float64)
    md,mn=C.voxel_downsample(model,VOXEL,nrm)
    ttree=cKDTree(md)
    mn=C.pca_normals(md,ttree,k=16)
    tfeat=C.fpfh(md,mn,ttree,FPFH_R)
    return md,tfeat

def run_one(i, md, tfeat, rng):
    t0=time.perf_counter()
    pc=C.load_xyz(C.f3d(i)); ts,t_gt,q_gt=C.load_pose(i)
    R_gt=C.quat_to_R(q_gt)
    sd=C.voxel_downsample(pc,VOXEL)
    stree=cKDTree(sd); sn=C.pca_normals(sd,stree,k=16)
    sfeat=C.fpfh(sd,sn,stree,FPFH_R)
    # global: src=target(target frame) -> dst=scan(lidar frame)
    Rr,tr,rf,rinl,it_used,n_corr=C.ransac_global(md,sd,tfeat,sfeat,rng,
                                             dist_thresh=RANSAC_D)
    Ri,ti,icf,icin,rmse=C.icp_point2point(md,sd,cKDTree(sd),Rr,tr,
                                          dist_thresh=ICP_D,max_iter=30)
    terr=float(np.linalg.norm(ti-t_gt))
    att,k_sym,Rerr=C.sym_aware_attitude_err(Ri,R_gt)
    # signed translation error expressed in TARGET frame (for bias analysis)
    dvec_l=ti-t_gt
    dvec_t=R_gt.T@dvec_l
    ax=C.rot_axis(Rerr)
    conv=bool(rf>0.3 and icf>0.5)
    dt=time.perf_counter()-t0
    return dict(scan_id=i,range_m=float(np.linalg.norm(t_gt)),
        point_count=len(pc),down_count=len(sd),converged=int(conv),
        ransac_fitness=rf,icp_fitness=icf,ransac_iters=it_used,n_corr=n_corr,
        translation_error_m=terr,attitude_error_deg=att,
        terr_vec_target_x=dvec_t[0],terr_vec_target_y=dvec_t[1],terr_vec_target_z=dvec_t[2],
        rot_err_axis_x=ax[0],rot_err_axis_y=ax[1],rot_err_axis_z=ax[2],
        symmetry_equivalent_rotation_k=k_sym,runtime_s=dt,icp_rmse=rmse)

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else "pilot"
    md,tfeat=prep_target()
    print(f"[target] downsampled to {len(md)} pts")
    # GT angular-rate proxy (analysis covariate only; never seen by baseline)
    Rall=[C.quat_to_R(C.load_pose(i)[2]) for i in range(501)]
    tsall=[C.load_pose(i)[0] for i in range(501)]
    def angrate(i):
        j=min(i+1,500); dt=max(tsall[j]-tsall[i],1e-9)
        return C.geodesic_deg(Rall[i],Rall[j])/dt
    rng=np.random.default_rng(C.RNG_SEED)
    if mode=="pilot":   ids=[0,125,250,375,500]
    elif mode=="sample": ids=list(range(0,501,5))     # stratified every 5th scan, n=101
    else:               ids=C.scan_ids()
    rows=[]; t0=time.perf_counter()
    for n,i in enumerate(ids):
        r=run_one(i,md,tfeat,rng); r["angular_rate_deg_s"]=angrate(i); rows.append(r)
        print(f"scan {i:04d} conv={r['converged']} rf={r['ransac_fitness']:.3f} "
              f"icf={r['icp_fitness']:.3f} tErr={r['translation_error_m']:.3f}m "
              f"aErr={r['attitude_error_deg']:.2f}deg iters={r['ransac_iters']} "
              f"rt={r['runtime_s']:.1f}s")
        if mode=="all" and n%25==0:
            pd.DataFrame(rows).to_csv(os.path.join(C.RESULTS,"baseline_endpoints.csv"),index=False)
    df=pd.DataFrame(rows)
    out={"pilot":"baseline_endpoints_pilot.csv","sample":"baseline_endpoints.csv",
         "all":"baseline_endpoints.csv"}[mode]
    df.to_csv(os.path.join(C.RESULTS,out),index=False)
    print(f"[done {mode}] {len(df)} scans, total {time.perf_counter()-t0:.1f}s "
          f"mean/scan {df.runtime_s.mean():.2f}s; converge {df.converged.mean():.3f}")

if __name__=="__main__":
    main()
