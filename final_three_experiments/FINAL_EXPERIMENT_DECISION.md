# FINAL EXPERIMENT DECISION — Final Three-Experiment Round

**Scope honored.** Only E1 (coarse initialization), E2 (VI held-out), E3 (runtime/memory) were run.
No new method, no parameter tuning, no main-config change, no new comparator, no frame
re-selection, no further hyper-parameter sweep. Frozen config unchanged: K=24, normal weight 0.30,
MiniBatchKMeans seed 42, support rule, registration solver, basin safeguard, and the Raw / Patch /
Huber / Patch+Huber / Full / Estimated-Full definitions. Every result carries exact command, config,
seed, input/output SHA-256, framewise results, aggregate CSV, and provenance JSON.

`STOP_EXPERIMENTS = TRUE` after this round regardless of outcome.

---

## Q1. Does Patch keep capture behaviour at least as good as Raw under coarser initialization?

**YES.** Extending the frozen ICP from the 50 mm/2° local regime to 100/5°, 200/10°, 300/15° with the
identical sign-balanced perturbation family:

- Patch's Capture-B recovery probability is **≥ Raw at every level on every trajectory** (at
  300 mm/15°: II 0.20 vs 0.10; III 0.33 vs 0.21; VI/IV structurally 0 for both because their
  reference errors exceed 50 mm).
- The paired Patch-over-Raw translation gain stays positive at every level (VI ≈ +45 mm; IV ≈ +5 mm;
  II ≈ +10 mm; III ≈ +7–8 mm; paired-better fraction 0.66–1.00).
- **Zero numerical failures in 8000 cells**; the frozen safeguard first trips for *both* methods at
  L6, and Patch never clips more often than Raw by a meaningful margin.
- The pre-registered "Patch-relative degradation onset" rule fires on **no** trajectory.
- Fidelity: the new runner reproduces the shipped L0–L3 results to ≤5.7e-14 mm with 0 categorical
  mismatches.

→ Patch neither loses capture earlier nor narrows Raw's basin. **No `COARSE_INIT_LIMITATION` for
Patch.** The only limitation is method-agnostic: both are local ICP and degrade at the 300 mm/15°
safeguard edge (see Limitations).

## Q2. Does the Patch-over-Raw effect keep its sign after VI leave-one-block-out?

**YES — retained at essentially full magnitude.** Six-fold LOBO over VI's frozen contiguous blocks
(frozen 24-patch partition; field mean rebuilt from the five training blocks; leakage hard-asserted):

- OOF pooled over all 501 scans: Raw 161.4 mm → held-out Patch 117.5 mm, **paired +43.1 mm**;
  in-sample all-VI Patch is 116.8 mm (+43.5 mm), so withholding a whole block costs only **0.44 mm
  of benefit (≈1%) / 0.69 mm of error**.
- **6/6 blocks positive** (+38.7…+45.3 mm) and **every scan improved**; block-bootstrap 95% CI
  [39.6, 44.9] mm and moving-block CIs exclude 0; block sign-flip p = 5e-4.
- Registration path reproduces frozen g1 M0/M4 to 2.8e-14 mm.

→ **No `VI_OVERFIT_WARNING`** (`OOF_POSITIVE_RETAINED`). The development gain is not an in-sample
calibration artifact in any meaningful amount; wording must remain "reduces concern," not "proves no
overfitting."

## Q3. Computational overhead of Patch / Full / Estimated Full vs Raw?

Single workstation (Core Ultra 9 285K), single-thread BLAS + single-thread NN, CPU-only, 80 frozen
scans, median of 5 timed runs:

| Method | median ms/frame | ×Raw | p95 ms | registrations/frame | peak RSS |
|---|---:|---:|---:|---:|---:|
| Raw | 477.5 | 1.00 | 808.1 | 1 | 158 MB |
| **Patch** (geometry cached once) | **412.5** | **0.86** | 611.5 | 1 | 158 MB |
| **Full** (per-frame query model) | **427.7** | **0.90** | 702.0 | 1 | 158 MB |
| **Estimated Full** | **953.3** | **2.00** | 1638.7 | 2 | 160 MB |

