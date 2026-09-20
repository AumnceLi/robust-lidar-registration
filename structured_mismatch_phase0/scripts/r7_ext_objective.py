# -*- coding: utf-8 -*-
"""r7_ext_objective.py -- P1 stationarity + P2 bounded local-opt for IV/V, frozen protocol.
Conditions raw/N1/N2/N3 use VI-FROZEN nuisance ops. No tuning on IV/V.
Scan-level multiprocessing; cKDTree forced workers=1 inside children (numerics unchanged)."""
import os
for _v in ["OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v,"1")
os.environ.setdefault("QTHREADS","4")
import sys,time
import numpy as np,pandas as pd
from concurrent.futures import ProcessPoolExecutor
import s0_common as C, m_common as M

CONDS=["raw","N1","N2","N3"]
EXT=os.path.join(M.CACHE,"ext")
_G={"OBJ":None,"br":None,"s":None,"Rse":None,"tse":None,"od":None,"meta":None}

def _init(tag):
    import os as _os
    _qt=int(_os.environ.get("QTHREADS","4"))
    _os.cpu_count=lambda:_qt   # cKDTree workers=-1 -> _qt query threads per child
    O=np.load(os.path.join(M.RESCACHE,"frozen_nuisance_ops.npz"))
    _G["OBJ"]=M.Objective(); _G["br"]=float(O["br"]); _G["s"]=float(O["s"])
    _G["Rse"]=O["Rse"]; _G["tse"]=O["tse"]
    _G["od"]=os.path.join(EXT,tag); _G["meta"]=pd.read_csv(os.path.join(EXT,f"meta_{tag}.csv"))

def _corrected(P,o,cond):
    d=(P-o)/np.linalg.norm(P-o,axis=1,keepdims=True)
    if cond=="raw": return P
    if cond=="N1": return P-_G["br"]*d
    if cond=="N2": return (_G["Rse"]@P.T).T+_G["tse"]
    return P/_G["s"]

def _scan(args):
    ii,selfidx=args; OBJ=_G["OBJ"]; meta=_G["meta"]; i=int(meta.scan.iloc[ii])
    z=np.load(os.path.join(_G["od"],f"scan_{i:04d}.npz")); P=z["aligned"].astype(np.float64)
    row=meta.iloc[ii]; o=np.array([row.ux,row.uy,row.uz])*row.range_m
    gh_s=M.grad_hess(OBJ,OBJ.M[selfidx]); sg=np.array([np.linalg.norm(gh_s["gp"]),np.linalg.norm(gh_s["gl"])])
    out={"sg":sg,"S":{}}
    for c in CONDS:
        Q=_corrected(P,o,c); gh=M.grad_hess(OBJ,Q)
        d=np.column_stack([-np.linalg.pinv(gh["Hp"])@gh["gp"],-np.linalg.pinv(gh["Hl"])@gh["gl"]])
        rec=dict(J0=np.array(gh["J0"]),g=np.column_stack([gh["gp"],gh["gl"]]),
                 Hp=gh["Hp"],Hl=gh["Hl"],dhat=d)
        xs=np.zeros((6,2)); js=np.zeros(2); it=np.zeros(2); ob=np.zeros(2)
        for k,fn in enumerate([M.local_min_p2p,M.local_min_p2l]):
            r=fn(OBJ,Q); xs[:,k]=r["xi"]; js[k]=OBJ.values(Q,r["xi"])[k]; it[k]=r["iters"]; ob[k]=float(r["on_bound"])
        rec.update(xistar=xs,Jstar=js,iters=it,onbnd=ob); out["S"][c]=rec
    return ii,out

def run(tag,nw=12):
    meta=pd.read_csv(os.path.join(EXT,f"meta_{tag}.csv")); n=len(meta)
    rng=np.random.default_rng(M.RNG_SEED)
    modeln=len(M.Objective().M)
    selfidx=[rng.choice(modeln,int(meta.n.iloc[ii]),replace=False) for ii in range(n)]
    S={c:{k:[] for k in ["J0","g","Hp","Hl","dhat","xistar","Jstar","iters","onbnd"]} for c in CONDS}
    sg=[]; order=[]; t0=time.perf_counter()
    with ProcessPoolExecutor(max_workers=nw,initializer=_init,initargs=(tag,)) as ex:
        for ii,out in ex.map(_scan,[(q,selfidx[q]) for q in range(n)],chunksize=4):
            order.append(ii); sg.append(out["sg"])
            for c in CONDS:
                for k in S[c]: S[c][k].append(out["S"][c][k])
            if (ii+1)%200==0: print(f"[{tag}] {ii+1}/{n} {time.perf_counter()-t0:.0f}s",flush=True)
    idx=np.argsort(order)
    def stack(c,k): a=np.array(S[c][k]); return a[idx]
    pack={"ids":meta.scan.values,"self_gnorm":np.array(sg)[idx]}
    for c in CONDS:
        pack[f"{c}__J0"]=stack(c,"J0"); pack[f"{c}__g"]=stack(c,"g")
        pack[f"{c}__H"]=np.stack([stack(c,"Hp"),stack(c,"Hl")],axis=-1)
        pack[f"{c}__dhat"]=stack(c,"dhat"); pack[f"{c}__xistar"]=stack(c,"xistar")
        pack[f"{c}__Jstar"]=stack(c,"Jstar"); pack[f"{c}__iters"]=stack(c,"iters")
        pack[f"{c}__onbnd"]=stack(c,"onbnd")
    np.savez_compressed(os.path.join(EXT,f"ext_objective_{tag}.npz"),**pack)
    print(f"[{tag}] saved ext_objective_{tag}.npz in {time.perf_counter()-t0:.0f}s",flush=True)

if __name__=="__main__":
    args=[a for a in sys.argv[1:] if not a.isdigit()]
    nw=int([a for a in sys.argv[1:] if a.isdigit()][0]) if any(a.isdigit() for a in sys.argv[1:]) else 12
    for tag in (args or ["iv","v"]): run(tag,nw)
