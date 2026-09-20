# -*- coding: utf-8 -*-
"""
m6_direction_patch.py -- (A) Directional mechanism: do mismatch spatial moments
predict the DIRECTION of the pose bias (cosine + permutation null)?  (B) Gate M4:
per-patch gradient contributions g_{t,j} (sum to g_t), high-residual-patch
disproportionate contribution, leave-one-patch-out influence.  This is a MECHANISTIC
INFLUENCE ANALYSIS only -- no filtering / correction is performed.
"""
import os, numpy as np, pandas as pd
from scipy import stats
import s0_common as C
import m_common as M

rng=np.random.default_rng(C.RNG_SEED)
D=np.load(os.path.join(M.RESCACHE,"objective_main.npz"))
pz=np.load(os.path.join(C.CACHE,"patches.npz")); PLAB=pz["lab"]; Kp=24
pm=np.load(os.path.join(C.CACHE,"patch_matrix.npz")); Mmat=pm["M"]; profile=pm["profile"]
obj=M.Objective(); hh=np.array([M.FD_T]*3+[M.FD_R]*3)

# ===================== (A) directional mechanism
dirout={}
for cond in ["raw","combined"]:
    D1=D[f"{cond}__D1"]; D2=D[f"{cond}__D2"]; tq=D[f"{cond}__torque"]
    for k,kn in enumerate(["p2p","p2l"]):
        xi=D[f"{cond}__xistar"][:,:,k]; T=xi[:,:3]; R=xi[:,3:]
        def cosblock(A,Bv):
            c=np.array([M.cosine(A[i],Bv[i]) for i in range(len(A))
                        if np.linalg.norm(A[i])>1e-12 and np.linalg.norm(Bv[i])>1e-12])
            return c
        c1=cosblock(D1,T); c2=cosblock(D2,T); cr=cosblock(tq,R)
        def perm(cosv,A,Bv,B=2000):
            obs=cosv.mean(); null=np.empty(B)
            for b in range(B):
                p=rng.permutation(len(A));
                cc=np.array([M.cosine(A[i],Bv[p[i]]) for i in range(len(A))
                             if np.linalg.norm(A[i])>1e-12 and np.linalg.norm(Bv[p[i]])>1e-12])
                null[b]=cc.mean()
            # two-sided: fraction of permutations with alignment at least as extreme
            p2=float((1+np.sum(np.abs(null)>=abs(obs)))/(B+1))
            return obs,p2,float(np.percentile(np.abs(null),95))
        o1,p1,_=perm(c1,D1,T); o2,p2,_=perm(c2,D2,T); orr,prr,_=perm(cr,tq,R)
        dirout[f"{cond}|{kn}"]=dict(cos_D1_dT=float(c1.mean()),p_D1=p1,
            cos_D2_dT=float(c2.mean()),p_D2=p2,cos_torque_dR=float(cr.mean()),p_torque=prr)
        print(f"[dir {cond:8s} {kn}] cos(D1,dT)={c1.mean():+.3f}(p{p1:.4f}) cos(D2,dT)={c2.mean():+.3f}(p{p2:.4f}) "
              f"cos(torque,dR)={cr.mean():+.3f}(p{prr:.4f})")

# ===================== (B) M4 patch gradient contributions (raw, both obj)
def patch_probes(P):
    """12 shared FD probes -> per-patch sum of q at +/- h for 6 axes, both obj."""
    N=len(P)
    # store per-patch sums at +h and -h for each axis: shape (6,2,Kp,2obj) and counts
    S=np.zeros((6,2,Kp,2)); cnt=np.zeros((6,2,Kp))
    for a in range(6):
        for sgn in (0,1):
            e=np.zeros(6); e[a]=hh[a]*(1 if sgn==0 else -1)
            z=obj.probe(P,e); lab=PLAB[z["idx"]]
            for j in range(Kp):
                msk=lab==j; cnt[a,sgn,j]=msk.sum()
                S[a,sgn,j,0]=z["q2"][msk].sum(); S[a,sgn,j,1]=z["ql"][msk].sum()
    return S,cnt,N
