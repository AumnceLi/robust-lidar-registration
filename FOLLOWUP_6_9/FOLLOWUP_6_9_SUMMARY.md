# FOLLOW-UP ITEMS 6–9 — CONSOLIDATED SUMMARY (Pose-Active Model Mismatch)

**Date:** 2026-09-11 · **Scope:** frozen data / frozen parameters only; no re-tuning; no method or
parameter chosen from II/III outcomes; III remains an appended frozen diagnostic (never development
data); no seed/condition/subset selection; all paired statistics use the existing frozen block
definition; frame- and block-level provenance retained on every output. Item 10 (non-GT
initialization) was **not** run, per instruction.

**Verification backbone.** The Item 7/9 mechanical replay reproduces the frozen g0/g1 arms and the
stored predicted step / nearest-view distance **exactly (0.0) on every used frame**
(`scripts/verify79_full.csv`); the Item 6 marginal pipeline reproduces the frozen master summary to
1.4×10⁻¹⁴; the Item 8 affected-fraction α reproduces the frozen phase map to 9×10⁻¹⁷ and its
re-derived bias/RMS track stored values (median rel diff 1.7% / 0.06%).

---

## 1. Fair incremental value of Patch over robust baselines (Item 6)

Paired **block** effects (benefit = comparator − target), not marginal medians, are the authoritative
contrast. The marginal medians overstate Patch's gain:

- **vs Global correction — the one consistent win.** Patch is better on all four trajectories at
  block level: +38.2 (VI, 6/6), +24.4 (IV, 4/4), +5.2 (II, 5/9), +24.3 mm (III, 8/8, p=.008).
- **vs Huber — trajectory-dependent, smaller than it looks.** +29.4 mm on VI (6/6, resolved), but
  only +0.6 mm on IV (2/4; the flagged 132.6→126.3 marginal gap is block composition), +5.6 on II
  (5/9), +12.2 on III (6/8); external CIs cross 0.
- **vs Trim — not uniform.** +22.2 (VI), **−7.6 (IV — Patch slightly worse, 2/4)**, +2.6 (II),
  +7.7 (III).
- **Translation–rotation trade-off.** Patch is rotation-neutral vs Raw, but vs the robust losses it
  pays a small, consistent rotation cost on every trajectory (vs Huber −0.89/−0.64/−0.30/−0.85°;
  vs Trim similar).
- **Full (view conditioning).** Large, reliable gain on VI/IV; **net negative on II** (Full vs Trim
  −18.8 mm, 2/9 blocks, p=.039); small/mixed on III. Full's gain does not transfer in direction the
  way Patch's local correction does.

**Take-away:** Patch's robust, defensible incremental claim is over the *single global correction*;
its edge over *robust-loss* estimators is real in direction but modest, trajectory-dependent, and
bought with a small rotation cost. (Files: `followup6_*`.)

## 2. Complementarity of structured geometry correction and robust loss (Item 7)

Frozen mechanical crosses (same corrected target, only per-correspondence weights change; δ=1.345 +
MAD scale, Trim keep 0.80, identical μ_j and GT-local init):

- **Complementary, not redundant.** Both directions improve translation on all four trajectories:
  adding Patch geometry to Huber/Trim (Patch+Huber vs Huber +45.1/+29.9/+3.9/+18.3; Patch+Trim vs
  Trim +47.3/+38.8/+5.7/+16.6) and adding a robust loss to Patch (+17.9/+27.7/+3.9/+5.5;
  +25.6/+40.8/+3.9/+2.6).
- **Synergy strong on VI/IV, weak/unresolved on II/III.** Best translation on VI/IV is the stack
  (Patch+Trim IV 89.9 vs Patch 126.3 / Trim 125.2); on II the stack (≈40) ties Patch (41.8); on III
  Patch+Huber (32.2) is clearly best.
- **Partial rotation recovery.** Huber on the corrected target recovers ≈0.43° (VI) / 0.30° (IV) of
  Patch's rotation cost (6/6, 4/4 blocks) but does not fully return to pure-Huber rotation; recovery
  ≈0 on II/III. Robustification never destroys patch structure (no cross arm is worse than Patch LS
  in translation; it also removes II basin-bound hits 7.0%→0–0.5%).
