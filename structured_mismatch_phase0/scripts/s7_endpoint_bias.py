# -*- coding: utf-8 -*-
"""
s7_endpoint_bias.py -- Stage 6 (endpoint association regression) +
Stage 7 (bias vs variance). Runs AFTER s6_baseline.py produced baseline_endpoints.csv.

Endpoint association (frozen baseline endpoints, GT used only for scoring):
  tErr/aErr ~ z(range)+z(point_count)+z(excess_fraction)+z(spatial_profile_consistency)
  partial R^2 of the mismatch block, standardised coefficients, 95% CI.

Bias vs variance: high/low mismatch groups by median excess_fraction;
Hotelling T^2 test of the 3-D translation-error-vector mean (target frame);
rotation-error-axis concentration; half1/half2 direction repeatability (cosine).
"""
import os, numpy as np, pandas as pd
from scipy import stats
import s0_common as C

def ols_full(X,y,names):
    Xd=np.column_stack([np.ones(len(y)),X]); n,p=Xd.shape
    beta,*_=np.linalg.lstsq(Xd,y,rcond=None); res=y-Xd@beta
    s2=res@res/(n-p); cov=s2*np.linalg.inv(Xd.T@Xd); se=np.sqrt(np.diag(cov))
    tc=stats.t.ppf(.975,n-p); r2=1-res@res/((y-y.mean())@(y-y.mean()))
    out=pd.DataFrame(dict(predictor=["intercept"]+names,coef=beta,se=se,
                          ci_low=beta-tc*se,ci_high=beta+tc*se,
                          pval=2*stats.t.sf(np.abs(beta/se),n-p)))
    return r2,out

def partial_r2_block(df,ycol,base_cols,block_cols):
    d=df[[ycol]+base_cols+block_cols].dropna()
    def R2(cols):
        X=d[cols].values; X=(X-X.mean(0))/X.std(0)
        Xd=np.column_stack([np.ones(len(d)),X]); b,*_=np.linalg.lstsq(Xd,d[ycol].values,rcond=None)
        r=d[ycol].values-Xd@b; return 1-r@r/((d[ycol].values-d[ycol].mean())**2).sum()
    r_base=R2(base_cols); r_full=R2(base_cols+block_cols)
    pr2=(r_full-r_base)/(1-r_base)
    # bootstrap CI
    rng=np.random.default_rng(C.RNG_SEED); bs=[]
    ix=np.arange(len(d))
    def R2ix(cols,ii):
        X=d[cols].values[ii]; X=(X-X.mean(0))/X.std(0)
        Xd=np.column_stack([np.ones(len(ii)),X]); b,*_=np.linalg.lstsq(Xd,d[ycol].values[ii],rcond=None)
        r=d[ycol].values[ii]-Xd@b; return 1-r@r/((d[ycol].values[ii]-d[ycol].values[ii].mean())**2).sum()
    for _ in range(2000):
        ii=rng.choice(ix,len(ix),replace=True)
        try:
            rb=R2ix(base_cols,ii); rf=R2ix(base_cols+block_cols,ii); bs.append((rf-rb)/(1-rb))
        except np.linalg.LinAlgError: pass
    lo,hi=np.percentile(bs,[2.5,97.5])
    return r_base,r_full,pr2,lo,hi,len(d)

def hotelling(v):
    n,p=v.shape; mu=v.mean(0); S=np.cov(v.T)
    T2=n*mu@np.linalg.pinv(S)@mu
    F=(n-p)/(p*(n-1))*T2; pv=stats.f.sf(F,p,n-p)
    return mu,np.linalg.norm(mu),T2,pv

