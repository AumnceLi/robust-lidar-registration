# G1_DECISION.md — B2-informed mismatch mitigation (ORACLE view)

- Date: 2026-09-10. Runs only because G0 = G0_PASS_ATTENUATED. Frozen predictor
  sha256 `8abcc82d…` queried only; **no relearning / network / fusion / new shrinkage**. Correction
  `m_i^corr = m_i + μ_{j(i)}(z_GT)`; three spatial levels reproduce frozen VI cosines 0.385/0.824/0.938.
- Primary outcome is **physical pose error** (e_t mm, e_R deg), not cosine. Sets: VI all 501 (development);
  IV in-support 156; II in-support 428; V all 1868 (out-of-support, supportive). Block bootstrap + paired
  block sign-flip (B=2000).

## VERDICT: **G1_PASS** — the historically learned structured-mismatch field is physically *actionable*: it moves the GT-started registration materially closer to physical GT on every trajectory. The marginal value of exact view conditioning (full vs patch) is, however, **trajectory dependent**.

### 1. Median e_t [mm] (L5 95% CI) and paired improvement vs raw p2p M0

| set | M0 raw p2p | M2 robust | M3 global | M4 patch | M5 full(oracle) | best level |
|---|---:|---:|---:|---:|---:|---|
| VI dev (501) | 161.4 | 148.9 | 157.0 | 116.8 | **76.9** [73.8,79.8] | full, Δ=83.1, 100% frames, p=0.0005 |
| IV in (156)  | 160.4 | 132.6 | 153.4 | 126.3 | **82.9** [78.6,96.8] | full, Δ=74.4, 100% frames, p=0.0005 |
| II in (428)  | 66.1 | 50.9 | 55.2 | **41.8** [38.9,48.0] | 68.9 (Δ=+0.8, p=0.129) | **patch**, Δ=19.1, 92.8% frames |
| V out (1868) | 173.8 | 169.5 | 176.0 (hurts) | 134.6 | **118.5** [114.2,122.7] | full, Δ=56.8, 99.7% frames, p=0.0005 |

### 2. Success-rule checklist (frozen before outcomes)

1. **Direction-consistent across blocks/trajectories — YES.** At least one of {patch,full} improves median
   e_t on every trajectory with 93–100% of frames improved and block sign-flip p=0.0005. M4 patch-only is
   positive on **all four** trajectories (Δ=43.5/33.6/19.1/40.9 mm) — the most robustly transferring level.
2. **No systematic rotation cost — YES (with one caveat).** M5 improves rotation on the in-support sets
   (VI +1.52°/96% frames, IV +1.57°/95%); II patch +0.39°; out-of-support V shows a small −0.24° (M5) /
   −0.72° (M4) rotation change in exchange for a 41–57 mm translation gain — a minor, not systematic, trade.
3. **Not driven by a few frames — YES.** Improvements are median-level with 93–100% frame fractions and tight CIs.
4. **Block-aware paired support — YES** for the winning level on every set (p=0.0005; II-full is the lone null, p=0.129).
5. **At least patch/full stable — YES**; M5 need not beat every baseline, and M4≈/＞M5 on II is reported as-is.

### 3. The core engineering claim is directly demonstrated (objective ⇏ pose)

- On **100%** of frames M0 raw ICP *lowers* the geometric objective (ΔJ_raw>0) yet settles >25 mm from GT.
- In **69–80%** of frames M5 is physically **closer to GT while reducing the raw objective less** than M0 —
  the raw-model optimum and the physical optimum are systematically different (`objective_vs_pose.csv`, G1F3).
  A single global vector M3 is weak and slightly hurts out-of-support, showing spatial (patch) structure is the
  ingredient that transfers; exact view conditioning adds further value only on some trajectories.

### 4. Adverse / qualifying results (kept)

- **II is the honest exception:** full view-conditioned M5 is neutral (68.9 vs 66.1, p=0.129) and patch M4 is
  best. This is *consistent with the frozen Dataset-II shuffle anomaly*: exact view↔mismatch specificity is not
  universal. Claim must be "mapping specificity is trajectory dependent; spatial patch structure transfers more
  consistently" — never "view-conditioned mapping transfers universally".
- Correction mitigates, it does not zero the bias (residual 42–118 mm): μ is an historical *expected* field, not
  per-frame truth. Out-of-support V still leaves 118 mm; extrapolation remains bounded.
- M1 p2l is not a mitigation and is slightly worse than M0 on II; it stays a baseline only.

### 5. Claims unlocked / constrained

- **May claim:** "a historically learned structured scan–model mismatch field can be used to *mitigate physical
  pose bias* of a robust/least-squares registration, with block-consistent gains across held-out trajectories."
- **Must phrase carefully:** spatial patch structure transfers more consistently than exact view conditioning;
  the latter's added value is trajectory dependent. Oracle view is used here — removing that dependency is G2.
- No new model is added; the II-full null is accepted, not rescued.

### 6. Gate

**G1 = G1_PASS → proceed to G2 (estimated-view deployable pipeline).** The deployable correction defaults to
the frozen hierarchy (full when supported, with patch as the robust fallback level); this fallback policy is
frozen before G2/G3 and is not tuned on outcomes.