- **Not a new method.** Reported strictly as a frozen diagnostic of operator complementarity; no
  parameter was tuned and it must not be re-packaged as a headline estimator. (Files: `followup7_*`.)

## 3. Equal-RMS mechanistic evidence (Item 8)

Pre-fixed 5% cross-family matching within geometry (10% sensitivity only), severity/bias from stored
frozen synthetic results:

- **60 matched pairs, median RMS difference 0.07 mm, yet median pose-bias ratio 5.96×; 77% of pairs
  differ by >2× and 53% by >5×** (structured–structured subset: median 3.39×, 68% >2×).
- **D4 (large residual / low pose-active projection) is the lower-bias side in 84%** of its 25
  matches (up to 10.6×; e.g. GB D4 RMS 4.06 → 0.058 mm bias vs D3 RMS 3.97 → 0.621 mm). At equal
  RMS, unstructured noise is far less biasing than organized residuals (structured side higher in
  75% of CTRL matches, median ≈58×).
- **Organization, not magnitude, predicts bias:** Spearman ρ(|Δbias|, |Δ‖g_t‖|)=0.907 (ρ vs
  |Δ‖P_JWδ‖|=0.74); the higher-bias side has the larger ‖g_t‖ in 88–91% of pairs. Same conclusion at
  10% (ρ=0.907).
- **Answer to the key question is YES:** with residual magnitude held (≈) fixed, changing the
  spatial organization of the mismatch still changes pose bias substantially. This is central
  mechanistic evidence for novelty. (Files: `followup8_*`.)

## 4. Transfer boundary of view conditioning (Item 9)

Per-frame view-support descriptors replayed from the frozen library (exact reproduction gate):

- **Full's reliable gain is confined to library-self (VI, +39.7, 100% beats Patch) and
  near-and-structurally-consistent support (IV, +38.9, 100%, ordered by proximity within IV).** It is
  net-negative on II (−24.6, beats Patch only 22%) and III (−20.0, 35%), and only modest/partial far
  outside support on V (+19.4, 75%).
- **Support geometry alone does not determine transfer.** II and IV are indistinguishable on
  nearest/τ (0.465 vs 0.490), ESS (15.79 vs 15.94; ESS saturates ≈16 everywhere) and coverage
  (1.00 vs 0.958), yet Full succeeds on IV and fails on II; within II the geometrically nearest bin
  transfers worst. The II failure is **consistent with a structural-content mismatch** with the VI
  library, not with poor coverage (association, not causality).
- **Patch is the stable floor** in poor/uncertain support because it is view-independent: it holds
  41.8/41.3 on II/III where Full degrades to 68.9/51.2.
- **High direction cosine ≠ reliable compensation:** V's cosine 0.902 (second-highest) co-occurs with
  nearest/τ≈5 and Full beating Patch only 75% of frames. (Files: `followup9_*`.)

---

## MANUSCRIPT_SAFE_CLAIMS (each supported by the cited frozen item)

1. At approximately fixed residual RMS, the **spatial organization** of a model mismatch changes
   pose bias (median ≈6×; 77% of matched pairs >2×; low-projection D4 lower-bias in 84%), and the
   pose-active translational gradient separates the sides (ρ=0.91; 88% sign agreement). **[Item 8,
   corroborated by Item 5]**
2. Unstructured residuals matched in RMS to organized residuals produce systematically less pose
   bias; residual magnitude alone is not predictive. **[Item 8]**
3. A **local patch correction outperforms a single global correction consistently** across all four
   trajectories at the frozen-block level (resolved on VI and III). **[Item 6]**
4. Patch's advantage over **robust-loss** estimators is directionally positive but modest and
   trajectory-dependent (large on VI; ≈0 vs Huber and negative vs Trim on IV; unresolved on II/III),
   and carries a small (≈0.3–0.9°) rotation cost; it is rotation-neutral vs Raw. State with paired
   block numbers, never marginal medians alone. **[Item 6]**
