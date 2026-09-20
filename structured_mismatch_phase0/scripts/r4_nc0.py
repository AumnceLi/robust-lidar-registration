# -*- coding: utf-8 -*-
"""r4_nc0.py -- NC0 gate on VI-internal non-circular prediction (must pass before IV/V)."""
import os, json, numpy as np, pandas as pd
from scipy import stats as st
import s0_common as C, m_common as M
import r3_vi_template as R3

rng=np.random.default_rng(M.RNG_SEED)
OM=np.load(os.path.join(M.RESCACHE,"objective_main.npz"))
CONDS=["raw","scale","combined"]; OBJS=["p2p","p2l"]
xistar={c:OM[f"{c}__xistar"] for c in CONDS}
P=np.load(os.path.join(M.RESCACHE,"r3_predictions.npz"))
dhatA=P["dhatA"]; dhatB=P["dhatB"]; kstar=int(P["kstar"]); kscores=P["kscores"]; kgrid=P["kgrid"]
N=M.N_SCANS

def cos_table(dhat):
    tab={}
    for c in CONDS:
        for ki,kn in enumerate(OBJS):
            ct=np.full(N,np.nan); nt=np.full(N,np.nan); no=np.full(N,np.nan)
            for t in range(N):
                a=dhat[t,:3,ki]; b=xistar[c][t,:3,ki]
                if np.linalg.norm(a)>1e-12 and np.linalg.norm(b)>1e-12:
                    ct[t]=M.cosine(a,b); nt[t]=np.linalg.norm(a)*1000; no[t]=np.linalg.norm(b[:3])*1000
            tab[f"{c}|{kn}"]=(ct,nt,no)
    return tab

def autocorr_block_len(x, thr=0.2, Lmin=5, Lmax=60):
    x=x-np.nanmean(x); n=len(x); ac=[]
    for L in range(1,Lmax+1):
        ac.append(np.sum(x[:-L]*x[L:])/(np.sum(x*x)+1e-12))
    ac=np.array(ac); idx=np.where(ac<thr)[0]
    return int(max(Lmin,(idx[0]+1) if len(idx) else Lmin))

def mb_boot_median(x, L, B=2000):
    x=x[np.isfinite(x)]; n=len(x); nb=int(np.ceil(n/L)); out=np.empty(B)
    starts=rng.integers(0,n-L+1,size=(B,nb))
    for b in range(B):
        samp=np.concatenate([x[s:s+L] for s in starts[b]])[:n]
        out[b]=np.median(samp)
    return np.percentile(out,[2.5,97.5])

def vector_pair_perm(dhat,xist,ki,B=2000):
    """Null: pair predicted vector of scan pi(t) with observed vector of t, recompute cosine."""
    a=dhat[:,:3,ki]; b=xist[:,:3,ki]
    ok=(np.linalg.norm(a,axis=1)>1e-12)&(np.linalg.norm(b,axis=1)>1e-12); idx=np.where(ok)[0]
    def medcos(ia,ib):
        aa=a[ia]; bb=b[ib]; na=np.linalg.norm(aa,axis=1); nb=np.linalg.norm(bb,axis=1)
        return np.median(np.einsum("ti,ti->t",aa,bb)/(na*nb+1e-15))
    obs=medcos(idx,idx); null=np.empty(B)
    for bb_ in range(B): null[bb_]=medcos(idx,rng.permutation(idx))
    return obs,float((1+np.sum(null>=obs))/(B+1))

def summarize(tab, tag, dhat):
    rows=[]; res={}
    for key,(ct,nt,no) in tab.items():
        cnd,objk=key.split("|"); ki=0 if objk=="p2p" else 1
        msk=np.isfinite(ct); c=ct[msk]
        med=float(np.median(c)); mean=float(c.mean()); frac=float((c>0).mean())
        ci_pt=np.percentile([np.median(rng.choice(c,len(c),replace=True)) for _ in range(2000)],[2.5,97.5])
        L=autoblock[key]; ci_mb=mb_boot_median(ct,L)
        obs,pp=vector_pair_perm(dhat,xistar[cnd],ki)
        rho=float(st.spearmanr(nt[msk],no[msk]).statistic) if np.isfinite(nt[msk]).any() else np.nan
        res[key]=dict(tag=tag,median=med,mean=mean,frac_pos=frac,ci_pt=[float(ci_pt[0]),float(ci_pt[1])],
                      ci_block=[float(ci_mb[0]),float(ci_mb[1])],block_len=L,perm_p=pp,mag_spearman=rho,n=int(msk.sum()))
        r=res[key]; rows.append(dict(protocol=tag,cond_obj=key,**{kk:vv for kk,vv in r.items() if kk!='tag'}))
    return res,pd.DataFrame(rows)

tabA=cos_table(dhatA); tabB=cos_table(dhatB)
# block length from observed raw p2p tx autocorrelation (VI only, pre-registered)
autoblock={}
for c in CONDS:
    for ki,kn in enumerate(OBJS):
        autoblock[f"{c}|{kn}"]=autocorr_block_len(xistar[c][:,0,ki])
print("[block lengths]",autoblock,flush=True)

resA,dfA=summarize(tabA,"A_embargo10",dhatA); resB,dfB=summarize(tabB,"B_blockout",dhatB)
df=pd.concat([dfA,dfB],ignore_index=True)
df.to_csv(os.path.join(M.RESCACHE,"..","..","..","reports","vi_noncircular.csv"),index=False)
df.to_csv(os.path.join(M.RESCACHE,"vi_noncircular_internal.csv"),index=False)

# ---- NC0 gate (primary: Protocol A, raw, p2p translation direction)
prim=resA["raw|p2p"]
NC0=dict(kstar=kstar,kgrid=kgrid.tolist(),kscores={int(k):float(v) for k,v in zip(kgrid,kscores)},
         primary="A|raw|p2p",median_cos=prim["median"],ci95_block=prim["ci_block"],
         frac_pos=prim["frac_pos"],perm_p=prim["perm_p"],mag_spearman=prim["mag_spearman"],
         thresholds=dict(median_min=0.70,ci_lo_gt=0,frac_pos_min=0.75,perm_p_max=0.01))
NC0["pass"]=bool(prim["median"]>=0.70 and prim["ci_block"][0]>0 and prim["frac_pos"]>=0.75 and prim["perm_p"]<=0.01)
out=dict(NC0=NC0,protocol_A=resA,protocol_B=resB,block_lengths=autoblock)
M.save_json(out,"nc0_vi.json")
print(json.dumps(NC0,indent=1,ensure_ascii=False),flush=True)
print("\n=== Protocol A all cond/obj ===")
for k,v in resA.items():
    print(f"A {k:14s} med={v['median']:.3f} CIblock[{v['ci_block'][0]:.3f},{v['ci_block'][1]:.3f}] frac+={v['frac_pos']:.2f} p={v['perm_p']:.4f} magRho={v['mag_spearman']:.2f}")
print("=== Protocol B ===")
for k,v in resB.items():
    print(f"B {k:14s} med={v['median']:.3f} frac+={v['frac_pos']:.2f} p={v['perm_p']:.4f}")
print("NC0 PASS =",NC0["pass"],flush=True)
