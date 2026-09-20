# FINAL_FREEZE_MANIFEST (G3)

Generated: 2026-09-10 16:36:47 local, BEFORE any Dataset III point-cloud byte is read.

## Frozen scientific choices

- predictor: VI_ONLY_PREDICTOR_FROZEN.npz ; k=16 ; range_std=2.064279860893169 ; tau_support=0.440330555961148 ; alpha_VI=0.019993613253599 ; 24 patches
- robust objective (G0 M2): Huber IRLS, delta=1.345, scale=1.4826 MAD floored at model NN spacing 0.00811 m; secondary trim keep=0.80
- basin 0.30 m / 15 deg; max_iter 40; tol 1e-8(p2p)/1e-9(p2l); FD 5 mm / 0.25 deg; nearest fixed-model correspondence
- correction (G1): m_corr[i] = m[i] + mu_{lab(i)}(z); levels global/patch/full as in hierarchy_library; ORACLE view z(T_GT)
- deployable (G2): T0 = frozen raw p2p LS local optimum; z0=z(T0); warm-start second registration; patch fallback policy frozen
- evaluation metrics: e_t=||t_hat-t_GT|| mm, e_R=angle(R_hat R_GT^T) deg; block bootstrap L=5/10/20 B=2000; sign-flip L=5
- confirmatory trajectory: Dataset III (metadata-only selection; 371 in-support, 6/6 orientation blocks, deciles 1-4)
- Dataset I stays permanently sealed; no substitution on outcome grounds; single-look, no re-run/edit/frame removal

## SHA256 of every frozen file used by the single-look

| artifact | sha256 |
|---|---|
| common/g_common.py | `f3fad45b64940108ecf192d8ae8ea192c51881310702bfec76ede3ab4a6e3072` |
| G0 scripts/g0_run.py | `8031984ad194fea08c83df4340515837b8bd6606186f31d96ee42dd9c7d94523` |
| G0 scripts/g0_stats.py | `e2ba7d6d618dcd469d41e493229670efa56539a3af379f4847b73513175bda12` |
| G0 frozen_config | `a4e9896c1d7b01b06db8ede09cdc015b8a37841f261d562d8d34b9af04fe1559` |
| G0 decision | `9f62cd8220c8a163b4dbc08d4eb2e1628a1c70a83b8b47fe992ab3f1ac7d4cee` |
| G1 scripts/g1_run.py | `7d0f2424e90946019727c7a7ff7bf23a8c5e8b420aa752f11eed74f6db30d75b` |
| G1 scripts/g1_stats.py | `a01b51e2d7ded153d0f875d6fa8f43180e499cf75a3547a925d2077dda7c9f5d` |
| G1 frozen_config | `aa1b1bd97978d386acd5ba4c8a6332406f7ab7d86f0371c76dcfef9ae5db77dc` |
| G1 decision | `bdcedfb9d9e9119b1b85da3f389eb8e6b37adebd2d28ffb3bdd01a8b19b4fcfe` |
| G2 scripts/g2_run.py | `4d0a7e01a6a5d78e547e49dccb73f77d52dcc9e78c45e52b754e49f3a3d8d4bc` |
| G2 scripts/g2_perturb.py | `9172f21a30c89b97862e108176dbfcccc8b36f0fe4e8e709714971b400dd0d0b` |
| G2 scripts/g2_stats.py | `5a8179a3afe34b70b5848e7bf7bdd27df9402d92f635a0cf70dc937f0e033b7b` |
| hierarchy/hierarchy_transfer.py | `dffeb3c603359007dd84d9e2b0327f67f73bebf3288081435a72e9dc83653b9d` |
| frozen predictor | `8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe` |
| frozen model_cache | `7e53cd544227ba1e8f5c7326a1c23ca5bae6273af275c5a9488eb2a9e42dad6e` |
| frozen patches | `6b4ffd09c6895abfecd1ed1dde1765eeb2d43f5f8e74e0c27dacbf7b6e5f9fe1` |
| phase0 numerical core s0_common | `0acf82fa3cbefc5610f96e9904442f5d8c18b7bebb36f1aa3e59f11386a02c9e` |
| phase0 numerical core m_common | `a0c7ad488a3164a921ab6a77b380a4e0cd768777425d16c82de28fc5e9f237b8` |
| TJ2 support screen | `ccc1eafea693d1b057120d042c19bf96f8833e4cb4ab135219461ee1acff8206` |
| TJ2 cd summary | `fb002fc5def7c2519afc398372492e9875306ccf592bb7ecde476e6b20a968ef` |
| untouched ledger | `dff60c68cd1a1afc0fd761affdd9c449b126c8fa86616da92095180af37d2098` |

## Expected single-look outputs (frozen list)

- G3_FINAL_CONFIRMATION/results/single_look_results.csv
- G3_FINAL_CONFIRMATION/results/g0_iii.csv
- G3_FINAL_CONFIRMATION/results/g1_iii.csv
- G3_FINAL_CONFIRMATION/results/g2_iii.csv
- G3_FINAL_CONFIRMATION/figures/*
- G3_FINAL_CONFIRMATION/FINAL_CONFIRMATION_DECISION.md

## Pre-registered confirmation criteria (decided BEFORE opening III)

C1 (mechanism survives robust): III Huber median e_t remains >> matched self-null and > LS*0.5 (attenuation only).
C2 (mitigation actionable): best of {patch,full} oracle median e_t < raw M0 with paired sign-flip p<0.05 and >=80% frames improved.
C3 (deployable): estimated-view warm pipeline retains >=70% of the oracle mitigation and beats raw on >=60% of in-support frames.
CONFIRMED = C1&C2&C3 ; PARTIALLY_CONFIRMED = C1 and only one of C2/C3 ; NOT_CONFIRMED = C1 fails or both C2/C3 fail.
