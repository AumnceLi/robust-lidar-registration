# -*- coding: utf-8 -*-
"""
r3_vi_template.py  -- VI-ONLY NON-CIRCULAR predictor + NC0 gate (must pass BEFORE IV/V).

Design (locked in FROZEN_REPLICATION_MANIFEST.yaml):
  * Train/define on VI only. For held-out scan t we use ONLY:
      - its GT viewing geometry (pose -> view direction/range) and per-point NN model
        indices/patch labels (GEOMETRY, allowed), and nominal CAD;
      - a mismatch template learned from OTHER VI scans.
    We NEVER use scan t's own residual vector/magnitude.
  * Per frozen patch j, view-conditioned mean mismatch 3-vector mu_j(z), z=(range, view dir),
    estimated by k-nearest-view Gaussian-kernel local average over training scans.
  * Predicted cloud Qhat_i = m_nn(i) + mu_{j(i)}(z_t); ghat = grad J(Qhat) at GT;
    dxi_hat = -pinv(H_nom) ghat, H_nom = Hessian on the NOMINAL support cloud m_nn(i).
  * Protocol A: hold out t and [t-10,t+10]. Protocol B: hold out whole orientation block.
"""
import os, sys, time, json
import numpy as np
import s0_common as C, m_common as M

rng = np.random.default_rng(M.RNG_SEED)
OBJ = M.Objective()
MODEL = OBJ.M
PLAB = np.load(os.path.join(M.CACHE,"patches.npz"))["lab"]   # frozen MODEL-point patch 0..23
N = M.N_SCANS; KP = 24
BASE = os.path.join(M.RESCACHE, "r3_vi_base.npz")

# ------------------------------------------------------------ 1. per-scan patch sums + views
def build_base():
    plab=np.load(os.path.join(M.CACHE,"patches.npz"))["lab"]   # MODEL-point frozen patch 0..23
    Vsum = np.zeros((N,KP,3)); Vcnt = np.zeros((N,KP)); Ssum=np.zeros((N,KP))
    rng_ = np.zeros(N); uvw = np.zeros((N,3))
    for t in range(N):
        sc = M.load_scan(t); P=sc["aligned"]; nn=sc["nnidx"]
        lab = plab[nn]                        # scan-point patch = model patch of its NN (frozen)
        v = P - MODEL[nn]                     # 3D mismatch vector (target frame)
        s = sc["signed"]
        for j in range(KP):
            msk = lab==j
            if msk.any():
                Vsum[t,j]=v[msk].sum(0); Vcnt[t,j]=msk.sum(); Ssum[t,j]=s[msk].sum()
        _,tt,q = C.load_pose(t); R=C.quat_to_R(q)
        o = -R.T@tt; rng_[t]=np.linalg.norm(o); uvw[t]=o/rng_[t]
        if (t+1)%100==0: print("base",t+1,"/",N,flush=True)
    np.savez_compressed(BASE,Vsum=Vsum,Vcnt=Vcnt,Ssum=Ssum,vrange=rng_,uview=uvw)
    print("[base] saved",BASE,flush=True)

def load_base():
    z=np.load(BASE); return z["Vsum"],z["Vcnt"],z["Ssum"],z["vrange"],z["uview"]

# view distance: standardized range + geodesic view angle
def view_distance_matrix(vrange,uview):
    sr = vrange.std()
    dr = (vrange[:,None]-vrange[None,:])/sr
    cosang = np.clip(uview@uview.T,-1,1); ang=np.arccos(cosang)
    D=np.sqrt(dr**2+ang**2)
    return D

def orientation_blocks(uview,K=6):
    """Temporally contiguous blocks cut by cumulative view-direction travel (VI only)."""
    step=np.zeros(N)
    for t in range(1,N):
        step[t]=np.arccos(np.clip(uview[t-1]@uview[t],-1,1))
    total=step.sum(); cut=total/K; blocks=np.zeros(N,int); acc=0.0; b=0
    for t in range(N):
        acc+=step[t]
        if acc>cut and b<K-1: b+=1; acc=0.0
        blocks[t]=b
    return blocks

# ------------------------------------------------------------ 2. template + prediction for one scan
def template_for(t, train_idx, order, D, k, Vmean, Vcnt, min_support=3):
    """mu_j(z_t): kernel local average over k nearest TRAIN scans (order excludes embargo)."""
    trainset=set(np.asarray(train_idx,int).tolist()); train_arr=np.asarray(sorted(trainset),int)
    cand = order[t]; cand=[s for s in cand if s in trainset][:k]
    cand=np.array(cand,int)
    dk = max(D[t,cand[-1]],1e-9)
    w = np.exp(-0.5*(D[t,cand]/dk)**2)          # adaptive Gaussian over k neighbours
    mu = np.zeros((KP,3)); supported=np.zeros(KP,bool)
    wc = Vcnt[cand]                              # (k,KP)
    num = np.einsum("k,kpj,kp->pj", w, Vmean[cand], (wc>0))
    den = (w[:,None]*(wc>0)).sum(0)
    ok = den>0; mu[ok]=num[ok]/den[ok,None]
    supported[ (wc>0).sum(0) >= min_support ]=True
    # fallback for unsupported patches: all train scans weighted
    if (~supported).any():
        allw = np.array([1.0/(1+D[t,s]) for s in train_arr])
        for j in np.where(~supported)[0]:
            seen=Vcnt[train_arr,j]>0
            if seen.any():
                ww=allw[seen]; vv=Vmean[train_arr[seen],j]
                mu[j]=(ww[:,None]*vv).sum(0)/ww.sum()
    return mu

