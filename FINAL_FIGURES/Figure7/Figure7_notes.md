# Figure 7: provenance and review notes

Fields: G1 method, et_mm/eR_deg, traj, scan, order, in_support; G2 arm=est_warmstart. Primary selection: VI all 501; IV 156, II 428 and III 371 saved in-support frames. III remains the original reserved single-look evaluation (sealed until all methods frozen, opened exactly once). Oracle Full starts at the reference pose; Estimated Full uses the saved warm-start pipeline, so C combines view and warm-start differences. Hollow red markers identify Estimated Full. A/B/C use descriptive 25th–75th percentile intervals, not CI; existing G1 block-aware CIs are exported separately. D uses paired Raw-method per-frame differences and descriptive 25th–75th percentile intervals. Because paired-median and difference-of-marginal-medians are distinct estimands, II Full is near zero in D while A truthfully shows its marginal median error is worse than Raw (68.86 vs 66.15 mm); both values are exported. No rotation-neutrality claim for Patch: VI Patch rotation median exceeds Raw, and II Full worsens rotation; retained in B. Never describe oracle-gain retention on II as meaningful because oracle itself fails to improve the translation median. Suggested Supplementary: block-bootstrap L=5/10/20 distributions, all-frame III sensitivity, calibration budget and estimated-view perturbation grid.

## Sources (read-only)
- `g_chain/G1_MITIGATION/results/all_pose_results.csv`; SHA256 `1546fb9afc6de42dc7a61511ec303ec2df7ae5f4f061e99e0e9e05cf34627442`
- `g_chain/G3_FINAL_CONFIRMATION/results/g1_iii.csv`; SHA256 `407faf9b877868cdc99eea9ed971611dab315977c2939efa279aa72e23c70f9f`
- `g_chain/G2_ESTIMATED_VIEW/results/g2_vi.csv`; SHA256 `063926ac32728d8a1ca8b121034ac0f8d38732493639e9603e3dc55c275ec0aa`
- `g_chain/G2_ESTIMATED_VIEW/results/g2_iv.csv`; SHA256 `9ac67632c948c229ae9257c34518a256fa219e38b8fca3a832622bdcf001d82e`
- `g_chain/G2_ESTIMATED_VIEW/results/g2_ii.csv`; SHA256 `fe488d079a1b980dcf9ffb1d68002e5ed2f8c1d733977cf809f02ece7948928d`
- `g_chain/G3_FINAL_CONFIRMATION/results/g2_iii.csv`; SHA256 `bf42b040f3c61a6708ceca6581f86fe3442a1f12b6a915bb5876b41e2b20c282`
- `g_chain/G1_MITIGATION/results/method_comparison.csv`; SHA256 `bbc112c3ed8b4d6a85f751f0a304cd00462c7736c4af0a79cc09d779f29ea3c4`
- `g_chain/G3_FINAL_CONFIRMATION/results/single_look_summary.json`; SHA256 `8f780bf7b17a9c291228f42cb0fac92d0b111ebfe276578bfd1adea2940fb638`

## Plotted-data tables
- `pose_summary_iqr.csv`
- `paired_estimated_gap.csv`
- `paired_improvement_forest.csv`
- `change_vs_raw.csv`
- `existing_frozen_confidence_intervals.csv`

Missing: None

N/A: None

No registration rerun, training, retuning or modification of frozen results. Statistics are descriptive reductions of saved results unless explicitly identified as an existing frozen CI. Human review is still required for scientific interpretation.
