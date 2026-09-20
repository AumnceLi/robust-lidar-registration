# -*- coding: utf-8 -*-
"""
s8_figures.py -- all deliverable figures (Agg backend, no GUI).
 fig1_residual_map.png      target-frame residual map, 2 views
 fig2_null_persistence.png  real persistence vs Null A/B
 fig3_error_vs_mismatch.png endpoint error vs mismatch, range-bin strata
 fig4_bias_vectors.png      translation bias vectors + rotation-axis distribution
 fig5_classification.png    R1-R4 trajectory fractions + global residual histogram
"""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
import s0_common as C

plt.rcParams.update({"font.size":9,"figure.dpi":130,"axes.grid":True,"grid.alpha":.3})

def fig1():
    mc=np.load(os.path.join(C.CACHE,"model_cache.npz"))
    model=mc["xyz"].astype(float); dnn=float(mc["dnn"])
    cachep=os.path.join(C.CACHE,"model_point_resid.npy")
    if os.path.exists(cachep):
        acc=np.load(cachep,allow_pickle=True).item()
    else:
        vals=[[] for _ in range(len(model))]
        for i in range(0,501,20):
            z=np.load(os.path.join(C.CACHE,"scans",f"scan_{i:04d}.npz"))
            t=cKDTree(z["aligned"].astype(float)); d,j=t.query(model,k=1)
            # nearest scan residual per model point (distance model->scan)
            for jj,dd in zip(j,d): vals[jj].append(dd)
        acc=np.array([np.median(v) if len(v) else np.nan for v in vals])
        np.save(cachep,acc)
    pm=np.load(os.path.join(C.CACHE,"patch_matrix.npz")); prof=pm["profile"]
    pz=np.load(os.path.join(C.CACHE,"patches.npz")); plab=pz["lab"]
    patch_resid=prof[plab]
    fig=plt.figure(figsize=(12,5.2))
    for k,(az,el,title) in enumerate([(-60,12,"view A (az -60)"),(30,10,"view B (az +30)")]):
        ax=fig.add_subplot(1,2,k+1,projection="3d")
        sc=ax.scatter(model[:,0],model[:,1],model[:,2],c=acc*1000,s=.4,
                      cmap="turbo",vmin=0,vmax=np.nanpercentile(acc,95)*1000)
        ax.set_title(f"Target-frame residual map [mm]  {title}")
        ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
        ax.view_init(elev=el,azim=az)
        cb=fig.colorbar(sc,ax=ax,shrink=.6,pad=.1); cb.set_label("median model->scan dist [mm]")
    fig.tight_layout(); fig.savefig(os.path.join(C.FIGDIR,"fig1_residual_map.png"),bbox_inches="tight")
    plt.close(fig)
    # patch-level companion
    fig,ax=plt.subplots(1,2,figsize=(11,4))
    order=np.argsort(prof)
    ax[0].barh(range(24),prof[order]*1000,color="steelblue")
    ax[0].set_yticks(range(24)); ax[0].set_yticklabels(order,fontsize=7)
    ax[0].axvline(2*dnn*1000,color="r",ls="--",label=f"2*d_model_nn={2*dnn*1000:.1f}mm (R1)")
    ax[0].set_xlabel("cross-scan patch median residual [mm]"); ax[0].set_ylabel("patch id"); ax[0].legend()
    ax[0].set_title("Frozen patch residual profile (target frame)")
    sc=ax[1].scatter(model[:,0],model[:,1],c=patch_resid*1000,s=.4,cmap="turbo")
    ax[1].set_aspect("equal"); ax[1].set_xlabel("x [m]"); ax[1].set_ylabel("y [m]")
    ax[1].set_title("patch profile projected (x-y)"); plt.colorbar(sc,ax=ax[1],label="[mm]")
    fig.tight_layout(); fig.savefig(os.path.join(C.FIGDIR,"fig1b_patch_profile.png"),bbox_inches="tight")
    plt.close(fig)