gj_all=np.zeros((501,Kp,6,2)); loo_all=np.zeros((501,Kp,6,2)); gall=np.zeros((501,6,2))
corr_resid_grad=[]
for i in C.scan_ids():
    P=M.load_scan(i)["aligned"].astype(np.float64)
    S,cnt,N=patch_probes(P)
    for k in range(2):
        # per-patch global-scaled gradient g_j = (1/N) central diff of patch sum
        gj=np.zeros((Kp,6))
        gloo=np.zeros((Kp,6))
        totp=S[:,0].sum(1)[:,k]; totm=S[:,1].sum(1)[:,k]   # sum over patches = grand sum at probe
        cntp=cnt[:,0,:]; cntm=cnt[:,1,:]                    # (6,Kp) per-patch counts
        for a in range(6):
            for j in range(Kp):
                gj[j,a]=(S[a,0,j,k]-S[a,1,j,k])/(2*hh[a]*N)
                # leave-j-out renormalized gradient
                ex_p=(totp[a]-S[a,0,j,k])/max(N-cntp[a,j],1)
                ex_m=(totm[a]-S[a,1,j,k])/max(N-cntm[a,j],1)
                gloo[j,a]=(ex_p-ex_m)/(2*hh[a])
        gj_all[i,:,:,k]=gj; loo_all[i,:,:,k]=gloo; gall[i,:,k]=gj.sum(0)
    # correlation patch residual level vs ||g_j|| (p2p)
    gjnorm=np.linalg.norm(gj_all[i,:,:,0],axis=1); ok=np.isfinite(Mmat[i])
    if ok.sum()>=8: corr_resid_grad.append(stats.spearmanr(Mmat[i,ok],gjnorm[ok]).statistic)
corr_resid_grad=np.array(corr_resid_grad)
# influence I_j = ||g - g^(-j)|| averaged over scans; compare with frozen profile
infl=np.linalg.norm(gall[:,None,:,:]-loo_all,axis=2).mean(0)   # (Kp,2obj)
prof_rank=stats.spearmanr(profile,infl[:,0])
# self-consistency: sum_j g_j vs direct g
direct=D["raw__g"]
recon_err=np.linalg.norm(gj_all.sum(1)-direct,axis=1)/np.linalg.norm(direct,axis=1)
m4=dict(dir=dirout,
    resid_grad_corr_mean=float(np.nanmean(corr_resid_grad)),
    resid_grad_corr_ci=[float(x) for x in np.nanpercentile(corr_resid_grad,[2.5,97.5])],
    resid_grad_frac_positive=float((corr_resid_grad>0).mean()),
    influence_profile_spearman_p2p=float(prof_rank.statistic),influence_profile_p=float(prof_rank.pvalue),
    top_influence_patches=np.argsort(-infl[:,0])[:6].tolist(),
    top_profile_patches=np.argsort(-profile)[:6].tolist(),
    gradient_recon_med_err=float(np.median(recon_err)),
    infl_p2p=infl[:,0].tolist(),infl_p2l=infl[:,1].tolist(),profile=profile.tolist())
M.save_json(m4,"m4_direction_patch.json")
np.savez_compressed(os.path.join(M.RESCACHE,"m4_patch_grad.npz"),gj=gj_all,loo=loo_all,g=gall,infl=infl)
print(f"[M4] resid-vs-|g_j| spearman mean={np.nanmean(corr_resid_grad):.3f} CI{m4['resid_grad_corr_ci']} "
      f"frac>0={m4['resid_grad_frac_positive']:.2f}")
print(f"[M4] influence vs frozen profile spearman={prof_rank.statistic:.3f}(p{prof_rank.pvalue:.1e}) "
      f"recon err med={np.median(recon_err):.4f}")
print("[M4] top influence patches",m4['top_influence_patches']," top residual patches",m4['top_profile_patches'])
