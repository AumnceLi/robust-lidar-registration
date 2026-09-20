# -*- coding: utf-8 -*-
"""s9_summary.py -- aggregate every number the reports cite into results/summary.json."""
import os, json, numpy as np, pandas as pd
import s0_common as C

def desc(s):
    s=pd.Series(s).dropna()
    return dict(mean=float(s.mean()),std=float(s.std(ddof=1)),median=float(s.median()),
                q05=float(s.quantile(.05)),q25=float(s.quantile(.25)),q75=float(s.quantile(.75)),
                q95=float(s.quantile(.95)),min=float(s.min()),max=float(s.max()))

def main():
    out={}
    per=pd.read_csv(os.path.join(C.RESULTS,"residual_per_scan.csv"))
    out["n_scans"]=int(len(per))
    out["range"]=desc(per.range_m); out["point_count"]=desc(per.point_count)
    out["dt"]=desc(per.dt_seconds[per.dt_seconds>0])
    out["duration_s"]=float(per.timestamp.iloc[-1]-per.timestamp.iloc[0])
    out["median_residual"]=desc(per.median_residual_m)
    out["p95_residual"]=desc(per.p95_residual_m)
    out["mean_residual"]=desc(per.mean_residual_m)
    out["excess_fraction"]=desc(per.excess_return_fraction)
    out["missing_proxy"]=desc(per.missing_proxy)
    for c in ["r1_frac","r2_backface_frac","r3_fov_frac","r4_structured_frac",
              "large_noise_frac","model_backface_frac","model_fov_trunc_frac",
              "model_visible_frac","mean_signed_residual"]:
        out[c]=desc(per[c])
    mc=np.load(os.path.join(C.CACHE,"model_cache.npz"))
    out["model_n_points"]=int(len(mc["xyz"])); out["d_model_nn_mm"]=float(mc["dnn"]*1000)
    out["r1_bound_mm"]=float(2*mc["dnn"]*1000)
    # global residual distribution from every 10th scan
    rs=[]
    for i in range(0,501,10):
        rs.append(np.load(os.path.join(C.CACHE,"scans",f"scan_{i:04d}.npz"))["r"])
    rs=np.concatenate(rs); out["global_resid_mm"]=dict(
        n=int(len(rs)),**{k:float(v) for k,v in zip(
            ["p10","p25","p50","p75","p90","p95","p99"],
            np.percentile(rs,[10,25,50,75,90,95,99]))})
    out["global_frac_gt_2dnn"]=float((rs>2*mc["dnn"]).mean())
    out["global_frac_gt_500mm"]=float((rs>0.5).mean())
    # signed residual global
    sg=[]
    for i in range(0,501,10):
        sg.append(np.load(os.path.join(C.CACHE,"scans",f"scan_{i:04d}.npz"))["signed"])
    sg=np.concatenate(sg); out["global_signed_mm"]=dict(mean=float(sg.mean()*1000),
        median=float(np.median(sg)*1000),std=float(sg.std()*1000))
    # patches
    pp=pd.read_csv(os.path.join(C.RESULTS,"patch_persistence.csv"))
    prof=pp.groupby("patch_id").median_residual.median()
    out["patch_profile_mm"]=dict(min=float(prof.min()*1000),max=float(prof.max()*1000),
        std=float(prof.std()*1000),mean=float(prof.mean()*1000),
        worst_patch=int(prof.idxmax()),best_patch=int(prof.idxmin()),
        ratio=float(prof.max()/prof.min()))
    # null tests
    nt=pd.read_csv(os.path.join(C.RESULTS,"null_tests.csv"))
    out["null"]=json.loads(nt.round(5).to_json(orient="records"))
    # confound
    cf=pd.read_csv(os.path.join(C.RESULTS,"confound_control.csv"))
    out["confound"]=json.loads(cf.round(5).to_json(orient="records"))
    # baseline
    ep=pd.read_csv(os.path.join(C.RESULTS,"baseline_endpoints.csv"))
    out["baseline"]=dict(n=int(len(ep)),converged=int(ep.converged.sum()),
        converge_rate=float(ep.converged.mean()),
        ransac_fitness_max=float(ep.ransac_fitness.max()),
        icp_fit_gt05=int((ep.icp_fitness>0.5).sum()),
        terr=desc(ep.translation_error_m),att=desc(ep.attitude_error_deg),
        n_terr_lt_01=int((ep.translation_error_m<0.1).sum()),
        n_att_lt_10=int((ep.attitude_error_deg<10).sum()),
        runtime_s_mean=float(ep.runtime_s.mean()),
        sym_k_counts=ep.symmetry_equivalent_rotation_k.value_counts().to_dict(),
        sampling="every 5th scan (ids 0,5,...,500), n=101, stratified across range/aspect")
    ea=pd.read_csv(os.path.join(C.RESULTS,"endpoint_association.csv"))
    out["endpoint_assoc"]=json.loads(ea.round(5).to_json(orient="records"))
    if os.path.exists(os.path.join(C.RESULTS,"endpoint_association_robust.csv")):
        er=pd.read_csv(os.path.join(C.RESULTS,"endpoint_association_robust.csv"))
        out["endpoint_assoc_robust"]=json.loads(er.round(5).to_json(orient="records"))
    bv=pd.read_csv(os.path.join(C.RESULTS,"bias_variance.csv"))
    out["bias"]=json.loads(bv.round(5).to_json(orient="records"))
    with open(os.path.join(C.RESULTS,"summary.json"),"w") as f:
        json.dump(out,f,indent=1)
    print(json.dumps({k:out[k] for k in ["n_scans","duration_s","d_model_nn_mm","r1_bound_mm",
        "global_resid_mm","global_frac_gt_2dnn","patch_profile_mm","baseline"]},indent=1))

if __name__=="__main__":
    main()
