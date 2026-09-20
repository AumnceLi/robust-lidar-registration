# GENERALITY_DECISION.md — controlled cross-geometry study (section G)

- Date: 2026-09-10. Optional generality stage; uses the **frozen** G0 solver/config, no predictor, no tuning,
  no new estimator. Three synthetic spacecraft-like geometries (GA box+twin wings; GB elongated bus+single
  wing+dish+boom; GC asymmetric cubesat+4 brackets), known GT (identity), realistic partial LiDAR views
  (75° front-face visibility, 2 mm sensor noise), 20 replicates/cell.

## VERDICT: **GENERALITY_PASS (qualified)** — the core mechanism reproduces on all three non-EPOS geometries,
and the study additionally delineates the boundary between the regime robust ICP handles and the regime it does not.

### 1. Numerical self-null holds
At mismatch magnitude 0 the GT-started displacement is 0.014–0.051 mm on every geometry (LS/Huber/Trim), i.e. the
solver introduces no bias of its own — the same numerical-null standard used in G0.

### 2. Coherent, spatially-extensive structured mismatch reproduces the full chain (the paper's regime)
**D1 whole-appendage-assembly displacement**, median GT-start e_t (LS, median over geometries), monotone on all
three geometries:

| magnitude | 0 | 2 mm | 5 | 10 | 25 | 50 | 100 |
|---|---|---|---|---|---|---|---|
| structured e_t [mm] | 0.02 | 0.91 | 2.30 | 8.93 | 17.6 | 39.2 | 80.7 |
| equal-RMS isotropic noise [mm] | – | 0.04 | 0.11 | 0.32 | 1.84 | 7.42 | 26.7 |
| **structured / noise** | – | **23×** | **20×** | **28×** | **9.6×** | **5.3×** | **3.0×** |

- ‖∇J(T_GT)‖ rises with mismatch and tracks the resulting bias (GF2, log–log monotone cloud): the
  mismatch→non-stationarity→biased-optimum chain is not EPOS-specific.
- **Robust ICP does not remove it**: at 50 mm, LS 39.2 → Huber 42.8 → Trim 50.7 mm (GF3). A coherent shift of a
  large visible fraction is not an independent outlier, so Huber/trim weights cannot reject it — the exact
  G0_PASS_ATTENUATED signature, now on geometries that share no geometry with EPOS.
- Coherence, not noise power, is the cause: equal-RMS isotropic noise produces 3–28× smaller systematic bias.

**D5 whole-assembly tilt** gives the rotation-domain analogue: a coherent assembly yaw is absorbed as a global
**rotation** error (median eR up to 1.3–1.5° for a 2° tilt on GA/GB; monotone in eR), which robust ICP likewise
does not remove. Translation stays small because the discrepancy is rotational — the bias follows the
discrepancy's degree of freedom, as the mechanism predicts.

### 3. The study sharpens the boundary (a result, not a weakness)
- **D3 local surface offset** biases only in proportion to the affected visible fraction and is strongly
  suppressed by robust ICP (50 mm: LS 3.6 → Huber 1.2 → Trim 0.03); on the large GA bus a small patch is
  absorbed, on the small GC bus it is not. **D4 one-sided scale** is near-null (≤0.8 mm) and robust-removed.
- **D2 unmodeled component** shows a sharp regime: a *partially* unmodeled feature (≤90%) is absorbed by the
  correctly-matching majority (≈0 bias), whereas a *wholly* absent large appendage is a gross-outlier failure
  (LS diverges to the 300 mm basin clip) that **Huber largely rescues (300→11.6 mm)**.
- Interpretation: standard robust ICP is designed for — and succeeds on — **independent/localized/gross
  outlier** structure (D2-full, D3, D4). It fails specifically on **coherent, spatially-extensive** mismatch
  (D1, D5), which is precisely the structured nominal-model mismatch regime the paper addresses. This makes the
  G0 falsification logic *stronger*: robust ICP is shown to work where it should, yet still not on the paper's
  target phenomenon.

### 4. How Contribution 1 may now be widened
- Permitted: "the chain from coherent structured scan–model mismatch to GT objective non-stationarity and a
  biased local optimum, which standard robust ICP only attenuates, is reproduced across multiple distinct
  spacecraft-like geometries (three controlled configurations) in addition to the EPOS trajectories, and is
  distinct in kind from the independent gross-outlier regime that robust ICP does handle."
- Still bounded: these are **synthetic, known-GT** configurations (one sensor-noise model, no real material/
  reflectance effects); they establish mechanism generality, not sensor-level performance. The real EPOS
  evidence (G0–G3) remains the empirical backbone. Claim "geometry-class-level mechanism generality", not
  "validated on arbitrary real hardware".

### 5. Outputs
`results/geometry_results.csv` (9120 rows), `dose_response.csv`, `noise_control.csv`, `generality_summary.csv`;
`figures/GF1_dose_response.png`, `GF2_gradient_vs_bias.png`, `GF3_formulations.png`, `GF4_struct_vs_noise.png`;
`protocol.md`, `frozen_config.yaml`. No parameter was chosen from outcomes; negative/weak cells (D4, partial D2,
D3 on the large bus) are retained as-is.

**GENERALITY_PASS (qualified): the mechanism is not specific to the EPOS target geometry; its scope is the
coherent structured-mismatch regime, with an explicit, demonstrated boundary against the gross-outlier regime.**
