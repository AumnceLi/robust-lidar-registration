# -*- coding: utf-8 -*-
"""r10_stats.py -- aggregate P1/P2 (ext_objective) and P3 (ext_predict) per trajectory,
IV and V reported SEPARATELY. Frozen block length L=5 (VI-derived), vector-pairing perm."""
import os,sys,json
import numpy as np,pandas as pd
from scipy import stats
import s0_common as C, m_common as M

EXT=os.path.join(M.CACHE,"ext"); RC=M.RESCACHE; L=5; B=2000
rng=np.random.default_rng(M.RNG_SEED)
CONDS=["raw","N1","N2","N3"]; OBJ=["p2p","p2l"]

def mb_median(v,L=L,B=B):
    v=np.asarray(v,float); v=v[np.isfinite(v)]; n=len(v); nb=int(np.ceil(n/L)); out=np.empty(B)
    for b in range(B):
        st=rng.integers(0,n,nb); out[b]=np.median(np.concatenate([v[s:s+L] for s in st]))
    return [float(x) for x in np.percentile(out,[2.5,97.5])]

def vecpair_perm(a,b,B=B):
    ok=(np.linalg.norm(a,axis=1)>1e-12)&(np.linalg.norm(b,axis=1)>1e-12); idx=np.where(ok)[0]
    def mc(ia,ib):
        x=a[ia]; y=b[ib]; return np.median(np.einsum("ti,ti->t",x,y)/(np.linalg.norm(x,axis=1)*np.linalg.norm(y,axis=1)+1e-15))
    obs=mc(idx,idx); null=np.empty(B)
    for q in range(B): null[q]=mc(idx,rng.permutation(idx))
    return float(obs),float((1+(null>=obs).sum())/(B+1))

def dirstats(pred,obs,insup):
    out={}
    for setname,sel in [("IN",insup),("OUT",~insup),("ALL",np.ones(len(obs),bool))]:
        a=pred[sel,:3]; b=obs[sel,:3]
        ok=(np.linalg.norm(a,axis=1)>1e-12)&(np.linalg.norm(b,axis=1)>1e-12); a,b=a[ok],b[ok]
        if len(a)<5: out[setname]=dict(n=int(len(a))); continue
        cosv=np.einsum("ti,ti->t",a,b)/(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)+1e-15)
        med,pp=vecpair_perm(a,b)
        out[setname]=dict(n=int(len(a)),median=float(np.median(cosv)),mean=float(cosv.mean()),
            ci_block=mb_median(cosv),frac_pos=float((cosv>0).mean()),perm_p=pp,
            mag_spearman=float(stats.spearmanr(np.linalg.norm(a,axis=1),np.linalg.norm(b,axis=1)).statistic))
    return out

