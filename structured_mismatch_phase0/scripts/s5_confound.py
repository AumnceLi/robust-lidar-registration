# -*- coding: utf-8 -*-
"""
s5_confound.py -- Stage 5: can range / point_count / FOV explain the anomaly?

(a) per-scan Pearson/Spearman correlations of mismatch metrics with confounds
(b) OLS mismatch ~ range + point_count + fov_fraction ; R^2 and coefficient 95% CI
(c) THE key K2 test at patch level:
      A: patch_median ~ range + point_count + fov + support
      B: A + patch fixed effects (24 one-hot)
    partial R^2 of patch identity = structure NOT explained by confounds.
Bootstrap 95% CI (B=2000) for partial R^2. Writes results/confound_control.csv.
"""
import os, numpy as np, pandas as pd
from scipy import stats
import s0_common as C

def ols(X,y,names):
    Xd=np.column_stack([np.ones(len(y)),X])
    beta,*_=np.linalg.lstsq(Xd,y,rcond=None)
    yhat=Xd@beta; res=y-yhat; n,p=Xd.shape
    s2=(res@res)/(n-p); cov=s2*np.linalg.inv(Xd.T@Xd); se=np.sqrt(np.diag(cov))
    tcrit=stats.t.ppf(0.975,n-p); r2=1-(res@res)/(((y-y.mean())@(y-y.mean())))
    rows=[]
    for nm,b,s in zip(["intercept"]+names,beta,se):
        rows.append((nm,b,b-tcrit*s,b+tcrit*s,2*stats.t.sf(abs(b/s),n-p)))
    return r2,beta,rows

def design(df,cols,std=True):
    X=df[cols].values.astype(float)
    sd=X.std(0)
    keep=sd>1e-12                      # drop zero-variance confounds (FOV=0 on all VI scans)
    X=X[:,keep]; cols=[c for c,k in zip(cols,keep) if k]
    if std: X=(X-X.mean(0))/X.std(0)
    return X,cols

def main():
    per=pd.read_csv(os.path.join(C.RESULTS,"residual_per_scan.csv"))
    pm=np.load(os.path.join(C.CACHE,"patch_matrix.npz")); sps=pm["sps"]
    per["sps"]=sps
    conf=["range_m","point_count","model_fov_trunc_frac"]
    metrics=["median_residual_m","p95_residual_m","excess_return_fraction",
             "r4_structured_frac","missing_proxy","sps"]
    rows=[]
    # (a) correlations
    for m in metrics:
        sub=per[[m]+conf].dropna()
        for c in conf:
            if sub[c].std()<1e-12: continue
            rp=stats.pearsonr(sub[m],sub[c]); rs=stats.spearmanr(sub[m],sub[c])
            rows.append(dict(analysis="correlation",target=m,predictor=c,
                coef=rp.statistic,ci_low=np.nan,ci_high=np.nan,p_value=rp.pvalue,
                model_r2=np.nan,partial_r2=np.nan,
                notes=f"spearman={rs.statistic:.3f}"))
    # (b) per-scan OLS
    for m in metrics:
        sub=per[[m]+conf].dropna()
        X,cn=design(sub,conf); r2,beta,rr=ols(X,sub[m].values,cn)
        for nm,b,lo,hi,pv in rr:
            rows.append(dict(analysis="ols_perscan",target=m,predictor=nm,coef=b,
                ci_low=lo,ci_high=hi,p_value=pv,model_r2=r2,partial_r2=np.nan,notes=""))
    # (c) patch-level fixed effects
    pp=pd.read_csv(os.path.join(C.RESULTS,"patch_persistence.csv"))
    d=pp.dropna(subset=["median_residual"]).copy()
    d=d[d.support_count>=20]
    d=d.merge(per[["scan_id","point_count","model_fov_trunc_frac"]],on="scan_id")
    base=["range_m","point_count","model_fov_trunc_frac","support_count"]
    Xa,base=design(d,base)
    patch_oh=pd.get_dummies(d.patch_id,prefix="p").values[:,1:].astype(float)
    Xb=np.column_stack([Xa,patch_oh])
    ya=d.median_residual.values
    r2a,_,_=ols(Xa,ya,base); r2b,_,_=ols(Xb,ya,base+[f"p{k}" for k in range(patch_oh.shape[1])])
    pr2=(r2b-r2a)/(1-r2a)
    # bootstrap CI for partial R2
    rng=np.random.default_rng(C.RNG_SEED); boots=[]
    idx_all=np.arange(len(ya))
    for b in range(2000):
        ix=rng.choice(idx_all,len(idx_all),replace=True)
        try:
            ra,_,_=ols(Xa[ix],ya[ix],base); rb,_,_=ols(Xb[ix],ya[ix],base)
            boots.append((rb-ra)/(1-ra))
        except np.linalg.LinAlgError: pass
    lo,hi=np.percentile(boots,[2.5,97.5])
    rows.append(dict(analysis="patch_fixed_effect",target="patch_median_residual",
        predictor="PATCH_ID(23 dof)",coef=np.nan,ci_low=lo,ci_high=hi,p_value=np.nan,
        model_r2=r2b,partial_r2=pr2,
        notes=f"confound-only R2={r2a:.4f}; +patch R2={r2b:.4f}; n_cells={len(ya)}"))
    # variance of patch profile itself (cross-scan mean patch medians)
    prof=pm["profile"]
    rows.append(dict(analysis="patch_profile_spread",target="cross_scan_patch_profile",
        predictor="patch_id",coef=np.nan,ci_low=np.nan,ci_high=np.nan,p_value=np.nan,
        model_r2=np.nan,partial_r2=np.nan,
        notes=f"profile min={np.nanmin(prof)*1000:.1f}mm max={np.nanmax(prof)*1000:.1f}mm "
              f"std={np.nanstd(prof)*1000:.1f}mm CV={np.nanstd(prof)/np.nanmean(prof):.3f}"))
    df=pd.DataFrame(rows); df.to_csv(os.path.join(C.RESULTS,"confound_control.csv"),index=False)
    print(f"[K2] confound-only R2={r2a:.4f}  +patch R2={r2b:.4f}  partial R2={pr2:.4f} "
          f"95%CI[{lo:.4f},{hi:.4f}]")
    print(df[df.analysis=="ols_perscan"].groupby("target").model_r2.first().round(4))
    print("[corr with range]",
          {m:round(stats.pearsonr(per[m],per.range_m).statistic,3) for m in metrics})

if __name__=="__main__":
    main()




