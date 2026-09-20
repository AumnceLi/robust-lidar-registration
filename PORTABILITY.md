# Portability note (read before comparing source hashes)

The authors' working tree used absolute machine paths of the form `D:\doubao\...`.
To make this bundle runnable from any clone location (Windows, Linux or macOS), the
curated copies underwent a **mechanical, behaviour-preserving port**:

1. Every path **string literal** beginning with `D:\doubao\` (or `D:/doubao/`) was rewritten
   to a repository-root-relative expression `_pp("<same/relative/path>")` (backslashes
   normalised to `/`, which Python and the OS accept on every platform).
2. Each affected file received the same small bootstrap header that locates the repository
   root at runtime via the marker file `.repo_root` and defines `_pp(...)`.
3. **No scientific code, parameter, constant, seed, formula, branch or numeric literal was
   changed.** The only edits are the path literals and the inserted bootstrap.

Because the file bytes changed, the SHA-256 of *ported source files* no longer matches the
code-file hashes recorded on the original machine in
`g_chain/G3_FINAL_CONFIRMATION/FREEZE_MANIFEST.md` (and similar provenance ledgers). This is
expected. What matters scientifically is that the **frozen numerical artifacts are byte
identical** and are still hash-asserted at runtime:

| Frozen artifact | SHA-256 (verified in this bundle) |
|---|---|
| `.../cache/rescue/VI_ONLY_PREDICTOR_FROZEN.npz` | `8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe` |
| `.../cache/model_cache.npz` | `7e53cd544227ba1e8f5c7326a1c23ca5bae6273af275c5a9488eb2a9e42dad6e` |
| `.../cache/patches.npz` | `6b4ffd09c6895abfecd1ed1dde1765eeb2d43f5f8e74e0c27dacbf7b6e5f9fe1` |

`g_common.load_frozen()` re-asserts the predictor hash on every run; the G3 single-look script
asserts only the frozen frame counts (1302 total / 371 in support), never code-file hashes.

To audit the port yourself, the difference between an original and a shipped file of the same
name is exactly: (a) the bootstrap block, and (b) `D:\doubao\...` literals replaced by
`_pp("...")`. `SHA256SUMS.txt` pins the exact bytes shipped here (run
`python verify_checksums.py`).

## Files that received the portability bootstrap (97)

- `AUDIT_FOLLOWUP/scripts/af_common.py`
- `FINAL_TOPJOURNAL_HARDENING/THEORY/inspect_deep.py`
- `FINAL_TOPJOURNAL_HARDENING/THEORY/inspect_inputs.py`
- `FINAL_TOPJOURNAL_HARDENING/THEORY/theory_empirics.py`
- `FOLLOWUP_6_9/scripts/dbg8.py`
- `FOLLOWUP_6_9/scripts/dbg8b.py`
- `FOLLOWUP_6_9/scripts/f_common.py`
- `FOLLOWUP_6_9/scripts/final_check.py`
- `FOLLOWUP_6_9/scripts/item8_build.py`
- `FOLLOWUP_6_9/scripts/probe.py`
- `FOLLOWUP_6_9/scripts/probe_item8.py`
- `FOLLOWUP_6_9/scripts/probe_keys.py`
- `FOLLOWUP_6_9/scripts/probe_syn.py`
- `FOLLOWUP_6_9/scripts/replay79.py`
- `FOLLOWUP_6_9/scripts/verify79_full.py`
- `figure_redesign_v2/checks/_probe_round6.py`
- `figure_redesign_v2/checks/assemble_figures_final.py`
- `figure_redesign_v2/checks/make_print_proof.py`
- `figure_redesign_v2/checks/regen_checksums.py`
- `figure_redesign_v2/configs/paths.py`
- `figure_redesign_v2/figures_final/src/configs/paths.py`
- `figure_redesign_v2/figures_final/src/scripts/draw_figure1.py`
- `figure_redesign_v2/figures_final/src/scripts/draw_figure2.py`
- `figure_redesign_v2/figures_final/src/scripts/figure3.py`
- `figure_redesign_v2/figures_final/src/scripts/make_figure5.py`
- `figure_redesign_v2/figures_final/src/scripts/reproduce_figure6_gate.py`
- `figure_redesign_v2/figures_final/src/scripts/verify_all_v2.py`
- `figure_redesign_v2/figures_final/src/scripts/verify_table3.py`
- `figure_redesign_v2/scripts/draw_figure1.py`
- `figure_redesign_v2/scripts/draw_figure2.py`
- `figure_redesign_v2/scripts/figure3.py`
- `figure_redesign_v2/scripts/figureS1.py`
- `figure_redesign_v2/scripts/make_figure5.py`
- `figure_redesign_v2/scripts/make_figureS2.py`
- `figure_redesign_v2/scripts/make_figureS3.py`
- `figure_redesign_v2/scripts/redraw_20260917_export_csvs.py`
- `figure_redesign_v2/scripts/redraw_20260917_fig2.py`
- `figure_redesign_v2/scripts/redraw_20260917_fig6.py`
- `figure_redesign_v2/scripts/redraw_20260917_figS_threshold.py`
- `figure_redesign_v2/scripts/redraw_20260917_vi_rotation_audit.py`
- `figure_redesign_v2/scripts/redraw_20260917_vi_rotation_check.py`
- `figure_redesign_v2/scripts/reproduce_figure6_gate.py`
- `figure_redesign_v2/scripts/verify_all_v2.py`
- `figure_redesign_v2/scripts/verify_table3.py`
- `final_three_experiments/01_coarse_initialization/e1_combine_analyze.py`
- `final_three_experiments/01_coarse_initialization/e1_fidelity_gate.py`
- `final_three_experiments/01_coarse_initialization/e1_provenance.py`
- `final_three_experiments/01_coarse_initialization/e1_run_coarse.py`
- `final_three_experiments/01_coarse_initialization/make_paper_figure.py`
- `final_three_experiments/02_vi_leave_block_out/e2_analyze.py`
- `final_three_experiments/02_vi_leave_block_out/e2_provenance.py`
- `final_three_experiments/02_vi_leave_block_out/e2_run_lobo.py`
- `final_three_experiments/03_runtime_memory/e3_analyze.py`
- `final_three_experiments/03_runtime_memory/e3_benchmark.py`
- `final_three_experiments/03_runtime_memory/e3_core.py`
- `final_three_experiments/03_runtime_memory/e3_mem_worker.py`
- `final_three_experiments/03_runtime_memory/e3_provenance.py`
- `final_three_experiments/_lib/f3_common.py`
- `final_three_experiments/assemble_final.py`
- `g_chain/G0_ROBUST_FALSIFICATION/scripts/g0_run.py`
- `g_chain/G0_ROBUST_FALSIFICATION/scripts/g0_stats.py`
- `g_chain/G0_ROBUST_FALSIFICATION/scripts/g0_validate.py`
- `g_chain/G1_MITIGATION/scripts/g1_run.py`
- `g_chain/G1_MITIGATION/scripts/g1_stats.py`
- `g_chain/G2_ESTIMATED_VIEW/scripts/g2_perturb.py`
- `g_chain/G2_ESTIMATED_VIEW/scripts/g2_run.py`
- `g_chain/G2_ESTIMATED_VIEW/scripts/g2_stats.py`
- `g_chain/G3_FINAL_CONFIRMATION/scripts/g3_decide.py`
- `g_chain/G3_FINAL_CONFIRMATION/scripts/g3_download_cache.py`
- `g_chain/G3_FINAL_CONFIRMATION/scripts/g3_freeze_manifest.py`
- `g_chain/G3_FINAL_CONFIRMATION/scripts/g3_single_look.py`
- `g_chain/G_GENERALITY/scripts/g_generality_run.py`
- `g_chain/G_GENERALITY/scripts/g_generality_stats.py`
- `g_chain/HIERARCHY_TRANSFER/scripts/hierarchy_transfer.py`
- `g_chain/common/_hier_check.py`
- `g_chain/common/g_common.py`
- `revision_experiments/_lib/gate0.py`
- `revision_experiments/_lib/probe_rotpen.py`
- `revision_experiments/_lib/revx_common.py`
- `revision_experiments/exp4_historical_baselines/e4_run.py`
- `revision_experiments/exp5_full_2x2/e5_run.py`
- `revision_experiments/exp6_trans_rotation/e6_joint.py`
- `revision_experiments/final_targeted/_inspect.py`
- `revision_experiments/final_targeted/ft_common.py`
- `revision_experiments/final_targeted/t3_solver_check.py`
- `revision_experiments/rev_common.py`
- `structured_mismatch_phase0/scripts/m0_inspect.py`
- `structured_mismatch_phase0/scripts/s0_common.py`
- `tj2_supplemental/scripts/tj2_1_remote_cd.py`
- `tj2_supplemental/scripts/tj2_2_fetch_poses.py`
- `tj2_supplemental/scripts/tj2_3_support_screen.py`
- `tj2_supplemental/scripts/tj2_3b_validate_against_tj1.py`
- `tj2_supplemental/scripts/tj2_4_download_ii.py`
- `tj2_supplemental/scripts/tj2_5_cache_ii.py`
- `tj2_supplemental/scripts/tj2_6_objective_ii.py`
- `tj2_supplemental/scripts/tj2_7_predict_ii.py`
- `tj2_supplemental/scripts/tj2_8_stats_ii.py`
