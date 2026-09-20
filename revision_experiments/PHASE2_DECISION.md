# PHASE 2 DECISION — Experiments 4–6 (second-priority, lowest-cost additions)

Scope: Exp.4 historical state-level baselines (DBS / Vector-DBS / Global-Vector vs Patch); Exp.5 minimal Full 2×2 ablation; Exp.6 joint translation–rotation evaluation. No existing main result was modified/overwritten/regenerated; all outputs live under `revision_experiments/`; no frozen parameter was retuned; **III is post-hoc / secondary throughout and is never called an untouched confirmation**; no frame/seed/baseline was chosen by outcome.

## Scientific answers

**Q4 — what does Patch add over simple historical state correction?** A single constant historical vector (Global-Vector) already gives a small, non-reversing gain on every trajectory; view-kNN state correction (DBS and the new Vector-DBS) wins big on VI/IV but reverses on II/III. Only Patch's *spatial* structure helps substantially on all four. Added value of Patch = spatially-resolved, all-history structure that transfers under view shift, not mere historical supervision and not view matching. → narrow the old “DBS failure” wording (Exp.4).

**Q-mech — what drives Full's cross-trajectory reversal?** The 2×2 ablation isolates it to **view-neighbor conditioning** (view effect flips sign VI/IV vs II/III at fixed weighting); point- vs scan-weighting is ~inert once view-conditioned (B2−B1≈0) and never flips sign. Keep all-history Patch as the primary transferable field; present Full's view conditioning as regime-dependent (Exp.5, exact reproduction of frozen Patch/Full to machine precision).

**Q6 — does translation gain carry a rotation cost?** vs Raw, Patch's translation gain almost never reverses but VI/III pay a small median rotation cost (majority t-better/r-worse); vs Huber/Trim the increment is trajectory-dependent (Patch is worse on II); Patch+Huber removes most rotation cost and dominates Raw on both axes. Disclose the trade-off; no invented safety threshold (Exp.6).

## Verdict for the second priority

**CONSISTENT_WITH_GO_WITH_REFRAMING.** Experiments 4–6 do not overturn Phase 1; they sharpen the claim in the same direction already set by PHASE1_DECISION (fixed-budget structured scan-to-model discrepancy + frozen historical compensation). Required wording changes:

1. Do not equate “DBS failure” with failure of all state-level historical correction: a constant vector is mildly universal, Vector-DBS is slightly more stable than DBS; the failure is view-kNN transfer under shift.
2. Attribute Full's trajectory dependence specifically to view conditioning, not to the point/scan aggregation choice.
3. Report Patch's small rotation trade-off vs Raw and its trajectory-dependent increment over Huber/Trim; highlight Patch+Huber for joint 6-DoF.
4. Keep III strictly post-hoc / secondary.

Stopped here as instructed; third-priority items (initialisation-basin perturbation, block-length/support-coverage/spatial-permutation) and the final REVISION_EXPERIMENTS_DECISION.md were NOT started.
