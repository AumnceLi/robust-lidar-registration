# -*- coding: utf-8 -*-
"""Verify the four Table 3 matched-RMS cases for Figure 4(c).

Two independent checks are performed and recorded:

(1) e_t cross-check against raw experiment table
    D:\\doubao\\g_chain\\G_GENERALITY\\results\\dose_response.csv (form == 'ls'):
    for each condition we locate the dose whose ls median is closest to the
    published Table 3 value and require |et_raw - et_published| <= ET_TOL.

(2) 5% matched-RMS criterion (the claim made by the panel title):
    for each pair, rel = |rms_A - rms_B| / max(rms_A, rms_B) * 100%.
    Every pair must satisfy rel <= RMS_MATCH_PCT = 5%.  The RMS summaries are
    NOT stored in any raw CSV (only error medians are); they are the published
    frozen-experiment condition medians from PDF Table 3, recorded as such.

The translation-error ratio is the LARGER e_t divided by the SMALLER (whichever
arm), and is checked against the published ratio.

Outputs:
  data/derived/figure4_table3_verification.csv  (full record)
  checks/figure4_table3_5pct_check.log          (human-readable verdict)
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

import sys, os
sys.path.insert(0, _pp("figure_redesign_v2/configs"))
from paths import TABLE3_CASES, SRC, DATA_DERIVED_DIR, CHECKS_DIR
import pandas as pd

ET_TOL = 0.002          # mm, published Table 3 rounding precision
RATIO_TOL = 0.15        # ratio rounding tolerance
RMS_MATCH_PCT = 5.0     # matched-RMS criterion: relative gap <= 5 %

df = pd.read_csv(SRC["dose_response"])

cond_map = {
    "D1 coherent displacement": "D1_appendage_disp",
    "D3 local mismatch": "D3_local_surface_off",
    "D4 span growth": "D4_appendage_scale",
    "D5 coherent tilt": "D5_appendage_tilt",
}
Y_LABEL = {0: "GA · D1/D3", 1: "GB · D4/D3", 2: "GB · D4/D5", 3: "GC · D3/D4"}

log_lines = []
def log(msg=""):
    print(msg)
    log_lines.append(msg)

results, all_ok = [], True
log("=== Figure 4(c) Table 3 verification ===")
log(f"[criterion] matched-RMS relative gap <= {RMS_MATCH_PCT:.0f}%  "
    f"(denominator = the larger RMS of the pair)")
log("[source] e_t verified against dose_response.csv (ls medians); "
    "RMS = published PDF Table 3 medians (no RMS field exists in raw CSVs)\n")

for i, case in enumerate(TABLE3_CASES):
    geo = case["geometry"]
    da, db = cond_map[case["family_A"]], cond_map[case["family_B"]]
    sub_a = df[(df.geometry == geo) & (df.dtype == da) & (df.form == "ls")].copy()
    sub_b = df[(df.geometry == geo) & (df.dtype == db) & (df.form == "ls")].copy()
    sub_a["diff"] = (sub_a.et_med - case["et_A"]).abs()
    sub_b["diff"] = (sub_b.et_med - case["et_B"]).abs()
    ba, bb = sub_a.loc[sub_a["diff"].idxmin()], sub_b.loc[sub_b["diff"].idxmin()]

    et_a_raw, et_b_raw = float(ba.et_med), float(bb.et_med)
    d_a, d_b = abs(et_a_raw - case["et_A"]), abs(et_b_raw - case["et_B"])
    # ratio = larger / smaller
    ratio_raw = max(et_a_raw, et_b_raw) / min(et_a_raw, et_b_raw)
    ratio_ok = abs(ratio_raw - case["ratio"]) <= RATIO_TOL
    # 5% RMS match
    rms_a, rms_b = float(case["rms_A"]), float(case["rms_B"])
    rms_gap = abs(rms_a - rms_b) / max(rms_a, rms_b) * 100.0
    rms_ok = rms_gap <= RMS_MATCH_PCT
    et_ok = (d_a <= ET_TOL) and (d_b <= ET_TOL)
    ok = et_ok and rms_ok and ratio_ok
    all_ok = all_ok and ok

    results.append(dict(
        case=i + 1, pair_id=Y_LABEL[i], geometry=geo,
        family_A=case["family_A"], dtype_A=da, mag_A=ba.mag,
        et_A_pub=case["et_A"], et_A_raw=round(et_a_raw, 4), et_A_diff=round(d_a, 4),
        family_B=case["family_B"], dtype_B=db, mag_B=bb.mag,
        et_B_pub=case["et_B"], et_B_raw=round(et_b_raw, 4), et_B_diff=round(d_b, 4),
        rms_A_pub=rms_a, rms_B_pub=rms_b,
        rms_rel_gap_pct=round(rms_gap, 3), rms_within_5pct=bool(rms_ok),
        ratio_pub=case["ratio"], ratio_raw=round(ratio_raw, 2), ratio_ok=bool(ratio_ok),
        et_ok=bool(et_ok), case_pass=bool(ok),
    ))
    log(f"Case {i+1}  {Y_LABEL[i]}")
    log(f"  A {case['family_A']:28s} mag={ba.mag:<6} et_pub={case['et_A']:.3f} "
        f"et_raw={et_a_raw:.4f} (d={d_a:.4f})  RMS={rms_a:.2f}")
    log(f"  B {case['family_B']:28s} mag={bb.mag:<6} et_pub={case['et_B']:.3f} "
        f"et_raw={et_b_raw:.4f} (d={d_b:.4f})  RMS={rms_b:.2f}")
    log(f"  RMS relative gap = {rms_gap:.2f}%  -> within 5%: {rms_ok}")
    log(f"  ratio larger/smaller = {ratio_raw:.2f} (pub {case['ratio']}) -> {ratio_ok}")
    log(f"  -> {'PASS' if ok else 'FAIL'}\n")

out = pd.DataFrame(results)
os.makedirs(DATA_DERIVED_DIR, exist_ok=True)
out.to_csv(os.path.join(DATA_DERIVED_DIR, "figure4_table3_verification.csv"), index=False)

log("SUMMARY")
log(out[["pair_id", "rms_A_pub", "rms_B_pub", "rms_rel_gap_pct",
         "rms_within_5pct", "ratio_pub", "ratio_raw", "case_pass"]].to_string(index=False))
verdict = "ALL PASS: 4/4 pairs within 5% RMS, e_t and ratios verified" if all_ok \
    else "FAIL: at least one matched-RMS / e_t / ratio check failed"
log("\nVERDICT: " + verdict)

os.makedirs(CHECKS_DIR, exist_ok=True)
with open(os.path.join(CHECKS_DIR, "figure4_table3_5pct_check.log"), "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")
print("\nSaved verification CSV and log.")
assert all_ok, verdict
