# G0_DECISION.md — Robust Registration Falsification

- Date: 2026-09-10. Config sealed in `frozen_config.yaml` / `protocol.md` **before** any outcome run.
- Shared weighted solver; R0/R1 (least-squares) reproduce the frozen `raw__xistar` to **≤1.1e-16**, so robust
  weighting is the *only* changed factor. Primary robust = **Huber IRLS ICP (δ=1.345, MAD scale)**; one
  pre-registered secondary = **trimmed ICP (keep 0.80)**. No other robust loss was tried (no loss-shopping).
- Sets: VI all 501 (development); IV in-support 156; II in-support 428; V all 1868 (out-of-support, supportive only).
  Uncertainty = temporal moving-block bootstrap of the median L=5/10/20 and paired block sign-flip (B=2000).

## VERDICT: **G0_PASS_ATTENUATED** — robust registration significantly *reduces* but does **not** eliminate the structured-mismatch GT-started biased optimum. G1 is AUTHORIZED.

### 1. Headline numbers (p2p; median GT-started translation displacement e_t^GT [mm], L5 block-bootstrap 95% CI)

| trajectory (set) | R0 LS | R2 Huber (primary) | R3 Trim80 (sens.) | paired LS→Huber reduction | % frames Huber<LS | sign-flip p |
|---|---:|---:|---:|---:|---:|---:|
| VI (dev, 501)        | 161.4 [158.8,163.8] | **148.9 [147.3,150.8]** | 144.8 | 14.4 | 100.0% | 0.0005 |
| IV (in-supp, 156)    | 160.4 [158.1,162.3] | **132.6 [131.0,135.4]** | 125.2 | 24.6 | 100.0% | 0.0005 |
| II (in-supp, 428)    | 66.1 [63.4,83.1]    | **50.9 [46.8,53.4]**    | 47.3  | 20.1 | 97.2%  | 0.0005 |
| V (out-supp, 1868)   | 173.8 [172.8,174.6] | **169.5 [168.5,170.5]** | 169.8 | 2.8  | 71.9%  | 0.0005 |

Matched **model-self null = 0.000000 mm median for every formulation and every trajectory** (real/self
ratio ≈ 1e13–1e14; Cohen d real-vs-self ≈ 2.0–30.8). p2l gives the same verdict (VI 159.9→149.7,
IV 156.6→134.9, II 70.5→52.5, V 173.6→170.2 mm).

### 2. The three joint criteria (no preset mm threshold)

1. **Real-vs-self effect size.** Huber leaves a 51–169 mm median physical displacement in the real data while
   the identical robust solver sits at 0.000000 mm on matched model-self clouds (d ≫ 2, MWU p≈0). The residual
   is therefore not a numerical artifact of the robust solver.
2. **Block-aware uncertainty.** *Every* temporal/orientation block has Huber median e_t > 10 mm
   (VI 6/6, IV 4/4, II 12/12, V 38/38; block medians: VI 133–154, IV 127–139, II 25–70, V 153–188 mm);
   the LS→Huber attenuation is block-consistent (VI/IV 100% of blocks, II 11/12, V 28/38) with tight CIs.
3. **Engineering magnitude.** 100% of in-support frames still leave GT by >10 mm under Huber
   (see `method_table.csv leave_gt_*`); a 5–17 cm GT-started drift is far beyond any pose-tolerance relevant
   to close-range spacecraft LiDAR tracking. Objective non-stationarity at GT also persists: median
   ‖∇J(T_GT)‖ drops only from ~0.069 to ~0.031 (VI) and stays ~1e13–1e14× the self gradient (~7e-6).

Both pre-registered robust formulations agree (Huber and Trim80 leave 47–170 mm), so the conclusion does not
depend on a hand-picked loss. Rotation is slightly **improved**, not traded off (VI 4.51→3.95°, IV 4.00→3.40°,
II 1.77→1.05°, V 3.03→2.33°); Huber also removes II's basin on-bound clipping (7.0%→0%).

### 3. Why ATTENUATED and not STRONG / not FAIL

- Not **G0_PASS_STRONG**: the attenuation is real, statistically decisive (paired p=0.0005) and non-trivial
  in-support (≈9–17% of the displacement; up to 25 mm), i.e. robust down-weighting of inconsistent
  correspondences does remove *part* of the bias. We must report that honestly.
- Not **G0_FAIL_ROBUST_RESOLVES**: the residual remains 51–169 mm, ~1e14× self, in 100% of blocks/frames, on
  both objectives and with two robust losses. Standard robust registration does **not** restore GT stationarity.
- Out-of-support V is informative: where the structured mismatch is most out-of-domain, Huber recovers only
  2.8 mm (72% of frames) — robust weighting is least able to help exactly where the systematic field is strongest,
  consistent with a *structured*, not an outlier-driven, error (a true outlier process would be removed by Huber).

### 4. Adverse / qualifying results (kept, not hidden)

- Robust weighting helps less out-of-support (V: 2.8 mm) than in-support; it is a partial palliative, not a cure.
- II has the smallest absolute residual (51 mm) and one block where Huber ≈ LS; magnitude is trajectory-dependent.
- Trim and Huber differ by only a few mm; no robust variant drives displacement toward zero.
- These are GT-started *local-basin* probes (basin 0.30 m/15°), not global coarse-registration benchmarks.

### 5. Claims that survive / must contract

- **Survive / strengthened:** "structured scan–model mismatch creates objective non-stationarity and a biased
  local optimum that is *not* a vanilla least-squares-ICP artifact — it survives standard Huber/trimmed robust
  registration, which only attenuates it." The mechanism chain (Contribution 1) passes a genuine falsification attempt.
- **Must contract:** do not claim robust registration is irrelevant — quantify that it removes ~10–17% in-support;
  position it as necessary-but-insufficient. Do not generalize the attenuation magnitude across trajectories.
- **Unchanged frozen decisions:** no new loss, no tuning, predictor untouched; VI remains development;
  IV/II/V remain post-development held-out; III stays sealed for G3.

### 6. Gate

**G0 = G0_PASS_ATTENUATED → proceed to G1 (frozen B2-informed mismatch mitigation, oracle view first).**
No robust-loss search will be performed; the robust arm M2 used in G1 is the frozen Huber above.
