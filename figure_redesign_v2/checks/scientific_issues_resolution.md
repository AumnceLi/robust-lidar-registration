# Scientific Issues Resolution (V2 Phase A)

## Issue A: Figure 4(c) matched-RMS error in V1

### Symptom
V1 Figure 4(c) displayed four paired cases with error ratios 2347×, 3151×, 237×, 186×. These do not match the paper's Table 3 (ratios 9.9, 10.6, 8.3, 8.5).

### Root cause
The V1 sub-agent selected **extreme dose points** (e.g., mag=100 mm for D1) where the least-squares registration had already diverged. Dividing two already-diverged registration errors produced spurious ratios of thousands. The selected conditions were:
- P1: GA D1@50.0 / D2@0.25 → 39.16/0.0167 = 2347× (D2 at 0.25 had collapsed to near-zero error)
- P2: GB D1@100.0 / D2@0.25 → 80.77/0.0256 = 3151× (D1@100 had diverged)
- P3: GC D2@0.5 / D3@25.0 → 11.40/0.048 = 237×
- P4: GA D1@25.0 / D5@2.0 → 18.66/0.100 = 186×

None of these correspond to Table 3's matched-RMS criterion (RMS within 5% across conditions).

### Resolution (V2)
- Extracted Table 3 from the verified PDF (`Ast.pdf`, p.8): four cases with RMS pairs 7.95/7.70, 4.06/3.97, 5.33/5.08, 3.75/3.80 (all within 5%).
- Verified e_t values against `dose_response.csv`: max deviation ≤0.002 mm.
- RMS values are not in raw CSVs; they are published medians from the PDF, recorded as such.
- V2 Figure 4(c) shows these four correct cases with ratios 9.9/10.6/8.3/8.5.
- All 2347×/3151×/237×/186× labels removed.

### Files
- `checks/figure4_table3_verification.md` — detailed verification
- `data/derived/figure4_matched_rms_cases.csv` — correct case data
- `data/derived/figure4_table3_verification.csv` — e_t cross-check

---

## Issue B: Figure 6 frame selection provenance

### Symptom
V1 Figure 6 labeled IV278 as "Full best" and II505 as "Full worse*", implying these were best/worst percentile cases. This contradicts the task specification that frames should be median-neighborhood representatives.

### Investigation
- Checked `revision_experiments/06_II_failure_cases/ii_failure_representative_frames.csv`: both IV278 and II505 are listed as **median-bin** representative frames.
- Checked `revision_experiments/_lib/p4_run.py`: selection rule for median bin = rank 0.45–0.55, effect=full_minus_patch closest to bin median.
- IV278: effect=+38.82 mm (Full improves over Patch in this median bin)
- II505: effect=−24.60 mm (Full degrades vs Patch in this median bin, on_bound=1)
- Neither frame is from best10 (q90+) or worst10 (q10-) categories.

### Resolution (V2)
- Removed "Full best" / "Full worse*" labels entirely.
- Both frames labeled as median-neighborhood representative frames in the caption and manifest.
- II505's on_bound=1 status is traced to the original `replay79_arms.csv` record and noted factually (robust safeguard triggered at 0.30 m / 15°), not interpreted as a protocol error.
- `manifests/case_selection.csv` records selection_source=median_neighborhood, rule, effect, nearest_d, and on_bound status for both frames.

### Files
- `manifests/case_selection.csv` — provenance record
- `checks/figure6_reproduction_gate.log` — reproduction gate output
- `checks/figure6_render_check.md` — 26/26 render consistency checks
