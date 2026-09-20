# E1 — Coarse / Non-Reference Initialization Robustness (FINAL ROUND)

**Question (pre-registered, deliberately narrow).** *When initialization error is increased beyond
the previously tested 50 mm / 2° local regime, does Patch preserve or degrade the capture behaviour
of the frozen ICP pipeline?* This is **not** a global-registration study and no global initializer is
introduced. All solver / safeguard / iteration / method definitions remain frozen.

## 1. Design (fixed before running)

- **Initialization grid.** Reused local levels L0=0, L1=10 mm/0.5°, L2=30 mm/1°, L3=50 mm/2°
  (verbatim from `final_targeted/initialization_sensitivity_framewise.csv`); **new coarse levels
  L4=100 mm/5°, L5=200 mm/10°, L6=300 mm/15°**. **L7=500 mm/20° is not run**: its 0.50 m start
  already exceeds the frozen 0.30 m translation safeguard at x0 (a probe shows it clips on iteration
  1), so the brief's precondition ("code allows AND does not violate the safeguard") is false.
- **Perturbations.** Same sign-balanced deterministic family as L1–L3: 4 translation directions
  with cyclically paired rotation axes (`t3_common.DIRS`/`ROT_PAIR`). The new L4–L6 vectors are
  constructed by the *same* code; max difference from the shipped family on L1–L3 is exactly 0.
