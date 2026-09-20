# -*- coding: utf-8 -*-
"""E3 timing benchmark (single process / single thread) + one-time calibration cost + memory spawn.

Fairness: BLAS threads pinned to 1 via env; os.cpu_count pinned to 1; all cKDTree queries single
thread (f3.OneThreadTree); identical for every method. 80 frozen roster frames (20/traj). Per frame
per method: WARMUP discarded calls, then REPEAT timed calls; per-frame statistic = median over
repeats; deployment latency distribution = across-frame median/p25/p75/p95 (computed in analyze).

Correctness gate: on VI roster frames the timed Raw/Huber/Patch/Full reproduce frozen g1_oracle_vi
(M0/M2/M4/M5) and EstimatedFull reproduces g2 est_warmstart to <1e-6 mm -- proving the benchmark
times the FROZEN methods, not altered ones.
"""
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

import os, sys, time, json, subprocess
for _v in ["OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"]:
    os.environ[_v] = "1"
os.cpu_count = lambda: 1
import numpy as np, pandas as pd
sys.path.insert(0, _pp("final_three_experiments/03_runtime_memory"))
sys.path.insert(0, _pp("final_three_experiments/_lib"))
import f3_common as F
import e3_core as E
from sklearn.cluster import MiniBatchKMeans

WARMUP, REPEAT = 1, 5
STAGES = ["model_build_ms","query_ms","kdtree_ms","registration1_ms","registration2_ms","total_ms"]


def med_repeat(calls):
    arr = {k: np.median([c[k] for c in calls]) for k in STAGES}
    return arr


def calibration_cost(env):
    model, normals = env["model"], env["fz"]["normals"]
    feat = np.concatenate([model, 0.30 * normals], axis=1)
    # time the FROZEN clustering recipe (k=24, seed=42, n_init=20, batch=4096); verify partition
    def fit():
        return MiniBatchKMeans(n_clusters=24, random_state=42, n_init=20, batch_size=4096).fit(feat)
    for _ in range(1): fit()
    ts = []
    for _ in range(3):
        t0 = time.perf_counter(); km = fit(); ts.append((time.perf_counter()-t0)*1000)
    frozen_lab = env["fz"]["plab"]
    label_exact = bool((km.labels_ == frozen_lab).all())
    # partition equivalence even if label ids permuted (Adjusted Rand)
    from sklearn.metrics import adjusted_rand_score
    ari = float(adjusted_rand_score(frozen_lab, km.labels_))
    # VI mu_patch field construction
    G_hier = F.G.hierarchy_library
    def field(): return G_hier(env["Vmean"], env["Vcnt"])
    field(); tf = []
    for _ in range(50):
        t0 = time.perf_counter(); field(); tf.append((time.perf_counter()-t0)*1000)
    # one-time reusable corrected-model build + KD-tree (Patch deployment cache)
    cm = []; tr = []
    for _ in range(20):
        t0 = time.perf_counter(); mp = env["model"] + env["mu_patch"][env["plab"]]; cm.append((time.perf_counter()-t0)*1000)
        t0 = time.perf_counter(); F.kdtree1(mp); tr.append((time.perf_counter()-t0)*1000)
    out = dict(kmeans_cluster_ms_median=float(np.median(ts)), kmeans_label_exact_match=label_exact,
               kmeans_partition_ARI=ari, vi_field_build_ms_median=float(np.median(tf)),
               patch_corrected_model_build_ms=float(np.median(cm)), patch_kdtree_build_ms=float(np.median(tr)),
               mu_patch_bytes=int(env["mu_patch"].nbytes),
               patches_npz_size_b=os.path.getsize(F.G.PATCH_NPZ),
               predictor_size_b=os.path.getsize(F.G.PREDICTOR),
               model_points=int(model.shape[0]))
    return out


