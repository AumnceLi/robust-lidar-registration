# Figure 8: provenance and review notes

A/B dose_response.csv: dtype, mag, form, geometry, et_med/eR_med; p2p summaries verified against geometry_results.csv. No replicate pooling. Shading spans the three geometry medians and is not uncertainty. C is an evidence-linked regime schematic; the complete numeric Huber/LS endpoint matrix remains exported in regime_ratios.csv for Supplementary, including GB D2 robust failure, D4 near-floor ratios, exploratory complete absence and solver-bound fractions. D results.csv loss=ls, alpha, eta_t, ete_med; D1-D5 use distinct markers. alpha = fraction of nominal-model points affected by the discrepancy (for D2 missing-component: fraction dropped; otherwise: fraction displaced beyond 1e-9 m). eta_t is a normalized residual-coherence proxy = ||sum r_i|| / sum ||r_i|| after NN matching, not exact H-weighted bias and not a universal threshold; eta_R is not mixed with translation. Phase-map 300/325-mm results remain saved solver-limited outcomes without clipping. Suggested Supplementary: numeric endpoint matrix, full LS/Huber phase maps, eta_R rotation phase map, per-geometry dose curves and D2 exploratory .9/1 provenance. No synthetic result is presented as independent hardware validation.

## Sources (read-only)
- `g_chain/G_GENERALITY/results/geometry_results.csv`; SHA256 `515ae775ebdccd0b72fe2fefd814ebe98d5ed1450d21971c2829bad22965f428`
- `g_chain/G_GENERALITY/results/dose_response.csv`; SHA256 `98e917d2e1a774822dd16bfed43dc11964f43f16c40117dad1efd3b6d73b151b`
- `FINAL_TOPJOURNAL_HARDENING/OPTIONAL_PHASE_MAP/results.csv`; SHA256 `6782a09e9df9cb76353330e1f0a71f0b260ecd958e3a27abeaed80ea14a8a561`

## Plotted-data tables
- `dose_response_geometry_ranges.csv`
- `regime_ratios.csv`
- `phase_samples_ls_translation.csv`

Missing: None

N/A: None

No registration rerun, training, retuning or modification of frozen results. Statistics are descriptive reductions of saved results unless explicitly identified as an existing frozen CI. Human review is still required for scientific interpretation.
