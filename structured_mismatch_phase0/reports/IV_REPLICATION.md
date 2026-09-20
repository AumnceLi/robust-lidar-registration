# IV_REPLICATION.md — Trajectory IV：P1 objective stationarity + P2 local-optimum bias

- 日期：2026-09-09。协议**完全冻结自 VI**（FD 5mm/0.25°、PCA normal、每次重算 NN、J1 p2p / J2 p2l、局部盆地 ±0.30m/±15°、无 robust/trim/outlier），IV 上未调任何参数。脚本 `r6_ext_cache.py`→`r7_ext_objective.py`→`r10_stats.py`；数值 `cache/ext/ext_objective_iv.npz`、`ext_stats_iv.json`。
- IV：2428 scans，range 2.81–16.81 m（VI 仅 8.75–14.8 m）。Nuisance 算子直接套用 VI 冻结值（`frozen_nuisance_ops.npz`），**不在 IV 重拟合**。
- 声明：GT-started local mechanism probe，**不是** autonomous pose-initialization benchmark。

## P1 — GT 处 objective 非平稳（‖g_real‖ vs model-self null）

| cond | obj | median ‖g_real‖ | median ‖g_self‖ | ratio | Hotelling p | 梯度方向集中度 |
|---|---|---:|---:|---:|---:|---:|
| raw | p2p | 0.0770 | 1.30e-5 | **5904** | 0 | 0.86 |
| raw | p2l | 0.0721 | 5.73e-6 | **12577** | 0 | — |
| N1 | p2p | 0.0306 | 1.30e-5 | 2343 | 3.0e-35 | 0.06 |
| N2 | p2p | 0.0356 | 1.30e-5 | 2729 | 0 | 0.42 |
| N3 | p2p | 0.0565 | 1.30e-5 | 4333 | 0 | 0.72 |
| N3 | p2l | 0.0542 | 5.73e-6 | 9460 | — | — |

> **P1 PASS**：真实 scan 在 GT 处的目标梯度比 model-self 数值零基线大 2.3×10³–1.3×10⁴ 倍，Hotelling T² 全部拒绝"均值梯度=0"（p≤3e-35，raw 下溢为 0）。raw 梯度方向集中度 0.86（跨 scan 稳定指向）。N1 全局 range offset 把 ‖g‖ 压低约 2.5×、并打散方向（集中度 0.06），但残余梯度仍 2300× 于 self——**单一全局 nuisance 无法解释 GT 非平稳**。

## P2 — 局部极小相对 GT 的系统位移（basin-clipped）

| cond | obj | median ‖Δt‖ (mm) | block 95%CI | mean Δt 向量 (mm) | median ‖Δr‖ (°) | 符号一致 | 旋转轴集中 | on-bound |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| raw | p2p | **148.2** | [147.1,149.2] | **[+64.5,+6.5,−2.4]** | — | 0.67 | 0.79 | 0.068 |
| raw | p2l | 156.4 | — | [+53.5,+6.3,−0.1] | 1.27 | — | — | 0.13 |
| N1 | p2p | 131.0 | [129.8,132.0] | [+7.7,+7.0,−2.1] | — | 0.51 | 0.80 | 0.073 |
| N2 | p2p | 138.0 | [136.5,139.4] | [+19.2,+6.9,+3.8] | — | 0.65 | 0.85 | 0.068 |
| N3 | p2p | 151.1 | [149.3,152.4] | [+40.2,+6.6,−2.8] | — | 0.67 | 0.74 | 0.063 |

> **P2 PASS**：raw 下局部极小稳定偏离 GT，中位平移 148–156 mm，平均向量 **+x 方向（+64.5/+53.5 mm）与 VI（+53 mm x）同号**；旋转轴集中度 0.79–0.85；触盆地比例仅 6.8–13%（非 clipping 人造）。N1 消掉大部分 x 均值但**位移幅度仍 131–145 mm**——range offset 解释"平均偏置分量"，不解释"每帧被推离 GT 的幅度/结构"。

## 小结
IV 上 **P1、P2 双双复现 VI**：真实目标在真姿态非平稳、局部极小系统偏离 GT，且不被任何单一全局 nuisance 消除。方向预测（P3）见 `EXTERNAL_NONCIRCULAR_PREDICTION.md`。