def main():
    env = E.build_env()
    g1 = pd.read_csv(os.path.join(F.ROOT,"g_chain","G1_MITIGATION","results","g1_oracle_vi.csv"))
    g2 = pd.read_csv(os.path.join(F.ROOT,"g_chain","G2_ESTIMATED_VIEW","results","g2_vi.csv"))
    g1m = {m: g1[g1.method==m].set_index("order") for m in g1.method.unique()}
    g2w = g2[g2.arm=="est_warmstart"].set_index("order")
    rep_rows, frame_rows, xcheck = [], [], []
    tasks = F.roster_tasks()
    t0 = time.perf_counter()
    for ii,(traj,order) in enumerate(tasks):
        P = F.Rv.load_aligned(traj,order); view = F.view_geometry(traj,order)
        for method in E.METHODS:
            for _ in range(WARMUP): E.stage_run(method,P,view,env)
            calls, last = [], None
            for r in range(REPEAT):
                s,res = E.stage_run(method,P,view,env); calls.append(s); last=res
                rep_rows.append(dict(trajectory=traj,frame_id=order,method=method,rep=r,**s,
                                     et_mm=res["et_mm"],eR_deg=res["eR_deg"],iters=res["iters"]))
            ms = med_repeat(calls)
            frame_rows.append(dict(trajectory=traj,frame_id=order,method=method,n_repeat=REPEAT,**ms,
                                   et_mm=last["et_mm"],eR_deg=last["eR_deg"],iters=last["iters"]))
            if traj=="VI":
                if method=="Raw": xcheck.append(("Raw",order,last["et_mm"],g1m["M0_raw_p2p"].loc[order,"et_mm"]))
                if method=="Huber": xcheck.append(("Huber",order,last["et_mm"],g1m["M2_raw_huber"].loc[order,"et_mm"]))
                if method=="Patch": xcheck.append(("Patch",order,last["et_mm"],g1m["M4_patch_corr"].loc[order,"et_mm"]))
                if method=="Full": xcheck.append(("Full",order,last["et_mm"],g1m["M5_full_corr"].loc[order,"et_mm"]))
                if method=="EstimatedFull": xcheck.append(("EstimatedFull",order,last["et_mm"],g2w.loc[order,"et_mm"]))
        if (ii+1)%10==0: print(f"  {ii+1}/80 frames {time.perf_counter()-t0:.0f}s",flush=True)
    rep_df=pd.DataFrame(rep_rows); frm=pd.DataFrame(frame_rows)
    rep_df.to_csv(os.path.join(F.E3_OUT,"e3_runtime_repeats.csv"),index=False)
    frm.to_csv(os.path.join(F.E3_OUT,"e3_runtime_framewise.csv"),index=False)
    # correctness gate
    xc=pd.DataFrame(xcheck,columns=["method","order","bench","frozen"])
    xc["absdiff"]=(xc.bench-xc.frozen).abs()
    worst=xc.groupby("method").absdiff.max().to_dict()
    assert max(worst.values())<1e-6, ("E3 frozen-method correctness gate failed",worst)
    # calibration cost
    cal=calibration_cost(env)
    cal["correctness_max_abs_et_diff"]=worst
    json.dump(cal,open(os.path.join(F.E3_OUT,"e3_calibration.json"),"w"),indent=2)
    print("correctness max |et diff| vs frozen:", {k: round(v, 4) for k, v in worst.items()})
    print("calibration:",cal)
    # ---- spawn isolated memory workers ----
    mem=[]
    for m in E.METHODS:
        p=subprocess.run([sys.executable,os.path.join(F.E3_OUT,"e3_mem_worker.py"),"--method",m],
                         capture_output=True,text=True,
                         env={**os.environ})
        line=[l for l in p.stdout.splitlines() if l.startswith("JSON_RESULT")]
        if not line:
            print("MEM WORKER FAIL",m,p.stderr[-800:]); raise SystemExit("memory worker failed: "+m)
        mem.append(json.loads(line[0].replace("JSON_RESULT ","")))
    pd.DataFrame(mem).to_csv(os.path.join(F.E3_OUT,"e3_memory.csv"),index=False)
    print("memory:",pd.DataFrame(mem).to_string(index=False))
    print(f"DONE timing in {time.perf_counter()-t0:.0f}s")


if __name__=="__main__":
    main()
