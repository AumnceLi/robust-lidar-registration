# -*- coding: utf-8 -*-
"""
m1_nuisance.py -- Rescue Audit sections 5-6: remove GLOBAL nuisance BEFORE mechanism.

All nuisance params are SHARED across all 501 VI scans (never per-frame):
  N1  b_r   single global range offset along the lidar ray
  N2  dT    single global SE(3) calibration offset (linearized point-to-plane)
  N3  s     single global isotropic CAD scale
  N4  theta_N=(b_r,dT,s) block-coordinate fit (frozen 8-DoF complexity; NO higher-order)

For raw + every correction we recompute the SAME frozen K1 structure diagnostics:
  global signed mean, unsigned median; 24-patch profile spread & worst/best ratio;
  lag-1 cross-scan patch-rank Spearman; similar-aspect (<30deg) Spearman.
Nuisance Gate: structure must survive N4, else STOP_GLOBAL_NUISANCE.
N4-corrected aligned clouds are cached for the downstream objective analysis.
"""
import os, time, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
import s0_common as C
import m_common as M

rng=np.random.default_rng(C.RNG_SEED)
mc=np.load(os.path.join(C.CACHE,"model_cache.npz"))
MODEL=mc["xyz"].astype(np.float64); NM=mc["normals"].astype(np.float64)
pz=np.load(os.path.join(C.CACHE,"patches.npz")); PLAB=pz["lab"]
TREE=cKDTree(MODEL)
CORRDIR=os.path.join(M.RESCACHE,"corr"); os.makedirs(CORRDIR,exist_ok=True)
FIT_PER_SCAN=600   # pooled fitting subsample (~300k), diagnostics use ALL points