def predict_scan(t, mu):
    sc=M.load_scan(t); nn=sc["nnidx"]; lab=PLAB[nn]   # frozen patch via NN (geometry only)
    m_nom = MODEL[nn]                            # nominal matched points (geometry)
    Qhat = m_nom + mu[lab]                       # nominal + VI template (NO own residual)
    gh = M.grad_hess(OBJ, Qhat)                  # ghat, H on predicted cloud
    gn = M.grad_hess(OBJ, m_nom)                 # H on NOMINAL support cloud
    return {"p2p": -np.linalg.pinv(gn["Hp"])@gh["gp"],
            "p2l": -np.linalg.pinv(gn["Hl"])@gh["gl"]}

# ------------------------------------------------------------ 3. full protocol run
def run_protocol(mode, k, D, Vmean, Vcnt, blocks=None):
    """mode 'A': +-10 embargo; 'B': leave-block-out. Returns predicted xi (501,6,2)."""
    order=[np.argsort(D[t]) for t in range(N)]
    dhat=np.zeros((N,6,2)); cover=np.zeros(N)
    t0=time.perf_counter()
    for t in range(N):
        if mode=="A":
            embargo=set(range(max(0,t-10),min(N,t+11)))
            train=np.array([s for s in range(N) if s not in embargo],int)
        else:
            b=blocks[t]; train=np.where(blocks!=b)[0]
        mu=template_for(t,train,order,D,k,Vmean,Vcnt)
        pr=predict_scan(t,mu)
        dhat[t,:,0]=pr["p2p"]; dhat[t,:,1]=pr["p2l"]; cover[t]=np.isfinite(mu).all()
        if (t+1)%100==0: print(f"  [{mode} k={k}] {t+1}/{N} {time.perf_counter()-t0:.0f}s",flush=True)
    return dhat,cover

def main():
    if not os.path.exists(BASE): build_base()
    Vsum,Vcnt,Ssum,vrange,uview=load_base()
    Vmean=np.divide(Vsum,Vcnt[:,:,None],out=np.zeros_like(Vsum),where=Vcnt[:,:,None]>0)
    D=view_distance_matrix(vrange,uview)
    blocks=orientation_blocks(uview,K=6)
    np.save(os.path.join(M.RESCACHE,"r3_viewdist.npy"),D)
    np.save(os.path.join(M.RESCACHE,"r3_blocks.npy"),blocks)
    print("[blocks] sizes",np.bincount(blocks),flush=True)

    # observed local optima (frozen, bounded)
    OM=np.load(os.path.join(M.RESCACHE,"objective_main.npz"))
    xistar={c:OM[f"{c}__xistar"] for c in ["raw","scale","combined"]}

    # ---- hyperparameter k chosen INSIDE VI via Protocol-A median translation cosine (p2p raw)
    kgrid=[8,16,32,64]; scores={}
    saved={}
    for k in kgrid:
        dhat,cov=run_protocol("A",k,D,Vmean,Vcnt)
        saved[k]=dhat
        cosv=np.array([M.cosine(dhat[t,:3,0],xistar["raw"][t,:3,0])
                       if np.linalg.norm(dhat[t,:3,0])>1e-12 else np.nan for t in range(N)])
        scores[k]=float(np.nanmedian(cosv))
        print(f"[k={k}] Protocol-A median cos(raw,p2p)={scores[k]:.4f}",flush=True)
    kstar=max(scores,key=scores.get)
    print("[k* chosen in VI] =",kstar,"scores=",scores,flush=True)
    dhatA=saved[kstar]

    # Protocol B with chosen k
    dhatB,covB=run_protocol("B",kstar,D,Vmean,Vcnt,blocks)

    np.savez_compressed(os.path.join(M.RESCACHE,"r3_predictions.npz"),
                        dhatA=dhatA,dhatB=dhatB,kstar=kstar,
                        coverA=np.ones(N),coverB=covB,
                        kscores=np.array([scores[k] for k in kgrid]),kgrid=np.array(kgrid))
    print("[saved] r3_predictions.npz k*=",kstar,flush=True)

if __name__=="__main__":
    main()
