# Exp.1 — Scan timing, target motion and reference-pose semantics audit

**Scope:** VI / IV / II / III only (V excluded, per Phase-1 instruction). Post-hoc / secondary
diagnostic for III; descriptive association only, **not** a motion-distortion causal proof.
All numbers below are computed from the shipped assets (`.3d` / `.pose` / frozen caches); no main
result file was modified.

Companion artifacts: `motion_frame_metrics.csv` (per-frame), `support_selected_vs_unselected.csv`
(group medians/IQR), `fig_timing_motion.png` (panels A–D).

---

## 1. Timing-semantics audit (one item per reviewer question)

| # | Question | Finding in the current code / assets | Evidence |
|---|----------|----------------------------------------|----------|
| 1 | Separate **scan timestamp** vs **pose timestamp**? | **No.** There is exactly one timestamp per frame: line 1 of `XXXX.pose`. One `.pose` per `.3d` with matching numeric id. | `s0_common.load_pose`, `r6_ext_cache.load_pose_generic`; counts equal per trajectory (501/2428/1253/1302). |
| 2 | Does `.pose` anchor scan **start / middle / end**? | The in-repo `epos_README.txt` only says *"absolute time in seconds"* — it does **not** state start/middle/end. The codebase consistently **assumes scan-END** (`s0_common`: "pose anchors the scan END instant"; `IDENTIFIABILITY_AUDIT.md`, `CONTRACT_AUDIT.md` attribute scan-end anchoring to the upstream EPOS-Lid source paper). This cannot be independently re-verified from assets shipped in this repo. | `external_dataset_scout/intermediate/samples/epos_README.txt`; prior audits. |
| 3 | Is a frame **accumulated over the scan time**? | Each `.3d` is one accumulated ASCII `x y z` cloud. There is **no intra-scan timing channel**, so the within-scan accumulation/sweep profile cannot be reconstructed from data. | `.3d` header inspection; `CONTRACT_AUDIT.md` ("xyz-only, no intensity/ring/per-point timestamp"). |
| 4 | Per-point timestamp? | **No.** Only three Cartesian columns; no intensity/ring/time-per-point. | `.3d` byte inspection; `GREEN_ASSETS.md`, `CONTRACT_AUDIT.md`. |
| 5 | Deskew / motion compensation? | **None anywhere.** GT alignment is a single rigid transform `aligned = R_GTᵀ(pc − t_GT)`; no per-point pose propagation, no undistortion. | `s0_common.build_aligned_cloud`, `r6_ext_cache.build`, II/III cache builders. |
| 6 | Is the reference pose **interpolated**? | **No.** Frame `i` uses pose `i` directly (nearest, same id); no interpolation between adjacent poses. | all cache builders. |
| 7 | Extrinsic matrix: source and value actually used? | **No separate sensor↔body extrinsic is applied.** `.pose` directly gives target↔LiDAR (`t` = target position in LiDAR frame; scalar-first Hamilton quaternion = rotation target→LiDAR). The nominal CAD model is already in the target/body frame, so the registration chart is written directly in that frame (identity extrinsic). | `notation.md`; `stage5_parameter_table.py` (model_frame = TARGET/body); `s0_common`. |
| 8 | Discontinuous time gaps between frames? | With an **isolated-dropout** rule (dt > 5× local 6-neighbour median) there are **0 isolated gaps** on all four trajectories. The framerate is **adaptive**: dt varies smoothly within a trajectory (slowdown *regimes*, not dropouts). All velocities below divide by the **real** dt; no finite difference crosses a flagged gap. | `rev_common.gap_flags`; dt ranges in §2. |

> **Adjacent-frame interval is never used as single-scan duration.** Because there is no
> per-point time channel and no documented scan-window length, intra-scan duration is unknown;
> only inter-pose dt is observable and it is used solely for inter-frame motion.

### BLOCKED flag
**`EXACT_DESKEW_DIAGNOSTIC_BLOCKED`** — EPOS-Lid ships xyz-only clouds with one pose timestamp
per frame and no per-point timestamps, scan-window duration, or sweep order. A point-level
deskew / intra-scan motion-distortion diagnostic therefore **cannot be executed rigorously from
the available assets**, and no scan-time model is invented here. What *is* testable is inter-frame
reference-pose motion (§2) and its association with errors/support selection (§3–4).

---

## 2. Reference-pose inter-frame motion (real dt; geodesic rotation)

Local linear velocity magnitude is frame-invariant (`‖Rᵀ Δt‖ = ‖Δt‖`); angular speed is the
geodesic angle between consecutive target→LiDAR rotations divided by real dt. Rotation increment
is `deg·geodesic(R_i,R_{i+1})`, translation increment `‖t_{i+1}−t_i‖`.

