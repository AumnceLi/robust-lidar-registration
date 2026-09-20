# -*- coding: utf-8 -*-
"""g3_freeze_manifest.py -- generate FINAL_FREEZE_MANIFEST immediately before the one-and-only III single-look.
Hashes every frozen asset/code/config that the single-look will use. Nothing here reads Dataset III point clouds."""
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

import os, sys, hashlib, json, datetime
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G

GCHAIN = _pp("g_chain")
PHASE = _pp("structured_mismatch_phase0/scripts")
TJ = _pp("tj2_supplemental")
OUT = os.path.join(GCHAIN, "G3_FINAL_CONFIRMATION", "FREEZE_MANIFEST.md")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

FILES = [
 ("common/g_common.py", os.path.join(GCHAIN, "common", "g_common.py")),
 ("G0 scripts/g0_run.py", os.path.join(GCHAIN, "G0_ROBUST_FALSIFICATION", "scripts", "g0_run.py")),
 ("G0 scripts/g0_stats.py", os.path.join(GCHAIN, "G0_ROBUST_FALSIFICATION", "scripts", "g0_stats.py")),
 ("G0 frozen_config", os.path.join(GCHAIN, "G0_ROBUST_FALSIFICATION", "frozen_config.yaml")),
 ("G0 decision", os.path.join(GCHAIN, "G0_ROBUST_FALSIFICATION", "G0_DECISION.md")),
 ("G1 scripts/g1_run.py", os.path.join(GCHAIN, "G1_MITIGATION", "scripts", "g1_run.py")),
 ("G1 scripts/g1_stats.py", os.path.join(GCHAIN, "G1_MITIGATION", "scripts", "g1_stats.py")),
 ("G1 frozen_config", os.path.join(GCHAIN, "G1_MITIGATION", "frozen_config.yaml")),
 ("G1 decision", os.path.join(GCHAIN, "G1_MITIGATION", "G1_DECISION.md")),
 ("G2 scripts/g2_run.py", os.path.join(GCHAIN, "G2_ESTIMATED_VIEW", "scripts", "g2_run.py")),
 ("G2 scripts/g2_perturb.py", os.path.join(GCHAIN, "G2_ESTIMATED_VIEW", "scripts", "g2_perturb.py")),
 ("G2 scripts/g2_stats.py", os.path.join(GCHAIN, "G2_ESTIMATED_VIEW", "scripts", "g2_stats.py")),
 ("hierarchy/hierarchy_transfer.py", os.path.join(GCHAIN, "HIERARCHY_TRANSFER", "scripts", "hierarchy_transfer.py")),
 ("frozen predictor", os.path.join(PHASE, "cache", "rescue", "VI_ONLY_PREDICTOR_FROZEN.npz")),
 ("frozen model_cache", os.path.join(PHASE, "cache", "model_cache.npz")),
 ("frozen patches", os.path.join(PHASE, "cache", "patches.npz")),
 ("phase0 numerical core s0_common", os.path.join(PHASE, "s0_common.py")),
 ("phase0 numerical core m_common", os.path.join(PHASE, "m_common.py")),
 ("TJ2 support screen", os.path.join(TJ, "metadata", "support_screen_summary.json")),
 ("TJ2 cd summary", os.path.join(TJ, "metadata", "cd_summary.json")),
 ("untouched ledger", os.path.join(GCHAIN, "UNTOUCHED_CONFIRMATORY_LEDGER.md")),
]

def main():
    lines = []
    lines.append("# FINAL_FREEZE_MANIFEST (G3)\n")
    lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} local, BEFORE any Dataset III point-cloud byte is read.\n")
    lines.append("## Frozen scientific choices\n")
    lines.append("- predictor: VI_ONLY_PREDICTOR_FROZEN.npz ; k=16 ; range_std=%.15f ; tau_support=%.15f ; alpha_VI=%.15f ; 24 patches"
                 % (G.RANGE_STD, G.TAU_SUPPORT, G.ALPHA_VI))
    lines.append("- robust objective (G0 M2): Huber IRLS, delta=%.3f, scale=1.4826 MAD floored at model NN spacing 0.00811 m; secondary trim keep=%.2f"
                 % (G.HUBER_DELTA, G.TRIM_KEEP))
    lines.append("- basin 0.30 m / 15 deg; max_iter 40; tol 1e-8(p2p)/1e-9(p2l); FD 5 mm / 0.25 deg; nearest fixed-model correspondence")
    lines.append("- correction (G1): m_corr[i] = m[i] + mu_{lab(i)}(z); levels global/patch/full as in hierarchy_library; ORACLE view z(T_GT)")
    lines.append("- deployable (G2): T0 = frozen raw p2p LS local optimum; z0=z(T0); warm-start second registration; patch fallback policy frozen")
    lines.append("- evaluation metrics: e_t=||t_hat-t_GT|| mm, e_R=angle(R_hat R_GT^T) deg; block bootstrap L=5/10/20 B=2000; sign-flip L=5")
    lines.append("- confirmatory trajectory: Dataset III (metadata-only selection; 371 in-support, 6/6 orientation blocks, deciles 1-4)")
    lines.append("- Dataset I stays permanently sealed; no substitution on outcome grounds; single-look, no re-run/edit/frame removal\n")
    lines.append("## SHA256 of every frozen file used by the single-look\n")
    lines.append("| artifact | sha256 |\n|---|---|")
    for name, p in FILES:
        if os.path.exists(p):
            lines.append(f"| {name} | `{sha(p)}` |")
        else:
            lines.append(f"| {name} | MISSING: {p} |")
    lines.append("\n## Expected single-look outputs (frozen list)\n")
    for f in ["G3_FINAL_CONFIRMATION/results/single_look_results.csv",
              "G3_FINAL_CONFIRMATION/results/g0_iii.csv", "G3_FINAL_CONFIRMATION/results/g1_iii.csv",
              "G3_FINAL_CONFIRMATION/results/g2_iii.csv", "G3_FINAL_CONFIRMATION/figures/*",
              "G3_FINAL_CONFIRMATION/FINAL_CONFIRMATION_DECISION.md"]:
        lines.append(f"- {f}")
    lines.append("\n## Pre-registered confirmation criteria (decided BEFORE opening III)\n")
    lines.append("C1 (mechanism survives robust): III Huber median e_t remains >> matched self-null and > LS*0.5 (attenuation only).")
    lines.append("C2 (mitigation actionable): best of {patch,full} oracle median e_t < raw M0 with paired sign-flip p<0.05 and >=80% frames improved.")
    lines.append("C3 (deployable): estimated-view warm pipeline retains >=70% of the oracle mitigation and beats raw on >=60% of in-support frames.")
    lines.append("CONFIRMED = C1&C2&C3 ; PARTIALLY_CONFIRMED = C1 and only one of C2/C3 ; NOT_CONFIRMED = C1 fails or both C2/C3 fail.")
    txt = "\n".join(lines) + "\n"
    with open(OUT, "w", encoding="utf-8") as f: f.write(txt)
    print(txt)
    print("[written]", OUT)

if __name__ == "__main__":
    main()