def traj(tag):
    E=np.load(os.path.join(EXT,f"ext_objective_{tag}.npz")); PR=np.load(os.path.join(EXT,f"ext_predict_{tag}.npz"))
    insup=PR["insup"]; ids=E["ids"]; res=dict(tag=tag,n=int(len(ids)),n_in_support=int(insup.sum()),
        n_out_support=int((~insup).sum()),tau=float(PR["tau"]),P1={},P2={},P3={})
    # ---- P1 stationarity + P2 localopt
    for c in CONDS:
        g=E[f"{c}__g"]; sg=E["self_gnorm"]; xs=E[f"{c}__xistar"]; onb=E[f"{c}__onbnd"]
        for ki,kn in enumerate(OBJ):
            G=g[:,:,ki]; gn=np.linalg.norm(G,axis=1)
            ok=np.isfinite(gn)&(gn>1e-12)
            # Hotelling T2 on centered gradient (mean != 0)
            Gc=G[ok]; mu=Gc.mean(0); S=np.cov(Gc.T); T2=len(Gc)*mu@np.linalg.pinv(S)@mu
            p_hot=float(stats.f.sf((len(Gc)-6)/(6*(len(Gc)-1))*T2,6,len(Gc)-6))
            u=Gc/gn[ok,None]; Rconc=float(np.linalg.norm(u.mean(0)))
            res["P1"][f"{c}|{kn}"]=dict(gnorm_median=float(np.median(gn)),
                gnorm_self_median=float(np.median(sg[:,ki])),ratio=float(np.median(gn)/np.median(sg[:,ki])),
                hotelling_p=p_hot,grad_dir_concentration=Rconc)
            t=xs[:,:3,ki]*1000; r=np.degrees(xs[:,3:,ki])
            tm=np.linalg.norm(t,axis=1); rm=np.linalg.norm(r,axis=1)
            signcons=float(np.mean([(np.sign(t[:,a])==np.sign(t[:,a].mean())).mean() for a in range(3)]))
            ax=xs[:,3:,ki]; ax=ax/(np.linalg.norm(ax,axis=1,keepdims=True)+1e-15)
            res["P2"][f"{c}|{kn}"]=dict(mean_t_mm=[float(x) for x in t.mean(0)],
                med_t_mm=float(np.median(tm)),t_ci_block=mb_median(tm),
                med_r_deg=float(np.median(rm)),sign_consistency=signcons,
                rot_axis_concentration=float(np.linalg.norm(np.nanmean(ax,0))),
                on_bound_frac=float(onb[:,ki].mean()))
    # ---- P3 non-circular external direction (primary IN_SUPPORT, raw)
    pred=PR["dxi"]; obs=E["raw__xistar"]
    for ki,kn in enumerate(OBJ):
        res["P3"][kn]=dirstats(pred[:,:,ki],obs[:,:,ki],insup)
    # D1 template direction transfer (sign fixed a priori: -D1)
    d1=-PR["d1"]; res["P3"]["D1_minus"]=dirstats(d1,obs[:,:3,0],insup)
    return res

if __name__=="__main__":
    allr={}; rows=[]
    for tag in ["iv","v"]:
        r=traj(tag); allr[tag]=r; json.dump(r,open(os.path.join(RC,f"ext_stats_{tag}.json"),"w"),indent=1,ensure_ascii=False)
        for kn in ["p2p","p2l"]:
            for sn in ["IN","OUT"]:
                q=r["P3"][kn][sn]
                if q.get("n",0)<5: continue
                rows.append(dict(traj=tag,obj=kn,support=sn,n=q.get("n"),median_cos=q.get("median"),
                    ci_lo=q.get("ci_block",[None])[0],ci_hi=q.get("ci_block",[None,None])[1],
                    frac_pos=q.get("frac_pos"),perm_p=q.get("perm_p"),mag_spearman=q.get("mag_spearman")))
        print(f"== {tag} n={r['n']} IN={r['n_in_support']} OUT={r['n_out_support']}")
        for kn in ["p2p","p2l"]:
            for sn in (["IN"] if r["P3"][kn]["IN"].get("n",0)>=5 else ["OUT"]):
                q=r["P3"][kn][sn]; print(f"  P3 {kn} {sn} n={q.get('n')} med={q.get('median'):.3f} CI{[round(x,3) for x in q.get('ci_block')]} frac+={q.get('frac_pos'):.2f} p={q.get('perm_p'):.4f} magRho={q.get('mag_spearman'):.2f}")
        print("  P1 raw|p2p ratio=%.1f hotelling_p=%.2e gconc=%.3f"%(r['P1']['raw|p2p']['ratio'],r['P1']['raw|p2p']['hotelling_p'],r['P1']['raw|p2p']['grad_dir_concentration']))
        q=r['P2']['raw|p2p']; print("  P2 raw|p2p meanT=%s medT=%.1fmm CI%s sign=%.2f onb=%.3f"%([round(x,1) for x in q['mean_t_mm']],q['med_t_mm'],[round(x,1) for x in q['t_ci_block']],q['sign_consistency'],q['on_bound_frac']))
    pd.DataFrame(rows).to_csv(os.path.join(C.REPORTS,"trajectory_summary.csv"),index=False)
    json.dump(allr,open(os.path.join(RC,"ext_stats_all.json"),"w"),indent=1,ensure_ascii=False)
    print("[saved] ext_stats_*.json, trajectory_summary.csv")
