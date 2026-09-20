# Figure 3: provenance and review notes

Fields: kind=p2p, form=ls, real=1/0, g_gt (data column name, retained), traj, order, block, in_support. VI all frames; IV/II/III saved in_support=True. The field g_gt is the saved norm of the six-component central-difference gradient evaluated at the reference pose, with translation in m and rotation in rad: a native-coordinate diagnostic, NOT a dimensionless invariant or exact analytic J^T W delta. Self-null has a finite numerical-gradient floor, even though its optimized pose error is near machine zero; these are different quantities. Panel B uses the actual saved block IDs, not rounded block counts from prose audits. Panel C landscape axes: frame, translation/rotation, coordinate, scale, +/- side, objective; use scale index 0 and p2p index 0. Select + if g<0, otherwise -, success Jside<J0-1e-12. Six probes per VI frame, no binomial CI. Suggested Supplementary: p2l, other step sizes, spatial shuffle and FD sensitivity.

## Sources (read-only)
- `g_chain/G0_ROBUST_FALSIFICATION/results/frame_results.csv`; SHA256 `5146df470f0fcde107cd2dfffbd47a02754dd472d94f2ccf3db0ebc74b9a66ac`
- `g_chain/G3_FINAL_CONFIRMATION/results/g0_iii.csv`; SHA256 `d15452b1fc5ce00e74eaeb037cf8878d845e29e10e2053c0d2d3d051fc96a500`
- `structured_mismatch_phase0/scripts/cache/rescue/objective_main.npz`; SHA256 `ab8ea7132fde9fb34e0980fc03d4a8c7050017b2a538427bb6a9e2d984f81fdf`

## Plotted-data tables
- `gradient_summary.csv`
- `saved_block_summary.csv`
- `descent_counts.csv`

Missing: None

N/A: None

No registration rerun, training, retuning or modification of frozen results. Statistics are descriptive reductions of saved results unless explicitly identified as an existing frozen CI. Human review is still required for scientific interpretation.
