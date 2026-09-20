# -*- coding: utf-8 -*-
"""
m_common.py -- Final Rescue Audit common numerical core.

FRAME CONVENTION (locked, identical to s0_common/s1):
  Everything lives in the TARGET (= nominal CAD model) frame.
  For scan t the GT-aligned real return cloud P_t (cache/scans/scan_XXXX.npz["aligned"])
  already satisfies P_target = R_GT^T (P_lidar - t_GT).  At xi=0 the source cloud is
  exactly at its ground-truth physical pose relative to the nominal model M.

LOCAL POSE CHART (locked):
  xi = [tx,ty,tz, rx,ry,rz]  (translation in METRES, rotation in RADIANS, target frame)
  T(xi) P = exp([r]x) P + t                       (perturbation of the SOURCE about GT)

OBJECTIVES (frozen; NO robust loss / trimming / outlier rejection in phase 1):
  J_p2p(xi) = (1/N) sum_i ||T xi p_i - m_{j(i)}||^2
  J_p2l(xi) = (1/N) sum_i [ n_{j(i)} . (T xi p_i - m_{j(i)}) ]^2
  j(i) = nearest MODEL point, RECOMPUTED at every evaluation (KD-tree over fixed model).
  Normals are the FROZEN PCA model normals from model_cache.npz.

The model KD-tree is built ONCE (model is fixed); each objective probe is one NN query
that returns BOTH J_p2p and J_p2l under identical correspondences.
"""
import os, json
import numpy as np
from scipy.spatial import cKDTree
from scipy import stats
import s0_common as C

# ---------------------------------------------------------------- locked paths / constants
ROOT   = C.ROOT
CACHE  = C.CACHE
RESCACHE = os.path.join(CACHE, "rescue")
os.makedirs(RESCACHE, exist_ok=True)
RESULTS = C.RESULTS
REPORTS = C.REPORTS

N_SCANS = C.N_SCANS            # 501
RNG_SEED = C.RNG_SEED          # 42
# Pre-registered finite-difference step (primary) + numerical-validity alternatives
FD_T = 0.005                   # 5 mm translation FD step
FD_R = np.deg2rad(0.25)        # 0.25 deg rotation FD step
FD_T_TRY = (0.0025, 0.005, 0.010)
FD_R_TRY = tuple(np.deg2rad(a) for a in (0.125, 0.25, 0.5))
# Mandated symmetric landscape grid (Rescue Audit section 8)
GRID_T = (0.01, 0.02, 0.05)            # +/- 1,2,5 cm
GRID_R = tuple(np.deg2rad(a) for a in (0.5, 1.0, 2.0))
# Local-opt basin (grid extent); ICP from GT
BASIN_T = 0.05
BASIN_R = np.deg2rad(2.0)
EVERY5 = list(range(0, N_SCANS, 5))    # pre-registered n=101 fallback / null subset

# ================================================================ SE(3) local chart
def skew(r):
    return np.array([[0.,-r[2],r[1]],[r[2],0.,-r[0]],[-r[1],r[0],0.]])

def rodrigues(r):
    th = np.linalg.norm(r)
    if th < 1e-12:
        return np.eye(3) + skew(r)
    k = r/th; K = skew(k)
    return np.eye(3) + np.sin(th)*K + (1-np.cos(th))*(K@K)

def rodrigues_log(R):
    c = (np.trace(R)-1)/2
    c = np.clip(c,-1,1); th = np.arccos(c)
    if th < 1e-10:
        return np.array([R[2,1]-R[1,2], R[0,2]-R[2,0], R[1,0]-R[0,1]])/2
    w = np.array([R[2,1]-R[1,2], R[0,2]-R[2,0], R[1,0]-R[0,1]])
    return w*th/(2*np.sin(th))

def apply_xi(P, xi):
    t = xi[:3]; R = rodrigues(xi[3:])
    return (R@P.T).T + t

def se3_log(R, t):
    """Return xi=[trans; rotvec] for transform P' = R P + t."""
    return np.concatenate([t, rodrigues_log(R)])

