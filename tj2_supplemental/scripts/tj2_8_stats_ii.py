# -*- coding: utf-8 -*-
"""TJ2 statistics + frozen external gate for the single Dataset II outcome test.
Same estimators as frozen r10_stats.py (moving-block bootstrap of the median, vector-pairing
permutation), seed 42, B 2000; ADDS the mandated larger-block-length sensitivity (L=5/10/20)
and per-support-block reporting. Primary = P3 p2p IN_SUPPORT; p2l confirmatory secondary."""
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
from scipy import stats
PHASE0 = _pp("structured_mismatch_phase0/scripts"); sys.path.insert(0, PHASE0)
import m_common as M

TJ = _pp("tj2_supplemental"); OD = os.path.join(TJ, "cache", "ii")
RES = os.path.join(TJ, "results"); os.makedirs(RES, exist_ok=True)
CONDS = ["raw", "N1", "N2", "N3"]; OBJ = ["p2p", "p2l"]; B = 2000; SEED = 42
BLOCKS = [(143, 197), (238, 510), (602, 701)]          # prospective IN_SUPPORT temporal blocks (scan id, inclusive)

def mb_median_ci(v, L, B=B, seed=SEED):
    v = np.asarray(v, float); v = v[np.isfinite(v)]; n = len(v); nb = int(np.ceil(n / L))
    rng = np.random.default_rng(seed); out = np.empty(B)
    for b in range(B):
        st = rng.integers(0, n, nb)
        out[b] = np.median(np.concatenate([v[s:s + L] for s in st]))
    return [float(x) for x in np.percentile(out, [2.5, 97.5])]

def vecpair_perm(a, b, B=B, seed=SEED):
    ok = (np.linalg.norm(a, axis=1) > 1e-12) & (np.linalg.norm(b, axis=1) > 1e-12); idx = np.where(ok)[0]
    def mc(ia, ib):
        x, y = a[ia], b[ib]
        return np.median(np.einsum("ti,ti->t", x, y) / (np.linalg.norm(x, axis=1) * np.linalg.norm(y, axis=1) + 1e-15))
    rng = np.random.default_rng(seed); obs = mc(idx, idx); null = np.empty(B)
    for q in range(B): null[q] = mc(idx, rng.permutation(idx))
    return float(obs), float((1 + (null >= obs).sum()) / (B + 1))

def cosvec(a, b):
    return np.einsum("ti,ti->t", a, b) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-15)

def dirstats(pred, obs, sel):
    a = pred[sel, :3]; b = obs[sel, :3]
    ok = (np.linalg.norm(a, axis=1) > 1e-12) & (np.linalg.norm(b, axis=1) > 1e-12); a, b = a[ok], b[ok]
    if len(a) < 5: return dict(n=int(len(a)))
    cosv = cosvec(a, b); med, pp = vecpair_perm(a, b)
    return dict(n=int(len(a)), median=float(np.median(cosv)), mean=float(cosv.mean()),
                ci_block_L5=mb_median_ci(cosv, 5), ci_block_L10=mb_median_ci(cosv, 10),
                ci_block_L20=mb_median_ci(cosv, 20), frac_pos=float((cosv > 0).mean()),
                perm_p=pp, mag_spearman=float(stats.spearmanr(np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1)).statistic))

def blockstats(pred, obs, ids, insup):
    out = []
    for (a, b) in BLOCKS:
        m = insup & (ids >= a) & (ids <= b)
        aa, bb = pred[m, :3], obs[m, :3]
        ok = (np.linalg.norm(aa, axis=1) > 1e-12) & (np.linalg.norm(bb, axis=1) > 1e-12)
        c = cosvec(aa[ok], bb[ok]) if ok.sum() else np.array([])
        out.append(dict(scan_range=f"{a}-{b}", n=int(m.sum()),
                        median_cos=float(np.median(c)) if len(c) else None,
                        frac_pos=float((c > 0).mean()) if len(c) else None))
    return out

