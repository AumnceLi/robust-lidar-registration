# -*- coding: utf-8 -*-
"""
m2_objective.py -- per-scan registration-objective analysis AT GT for all 501 VI scans.

For conditions {raw, N4-corrected} and objectives {p2p,p2l}, at xi=0 (=GT):
  J0, central-diff gradient g, Hessian H (frozen step), eigen/condition,
  quadratic predictor  dhat=-H^-1 g,
  actual local optimum via (i) bounded L-BFGS-B and (ii) ICP (independent cross-check),
  symmetric landscape grid, and mismatch spatial moments D1/D2/torque.
Checkpoints every 50 scans. No robust loss anywhere.
"""
import os, time, numpy as np, pandas as pd
import s0_common as C
import m_common as M

obj=M.Objective()
ids=C.scan_ids(); n=len(ids)
CONDS=["raw","scale","combined"]; K=2
def cond_cloud(i,c):
    z=M.load_scan(i); P=z["aligned"].astype(np.float64)
    if c=="raw": return P
    sub="scale" if c=="scale" else "combined"
    return np.load(os.path.join(M.RESCACHE,"corr",sub,f"corr_{i:04d}.npz"))["aligned"].astype(np.float64)
def z(nshape,dtype=float): return np.zeros((n,*nshape),dtype=dtype)
in_subset=np.isin(ids,np.array(M.EVERY5))
S={}
for c in CONDS:
    S[c]=dict(J0=z((K,)), g=z((6,K)), H=z((6,6,K)), dhat=z((6,K)),
              xistar=z((6,K)), Jstar=z((K,)), iters=z((K,),int),
              xilst=z((6,K)), lst_gn=z((K,)), lst_conv=z((K,),bool), lst_onbnd=z((K,),bool),
              eigmin=z((K,)), cond=z((K,)),
              D1=z((3,)), D2=z((3,)), torque=z((3,)))
# landscape: 3 trans mags + 3 rot mags, 3 axes, 2 signs, 2 obj  -> store raw only
LG=np.full((n,2,3,3,2,K),np.nan)
CKP=os.path.join(M.RESCACHE,"objective_main.npz")
t_start=time.perf_counter()
for ii,i in enumerate(ids):
    P=cond_cloud(i,"raw")
    for ci,c in enumerate(CONDS):
        Q = P if c=="raw" else cond_cloud(i,c)
        gh=M.grad_hess(obj,Q)
        # spatial moments (use frozen normals at raw NN; recompute for corr)
        _,nnq=obj.tree.query(Q,k=1,workers=-1); nq=obj.nM[nnq]; mq=obj.M[nnq]
        sq=np.einsum("ij,ij->i",Q-mq,nq)
        S[c]["D1"][ii]=(sq[:,None]*Q).mean(0)
        S[c]["D2"][ii]=(np.abs(sq)[:,None]*Q).sum(0)/np.abs(sq).sum()
        S[c]["torque"][ii]=(sq[:,None]*np.cross(Q,nq)).mean(0)
        for k in range(K):
            g=gh["gp"] if k==0 else gh["gl"]; H=gh["Hp"] if k==0 else gh["Hl"]
            S[c]["J0"][ii,k]=gh["J0"][k]; S[c]["g"][ii,:,k]=g; S[c]["H"][ii,:,:,k]=H
            ev=np.linalg.eigvalsh(H); S[c]["eigmin"][ii,k]=ev.min(); S[c]["cond"][ii,k]=np.linalg.cond(H)
            d,*_=np.linalg.lstsq(H,-g,rcond=None); S[c]["dhat"][ii,:,k]=d
            # PRIMARY local optimum = the objective's natural ICP local solver (all scans)
            ic=M.local_min_p2p(obj,Q) if k==0 else M.local_min_p2l(obj,Q)
            S[c]["xistar"][ii,:,k]=ic["xi"]; S[c]["Jstar"][ii,k]=ic["J"]; S[c]["iters"][ii,k]=ic["iters"]
            # independent cross-check = bounded L-BFGS-B on the pre-registered every-5th subset
            if in_subset[ii]:
                lo=M.local_opt_lbfgs(obj,Q,"p2p" if k==0 else "p2l")
                S[c]["xilst"][ii,:,k]=lo["xi"]; S[c]["lst_gn"][ii,k]=lo["gnorm"]
                S[c]["lst_conv"][ii,k]=lo["converged"]; S[c]["lst_onbnd"][ii,k]=lo["on_bound"]
    # landscape (raw): LG[type,axis,mag,sign,obj] ; zero is J0 already stored
    ls=M.landscape(obj,P)
    for ai in range(3):
        for mi,mag in enumerate(M.GRID_T):
            (pp,mm)=ls["t"][(ai,float(mag))]
            LG[ii,0,ai,mi,0,0]=pp[0]; LG[ii,0,ai,mi,1,0]=mm[0]
            LG[ii,0,ai,mi,0,1]=pp[1]; LG[ii,0,ai,mi,1,1]=mm[1]
        for mi,mag in enumerate(M.GRID_R):
            (pp,mm)=ls["r"][(ai,float(mag))]
            LG[ii,1,ai,mi,0,0]=pp[0]; LG[ii,1,ai,mi,1,0]=mm[0]
            LG[ii,1,ai,mi,0,1]=pp[1]; LG[ii,1,ai,mi,1,1]=mm[1]
    if (ii+1)%25==0 or ii==n-1:
        np.savez_compressed(CKP,
            **{f"{c}__{k}":v for c in CONDS for k,v in S[c].items()}, landscape=LG)
        el=(time.perf_counter()-t_start)/(ii+1)*(n-ii-1)
        print(f"  {ii+1}/{n}  eta {el/60:.1f}min",flush=True)
# flat CSV
rows=[]
for c in CONDS:
    for ii,i in enumerate(ids):
        for k,kn in enumerate(["p2p","p2l"]):
            xi=S[c]["xistar"][ii,:,k]; dh=S[c]["dhat"][ii,:,k]; xl=S[c]["xilst"][ii,:,k]
            rows.append(dict(scan=i,cond=c,obj=kn,J0=S[c]["J0"][ii,k],
                gnorm=np.linalg.norm(S[c]["g"][ii,:,k]),
                dhat_t_mm=np.linalg.norm(dh[:3])*1000,dhat_r_deg=np.degrees(np.linalg.norm(dh[3:])),
                tstar_mm=np.linalg.norm(xi[:3])*1000,rstar_deg=np.degrees(np.linalg.norm(xi[3:])),
                lbfgs_t_mm=np.linalg.norm(xl[:3])*1000,
                opt_cos=M.cosine(xi,xl) if (np.linalg.norm(xi)>1e-9 and np.linalg.norm(xl)>1e-9) else np.nan,
                Jstar=S[c]["Jstar"][ii,k],icp_iters=S[c]["iters"][ii,k],
                lst_gn=S[c]["lst_gn"][ii,k],lst_conv=S[c]["lst_conv"][ii,k],
                lst_onbnd=S[c]["lst_onbnd"][ii,k],
                eigmin=S[c]["eigmin"][ii,k],condH=S[c]["cond"][ii,k]))
pd.DataFrame(rows).to_csv(os.path.join(M.RESCACHE,"objective_per_scan.csv"),index=False)
print("[done] objective_main.npz + objective_per_scan.csv")