# --------------------------------------------------------------- frozen K1 diagnostics
def patch_lower_median(pp,r,k=24,supp=20):
    order=np.lexsort((r,pp)); ps=pp[order]; rs=r[order]
    cnt=np.bincount(ps,minlength=k); csum=np.cumsum(cnt); starts=np.r_[0,csum[:-1]]
    out=np.full(k,np.nan); nz=cnt>0; out[nz]=rs[starts[nz]+(cnt[nz]-1)//2]
    out[cnt<supp]=np.nan; return out

def lag_rank_spearman(Mat,L=1):
    vals=[]
    for i in range(Mat.shape[0]-L):
        a,b=Mat[i],Mat[i+L]; ok=np.isfinite(a)&np.isfinite(b)
        if ok.sum()>=8: vals.append(spearmanr(a[ok],b[ok]).statistic)
    return float(np.nanmean(vals))

def aspect_rank_spearman(Mat,Rs,ranges,mode,nref=60):
    vals=[]; idxs=rng.choice(501,size=min(nref,501),replace=False)
    for ii in idxs:
        ang=np.array([C.geodesic_deg(Rs[ii],Rs[j]) for j in range(501)])
        dr=np.abs(ranges-ranges[ii])
        cand=np.where(((ang<30) if mode=="sim" else (ang>90)) & (dr<1.0))[0]
        cand=cand[cand!=ii]
        for j in cand[:8]:
            a,b=Mat[ii],Mat[j]; ok=np.isfinite(a)&np.isfinite(b)
            if ok.sum()>=8: vals.append(spearmanr(a[ok],b[ok]).statistic)
    return float(np.nanmean(vals)),len(vals)

def load_raw(i):
    z=M.load_scan(i); P=z["aligned"].astype(np.float64); nn=z["nnidx"]
    d=M.ray_dirs_target(i,P)
    return P,nn,d

# --------------------------------------------------------------- assemble fit subsample
print("[assemble] pooled fitting subsample + GT rotations ...")
t0=time.perf_counter()
Rs=[]; ranges=pd.read_csv(os.path.join(C.RESULTS,"residual_per_scan.csv")).range_m.values
fitP=[];fitm=[];fitn=[];fitd=[]
for i in C.scan_ids():
    P,nn,d=load_raw(i); Rs.append(C.quat_to_R(C.load_pose(i)[2]))
    sel=rng.choice(len(P),min(FIT_PER_SCAN,len(P)),replace=False)
    fitP.append(P[sel]); fitm.append(MODEL[nn[sel]]); fitn.append(NM[nn[sel]]); fitd.append(d[sel])
fitP=np.vstack(fitP);fitm=np.vstack(fitm);fitn=np.vstack(fitn);fitd=np.vstack(fitd)
print(f"  pooled fit N={len(fitP)} in {time.perf_counter()-t0:.1f}s")

def signed_of(Cc,nn=None):
    if nn is None: _,nn=TREE.query(Cc,k=1,workers=-1)
    return np.einsum("ij,ij->i",Cc-MODEL[nn],NM[nn]),nn

# --------------------------------------------------------------- N1 single range offset
def fit_br(Cc,d,n=None,nn=None):
    s,nn=signed_of(Cc,nn)
    if n is None: n=NM[nn]
    c=np.einsum("ij,ij->i",n,d)
    return float(np.sum(s*c)/np.sum(c*c)),nn
_,nnfit=TREE.query(fitP,k=1,workers=-1)
br_raw=fit_br(fitP,fitd,nn=nnfit)[0]
print(f"[N1] global range offset b_r = {br_raw*1000:+.2f} mm")

# --------------------------------------------------------------- N3 single isotropic scale
def fit_s(Cc,nn):
    m=MODEL[nn]; return float(np.einsum("ij,ij->",Cc,m)/np.einsum("ij,ij->",m,m))
s_raw=fit_s(fitP,nnfit); print(f"[N3] global isotropic scale s = {s_raw:.6f} ({(s_raw-1)*100:+.3f}%)")

# --------------------------------------------------------------- N2 single shared SE(3)
def se3_p2l_steps(Cc,iters=12):
    Racc=np.eye(3); tacc=np.zeros(3)
    for _ in range(iters):
        Q=(Racc@Cc.T).T+tacc
        _,nn=TREE.query(Q,k=1,workers=-1); m=MODEL[nn]; n=NM[nn]
        A=np.concatenate([n,np.cross(Q,n)],axis=1); b=np.einsum("ij,ij->i",n,m-Q)
        delta=np.linalg.lstsq(A.T@A,A.T@b,rcond=None)[0]
        v=delta[:3]; w=delta[3:]; Rd=M.rodrigues(w)
        Racc=Rd@Racc; tacc=Rd@tacc+v
        if np.linalg.norm(delta[:3])<1e-7 and np.linalg.norm(delta[3:])<1e-8: break
    return Racc,tacc
Rse,tse=se3_p2l_steps(fitP)
print(f"[N2] shared SE3: |t|={np.linalg.norm(tse)*1000:.2f} mm  rot={np.degrees(np.linalg.norm(M.rodrigues_log(Rse))):.4f} deg")

# --------------------------------------------------------------- N4 JOINT Gauss-Newton (8 DoF, one LS solve/iter)
# Model observed from nominal:  C ~= m + t + [w]x m + gamma m + b_r d
# ONE 8-parameter least squares per iteration (lstsq handles range/scale/SE3 collinearity);
# record the ordered removal steps and replay them identically on every raw scan.
print("[N4] joint 8-DoF Gauss-Newton ...")
Cw=fitP.copy(); dw_ray=fitd.copy(); steps=[]; hist=[]; conds=[]
for it in range(12):
    _,nn=TREE.query(Cw,k=1,workers=-1); m=MODEL[nn]; n=NM[nn]
    target=np.einsum("ij,ij->i",Cw-m,n)
    A=np.column_stack([n,np.cross(m,n),
                       np.einsum("ij,ij->i",n,m),np.einsum("ij,ij->i",n,dw_ray)])
    conds.append(float(np.linalg.cond(A.T@A)))
    delta,*_=np.linalg.lstsq(A,target,rcond=None)
    dt,dwx,dg,dbr=delta[:3],delta[3:6],float(delta[6]),float(delta[7])
    Rd=M.rodrigues(dwx)
    steps.append((dt.copy(),Rd.copy(),dg,dbr))
    Cw=((Rd.T@(Cw-dt-dbr*dw_ray).T).T)/(1+dg)
    dw_ray=(Rd.T@dw_ray.T).T
    J=float(np.sqrt(np.mean(target**2))); hist.append(J)
    if np.linalg.norm(dt)<1e-7 and np.linalg.norm(dwx)<1e-8 and abs(dg)<1e-6 and abs(dbr)<1e-7: break
# equivalent totals (replayed)
tot_t=np.zeros(3); tot_R=np.eye(3); tot_g=0.0; tot_br=0.0
def replay(x,d):
    for dt,Rd,dg,dbr in steps:
        x=((Rd.T@(x-dt-dbr*d).T).T)/(1+dg)
    return x
# accumulate approximate totals for reporting
Racc=np.eye(3); tacc=np.zeros(3); G=1.0; B=0.0
for dt,Rd,dg,dbr in steps:
    B+=dbr; G*=(1+dg); Racc=Rd.T@Racc; tacc=Rd.T@(tacc-dt)
print(f"[N4] steps={len(steps)} br~{B*1000:+.1f}mm scale~{G:.5f}({(G-1)*100:+.2f}%) "
      f"|t|~{np.linalg.norm(tacc)*1000:.2f}mm rot~{np.degrees(np.linalg.norm(M.rodrigues_log(Racc))):.3f}deg "
      f"rms {hist[0]*1000:.1f}->{hist[-1]*1000:.1f}mm cond(AtA) first/last={conds[0]:.1e}/{conds[-1]:.1e}")

# --------------------------------------------------------------- correction operators on raw cloud
def correct(i,variant):
    P,nn,d=load_raw(i)
    if variant=="raw": Cc=P
    elif variant=="N1_range": Cc=P-br_raw*d
    elif variant=="N3_scale": Cc=P/s_raw
    elif variant=="N2_se3": Cc=(Rse@P.T).T+tse
    elif variant=="N4_combined": Cc=replay(P,d)
    return Cc

# --------------------------------------------------------------- diagnostics over ALL points
def diagnostics(variant,cache_corr=False):
    signed_pool=[]; Mat=np.full((501,24),np.nan); umed=[]
    for i in C.scan_ids():
        Cc=correct(i,variant)
        r,nn=TREE.query(Cc,k=1,workers=-1)
        sgn=np.einsum("ij,ij->i",Cc-MODEL[nn],NM[nn])
        signed_pool.append(sgn); umed.append(np.median(r))
        pp=PLAB[nn]; Mat[i]=patch_lower_median(pp,r)
        if cache_corr and variant in ("N3_scale","N4_combined"):
            sub="scale" if variant=="N3_scale" else "combined"
            d=os.path.join(CORRDIR,sub); os.makedirs(d,exist_ok=True)
            np.savez_compressed(os.path.join(d,f"corr_{i:04d}.npz"),aligned=Cc.astype(np.float32))
    signed_pool=np.concatenate(signed_pool)
    profile=np.nanmedian(Mat,axis=0)
    fin=profile[np.isfinite(profile)]
    lag1=lag_rank_spearman(Mat,1)
    sim,_=aspect_rank_spearman(Mat,Rs,ranges,"sim")
    dif,npair=aspect_rank_spearman(Mat,Rs,ranges,"dif")
    return dict(variant=variant,n_points=int(len(signed_pool)),
        signed_mean_mm=float(signed_pool.mean()*1000),signed_median_mm=float(np.median(signed_pool)*1000),
        unsigned_median_mm=float(np.median(umed)*1000),
        patch_profile_std_mm=float(np.nanstd(fin)*1000),
        patch_profile_min_mm=float(np.nanmin(fin)*1000),patch_profile_max_mm=float(np.nanmax(fin)*1000),
        patch_worst_best_ratio=float(np.nanmax(fin)/np.nanmin(fin)),
        lag1_rank_spearman=lag1,similar_aspect_spearman=sim,different_aspect_spearman=dif,
        aspect_pairs=npair)

variants=["raw","N1_range","N2_se3","N3_scale","N4_combined"]
rows=[]
for v in variants:
    t=time.perf_counter(); dd=diagnostics(v,cache_corr=True); rows.append(dd)
    print(f"[{v}] signed={dd['signed_mean_mm']:+.2f}mm patchStd={dd['patch_profile_std_mm']:.2f}mm "
          f"ratio={dd['patch_worst_best_ratio']:.2f} lag1={dd['lag1_rank_spearman']:.3f} "
          f"simAsp={dd['similar_aspect_spearman']:.3f} ({time.perf_counter()-t:.0f}s)")
df=pd.DataFrame(rows); df.to_csv(os.path.join(M.RESCACHE,"nuisance_diagnostics.csv"),index=False)
np.save(os.path.join(M.RESCACHE,"n4_steps.npy"),np.array(steps,dtype=object),allow_pickle=True)
M.save_json(dict(N1_br_mm=br_raw*1000,N3_s=s_raw,N3_scale_pct=(s_raw-1)*100,
    N2_se3_t_mm=tse*1000,N2_se3_rot_deg=np.degrees(np.linalg.norm(M.rodrigues_log(Rse))),
    N4=dict(br_mm=B*1000,scale=G,scale_pct=(G-1)*100,t_mm=tacc*1000,
            rot_deg=np.degrees(np.linalg.norm(M.rodrigues_log(Racc))),
            rms_first_mm=hist[0]*1000,rms_final_mm=hist[-1]*1000,
            cond_AtA_first=conds[0],cond_AtA_last=conds[-1],n_steps=len(steps)),
    diagnostics=rows),"nuisance_params.json")
print("[saved] nuisance_diagnostics.csv / nuisance_params.json / corr clouds")