def bias_block(df,name,vec_cols=("terr_vec_target_x","terr_vec_target_y","terr_vec_target_z"),
               ax_cols=("rot_err_axis_x","rot_err_axis_y","rot_err_axis_z")):
    v=df[list(vec_cols)].values
    mu,bnorm,T2,pv=hotelling(v)
    ax=df[list(ax_cols)].values; axmean=ax.mean(0); conc=np.linalg.norm(axmean); axmean=axmean/max(conc,1e-12)
    return dict(analysis=name,group=name,n_scans=len(df),
        mean_translation_error_m=df.translation_error_m.mean(),
        std_translation_error_m=df.translation_error_m.std(ddof=1),
        mean_bias_vector_x=mu[0],mean_bias_vector_y=mu[1],mean_bias_vector_z=mu[2],
        bias_vector_norm_m=bnorm,bias_significance_p=pv,
        mean_attitude_error_deg=df.attitude_error_deg.mean(),
        std_attitude_error_deg=df.attitude_error_deg.std(ddof=1),
        rotation_bias_axis_x=axmean[0],rotation_bias_axis_y=axmean[1],rotation_bias_axis_z=axmean[2],
        axis_concentration=conc)

def main():
    ep=pd.read_csv(os.path.join(C.RESULTS,"baseline_endpoints.csv"))
    per=pd.read_csv(os.path.join(C.RESULTS,"residual_per_scan.csv"))
    sps=np.load(os.path.join(C.CACHE,"patch_matrix.npz"))["sps"]
    per["sps"]=sps
    d=ep.merge(per[["scan_id","excess_return_fraction","r4_structured_frac","sps"]],on="scan_id")
    d=d.dropna(subset=["sps"])
    z=lambda c:(d[c]-d[c].mean())/d[c].std()
    for c in ["range_m","point_count","excess_return_fraction","r4_structured_frac","sps"]:
        d["z_"+c]=z(c)

    # ---------- endpoint association
    rows=[]
    for ycol in ["translation_error_m","attitude_error_deg"]:
        base=["z_range_m","z_point_count"]
        blocks={"excess":["z_excess_return_fraction"],
                "sps":["z_sps"],
                "mismatch_block":["z_excess_return_fraction","z_sps","z_r4_structured_frac"]}
        rb,rf,pr2,lo,hi,n=partial_r2_block(d,ycol,
            ["range_m","point_count"],
            ["excess_return_fraction","sps","r4_structured_frac"])
        rows.append(dict(endpoint=ycol,term="mismatch_block_partialR2",coef=pr2,
                         ci_low=lo,ci_high=hi,p_value=np.nan,base_R2=rb,full_R2=rf,n=n))
        cols=["z_range_m","z_point_count","z_excess_return_fraction","z_r4_structured_frac","z_sps"]
        r2,tb=ols_full(d[cols].values,d[ycol].values,
                       ["range","point_count","excess_fraction","r4_structured_frac","spatial_persistence"])
        for _,r in tb.iterrows():
            rows.append(dict(endpoint=ycol,term=r.predictor,coef=r.coef,ci_low=r.ci_low,
                             ci_high=r.ci_high,p_value=r.pval,base_R2=np.nan,full_R2=r2,n=len(d)))
    # convergence: linear probability model
    cols=["z_range_m","z_point_count","z_excess_return_fraction","z_sps"]
    r2,tb=ols_full(d[cols].values,d.converged.values.astype(float),
                   ["range","point_count","excess_fraction","spatial_persistence"])
    for _,r in tb.iterrows():
        rows.append(dict(endpoint="converged(LPM)",term=r.predictor,coef=r.coef,ci_low=r.ci_low,
                         ci_high=r.ci_high,p_value=r.pval,base_R2=np.nan,full_R2=r2,n=len(d)))
    pd.DataFrame(rows).to_csv(os.path.join(C.RESULTS,"endpoint_association.csv"),index=False)
    print("[endpoint association]"); print(pd.DataFrame(rows).round(4).to_string(index=False))

    # robustness: same regressions on the ICP-locked subset (icp_fitness>0.5, n~36)
    rows_r=[]
    dl=d[d.icp_fitness>0.5]
    for ycol in ["translation_error_m","attitude_error_deg"]:
        rb,rf,pr2,lo,hi,n=partial_r2_block(dl,ycol,["range_m","point_count"],
                                           ["excess_return_fraction","sps","r4_structured_frac"])
        rows_r.append(dict(subset=f"icp_locked n={n}",endpoint=ycol,mismatch_partialR2=pr2,
                           ci_low=lo,ci_high=hi,base_R2=rb,full_R2=rf))
    pd.DataFrame(rows_r).to_csv(os.path.join(C.RESULTS,"endpoint_association_robust.csv"),index=False)
    print("[robust icp-locked]"); print(pd.DataFrame(rows_r).round(4).to_string(index=False))

    # ---------- bias vs variance
    med=d.excess_return_fraction.median()
    hi=d[d.excess_return_fraction>med]; lo=d[d.excess_return_fraction<=med]
    b=[bias_block(d,"ALL"),bias_block(hi,"HIGH_mismatch(excess>median)"),
       bias_block(lo,"LOW_mismatch(excess<=median)")]
    # half1/half2 repeatability on the high-mismatch group
    h1=hi[hi.scan_id<=250]; h2=hi[hi.scan_id>250]
    b1=bias_block(h1,"HIGH_half1(scan<=250)"); b2=bias_block(h2,"HIGH_half2(scan>250)")
    v1=np.array([b1["mean_bias_vector_x"],b1["mean_bias_vector_y"],b1["mean_bias_vector_z"]])
    v2=np.array([b2["mean_bias_vector_x"],b2["mean_bias_vector_y"],b2["mean_bias_vector_z"]])
    cos=float(v1@v2/(np.linalg.norm(v1)*np.linalg.norm(v2)+1e-12))
    a1=np.array([b1["rotation_bias_axis_x"],b1["rotation_bias_axis_y"],b1["rotation_bias_axis_z"]])
    a2=np.array([b2["rotation_bias_axis_x"],b2["rotation_bias_axis_y"],b2["rotation_bias_axis_z"]])
    cos_ax=float(a1@a2/(np.linalg.norm(a1)*np.linalg.norm(a2)+1e-12))
    for r in b+[b1,b2]:
        r["half1_half2_bias_cosine"]=np.nan; r["notes"]=f"excess_median_split={med:.4f}"
    bdf=pd.DataFrame(b+[b1,b2])
    bdf.loc[bdf.group=="HIGH_half2(scan>250)","half1_half2_bias_cosine"]=cos
    bdf["half1_half2_axis_cosine"]=np.nan
    bdf.loc[bdf.group=="HIGH_half2(scan>250)","half1_half2_axis_cosine"]=cos_ax
    # robustness grouping by r4_structured_frac (excess_fraction is ~0 for most scans)
    med4=d.r4_structured_frac.median()
    h4=d[d.r4_structured_frac>med4]; l4=d[d.r4_structured_frac<=med4]
    b4h=bias_block(h4,"ROBUST HIGH r4>median"); b4l=bias_block(l4,"ROBUST LOW r4<=median")
    b4h["half1_half2_bias_cosine"]=np.nan; b4l["half1_half2_bias_cosine"]=np.nan
    b4h["half1_half2_axis_cosine"]=np.nan; b4l["half1_half2_axis_cosine"]=np.nan
    b4h["notes"]=f"r4_median_split={med4:.4f}"; b4l["notes"]=f"r4_median_split={med4:.4f}"
    bdf=pd.concat([bdf,pd.DataFrame([b4h,b4l])],ignore_index=True)
    bdf.to_csv(os.path.join(C.RESULTS,"bias_variance.csv"),index=False)
    print("\n[bias vs variance]"); print(bdf.round(4).to_string(index=False))
    print(f"\nhalf cosine translation={cos:.3f} axis={cos_ax:.3f}")
    d.to_csv(os.path.join(C.CACHE,"endpoint_merged.csv"),index=False)

if __name__=="__main__":
    main()
