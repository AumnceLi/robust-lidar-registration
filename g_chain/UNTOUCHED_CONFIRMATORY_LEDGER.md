# UNTOUCHED_CONFIRMATORY_LEDGER.md

- Created: 2026-09-10 13:39 +08:00 (Asia/Shanghai), before ANY new outcome-bearing computation of the G-chain.
- Owner rule: this ledger is the single authority on which trajectory may be opened for the final single-look. It must not be edited after the FINAL_FREEZE_MANIFEST is sealed except to append the single-look record.

## 1. Per-trajectory point-cloud outcome status (audited from disk, not memory)

| Dataset | role in prior campaign | `.3d` point clouds ever downloaded/opened? | local `.3d` count now | local zip now | pose-only metadata | status label |
|---|---|---|---:|---|---|---|
| VI  | development trajectory (all frozen decisions made here) | YES (opened throughout) | 501 | present (vi) | yes | DEVELOPMENT — never confirmatory |
| IV  | TJ1 confirmatory external (opened 2026-09-09) | YES | 2428 | present (iv, 189,777,178 B) | yes | POST-DEVELOPMENT HELD-OUT (already opened) |
| V   | supportive, OUT-OF-SUPPORT extrapolation (opened) | YES | 1868 | present (v, 152,090,372 B) | yes | POST-DEVELOPMENT HELD-OUT, extrapolation-only forever |
| II  | TJ2 prospectively-selected supplemental (opened once, 2026-09-09) | YES (the one permitted TJ2 single-look) | 1253 | present (ii, 89,932,451 B) | yes | POST-DEVELOPMENT HELD-OUT (already opened once) |
| **III** | never used | **NO — never downloaded, never byte-read** | **0** | **absent** | yes (1302 `.pose`) | **FINAL UNTOUCHED CONFIRMATORY (primary single-look)** |
| I   | never used | **NO — never downloaded, never byte-read** | **0** | **absent** | yes (2483 `.pose`) | **SEALED RESERVE — must stay untouched; not opened even at G3** |

Disk audit command evidence (2026-09-10): no directory named `epos_dataset_i` / `epos_dataset_iii` contains any `.3d`; no `epos_dataset_i.zip` / `epos_dataset_iii.zip` exists anywhere under `D:\doubao`. Only PROPFIND / ZIP central-directory metadata and `.pose` files (which carry pose, NOT point-cloud outcomes) were ever read for I/III during the TJ2 metadata-only screen.

## 2. Pose-only metadata fingerprints (point clouds NOT included)

| Dataset | n `.pose` | concatenated SHA256 over pose files (sorted) | pose dir last write |
|---|---:|---|---|
| I   | 2483 | `66fd2f740eada795cab124f344d55b53a951e87cba653f60057b6a2b4c1f4d1a` | 2026-09-09 19:57:07 |
| III | 1302 | `cf1f0d3afc94f24222fd964a4931fe809aa9128023875552b393f648eda64f2c` | 2026-09-09 20:04:45 |

Remote zip central-directory facts (from `tj2_supplemental/metadata/cd_summary.json`, metadata only):
`epos_dataset_i.zip` = 194,066,093 B, 2483×(.3d+.pose); `epos_dataset_iii.zip` = 94,194,038 B, 1302×(.3d+.pose). Download endpoint is the DESY public WebDAV share already used for II/IV/V (token frozen in the existing r5/tj2_4 download scripts).

## 3. Why III is the primary single-look (decision made on METADATA ONLY, before any point-cloud read)

Frozen support rule τ_support = 0.4403305559611483 applied to pose-derived view geometry only (`support_screen_summary.json`):

| candidate untouched | N_IN_SUPPORT | #support blocks | temporal deciles with support | distinct VI orientation blocks hit | in-support range (m) |
|---|---:|---:|---:|---:|---|
| I   | 313 | 1 (one contiguous run of 313) | 2 (deciles 0–1 only) | 2 of 6 (blocks 0,1) | 14.809–14.891 (a 8 cm sliver) |
| **III** | **371** | 1 (371) | **4 (deciles 1–4)** | **6 of 6** | 8.250–15.464 |

III is chosen as the FINAL UNTOUCHED CONFIRMATORY trajectory on metadata-only grounds: it has more frozen-support frames (371 > 313), spans 4 temporal deciles vs 2, and covers all six VI orientation blocks vs only two; I's support is confined to a single 8 cm range sliver and two orientation blocks, which would be a weaker, more localized confirmation. No predictor cosine / residual / outcome statistic entered this choice (none could — point clouds are sealed).

## 4. Access protocol (hard rules)

1. **III** stays byte-sealed (no download, no `.3d` read) until ALL of: G0 decided, G1 decided, G2 pipeline frozen, hierarchy transfer computed, every baseline/correction/threshold/metric/code hash sealed in `G3_FINAL_CONFIRMATION/FREEZE_MANIFEST.md`.
2. At that point III is downloaded once, its zip byte-size and per-entry CRC checked against `cd_summary.json`, cached with the frozen r6/tj2_5 pipeline, and the ENTIRE frozen G0–G2 evaluation is run **exactly once end-to-end** (single-look). No re-run with a changed formulation, no frame deletion, no subset change, no threshold/support/correction/metric edit afterward, regardless of result.
3. **I remains permanently sealed as a reserve.** It is NOT opened at G3 and NOT used to "rescue" an adverse III result. Opening I would require a new, separately documented protocol decision (out of scope of this G-chain).
4. IV / II / V new results in this G-chain are labelled **post-development held-out / cross-trajectory evaluation** only — never "prospective confirmation" or "independent external validation". Only III (sealed until the end) can carry the final prospective single-look label.

## 5. Who may change this protocol

Only the human author, by explicit written instruction. Automated steps never relax the seal, never substitute I for III on outcome grounds, and never widen the support rule. Last authorized state: as written above (2026-09-10).

## 6. Single-look access record (appended after the seal was lifted exactly once)

- Seal lifted: 2026-09-10, after `G3_FINAL_CONFIRMATION/FREEZE_MANIFEST.md` was written (all frozen file SHA256 recorded).
- Download: `epos_dataset_iii.zip` = 94,194,038 B (matches `cd_summary.json`); zip SHA256 `9a945a0e08affe4147fe3cc35591e909e75596b4ecc1b20a90cec84cd4038856`; `zipfile.testzip()` = no CRC error; 1302 .3d + 1302 .pose extracted; pose-only concat-SHA256 re-verified = `cf1f0d3a…a64f2c` (matches section 2).
- Frozen support rule on cached view geometry: **in-support = 371/1302**, exactly the metadata-screen count.
- The frozen G0–G2 chain was executed **once end-to-end** over all 1302 frames (primary = 371 in-support); outputs `results/g0_iii.csv`, `g1_iii.csv`, `g2_iii.csv`, `single_look_results.csv`, `single_look_summary.json`, figures. No formulation/parameter/threshold/frame subset was changed afterward; no second run.
- Result: **CONFIRMED** (C1 robust-attentuates PASS; C2 patch-level mitigation PASS p=0.0005/99.5% frames; C3 estimated-view PASS, 0.997 retention). See `G3_FINAL_CONFIRMATION/FINAL_CONFIRMATION_DECISION.md`.
- **Dataset I remains permanently sealed** (never downloaded, never opened); it is not used for any follow-up. III is now CLOSED — no re-look permitted.
