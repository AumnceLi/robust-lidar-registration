# -*- coding: utf-8 -*-
"""
m5_m3_specificity.py -- Gate M3: does STRUCTURED MISMATCH explain the local-optimum
displacement AFTER controlling range / point-count / aspect / time / tumble / residual
global nuisance?  Nested OLS incremental partial R2 + bootstrap CI + range-bin
permutation (Null C) + matched high/low mismatch (Null D).
"""
import os, numpy as np, pandas as pd
from scipy import stats
import s0_common as C
import m_common as M

rng=np.random.default_rng(C.RNG_SEED)
rs=pd.read_csv(os.path.join(C.RESULTS,"residual_per_scan.csv")).sort_values("scan_id").reset_index(drop=True)
pm=np.load(os.path.join(C.CACHE,"patch_matrix.npz")); Mmat=pm["M"]; prof=pm["profile"]; sps=pm["sps"]
D=np.load(os.path.join(M.RESCACHE,"objective_main.npz"))

# ---- controls: aspect to scan0 + tumble rate
Rs=np.array([C.quat_to_R(C.load_pose(i)[2]) for i in C.scan_ids()])
ts=np.array([C.load_pose(i)[0] for i in C.scan_ids()])
aspect=np.array([C.geodesic_deg(Rs[0],R) for R in Rs])
tumble=np.zeros(501)
for i in range(1,501):
    tumble[i]=C.geodesic_deg(Rs[i-1],Rs[i])/max(ts[i]-ts[i-1],1e-6)
tumble[0]=tumble[1]
profdev=np.sqrt(np.nanmean((Mmat-prof[None,:])**2,axis=1))
asym=rs.p90_residual_m-rs.median_residual_m

feat=pd.DataFrame(dict(
    sps=sps, r4=rs.r4_structured_frac, signed=rs.mean_signed_residual,
    excess=rs.excess_return_fraction, profdev=profdev, asym=asym,
    rng=rs.range_m, logn=np.log(rs.point_count), aspect=aspect,
    t=(ts-ts.mean())/ts.std(), tumble=tumble))
MIS=["sps","r4","signed","excess","profdev","asym"]
CTL=["rng","logn","aspect","t","tumble"]

def ols_sse(X,y):
    X=np.column_stack([np.ones(len(X)),np.nan_to_num(X)]); beta=np.linalg.pinv(X)@y
    r=y-X@beta; return r@r, beta
def partial_r2(Xc,Xm,y):
    sc,_=ols_sse(Xc,y); sf,_=ols_sse(np.column_stack([Xc,Xm]),y)
    return (sc-sf)/sc

def zmat(cols,df):
    X=df[cols].values.astype(float); sd=X.std(0); sd[sd==0]=1
    X=(X-X.mean(0))/sd; return np.nan_to_num(X)
Xc=zmat(CTL,feat)
# nuisance residual control = combined-corrected J0 (p2p) added to controls for the raw endpoint test
J0comb=D["combined__J0"][:,0]
Xc_full=np.column_stack([Xc,(J0comb-J0comb.mean())/J0comb.std()])
Xm=zmat(MIS,feat)

res={}
for cond in ["raw","scale","combined"]:
    for k,kn in enumerate(["p2p","p2l"]):
        xi=D[f"{cond}__xistar"][:,:,k]; T=xi[:,:3]; R=xi[:,3:]
        consensus=T.mean(0); consensus/=np.linalg.norm(consensus)
        endpoints={"proj":T@consensus,"tmag":np.linalg.norm(T,axis=1),
                   "rmag":np.linalg.norm(R,axis=1)}
        for en,y in endpoints.items():
            ctrls = Xc_full if cond=="raw" else Xc
            pr=partial_r2(ctrls,Xm,y)
            # bootstrap CI
            boots=[]
            for b in range(2000):
                idx=rng.integers(0,len(y),len(y)); boots.append(partial_r2(ctrls[idx],Xm[idx],y[idx]))
            lo,hi=np.percentile(boots,[2.5,97.5])
            # Null C: permute mismatch block jointly within range quintile bins
            rbins=pd.qcut(feat.rng,5,labels=False)
            null=[]
            for b in range(1000):
                Xp=Xm.copy()
                for q in range(5):
                    ix=np.where(rbins==q)[0]; Xp[ix]=Xm[rng.permutation(ix)]
                null.append(partial_r2(ctrls,Xp,y))
            pperm=(1+np.sum(np.array(null)>=pr))/(len(null)+1)
            res[f"{cond}|{kn}|{en}"]=dict(partial_R2=float(pr),ci=[float(lo),float(hi)],
                                          perm_p=float(pperm),null_mean=float(np.mean(null)))
# ---- Null D matched high/low on controls (raw p2p tmag primary)
xi=D["raw__xistar"][:,:,0]; tmag=np.linalg.norm(xi[:,:3],axis=1)
mc=zmat(CTL,feat); mismatch_score=zmat(MIS,feat).mean(1)
med=np.median(mismatch_score); hi_idx=np.where(mismatch_score>=med)[0]; lo_idx=np.where(mismatch_score<med)[0]
pairs=[]; used=set()
for i in hi_idx:
    d=np.linalg.norm(mc[lo_idx]-mc[i],axis=1); j=lo_idx[np.argmin(d)]
    if j not in used and np.min(d)<1.0: pairs.append((i,j)); used.add(j)
pairs=np.array(pairs)
dh=tmag[pairs[:,0]]; dl=tmag[pairs[:,1]]
wx=stats.wilcoxon(dh,dl,alternative="greater")
nullD=dict(n_pairs=len(pairs),high_med=float(np.median(dh)),low_med=float(np.median(dl)),
           wilcoxon_p=float(wx.pvalue),high_mean=float(dh.mean()),low_mean=float(dl.mean()))
M.save_json(dict(partial=res,nullD=nullD),"m3_specificity.json")
rows=[]
for key,v in res.items():
    cond,kn,en=key.split("|"); rows.append(dict(cond=cond,obj=kn,endpoint=en,
        partialR2=v['partial_R2'],ci_lo=v['ci'][0],ci_hi=v['ci'][1],perm_p=v['perm_p'],null_mean=v['null_mean']))
pd.DataFrame(rows).to_csv(os.path.join(M.RESCACHE,"m3_summary.csv"),index=False)
for key,v in res.items():
    print(f"{key:22s} dR2={v['partial_R2']:.4f} CI[{v['ci'][0]:.4f},{v['ci'][1]:.4f}] permP={v['perm_p']:.4f} null={v['null_mean']:.4f}")
print("NullD",nullD)
