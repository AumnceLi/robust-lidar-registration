# -*- coding: utf-8 -*-
"""
m7_quadratic.py -- Section 16: does the local quadratic model at GT PREDICT the actual
local-optimum displacement?  Compare dhat=-H^-1 g with dstar from the local optimizer:
6-D / translation / rotation direction cosine, magnitude correlation, RMSE, and a
calibration slope dstar = a*dhat (a~1 ideal; a<<1 => quadratic overshoot).
"""
import os, numpy as np, pandas as pd
from scipy import stats
import s0_common as C
import m_common as M
rng=np.random.default_rng(C.RNG_SEED)
D=np.load(os.path.join(M.RESCACHE,"objective_main.npz"))
out={}
for cond in ["raw","scale","combined"]:
    dh=D[f"{cond}__dhat"]; st=D[f"{cond}__xistar"]
    for k,kn in enumerate(["p2p","p2l"]):
        a=dh[:,:,k]; b=st[:,:,k]
        cos6=np.array([M.cosine(a[i],b[i]) for i in range(len(a))])
        cost=np.array([M.cosine(a[i,:3],b[i,:3]) for i in range(len(a))])
        cosr=np.array([M.cosine(a[i,3:],b[i,3:]) for i in range(len(a))
                       if np.linalg.norm(a[i,3:])>1e-9 and np.linalg.norm(b[i,3:])>1e-9])
        ata=np.linalg.norm(a[:,:3],axis=1)*1000; atb=np.linalg.norm(b[:,:3],axis=1)*1000
        ara=np.degrees(np.linalg.norm(a[:,3:],axis=1)); arb=np.degrees(np.linalg.norm(b[:,3:],axis=1))
        # calibration slope through origin (translation vector components pooled)
        slope=np.sum(a[:,:3]*b[:,:3])/np.sum(a[:,:3]**2)
        # bootstrap slope CI
        bs=[]
        for _ in range(2000):
            ix=rng.integers(0,len(a),len(a)); bs.append(np.sum(a[ix,:3]*b[ix,:3])/np.sum(a[ix,:3]**2))
        slo,shi=np.percentile(bs,[2.5,97.5])
        # R2 of dhat predicting dstar (translation vector, with intercept-free fit)
        pred=slope*a[:,:3]; ss_res=np.sum((b[:,:3]-pred)**2); ss_tot=np.sum((b[:,:3]-b[:,:3].mean(0))**2)
        out[f"{cond}|{kn}"]=dict(
            cos6_med=float(np.median(cos6)),cos6_frac_pos=float((cos6>0).mean()),
            cos_trans_med=float(np.median(cost)),cos_trans_mean=float(cost.mean()),
            cos_rot_med=float(np.median(cosr)),
            mag_spearman_t=float(stats.spearmanr(ata,atb).statistic),
            mag_spearman_r=float(stats.spearmanr(ara,arb).statistic),
            rmse_trans_mm=float(np.sqrt(np.mean((ata-atb)**2))),
            rmse_rot_deg=float(np.sqrt(np.mean((ara-arb)**2))),
            slope=float(slope),slope_ci=[float(slo),float(shi)],R2_trans=float(1-ss_res/ss_tot),
            dhat_t_med=float(np.median(ata)),dstar_t_med=float(np.median(atb)))
        o=out[f"{cond}|{kn}"]
        print(f"[{cond:8s} {kn}] cosT med={o['cos_trans_med']:.3f} (frac+={o['cos6_frac_pos']:.2f}) "
              f"magRho_t={o['mag_spearman_t']:.3f} slope={o['slope']:.3f}[{slo:.3f},{shi:.3f}] "
              f"R2t={o['R2_trans']:.3f} RMSEt={o['rmse_trans_mm']:.1f}mm dhat={o['dhat_t_med']:.1f} dstar={o['dstar_t_med']:.1f}")
M.save_json(out,"m7_quadratic.json")
pd.DataFrame([dict(key=k,**v) for k,v in out.items()]).to_csv(os.path.join(M.RESCACHE,"m7_summary.csv"),index=False)
