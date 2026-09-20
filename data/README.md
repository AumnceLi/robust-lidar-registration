# Raw datasets — provenance and download

The raw LiDAR trajectories total roughly **3 GB** and are therefore **not committed** to Git.
They are public and can be re-downloaded and byte-verified with the helpers in this repository.
The small **frozen artifacts** derived from them (nominal model, PCA normals, 24 patches, the
VI-only predictor, and all per-frame result tables) **are** committed, so the statistics and
figures reproduce without any download.

## Source

All trajectories and the nominal target model come from the public **EPOS-Lid** HITL release
(real Livox Mid-40 scans), distributed through a DLR/DESY public WebDAV share:

```
https://syncandshare.desy.de/public.php/webdav/
```

The read-only public share token is already embedded in the frozen download scripts
(`r5_download_ivv.py`, `g3_download_cache.py`, `tj2_4_download_ii.py`); it is a public share
credential, not a private account secret.

File format (see `structured_mismatch_phase0/scripts/s0_common.py`):

- `NNNN.3d` — ASCII `x y z` per line, **metres**, **LiDAR frame** (the nominal `target_model.3d`
  is in the TARGET frame).
- `NNNN.pose` — line 1 timestamp [s]; line 2 target position in the LiDAR frame `t`; line 3
  scalar-first Hamilton quaternion `q_s q_x q_y q_z` rotating TARGET → LIDAR; pose anchors the
  scan **end** instant.
- Ground-truth alignment: `P_target = R^T (P_lidar − t)`.

## Trajectories

| Tag | Zip | Verified zip bytes | Scans | Used in support | Role | Acquired by |
|---|---|---:|---:|---:|---|---|
| VI | `epos_dataset_vi.zip` | ~33.9 MB | 501 | 501 | Development / field estimation | `data/download_epos.py` |
| IV | `epos_dataset_iv.zip` | 189,777,178 | 2,428 | 156 | External transfer | `data/download_epos.py` / `r5_download_ivv.py` |
| V  | `epos_dataset_v.zip`  | 152,090,372 | 1,868 | — | External control | `data/download_epos.py` / `r5_download_ivv.py` |
| II | `epos_dataset_ii.zip` | 89,932,451 | 1,253 | 428 | Difficult external transfer (supplemental) | `tj2_supplemental/scripts/tj2_4_download_ii.py` |
| III | `epos_dataset_iii.zip` | 94,194,038 | 1,302 | 371 | **Untouched confirmatory, single-look** | `g_chain/G3_FINAL_CONFIRMATION/scripts/g3_download_cache.py` |

The nominal model `epos_target_model.3d` (67,870 points) is committed at
`external_dataset_scout/intermediate/samples/epos_target_model.3d` and is also embedded in the
frozen `structured_mismatch_phase0/scripts/cache/model_cache.npz`.

## Where the data must land

| Data | Expected path (relative to repo root) |
|---|---|
| VI raw scans | `structured_mismatch_phase0/scripts/vi_data/epos_dataset_vi/` |
| IV / V raw scans | `structured_mismatch_phase0/scripts/ivv_data/epos_dataset_{iv,v}/` |
| II raw scans | `tj2_supplemental/ii_data/epos_dataset_ii/` |
| III raw scans + built cache | `g_chain/G3_FINAL_CONFIRMATION/download/epos_dataset_iii/` and `…/iii_cache/` |

`data/download_epos.py` places VI/IV/V correctly and verifies zip CRC and scan counts. After
downloading, the per-scan aligned caches are rebuilt by the run/cache scripts (e.g.
`r6_ext_cache.py`, `g3_download_cache.py`, `tj2_5_cache_ii.py`).

## Dataset II / III gated order (do not skip)

These trajectories were opened under a pre-registered, single-look policy. Use the frozen scripts
in order so the metadata screen and byte/pose fingerprints are enforced:

```bash
# III (download -> CRC -> pose SHA-256 -> aligned cache -> metadata-only support screen)
python g_chain/G3_FINAL_CONFIRMATION/scripts/g3_download_cache.py

# II (metadata-only pose fetch/screen first, point clouds only for the single outcome test)
python tj2_supplemental/scripts/tj2_1_remote_cd.py
python tj2_supplemental/scripts/tj2_2_fetch_poses.py
python tj2_supplemental/scripts/tj2_3_support_screen.py
python tj2_supplemental/scripts/tj2_4_download_ii.py     # cross-checks poses vs metadata fetch
python tj2_supplemental/scripts/tj2_5_cache_ii.py
```

Dataset I is permanently sealed and is never downloaded.

## License

The EPOS-Lid datasets are licensed under **CDLA-Sharing-1.0**; see
[`LICENSE_EPOS_DATASET.md`](LICENSE_EPOS_DATASET.md). Cite the EPOS-Lid release in any derived
work.