| Traj | n | dt med [min,max] s | ω med (p5–p95; max) deg/s | v med mm/s | rot incr/frame med deg | trans incr/frame med mm |
|---|---|---|---|---|---|---|
| VI  | 501  | 0.963 [0.708, 1.260] | **8.146** (6.07–9.61; 11.00) | 17.82 | 7.908 | 13.44 |
| IV  | 2428 | 0.411 [0.325, 1.632] | **4.896** (3.63–6.65; 9.82)  | 10.02 | 1.640 | 3.38 |
| II  | 1253 | 0.717 [0.329, 1.842] | **1.063** (0.99–1.07; 1.17)  | 19.96 | 0.765 | 13.57 |
| III | 1302 | 0.530 [0.328, 1.932] | **1.063** (1.06–1.07; 1.10)  | 19.99 | 0.562 | 10.45 |

The four trajectories span distinct motion regimes: VI is the fast-tumble development set
(~8 °/s), IV is intermediate (~5 °/s, adaptive dt with slowdown bands), II and III are slow
(~1.06 °/s). Linear approach speed is ~10–20 mm/s. Because per-frame rotation increment =
ω·dt, the adaptive framerate keeps the per-frame rotation comparable even where dt changes.

## 3. Support-domain selected vs unselected (frozen `insup`, τ_support = 0.4403)

Coverage matches the frozen numbers: **IV 156/2428, II 428/1253, III 371/1302; VI 501/501**.

| Traj | group | n | range med m | view-angle med ° | ω med deg/s | v med mm/s | raw residual RMS med mm | valid pts med |
|---|---|---|---|---|---|---|---|---|
| IV | selected | 156 | 14.82 | 26.2 | 5.05 | 1.58 | 99.4 | 9926 |
| IV | unselected | 2272 | 6.05 | 2.8 | 4.90 | 10.04 | 74.4 | 10702 |
| II | selected | 428 | 10.73 | 33.2 | 1.063 | 20.00 | 84.7 | 10025 |
| II | unselected | 825 | 6.33 | 20.7 | 1.063 | 19.93 | 65.9 | 10699 |
| III | selected | 371 | 11.51 | 39.4 | 1.063 | 20.04 | 69.6 | 10268 |
| III | unselected | 931 | 4.91 | 34.9 | 1.063 | 19.95 | 67.6 | 10753 |
| VI | selected | 501 | 12.09 | 34.9 | 8.146 | 17.82 | 104.1 | 10048 |

**Reading.** The frozen support gate is overwhelmingly a **range / viewing-geometry** gate:
selected frames sit at far range and at viewing directions close to the VI training views
(large view angle / view-direction change), whereas unselected frames are near-range front
views. It is **not** a low-motion selection — selected and unselected angular speeds are
essentially identical on II/III (1.063 vs 1.063) and IV (5.05 vs 4.90), and linear speeds are
likewise not systematically lower in the selected set. Selected frames do not have lower raw
residual RMS (if anything slightly higher at far range on IV/II), so the support mask is not
cherry-picking "easy/low-residual/low-motion" frames. Full IQRs in the CSV.

## 4. Association with realised pose error (Fig. A–D; descriptive only)

Within-trajectory Spearman correlations of local angular speed with realised Raw translation
error and with Patch−Raw paired gain:

| Traj | ρ(Raw trans error, ω) | ρ(Patch−Raw gain, ω) |
|---|---|---|
| VI  | −0.080 | −0.038 |
| IV  | −0.052 | +0.015 |
| II  | +0.115 | +0.030 |
| III | −0.056 | −0.086 |

All within-trajectory associations are negligible (|ρ| ≤ 0.12). Differences across trajectories
in error/gain track the **distinct motion regimes** (clusters along x), not a continuous
within-regime dependence on angular speed. There is no descriptive signature that Patch gain is
an artifact of fast motion (which would be the expected pattern if un-deskewed intra-scan
distortion drove the result), but this remains an **association statement**: with
`EXACT_DESKEW_DIAGNOSTIC_BLOCKED`, intra-scan distortion cannot be measured or ruled out at
point level.

## 5. Bottom line for Phase 1
- Time semantics are fully audited: one pose timestamp/frame (assumed scan-END from upstream
  docs, not re-verifiable in-repo), no per-point time, **no deskew, no pose interpolation, no
  separate extrinsic**, adaptive inter-frame dt, zero isolated gaps.
- Motion is quantified with real dt; the support mask is a range/view-geometry gate, not a
  motion-speed or residual gate.
- Pose error and Patch gain show no meaningful within-regime association with angular speed.
- Exact intra-scan deskew diagnosis is **BLOCKED** for lack of per-point timestamps; no scan-time
  model is fabricated.
