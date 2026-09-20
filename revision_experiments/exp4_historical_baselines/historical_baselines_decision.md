# Exp.4 — Cheapest historical state-level baselines (DBS / Vector-DBS / Global-Vector)

**Status: COMPLETE.** All frozen inputs reused read-only; no parameter retuned. III is **post-hoc / secondary diagnostic** (its raw bias vector has no objective cache and was computed with the frozen `m_common.local_min_p2p`, identical to Exp.3). Raw error reproduced the frozen replay to **2.84e-14 mm** on all 1456 frames.

## Definitions (only the aggregation changes; history/neighbors/weights/support identical)

- **DBS (existing):** direction `unit(Σ w_s unit(b_s))` renormalised, times magnitude `Σ w_s ||b_s||/Σw_s` (direction/magnitude separated).
- **Vector-DBS (new):** `b̂(z)=Σ w_s b_s/Σw_s` — direct weighted mean of the FULL translation-bias vectors, same k=16 adaptive-Gaussian view neighbors.
- **Global-Vector (new):** one fixed 3-vector = equal-frame mean over the whole VI history (VI: leave-own-block-out), applied to every test frame.
- All three are **translation-only** perturbation corrections `xi_raw-b̂`; rotation is unchanged (eR == Raw). Patch is the existing frozen replay arm.

## Median translation error (mm)

| trajectory   |    Raw |    DBS |   Vector-DBS |   Global-Vector |   Patch |
|:-------------|-------:|-------:|-------------:|----------------:|--------:|
| VI           | 161.41 |  17.89 |        21.28 |          155.94 |  116.82 |
| IV           | 160.42 |  19.92 |        21.37 |          146.61 |  126.26 |
| II           |  66.15 | 142.97 |       135.67 |           51.16 |   41.78 |
| III          |  75.04 | 108.83 |       102.37 |           62.35 |   41.3  |

## Paired median translation gain vs Raw (mm) / improved-frame fraction

| traj   | DBS              | Vector-DBS       | Global-Vector   | Patch           |
|:-------|:-----------------|:-----------------|:----------------|:----------------|
| VI     | +143.87 / 100.0% | +139.90 / 100.0% | +11.19 / 79.2%  | +43.51 / 100.0% |
| IV     | +139.85 / 100.0% | +138.33 / 100.0% | +13.44 / 100.0% | +33.63 / 99.4%  |
| II     | -72.05 / 19.4%   | -66.42 / 22.4%   | +17.30 / 96.5%  | +19.10 / 92.8%  |
| III    | -36.48 / 26.4%   | -27.42 / 35.0%   | +8.42 / 65.5%   | +28.93 / 99.5%  |

## Findings

1. **View-kNN state correction (DBS and Vector-DBS) transfers on VI/IV but REVERSES on II/III**: median paired gain is large positive on VI/IV but negative on II (-72.1 DBS, -66.4 Vector) and III (-36.5 / -27.4); improved-frame fraction there is only 0.19–0.35.

2. **Vector-DBS is modestly more stable than DBS exactly where it matters**: it beats DBS on 95.8% of II and 100.0% of III frames (and its reversal is smaller in magnitude), while DBS is marginally better on VI/IV. The direction/magnitude separation is therefore not the cause of failure — but Vector-DBS **does not rescue** view-kNN state transfer (still reverses).

3. **The single Global-Vector is positive on EVERY trajectory** (VI +11.2, IV +13.4, II +17.3, III +8.4 mm; improved fraction 0.65–1.0). Mere historical supervision yields a small, non-reversing gain — so the paper **must not generalise “DBS failure” to all state-level historical correction**.

4. **Only the spatially-structured Patch helps substantially on all four trajectories** (+43.5/+33.6/+19.1/+28.9 mm; improved fraction 0.93–1.0). What fails under shift is *view-matched state-level transfer*; spatial (patch) structure is what transfers robustly.

## Decision

**HISTORICAL_BASELINE_SUPPORTED_WITH_REFRAMING.** Keep the DBS-failure claim but narrow it: a constant historical vector is mildly and universally helpful, and Vector-DBS is slightly more stable than direction-separated DBS; the failure is specific to view-kNN state transfer under distribution shift, and Patch's spatial structure is its demonstrated added value. No frozen parameter was changed; III remains post-hoc.
