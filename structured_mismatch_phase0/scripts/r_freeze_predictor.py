# -*- coding: utf-8 -*-
"""r_freeze_predictor.py -- freeze the VI-only predictor BEFORE touching IV/V."""
import os,json,hashlib
import numpy as np
import s0_common as C, m_common as M

RC=M.RESCACHE
b=np.load(os.path.join(RC,"r3_vi_base.npz"))
Vsum,Vcnt=b["Vsum"],b["Vcnt"]; vr=b["vrange"]; uv=b["uview"]
Vmean=np.divide(Vsum,Vcnt[:,:,None],out=np.zeros_like(Vsum),where=Vcnt[:,:,None]>0)
P=np.load(os.path.join(RC,"r3_predictions.npz")); kstar=int(P["kstar"]); blocks=np.load(os.path.join(RC,"r3_blocks.npy"))
sr=float(vr.std())
# support tau: VI leave-block-out nearest-training distance, 95th percentile
Dm=np.sqrt(((vr[:,None]-vr[None,:])/sr)**2+np.arccos(np.clip(uv@uv.T,-1,1))**2)
near=np.array([Dm[t,np.where(blocks!=blocks[t])[0]].min() for t in range(len(vr))])
tau=float(np.percentile(near,95))
# single VI-only magnitude scalar alpha (raw p2p translation, through origin)
OM=np.load(os.path.join(RC,"objective_main.npz"))
dh=OM["raw__dhat"][:,:,0]; xs=OM["raw__xistar"][:,:,0]
alpha=float(np.einsum("ti,ti->",dh[:,:3],xs[:,:3])/np.einsum("ti,ti->",dh[:,:3],dh[:,:3]))
ops=np.load(os.path.join(RC,"frozen_nuisance_ops.npz"))
frozen=os.path.join(RC,"VI_ONLY_PREDICTOR_FROZEN.npz")
np.savez_compressed(frozen,Vmean=Vmean,Vcnt=Vcnt,vrange=vr,uview=uv,blocks=blocks,
    kstar=np.int64(kstar),range_std=np.float64(sr),tau_support=np.float64(tau),alpha_VI=np.float64(alpha),
    br=ops["br"],s=ops["s"],Rse=ops["Rse"],tse=ops["tse"],
    step_dt=ops["step_dt"],step_Rd=ops["step_Rd"],step_g=ops["step_g"],step_br=ops["step_br"])
sha=hashlib.sha256(open(frozen,"rb").read()).hexdigest()
meta=dict(file="VI_ONLY_PREDICTOR_FROZEN.npz",sha256=sha,k_nearest_views=kstar,
    kernel="adaptive Gaussian exp(-0.5(d/d_k)^2) over k nearest VI scans",
    distance="d^2=(dr/range_std)^2 + view_angle^2 ; range_std=%.6f m"%sr,
    tau_support=tau,tau_rule="95th pct of VI leave-block-out nearest-training distance",
    min_patch_support=3,fallback="global inverse-distance weighted VI mean",
    predicted_step="dxi=-pinv(H_nom) ghat; H_nom on nominal support cloud (no test residual)",
    alpha_VI_raw_p2p=alpha,alpha_note="single through-origin scalar fit on VI only; never refit on IV/V",
    primary_nuisance=["raw","N1","N2","N3"],N4="stress test only",seed=42,
    nc0=json.load(open(os.path.join(RC,"nc0_vi.json")))["NC0"])
json.dump(meta,open(os.path.join(RC,"VI_ONLY_PREDICTOR_FROZEN.json"),"w"),indent=1,ensure_ascii=False)
print("[frozen predictor]",frozen); print("SHA256:",sha)
print("k*=",kstar," range_std=%.4f tau_support=%.4f alpha_VI=%.4f"%(sr,tau,alpha))
