# -*- coding: utf-8 -*-
"""m_figures.py -- figures for the rescue-audit reports (run after m2-m7)."""
import os, json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import m_common as M
plt.rcParams.update({"font.size":9,"axes.grid":True,"grid.alpha":0.3,"figure.dpi":130})
FIG=os.path.join(M.REPORTS,"rescue_figs"); os.makedirs(FIG,exist_ok=True)

# F1 nuisance
nd=pd.read_csv(os.path.join(M.RESCACHE,"nuisance_diagnostics.csv"))
fig,ax=plt.subplots(1,2,figsize=(9,3.4))
order=["raw","N1_range","N2_se3","N3_scale","N4_combined"]; lab=["raw","N1 range","N2 SE3","N3 scale","N4 combined"]
dd=nd.set_index("variant").loc[order]
ax[0].bar(lab,dd.patch_profile_std_mm,color="steelblue"); ax[0].axhline(8.1,ls="--",c="gray",lw=1); ax[0].set_ylabel("24-patch spread std (mm)"); ax[0].tick_params(axis="x",rotation=30)
ax[1].plot(lab,dd.lag1_rank_spearman,"o-",label="lag-1 rank ρ"); ax[1].plot(lab,dd.similar_aspect_spearman,"s--",label="similar-aspect ρ"); ax[1].set_ylim(0,1); ax[1].legend(); ax[1].tick_params(axis="x",rotation=30)
fig.tight_layout(); fig.savefig(os.path.join(FIG,"F1_nuisance.png"),bbox_inches="tight"); plt.close(fig)

D=np.load(os.path.join(M.RESCACHE,"objective_main.npz"))
csv=pd.read_csv(os.path.join(M.RESCACHE,"objective_per_scan.csv"))
# F2 M1 gradient norm real vs nulls (p2p)
nA=pd.read_csv(os.path.join(M.RESCACHE,"nullA_self.csv")); NB=np.load(os.path.join(M.RESCACHE,"nullB_shuffle.npz"))
fig,ax=plt.subplots(figsize=(7,3.6))
data=[]; labs=[]
for c in ["raw","scale","combined"]:
    x=csv[(csv.cond==c)&(csv.obj=="p2p")].gnorm.values; data.append(x); labs.append(c+" real")
data.append(nA[nA.obj=="p2p"].gnorm.values); labs.append("NullA self")
data.append(NB["gnorm_shuf"][:,:,0].ravel()); labs.append("NullB shuffle")
ax.boxplot(data,tick_labels=labs,showfliers=False); ax.set_yscale("log"); ax.set_ylabel("‖∇J(T_GT)‖  (p2p)")
ax.tick_params(axis="x",rotation=20)
fig.tight_layout(); fig.savefig(os.path.join(FIG,"F2_gradient_vs_null.png"),bbox_inches="tight"); plt.close(fig)

# F3 M2 displacement direction (raw p2p translation, xy + xz)
xi=D["raw__xistar"][:,:,0]; T=xi[:,:3]*1000
fig,axs=plt.subplots(1,2,figsize=(8,3.8))
for ax,(a,b,la,lb) in zip(axs,[(0,1,"tx (mm)","ty (mm)"),(0,2,"tx (mm)","tz (mm)")]):
    ax.scatter(T[:,a],T[:,b],s=6,alpha=0.4)
    m=T[:,[a,b]].mean(0); ax.annotate("",xy=m,xytext=(0,0),arrowprops=dict(arrowstyle="->",color="red",lw=2))
    ax.axhline(0,color="k",lw=.6); ax.axvline(0,color="k",lw=.6); ax.set_xlabel(la); ax.set_ylabel(lb); ax.set_aspect("equal")
fig.suptitle("Local-optimum translation displacement from GT (p2p)")
fig.tight_layout(); fig.savefig(os.path.join(FIG,"F3_displacement_direction.png"),bbox_inches="tight"); plt.close(fig)

