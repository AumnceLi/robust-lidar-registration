# -*- coding: utf-8 -*-
"""E3 aggregate: runtime_summary.csv (required schema) + compact deployment table + key numbers."""
# ==== portable repo root (auto-added; replaces hard-coded D:\doubao) ====
import os as _os
def _repo_root():
    _d = _os.path.dirname(_os.path.abspath(__file__))
    while not _os.path.exists(_os.path.join(_d, '.repo_root')):
        _p = _os.path.dirname(_d)
        if _p == _d:
            raise RuntimeError('repo-root marker .repo_root not found')
        _d = _p
    return _d
_REPO = _repo_root()
def _pp(*_a):
    return _os.path.join(_REPO, *_a).replace('\\', '/')
# ==== end portable root ====

import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F
STAGES=["model_build_ms","query_ms","kdtree_ms","registration1_ms","registration2_ms"]
META={"Raw":("yes (nominal model cached)",1), "Huber":("yes (nominal model cached)",1),
      "Patch":("yes (corrected model+tree cached once)",1), "PatchHuber":("yes (corrected model+tree cached once)",1),
      "Full":("no (query-dependent model+tree per frame)",1),
      "EstimatedFull":("partial (nominal cached; 2nd model query-dependent)",2)}


def block(g):
    tot=g.total_ms.values
    return dict(n_frames=len(g), median_total_ms=np.median(tot), p25_ms=np.percentile(tot,25),
                p75_ms=np.percentile(tot,75), p95_ms=np.percentile(tot,95),
                **{c: float(g[c].median()) for c in STAGES})


def main():
    frm=pd.read_csv(os.path.join(F.E3_OUT,"e3_runtime_framewise.csv"))
    mem=pd.read_csv(os.path.join(F.E3_OUT,"e3_memory.csv")).set_index("method")
    rows=[]
    for (m,tr),g in frm.groupby(["method","trajectory"]):
        d=dict(method=m,trajectory=tr); d.update(block(g)); d["peak_rss_mb"]=float(mem.loc[m,"peak_rss_mb"]); rows.append(d)
    for m,g in frm.groupby("method"):
        d=dict(method=m,trajectory="ALL"); d.update(block(g)); d["peak_rss_mb"]=float(mem.loc[m,"peak_rss_mb"]); rows.append(d)
    summ=pd.DataFrame(rows)
    order={m:i for i,m in enumerate(E_METHODS())}
    tord={t:i for i,t in enumerate(["VI","IV","II","III","ALL"])}
    summ["_m"]=summ.method.map(order); summ["_t"]=summ.trajectory.map(tord)
    summ=summ.sort_values(["_m","_t"]).drop(columns=["_m","_t"]).reset_index(drop=True)
    cols=["method","trajectory","n_frames","median_total_ms","p25_ms","p75_ms","p95_ms"]+STAGES+["peak_rss_mb"]
    summ[cols].to_csv(os.path.join(F.E3_OUT,"runtime_summary.csv"),index=False)

    # compact main table (ALL)
    raw_med=float(summ[(summ.method=="Raw")&(summ.trajectory=="ALL")].median_total_ms.iloc[0])
    main_rows=[]
    for m in E_METHODS():
        r=summ[(summ.method==m)&(summ.trajectory=="ALL")].iloc[0]
        reusable,nreg=META[m]
        main_rows.append(dict(method=m, reusable_model=reusable, registrations_per_frame=nreg,
            median_latency_ms=round(r.median_total_ms,2), p95_latency_ms=round(r.p95_ms,2),
            overhead_vs_Raw_x=round(r.median_total_ms/raw_med,3),
            added_ms_vs_Raw=round(r.median_total_ms-raw_med,2),
            model_build_ms=round(r.model_build_ms,3), query_ms=round(r.query_ms,3),
            kdtree_ms=round(r.kdtree_ms,3), reg1_ms=round(r.registration1_ms,3),
            reg2_ms=round(r.registration2_ms,3), peak_rss_mb=r.peak_rss_mb))
    main=pd.DataFrame(main_rows)
    main.to_csv(os.path.join(F.E3_OUT,"e3_compact_table.csv"),index=False)
    cal=json.load(open(os.path.join(F.E3_OUT,"e3_calibration.json")))
    key=dict(raw_median_ms=raw_med, compact=main_rows, calibration=cal,
             memory=mem.reset_index().to_dict("records"))
    json.dump(key,open(os.path.join(F.E3_OUT,"e3_key_numbers.json"),"w"),indent=2,default=float)
    print("=== runtime_summary (ALL rows) ===")
    print(summ[summ.trajectory=="ALL"][cols].round(3).to_string(index=False))
    print("\n=== compact deployment table ===")
    print(main.to_string(index=False))
    print("\n=== one-time calibration ===")
    for k in ["kmeans_cluster_ms_median","kmeans_label_exact_match","kmeans_partition_ARI",
              "vi_field_build_ms_median","patch_corrected_model_build_ms","patch_kdtree_build_ms",
              "mu_patch_bytes","patches_npz_size_b","predictor_size_b"]:
        print(" ",k,cal[k])


def E_METHODS():
    return ["Raw","Huber","Patch","PatchHuber","Full","EstimatedFull"]

if __name__=="__main__":
    main()
