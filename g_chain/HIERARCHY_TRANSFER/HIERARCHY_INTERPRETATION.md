# HIERARCHY_INTERPRETATION.md

**LABEL: POST-HOC / POST-DEVELOPMENT EXPLORATORY ANALYSIS.** IV/II/V were already opened in prior stages;
this is cross-trajectory evaluation, **not** prospective confirmation and not independent external validation.
The global/patch/full levels are the *frozen* VI mismatch hierarchy (their VI direction cosines reproduce the
frozen 0.391/0.824/0.940 as 0.385/0.824/0.938). No parameter was fit here; the full VI library is queried.

## 1. Median predicted-step direction cosine (L5 moving-block 95% CI)

| trajectory (set) | global | patch | **full view-conditioned** | ordering |
|---|---:|---:|---:|---|
| VI development (reference) | 0.385 | 0.824 | **0.938** | global < patch < full |
| IV in-support 156 | 0.423 [0.391,0.446] | 0.630 [0.579,0.724] | **0.841 [0.811,0.867]** | **global < patch < full** |
| II in-support 428 | 0.718 [0.692,0.742] | **0.890 [0.870,0.910]** | 0.788 [0.722,0.831] | **global < full < patch** (patch ≫ full) |
| V out-of-support 1868 (note) | 0.030 [0.013,0.053] | 0.514 [0.467,0.554] | **0.902 [0.887,0.914]** | global fails; full rescues |

## 2. Answers to the three questions posed in section E

**(a) Does spatial patch information transfer? — YES, consistently.** The patch level is strongly positive on
both held-out in-support trajectories (IV 0.630, II 0.890) and moderately positive even out-of-support (V 0.514).
The "which physical region carries how much mismatch" field is an object-level, trajectory-robust quantity. This
matches the frozen P4 patch-residual-profile transfer (IV 0.43 / V 0.71) and the G1 result that patch-only
mitigation is positive on **every** trajectory.

**(b) Is the gain of exact view conditioning trajectory dependent? — YES, decisively.** On IV, adding exact
view conditioning on top of patch raises the cosine from 0.630 to 0.841 (non-overlapping CIs); on II it
*lowers* it from 0.890 to 0.788 (non-overlapping CIs the other way). The marginal value of the view-conditioned
layer is therefore not universal — it helps on IV/V but not on II.

**(c) Does this explain the Dataset-II shuffle anomaly? — YES, coherently.** The frozen shuffle test found II
does not support exact view↔mismatch specificity. The hierarchy shows why: on II the *spatial patch* structure
already captures almost all the transferable signal (0.890), and conditioning on the exact view adds noise /
mislocalization (drops to 0.788). The anomaly is not a contradiction; it is the case where spatial structure
dominates and exact view conditioning is redundant-to-harmful.

## 3. Physical-mitigation cross-check (consistency with G1)
The directional hierarchy agrees with the physical pose results: on IV the full level gives the largest physical
gain (160→83 mm); on II the patch level is best (66→42 mm) while full is neutral (69 mm). Direction and pose
evidence tell the same story.

## 4. Consequence for claims (per section H)
- Permitted: "spatial patch structure transfers more consistently than exact view conditioning; the added
  value of view conditioning is trajectory dependent."
- Forbidden: "view-conditioned mismatch mapping transfers universally." The II result (and the frozen shuffle
  anomaly) explicitly rules that out.
- Deployable implication (already frozen in G1/G2): use the full level where supported, with patch as the robust
  fallback; never present global-only as adequate (it collapses out-of-support, V 0.03).