# ================================================================ Objective holder
class Objective:
    def __init__(self, model=None, normals=None):
        if model is None:
            mc = np.load(os.path.join(CACHE,"model_cache.npz"))
            model = mc["xyz"].astype(np.float64)
            normals = mc["normals"].astype(np.float64)
        self.M = model
        self.nM = normals
        self.tree = cKDTree(self.M)
    def probe(self, P, xi):
        """Both objectives at T(xi)P; returns dict with scalar J's and per-point data."""
        Q = apply_xi(P, xi)
        d, idx = self.tree.query(Q, k=1, workers=-1)
        m = self.M[idx]; n = self.nM[idx]
        e = Q - m
        q2 = np.einsum("ij,ij->i", e, e)
        nd = np.einsum("ij,ij->i", n, e)
        ql = nd*nd
        return dict(Jp2p=q2.mean(), Jp2l=ql.mean(), q2=q2, ql=ql, idx=idx, e=e, Q=Q, nd=nd)
    def values(self, P, xi):
        z = self.probe(P, xi)
        return z["Jp2p"], z["Jp2l"]

# ================================================================ finite-difference g,H
def _steps(ht, hr):
    h = np.array([ht,ht,ht,hr,hr,hr]); return h

def grad_hess(obj, P, ht=FD_T, hr=FD_R):
    """Central-difference gradient and symmetric Hessian of BOTH objectives at xi=0."""
    h = _steps(ht,hr)
    Jp0, Jl0 = obj.values(P, np.zeros(6))
    gp = np.zeros(6); gl = np.zeros(6)
    Hp = np.zeros((6,6)); Hl = np.zeros((6,6))
    fwd = np.zeros((6,2)); bwd = np.zeros((6,2))
    for a in range(6):
        ep = np.zeros(6); ep[a]=h[a]
        fwd[a] = obj.values(P,  ep)
        bwd[a] = obj.values(P, -ep)
        gp[a] = (fwd[a,0]-bwd[a,0])/(2*h[a])
        gl[a] = (fwd[a,1]-bwd[a,1])/(2*h[a])
        Hp[a,a] = (fwd[a,0]+bwd[a,0]-2*Jp0)/h[a]**2
        Hl[a,a] = (fwd[a,1]+bwd[a,1]-2*Jl0)/h[a]**2
    for a in range(6):
        for b in range(a+1,6):
            ea=np.zeros(6); eb=np.zeros(6); ea[a]=h[a]; eb[b]=h[b]
            pp=np.array(obj.values(P, ea+eb)); pm=obj.values(P, ea-eb)
            mp=obj.values(P,-ea+eb); mm=obj.values(P,-ea-eb)
            den=4*h[a]*h[b]
            Hp[a,b]=Hp[b,a]=(pp[0]-pm[0]-mp[0]+mm[0])/den
            Hl[a,b]=Hl[b,a]=(pp[1]-pm[1]-mp[1]+mm[1])/den
    return dict(J0=(Jp0,Jl0), gp=gp, gl=gl, Hp=Hp, Hl=Hl, h=h)

def landscape(obj, P):
    """Mandated symmetric grid J(+/- s e_a) for both objectives (section 8)."""
    out = {"t":{}, "r":{}}
    for ax in range(3):
        for s in GRID_T:
            ep=np.zeros(6); ep[ax]=s; em=np.zeros(6); em[ax]=-s
            out["t"][(ax,float(s))]  = (obj.values(P,ep), obj.values(P,em))
        for s in GRID_R:
            ep=np.zeros(6); ep[3+ax]=s; em=np.zeros(6); em[3+ax]=-s
            out["r"][(ax,float(s))]  = (obj.values(P,ep), obj.values(P,em))
    out["zero"]=obj.values(P,np.zeros(6))
    return out

# ================================================================ local optimizers (ICP from GT)
def _basin_factor(Racc,tacc,bt,br):
    f=1.0; nt=np.linalg.norm(tacc); nr=np.linalg.norm(rodrigues_log(Racc))
    if nt>bt: f=min(f,bt/nt)
    if nr>br: f=min(f,br/nr)
    return f
