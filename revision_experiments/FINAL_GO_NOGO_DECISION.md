# FINAL REVISION STATUS — GO / NO-GO

**FINAL_REVISION_STATUS = READY_WITH_LIMITATION**

Rationale: every mandatory experiment (P1-A/B/C, P2-A) is complete with framewise raw outputs,
aggregates, exact command/config/seed and input/output hashes, and all non-circularity gates pass.
The core Patch translation benefit is positive across every tested patch count, normal weight and
clustering seed on all four trajectories — no sign reversal, no trajectory-specific collapse.
Residual items are honest limitations, not missing experiments.

## Q1. Is the 24-patch configuration in a stable region?
**Yes.** Over K∈{12,18,24,32,48} the paired Raw−Patch translation benefit is positive for every K on
VI/IV/II/III (14.5–56.8 mm); only the extreme K=48 dips modestly on II while staying +14.55 mm. 24 is
a mid-plateau value, not a peak, and rotation change stays within ±0.47°.

## Q2. Is the Patch translation benefit stable to normal weight and clustering seed?
**Yes.** All-positive at w∈{0,.15,.30,.60,1.00} (position-only w=0 already gives most of the gain)
and strictly positive for all five seeds {0,1,2,42,20240910} on every trajectory, with narrow seed
ranges (e.g. IV 33.4–36.5 mm). The gain does not depend on a single hand-picked parameter combination.

## Q3. Does the rotation penalty change materially after recomputed normals / smoothing?
- **Point-to-point (paper primary): No.** ReNormal is bit-identical to Patch+Huber (1.4e-14 mm)
  because point-to-point Kabsch does not use normals; the parameter-free k=16 boundary smoothing also
  leaves the p2p penalty essentially unchanged. The primary rotation cost is therefore intrinsic to
  shifting target geometry, not to stale normals or hard patch boundaries.
- **Point-to-plane (diagnostic channel): partially.** ReNormal reduces the penalty on all four
  trajectories (VI 1.12→0.75°, IV 0.61→0.28°, II 0.89→0.66°, III 1.06→0.99°) and smoothing reduces it
  on three, with translation gain preserved; a residual penalty remains. Wording limited to
  "consistent with contributing", no causal claim.

## Q4. Is there still a "must-add, otherwise do not submit" experiment?
**No.** The mandatory grid closes the parameter-robustness and rotation-penalty questions a reviewer
would most likely raise; P3 and P4 (both low cost) additionally cover aggregation robustness and the
II transfer failure. Remaining issues are limitations to state, not experiments that block submission.

## MUST_ADD_TO_PAPER
1. Patch-count stability paragraph (positive over K=12…48; 24 on a plateau).
2. Normal-weight stability paragraph (positive over w=0…1; position-only already works; 0.30 not "optimal").
3. Five-seed clustering robustness (benefit positive for every seed).
4. The mechanistic fact that recomputing normals leaves the point-to-point primary result unchanged
   (bit-identical), with the point-to-plane reduction reported only as "consistent with".

## SHOULD_ADD_TO_PAPER
1. Block-size robustness (25/50/100; primary contrasts keep direction, block-CIs above 0).
2. II transfer-failure diagnostic as a transfer-boundary/limitation paragraph (support adequate;
   predicted-step direction mis-aligned; physical cause not uniquely identified).
3. Parameter-free boundary-smoothing result as a one-line negative control for the p2p rotation cost.

## KEEP_AS_LIMITATION
1. A small Patch(+Huber) rotation cost remains (p2p +0.05…+0.72°) and is intrinsic to pre-shifting
   target geometry; it is not removed by normal recomputation or boundary smoothing.
2. On II, Patch-vs-Global-Vector is directionally positive but block-CIs still cross zero — report as
   unresolved, not significant.
3. II transfer failure localizes to view-conditioning/direction mismatch with no single identifiable
   physical cause (use the mandated sentence verbatim).
4. Sweeps cover fixed finite grids (K 12–48, w 0–1, five seeds) on one physical target.

## DO_NOT_ADD
1. Do not relabel 24 / w=0.30 / seed42 as "optimal" or re-select the main config from the sweeps.
2. Do not claim stale normals or patch boundaries *cause* the rotation penalty (p2p unchanged; p2l only partial).
3. Do not introduce Patch-Smooth / Patch-ReNormal or a third deterministic partition as a method/contribution.
4. Do not re-run the zero-perturbation L0 initialization study or add further hyperparameter sweeps.
5. Do not tune block size to force II Patch-vs-Global significance, and do not hand-pick P4 frames.
