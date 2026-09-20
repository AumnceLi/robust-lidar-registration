# Figure 4: provenance and review notes

Panel B uses raw__dhat and raw__xistar first three coordinates only, objective index 0/1; VI/IV/II all saved frames (not the in-support engineering subset), clearly separate scope from Figure 7. C/D use all 96 geometry x dtype x mag conditions including zero-dose, exploratory D2 .9/1 endpoints and solver-bound outcomes; no point excluded for weak association. RMS=sqrt(median J0)*1000 because frozen LS objective is mean squared residual. The data column grad_gt is a six-component FD norm under frozen m/rad coordinates evaluated at the reference pose, not exact J^T W delta and not a coordinate-invariant 6-DoF physical magnitude. Analytic per-condition J^T W delta vectors were not retained in this CSV; no method is rerun to manufacture them. Correlations are descriptive over designed conditions, not iid inferential tests. D4 is retained even when its residual RMS overlaps other types. Negative real VI comparison: Spearman residual RMS vs translation error=0.623589, translation-gradient norm vs error=0.445168; residual is stronger there. Therefore do NOT claim universal correlation dominance. D2 bound flags indicate solver-limited outcomes (some final norms exceed nominal 300 mm after rotational composition), not exact physical 300-mm measurements. Suggested Supplementary: all-direction/p2l theory diagnostics, VI counterexample scatter, damping negative results.

## Sources (read-only)
- `structured_mismatch_phase0/scripts/cache/rescue/objective_main.npz`; SHA256 `ab8ea7132fde9fb34e0980fc03d4a8c7050017b2a538427bb6a9e2d984f81fdf`
- `structured_mismatch_phase0/scripts/cache/ext/ext_objective_iv.npz`; SHA256 `ec6a83e507656671f82415e20b7957fb30dc1f958dd2a07b4b2c4a64bba82da8`
- `tj2_supplemental/cache/ii/ext_objective_ii.npz`; SHA256 `c0f8622ebcec1b019889218976fed3e9838c94c9c23a4b8162a5e1e12c6bf9b5`
- `g_chain/G_GENERALITY/results/geometry_results.csv`; SHA256 `515ae775ebdccd0b72fe2fefd814ebe98d5ed1450d21971c2829bad22965f428`

## Plotted-data tables
- `direction_cosines.csv`
- `matched_scatter_conditions.csv`
- `correlations.csv`

Missing: Exact analytic synthetic J^T W delta vectors absent; explicitly labeled saved FD diagnostic used instead.

N/A: None

No registration rerun, training, retuning or modification of frozen results. Statistics are descriptive reductions of saved results unless explicitly identified as an existing frozen CI. Human review is still required for scientific interpretation.
