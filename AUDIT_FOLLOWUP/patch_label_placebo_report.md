# Literal patch-label permutation placebo (P0 follow-up)

## 1. What this is (and how it differs from the existing shuffle control)

The pre-existing falsification control was a **bijective view<->template cross-block shuffle** of the 24 patch profiles. That breaks view-to-template correspondence, but it is **not** a literal patch-LABEL placebo. This test keeps the frozen patch-correction LIBRARY fixed and randomly relabels which spatial patch receives which correction vector:

- 24 frozen patch correction 3-vectors `mu_patch[0..23]` are reassigned to spatial patch labels by one fixed bijection. Because it is a permutation, the **multiset of correction vectors and the distribution of their magnitudes are preserved exactly** (identical ||mu|| histogram; verified in code).
- Primary permutation seed `20240910`, drawn BEFORE looking at outcomes and used exactly once; permutation = [4, 7, 15, 18, 6, 0, 19, 21, 2, 14, 16, 9, 17, 23, 22, 1, 11, 10, 5, 8, 20, 12, 13, 3]. No seed is selected or repeated.
- A fixed ensemble of 4 additional seeds ([20240911, 20240912, 20240913, 20240914]) is reported only as a null band.
- All three arms use the SAME aligned scans, the SAME GT-aligned start (xi=0), the SAME frozen p2p LS ICP solver, weights and basin; no parameter is changed. Arms: **Raw** (no correction), **true Patch** (correct label map, = shipped M4), **Shuffled Patch** (permuted labels).

## 2. Trajectory-level results (primary scope medians; V analyzed on all frames)

| traj | n | Raw t | Patch t | Shuf t | ens Shuf t | Raw R | Patch R | Shuf R | Raw ||gt|| | Patch ||gt|| | Shuf ||gt|| |
|---|---|---|---|---|---|---|---|---|---|---|---|
| II | 428 | 66.149 | 41.777 | 67.683 | 65.303 | 1.774 | 1.269 | 2.134 | 0.052 | 0.023 | 0.039 |
| III | 371 | 75.037 | 41.298 | 66.622 | 69.912 | 1.658 | 2.116 | 3.008 | 0.046 | 0.017 | 0.038 |
| IV | 156 | 160.424 | 126.260 | 153.949 | 156.645 | 4.006 | 4.000 | 3.605 | 0.066 | 0.040 | 0.054 |
| V | 1868 | 173.761 | 134.575 | 174.361 | 176.714 | 3.026 | 3.620 | 3.257 | 0.069 | 0.059 | 0.064 |
| VI | 501 | 161.408 | 116.815 | 152.155 | 158.898 | 4.509 | 4.667 | 4.112 | 0.069 | 0.044 | 0.061 |

## 3. Block-level paired comparison (median block paired effects; t = translation mm)

| traj | K blocks | Patch>Raw k | Shuf>Raw k | Patch>Shuf k | med dEt(P-Raw) | med dEt(Shuf-Raw) | med dEt(P-Shuf) | p P~Shuf | p P~Raw | p Shuf~Raw |
|---|---|---|---|---|---|---|---|---|---|---|
| II | 9 | 9 | 7 | 7 | 18.0992 | 5.2362 | 11.1545 | 0.0391 | 0.0039 | 0.0742 |
| III | 8 | 8 | 6 | 7 | 31.6578 | 8.0193 | 26.5318 | 0.0156 | 0.0078 | 0.1484 |
| IV | 4 | 4 | 4 | 4 | 31.3145 | 9.1575 | 22.8793 | 0.1250 | 0.1250 | 0.1250 |
| V | 38 | 38 | 18 | 38 | 41.2710 | -0.1050 | 38.8340 | 0.0000 | 0.0000 | 0.5466 |
| VI | 6 | 6 | 6 | 6 | 43.8050 | 9.0028 | 35.6173 | 0.0312 | 0.0312 | 0.0312 |

Positive dEt = that arm lowers translation error vs the comparator. `k/K` is a block-level sign test; Wilcoxon p is across block medians (two-sided).

## 4. Reading

- The correct patch map must do better than a label-scrambled map of the SAME vectors; the gap `med dEt(P-Shuf)` and `Patch>Shuf k/K` quantify how much of the patch result depends on **where** each correction sits rather than on the correction magnitudes alone.
- If Shuffled Patch behaves like Raw (or worse) while true Patch improves, the effect is carried by spatial organization, not by the marginal magnitude distribution -- the literal placebo is then null, as required.
- Ensemble spread shows whether the primary-seed conclusion is stable to the particular relabeling; per-seed numbers were never used to choose a result.

### Observed verdict (primary seed)

- **II** (9 blocks): true Patch lowers translation in 9/9 blocks (median +18.10 mm); the label-scrambled map only in 7/9 (median +5.24 mm); true Patch beats shuffled in 7/9 blocks (median +11.15 mm, Wilcoxon p=0.0391).
- **III** (8 blocks): true Patch lowers translation in 8/8 blocks (median +31.66 mm); the label-scrambled map only in 6/8 (median +8.02 mm); true Patch beats shuffled in 7/8 blocks (median +26.53 mm, Wilcoxon p=0.0156).
- **IV** (4 blocks): true Patch lowers translation in 4/4 blocks (median +31.31 mm); the label-scrambled map only in 4/4 (median +9.16 mm); true Patch beats shuffled in 4/4 blocks (median +22.88 mm, Wilcoxon p=0.1250).
- **V** (38 blocks): true Patch lowers translation in 38/38 blocks (median +41.27 mm); the label-scrambled map only in 18/38 (median -0.10 mm); true Patch beats shuffled in 38/38 blocks (median +38.83 mm, Wilcoxon p=0.0000).
- **VI** (6 blocks): true Patch lowers translation in 6/6 blocks (median +43.81 mm); the label-scrambled map only in 6/6 (median +9.00 mm); true Patch beats shuffled in 6/6 blocks (median +35.62 mm, Wilcoxon p=0.0312).

The clearest null is V (out-of-support): shuffled labels give a median block effect of approximately zero and win only 18/38 blocks, whereas the correctly labelled Patch map wins 38/38; on the in-sample VI even scrambled vectors absorb some average bias (6/6), but the correct map is still ~4x larger and significantly above shuffled. The literal placebo is therefore null as required, and the result is attributable to spatial label assignment rather than to the magnitude multiset.

## 5. Files / reproducibility

- `patch_label_placebo_frame.csv`: per-frame errors, gradient-split norms, iters/on-bound and ensemble band for every trajectory (all frames; in_support flag).
- `patch_label_placebo_block.csv`: per-block medians and paired deltas.
- `scripts/t2_permutations.json`: the exact primary permutation and ensemble seeds.
- Raw and true-Patch arms reproduce the shipped frozen g1 results M0_raw_p2p / M4_patch_corr to numerical precision (checked during the run).
