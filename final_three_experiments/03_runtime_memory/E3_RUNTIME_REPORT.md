# E3 — Runtime / Memory / Deployment-Cost Evaluation (FINAL ROUND)

**Question.** What computational cost do Raw / Patch / Full / Estimated Full add relative to Raw?
This is a transparent cost measurement, **not** a real-time claim; no algorithm was changed for timing
(only logging-free runs and fair, uniform thread pinning).

## 1. Benchmark environment (fixed single machine)

| Item | Value |
|---|---|
| CPU | Intel Core Ultra 9 285K, 24 physical / 24 logical cores |
| RAM | 31.6 GB (Win32) / 33.95 GB (psutil) |
| OS | Windows 11 Pro 10.0.22631 (x86-64) |
| Python / NumPy / SciPy / scikit-learn / pandas / psutil | 3.14.7 / 2.5.3 / 1.18.1 / 1.9.0 / 3.0.5 / 7.2.2 |
| GPU | none used (the frozen ICP is CPU-only; no GPU introduced) |
| Parallelism | **single process; BLAS threads=1 (`OMP/MKL/OPENBLAS=1`); cKDTree query workers=1**, identical for every method |
| Frames | frozen 20/trajectory roster = **80 frames** (same roster as E1), not the full 1456 |
| Repeats | 1 warm-up + 5 timed calls/frame/method; per-frame value = median over repeats; deployment distribution = across-frame median/p25/p75/p95 |
| Correctness gate | timed Raw/Huber/Patch/Full reproduce frozen `g1_oracle_vi` M0/M2/M4/M5 and EstimatedFull reproduces `g2_vi` **est_warmstart** to ≤ 2.8e-14 mm (`e3_calibration.json`) |

## 2. Main deployment table (80 frames, single-thread, ms)

| Method | reusable model? | registrations/frame | median latency | p95 | ×Raw | peak RSS (MB) |
|---|---|---:|---:|---:|---:|---:|
| Raw | yes (nominal cached) | 1 | **477.5** | 808.1 | 1.00 | 158.3 |
| Huber | yes | 1 | 588.4 | 988.4 | 1.23 | 157.1 |
| **Patch** | yes (corrected model+tree cached once) | 1 | **412.5** | 611.5 | **0.86** | 158.5 |
| PatchHuber | yes (cached once) | 1 | 470.1 | 736.1 | 0.98 | 159.2 |
| Full | no (query-dependent model+tree/frame) | 1 | 427.7 | 702.0 | 0.90 | 157.5 |
| **Estimated Full** | partial (2nd model query-dependent) | **2** | **953.3** | 1638.7 | **2.00** | 159.6 |

## 3. Decomposed stage cost (median ms, 80 frames)

| Method | view query | corrected-model build | KD-tree build | registration 1 | registration 2 |
|---|---:|---:|---:|---:|---:|
| Raw / Huber / Patch / PatchHuber | 0 | 0 (cached) | 0 (cached) | 477 / 588 / 412 / 470 | – |
| Full | 0.09 | 0.84 | 10.88 | 416.2 | – |
| Estimated Full | 0.08 | 0.84 | 10.82 | 480.5 (nominal) | 417.2 (corrected) |

- Once the Patch corrected geometry is cached, its **per-frame overhead is zero**; its latency is in
  fact lower than Raw because the corrected model converges in fewer ICP iterations (median 0.86× Raw).
- **Full** rebuilds a query-dependent corrected model + KD-tree every frame, but this is only
  ≈ **11.8 ms** (query 0.09 + build 0.84 + tree 10.88); registration dominates, so Full is comparable
  to Patch (0.90× Raw).
- **Estimated Full** runs the frozen nominal registration **and** a second corrected-model
  registration, hence ≈ **2.0× Raw** (953 ms median / 1639 ms p95 single-thread). The two
  registrations, not the field query, are the cost.

## 4. Memory (fresh process per method)

All methods peak at **157–160 MB RSS**; the common frozen footprint (model + VI library) dominates,
and method-specific working-set delta is only **3.1–4.8 MB**; tracemalloc Python-allocation peak is
5.4–7.6 MB. Patch/Full/Estimated Full add essentially **no memory** over Raw.

## 5. One-time offline calibration cost (not charged to per-frame latency)

| Step | median time | output size |
|---|---:|---:|
| 24-patch MiniBatchKMeans (k=24, normal weight 0.30, seed 42, n_init 20, batch 4096) | **151.7 ms** | `patches.npz` 26.1 KB |
| VI `mu_patch` field construction (all 501 scans) | **0.18 ms** | `mu_patch` 576 B |
| Patch corrected-model build (one-time) | 0.91 ms | – |
| Patch KD-tree build (one-time) | 11.0 ms | – |
| Frozen VI predictor on disk | – | 288.5 KB |

The re-clustering reproduces the frozen partition **exactly** (label-exact, Adjusted Rand = 1.0), so
the timed calibration is precisely the frozen recipe. Re-targeting / re-calibrating a field therefore
costs ≈ 0.16 s of clustering once, plus sub-millisecond field assembly — negligible offline cost.

## 6. Interpretation and verdict

- On the tested workstation, with geometry cached, **Patch adds no per-frame overhead and is slightly
  faster than Raw**; **Full** pays only ≈ 12 ms/frame for its query-dependent model/tree; **Estimated
  Full doubles latency** because it performs two registrations. Memory is effectively identical across
  methods (~158 MB); one-time calibration is sub-0.2 s and 29 KB of artifacts.
- **Flag: `DEPLOYMENT_COST_LIMITATION` (Estimated Full only).** The fully self-contained one-pass
  Estimated Full pipeline costs ≈ 2× a single registration (~0.95 s/frame median single-thread here).
  This is an honest deployment limitation to state, not a reason to alter the algorithm. The cheaper
  cached Patch path has no such penalty.
- Per the brief, no "real-time / flight-ready" claim is made; numbers are single-thread on one
  workstation and would scale with cores/multithreading equally for all methods.

## 7. Artifacts (hashes in `e3_provenance.json`)

`runtime_summary.csv` (required schema, per-trajectory + ALL), `e3_compact_table.csv`,
`e3_runtime_framewise.csv`, `e3_runtime_repeats.csv` (raw repeats), `e3_memory.csv`,
`e3_calibration.json`, `e3_key_numbers.json`. Runners: `e3_core.py`, `e3_benchmark.py`,
`e3_mem_worker.py`, `e3_analyze.py`, `e3_provenance.py`.
