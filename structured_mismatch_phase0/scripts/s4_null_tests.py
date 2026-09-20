# -*- coding: utf-8 -*-
"""
s4_null_tests.py -- Stage 4: spatial repeatability vs two frozen null models.

Real metrics (patch = frozen k=24 target-frame patches, matrix M[scan,patch]):
  T-lag autocorrelation of per-patch median residual series (lag 1/5/10/50)
  Cross-scan patch-rank Spearman at time lag L (spatial pattern persistence)
  Similar-aspect (<30 deg) vs different-aspect (>90 deg) patch-vector Spearman
Null A : shuffle residual VALUES across points within each scan (positions fixed)
Null B : permute whole scan patch-vectors within 1-m range bins (range preserved)
N_PERM=100 for both. Effect z, percentile, permutation p=(1+#{null>=real})/(N+1).
"""
import os, numpy as np, pandas as pd
from scipy.stats import spearmanr
import s0_common as C

N_PERM=100; LAGS=(1,5,10,50); SUPP_MIN=20

def patch_lower_median(pp, r, k=24):
    """Vectorised lower-median of r per patch id pp (length k); NaN if empty."""
    order=np.lexsort((r,pp)); ps=pp[order]; rs=r[order]
    cnt=np.bincount(ps,minlength=k); csum=np.cumsum(cnt)
    starts=np.r_[0,csum[:-1]]
    out=np.full(k,np.nan)
    nz=cnt>0
    out[nz]=rs[starts[nz]+(cnt[nz]-1)//2]
    out[cnt<SUPP_MIN]=np.nan
    return out

def patch_mean(pp,r,k=24):
    cnt=np.bincount(pp,minlength=k).astype(float)
    sm=np.bincount(pp,weights=r,minlength=k)
    out=np.full(k,np.nan); ok=cnt>=SUPP_MIN; out[ok]=sm[ok]/cnt[ok]; return out

def lag_autocorr(M,lags):
    out={}
    for L in lags:
        vals=[]
        for k in range(M.shape[1]):
            a=M[:-L,k]; b=M[L:,k]; ok=np.isfinite(a)&np.isfinite(b)
            if ok.sum()>30 and np.std(a[ok])>1e-9 and np.std(b[ok])>1e-9:
                vals.append(np.corrcoef(a[ok],b[ok])[0,1])
        out[L]=float(np.nanmean(vals))
    return out

def lag_rank_spearman(M,L):
    vals=[]
    for i in range(M.shape[0]-L):
        a,b=M[i],M[i+L]; ok=np.isfinite(a)&np.isfinite(b)
        if ok.sum()>=8:
            vals.append(spearmanr(a[ok],b[ok]).statistic)
    return float(np.nanmean(vals))

def main():
    rng=np.random.default_rng(C.RNG_SEED)
    per=pd.read_csv(os.path.join(C.RESULTS,"residual_per_scan.csv"))
    pp_cache=[]; r_cache=[]
    pz=np.load(os.path.join(C.CACHE,"patches.npz")); plab=pz["lab"]
    K=24
    for i in C.scan_ids():
        z=np.load(os.path.join(C.CACHE,"scans",f"scan_{i:04d}.npz"))
        pp_cache.append(plab[z["nnidx"]]); r_cache.append(z["r"].astype(np.float64))
    M=np.array([patch_lower_median(pp_cache[i],r_cache[i],K) for i in range(501)])
    rng_m = per.range_m.values

    # aspect groups from GT rotations (GT used for analysis grouping only)
    Rs=[C.quat_to_R(C.load_pose(i)[2]) for i in range(501)]
    def aspect_pair_spearman(mode, nref=60):
        vals=[]; idxs=rng.choice(501,size=min(nref,501),replace=False)
        for ii in idxs:
            ang=np.array([C.geodesic_deg(Rs[ii],Rs[j]) for j in range(501)])
            dr=np.abs(rng_m-rng_m[ii])
            if mode=="sim": cand=np.where((ang<30)&(dr<1.0))[0]
            else:           cand=np.where((ang>90)&(dr<1.0))[0]
            cand=cand[cand!=ii]
            if len(cand)==0: continue
            for j in cand[:8]:
                a,b=M[ii],M[j]; ok=np.isfinite(a)&np.isfinite(b)
                if ok.sum()>=8: vals.append(spearmanr(a[ok],b[ok]).statistic)
        return float(np.nanmean(vals)), len(vals)
    sim_real,sim_n = aspect_pair_spearman("sim")
    dif_real,dif_n = aspect_pair_spearman("dif")

    real_ac=lag_autocorr(M,LAGS)
    real_rs={L:lag_rank_spearman(M,L) for L in LAGS}

    # ---------- Null A: within-scan value shuffle
    nullA={"ac":{L:[] for L in LAGS},"rs":{L:[] for L in LAGS},"sim":[],"dif":[]}
    for b in range(N_PERM):
        Mb=[]
        for i in range(501):
            rr=r_cache[i].copy(); rng.shuffle(rr)
            Mb.append(patch_lower_median(pp_cache[i],rr,K))
        Mb=np.array(Mb)
        ac=lag_autocorr(Mb,LAGS)
        for L in LAGS:
            nullA["ac"][L].append(ac[L]); nullA["rs"][L].append(lag_rank_spearman(Mb,L))
        # aspect comparisons under same grouping, shuffled matrix
        for mode,key in (("sim","sim"),("dif","dif")):
            vals=[]; idxs=range(0,501,9)
            for ii in idxs:
                ang=np.array([C.geodesic_deg(Rs[ii],Rs[j]) for j in range(501)])
                dr=np.abs(rng_m-rng_m[ii])
                cand=np.where(((ang<30) if mode=="sim" else (ang>90))&(dr<1.0))[0]
                cand=cand[cand!=ii][:4]
                for j in cand:
                    a,bb=Mb[ii],Mb[j]; ok=np.isfinite(a)&np.isfinite(bb)
                    if ok.sum()>=8: vals.append(spearmanr(a[ok],bb[ok]).statistic)
            nullA[key].append(np.nanmean(vals))
        if b%20==0: print(f"  NullA {b}/{N_PERM}")

    # ---------- Null B: range-bin scan-vector permutation
    bins=np.floor(rng_m).astype(int)
    nullB={"ac":{L:[] for L in LAGS},"rs":{L:[] for L in LAGS},"sim":[],"dif":[]}
    for b in range(N_PERM):
        perm=np.arange(501)
        for bn in np.unique(bins):
            ix=np.where(bins==bn)[0]; perm[ix]=rng.permutation(ix)
        Mb=M[perm]
        ac=lag_autocorr(Mb,LAGS)
        for L in LAGS:
            nullB["ac"][L].append(ac[L]); nullB["rs"][L].append(lag_rank_spearman(Mb,L))
        # aspect: re-derive pairs but take vectors from permuted matrix
        for mode,key in (("sim","sim"),("dif","dif")):
            vals=[]
            for ii in range(0,501,9):
                ang=np.array([C.geodesic_deg(Rs[ii],Rs[j]) for j in range(501)])
                dr=np.abs(rng_m-rng_m[ii])
                cand=np.where(((ang<30) if mode=="sim" else (ang>90))&(dr<1.0))[0]
                cand=cand[cand!=ii][:4]
                for j in cand:
                    a,bb=Mb[ii],Mb[perm[j]]; ok=np.isfinite(a)&np.isfinite(bb)
                    if ok.sum()>=8: vals.append(spearmanr(a[ok],bb[ok]).statistic)
            nullB[key].append(np.nanmean(vals))
    print("  NullB done")

    rows=[]
    def add(test,nullname,comp,realv,nulldist,notes=""):
        nd=np.array(nulldist,float); mu,sd=nd.mean(),nd.std(ddof=1)
        z=(realv-mu)/sd if sd>1e-12 else np.nan
        pct=float((nd<realv).mean()*100)
        pval=(1+np.sum(nd>=realv))/(N_PERM+1)
        rows.append(dict(test_name=test,null_model=nullname,lag_or_comparison=comp,
            real_value=realv,null_mean=mu,null_std=sd,effect_size_z=z,percentile=pct,
            p_value=pval,n_permutations=N_PERM,notes=notes))
    for L in LAGS:
        add(f"temporal_autocorr_patchmedian","NullA_within_scan_shuffle",f"lag{L}",real_ac[L],nullA["ac"][L])
        add(f"temporal_autocorr_patchmedian","NullB_rangebin_permute",f"lag{L}",real_ac[L],nullB["ac"][L])
        add(f"cross_scan_patch_rank_spearman","NullA_within_scan_shuffle",f"lag{L}",real_rs[L],nullA["rs"][L])
        add(f"cross_scan_patch_rank_spearman","NullB_rangebin_permute",f"lag{L}",real_rs[L],nullB["rs"][L])
    add("aspect_patch_rank_spearman_similar","NullA_within_scan_shuffle","aspect<30deg",sim_real,nullA["sim"],f"n_pairs={sim_n}")
    add("aspect_patch_rank_spearman_similar","NullB_rangebin_permute","aspect<30deg",sim_real,nullB["sim"],f"n_pairs={sim_n}")
    add("aspect_patch_rank_spearman_different","NullA_within_scan_shuffle","aspect>90deg",dif_real,nullA["dif"],f"n_pairs={dif_n}")
    add("aspect_patch_rank_spearman_different","NullB_rangebin_permute","aspect>90deg",dif_real,nullB["dif"],f"n_pairs={dif_n}")
    df=pd.DataFrame(rows); df.to_csv(os.path.join(C.RESULTS,"null_tests.csv"),index=False)

    # per-scan spatial consistency with cross-scan mean patch profile (for regressions)
    prof=np.nanmean(M,axis=0)
    sps=np.array([spearmanr(M[i][np.isfinite(M[i])],prof[np.isfinite(M[i])]).statistic
                  if np.isfinite(M[i]).sum()>=8 else np.nan for i in range(501)])
    np.savez_compressed(os.path.join(C.CACHE,"patch_matrix.npz"),M=M,profile=prof,sps=sps)
    print(df.round(4).to_string(index=False))
    print(f"[sps] per-scan profile-consistency Spearman mean={np.nanmean(sps):.3f} "
          f"min={np.nanmin(sps):.3f} max={np.nanmax(sps):.3f}")

if __name__=="__main__":
    main()
