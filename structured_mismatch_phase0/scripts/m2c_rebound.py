# -*- coding: utf-8 -*-
"""m2c: recompute ONLY the basin-clipped ICP local optima (g/H/dhat/moments unchanged)."""
import os, time, numpy as np, pandas as pd
import s0_common as C, m_common as M
obj=M.Objective()
P_=os.path.join(M.RESCACHE,"objective_main.npz"); D=dict(np.load(P_))
CONDS=["raw","scale","combined"]; ids=C.scan_ids(); n=len(ids)
def cloud(i,c):
    P=M.load_scan(i)["aligned"].astype(np.float64)
    if c=="raw": return P
    sub="scale" if c=="scale" else "combined"
    return np.load(os.path.join(M.RESCACHE,"corr",sub,f"corr_{i:04d}.npz"))["aligned"].astype(np.float64)
t0=time.perf_counter()
for c in CONDS:
    xi=np.zeros((n,6,2)); js=np.zeros((n,2)); it=np.zeros((n,2),int); bnd=np.zeros((n,2),bool)
    for ii,i in enumerate(ids):
        Q=cloud(i,c)
        for k in range(2):
            r=M.local_min_p2p(obj,Q) if k==0 else M.local_min_p2l(obj,Q)
            xi[ii,:,k]=r["xi"]; it[ii,k]=r["iters"]; bnd[ii,k]=r["on_bound"]
            js[ii,k]=obj.values(Q,r["xi"])[k]
        if (ii+1)%50==0: print(c,ii+1,"/",n,flush=True)
    D[f"{c}__xistar"]=xi; D[f"{c}__Jstar"]=js; D[f"{c}__iters"]=it
    np.savez_compressed(P_,**D)   # checkpoint per condition
    print("saved condition",c,flush=True)
# regenerate flat CSV
rows=[]
for c in CONDS:
    for ii,i in enumerate(ids):
        for k,kn in enumerate(["p2p","p2l"]):
            x=D[f"{c}__xistar"][ii,:,k]; dh=D[f"{c}__dhat"][ii,:,k]; xl=D[f"{c}__xilst"][ii,:,k]
            rows.append(dict(scan=i,cond=c,obj=kn,J0=D[f"{c}__J0"][ii,k],
                gnorm=np.linalg.norm(D[f"{c}__g"][ii,:,k]),
                dhat_t_mm=np.linalg.norm(dh[:3])*1000,dhat_r_deg=np.degrees(np.linalg.norm(dh[3:])),
                tstar_mm=np.linalg.norm(x[:3])*1000,rstar_deg=np.degrees(np.linalg.norm(x[3:])),
                lbfgs_t_mm=np.linalg.norm(xl[:3])*1000,
                opt_cos=M.cosine(x,xl) if (np.linalg.norm(x)>1e-9 and np.linalg.norm(xl)>1e-9) else np.nan,
                Jstar=D[f"{c}__Jstar"][ii,k],icp_iters=D[f"{c}__iters"][ii,k],
                lst_gn=D[f"{c}__lst_gn"][ii,k],lst_conv=D[f"{c}__lst_conv"][ii,k],
                lst_onbnd=D[f"{c}__lst_onbnd"][ii,k],
                eigmin=D[f"{c}__eigmin"][ii,k],condH=D[f"{c}__cond"][ii,k]))
pd.DataFrame(rows).to_csv(os.path.join(M.RESCACHE,"objective_per_scan.csv"),index=False)
print("[done] rebound local optima in %.1fmin"%((time.perf_counter()-t0)/60))