def local_min_p2p(obj, P, max_iter=40, tol=1e-8, bound_t=0.30, bound_r_deg=15.0):
    """Point-to-point ICP started AT GT (xi=0), clipped to the declared local basin."""
    br_=np.deg2rad(bound_r_deg)
    Racc=np.eye(3); tacc=np.zeros(3); hist=[]; hit=False
    for it in range(max_iter):
        Q=(Racc@P.T).T+tacc
        d,idx=obj.tree.query(Q,k=1,workers=-1)
        Rdl,tdl = kabsch(Q.T, obj.M[idx].T)      # m ~= Rdl Q + tdl
        Rn=Rdl@Racc; tn=Rdl@tacc+tdl; f=_basin_factor(Rn,tn,bound_t,br_)
        if f<1.0: tacc=tacc+f*(tn-tacc); hit=True; break
        Racc,tacc=Rn,tn
        J=float(np.mean(np.sum(((Rdl@Q.T).T+tdl-obj.M[idx])**2,axis=1)))
        hist.append(J)
        if it>0 and abs(hist[-2]-J) < tol*max(1,hist[-2]): break
    xi=se3_log(Racc,tacc)
    return dict(xi=xi,R=Racc,t=tacc,hist=hist,iters=it+1,J=(hist[-1] if hist else np.nan),on_bound=hit)

def local_min_p2l(obj, P, max_iter=40, tol=1e-9, reg=1e-9, bound_t=0.30, bound_r_deg=15.0):
    """Linearized point-to-plane ICP (6-DoF Gauss-Newton) started AT GT, basin-clipped."""
    br_=np.deg2rad(bound_r_deg)
    Racc=np.eye(3); tacc=np.zeros(3); hist=[]; hit=False
    for it in range(max_iter):
        Q=(Racc@P.T).T+tacc
        d,idx=obj.tree.query(Q,k=1,workers=-1)
        m=obj.M[idx]; n=obj.nM[idx]
        # A_i delta = n.(m-Q),  A=[n^T , (Q x n)^T]
        cx=np.cross(Q,n)
        A=np.concatenate([n,cx],axis=1)
        b=np.einsum("ij,ij->i",n,m-Q)
        AtA=A.T@A + reg*np.eye(6); Atb=A.T@b
        try:
            delta=np.linalg.solve(AtA,Atb)
        except np.linalg.LinAlgError:
            delta=np.linalg.lstsq(AtA,Atb,rcond=None)[0]
        v=delta[:3]; w=delta[3:]
        Rd=rodrigues(w)
        Rn=Rd@Racc; tn=Rd@tacc+v; f=_basin_factor(Rn,tn,bound_t,br_)
        if f<1.0: tacc=tacc+f*(tn-tacc); hit=True; break
        Racc,tacc=Rn,tn
        Qn=(Rd@Q.T).T+v
        nd=np.einsum("ij,ij->i",obj.nM[idx],Qn-m)
        J=float(np.mean(nd*nd)); hist.append(J)
        if it>0 and abs(hist[-2]-J)<tol*max(1,hist[-2]): break
    xi=se3_log(Racc,tacc)
    return dict(xi=xi,R=Racc,t=tacc,hist=hist,iters=it+1,J=(hist[-1] if hist else np.nan),on_bound=hit)

def local_opt_lbfgs(obj, P, kind="p2p", bound_t=0.30, bound_r_deg=15.0,
                    maxiter=200, ht=FD_T, hr=FD_R):
    """Stationarity-convergent LOCAL optimizer started AT GT (xi=0).
    Bound is a declared local-convergence radius (NOT a global search): at 9-15 m
    range 0.30 m ~= 1.4-1.9 deg, far from the 120-deg symmetry basins. NN is
    recomputed every evaluation (no robust loss). Cross-check with the ICP
    optimisers above."""
    from scipy.optimize import minimize
    k = 0 if kind=="p2p" else 1
    hh = np.array([ht]*3+[hr]*3)
    def fg(x):
        # ONE probe set: centre + central differences, ONLY the requested objective
        f0=obj.values(P,x)[k]; g=np.zeros(6)
        for a in range(6):
            e=np.zeros(6); e[a]=hh[a]
            g[a]=(obj.values(P,x+e)[k]-obj.values(P,x-e)[k])/(2*hh[a])
        return f0,g
    J0=fg(np.zeros(6))[0]
    bnds=[(-bound_t,bound_t)]*3+[(-np.deg2rad(bound_r_deg),np.deg2rad(bound_r_deg))]*3
    r=minimize(fg,np.zeros(6),jac=True,method="L-BFGS-B",bounds=bnds,
               options=dict(maxiter=maxiter,ftol=1e-11,gtol=1e-7,maxls=8))
    xi=r.x
    on_bound = bool(np.any(np.abs(xi[:3])>0.95*bound_t) or
                    np.any(np.abs(xi[3:])>0.95*np.deg2rad(bound_r_deg)))
    fstar,gstar=fg(xi)
    return dict(xi=xi, J0=J0, Jstar=float(fstar), gnorm=float(np.linalg.norm(gstar)),
                converged=bool(r.success), nit=int(r.nit), on_bound=on_bound)