- **Frames.** Frozen 20-frame/trajectory roster (VI/IV/II/III = 80 frames), not re-selected.
- **Methods.** Raw, Huber, Patch, PatchHuber (same set as the local experiment for continuity); the
  **primary comparison is Raw vs Patch**. Estimated Full / Full are excluded per brief (Estimated
  Full's internal nominal pass would entangle initialization with the estimated-view effect).
- **Pre-registered outcomes.**
  - *Capture-A (relative):* final t-error < injected t-error **and** final r-error < injected r-error.
  - *Capture-B (recovery):* final pose back inside the previously validated local basin
    (≤ 50 mm **and** ≤ 2°) — an **experimental recovery criterion, not a mission tolerance**.
  - *path-safeguard trigger* = frozen 0.30 m/15° basin clip; *iteration-cap*; *numerical failure* =
    non-finite final pose; *solver-valid* = finite pose and no safeguard clip (cap allowed).
- **Fidelity gate before extension.** The new runner reproduces every shipped L0–L3 row
  (4160 rows): max |Δt| = 5.7e-14 mm, max |Δr| = 1.8e-15 deg, **0** mismatches in iteration count,
  termination, safeguard or cap flags (`e1_fidelity_gate.json`).
- Counts: 8000 framewise cells (320 reference + 6 levels × 1280); new compute = L4–L6 = 3840.

## 2. Result — Capture-B probability (final pose recovered to ≤ 50 mm / ≤ 2°)

Capture-B is only discriminative where the reference-started solution can itself reach ≤ 50 mm
(II, III). On VI/IV the reference-started median error is already 115–161 mm for both methods, so
Capture-B is structurally 0 for Raw **and** Patch at every level — the continuous-error results
below are the informative quantity there.

| traj | method | L0 | L1 | L2 | L3 | L4 | L5 | L6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| II  | Raw | .350 | .350 | .350 | .350 | .300 | .150 | **.100** |
| II  | Patch | .400 | .400 | .400 | .400 | .375 | .300 | **.200** |
| III | Raw | .350 | .350 | .350 | .350 | .312 | .262 | **.212** |
| III | Patch | .450 | .450 | .462 | .438 | .425 | .388 | **.325** |
| IV  | Raw/Patch | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| VI  | Raw/Patch | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**Patch Capture-B ≥ Raw at every level of every trajectory.** Both methods decline as the start
moves further out, but Patch declines no faster (II L6: .20 vs .10; III L6: .325 vs .212).

## 3. Result — continuous median final translation error (mm)

| traj | method | L0 | L3 (50/2) | L4 (100/5) | L5 (200/10) | L6 (300/15) |
|---|---|---:|---:|---:|---:|---:|
| VI  | Raw | 160.6 | 160.8 | 160.9 | 160.1 | 162.5 |
| VI  | Patch | 115.3 | 115.4 | 115.5 | 115.5 | 116.8 |
| IV  | Raw | 151.6 | 151.2 | 151.5 | 151.7 | 153.4 |
| IV  | Patch | 140.4 | 140.4 | 141.2 | 141.6 | 143.9 |
| II  | Raw | 60.6 | 60.2 | 58.0 | 57.7 | 65.2 |
| II  | Patch | 47.1 | 49.6 | 51.2 | 49.8 | 58.2 |
| III | Raw | 49.2 | 49.3 | 49.3 | 49.6 | 62.9 |
| III | Patch | 40.2 | 40.0 | 40.0 | 40.1 | 41.0 |

The paired Patch-over-Raw median gain stays **positive at every level on every trajectory**
(VI ≈ +45 mm, IV ≈ +5 mm, II ≈ +10 mm, III ≈ +7–8 mm; paired-better fraction 0.66–1.00). Patch's
advantage is essentially flat from L0 to L5 and is retained at L6. Rotation medians stay within
~1° of reference through L5 and widen modestly at L6 (e.g. IV Raw 2.4°→5.8°, Patch 1.8°→5.0°).

## 4. Result — failure / safeguard behaviour

- **Numerical failures: 0** across all 8000 cells.
- **Path-safeguard clips are ~0 through L5** (only VI Raw L5 = 2.5%) and appear for **both** methods
  at L6: VI Raw 35.0% / Patch 30.0%, III Raw 22.5% / Patch 16.2%, II Raw 12.5% / Patch 10.0%,
  IV Raw 16.2% / Patch 17.5% (tie). Patch never trips the safeguard materially more than Raw.
- Capture-A (relative reduction) rises with perturbation size as expected and is ≥ Raw for Patch
  (e.g. VI L5 Patch 1.00 vs Raw .975; II L4 .90 vs .80).
- A pre-registered rule flags a level as "Patch-relative degradation" if Patch Capture-B falls
  >0.10 below Raw **or** Patch safeguard rate exceeds Raw by >0.10. **No such level exists on any
  trajectory** (`e1_key_numbers.json: patch_relative_degradation_onset = None`).

## 5. Answers to the three E1 questions

- **Q1 — Does Patch lose capture more easily under coarse init?** **No.** On the only trajectories
  where Capture-B is reachable (II/III), Patch's recovery probability is higher than Raw's at every
  level including L6; its safeguard-clip and numerical-failure rates are never worse by a meaningful
  margin; its paired error advantage never reverses.
- **Q2 — Does Patch shrink Raw's basin?** **No measurable shrinkage.** The Patch-vs-Raw gap is stable
  from L0 to L5 and remains positive at L6; the level at which capture degrades is the same for both.
- **Q3 — Where does degradation begin?** The *shared* local-ICP behaviour starts to degrade at
  **L6 (300 mm / 15°)**, i.e. at the frozen safeguard boundary: both methods show increased basin
  clips and slightly larger final errors. Through L5 (200 mm / 10°) both are essentially unchanged
  from the reference-pose result. This is the expected, allowed outcome: *both* pipelines are local
  ICP and deteriorate outside the validated basin — Patch does not, and is not claimed to, turn the
  pipeline into a global method.

## 6. Verdict and limitations

- **Flag: no `COARSE_INIT_LIMITATION` for Patch.** Patch preserves the frozen pipeline's capture
  behaviour and its accuracy advantage out to 300 mm/15°.
- **KEEP-AS-LIMITATION (shared, method-agnostic):** both Raw and Patch are local methods and begin
  to trip the 0.30 m/15° safeguard at L6; beyond it (L7) the frozen safeguard itself refuses the
  start. The paper should state this honestly rather than imply global capture.
- Capture-B is uninformative (structurally 0) on VI/IV because their reference errors exceed 50 mm;
  this is a property of those hard scans, reported alongside continuous errors rather than hidden.
- Huber/PatchHuber show the same qualitative pattern (see `e1_coarse_init_summary.csv`); they do not
  change any conclusion and are secondary to Raw vs Patch.

## 7. Artifacts (hashes in `e1_provenance.json`)

`e1_coarse_L4L6_framewise.csv` (new), `e1_coarse_init_framewise.csv` (canonical L0–L6, 8000 rows),
`e1_coarse_init_summary.csv`, `e1_fidelity_gate.{json,txt}`, `e1_key_numbers.json`,
`fig_e1_captureB.png`, `fig_e1_median_et.png`, `fig_e1_boundary_fail.png`.
Runners: `e1_run_coarse.py`, `e1_fidelity_gate.py`, `e1_combine_analyze.py`, `e1_provenance.py`.
