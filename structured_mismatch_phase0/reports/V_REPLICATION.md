# V_REPLICATION.md — Trajectory V：P1 objective stationarity + P2 local-optimum bias

- 日期：2026-09-09。冻结协议同 IV（见 `IV_REPLICATION.md` 与 `FROZEN_REPLICATION_MANIFEST.yaml`），V 上未调参。脚本同上；数值 `cache/ext/ext_objective_v.npz`、`ext_stats_v.json`。
- V：1868 scans，range **2.79–7.76 m（mean 4.82 m）——整体比 VI（8.75–14.8 m）更近，与 VI range 无重叠**；但 target 系观测方向与 VI 高度重合（最近观测夹角中位仅 0.33°）。这一覆盖结构对 P3 支持域判定是决定性的（见 EXTERNAL 报告）。
- GT-started local mechanism probe，非初始化基准。

## P1 — GT 处 objective 非平稳

| cond | obj | ratio ‖g_real‖/‖g_self‖ | Hotelling p | 梯度方向集中度 |
|---|---|---:|---:|---:|
| raw | p2p | **5539** | 1.2e-280 | 0.27 |
| raw | p2l | **10863** | — | — |
| N1 | p2p | 6733 | 0 | 0.52 |
| N2 | p2p | 7073 | 0 | 0.55 |
| N3 | p2p | 6373 | — | 0.43 |
| N1 | p2l | 12269 | — | — |

> **P1 PASS**：ratio 5.5×10³–1.3×10⁴，Hotelling 全部拒绝零梯度。raw 梯度方向集中度（0.27）低于 IV（0.86）——V 的近距离扫描跨视角梯度方向更分散，但均值仍显著非零。

## P2 — 局部极小偏离 GT

| cond | obj | median ‖Δt‖ (mm) | block 95%CI | mean Δt 向量 (mm) | median ‖Δr‖ (°) | 符号一致 | 旋转轴集中 | on-bound |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| raw | p2p | **173.8** | [172.9,174.6] | [−14.5,−0.7,−2.7] | — | 0.53 | 0.63 | **0.000** |
| raw | p2l | 169.2 | — | [−13.2,+3.9,−1.8] | 2.27 | — | — | 0.07 |
| N1 | p2p | 154.5 | [152.5,157.0] | [−59.2,−0.7,−2.7] | — | 0.67 | 0.62 | 0.000 |
| N2 | p2p | 182.0 | [180.2,183.8] | [−60.0,−0.4,+3.1] | — | 0.66 | 0.85 | 0.000 |
| N3 | p2p | 162.6 | [161.1,164.6] | [−39.1,−0.8,−2.4] | — | 0.64 | 0.59 | 0.000 |

> **P2 PASS**：中位平移 154–182 mm，**on-bound=0（p2p 无一触盆地，结果不是 clipping 人造）**，旋转轴集中 0.59–0.85。V 的平均分量符号（−x）与 IV/VI（+x）相反——这是不同轨迹观测几何下的**方向逐帧由视角决定**的体现，因此 pooled 均值方向不是主证据，逐帧方向预测（P3）才是。

## 小结
V 上 **P1、P2 同样复现**：更近的工作距离下目标仍在 GT 非平稳、局部极小被系统推离 GT 约 0.15–0.18 m，且零触界。但 V 整体落在 VI 支持域之外（range 不重叠），其非循环方向预测只能作为 out-of-support 外推报告（见 `EXTERNAL_NONCIRCULAR_PREDICTION.md`）。
