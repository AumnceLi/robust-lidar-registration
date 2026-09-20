# -*- coding: utf-8 -*-
"""
m3_m1_stationarity.py -- Gate M1: is the standard registration objective STATIONARY
at the true pose?  Compare ||g(T_GT)|| real vs Null A (model-self) and Null B
(spatial shuffle); effect size, bootstrap CI, Mann-Whitney/permutation p; J1/J2
consistency; finite-difference step stability (numerical validity).
"""
import os, numpy as np, pandas as pd
from scipy import stats
import s0_common as C
import m_common as M

D=np.load(os.path.join(M.RESCACHE,"objective_main.npz"))
CONDS=["raw","scale","combined"]; OBJ=["p2p","p2l"]
ids=np.array(C.scan_ids()); every5=np.array(M.EVERY5); m5=np.isin(ids,every5)
nullA=pd.read_csv(os.path.join(M.RESCACHE,"nullA_self.csv"))
NB=np.load(os.path.join(M.RESCACHE,"nullB_shuffle.npz"))

def cohend(a,b):
    na,nb=len(a),len(b); sp=np.sqrt(((na-1)*a.var(ddof=1)+(nb-1)*b.var(ddof=1))/(na+nb-2))
    return float((a.mean()-b.mean())/sp)

out={"by_condition":{},"fd_stability":{}}
for c in CONDS:
    g=D[f"{c}__g"]; J0=D[f"{c}__J0"]
    rec={}
    for k,kn in enumerate(OBJ):
        gv=g[:,:,k]; gn=np.linalg.norm(gv,axis=1)
        mu,muNorm,T2,hp=M.hotelling(gv)
        # nulls on same every-5th subset
        gn_sub=gn[m5]
        ga=nullA[(nullA.variant=="self")&(nullA.obj==kn)].gnorm.values
        gan=nullA[(nullA.variant=="self_noise")&(nullA.obj==kn)].gnorm.values
        sh=NB["gnorm_shuf"][:,:,k].ravel()
        med,lo,hi=M.boot_ci(gn_sub,np.median)
        u_p=stats.mannwhitneyu(gn_sub,ga,alternative="greater").pvalue
        p_sh=M.perm_p(np.median(gn_sub),[np.median(NB["gnorm_shuf"][b,:,k]) for b in range(NB["gnorm_shuf"].shape[0])])
        rec[kn]=dict(real_median=float(np.median(gn)),real_mean=float(gn.mean()),
            boot_median_ci=[med,lo,hi],
            self_median=float(np.median(ga)),selfnoise_median=float(np.median(gan)),
            shuffle_median=float(np.median(sh)),
            ratio_real_self=float(np.median(gn_sub)/np.median(ga)),
            ratio_real_shuffle=float(np.median(gn_sub)/np.median(sh)),
            cohens_d_self=cohend(gn_sub,ga),cohens_d_shuffle=cohend(gn_sub,sh),
            mw_p_self=float(u_p),perm_p_shuffle=float(p_sh),
            hotelling_T2=T2,hotelling_p=hp,mean_g=mu)
    # J1/J2 consistency
    gp,gl=g[:,:,0],g[:,:,1]
    cos=np.array([M.cosine(gp[i],gl[i]) for i in range(len(gp))])
    rp=stats.spearmanr(np.linalg.norm(gp,axis=1),np.linalg.norm(gl,axis=1)).statistic
    rec["J1J2"]=dict(cos_median=float(np.median(cos)),cos_mean=float(cos.mean()),
                     cos_p05=float(np.percentile(cos,5)),gnorm_spearman=float(rp))
    out["by_condition"][c]=rec

# ---- finite-difference step stability on a fixed 30-scan subset (numerical validity)
obj=M.Objective(); sub=np.linspace(0,500,30,dtype=int)
stab=[]
for i in sub:
    P=M.load_scan(i)["aligned"].astype(np.float64)
    base=M.grad_hess(obj,P,M.FD_T,M.FD_R)
    for ht,hr in zip(M.FD_T_TRY,M.FD_R_TRY):
        gh=M.grad_hess(obj,P,ht,hr)
        for k,kn in enumerate(OBJ):
            g0=base["gp"] if k==0 else base["gl"]; g1=gh["gp"] if k==0 else gh["gl"]
            stab.append(dict(scan=i,obj=kn,ht=ht,hr=hr,gnorm=np.linalg.norm(g1),cos=M.cosine(g0,g1)))
sdf=pd.DataFrame(stab); sdf.to_csv(os.path.join(M.RESCACHE,"fd_stability.csv"),index=False)
for kn in OBJ:
    d=sdf[sdf.obj==kn]
    out["fd_stability"][kn]=(d.groupby("ht").cos.apply(lambda x:float(x.mean())).to_dict(),
                             float(d.groupby("ht").gnorm.apply(lambda x:x.std()/x.mean()).mean()))
M.save_json(out,"m1_stationarity.json")
pd.DataFrame([dict(cond=c,obj=kn,**{kk:(vv if not isinstance(vv,dict) else vv) for kk,vv in out["by_condition"][c][kn].items()})
              for c in CONDS for kn in OBJ]).to_csv(os.path.join(M.RESCACHE,"m1_summary.csv"),index=False)
# console verdict
for c in CONDS:
    for kn in OBJ:
        r=out["by_condition"][c][kn]
        print(f"[{c:8s} {kn}] real|g| med={r['real_median']:.5f} self={r['self_median']:.2e} "
              f"ratio={r['ratio_real_self']:7.0f}x d={r['cohens_d_self']:.1f} p={r['mw_p_self']:.1e} "
              f"shufRatio={r['ratio_real_shuffle']:.2f}x Hotelling p={r['hotelling_p']:.1e}")
print("J1/J2:",{c:out['by_condition'][c]['J1J2'] for c in CONDS})
