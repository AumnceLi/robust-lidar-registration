# PATCH_TRANSFER.md — P4：冻结 24-patch 结构与 patch-influence 的外部迁移（secondary）

- 日期：2026-09-09。**主预测统计锁定后**才打开 IV/V residual map；使用相同 24 patches，**不重新聚类**。脚本 `r9_transfer.py`；机器表 `reports/patch_transfer.csv`。
- 规则：VI 先定义冻结量（patch residual profile、每 patch expected influence ranking I_j^VI），再检验其是否预测 IV/V；IV/V 当前帧 residual 只用于"自身是否有相似结构"，不作主 predictor。

## 1. 冻结 patch residual profile 的迁移
VI 冻结 profile（24 维，patch_matrix）vs 外部 IN_SUPPORT（IV）/全部（V，因 IN=0）池化每 patch 中位 unsigned residual 的 Spearman：

| 轨迹 | 使用集合 | profile Spearman |
|---|---|---:|
| IV | IN_SUPPORT (156) | **0.430** |
| V | ALL=OUT (1868) | **0.707** |

> 冻结 patch 的残差高低排序在两条新轨迹上方向性复现（V 强 0.71，IV 中等 0.43），说明"哪些物理区域失配重"是物体级、跨轨迹稳定的。

## 2. VI patch-influence ranking → 外部 influence
VI 每 patch 期望梯度影响 I_j^VI（m4，p2p leave-one-patch-out）vs 外部同法计算的 I_j（IV 每 5 帧取 IN_SUPPORT 共 32 帧；V 每 5 帧共 374 帧；12 个共享 FD probe，分解闭合同 VI）：

| 轨迹 | influence ranking Spearman | 帧内 residual–‖g_j‖ ρ（VI=0.53） | n 子集 |
|---|---:|---:|---:|
| IV | **0.046**（基本无） | 0.266 | 32 |
| V | **0.442**（中等） | 0.126 | 374 |

> influence 排名迁移**不一致**：V 中等复现（0.44），IV 的 156 帧 IN_SUPPORT 子集上仅 0.05（且子集仅 32 帧、估计噪声大）。外部帧内"残差高的 patch 梯度贡献大"关系（0.27/0.13）也弱于 VI（0.53）。这与 VI 内部已知弱点一致：**静态全局 profile 与逐帧 influence 在 VI 里就只有 ρ=−0.46 的错位**，外部进一步表明 patch-influence 比 patch-residual-profile 更依赖具体观测几何。

## 3. 对 TJ1-F 的判定
- 冻结 patch **residual profile 方向性复现**（0.43/0.71）→ F 的"patch pattern 方向性复现"部分成立。
- **influence ranking 仅 V 复现、IV IN_SUPPORT 不成立** → F 不完全满足，属**混合/部分**。
- 严格按"mechanistic influence analysis，非 filtering algorithm、不主张删 patch 提精度"表述；本轮不做任何 correction。
