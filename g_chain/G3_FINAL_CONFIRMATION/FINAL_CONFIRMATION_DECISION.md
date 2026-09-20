# FINAL_CONFIRMATION_DECISION.md — G3 untouched single-look (Dataset III)

**Verdict: CONFIRMED.**

Dataset III was selected as the confirmatory trajectory from **pose-only metadata** (371 in-support frames,
6/6 orientation blocks, four temporal deciles); its point clouds were downloaded and read **exactly once**,
after G0–G2 and the hierarchy analysis were complete and frozen (see `FREEZE_MANIFEST.md`, all SHA256 recorded).
Acquisition integrity gates passed before any outcome was computed: zip = 94,194,038 B (expected), every zip
entry CRC-valid, 1302 .3d + 1302 .pose, and the pose-only concat-SHA256 matched the pre-recorded fingerprint
`cf1f0d3a…a64f2c`. The frozen support rule reproduced the metadata-screen count **371/1302 exactly**. No
parameter, threshold, formulation, frame subset or correction was changed after the single look; there was no
second run. Dataset I remains sealed.

The pre-registered criteria (written in `FREEZE_MANIFEST.md` before opening III) are evaluated below on the
371 in-support frames (primary); all 1302 frames are reported secondarily and labelled as out-of-support
extrapolation where applicable.

## C1 — mechanism survives a standard robust registration: **PASS**
Median GT-started translation displacement e_t (p2p), real cloud vs matched model-self null:

| formulation | LS | Huber | Trim | self-null (Huber) |
|---|---:|---:|---:|---:|
| III in-support [mm] | 75.0 | 55.9 | 55.0 | 8.7e-14 |

- Robust ICP only **attenuates** (75.0→55.9 mm Huber; Huber stays at 0.745×LS, i.e. > 0.5×LS as pre-registered);
  it does not restore GT stationarity. Residual Huber bias is ≈5.6×10¹³ times the matched self-null.
- **100%** of in-support frames still leave GT by >10 mm under Huber, and **every one of the 8 temporal blocks**
  has median Huber displacement >10 mm. This is the same G0_PASS_ATTENUATED signature seen on VI/IV/II/V.

## C2 — frozen historical mismatch is physically actionable (oracle): **PASS (via patch level)**
Median oracle e_t vs raw M0 = 75.0 mm, paired on the same frames:

| level | median e_t [mm] | median gain [mm] (L5 95% CI) | sign-flip p | % frames improved | criterion |
|---|---:|---:|---:|---:|---|
| M4 patch | **41.3** | +28.9 [25.7, 33.0] | 0.0005 | **99.5%** | **meets (gain>0, p<0.05, ≥80%)** |
| M5 full view-conditioned | 51.2 | +21.9 [9.6, 29.7] | 0.0015 | 64.4% | median-positive but <80% frame-consistent |

The patch level — the level the post-development hierarchy analysis identified as the most consistently
transferable — clears the pre-registered bar decisively on the untouched trajectory. The full view-conditioned
level is positive on average but, as on Dataset II, is not frame-uniform on III; the pre-registered rule only
requires *one* of {patch, full} to pass, and patch does. No level was chosen after looking: both were frozen.

## C3 — deployable estimated-view pipeline: **PASS**
Frozen one-pass pipeline (T0 = raw p2p LS → z(T0) → μ → M_corr → re-register), full view-conditioned level as
frozen in G2:

| arm | median e_t [mm] |
|---|---:|
| T0 raw | 75.0 |
| oracle z(T_GT) | 51.2 |
| estimated view, GT-start (pure view gap) | 51.4 |
| **estimated view, warm-start (deployed)** | **51.4** |

- Median fraction of the raw→oracle mitigation **retained = 0.997** (≥0.70 required); the deployed pipeline
  beats raw T0 on **64.2%** of in-support frames (≥60% required). Oracle→estimated gap is ≈0.15 mm.
- Both pre-registered sub-conditions hold, so C3 passes. The 64% win-rate mirrors C2's full-level frame
  consistency (64.4%): on III the *full* level is the weaker, more view-sensitive level — exactly the trajectory
  dependence documented on II. The frozen pipeline was not switched to patch after the look; reported as-is.

## Secondary all-1302-frame view (includes out-of-support; NOT part of the verdict)
LS 52.7 → Huber 29.6 → Trim 26.4 mm (attenuation persists); M0 52.7 → M4 patch 40.0 mm (patch helps even with
out-of-support frames) while M5 full = 69.0 mm (full view conditioning degrades out-of-support). This reinforces
the frozen conclusion: **spatial-patch correction transfers robustly; exact view conditioning requires support**,
and claims must remain trajectory-dependent rather than universal.

## What this confirms, and its honest boundary
- Confirmed prospectively on a trajectory whose outcomes were never opened: (i) the structured-mismatch biased
  optimum is **not** a vanilla-LS artifact and is only attenuated by standard robust ICP; (ii) the frozen VI
  mismatch model is **physically actionable**, reducing pose error; (iii) the mitigation runs from an
  **estimated** view with essentially no oracle gap.
- Boundary (stated, not hidden): on III, as on II, the *patch* level is the most uniformly beneficial level and
  exact view conditioning is median-positive but not frame-universal. This is consistent with every prior stage
  and with the frozen Dataset-II shuffle result; it does not weaken CONFIRMED because the pre-registered C2/C3
  thresholds are met, but it dictates the claim wording (trajectory-dependent specificity; patch as robust
  fallback) in the manuscript.

**FINAL: CONFIRMED.** Method development stops here; proceed to manuscript writing.