- **Patch adds no per-frame overhead** (cached corrected model/tree) and is slightly faster (fewer
  iterations). **Full** spends only ≈12 ms/frame on view query (0.09) + model build (0.84) + KD-tree
  (10.9); registration dominates, so it is comparable to Raw. **Estimated Full ≈ 2× Raw** because it
  runs two registrations (nominal + corrected).
- Memory is effectively identical across methods (~158 MB; method-specific ΔRSS 3–5 MB).
- One-time re-calibration: 24-patch clustering **151.7 ms** (reproduces frozen partition exactly,
  ARI 1.0), VI field assembly **0.18 ms**, cached KD-tree 11 ms; on-disk artifacts 29 KB.

→ **`DEPLOYMENT_COST_LIMITATION` applies only to Estimated Full (≈2× latency, two registrations).**
Cached Patch and Full carry no meaningful cost penalty.

---

## Flags

| Flag | Triggered? | Note |
|---|---|---|
| `COARSE_INIT_LIMITATION` (Patch worse under coarse init) | **No** | shared local-ICP degradation at L6 only |
| `VI_OVERFIT_WARNING` (OOF benefit gone/reversed) | **No** | OOF retains 99% of in-sample benefit, 6/6 positive |
| `DEPLOYMENT_COST_LIMITATION` (Estimated Full very slow) | **Yes (Est. Full only)** | ≈2× single-registration latency; Patch/Full cheap |

## FINAL_SUBMISSION_STATUS = `READY_WITH_LIMITATION`

Rationale: no result reverses or weakens a core claim — Patch preserves capture (Q1), the VI gain
survives held-out calibration (Q2), and the cheap Patch/Full paths add no cost (Q3). Two honest,
non-blocking limitations must be stated (shared local basin edge; Estimated-Full 2× cost), hence
"with limitation" rather than an unqualified READY; there is no claim-reversing robustness warning.

### MUST_ADD_TO_PAPER
1. The single coarse-initialization figure + short paragraph (`PAPER_INSERTIONS_FINAL.md §1`):
   Patch preserves capture through 300 mm/15°; both local methods meet the safeguard at L6.
2. The VI LOBO table + short paragraph (`§2`): OOF +43.1 mm, 6/6 blocks positive, only ~1% optimism.
3. The compact runtime table + short paragraph (`§3`): Patch 0.86×/Full 0.90×/Est.Full 2.00× Raw,
   ~158 MB, 0.15 s one-time calibration; **no** "real-time/flight-ready" wording.

### SHOULD_ADD_TO_PAPER
4. One sentence that Capture-B is an experimental recovery criterion (≤50 mm/2°), not a mission
   tolerance, and is structurally 0 on VI/IV because their reference errors exceed 50 mm.
5. The Huber/PatchHuber coarse and held-out numbers as supplemental (same qualitative conclusions).
6. The benchmark environment and single-thread fairness statement (threads pinned identically).

### KEEP_AS_LIMITATION (state honestly; do NOT "fix" with new algorithms)
7. Both Raw and Patch are **local** ICP: capture degrades and the frozen 0.30 m/15° safeguard begins
   to trip at 300 mm/15°; 500 mm/20° starts beyond the safeguard. No global initializer is claimed.
8. **Estimated Full costs ≈2× a single registration** (two-pass); the cheaper cached Patch path does
   not. Report as a deployment trade-off.
9. VI LOBO shows internal cross-block generalization only; external generalization still rests on
   IV/II (III secondary/post-hoc). Do not write "proves no overfitting."

---

## Deliverables index (`final_three_experiments/`)
- `FINAL_THREE_AUDIT.md` (G0 reuse audit)
- `01_coarse_initialization/`: `E1_COARSE_INIT_REPORT.md`, framewise/summary CSVs, 4 figures,
  fidelity gate, provenance.
- `02_vi_leave_block_out/`: `E2_VI_OOF_REPORT.md`, framewise/OOF/fold CSVs, summary + fold
  provenance, provenance.
- `03_runtime_memory/`: `E3_RUNTIME_REPORT.md`, `runtime_summary.csv`, compact table, raw repeats,
  memory, calibration, provenance.
- `final_three_summary.csv`, `PAPER_INSERTIONS_FINAL.md`, this file.
