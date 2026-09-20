# -*- coding: utf-8 -*-
"""r9_transfer.py -- SECONDARY transfers (after primary P3 locked):
 (1) single VI-only scalar alpha_VI for quadratic magnitude (never fit on IV/V);
 (2) frozen patch-profile replication; (3) VI patch-influence ranking -> IV/V."""
import os,sys,json
import numpy as np,pandas as pd
from scipy import stats
import s0_common as C, m_common as M

RC=M.RESCACHE; EXT=os.path.join(M.CACHE,"ext"); KP=24
hh=np.array([M.FD_T]*3+[M.FD_R]*3)
PLAB=np.load(os.path.join(M.CACHE,"patches.npz"))["lab"]
obj=M.Objective()
vi_infl=np.array(json.load(open(os.path.join(RC,"m4_direction_patch.json")))["infl_p2p"])
vi_profile=np.load(os.path.join(M.CACHE,"patch_matrix.npz"))["profile"]

# ---------- (1) alpha_VI : single scalar through-origin on VI raw p2p translation
OM=np.load(os.path.join(RC,"objective_main.npz"))
dh=OM["raw__dhat"][:,:,0]; xs=OM["raw__xistar"][:,:,0]
num=np.einsum("ti,ti->",dh[:,:3],xs[:,:3]); den=np.einsum("ti,ti->",dh[:,:3],dh[:,:3])
alpha=float(num/den)
print("[alpha_VI] =",alpha,flush=True)

def patch_probes(P):
    N=len(P); S=np.zeros((6,2,KP,2)); cnt=np.zeros((6,2,KP))
    for a in range(6):
        for sgn in (0,1):
            e=np.zeros(6); e[a]=hh[a]*(1 if sgn==0 else -1)
            z=obj.probe(P,e); lab=PLAB[z["idx"]]
            for j in range(KP):
                msk=lab==j; cnt[a,sgn,j]=msk.sum()
                S[a,sgn,j,0]=z["q2"][msk].sum(); S[a,sgn,j,1]=z["ql"][msk].sum()
    return S,cnt,N

def ext_influence(tag,insup,ids,od,step=5):
    sub=[ii for ii in range(len(ids)) if insup[ii]][::step]
    infl=np.zeros((len(sub),KP)); rg=[]
    for q,ii in enumerate(sub):
        z=np.load(os.path.join(od,f"scan_{int(ids[ii]):04d}.npz")); P=z["aligned"].astype(np.float64)
        d=z["d"]; patch=z["patch"]; S,cnt,N=patch_probes(P)
        gj=np.zeros((KP,6)); loo=np.zeros((KP,6)); k=0
        totp=S[:,0].sum(1)[:,k]; totm=S[:,1].sum(1)[:,k]; cntp=cnt[:,0]; cntm=cnt[:,1]
        for a in range(6):
            for j in range(KP):
                gj[j,a]=(S[a,0,j,k]-S[a,1,j,k])/(2*hh[a]*N)
                ep=(totp[a]-S[a,0,j,k])/max(N-cntp[a,j],1); em=(totm[a]-S[a,1,j,k])/max(N-cntm[a,j],1)
                loo[j,a]=(ep-em)/(2*hh[a])
        gall=gj.sum(0); infl[q]=np.linalg.norm(gall[None,:]-loo,axis=1)
        gjn=np.linalg.norm(gj,axis=1)
        # per-scan patch residual level vs ||g_j||
        pres=np.array([np.median(d[patch==j]) if (patch==j).any() else np.nan for j in range(KP)])
        msk=np.isfinite(pres);
        if msk.sum()>=8: rg.append(stats.spearmanr(pres[msk],gjn[msk]).statistic)
    return infl.mean(0),np.array(rg),len(sub)

rows=[]
for tag in (sys.argv[1:] or ["iv","v"]):
    od=os.path.join(EXT,tag); E=np.load(os.path.join(EXT,f"ext_objective_{tag}.npz"))
    PR=np.load(os.path.join(EXT,f"ext_predict_{tag}.npz")); insup=PR["insup"]; ids=E["ids"]
    dhE=E["raw__dhat"][:,:,0]; xsE=E["raw__xistar"][:,:,0]
    support_set="IN_SUPPORT" if insup.sum()>=20 else "ALL_OUT_OF_SUPPORT"
    m=insup if insup.sum()>=20 else np.ones(len(ids),bool)
    # (1) scalar quadratic magnitude transfer
    pred=alpha*dhE[m,:3]; obs=xsE[m,:3]
    slope=float(np.einsum("ti,ti->",pred,obs)/np.einsum("ti,ti->",pred,pred))
    rho=float(stats.spearmanr(np.linalg.norm(pred,axis=1),np.linalg.norm(obs,axis=1)).statistic)
    rmse=float(np.sqrt(((pred-obs)**2).sum(1).mean())*1000)
    # (2) patch profile transfer (pooled median unsigned residual per patch, IN_SUPPORT)
    pres=np.full(KP,np.nan)
    pool_d=[]; pool_p=[]
    for ii in np.where(m)[0]:
        z=np.load(os.path.join(od,f"scan_{int(ids[ii]):04d}.npz")); pool_d.append(z["d"]); pool_p.append(z["patch"])
    pool_d=np.concatenate(pool_d); pool_p=np.concatenate(pool_p)
    for j in range(KP):
        mm=pool_p==j
        if mm.any(): pres[j]=np.median(pool_d[mm])
    ok=np.isfinite(pres); prof_rho=float(stats.spearmanr(vi_profile[ok],pres[ok]).statistic)
    # (3) influence ranking transfer
    infl,rg,nsub=ext_influence(tag,m,ids,od)
    infl_rho=float(stats.spearmanr(vi_infl,infl).statistic)
    rows.append(dict(traj=tag,n_used=int(m.sum()),n_in_support=int(insup.sum()),support_set=support_set,alpha_VI=alpha,quad_slope=slope,
                     quad_mag_spearman=rho,quad_rmse_mm=rmse,profile_spearman=prof_rho,
                     influence_spearman=infl_rho,within_scan_resid_grad_rho=float(np.nanmean(rg)),
                     influence_n_subset=nsub))
    print(f"[{tag}] slope={slope:.3f} magRho={rho:.3f} rmse={rmse:.1f}mm profRho={prof_rho:.3f} "
          f"inflRho={infl_rho:.3f} withinRho={np.nanmean(rg):.3f}(n={nsub})",flush=True)
pd.DataFrame(rows).to_csv(os.path.join(M.REPORTS,"patch_transfer.csv"),index=False)
np.savez_compressed(os.path.join(RC,"quad_alpha.npz"),alpha=alpha)
print("[saved] patch_transfer.csv, quad_alpha.npz",flush=True)
