# EXTERNAL_NONCIRCULAR_PREDICTION.md — P3：VI-only predictor → IV/V 的非循环外部预测（全文最关键实验）

- 日期：2026-09-09。**TRAIN/DEFINE ON VI ONLY，TEST ON IV/V ONLY。** 预测 IV/V 帧 u 时，输入**只有**：VI 冻结模板 `VI_ONLY_PREDICTOR_FROZEN.npz`（SHA256 `8abcc82d…`，k\*=16）、u 的 **GT 观测几何**（range、target 系观测方向、每点 NN model 索引与冻结 patch，纯几何）、nominal CAD；**绝不读取 u 自身的 residual/SPS/R4/signed/profile**。
- 预测：μ_j(z_u)（VI view-conditioned patch 模板）→ Q̂=m_nn+μ → ĝ=∇J(Q̂)|GT，**Δξ̂=−pinv(H_nom)ĝ，H_nom 只由 nominal 支撑云构造**。再与 IV/V 实测 basin-clipped 局部极小 Δξ* 比较。脚本 `r8_ext_predict.py`、`r10_stats.py`；逐帧表 `reports/iv_prediction.csv`、`v_prediction.csv`，汇总 `trajectory_summary.csv`。
- 主终点：平移方向 cos(Δt̂,Δt*)。统计：median、mean、**moving-block bootstrap 95%CI（L=5，VI 自相关定长，防 pseudoreplication）**、正向比例、**向量配对置换 p（把预测向量按帧置换 B=2000）**。
- 支持域 τ_support=0.4403 在打开 IV/V **之前**由 VI leave-block-out nearest-training distance 的 95 分位冻结；d²=(Δrange/2.064)²+观测夹角²。**阈值锁定后不改。**

## 1. 支持域构成（冻结阈值的直接结果，非事后选择）

| 轨迹 | range 区间 | 最近 VI range 项（中位） | 最近 VI 观测夹角（中位） | IN_SUPPORT | OUT |
|---|---|---:|---:|---:|---:|
| IV | 2.81–16.81 m | 1.15（p5=0.00，有重叠） | 31.7°（仅少数对齐） | **156** | 2272 |
| V | 2.79–7.76 m | 2.10（**最小 0.495，range 完全不重叠**） | **0.33°（方向几乎完全重合）** | **0** | 1868 |

- IV 有 156 帧同时落在 VI 的 range 与 orientation 邻域 → 构成 confirmatory IN_SUPPORT 集。
- **V 没有任何一帧 d≤τ**：V 是近距离接近轨迹，range 与 VI 完全分离（最近帧的纯 range 项 0.495 已使组合距离 ≥0.484>0.440），尽管其观测方向与 VI 几乎一致。这是数据覆盖事实，不是预测失败。

## 2. 外部方向预测主结果

| 轨迹 | 集合 | obj | n | median cos | mean | block 95%CI | cos>0 | 向量置换 p | 幅度 Spearman（次要） |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| **IV** | **IN_SUPPORT（confirmatory）** | p2p | 156 | **0.841** | 0.826 | **[0.811,0.866]** | **1.00** | **0.0005** | −0.15 |
| **IV** | **IN_SUPPORT（confirmatory）** | p2l | 156 | **0.982** | 0.961 | **[0.975,0.987]** | **1.00** | **0.0005** | −0.05 |
| IV | IN，−D1 模板（符号一阶预定） | p2p | 156 | 0.778 | — | — | 1.00 | — | — |
| IV | OUT（外推附录） | p2p | 2272 | 0.145 | 0.111 | [0.055,0.215] | 0.58 | 0.33 | −0.27 |
| IV | OUT | p2l | 2272 | 0.048 | 0.021 | [−0.060,0.132] | 0.52 | 0.14 | −0.09 |
| V | **OUT（全部，因 IN=0）** | p2p | 1868 | **0.902** | 0.723 | **[0.887,0.914]** | **0.91** | **0.0005** | −0.50 |
| V | OUT | p2l | 1868 | **0.891** | 0.722 | **[0.876,0.902]** | **0.93** | **0.0005** | −0.22 |
| V | OUT，−D1 模板 | p2p | 1868 | 0.828 | — | — | 0.86 | — | — |

外部 PASS 阈值（每条轨迹）：median cos≥0.60、block-CI 下界>0、≥70% 正向、置换 p≤0.01。

## 3. 判读（严格、不事后改阈值）
1. **IV confirmatory（IN_SUPPORT）明确 PASS**：median cos 0.841/0.982，CI 下界 0.811/0.975 远大于 0，**100% 正向**，置换 p=0.0005（下限），−D1 一阶方向 0.778。VI 只凭"视角几何+冻结模板"就非循环预测出未见 IV 帧的 bias 方向，且不使用该帧任何残差。
2. **支持域设计被结果验证为必要而非挑选**：IV 的 OUT 集（视角/range 未对齐）方向 cos 跌到 0.14/0.05、置换 p=0.33/0.14（≈机会水平）。按 range 分层：IV 0–6 m cos=−0.03、6–8.75 m −0.13、8.75–14.8 m（仅 range 对齐）0.30、**14.8–20 m 且方向对齐 0.88**——真正决定迁移的是"观测方向是否被 VI 覆盖"。
3. **V 经验上强迁移，但 confirmatory 不可评估**：V 全部落在冻结支持域外（IN=0），按 §11/§17 只能作为 **out-of-support 外推附录**；即便如此其方向 cos 0.902/0.891、CI>0、91–93% 正向、p=0.0005、−D1=0.828。机制解释：V 观测方向与 VI 几乎重合（0.33°），而失配机制主要由**观测方向**条件化，因此跨 range 仍成立。**但我们不把外推结果重标为 confirmatory，也不回改 τ。**
4. **幅度不迁移（与 VI 内部一致）**：方向强、幅度 Spearman 弱/负（IV −0.15、V −0.50/−0.22），Level-4 幅度迁移不成立（详见 QUADRATIC_TRANSFER）。

## 4. 对顶刊门的含义
- TJ1-D（VI→IV 方向）**confirmatory PASS**。
- TJ1-E（VI→V 方向）：**confirmatory 集合 n=0，无法按冻结规则判定 PASS**；外推证据强（0.90）但只能计为 supportive/extrapolation。
- 要把 V 升级为 confirmatory，唯一合规路径是**新一轮冻结**：扩展 VI 训练覆盖到近距离，或补一条 range 与 VI（8.75–14.8 m）重叠的轨迹；**不得在本轮反改 τ_support**。
