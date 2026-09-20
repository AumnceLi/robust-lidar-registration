# G_GENERALITY / protocol.md — controlled cross-geometry study (OPTIONAL section G)

**Status:** generality only. It does NOT train/touch the predictor, does NOT tune any parameter, and does NOT
replace the real EPOS-LiDAR evidence (G0–G3). It tests whether Contribution 1's mechanism chain
*structured mismatch → ‖∇J(T_GT)‖ > 0 → GT-started biased optimum* is an artifact of the single EPOS target
geometry, by reproducing it on three synthetic spacecraft-like geometries with known ground truth.

## 1. Three non-EPOS target configurations (analytic-normalled surface samples, ~13 mm spacing)
- **GA** — 1.0 m box bus + twin 2.0×0.8 m solar wings + antenna (56.6k nominal points, 4 components).
- **GB** — elongated 1.4×0.8×0.8 m bus + single large wing + tilted dish + boom (52.0k, 4 components).
- **GC** — 0.6 U asymmetric cubesat + four varied brackets (14.5k, 5 components).
Nominal CAD M is the complete closed model; the observed scan is a **partial view** (front-facing surfaces
within a 75° half-angle from one of three frozen sensor vantages that see the target appendage), plus 2 mm
isotropic sensor noise — i.e. the scan is a realistic partial LiDAR view registered against a complete CAD,
exactly as in the real experiments. Ground-truth pose is identity, so the ICP displacement from xi=0 is the bias.

## 2. Five structured discrepancy types (applied to the TRUE geometry; CAD stays nominal)
- **D1 appendage-assembly displacement** — all non-bus surfaces translated along the assembly normal.
- **D2 unmodeled component** — the scan contains a feature (progressively, fraction f) that the nominal CAD
  lacks (the realistic "as-built feature absent from CAD" case).
- **D3 local surface offset** — a local ~44 cm bus-face region displaced outward.
- **D4 one-sided appendage scale growth** — assembly extends one-sided along its span.
- **D5 appendage-assembly tilt** — coherent yaw of the assembly about the body hinge axis (rotation-dominant).
Magnitude sweeps (magnitude 0 = numerical self-null): D1/D3 ∈ {0,2,5,10,25,50,100} mm; D2 ∈ {0,.25,.5,.75};
D4 ∈ {0,.005,.01,.025,.05,.10}; D5 ∈ {0,.1,.25,.5,1,2}°. 20 independent replicates per cell (vantage × sensor
noise), fixed seeds.

## 3. Controls
- **Self-null** (magnitude 0): scan = partial view of the nominal CAD; GT displacement must be ~0 (solver sanity).
- **Matched-RMS unstructured noise control**: isotropic Gaussian noise with RMS equal to each linear magnitude
  (2…100 mm), NO coherent component deviation. If coherent structure causes systematic bias while equal-RMS
  isotropic noise does not, "structured" (not noise power) is the cause.

## 4. Frozen evaluation (identical solver/config to G0)
p2p LS / Huber (δ=1.345, 1.4826 MAD, floor = model NN spacing) / Trim(0.80), plus p2l LS; basin 0.30 m/15°,
max_iter 40, FD 5 mm/0.25°. Per cell record ‖∇J(T_GT)‖, e_t, e_R, ΔJ. Ordinary bootstrap over the 20 replicates
(B=2000) for medians/95% CI. No formulation is chosen by outcome.

## 5. Decision (generality)
**GENERALITY_PASS** requires, on all three geometries: self-null ≈ 0; a monotone (non-decreasing) structured
dose–response with e_t clearly above the matched-RMS noise control at matched magnitude for the dominant
discrepancy types; ‖∇J(T_GT)‖ rising with mismatch; and Huber/Trim at best attenuating (mirroring
G0_PASS_ATTENUATED) except for the gross-outlier regime D2, where robust ICP is expected to help strongly (that
contrast is itself a finding). Failure on all three geometries would shrink Contribution 1 to the EPOS target.