# F4 quadratic prediction (raw, both obj)
fig,axs=plt.subplots(1,2,figsize=(8,3.7))
for ax,k,kn in zip(axs,range(2),["p2p","p2l"]):
    dh=np.linalg.norm(D["raw__dhat"][:,:3,k],axis=1)*1000
    st=np.linalg.norm(D["raw__xistar"][:,:3,k],axis=1)*1000
    ax.scatter(dh,st,s=6,alpha=0.4); lim=np.percentile(np.r_[dh,st],99); ax.plot([0,lim],[0,lim],"k--",lw=1)
    ax.set_xlabel("predicted ‖-H⁻¹g‖ trans (mm)"); ax.set_ylabel("measured local-opt trans (mm)"); ax.set_title(kn)
fig.tight_layout(); fig.savefig(os.path.join(FIG,"F4_quadratic.png"),bbox_inches="tight"); plt.close(fig)

# F5 patch influence vs frozen profile
m4=json.load(open(os.path.join(M.RESCACHE,"m4_direction_patch.json")))
fig,ax=plt.subplots(figsize=(8,3.6)); xp=np.arange(24)
ax.bar(xp-0.2,m4["profile"],width=0.4,label="frozen patch median residual (mm)")
ax2=ax.twinx(); ax2.bar(xp+0.2,np.array(m4["infl_p2p"])*1000,width=0.4,color="darkorange",label="mean leave-one-out ‖Δg‖")
ax.set_xlabel("frozen patch id"); ax.set_ylabel("residual (mm)"); ax2.set_ylabel("gradient influence (scaled)")
ax.legend(loc="upper left"); fig.tight_layout(); fig.savefig(os.path.join(FIG,"F5_patch_influence.png"),bbox_inches="tight"); plt.close(fig)

# F6 landscape example (scan 0, p2p)
LG=D["landscape"] if "landscape" in D.files else None
if LG is not None:
    fig,ax=plt.subplots(1,2,figsize=(8,3.4))
    J0=csv[(csv.cond=="raw")&(csv.obj=="p2p")].J0.iloc[0]
    for axi,tidx,xt in zip(ax,[0,1],["translation (cm)","rotation (deg)"]):
        for a,c in zip(range(3),["r","g","b"]):
            xs=[];ys=[]
            mags=M.GRID_T if tidx==0 else M.GRID_R
            for mi,mag in enumerate(mags):
                for sgn in (0,1):
                    x=(mag if sgn==0 else -mag)
                    x=x*100 if tidx==0 else np.degrees(x)
                    xs.append(x); ys.append(LG[0,tidx,a,mi,sgn,0])
            order=np.argsort(xs); axi.plot(np.array(xs)[order],(np.array(ys)-J0)[order],"o-",color=c,label=f"axis{a}")
        axi.axhline(0,color="k",lw=.6); axi.set_xlabel(xt); axi.set_ylabel("ΔJ (p2p)"); axi.legend(fontsize=7)
    fig.suptitle("Objective landscape about GT (scan 0)"); fig.tight_layout()
    fig.savefig(os.path.join(FIG,"F6_landscape.png"),bbox_inches="tight"); plt.close(fig)

# F7 M3 partial R2
m3=pd.read_csv(os.path.join(M.RESCACHE,"m3_summary.csv"))
fig,ax=plt.subplots(figsize=(8,3.8))
sel=m3[m3.endpoint=="proj"]; y=np.arange(len(sel))
ax.barh(y,sel.partialR2,xerr=np.vstack([sel.partialR2-sel.ci_lo,sel.ci_hi-sel.partialR2]),color="seagreen")
ax.set_yticks(y); ax.set_yticklabels(sel.cond+" "+sel.obj); ax.set_xlabel("incremental partial R² (mismatch block | controls)")
fig.tight_layout(); fig.savefig(os.path.join(FIG,"F7_partialR2.png"),bbox_inches="tight"); plt.close(fig)
print("[figures] written to",FIG)
