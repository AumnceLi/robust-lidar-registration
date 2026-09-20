# Figure 2: provenance and review notes

Fields: patch_id, scan_id, support_count, median_residual (m), range_m; frozen blocks indexed by scan_id. Only support_count>0 and finite residuals retained. Missing heatmap cells remain masked, never zero-filled. Model projection is x+0.42y versus z+0.23y, schematic units omitted. Original patch IDs 0-23 preserved. The six frozen orientation blocks are the same contiguous view-travel blocks used throughout the VI analysis (cumulative view-direction travel; sizes 70/70/79/96/103/83). Example patches [3, 20, 8] selected by largest nominal model_point_count within dominant absolute normal axis (x/y/z), independent of residual outcomes. Range bins: eight equal-width intervals over all supported VI observations. Bands are descriptive 25th–75th percentile intervals, NOT confidence intervals. Figure limited to VI because patch-wise cross-trajectory residual tables were not needed for this supported realization; no cross-trajectory patch field was recomputed. Human review: range and orientation covary, so do not claim a causal range effect. Suggested Supplementary: complete 24-patch view profiles.

## Sources (read-only)
- `structured_mismatch_phase0/results/patch_persistence.csv`; SHA256 `ce16526f146922fa9d1ebe83a98d79ad9732443b76a00c923ed352e79535b572`
- `structured_mismatch_phase0/results/patch_definition.csv`; SHA256 `e1aa5ead8317971f1ab23afbf71e333793bb044fc592ff37115fb1c6ad4d9973`
- `structured_mismatch_phase0/scripts/cache/model_cache.npz`; SHA256 `7e53cd544227ba1e8f5c7326a1c23ca5bae6273af275c5a9488eb2a9e42dad6e`
- `structured_mismatch_phase0/scripts/cache/patches.npz`; SHA256 `6b4ffd09c6895abfecd1ed1dde1765eeb2d43f5f8e74e0c27dacbf7b6e5f9fe1`
- `structured_mismatch_phase0/scripts/cache/rescue/VI_ONLY_PREDICTOR_FROZEN.npz`; SHA256 `8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe`

## Plotted-data tables
- `patch_block_residual.csv`
- `patch_definitions.csv`
- `view_examples_binned.csv`

Missing: None

N/A: None

No registration rerun, training, retuning or modification of frozen results. Statistics are descriptive reductions of saved results unless explicitly identified as an existing frozen CI. Human review is still required for scientific interpretation.