def fig2():
    nt=pd.read_csv(os.path.join(C.RESULTS,"null_tests.csv"))
    lags=[1,5,10,50]
    fig,ax=plt.subplots(1,2,figsize=(11,4.2))
    for axi,metric,title in [(ax[0],"temporal_autocorr_patchmedian","temporal autocorr of patch median"),
                             (ax[1],"cross_scan_patch_rank_spearman","cross-scan patch-rank Spearman")]:
        sub=nt[nt.test_name==metric]
        real=[sub[sub.lag_or_comparison==f"lag{L}"].real_value.iloc[0] for L in lags]
        for nm,mk,col in [("NullA_within_scan_shuffle","o","tab:orange"),
                          ("NullB_rangebin_permute","s","tab:green")]:
            mu=[sub[(sub.null_model==nm)&(sub.lag_or_comparison==f"lag{L}")].null_mean.iloc[0] for L in lags]
            sd=[sub[(sub.null_model==nm)&(sub.lag_or_comparison==f"lag{L}")].null_std.iloc[0] for L in lags]
            mu=np.array(mu); sd=np.array(sd); x=np.arange(4)
            axi.errorbar(x,mu,yerr=2*sd,fmt=mk,color=col,capsize=3,label=nm.replace("_"," "))
        axi.plot(range(4),real,"-D",color="tab:red",lw=2,label="REAL VI")
        axi.set_xticks(range(4)); axi.set_xticklabels([f"lag{L}" for L in lags])
        axi.set_title(title); axi.set_xlabel("time lag [scans]"); axi.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(C.FIGDIR,"fig2_null_persistence.png"),bbox_inches="tight")
    plt.close(fig)

def fig3():
    d=pd.read_csv(os.path.join(C.CACHE,"endpoint_merged.csv"))
    fig,ax=plt.subplots(1,2,figsize=(11,4.2))
    bins=[(8,11),(11,13.5),(13.5,15)]; cols=["tab:blue","tab:orange","tab:red"]
    for (lo,hi),c in zip(bins,cols):
        s=d[(d.range_m>=lo)&(d.range_m<hi)]
        ax[0].scatter(s.excess_return_fraction,s.translation_error_m,s=14,color=c,alpha=.7,
                      label=f"{lo}-{hi}m n={len(s)}")
        ax[1].scatter(s.excess_return_fraction,s.attitude_error_deg,s=14,color=c,alpha=.7)
    for axi,y,tt in [(ax[0],"translation_error_m","translation error [m]"),
                     (ax[1],"attitude_error_deg","sym-aware attitude error [deg]")]:
        b=np.polyfit(d.excess_return_fraction,d[y],1); xs=np.linspace(d.excess_return_fraction.min(),
                  d.excess_return_fraction.max(),50)
        rho=spearmanr(d.excess_return_fraction,d[y])
        axi.plot(xs,np.polyval(b,xs),"k--",lw=1.5,label=f"OLS fit, Spearman ρ={rho.statistic:.2f} p={rho.pvalue:.2g}")
        axi.set_xlabel("per-scan excess-return fraction (r>0.5 m)"); axi.set_ylabel(tt); axi.legend(fontsize=7)
    ax[0].set_title("Endpoint error vs structured mismatch (stratified by range)")
    fig.tight_layout(); fig.savefig(os.path.join(C.FIGDIR,"fig3_error_vs_mismatch.png"),bbox_inches="tight")
    plt.close(fig)

