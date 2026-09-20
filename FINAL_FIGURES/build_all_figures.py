"""Read-only figure build from frozen artifacts; never imports/runs registration methods.
Usage: python FINAL_FIGURES/build_all_figures.py [--figures 1 2 ...]
Dependencies: numpy pandas scipy matplotlib Pillow; PyMuPDF for separate QA script.
"""
from pathlib import Path
import sys,json,hashlib,argparse,datetime
import numpy as np
import pandas as pd
from scipy.stats import spearmanr,pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle,FancyArrowPatch,Polygon,ConnectionPatch,FancyBboxPatch,Ellipse,Arc
from matplotlib.colors import LinearSegmentedColormap,LogNorm,TwoSlopeNorm
from master_style.matplotlib_style import apply,COLORS as C,MARKERS as M,REGIME_COLORS,MM
apply()
OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
S='structured_mismatch_phase0/'
G='g_chain/'
H='FINAL_TOPJOURNAL_HARDENING/'
TR=['vi','iv','ii','iii']
METHOD={'Raw':'M0_raw_p2p','p2l':'M1_raw_p2l','Huber':'M2_raw_huber','Global':'M3_global_corr','Patch':'M4_patch_corr','Full':'M5_full_corr'}
SOURCES={}; TABLES={}; LOG=[]
CURRENT=0
def source(p):
    p=ROOT/p
    if not p.exists(): raise FileNotFoundError('MISSING frozen input: '+str(p))
    rel=p.relative_to(ROOT).as_posix()
    SOURCES.setdefault(CURRENT,{})[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return p
def csv(p): return pd.read_csv(source(p))
def npz(p): return np.load(source(p),allow_pickle=False)
def note_source(p): source(p)
def table(name,d):
    target=OUT/f'Figure{CURRENT}'/(name+'.csv');d.to_csv(target,index=False)
    TABLES.setdefault(CURRENT,[]).append(target.name)
def fig(h=116): return plt.figure(figsize=(178*MM,h*MM),layout='constrained')
def panel(ax,letter,title):
    ax.set_title(title,loc='left',x=.145,pad=9,fontweight='bold')
    ax.annotate(f'({letter})',(0,1),xycoords='axes fraction',xytext=(0,9),textcoords='offset points',ha='left',va='baseline',fontsize=10,fontweight='bold')
def clean(ax,ylabel=None,xlabel=None):
    if ylabel: ax.set_ylabel(ylabel)
    if xlabel: ax.set_xlabel(xlabel)
    ax.tick_params(direction='out',length=3)
def legend(f,names,y=1.01):
    hs=[Line2D([],[],color=C[n],marker=M.get(n,'o'),linestyle='None',markerfacecolor='white' if n=='Estimated Full' else C[n],label=n) for n in names]
    f.legend(handles=hs,loc='outside lower center',ncol=min(len(names),6),frameon=False,handletextpad=.4,columnspacing=1.4)
def summary(v):
    a=np.asarray(v,float);a=a[np.isfinite(a)]
    return np.quantile(a,[.25,.5,.75]) if len(a) else np.full(3,np.nan)
def point(ax,x,v,name,width=1.2):
    lo,med,hi=summary(v)
    ax.errorbar(x,med,yerr=[[med-lo],[hi-med]],fmt=M.get(name,'o'),color=C.get(name,'#4D4D4D'),
       mfc='white' if name=='Estimated Full' else C.get(name,'#4D4D4D'),ms=5,capsize=2.2,elinewidth=width,mew=1.1,zorder=3)
    return lo,med,hi
def subset(d,t):
    q=d[d.traj==t].copy()
    if t not in ['vi','v']:q=q[q.in_support==True]
    return q.sort_values('order')
def g1():
    return pd.concat([csv(G+'G1_MITIGATION/results/all_pose_results.csv'),csv(G+'G3_FINAL_CONFIRMATION/results/g1_iii.csv')],ignore_index=True)
def g0():
    return pd.concat([csv(G+'G0_ROBUST_FALSIFICATION/results/frame_results.csv'),csv(G+'G3_FINAL_CONFIRMATION/results/g0_iii.csv')],ignore_index=True)
def g2():
    return pd.concat([csv(G+f'G2_ESTIMATED_VIEW/results/g2_{t}.csv') for t in ['vi','iv','ii']]+[csv(G+'G3_FINAL_CONFIRMATION/results/g2_iii.csv')],ignore_index=True)
def grouped(ax,d,names,field,trajectories=TR):
    rows=[]
    for i,t in enumerate(trajectories):
        q=subset(d,t)
        for k,n in enumerate(names):
            a=q[q.method==METHOD[n]][field]
            lo,med,hi=point(ax,i+(k-(len(names)-1)/2)*.145,a,n)
            rows.append(dict(trajectory=t,method=n,field=field,n=len(a),q25=lo,median=med,q75=hi))
    ax.set_xticks(range(len(trajectories)),[t.upper()+('\nreserved' if t=='iii' else '\ndev.' if t=='vi' else '') for t in trajectories])
    ax.set_xlim(-.55,len(trajectories)-.45)
    return rows
def finish(f,caption,notes,status='SUCCESS',missing='None',na='None'):
    n=CURRENT; folder=OUT/f'Figure{n}'
    f.set_constrained_layout_pads(w_pad=3/72,h_pad=3/72,wspace=.07,hspace=.09)
    for axis in f.axes:
        for collection in axis.collections:collection.set_rasterized(False)
    for ext in ['pdf','svg','png']:f.savefig(folder/f'Figure{n}.{ext}',dpi=600)
    plt.close(f)
    (folder/f'Figure{n}_caption_draft.md').write_text(caption+'\n',encoding='utf-8')
    sr='\n'.join(f'- `{p}`; SHA256 `{h}`' for p,h in SOURCES[n].items())
    text=f'# Figure {n}: provenance and review notes\n\n{notes}\n\n## Sources (read-only)\n{sr}\n\n## Plotted-data tables\n'+ '\n'.join(f'- `{p}`' for p in TABLES.get(n,[]))
    text+=f'\n\nMissing: {missing}\n\nN/A: {na}\n\nNo registration rerun, training, retuning or modification of frozen results. Statistics are descriptive reductions of saved results unless explicitly identified as an existing frozen CI. Human review is still required for scientific interpretation.\n'
    (folder/f'Figure{n}_notes.md').write_text(text,encoding='utf-8')
    (folder/'source_hashes.json').write_text(json.dumps(SOURCES[n],indent=2),encoding='utf-8')
    LOG.append(dict(figure=n,status=status,missing=missing,na=na,sources=list(SOURCES[n])))
    print(f'Figure {n}: {status}',flush=True)

def figure1():
    note_source(H+'THEORY/derivation.md');note_source(H+'AUDIT/operating_assumptions.md')
    f=fig(122);axes=f.subplots(2,3)
    titles=['Scan versus nominal model','Structured residual field','Pose-active projection','Shifted objective optimum','Historical patch field','Corrected geometry']
    desc=['Observed scan and known target geometry','Spatially coherent scan-to-model offsets',r'Rigid-pose component $J^T W\delta$','Reference pose is locally non-stationary',r'Frozen $\mu_j(z)$ from calibrated history','Corrected geometry moves pose toward the reference']
    edge='#CCD5D9';ink='#425056';scan=C['Full'];accent=C['Patch'];blue=C['Huber']
    body=np.array([[.26,.31],[.74,.31],[.74,.62],[.26,.62]])
    left=np.array([[.08,.38],[.26,.38],[.26,.55],[.08,.55]])
    right=np.array([[.74,.38],[.92,.38],[.92,.55],[.74,.55]])
    def satellite(ax,shift=(0,0),color=ink,ls='-',fill='#F4F6F7',lw=1.3):
        for pts in [body,left,right]:
            pts=pts+np.asarray(shift);ax.add_patch(Polygon(pts,closed=True,fc=fill,ec=color,lw=lw,ls=ls,joinstyle='round'))
        ax.plot([.41+shift[0],.59+shift[0]],[.62+shift[1],.62+shift[1]],color=color,lw=lw)
        ax.plot([.47+shift[0],.47+shift[0]],[.62+shift[1],.70+shift[1]],color=color,lw=lw)
        ax.add_patch(Arc((.47+shift[0],.75+shift[1]),.16,.12,theta1=20,theta2=160,ec=color,lw=lw))
    for i,ax in enumerate(axes.flat):
        ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
        ax.add_patch(FancyBboxPatch((.015,.04),.97,.90,boxstyle='round,pad=.012,rounding_size=.025',fc='#FBFCFC',ec=edge,lw=.8,zorder=-5))
        panel(ax,chr(65+i),titles[i]);ax.text(.5,.095,desc[i],ha='center',va='center',fontsize=8,color=ink)
        if i==0:
            satellite(ax,shift=(0,.04))
            pts=np.array([[.12,.43],[.23,.36],[.31,.29],[.43,.27],[.57,.29],[.71,.35],[.78,.60],[.88,.48]])
            ax.plot(pts[:,0],pts[:,1],'o',mfc='white',mec=scan,ms=4,mew=1.2)
            ax.plot(pts[:,0],pts[:,1],color=scan,lw=.8,alpha=.55)
            ax.text(.08,.77,'model',color=ink,fontsize=8,fontweight='bold');ax.text(.72,.77,'scan',color=scan,fontsize=8,fontweight='bold')
        elif i==1:
            x=np.linspace(.13,.87,7);nom=.39+.10*np.sin(np.linspace(0,np.pi,7));obs=nom+np.array([.05,.08,.12,.15,.11,.07,.04])
            ax.plot(x,nom,color=ink,lw=1.5);ax.plot(x,obs,color=scan,lw=1.8)
            for xx,y0,y1 in zip(x[1:-1],nom[1:-1],obs[1:-1]):ax.annotate('',(xx,y1),(xx,y0),arrowprops=dict(arrowstyle='-|>',color=scan,lw=1.1,mutation_scale=8))
            ax.text(.77,.72,r'$\delta_i$',fontsize=12,color=scan)
            ax.text(.14,.31,'nominal surface',fontsize=7.5,color=ink)
        elif i==2:
            origin=(.25,.30)
            ax.annotate('',(.82,.30),origin,arrowprops=dict(arrowstyle='->',color=ink,lw=1.2))
            ax.annotate('',(.25,.73),origin,arrowprops=dict(arrowstyle='->',color=ink,lw=1.2))
            ax.annotate('',(.69,.61),origin,arrowprops=dict(arrowstyle='-|>',color=scan,lw=2,mutation_scale=10))
            ax.plot([.25,.69],[.30,.30],'--',color=blue,lw=1)
            ax.annotate('',(.69,.30),origin,arrowprops=dict(arrowstyle='-|>',color=blue,lw=1.7,mutation_scale=9))
            ax.text(.53,.68,'residual field',color=scan,fontsize=7.5);ax.text(.48,.22,'pose-active part',color=blue,fontsize=7.5)
            ax.text(.5,.80,r'$g_{\rm ref}=J^T W\delta$',ha='center',fontsize=11)
        elif i==3:
            x=np.linspace(.13,.87,100);y=.27+1.42*(x-.65)**2;ax.plot(x,y,color=ink,lw=1.8)
            ygt=np.interp(.30,x,y);ax.plot(.30,ygt,'o',mfc='white',mec=ink,mew=1.2,ms=5);ax.annotate('',(.43,np.interp(.43,x,y)),(.30,ygt),arrowprops=dict(arrowstyle='-|>',color=scan,lw=1.4))
            ax.plot(.65,.27,'o',color=scan,ms=5);ax.axvline(.30,ymin=.18,ymax=.52,color='#AAB3B7',lw=.8,ls=':')
            ax.text(.12,.19,'Reference',fontsize=8);ax.text(.62,.17,r'$\Delta\xi_{\rm FO}$',fontsize=9,color=scan)
            ax.text(.5,.78,r'$\Delta\xi_{\rm FO}=-H_{\rm GN}^{\dagger}g_{\rm ref}$',ha='center',fontsize=10.5)
        elif i==4:
            satellite(ax,shift=(-.13,.00),color=ink,fill='#F4F6F7',lw=1.0)
            shades=['#E7F3EF','#CBE8DF','#A9D9CB','#78C3AD','#43A98B','#1B9E77']
            for k,(xx,yy) in enumerate([( .15,.41),(.28,.41),(.41,.41),(.54,.41),(.67,.41),(.80,.41)]):
                ax.add_patch(Rectangle((xx,yy),.11,.16,fc=shades[k],ec='white',lw=.7))
            ax.annotate('',(.76,.72),(.88,.82),arrowprops=dict(arrowstyle='-|>',color=blue,lw=1.4));ax.text(.70,.76,'view $z$',fontsize=8,color=blue)
            ax.text(.5,.70,r'$\mu_j(z)$',ha='center',fontsize=12,color=accent)
        else:
            satellite(ax,shift=(0,.02),color=ink,fill='#F4F6F7',lw=1.1)
            pts=np.array([[.12,.42],[.24,.40],[.31,.34],[.43,.33],[.57,.34],[.71,.40],[.78,.58],[.88,.47]])
            ax.plot(pts[:,0],pts[:,1],'o',mfc='white',mec=accent,ms=3.8,mew=1.1)
            ax.annotate('',(.52,.68),(.52,.56),arrowprops=dict(arrowstyle='-|>',color=accent,lw=1.5))
            ax.text(.5,.76,'scan and corrected model',ha='center',fontsize=8,color=accent)
            ax.text(.12,.22,'translation-error reduction',fontsize=8,color=scan,fontweight='bold')
    # Vector connectors preserve the clear A-B-C-D-E-F reading order.
    for left,right in [(axes[0,0],axes[0,1]),(axes[0,1],axes[0,2]),(axes[1,0],axes[1,1]),(axes[1,1],axes[1,2])]:
        f.add_artist(ConnectionPatch((.96,.45),(.04,.45),'axes fraction','axes fraction',axesA=left,axesB=right,arrowstyle='->',lw=1,color='#8B959B',shrinkA=3,shrinkB=3))
    axes[0,2].text(.83,.12,'continue to (D)',ha='right',fontsize=7.5,color='#68757B')
    finish(f,'**Conceptual mechanism and compensation workflow.** (A-C) A scan-to-model discrepancy creates a pose-active residual component. (D-F) A shifted local optimum motivates a historical, patch-indexed mismatch field and geometry compensation. The first-order step is $\\Delta\\xi_{\\rm FO}=-H_{\\rm GN}^{\\dagger}g_{\\rm ref}$ (FO = first-order; $H_{\\rm GN}$ is the Gauss-Newton normal-equation matrix; $g_{\\rm ref}$ is the gradient at the reference pose). All shapes and objective curves are conceptual illustrations; no quantitative data or statistical estimates are shown. The diagram links local non-stationarity to a physically motivated correction under known nominal geometry and calibrated historical observations.',
      'Panels are vector schematics drawn with matplotlib, not measured geometry. Reading order A-B-C-D-E-F. Formula is for the fixed-correspondence local surrogate on the observable subspace; improvement is conditional and empirically evaluated, not theoretically guaranteed. Human design choices: schematic locations, curves and colors. No synthetic numerical labels or measured-looking scales. Historical reference-pose alignment is required; runtime estimated-view conditions are treated in Figure 7. The nominal geometry is a discrete model point cloud, not a CAD solid.')

def figure2():
    p=csv(S+'results/patch_persistence.csv');defs=csv(S+'results/patch_definition.csv')
    md=npz(S+'scripts/cache/model_cache.npz');pa=npz(S+'scripts/cache/patches.npz');fr=npz(S+'scripts/cache/rescue/VI_ONLY_PREDICTOR_FROZEN.npz')
    p['block']=fr['blocks'][p.scan_id.to_numpy(int)];p['residual_mm']=p.median_residual*1000
    p=p[(p.support_count>0)&np.isfinite(p.residual_mm)].copy()
    heat=p.pivot_table(index='block',columns='patch_id',values='residual_mm',aggfunc='median').reindex(columns=range(24))
    table('patch_block_residual',heat.reset_index());table('patch_definitions',defs)
    f=fig(148);gs=f.add_gridspec(2,6,height_ratios=[1.18,1.08])
    a=f.add_subplot(gs[0,:3]);b=f.add_subplot(gs[0,3:]);panel(a,'A','Frozen nominal target: 24 patches');panel(b,'B','VI: spatial residual structure')
    # Fixed orthographic projection of real CAD; no 3D shading.
    P=np.array([[1,.42,0],[0,.23,1]])
    xyz=md['xyz']@P.T;cent=defs[['patch_center_x','patch_center_y','patch_center_z']].to_numpy()@P.T
    a.scatter(xyz[::7,0],xyz[::7,1],s=.75,color='#89979D',alpha=.52,linewidths=0)
    center=(xyz.min(0)+xyz.max(0))/2
    order=np.argsort(np.arctan2(cent[:,1]-center[1],cent[:,0]-center[0]))
    ang=np.linspace(-np.pi,np.pi,24,endpoint=False)
    for k,j in enumerate(order):
        pos=np.array([1.55*np.cos(ang[k]),1.2*np.sin(ang[k])])+center
        a.annotate(str(int(defs.patch_id.iloc[j])),cent[j],xytext=pos,ha='center',va='center',fontsize=7,
          arrowprops=dict(arrowstyle='-',color='#78888E',lw=.65),bbox=dict(fc='white',ec='none',pad=.3))
    a.set_aspect('equal');a.set_xlim(center[0]-1.8,center[0]+1.8);a.set_ylim(center[1]-1.45,center[1]+1.45);a.axis('off')
    cmap=LinearSegmentedColormap.from_list('residual',['#F5F7F8','#4C78A8']);cmap.set_bad('#DDDDDD')
    im=b.pcolormesh(np.ma.masked_invalid(heat.to_numpy()),cmap=cmap,shading='flat',vmin=0)
    b.set_xticks(np.arange(0,24,3)+.5,np.arange(0,24,3));b.set_yticks(np.arange(len(heat))+.5,heat.index.astype(str));b.invert_yaxis()
    clean(b,'Frozen orientation (view-travel) block','Patch ID');f.colorbar(im,ax=b,location='bottom',shrink=.95,pad=.12,label='Median per-scan patch residual (mm)')
    # Outcome-independent examples: largest nominal patch in each CAD-normal family.
    defs['family']=np.argmax(np.abs(defs[['patch_normal_x','patch_normal_y','patch_normal_z']].to_numpy()),axis=1)
    chosen=defs.sort_values(['model_point_count','patch_id'],ascending=[False,True]).groupby('family',sort=True).head(1).sort_values('family').patch_id.tolist()
    selected=[]
    for i,j in enumerate(chosen):
        ax=f.add_subplot(gs[1,i*2:(i+1)*2]);panel(ax,chr(67+i),f'Patch {j}: range dependence')
        q=p[p.patch_id==j].copy();q['range_bin']=pd.cut(q.range_m,np.linspace(p.range_m.min(),p.range_m.max(),9),include_lowest=True)
        agg=q.groupby('range_bin',observed=True).agg(x=('range_m','median'),med=('residual_mm','median'),lo=('residual_mm',lambda x:x.quantile(.25)),hi=('residual_mm',lambda x:x.quantile(.75)),n=('residual_mm','size')).reset_index(drop=True)
        ax.fill_between(agg.x,agg.lo,agg.hi,color=C['Huber'],alpha=.16,linewidth=0)
        ax.plot(agg.x,agg.med,'o-',color=C['Huber'],lw=1.7,ms=4.5)
        clean(ax,'Patch residual (mm)' if i==0 else None,'Sensor range (m)');ax.set_ylim(bottom=0)
        agg['patch_id']=j;selected.append(agg)
    table('view_examples_binned',pd.concat(selected))
    finish(f,'**Spatial and range-conditioned discrepancy on the EPOS development trajectory.** (A) Orthographic projection of the frozen nominal model and original patch IDs. (B) Patch residuals across frozen VI orientation (view-travel) blocks. For each patch and VI block, the color shows the median across scans of the within-patch median residual magnitude. (C-E) Range-conditioned residuals for one patch from each dominant normal family. Lines and shaded bands are median and 25th–75th percentile interval in eight fixed equal-width range bins, without an independence assumption or fitted curve. The observed discrepancy is spatially nonuniform and varies with viewing range on VI.',
      f'Fields: patch_id, scan_id, support_count, median_residual (m), range_m; frozen blocks indexed by scan_id. Only support_count>0 and finite residuals retained. Missing heatmap cells remain masked, never zero-filled. Model projection is x+0.42y versus z+0.23y, schematic units omitted. Original patch IDs 0-23 preserved. The six frozen orientation blocks are the same contiguous view-travel blocks used throughout the VI analysis (cumulative view-direction travel; sizes 70/70/79/96/103/83). Example patches {chosen} selected by largest nominal model_point_count within dominant absolute normal axis (x/y/z), independent of residual outcomes. Range bins: eight equal-width intervals over all supported VI observations. Bands are descriptive 25th–75th percentile intervals, NOT confidence intervals. Figure limited to VI because patch-wise cross-trajectory residual tables were not needed for this supported realization; no cross-trajectory patch field was recomputed. Human review: range and orientation covary, so do not claim a causal range effect. Suggested Supplementary: complete 24-patch view profiles.')

def figure3():
    d=g0();d=d[(d.kind=='p2p')&(d.form=='ls')]
    f=fig(118);gs=f.add_gridspec(2,2,width_ratios=[1.02,1.18],height_ratios=[1,1]);a=f.add_subplot(gs[:,0]);b=f.add_subplot(gs[0,1]);c=f.add_subplot(gs[1,1])
    panel(a,'A','Reference-pose-local gradient versus numerical null');panel(b,'B','Medians within saved blocks');panel(c,'C','Recomputed-NN descent check')
    records=[];blocks=[]
    for i,t in enumerate(TR):
        q=subset(d,t)
        for r,n,off in [(1,'Raw',-.12),(0,'Self-null',.12)]:
            v=q[q.real==r].g_gt;lo,med,hi=point(a,i+off,v,n);records.append(dict(traj=t,condition=n,n=len(v),q25=lo,median=med,q75=hi))
        bl=q[q.real==1].groupby('block').g_gt.median()
        for k,(bid,v) in enumerate(bl.items()):
            b.plot(i+(k-(len(bl)-1)/2)*.030,v,'o',ms=4,color=C['Raw'],alpha=.82,mec='white',mew=.35);blocks.append(dict(traj=t,block=bid,median=v))
    a.set_yscale('log');a.set_xticks(range(4),[t.upper() for t in TR]);a.set_ylim(1e-6,.2)
    clean(a,'Reference-pose-local FD gradient norm (native coordinates)');clean(b,'FD gradient norm');b.set_xticks(range(4),[t.upper() for t in TR]);b.set_ylim(bottom=0)
    z=npz(S+'scripts/cache/rescue/objective_main.npz');rates=[]
    for group in [0,1]:
        grad=z['raw__g'][:,group*3:group*3+3,0];arr=z['landscape'][:,group,:,0,:,0]
        chosen=np.where(grad<0,arr[:,:,0],arr[:,:,1]);ok=chosen<z['raw__J0'][:,0,None]-1e-12
        rates.append(dict(probe=['Translation: 10 mm','Rotation: 0.5 deg'][group],fraction=ok.mean(),success=int(ok.sum()),n=ok.size))
    for i,r in enumerate(rates):
        val=100*r['fraction'];c.plot([86,val],[i,i],color='#C8D5DE',lw=2.2,zorder=1);c.plot(val,i,'o',color=C['Huber'],ms=6,zorder=2)
        c.text(val-.35,i+.16,f"{val:.1f}%  ({r['success']}/{r['n']})",ha='right',va='bottom',fontsize=8,color=C['Huber'])
    c.set_yticks(range(2),['Translation\n10 mm','Rotation\n0.5 deg']);c.set_xlim(86,100.6);c.set_ylim(-.55,1.55);clean(c,None,'Predicted-side objective decrease (%)')
    legend(f,['Raw','Self-null']);table('gradient_summary',pd.DataFrame(records));table('saved_block_summary',pd.DataFrame(blocks));table('descent_counts',pd.DataFrame(rates))
    finish(f,'**Non-stationarity of the nominal point-to-point objective near the reference pose.** (A) Real and matched numerical-null gradient norms on VI, IV, II and III. (B) Real-gradient medians within the saved temporal/orientation blocks. (C) VI directional probes for the smallest frozen translation and rotation scales, with the nearest-neighbor objective fully recomputed. Points and bars in (A) show median and 25th–75th percentile interval; each point in (B) is one existing block, while (C) reports descriptive probe counts without treating probes as independent trials. The nominal objective is not locally stationary at the reference pose in these evaluated trajectories.',
      'Fields: kind=p2p, form=ls, real=1/0, g_gt (data column name, retained), traj, order, block, in_support. VI all frames; IV/II/III saved in_support=True. The field g_gt is the saved norm of the six-component central-difference gradient evaluated at the reference pose, with translation in m and rotation in rad: a native-coordinate diagnostic, NOT a dimensionless invariant or exact analytic J^T W delta. Self-null has a finite numerical-gradient floor, even though its optimized pose error is near machine zero; these are different quantities. Panel B uses the actual saved block IDs, not rounded block counts from prose audits. Panel C landscape axes: frame, translation/rotation, coordinate, scale, +/- side, objective; use scale index 0 and p2p index 0. Select + if g<0, otherwise -, success Jside<J0-1e-12. Six probes per VI frame, no binomial CI. Suggested Supplementary: p2l, other step sizes, spatial shuffle and FD sensitivity.')

def figure4():
    f=plt.figure(figsize=(178*MM,158*MM));gs=f.add_gridspec(2,10,height_ratios=[.72,1.28]);a=f.add_subplot(gs[0,:4]);b=f.add_subplot(gs[0,4:]);c=f.add_subplot(gs[1,:5]);d=f.add_subplot(gs[1,5:])
    f.subplots_adjust(left=.095,right=.98,bottom=.125,top=.92,wspace=1.15,hspace=.48)
    panel(a,'A','Local first-order mechanism');a.set(xlim=(0,1),ylim=(0,1));a.axis('off')
    a.add_patch(FancyBboxPatch((.02,.10),.96,.78,boxstyle='round,pad=.02,rounding_size=.03',fc='#F7F9FA',ec='#CDD5D9',lw=.8))
    a.text(.08,.72,r'$r(\Delta\xi)\approx\delta+J\Delta\xi$',fontsize=11)
    a.text(.08,.49,r'$g_{\rm ref}=J^T W\delta$',fontsize=10.5,color=C['Huber'])
    a.text(.08,.27,r'$\Delta\xi_{\rm FO}=-H_{\rm GN}^{\dagger}g_{\rm ref}$',fontsize=10.5)
    a.text(.08,.13,'fixed correspondences; observable subspace',fontsize=7.5,color='#657278')
    panel(b,'B','Predicted versus realized translation')
    rows=[]
    paths=[S+'scripts/cache/rescue/objective_main.npz',S+'scripts/cache/ext/ext_objective_iv.npz','tj2_supplemental/cache/ii/ext_objective_ii.npz']
    for i,(t,p) in enumerate(zip(['VI','IV','II'],paths)):
        z=npz(p)
        for k,(obj,n) in enumerate([(0,'Raw'),(1,'p2l')]):
            v=z['raw__dhat'][:,:3,obj];w=z['raw__xistar'][:,:3,obj]
            co=np.einsum('ij,ij->i',v,w)/(np.linalg.norm(v,axis=1)*np.linalg.norm(w,axis=1))
            x0=i+(k-.5)*.22;lo,med,hi=summary(co)
            color=C['Raw'] if obj==0 else '#B8B8B8';marker='o' if obj==0 else 'x';alpha=1 if obj==0 else .7
            b.errorbar(x0,med,yerr=[[med-lo],[hi-med]],fmt=marker,color=color,ms=6 if obj==0 else 5,capsize=2.4,elinewidth=1.35 if obj==0 else .9,mew=1.1,alpha=alpha,zorder=3 if obj==0 else 2)
            rows.append(dict(trajectory=t,objective=['p2p','p2l'][obj],n=len(co),q25=lo,median=med,q75=hi))
    b.set_xticks(range(3),['VI','IV','II']);b.set_ylim(-.3,1.05);clean(b,'Direction cosine')
    b.axhline(0,color='#D0D0D0',lw=.7)
    b.legend(handles=[Line2D([],[],marker='o',color=C['Raw'],ls='',label='p2p primary'),Line2D([],[],marker='x',color='#B8B8B8',ls='',label='p2l reference')],frameon=False,loc='lower right')
    q=csv(G+'G_GENERALITY/results/geometry_results.csv');q=q[(q.kind=='p2p')&(q.form=='ls')&(q.condition=='structured')]
    ag=q.groupby(['geometry','dtype','mag'],sort=True).agg(J0=('J0','median'),gradient=('grad_gt','median'),error=('et_mm','median'),n=('et_mm','size'),bound_fraction=('on_bound','mean')).reset_index()
    ag['residual_rms_mm']=np.sqrt(ag.J0)*1000
    panel(c,'C','Residual magnitude');panel(d,'D','Pose-active gradient diagnostic')
    cor=[]
    for axis,field,label in [(c,'residual_rms_mm','Residual RMS at reference (mm)'),(d,'gradient','Reference-pose-local FD gradient norm\n(native coordinates)')]:
        for k,(dt,grp) in enumerate(ag.groupby('dtype')):
            axis.scatter(grp[field],grp.error,s=22,color=REGIME_COLORS[k],marker=['o','s','^','D','v'][k],linewidths=.45,edgecolors='white',label=dt[:2],alpha=.92)
        sp=spearmanr(ag[field],ag.error).statistic;pe=pearsonr(ag[field],ag.error).statistic
        axis.set_xscale('log');axis.set_yscale('log');axis.set_ylim(.009,500);clean(axis,'Translation error (mm)',label)
        axis.text(.04,.96,rf'$\rho_s={sp:.3f}$; $r={pe:.3f}$',transform=axis.transAxes,va='top',fontsize=8.5)
        cor.append(dict(predictor=field,spearman=sp,pearson=pe,n_conditions=len(ag)))
    handles,labels=c.get_legend_handles_labels();f.legend(handles,labels,frameon=False,ncol=5,loc='outside lower center',handletextpad=.3,columnspacing=1.5)
    d4=ag[ag.dtype.str.startswith('D4') & (ag.mag>=.05)]
    for axis,field in [(c,'residual_rms_mm'),(d,'gradient')]:axis.scatter(d4[field],d4.error,s=58,facecolors='none',edgecolors=C['DBS'],linewidths=1.1,zorder=4)
    c.annotate('D4: residual remains,\npose error stays low',xy=(d4.residual_rms_mm.median(),d4.error.median()),xytext=(.44,.16),textcoords='axes fraction',fontsize=8.2,color=C['DBS'],fontweight='bold',arrowprops=dict(arrowstyle='-|>',lw=1,color=C['DBS']))
    d.annotate('low pose-active\nprojection',xy=(d4.gradient.median(),d4.error.median()),xytext=(.48,.22),textcoords='axes fraction',fontsize=8.2,color=C['DBS'],fontweight='bold',arrowprops=dict(arrowstyle='-|>',lw=1,color=C['DBS']))
    table('direction_cosines',pd.DataFrame(rows));table('matched_scatter_conditions',ag);table('correlations',pd.DataFrame(cor))
    # Preserve a non-supporting real-trajectory correlation, without outcome-driven replacement.
    z=npz(paths[0]);y=np.linalg.norm(z['raw__xistar'][:,:3,0],axis=1)
    vr=spearmanr(np.sqrt(z['raw__J0'][:,0]),y).statistic;vg=spearmanr(np.linalg.norm(z['raw__g'][:,:3,0],axis=1),y).statistic
    finish(f,'**Directional theory comparison and conditional error severity.** (A) Local first-order approximation (schematic): $\\Delta\\xi_{\\rm FO}=-H_{\\rm GN}^{\\dagger}g_{\\rm ref}$ (FO = first-order). (B) Translation-direction cosine between the saved Newton prediction and realized displacement, with p2l retained as a negative reference. (C,D) Identical geometry-by-regime-by-dose cells from the frozen synthetic D1-D5 experiment, relating translation error to residual RMS and the saved reference-pose-local finite-difference gradient norm. Panel (B) shows median and 25th–75th percentile interval over the full saved trajectories; each scatter point is the median of 20 saved repetitions, with descriptive Pearson and Spearman correlations across conditions. The first-order direction is supported for p2p, and the native-coordinate gradient diagnostic is more strongly associated with synthetic translation error than residual RMS in this experiment.',
      f'Panel B uses raw__dhat and raw__xistar first three coordinates only, objective index 0/1; VI/IV/II all saved frames (not the in-support engineering subset), clearly separate scope from Figure 7. C/D use all 96 geometry x dtype x mag conditions including zero-dose, exploratory D2 .9/1 endpoints and solver-bound outcomes; no point excluded for weak association. RMS=sqrt(median J0)*1000 because frozen LS objective is mean squared residual. The data column grad_gt is a six-component FD norm under frozen m/rad coordinates evaluated at the reference pose, not exact J^T W delta and not a coordinate-invariant 6-DoF physical magnitude. Analytic per-condition J^T W delta vectors were not retained in this CSV; no method is rerun to manufacture them. Correlations are descriptive over designed conditions, not iid inferential tests. D4 is retained even when its residual RMS overlaps other types. Negative real VI comparison: Spearman residual RMS vs translation error={vr:.6f}, translation-gradient norm vs error={vg:.6f}; residual is stronger there. Therefore do NOT claim universal correlation dominance. D2 bound flags indicate solver-limited outcomes (some final norms exceed nominal 300 mm after rotational composition), not exact physical 300-mm measurements. Suggested Supplementary: all-direction/p2l theory diagnostics, VI counterexample scatter, damping negative results.',
      missing='Exact analytic synthetic J^T W delta vectors absent; explicitly labeled saved FD diagnostic used instead.')

def figure5():
    real=g0();real=real[(real.kind=='p2p')&(real.real==1)];f=fig(142);axes=f.subplots(2,2);a,b,c,d=axes.flat
    panel(a,'A','Real EPOS: translation');panel(b,'B','Real EPOS: rotation')
    records=[]
    for axis,field,ylabel in [(a,'et_mm','Reference-relative displacement (mm)'),(b,'eR_deg','Reference-relative rotation (deg)')]:
        for i,t in enumerate(TR):
            q=subset(real,t)
            for k,(form,n) in enumerate([('ls','Raw'),('huber','Huber'),('trim','Trim')]):
                v=q[q.form==form][field];lo,med,hi=point(axis,i+(k-1)*.18,v,n)
                records.append(dict(trajectory=t,loss=form,field=field,n=len(v),q25=lo,median=med,q75=hi))
        axis.set_xticks(range(4),['VI\ndev.','IV','II','III\nreserved']);axis.set_xlim(-.5,3.5);axis.set_ylim(bottom=0);clean(axis,ylabel)
    panel(c,'C','Coherent mismatch');panel(d,'D','Localized / gross mismatch')
    syn=csv(G+'G_GENERALITY/results/geometry_results.csv');syn=syn[(syn.kind=='p2p')&(syn.condition=='structured')]
    rr=[];geom_marker={'GA':'o','GB':'s','GC':'^'}
    groups=[(c,[('D1_appendage_disp',50,'et_mm','D1\n50 mm'),('D5_appendage_tilt',2,'eR_deg','D5\n2 deg')]),
            (d,[('D2_missing_component',1,'et_mm','D2\ncomplete*'),('D3_local_surface_off',100,'et_mm','D3\n100 mm')])]
    for axis,items in groups:
        for i,(dtype,dose,metric,label) in enumerate(items):
            for k,geo in enumerate(['GA','GB','GC']):
                q=syn[(syn.dtype==dtype)&(syn.mag==dose)&(syn.geometry==geo)]
                ls=q[q.form=='ls'][metric].median();hu=q[q.form=='huber'][metric].median();ratio=hu/ls
                axis.plot(i+(k-1)*.16,ratio,geom_marker[geo],ms=6,color=C['Huber'],mfc='white' if geo=='GC' else C['Huber'],mew=1.1)
                rr.append(dict(dtype=dtype,dose=dose,metric=metric,geometry=geo,ls_median=ls,huber_median=hu,huber_over_ls=ratio,bound_fraction=q[q.form=='ls'].on_bound.mean()))
        axis.axhline(1,color='#777777',ls='--',lw=.9);axis.set_yscale('log');axis.set_ylim(.025,1.75);axis.set_xticks(range(2),[x[3] for x in items]);clean(axis,'Huber / LS median error')
        axis.text(.03,.94,'robust often suppresses' if axis is d else 'robust response varies',transform=axis.transAxes,va='top',fontsize=8,color=C['Huber'])
    c.legend(handles=[Line2D([],[],marker=geom_marker[g],mfc='white' if g=='GC' else C['Huber'],mec=C['Huber'],ls='',label=g) for g in ['GA','GB','GC']],frameon=False,ncol=3,loc='lower right')
    d.text(.02,.03,'* exploratory complete-absence endpoint',transform=d.transAxes,fontsize=7.5)
    legend(f,['Raw','Huber','Trim']);table('real_displacements',pd.DataFrame(records));table('synthetic_endpoint_contrasts',pd.DataFrame(rr))
    finish(f,'**Reference-relative displacement and robust-loss falsification.** (A,B) Real EPOS translation and rotation for p2p LS, Huber and Trim. (C,D) Huber-to-LS median-error ratios across the three controlled geometries, separated into coherent and localized/gross mismatch regimes; D5 uses rotation error and the other endpoints use translation error. Real-data markers and bars are medians and 25th–75th percentile intervals of saved primary-subset frames; synthetic ratios use the median of 20 saved repetitions per geometry. Robust weighting attenuates but does not eliminate real EPOS error, and its effectiveness depends on mismatch organization.',
      'A/B: G0 saved p2p real=1 rows, forms ls/huber/trim; VI all, IV/II/III in_support=True; fields et_mm/eR_deg. C/D use frozen structured p2p rows, all GA/GB/GC: D1=50 mm translation, D5=2 deg rotation, D2=1 complete absence translation, D3=100 mm translation. Endpoints fixed by the requested regime contrast. Ratios are dimensionless so translation and rotation can be shown together without mixing units; absolute medians and solver-bound fractions are exported. The horizontal line is ratio=1, not a significance threshold. D2 complete absence is exploratory and bound outcomes are retained. Panel titles describe the observed regime tendency, not a universal guarantee: GB D2 remains near ratio 1 and is visible. Suggested Supplementary: absolute per-geometry endpoint values, p2l details, all D2 doses and Trim synthetic ratios.')

def figure6():
    h=csv(G+'HIERARCHY_TRANSFER/results/block_stats.csv');comp=csv(H+'DIRECT_BIAS_BASELINE/directbias_vs_mismatch.csv')
    f=fig(126);gs=f.add_gridspec(2,5,height_ratios=[.82,1.18]);a=f.add_subplot(gs[0,:3]);c=f.add_subplot(gs[0,3:]);b=f.add_subplot(gs[1,:])
    panel(a,'A','Historical mismatch information');panel(b,'B','Direct discrepancy subtraction: high ceiling, poor transfer');panel(c,'C','What DBS subtracts')
    for i,t in enumerate(['iv','ii','v']):
        for k,n in enumerate(['Global','Patch','Full']):
            r=h[(h.traj==t)&(h.level=='cos_'+n.lower())].iloc[0];x=i+(k-1)*.19
            a.errorbar(x,r['median'],yerr=[[r['median']-r.L5_lo],[r.L5_hi-r['median']]],fmt=M[n],color=C[n],capsize=2.2,elinewidth=1.1,ms=5)
    a.set_xticks(range(3),['IV','II','V\nout-of-support']);a.set_ylim(-.05,1.05);clean(a,'Translation direction cosine')
    a.legend(handles=[Line2D([],[],marker=M[n],color=C[n],ls='',label=n) for n in ['Global','Patch','Full']],frameon=False,ncol=3,loc='lower left')
    c.set(xlim=(0,1),ylim=(0,1));c.axis('off');c.add_patch(FancyBboxPatch((.03,.13),.94,.72,boxstyle='round,pad=.02,rounding_size=.035',fc='#FAFBFB',ec='#CDD5D9',lw=.8))
    origin=(.17,.48);c.annotate('',(.52,.48),origin,arrowprops=dict(arrowstyle='-|>',color=C['Raw'],lw=2,mutation_scale=10));c.text(.17,.58,r'$t_{\rm raw}$',ha='center',fontsize=10.5,color=C['Raw'])
    c.annotate('',(.39,.48),(.74,.48),arrowprops=dict(arrowstyle='-|>',color=C['DBS'],lw=2,mutation_scale=10));c.text(.72,.58,r'$\hat m_{\rm VI}\hat v_{\rm B1}$',ha='center',fontsize=10.5,color=C['DBS'])
    c.plot(.39,.48,'o',color=C['DBS'],ms=5);c.text(.50,.25,r'$\hat t_{\rm DBS}=t_{\rm raw}-\hat m_{\rm VI}\hat v_{\rm B1}$',ha='center',fontsize=10.5)
    c.text(.50,.08,'translation only  |  rotation: N/A',ha='center',fontsize=8,color='#657278')
    amap={'Raw':'Raw (p2p)','DBS':'DBS (B1 direct subtraction)','Patch':'Patch correction','Full':'Full correction'};rows=[]
    for i,t in enumerate(['vi','iv','ii']):
        for k,n in enumerate(amap):
            x=i+(k-1.5)*.19
            r=comp[(comp.trajectory==t.upper())&(comp.arm==amap[n])].iloc[0];lo,med,hi=r.ete_iqr_lo,r.ete_med,r.ete_iqr_hi
            b.errorbar(x,med,yerr=[[med-lo],[hi-med]],fmt=M[n],color=C[n],ms=5.5,capsize=2.3,elinewidth=1.1,mew=1)
            rows.append(dict(traj=t,method=n,q25=lo,median=med,q75=hi))
    b.set_xticks(range(3),['VI\ndevelopment','IV\nheld-out','II\nheld-out']);b.set_xlim(-.48,2.48);b.set_ylim(0,185);clean(b,'Translation error (mm)')
    b.annotate('transfer collapse',xy=(2-.095,143),xytext=(1.53,166),color=C['DBS'],fontsize=8.5,fontweight='bold',arrowprops=dict(arrowstyle='-|>',color=C['DBS'],lw=1))
    legend(f,['Raw','DBS','Patch','Full']);table('translation_comparison',pd.DataFrame(rows));table('hierarchy_existing_ci',h)
    finish(f,'**Why direct empirical discrepancy subtraction is not a reliable cross-trajectory replacement for mismatch correction.** (A) Global, Patch and Full translation-direction prediction across IV, II and out-of-support V. (B) Physical translation error for Raw, DBS, Patch and Full on development VI and held-out IV/II. (C) DBS subtracts a B1-predicted translation direction with magnitude fixed from VI history; it has no rotation output. Panel (A) uses existing moving-block 95% confidence intervals (L=5), while panel (B) shows median and 25th–75th percentile interval of saved primary-subset frames. DBS approaches a high translation-accuracy ceiling on VI/IV but collapses on II, whereas structured mismatch correction avoids that direct-subtraction failure mode.',
      'A fields: level, median, L5_lo/L5_hi; post-development hierarchy analysis, not prospective. VI hierarchy is absent from this selected frozen table and is not reconstructed. B fields ete_med/ete_iqr_lo/ete_iqr_hi for VI, IV and II only; Huber and Global are intentionally removed to make the baseline question singular. V DBS is a fragile out-of-support result and moves to Supplementary; III belongs to the final performance figure and DBS remains uncomputable there because raw perturbation/view vectors were not retained. C is a conceptual vector diagram, not a quantitative scale. DBS predicts translation direction only, uses VI-frozen magnitude and leaves rotation unchanged; rotation is N/A as a DBS correction output. Suggested Supplementary: V transfer, III N/A provenance, Global/Huber comparison, DBS magnitude sensitivity and block-level failures.',na='DBS rotation correction is N/A; III DBS remains noncomputable and is excluded from this focused main panel.')

def figure7():
    d=g1();e=g2();names=['Raw','Huber','Patch','Full','Estimated Full'];METHOD['Estimated Full']='Estimated Full'
    e=e[e.arm=='est_warmstart'].copy();e['method']='Estimated Full';d=pd.concat([d,e],ignore_index=True)
    f=fig(150);axes=f.subplots(2,2);a,b,c,dd=axes.flat
    panel(a,'A','Physical translation accuracy');panel(b,'B','Physical rotation accuracy');panel(c,'C','Estimated-view gap to oracle Full');panel(dd,'D','Paired translation reduction vs Raw')
    rows=grouped(a,d,names,'et_mm')+grouped(b,d,names,'eR_deg');a.set_ylim(0,205);b.set_ylim(0,6)
    clean(a,'Translation error (mm)');clean(b,'Rotation error (deg)');gap=[];changes=[];forest=[]
    for i,t in enumerate(TR):
        q=subset(d,t);base=q[q.method==METHOD['Raw']].set_index('scan');oracle=q[q.method==METHOD['Full']].set_index('scan');est=q[q.method=='Estimated Full'].set_index('scan')
        ids=oracle.index.intersection(est.index);assert len(ids)==len(oracle)==len(est)
        vals=est.loc[ids,'et_mm']-oracle.loc[ids,'et_mm'];lo,med,hi=point(c,i,vals,'Estimated Full')
        gap.append(dict(traj=t,n=len(vals),q25=lo,median=med,q75=hi))
        for k,n in enumerate(['Huber','Patch','Full','Estimated Full']):
            qq=q[q.method==METHOD[n]].set_index('scan');assert set(qq.index)==set(base.index)
            delta=qq.et_mm.median()-base.et_mm.median()
            paired=base.loc[qq.index,'et_mm']-qq.et_mm;lo,med,hi=summary(paired)
            y=i+(k-1.5)*.15;dd.errorbar(med,y,xerr=[[med-lo],[hi-med]],fmt=M[n],color=C[n],mfc='white' if n=='Estimated Full' else C[n],ms=5,capsize=2,elinewidth=1.05,mew=1)
            changes.append(dict(traj=t,method=n,delta_of_medians_mm=delta,median_paired_delta_mm=-med))
            forest.append(dict(traj=t,method=n,n=len(paired),q25_raw_minus_method=lo,median_raw_minus_method=med,q75_raw_minus_method=hi))
    c.axhline(0,color='#888888',lw=.8,ls='--');c.set_xticks(range(4),[t.upper() for t in TR])
    dd.axvline(0,color='#888888',lw=.8,ls='--');dd.set_yticks(range(4),[t.upper() for t in TR]);dd.set_ylim(-.48,3.48);dd.invert_yaxis()
    clean(c,'Estimated - oracle error (mm)');clean(dd,None,'Framewise translation-error reduction\nrelative to Raw (mm)')
    dd.text(.97,.06,'right of zero: improvement',transform=dd.transAxes,ha='right',fontsize=7.5)
    legend(f,names);table('pose_summary_iqr',pd.DataFrame(rows));table('paired_estimated_gap',pd.DataFrame(gap));table('paired_improvement_forest',pd.DataFrame(forest));table('change_vs_raw',pd.DataFrame(changes))
    ci=csv(G+'G1_MITIGATION/results/method_comparison.csv');table('existing_frozen_confidence_intervals',ci)
    note_source(G+'G3_FINAL_CONFIRMATION/results/single_look_summary.json')
    finish(f,'**Final physical pose accuracy and estimated-view transfer.** (A,B) Raw, Huber, Patch, oracle Full and estimated-view Full on VI development, IV/II held-out and the reserved III evaluation. (C) Paired per-frame translation-error gap between estimated-view warm-start Full and oracle Full. (D) Framewise translation-error reduction relative to Raw (Raw − method; positive values indicate reduction). All points and bars show medians and 25th–75th percentile intervals of saved primary-subset frames or paired frame differences. Patch transfers more consistently in translation, while the benefit of Full view conditioning is trajectory dependent and the estimated pipeline closely follows its oracle counterpart.',
      'Fields: G1 method, et_mm/eR_deg, traj, scan, order, in_support; G2 arm=est_warmstart. Primary selection: VI all 501; IV 156, II 428 and III 371 saved in-support frames. III remains the original reserved single-look evaluation (sealed until all methods frozen, opened exactly once). Oracle Full starts at the reference pose; Estimated Full uses the saved warm-start pipeline, so C combines view and warm-start differences. Hollow red markers identify Estimated Full. A/B/C use descriptive 25th–75th percentile intervals, not CI; existing G1 block-aware CIs are exported separately. D uses paired Raw-method per-frame differences and descriptive 25th–75th percentile intervals. Because paired-median and difference-of-marginal-medians are distinct estimands, II Full is near zero in D while A truthfully shows its marginal median error is worse than Raw (68.86 vs 66.15 mm); both values are exported. No rotation-neutrality claim for Patch: VI Patch rotation median exceeds Raw, and II Full worsens rotation; retained in B. Never describe oracle-gain retention on II as meaningful because oracle itself fails to improve the translation median. Suggested Supplementary: block-bootstrap L=5/10/20 distributions, all-frame III sensitivity, calibration budget and estimated-view perturbation grid.')

def figure8():
    raw=csv(G+'G_GENERALITY/results/geometry_results.csv');raw=raw[(raw.kind=='p2p')&(raw.condition=='structured')]
    dose=csv(G+'G_GENERALITY/results/dose_response.csv');phase=csv(H+'OPTIONAL_PHASE_MAP/results.csv')
    f=fig(152);gs=f.add_gridspec(2,10,height_ratios=[.92,1.08]);a=f.add_subplot(gs[0,:5]);b=f.add_subplot(gs[0,5:]);c=f.add_subplot(gs[1,:3]);d=f.add_subplot(gs[1,3:])
    panel(a,'A','D1: coherent translation mismatch');panel(b,'B','D5: coherent tilt mismatch');panel(c,'C','Observed mismatch regimes');panel(d,'D','Controlled translation-coherence samples')
    records=[]
    for axis,dt,field,xlabel,ylabel in [(a,'D1_appendage_disp','et_med','Appendage displacement (mm)','Translation error (mm)'),(b,'D5_appendage_tilt','eR_med','Appendage tilt (deg)','Rotation error (deg)')]:
        for loss,n in [('ls','Raw'),('huber','Huber'),('trim','Trim')]:
            q=dose[(dose.dtype==dt)&(dose.form==loss)]
            ag=q.groupby('mag')[field].agg(['median','min','max']).reset_index()
            axis.fill_between(ag.mag,ag['min'],ag['max'],color=C[n],alpha=.10,linewidth=0)
            axis.plot(ag.mag,ag['median'],marker=M[n],ls={'Raw':'-','Huber':'--','Trim':':' }[n],color=C[n],lw=1.8,ms=4.5)
            for _,r in ag.iterrows():records.append(dict(dtype=dt,loss=loss,dose=r.mag,median_across_geometry_medians=r['median'],geometry_min=r['min'],geometry_max=r['max'],field=field))
        clean(axis,ylabel,xlabel);axis.set_ylim(bottom=0)
    cells=[]
    for dt,ddose,metric in [('D1_appendage_disp',50,'et_mm'),('D2_missing_component',1,'et_mm'),('D3_local_surface_off',100,'et_mm'),('D4_appendage_scale',.1,'et_mm'),('D5_appendage_tilt',2,'eR_deg')]:
        for geo in ['GA','GB','GC']:
            q=raw[(raw.dtype==dt)&(raw.mag==ddose)&(raw.geometry==geo)];ls=q[q.form=='ls'][metric].median();hu=q[q.form=='huber'][metric].median()
            cells.append(dict(regime=dt[:2],geometry=geo,dose=ddose,metric=metric,ls=ls,huber=hu,ratio=hu/ls))
    ce=pd.DataFrame(cells)
    c.set(xlim=(0,1),ylim=(0,1));c.axis('off')
    boxes=[(.08,.67,'Coherent pose-active\nmismatch','Residual error may remain',C['Full']),(.08,.37,'Localized / gross','Robust loss can reduce error',C['Huber']),(.08,.07,'Low projection','Limited pose error',C['Patch'])]
    for x,y,head,msg,col in boxes:
        c.add_patch(FancyBboxPatch((x,y),.84,.20,boxstyle='round,pad=.015,rounding_size=.025',fc='#FAFBFB',ec=col,lw=1.1))
        c.add_patch(Rectangle((x,y),.035,.20,fc=col,ec='none'))
        c.text(x+.08,y+.13,head,fontsize=8.2,fontweight='bold',va='center');c.text(x+.08,y+.045,msg,fontsize=7.5,color='#58666C',va='center')
    ph=phase[phase.loss=='ls'].copy();scatter=None
    for k,(dt,grp) in enumerate(ph.groupby('dtype')):
        scatter=d.scatter(grp.alpha,grp.eta_t,c=grp.ete_med,cmap='Blues',norm=LogNorm(vmin=ph.ete_med.min(),vmax=ph.ete_med.max()),s=48,marker=['o','s','^','D','v'][k],edgecolors='#4D4D4D',linewidths=.6,label=dt[:2])
    clean(d,r'Translation coherence proxy $\eta_t$',r'Affected fraction $\alpha$');d.set_ylim(0,1.04)
    f.colorbar(scatter,ax=d,location='bottom',pad=.14,label='Raw LS translation error (mm)',shrink=.95)
    d.text(.03,.96,'Empirical discriminator\nNo universal threshold',transform=d.transAxes,va='top',fontsize=8)
    d.legend(frameon=False,ncol=5,loc='lower right',handletextpad=.2,columnspacing=.55,fontsize=7.5)
    legend(f,['Raw','Huber','Trim']);table('dose_response_geometry_ranges',pd.DataFrame(records));table('regime_ratios',ce);table('phase_samples_ls_translation',ph)
    finish(f,'**Controlled synthetic failure-regime boundary across three geometries.** (A,B) D1 translation and D5 rotation dose responses for LS, Huber and Trim. (C) Compact interpretation of the three observed mismatch regimes. (D) Frozen LS controlled translation-coherence samples colored by translation error against affected fraction and translation-coherence proxy. Curves show medians of the three geometry-specific medians (20 repetitions each), with shaded ranges spanning those geometry medians; these are not confidence intervals. Cells use saved 10-repetition summaries. Coherent pose-active mismatch is not reliably neutralized by standard robust weighting, and the observed boundary depends on geometry and regime. Definitions: affected fraction $\\alpha$ = fraction of nominal-model points displaced (or dropped, for missing-component types) by the imposed discrepancy; translation-coherence proxy $\\eta_t=\\|\\sum_i \\mathbf{r}_i\\|/\\sum_i\\|\\mathbf{r}_i\\|$ where $\\mathbf{r}_i$ are point-to-model residual vectors after nearest-neighbor matching (higher = more translation-coherent).',
      'A/B dose_response.csv: dtype, mag, form, geometry, et_med/eR_med; p2p summaries verified against geometry_results.csv. No replicate pooling. Shading spans the three geometry medians and is not uncertainty. C is an evidence-linked regime schematic; the complete numeric Huber/LS endpoint matrix remains exported in regime_ratios.csv for Supplementary, including GB D2 robust failure, D4 near-floor ratios, exploratory complete absence and solver-bound fractions. D results.csv loss=ls, alpha, eta_t, ete_med; D1-D5 use distinct markers. alpha = fraction of nominal-model points affected by the discrepancy (for D2 missing-component: fraction dropped; otherwise: fraction displaced beyond 1e-9 m). eta_t is a normalized residual-coherence proxy = ||sum r_i|| / sum ||r_i|| after NN matching, not exact H-weighted bias and not a universal threshold; eta_R is not mixed with translation. Phase-map 300/325-mm results remain saved solver-limited outcomes without clipping. Suggested Supplementary: numeric endpoint matrix, full LS/Huber phase maps, eta_R rotation phase map, per-geometry dose curves and D2 exploratory .9/1 provenance. No synthetic result is presented as independent hardware validation.')

def docs():
    st=OUT/'master_style';st.mkdir(exist_ok=True)
    (st/'color_palette.md').write_text('# Fixed palette\n\n'+ '\n'.join(f'- {k}: `{v}`; marker `{M.get(k,"o")}`' for k,v in C.items())+'\n\nEstimated Full: hollow red marker. Loss curves: LS solid, Huber dashed, Trim dotted. D1-D5 have distinct muted colors AND o/s/^/D/v shapes. Continuous heatmaps are monotone; ratio heatmap uses a muted diverging scale around 1. Grayscale distinguishability uses shapes, position, line style, and direct numeric ratios.\n',encoding='utf-8')
    (st/'font_and_size.md').write_text('# Typography and export\n\nArial preferred, Liberation Sans/Helvetica fallback. Axis labels 9 pt; ticks and legends 8 pt; panel headings 9 pt bold; panel letters 10 pt bold. Curves 1.5-1.8 pt; uncertainty marks 1-1.2 pt; axes 0.85 pt. White background. PDF embeds TrueType; SVG outlines glyphs for portable appearance. PNG 600 dpi is a preview; PDF is the vector submission master. Mathematical subscripts, superscripts and log-axis exponents are naturally rendered smaller than their 8-11 pt parent text.\n',encoding='utf-8')
    (st/'figure_size_templates.md').write_text('# Final-size templates\n\nSingle column: 85 mm wide (SINGLE_MM). Double column: 178 mm wide (DOUBLE_MM). All current multipanel figures use 178 mm, heights 110-155 mm. Set fig(h) for adaptive height; do not rescale into a single column without relayout. No tight bounding-box crop that silently changes print dimensions.\n\nUser dimensions take precedence over publisher general examples; exact journal column widths should be checked when the destination is selected.\n',encoding='utf-8')
    (st/'publisher_export_notes.md').write_text('# Publisher guidance checked 2026-09-10\n\nUse vector PDF as the submission master; 600-dpi PNG is the requested preview. Elsevier distinguishes 500-dpi combination artwork and 1000-dpi raster line art, so a 600-dpi preview is not claimed universally sufficient as a raster-only submission. Arial is a preferred font and embedded fonts are used.\n\nSources: [Elsevier artwork types](https://www.elsevier.com/en-gb/about/policies-and-standards/author/artwork-and-media-instructions/artwork-types), [Elsevier artwork overview](https://www.elsevier.com/en-gb/about/policies-and-standards/author/artwork-and-media-instructions/artwork-overview), [IEEE resolution and size](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/resolution-and-size/). Target-journal submission portal checks remain author-side.\n',encoding='utf-8')

def main():
    global CURRENT
    parser=argparse.ArgumentParser();parser.add_argument('--figures',type=int,nargs='+',default=list(range(1,9)));args=parser.parse_args()
    docs()
    for n in args.figures:
        CURRENT=n;(OUT/f'Figure{n}').mkdir(exist_ok=True)
        globals()[f'figure{n}']()
    # Recheck every consumed source to prove plotting did not mutate inputs.
    for paths in SOURCES.values():
        for p,h in paths.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,f'Source changed: {p}'
    if len(args.figures)==8:
        lines=['# Build log','',f'Build date: {datetime.datetime.now().isoformat(timespec="seconds")}.','',
          'Read-only inputs verified SHA256 before/after. No method reruns. Human review of scientific scope required for all figures.','',
          '| Figure | Status | Missing | N/A |','|---|---|---|---|']
        for r in LOG:lines.append(f"| {r['figure']} | {r['status']} | {r['missing']} | {r['na']} |")
        for r in LOG:lines+=['',f"## Figure {r['figure']} sources"]+[f'- `{p}`' for p in r['sources']]
        (OUT/'build_log.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    titles=['Concept and workflow','Real patch and range structure','Reference-pose-local non-stationarity','First-order direction and synthetic severity','Robust falsification','Information hierarchy and DBS','Final physical pose accuracy','Synthetic regime boundary']
    manifest='# Figure manifest\n\n| Figure | Role | Files |\n|---|---|---|\n'+'\n'.join(f'| {i} | {t} | Figure{i}/Figure{i}.pdf, .svg, .png; caption draft; notes; plotted data |' for i,t in enumerate(titles,1))
    manifest+='\n\nFinal role split: Figure 1 concept and mechanism; Figure 2 real mismatch; Figure 3 reference-pose non-stationarity; Figure 4 pose-active theory; Figure 5 robust falsification; Figure 6 direct discrepancy subtraction ceiling/risk; Figure 7 final pose performance with III; Figure 8 synthetic regime boundary. Numeric Figure 8 endpoint matrix, p2l detail, V direct discrepancy subtraction transfer, full bootstrap distributions and calibration budget are Supplementary candidates.\n\nCritical author checks: FD gradient versus analytic projection, mixed m/rad native norm, designed-condition correlations, III 371-frame primary versus 1302-frame supplementary, saved block IDs versus inconsistent prose counts, DBS translation-only identity, solver-bound >300-mm synthetic cases, unquantified calibration uncertainty. Read each FigureX_notes.md before using a caption.\n'
    (OUT/'figure_manifest.md').write_text(manifest,encoding='utf-8');(OUT/'master_style/figure_manifest.md').write_text(manifest,encoding='utf-8')
    (OUT/'requirements.txt').write_text('numpy\npandas\nscipy\nmatplotlib>=3.8\nPillow\nPyMuPDF\n',encoding='utf-8')
if __name__=='__main__':main()