5. Structured geometry correction and robust per-correspondence weighting are **complementary
   operators** (stacking improves translation on every trajectory; Huber recovers part of Patch's
   rotation cost on VI/IV); the synergy is strong on VI/IV and weak/unresolved on II/III. **[Item 7]**
6. View conditioning adds large, reliable value only in the library-self and the geometrically
   near **and structurally consistent** regime; it can produce negative transfer (II), and the
   view-independent Patch is the stable floor under poor/uncertain support. **[Items 6, 9]**
7. View-support distance/ESS/coverage do **not by themselves** guarantee transfer (II is as well
   supported as IV yet fails); a high translation direction cosine does **not** imply reliable
   compensation (V). **[Items 3, 9]**
8. All quantitative claims are made under **GT-local (reference-pose) initialization with
   target-specific frozen historical calibration**; III is an appended frozen diagnostic, not
   development data. **[global]**

## MANUSCRIPT_CLAIMS_TO_REMOVE (or explicitly soften)

- Any statement that Patch *uniformly/robustly beats Huber or Trim* (false on IV vs Trim; external
  paired effects unresolved).
- Any claim of *monotonic / guaranteed view transfer* or that nearest-view distance, ESS or coverage
  ensures Full benefit (II is the counter-example; ESS saturates).
- Any claim that a high direction cosine validates correction **magnitude or reliability**.
- Any claim of operation from **arbitrary / estimated / non-reference pose initialization** — Item 10
  was not run; this is unsupported today.
- Presenting **Patch+Huber / Patch+Trim as a new headline method** (it is a frozen complementarity
  diagnostic, with weak II/III synergy).
- Marginal-median-only superiority tables; causal language about view-support associations; any
  method/parameter choice that used II/III; treating V as anything more than a supportive set.

## NEW_EXPERIMENTS_STILL_REQUIRED

- **Item 10 non-GT initialization — REQUIRED ONLY IF the claimed scope expands** beyond
  GT-local/reference-pose operation to a tracker started far from the reference pose. It is **not**
  required for the scoped paper as defined in question B (not run this round, by instruction).
- *Non-blocking / optional:* additional external sequences/blocks to widen the small external block
  counts (IV K=4) that make paired CIs broad; store the original synthetic RNG salt (or raw synthetic
  clouds) so Item-8 mechanism descriptors byte-match stored realizations (currently a validated
  fixed-seed re-derivation); a *controlled* structural-consistency experiment if a causal view-
  transfer claim is ever wanted (today the II–IV contrast is association only).
- **No experiment within Items 6–9 required new data** — every scoped question was answered from
  frozen inputs; no `NEW_EXPERIMENT_REQUIRED` was triggered for 6–9.

---

## JUDGMENT A — Is Item 10 (non-GT init) required to submit the *current scoped* paper?

**No — provided the scope and limitations are stated honestly.** Every result here is, by design,
GT-local; the paper's mechanism and local-mitigation claims do not depend on the basin from an
arbitrary distant start (the Item-7 arms converge without basin-bound clipping, on-bound ≈0, which is
consistent with a well-behaved *local* basin but says nothing about distant starts). Item 10 becomes
mandatory only if the paper claims deployment from non-reference/estimated initialization or
end-to-end tracking robustness. Such deployment claims must be removed until Item 10 exists.

## JUDGMENT B — Submission-ready under the explicit scope
(GT-local / reference-pose mechanism study + target-specific historical calibration + local
mitigation)?

**Yes — the evidence is submission-ready for that scope**, once claims are tightened to
MANUSCRIPT_SAFE_CLAIMS and the over-claims above are removed. The mechanistic core (Item 8, with
Items 4–5), the fair incremental-value accounting (Item 6), the complementarity diagnostic (Item 7)
and the explicit view-transfer boundary (Item 9) are mutually consistent, are all computed on frozen
data with exact-reproduction gates, and convert the previously ambiguous points into *qualified,
defensible* statements. The paper should present itself as a reference-pose mechanism + frozen
target-specific local-mitigation study, name non-GT initialization and cross-target view transfer as
deliberate boundary/limitations, and not claim a universally deployable corrector.