def fig4():
    b=pd.read_csv(os.path.join(C.RESULTS,"bias_variance.csv"))
    fig=plt.figure(figsize=(12,5))
    ax=fig.add_subplot(1,2,1,projection="3d")
    def vec(row,c,label):
        v=np.array([row.mean_bias_vector_x,row.mean_bias_vector_y,row.mean_bias_vector_z])
        ax.quiver(0,0,0,*v,color=c,lw=2.5,label=f"{label} |v|={np.linalg.norm(v)*100:.1f}cm")
    vec(b[b.group=="HIGH_mismatch(excess>median)"].iloc[0],"tab:red","HIGH mismatch")
    vec(b[b.group=="LOW_mismatch(excess<=median)"].iloc[0],"tab:blue","LOW mismatch")
    vec(b[b.group=="HIGH_half1(scan<=250)"].iloc[0],"tab:red","")
    vec(b[b.group=="HIGH_half2(scan>250)"].iloc[0],"darkred","")
    ax.set_title("Mean translation-error vectors (target frame)"); ax.legend(fontsize=7)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    d=pd.read_csv(os.path.join(C.CACHE,"endpoint_merged.csv")); med=d.excess_return_fraction.median()
    hi=d[d.excess_return_fraction>med]
    ax2=fig.add_subplot(1,2,2,projection="3d")
    ax2.scatter(hi.rot_err_axis_x,hi.rot_err_axis_y,hi.rot_err_axis_z,s=12,c="tab:red",alpha=.6)
    # unit sphere wire
    u=np.linspace(0,2*np.pi,20); v=np.linspace(0,np.pi,15); gx=np.outer(np.cos(u),np.sin(v))
    gy=np.outer(np.sin(u),np.sin(v)); gz=np.outer(np.ones_like(u),np.cos(v))
    ax2.plot_wireframe(gx,gy,gz,color="gray",alpha=.15,lw=.5)
    rr=b[b.group=="HIGH_mismatch(excess>median)"].iloc[0]
    ax2.quiver(0,0,0,rr.rotation_bias_axis_x,rr.rotation_bias_axis_y,rr.rotation_bias_axis_z,
               color="k",lw=3)
    ax2.set_title(f"HIGH-mismatch rotation-error axes (conc={rr.axis_concentration:.2f})")
    fig.tight_layout(); fig.savefig(os.path.join(C.FIGDIR,"fig4_bias_vectors.png"),bbox_inches="tight")
    plt.close(fig)

def fig5():
    per=pd.read_csv(os.path.join(C.RESULTS,"residual_per_scan.csv"))
    mc=np.load(os.path.join(C.CACHE,"model_cache.npz")); dnn=float(mc["dnn"])
    fig,ax=plt.subplots(1,2,figsize=(11,4))
    x=per.scan_id
    ax[0].stackplot(x,per.r1_frac,per.r2_backface_frac,per.r3_fov_frac,
                    per.r4_structured_frac,per.large_noise_frac,
                    labels=["R1 sampling","R2 backface/occl","R3 FOV trunc","R4 structured candidate","large-resid noise"],
                    colors=["#2ca02c","#7f7f7f","#9467bd","#d62728","#ff7f0e"],alpha=.85)
    ax[0].set_xlabel("scan id"); ax[0].set_ylabel("fraction of scan points"); ax[0].legend(fontsize=7)
    ax[0].set_title("R1-R4 operational classification along VI")
    # global residual histogram from a subset of cached scans
    rs=[]
    for i in range(0,501,10):
        rs.append(np.load(os.path.join(C.CACHE,"scans",f"scan_{i:04d}.npz"))["r"])
    rs=np.concatenate(rs)
    ax[1].hist(rs*1000,bins=np.linspace(0,300,120),color="steelblue",density=True)
    ax[1].axvline(2*dnn*1000,color="g",ls="--",label=f"R1 bound 2·dnn={2*dnn*1000:.1f}mm")
    ax[1].axvline(500,color="r",ls="--",label="excess 500mm")
    ax[1].set_xlabel("unsigned residual [mm]"); ax[1].set_ylabel("density"); ax[1].legend(fontsize=8)
    ax[1].set_title(f"global residual distribution (n={len(rs):,} points, every 10th scan)")
    fig.tight_layout(); fig.savefig(os.path.join(C.FIGDIR,"fig5_classification.png"),bbox_inches="tight")
    plt.close(fig)

if __name__=="__main__":
    fig1(); print("fig1 ok"); fig2(); print("fig2 ok")
    if os.path.exists(os.path.join(C.CACHE,"endpoint_merged.csv")):
        fig3(); print("fig3 ok"); fig4(); print("fig4 ok")
    fig5(); print("fig5 ok")