def main():
    E = np.load(os.path.join(OD, "ext_objective_ii.npz")); PR = np.load(os.path.join(OD, "ext_predict_ii.npz"))
    insup = PR["insup"]; ids = E["ids"]
    res = dict(trajectory="Dataset_II", n=int(len(ids)), n_in_support=int(insup.sum()),
               n_out_support=int((~insup).sum()), tau=float(PR["tau"]), P1={}, P2={}, P3={}, blocks={})
    # P1 / P2
    for c in CONDS:
        g = E[f"{c}__g"]; sg = E["self_gnorm"]; xs = E[f"{c}__xistar"]; onb = E[f"{c}__onbnd"]
        for ki, kn in enumerate(OBJ):
            G = g[:, :, ki]; gn = np.linalg.norm(G, axis=1); ok = np.isfinite(gn) & (gn > 1e-12); Gc = G[ok]
            mu = Gc.mean(0); S = np.cov(Gc.T); T2 = len(Gc) * mu @ np.linalg.pinv(S) @ mu
            p_hot = float(stats.f.sf((len(Gc) - 6) / (6 * (len(Gc) - 1)) * T2, 6, len(Gc) - 6))
            u = Gc / gn[ok, None]
            res["P1"][f"{c}|{kn}"] = dict(gnorm_median=float(np.median(gn)),
                gnorm_self_median=float(np.median(sg[:, ki])), ratio=float(np.median(gn) / np.median(sg[:, ki])),
                hotelling_p=p_hot, grad_dir_concentration=float(np.linalg.norm(u.mean(0))))
            t = xs[:, :3, ki] * 1000; r = np.degrees(xs[:, 3:, ki]); tm = np.linalg.norm(t, axis=1); rm = np.linalg.norm(r, axis=1)
            signcons = float(np.mean([(np.sign(t[:, a]) == np.sign(t[:, a].mean())).mean() for a in range(3)]))
            ax = xs[:, 3:, ki]; ax = ax / (np.linalg.norm(ax, axis=1, keepdims=True) + 1e-15)
            res["P2"][f"{c}|{kn}"] = dict(mean_t_mm=[float(x) for x in t.mean(0)], med_t_mm=float(np.median(tm)),
                t_ci_block_L5=mb_median_ci(tm, 5), med_r_deg=float(np.median(rm)), sign_consistency=signcons,
                rot_axis_concentration=float(np.linalg.norm(np.nanmean(ax, 0))), on_bound_frac=float(onb[:, ki].mean()))
    # P3
    pred = PR["dxi"]; obs = E["raw__xistar"]
    for ki, kn in enumerate(OBJ):
        res["P3"][kn] = {sn: dirstats(pred[:, :, ki], obs[:, :3, ki],
                          {"IN": insup, "OUT": ~insup, "ALL": np.ones(len(obs), bool)}[sn])
                         for sn in ["IN", "OUT", "ALL"]}
        res["blocks"][kn] = blockstats(pred[:, :, ki], obs[:, :3, ki], ids, insup)
    res["P3"]["D1_minus"] = {sn: dirstats(-PR["d1"], obs[:, :3, 0],
                          {"IN": insup, "OUT": ~insup, "ALL": np.ones(len(obs), bool)}[sn])
                             for sn in ["IN", "OUT", "ALL"]}
    # frozen external gate on P3 p2p IN_SUPPORT
    q = res["P3"]["p2p"]["IN"]
    gate = dict(endpoint="P3 p2p translation-direction cosine, IN_SUPPORT, raw", n=q["n"],
        median_cos=q["median"], ci95_L5=q["ci_block_L5"], frac_pos=q["frac_pos"], perm_p=q["perm_p"],
        thresholds=dict(median_min=0.60, ci95_lower_gt=0.0, frac_pos_min=0.70, perm_p_max=0.01))
    checks = dict(median_ge_060=q["median"] >= 0.60,
                  ci95_lower_gt_0=q["ci_block_L5"][0] > 0.0,
                  frac_pos_ge_070=q["frac_pos"] >= 0.70,
                  perm_p_le_001=q["perm_p"] <= 0.01)
    gate["checks"] = checks; gate["PASS"] = bool(all(checks.values()))
    res["gate"] = gate
    json.dump(res, open(os.path.join(RES, "ext_stats_ii.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(gate, open(os.path.join(RES, "gate_ii.json"), "w"), indent=1, ensure_ascii=False)
    # console summary
    print(f"== Dataset II n={res['n']} IN={res['n_in_support']} OUT={res['n_out_support']}")
    for kn in OBJ:
        for sn in ["IN", "OUT", "ALL"]:
            x = res["P3"][kn][sn]
            if x.get("n", 0) < 5: continue
            print(f"  P3 {kn} {sn:3s} n={x['n']:4d} med={x['median']:.3f} "
                  f"CI_L5={[round(v,3) for v in x['ci_block_L5']]} CI_L10={[round(v,3) for v in x['ci_block_L10']]} "
                  f"CI_L20={[round(v,3) for v in x['ci_block_L20']]} frac+={x['frac_pos']:.3f} p={x['perm_p']:.4f} magRho={x['mag_spearman']:.2f}")
    p1 = res["P1"]["raw|p2p"]; p2 = res["P2"]["raw|p2p"]
    print("  P1 raw|p2p ratio=%.1f hotelling_p=%.2e gconc=%.3f" % (p1["ratio"], p1["hotelling_p"], p1["grad_dir_concentration"]))
    print("  P2 raw|p2p meanT=%s medT=%.1fmm CI_L5=%s sign=%.3f onb=%.3f" %
          ([round(x, 1) for x in p2["mean_t_mm"]], p2["med_t_mm"], [round(x,1) for x in p2["t_ci_block_L5"]],
           p2["sign_consistency"], p2["on_bound_frac"]))
    for kn in OBJ:
        print(f"  per-IN-block {kn}:", [(b["scan_range"], b["n"], None if b["median_cos"] is None else round(b["median_cos"],3),
                                        None if b["frac_pos"] is None else round(b["frac_pos"],3)) for b in res["blocks"][kn]])
    print("  GATE:", json.dumps(checks), "->", "PASS" if gate["PASS"] else "FAIL")

if __name__ == "__main__":
    main()
