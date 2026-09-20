# -*- coding: utf-8 -*-
"""
s1_residuals.py -- Stage 1 (GT-aligned residuals) + Stage 2 (R1-R4 separation).

GT ONLY used here to align scans and to define visibility; no baseline sees it.
Outputs:
  results/residual_per_scan.csv
  cache/model_cache.npz            (target xyz, normals, self-NN, dnn)
  cache/scans/scan_XXXX.npz        (aligned xyz, residual, signed, nn model idx, label)
"""
import os, time
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.cluster import DBSCAN
import s0_common as C

FOV_HALF_DEG = 19.2          # Livox Mid-40 circular FOV 38.4 deg -> half 19.2
OPT_AXIS = np.array([1.,0.,0.])   # data-driven: scan 0000 centroid lies on +X (verified at runtime)
EXCESS_M = 0.5
COVER_M  = 0.05              # missing-proxy neighbourhood radius
R4_EPS   = 0.10; R4_MINPTS  = 5

def main():
    t00=time.perf_counter()
    ids = C.scan_ids()
    model = C.load_xyz(C.TARGET)
    print(f"[model] N={len(model)}  extent x[{model[:,0].min():.3f},{model[:,0].max():.3f}] "
          f"y[{model[:,1].min():.3f},{model[:,1].max():.3f}] z[{model[:,2].min():.3f},{model[:,2].max():.3f}]")

    # ---- model self NN baseline (R1 null scale) + PCA normals
    mt = cKDTree(model)
    dnn2,_ = mt.query(model, k=2)
    dnn_each = dnn2[:,1]
    d_model_nn = float(np.median(dnn_each))
    print(f"[model] self-NN median={d_model_nn*1000:.2f} mm  mean={dnn_each.mean()*1000:.2f} mm "
          f"p90={np.percentile(dnn_each,90)*1000:.2f} mm")
    n_model = C.pca_normals(model, mt, k=16)
    np.savez_compressed(os.path.join(C.CACHE,"model_cache.npz"),
                        xyz=model.astype(np.float32), normals=n_model.astype(np.float32),
                        nn=dnn_each.astype(np.float32), dnn=np.float64(d_model_nn))
    r1_thresh = 2.0*d_model_nn
    os.makedirs(os.path.join(C.CACHE,"scans"),exist_ok=True)

    # ---- runtime check of optical axis on scan 0000
    p0 = C.load_xyz(C.f3d(0)); ts0,t0,q0 = C.load_pose(0)
    cdir = p0.mean(0)/np.linalg.norm(p0.mean(0))
    print(f"[axis] scan0000 centroid dir={cdir.round(3)}  |t|={np.linalg.norm(t0):.4f} m  "
          f"=> optical axis +X confirmed: {abs(cdir[0])>0.99}")

    rows=[]; prev_ts=None
    for i in ids:
        pc = C.load_xyz(C.f3d(i)); ts,t,q = C.load_pose(i)
        R = C.quat_to_R(q)
        aligned = ((R.T)@(pc - t).T).T                      # GT align -> target frame
        d, j = mt.query(aligned, k=1)                        # unsigned residual
        signed = ((aligned-model[j])*n_model[j]).sum(1)      # along model normal
        rng = float(np.linalg.norm(t))

        # model visibility in this pose
        pl = (R@model.T).T + t
        nl = (R@n_model.T).T
        view = pl/np.maximum(np.linalg.norm(pl,axis=1,keepdims=True),1e-12)
        backface = (nl*view).sum(1) > 0                      # normal points away from lidar
        cosfov = (view*OPT_AXIS).sum(1)
        outfov  = np.degrees(np.arccos(np.clip(cosfov,-1,1))) > FOV_HALF_DEG
        visible = (~backface)&(~outfov)
        # missing proxy: visible model surface with no aligned scan point within COVER_M
        st = cKDTree(aligned)
        dv,_ = st.query(model[visible], k=1, distance_upper_bound=COVER_M)
        missing = float(np.mean(~np.isfinite(dv)))
        fov_frac = float(np.mean(outfov)); back_frac = float(np.mean(backface))

        # ---- R1-R4 operational labels
        lab = np.full(len(aligned), -1, np.int8)            # -1 unassigned
        r1 = d <= r1_thresh
        lab[r1] = 1
        cand_r2 = (~r1) & backface[j];  lab[cand_r2]=2
        cand_r3 = (~r1)&(lab!=2)&outfov[j]; lab[cand_r3]=3
        r4_pool = (~r1)&(lab==-1)                            # large residual, front+in-FOV
        lab[r4_pool] = 0                                     # 0 = large-residual unclustered noise
        if r4_pool.sum() >= R4_MINPTS:
            db = DBSCAN(eps=R4_EPS, min_samples=R4_MINPTS, n_jobs=-1).fit(aligned[r4_pool])
            cl = db.labels_
            idx_pool = np.where(r4_pool)[0]
            clustered = cl != -1
            lab[idx_pool[clustered]] = 4                     # R4 structured candidate
        n4 = int((lab==4).sum()); nnoise=int((lab==0).sum())

        dt = 0.0 if prev_ts is None else ts-prev_ts; prev_ts=ts
        exc = d > EXCESS_M
        rows.append(dict(
            scan_id=i, timestamp=ts, range_m=rng, point_count=len(pc),
            median_residual_m=np.median(d), p90_residual_m=np.percentile(d,90),
            p95_residual_m=np.percentile(d,95), max_residual_m=d.max(),
            mean_residual_m=d.mean(), std_residual_m=d.std(ddof=1),
            excess_return_count=int(exc.sum()), excess_return_fraction=exc.mean(),
            missing_proxy=missing, dt_seconds=dt,
            r1_frac=(lab==1).mean(), r2_backface_frac=(lab==2).mean(),
            r3_fov_frac=(lab==3).mean(),
            r4_structured_frac=(lab==4).mean(),
            large_noise_frac=(lab==0).mean(),
            model_backface_frac=back_frac, model_fov_trunc_frac=fov_frac,
            model_visible_frac=visible.mean(),
            r4_point_count=n4, large_noise_count=nnoise,
            mean_signed_residual=signed.mean()))
        np.savez_compressed(os.path.join(C.CACHE,"scans",f"scan_{i:04d}.npz"),
                            aligned=aligned.astype(np.float32), r=d.astype(np.float32),
                            signed=signed.astype(np.float32), nnidx=j.astype(np.int32),
                            lab=lab)
        if i%50==0: print(f"  scan {i:04d} range={rng:6.3f} n={len(pc)} "
                          f"med={np.median(d)*1000:6.1f}mm p95={np.percentile(d,95)*1000:6.1f}mm "
                          f"R4={n4} miss={missing:.3f} t={time.perf_counter()-t00:.0f}s")
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(C.RESULTS,"residual_per_scan.csv"), index=False)
    print(f"[done] {time.perf_counter()-t00:.1f}s  rows={len(df)}")
    print(df[["range_m","point_count","median_residual_m","p95_residual_m",
              "excess_return_fraction","r4_structured_frac","missing_proxy"]].describe().round(4))

if __name__=="__main__":
    main()