def kabsch(A,B):
    """R,t with B ~= R A + t for 3xN (local copy to avoid importing ICP code)."""
    ca,cb=A.mean(1),B.mean(1)
    Hm=(A-ca[:,None])@(B-cb[:,None]).T
    U,_,Vt=np.linalg.svd(Hm); D=np.eye(3); D[2,2]=np.sign(np.linalg.det(Vt.T@U.T))
    R=Vt.T@D@U.T
    return R, cb-R@ca

# ================================================================ stats helpers
def boot_ci(x, fn=np.mean, B=2000, seed=RNG_SEED, alpha=0.05):
    x=np.asarray(x,float); rng=np.random.default_rng(seed); n=len(x); out=np.empty(B)
    for b in range(B):
        out[b]=fn(rng.choice(x,n,replace=True))
    lo,hi=np.percentile(out,[100*alpha/2,100*(1-alpha/2)])
    return float(fn(x)),float(lo),float(hi)

def perm_p(real, null_vals):
    """p=(1+#{null>=real})/(B+1), matching s4 convention (two-sided handled by caller)."""
    null_vals=np.asarray(null_vals,float)
    return float((1+np.sum(null_vals>=real))/(len(null_vals)+1))

def hotelling(V):
    V=np.asarray(V,float); n,p=V.shape; mu=V.mean(0); S=np.cov(V.T)
    T2=n*mu@np.linalg.pinv(S)@mu
    F=(n-p)/(p*(n-1))*T2; pv=stats.f.sf(F,p,n-p)
    return mu,np.linalg.norm(mu),float(T2),float(pv)

def resultant_concentration(unit_vecs):
    """Mean resultant length of unit vectors (direction concentration); also mean dir."""
    V=np.asarray(unit_vecs,float); V=V/np.maximum(np.linalg.norm(V,axis=1,keepdims=True),1e-12)
    m=V.mean(0); Rlen=float(np.linalg.norm(m)); return Rlen, m/np.maximum(Rlen,1e-12)

def rayleigh_p(Rlen,n):
    """Rayleigh test of uniformity on S^2: Z=3n R^2, p approx exp(-Z)*(1+...)."""
    Z=3*n*Rlen**2
    p=np.exp(-Z)*(1 + (3*Z-Z**2)/(4*n) - (15*Z+7*Z**2+Z**3)/(96*n**2))
    return float(np.clip(p,0,1))

def cosine(a,b):
    return float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)+1e-15))

def load_scan(i):
    return np.load(os.path.join(CACHE,"scans",f"scan_{i:04d}.npz"))

def ray_dirs_target(i, P):
    """Target-frame lidar viewing ray for each GT-aligned point of scan i.
    lidar ray in lidar frame = (R P + t)/||.|| ; rotate back to target frame:
    R^T (R P + t)/||.|| = (P + R^T t)/||R P + t||."""
    _,t,q=C.load_pose(i); R=C.quat_to_R(q)
    pl=(R@P.T).T+t
    return (P+R.T@t)/np.linalg.norm(pl,axis=1,keepdims=True)

def save_json(obj, name):
    def conv(o):
        if isinstance(o,np.ndarray): return o.tolist()
        if isinstance(o,(np.floating,np.integer)): return o.item()
        if isinstance(o,dict): return {str(k):conv(v) for k,v in o.items()}
        if isinstance(o,(list,tuple)): return [conv(v) for v in o]
        return o
    with open(os.path.join(RESCACHE,name),"w") as f:
        json.dump(conv(obj),f,indent=1)
