# -*- coding: utf-8 -*-
"""
m4_m2_localopt.py -- Gate M2: systematic displacement of the objective's local
minimum from GT.  E[Dxi]!=0 (not just E[||Dxi||]>0): Hotelling on translation and
rotation vectors, component bootstrap CI, sign consistency, spherical direction /
rotation-axis concentration (Rayleigh), magnitude CI, self-floor, L-BFGS vs ICP
optimizer agreement.
"""
import os, numpy as np, pandas as pd
from scipy import stats
import s0_common as C
import m_common as M

D=np.load(os.path.join(M.RESCACHE,"objective_main.npz"))
csv=pd.read_csv(os.path.join(M.RESCACHE,"objective_per_scan.csv"))
nullA=pd.read_csv(os.path.join(M.RESCACHE,"nullA_self.csv"))
CONDS=["raw","scale","combined"]; OBJ=["p2p","p2l"]
out={}
for c in CONDS:
    xi=D[f"{c}__xistar"]; xilst=D[f"{c}__xilst"]; rec={}
    for k,kn in enumerate(OBJ):
        X=xi[:,:,k]; T=X[:,:3]; R=X[:,3:]
        tnorm=np.linalg.norm(T,axis=1); rnorm=np.linalg.norm(R,axis=1)
        mu_t,nt,T2t,pt=M.hotelling(T); mu_r,nr,T2r,pr=M.hotelling(R)
        # component bootstrap CIs
        ci_t=[M.boot_ci(T[:,j]) for j in range(3)]
        # sign consistency along mean translation direction
        ut=T/np.maximum(tnorm[:,None],1e-12); dirT=mu_t/np.linalg.norm(mu_t)
        signcons=float((T@dirT>0).mean())
        Rlen_t,meandt=M.resultant_concentration(T[tnorm>1e-6])
        ray_t=M.rayleigh_p(Rlen_t,len(T))
        Rlen_r,meandr=M.resultant_concentration(R[rnorm>1e-6])
        ray_r=M.rayleigh_p(Rlen_r,int((rnorm>1e-6).sum()))
        # magnitude CI
        mt,lot,hit=M.boot_ci(tnorm*1000); mr,lor,hir=M.boot_ci(np.degrees(rnorm))
        # self floor
        sa=nullA[(nullA.variant=="self")&(nullA.obj==kn)].tstar_mm.values
        # optimizer agreement (ICP primary vs L-BFGS cross-check) on the every-5th subset
        hassub=np.linalg.norm(xilst,axis=1)>1e-9
        cosopt=np.array([M.cosine(X[i],xilst[i,:,k]) for i in np.where(hassub)[0]])
        sub=csv[(csv.cond==c)&(csv.obj==kn)]
        subl=sub[sub.lbfgs_t_mm>0]
        rec[kn]=dict(mean_trans_mm=(mu_t*1000).tolist(),hotelling_T_p=pt,
            mean_rotvec_deg=np.degrees(mu_r).tolist(),hotelling_R_p=pr,
            trans_mag_mean=float(tnorm.mean()*1000),trans_mag_med_ci=[mt,lot,hit],
            rot_mag_mean_deg=float(np.degrees(rnorm.mean())),rot_mag_ci=[mr,lor,hir],
            sign_consistency=signcons,dir_concentration=Rlen_t,rayleigh_t_p=ray_t,
            axis_concentration=Rlen_r,rayleigh_r_p=ray_r,
            self_tstar_med_mm=float(np.median(sa)),
            ratio_to_self=float(np.median(tnorm*1000)/max(np.median(sa),1e-6)),
            opt_agreement_cos_med=float(np.median(cosopt)),
            lbfgs_converged_frac=float(subl.lst_conv.mean()),lbfgs_onbound_frac=float(subl.lst_onbnd.mean()),
            lbfgs_icp_t_spearman=float(stats.spearmanr(subl.tstar_mm,subl.lbfgs_t_mm).statistic) if len(subl)>5 else np.nan)
    out[c]=rec
M.save_json(out,"m2_localopt.json")
rows=[]
for c in CONDS:
    for kn in OBJ:
        r=out[c][kn]; rows.append(dict(cond=c,obj=kn,
            mean_t_x=r['mean_trans_mm'][0],mean_t_y=r['mean_trans_mm'][1],mean_t_z=r['mean_trans_mm'][2],
            Hotelling_p=r['hotelling_T_p'],tmag_med=r['trans_mag_med_ci'][0],tmag_lo=r['trans_mag_med_ci'][1],tmag_hi=r['trans_mag_med_ci'][2],
            sign=r['sign_consistency'],dirconc=r['dir_concentration'],ray_p=r['rayleigh_t_p'],
            selfmed=r['self_tstar_med_mm'],ratio_self=r['ratio_to_self'],optcos=r['opt_agreement_cos_med'],
            lbfgs_conv=r['lbfgs_converged_frac'],lbfgs_onbound=r['lbfgs_onbound_frac']))
pd.DataFrame(rows).to_csv(os.path.join(M.RESCACHE,"m2_summary.csv"),index=False)
for c in CONDS:
    for kn in OBJ:
        r=out[c][kn]
        print(f"[{c:8s} {kn}] meanT(mm)=[{r['mean_trans_mm'][0]:.1f},{r['mean_trans_mm'][1]:.1f},{r['mean_trans_mm'][2]:.1f}] "
              f"|T|={r['trans_mag_med_ci'][0]:.1f}mm sign={r['sign_consistency']:.2f} dirConc={r['dir_concentration']:.3f} "
              f"rayP={r['rayleigh_t_p']:.1e} selfT={r['self_tstar_med_mm']:.3f}mm optCos={r['opt_agreement_cos_med']:.3f} "
              f"lbfgsBound={r['lbfgs_onbound_frac']:.2f}")
