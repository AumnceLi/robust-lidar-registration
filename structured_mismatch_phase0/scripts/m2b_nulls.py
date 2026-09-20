# -*- coding: utf-8 -*-
"""
m2b_nulls.py -- Null A (model-self) and Null B (spatial shuffle) for M1.

Null A: source = random subset of the MODEL with matched point count (a rigidly
        transformed model analysed about its own true alignment); plus a zero-mean
        isotropic-noise control (sigma = model NN spacing) showing symmetric noise
        does not create a mean gradient.
Null B: keep the exact mismatch-VECTOR multiset v_i = P_i - m_nn(i), permute its
        spatial assignment: P~_i = m_nn(i) + v_pi(i); gradient-only over B perms.
Pre-registered subset = every 5th scan (n=101).
"""
import os, time, numpy as np, pandas as pd
import s0_common as C
import m_common as M

obj=M.Objective(); MM=obj.M; rng=np.random.default_rng(C.RNG_SEED)
ids=M.EVERY5
B_SHUF=100
hh=np.array([M.FD_T]*3+[M.FD_R]*3)

def grad_only(P):
    g=np.zeros((6,2))
    for a in range(6):
        e=np.zeros(6); e[a]=hh[a]
        gp=obj.values(P, e); gm=obj.values(P,-e)
        g[a,0]=(gp[0]-gm[0])/(2*hh[a]); g[a,1]=(gp[1]-gm[1])/(2*hh[a])
    return g

# ---------------- Null A
rowsA=[]
for ii,i in enumerate(ids):
    z=M.load_scan(i); N=len(z["aligned"])
    sel=rng.choice(len(MM),N,replace=False)
    for variant,sig in [("self",0.0),("self_noise",0.0081)]:
        P=MM[sel].copy()
        if variant=="self_noise": P=P+rng.normal(0,sig,P.shape)
        gh=M.grad_hess(obj,P)
        for k,kn in enumerate(["p2p","p2l"]):
            g=gh["gp"] if k==0 else gh["gl"]; H=gh["Hp"] if k==0 else gh["Hl"]
            d,*_=np.linalg.lstsq(H,-g,rcond=None)
            lo=M.local_opt_lbfgs(obj,P,kn)
            rowsA.append(dict(scan=i,variant=variant,obj=kn,J0=gh["J0"][k],
                gnorm=np.linalg.norm(g),dhat_t_mm=np.linalg.norm(d[:3])*1000,
                dhat_r_deg=np.degrees(np.linalg.norm(d[3:])),
                tstar_mm=np.linalg.norm(lo["xi"][:3])*1000,
                rstar_deg=np.degrees(np.linalg.norm(lo["xi"][3:])),gnstar=lo["gnorm"]))
    if (ii+1)%20==0: print(f"  NullA {ii+1}/{len(ids)}",flush=True)
pd.DataFrame(rowsA).to_csv(os.path.join(M.RESCACHE,"nullA_self.csv"),index=False)

# ---------------- Null B (gradient-only shuffle)
gnorm_shuf=np.zeros((len(ids),B_SHUF,2))
gnorm_real=np.zeros((len(ids),2))
gvec_shuf=np.zeros((len(ids),B_SHUF,6,2))
t0=time.perf_counter()
for ii,i in enumerate(ids):
    z=M.load_scan(i); P=z["aligned"].astype(np.float64); nn=z["nnidx"]
    gnorm_real[ii]=[np.linalg.norm(M.grad_hess(obj,P)["gp"]),
                    np.linalg.norm(M.grad_hess(obj,P)["gl"])]
    v=P-MM[nn]
    for b in range(B_SHUF):
        pi=rng.permutation(len(P))
        Pt=MM[nn]+v[pi]
        gb=grad_only(Pt)
        gnorm_shuf[ii,b,0]=np.linalg.norm(gb[:,0]); gnorm_shuf[ii,b,1]=np.linalg.norm(gb[:,1])
        gvec_shuf[ii,b]=gb
    if (ii+1)%10==0: print(f"  NullB {ii+1}/{len(ids)} eta {(time.perf_counter()-t0)/(ii+1)*(len(ids)-ii-1)/60:.1f}m",flush=True)
np.savez_compressed(os.path.join(M.RESCACHE,"nullB_shuffle.npz"),
                    gnorm_shuf=gnorm_shuf,gnorm_real=gnorm_real,gvec_shuf=gvec_shuf,ids=np.array(ids))
print("[done] nullA_self.csv + nullB_shuffle.npz")
