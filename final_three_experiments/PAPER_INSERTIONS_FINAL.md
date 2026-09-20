# PAPER INSERTIONS — FINAL THREE EXPERIMENTS (ready to paste)

Insertion budget respected: coarse initialization = **1 figure + 1 short paragraph**; VI held-out =
**1 small table + 1 short paragraph**; runtime = **1 compact table + 1 short paragraph**. No new
section, no expansion into a long paper. All numbers are frozen-output values with provenance in
`final_three_experiments/`.

---

## (1) Coarse / non-reference initialization — 1 figure + 1 paragraph

**Figure (single):** `01_coarse_initialization/fig_e1_paper_composite.png`
(top: Capture-B recovery rate; bottom: median final translation error with IQR; one column per
trajectory; blue = Raw, red = Patch). Caption:

> **Figure X.** Coarse-initialization robustness. Initial perturbation increases left-to-right from
> the reference pose (0) to 300 mm / 15°, using the same four sign-balanced deterministic
> perturbation directions at every level. Top: fraction of runs recovered to within the previously
> tested local basin (≤50 mm, ≤2°); bottom: median final translation error (IQR band). Patch (red)
> retains Raw's (blue) capture behaviour and its error advantage at every level; both local methods
> begin to encounter the 0.30 m/15° safeguard only at 300 mm/15°.

**Paragraph (paste near the existing local-initialization result):**

> We extend the initialization sweep from the 50 mm/2° local regime to 100 mm/5°, 200 mm/10°, and
> 300 mm/15° using the identical sign-balanced perturbation construction (4 deterministic
> directions, 20 fixed scans per trajectory). The new runner reproduces the prior local results to
> machine precision (≤6e-14 mm; identical iteration and termination records). Patch does not shrink
> the frozen ICP capture basin: its probability of recovering to within the 50 mm/2° local basin is
> at least Raw's at every level on every trajectory (e.g., at 300 mm/15°, II: 0.20 vs 0.10; III:
> 0.33 vs 0.21), and its paired translation advantage is retained throughout (median +45 mm on VI,
> +5–10 mm on the external/secondary sets). No numerical failure occurs; both methods begin to trip
> the 0.30 m/15° safeguard only at the coarsest 300 mm/15° level, where Patch clips no more often
> than Raw. Both pipelines therefore remain local ICP methods that deteriorate outside the validated
> basin, but the Patch correction neither loses capture earlier nor narrows that basin. (We do not
> pursue a global initializer; 500 mm/20° already exceeds the frozen safeguard at the start pose.)

---

## (2) VI-internal held-out validation — 1 small table + 1 paragraph

**Table (small):** per-fold leave-one-block-out (LOBO) on VI; place next to the VI results.

| Held-out VI block | n | Raw med. (mm) | Patch, held-out field med. (mm) | paired benefit (mm) | scans improved |
|---|---:|---:|---:|---:|---:|
| block 0 [0,70)   | 70  | 151.2 | 112.0 | +40.6 | 1.00 |
| block 1 [70,140) | 70  | 151.7 | 111.0 | +38.7 | 1.00 |
| block 2 [140,219)| 79  | 165.5 | 125.0 | +41.9 | 1.00 |
| block 3 [219,315)| 96  | 168.4 | 123.6 | +45.3 | 1.00 |
| block 4 [315,418)| 103 | 164.2 | 117.9 | +44.5 | 1.00 |
| block 5 [418,501)| 83  | 159.3 | 114.7 | +44.1 | 1.00 |
| **OOF pooled (501)** | 501 | **161.4** | **117.5** | **+43.1** [39.6, 44.9] | **1.00** |

(Bracket = 95% block-bootstrap interval over the six blocks; in-sample all-VI Patch = 116.8 mm.)

**Paragraph:**

> Because the Patch field is calibrated on VI, VI is not independent evidence for it. We therefore
> run six-fold leave-one-block-out validation over VI's six frozen contiguous view-travel blocks:
> for each scan we rebuild the per-patch discrepancy mean from the other five blocks while holding
> the 24-patch partition fixed (so clustering variability is not conflated with field-history
> leakage), with hard assertions that no held-out residual enters the field. The held-out Patch
> field lowers the median translation error from 161.4 to 117.5 mm—a paired +43.1 mm benefit, with
> all six blocks positive and every scan improved (block-bootstrap 95% interval [39.6, 44.9] mm).
> This retains 99% of the in-sample benefit (+43.5 mm; the held-out field is only 0.7 mm less
> accurate). VI leave-one-block-out calibration thus retains a positive Patch-over-Raw effect of
> essentially the same magnitude, reducing concern that the development gain is solely an in-sample
> calibration artifact (this does not by itself prove absence of overfitting; external evidence
> remains IV/II, with III secondary).

---

## (3) Runtime / memory / deployment cost — 1 compact table + 1 paragraph

**Table (compact):** single workstation, single thread (CPU-only), 80 fixed scans, median of 5
timed runs after warm-up; ms per frame.

| Method | reusable geometry | registrations/frame | median (ms) | p95 (ms) | ×Raw | peak RSS (MB) |
|---|---|---:|---:|---:|---:|---:|
| Raw | yes | 1 | 477.5 | 808.1 | 1.00 | 158 |
| Patch | yes (cached once) | 1 | 412.5 | 611.5 | 0.86 | 158 |
| Full | no (per-frame query model) | 1 | 427.7 | 702.0 | 0.90 | 158 |
| Estimated Full | partial | 2 | 953.3 | 1638.7 | 2.00 | 160 |

(Offline one-time calibration: 24-patch clustering 152 ms, VI field assembly 0.18 ms, cached
corrected-model KD-tree 11 ms; artifacts 29 KB.)

**Paragraph:**

> We benchmark per-frame cost on a single workstation with single-thread BLAS and nearest-neighbour
> queries (identical for all methods; CPU-only). Once its corrected geometry is cached, Patch adds
> no per-frame overhead and is slightly faster than Raw (0.86×) because it converges in fewer
> iterations; Full, which rebuilds a query-dependent corrected model and KD-tree each frame, spends
> only ≈12 ms on that construction and is comparable overall (0.90× Raw). The self-contained
> Estimated-Full pipeline performs a nominal and then a corrected registration and therefore takes
> ≈2× a single registration. Peak resident memory is essentially identical across methods (≈158 MB;
> method-specific working set <5 MB), and rebuilding a field for a new target costs ≈0.15 s of
> one-time clustering plus sub-millisecond field assembly. These are transparent single-machine
> timings, not a real-time claim.

---

## Do-not-add list (per round rules)
No new method/global initializer; no new comparator; no parameter/sweep changes; no re-selected
frames; no large new figures beyond the one E1 composite, the one E2 table, and the one E3 table.
