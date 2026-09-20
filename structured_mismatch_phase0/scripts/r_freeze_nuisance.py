# -*- coding: utf-8 -*-
"""r_freeze_nuisance.py -- re-derive VI-only global nuisance OPERATORS (deterministic,
seed 42, identical to m1) and freeze the full transforms for IV/V replication.
Verifies scalar values match nuisance_params.json; never touches IV/V."""
import os,json,numpy as np
from scipy.spatial import cKDTree
import s0_common as C, m_common as M

rng=np.random.default_rng(C.RNG_SEED)
mc=np.load(os.path.join(M.CACHE,"model_cache.npz"))
MODEL=mc["xyz"].astype(np.float64); NM=mc["normals"].astype(np.float64); TREE=cKDTree(MODEL)
FIT_PER_SCAN=600
fitP=[];fitd=[]
for i in C.scan_ids():
    z=M.load_scan(i); P=z["aligned"].astype(np.float64)
    d=M.ray_dirs_target(i,P); sel=rng.choice(len(P),min(FIT_PER_SCAN,len(P)),replace=False)
    fitP.append(P[sel]); fitd.append(d[sel])
fitP=np.vstack(fitP); fitd=np.vstack(fitd)
_,nnfit=TREE.query(fitP,k=1,workers=-1)

# N1
n=NM[nnfit]; c=np.einsum("ij,ij->i",n,fitd); sgn=np.einsum("ij,ij->i",fitP-MODEL[nnfit],n)
br=float(np.sum(sgn*c)/np.sum(c*c))
# N3
s=float(np.einsum("ij,ij->",fitP,MODEL[nnfit])/np.einsum("ij,ij->",MODEL[nnfit],MODEL[nnfit]))
# N2
def se3_p2l(Cc,iters=12):
    Racc=np.eye(3); tacc=np.zeros(3)
    for _ in range(iters):
        Q=(Racc@Cc.T).T+tacc; _,nn=TREE.query(Q,k=1,workers=-1)
        m=MODEL[nn]; nn2=NM[nn]
        A=np.concatenate([nn2,np.cross(Q,nn2)],axis=1); b=np.einsum("ij,ij->i",nn2,m-Q)
        delta=np.linalg.lstsq(A.T@A,A.T@b,rcond=None)[0]
        v=delta[:3]; w=delta[3:]; Rd=M.rodrigues(w); Racc=Rd@Racc; tacc=Rd@tacc+v
        if np.linalg.norm(delta[:3])<1e-7 and np.linalg.norm(delta[3:])<1e-8: break
    return Racc,tacc
Rse,tse=se3_p2l(fitP)
# N4 steps (identical to m1)
Cw=fitP.copy(); dw=fitd.copy(); steps=[]
for it in range(12):
    _,nn=TREE.query(Cw,k=1,workers=-1); m=MODEL[nn]; nn2=NM[nn]
    target=np.einsum("ij,ij->i",Cw-m,nn2)
    A=np.column_stack([nn2,np.cross(m,nn2),np.einsum("ij,ij->i",nn2,m),np.einsum("ij,ij->i",nn2,dw)])
    delta,*_=np.linalg.lstsq(A,target,rcond=None)
    dt,dwx,dg,dbr=delta[:3],delta[3:6],float(delta[6]),float(delta[7])
    Rd=M.rodrigues(dwx); steps.append((dt.copy(),Rd.copy(),dg,dbr))
    Cw=((Rd.T@(Cw-dt-dbr*dw).T).T)/(1+dg); dw=(Rd.T@dw.T).T
    if np.linalg.norm(dt)<1e-7 and np.linalg.norm(dwx)<1e-8 and abs(dg)<1e-6 and abs(dbr)<1e-7: break
Sdt=np.array([a[0] for a in steps]); SRd=np.array([a[1] for a in steps])
Sg=np.array([a[2] for a in steps]); Sbr=np.array([a[3] for a in steps])

out=os.path.join(M.RESCACHE,"frozen_nuisance_ops.npz")
np.savez_compressed(out,br=br,s=s,Rse=Rse,tse=tse,step_dt=Sdt,step_Rd=SRd,step_g=Sg,step_br=Sbr)
ref=json.load(open(os.path.join(M.RESCACHE,"nuisance_params.json")))
print("N1 br mm: %.4f (ref %.4f)"%(br*1000,ref["N1_br_mm"]))
print("N3 s: %.6f (ref %.6f)"%(s,ref["N3_s"]))
print("N2 |t| mm: %.4f (ref %.4f)  rot deg %.4f (ref %.4f)"%(
    np.linalg.norm(tse)*1000,np.linalg.norm(ref["N2_se3_t_mm"]),
    np.degrees(np.linalg.norm(M.rodrigues_log(Rse))),ref["N2_se3_rot_deg"]))
print("[frozen]",out,"N4 steps",len(steps))
