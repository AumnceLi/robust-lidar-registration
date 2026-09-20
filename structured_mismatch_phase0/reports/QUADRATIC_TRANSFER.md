# QUADRATIC_TRANSFER.md — 二次预测 −H⁻¹g 的方向与单一标量幅度迁移

- 日期：2026-09-09。VI 内部已知：−H⁻¹g **方向强、幅度弱**（raw p2p 方向中位 cos 0.959、combined 0.998，但 raw 幅度 slope≈0.02、d̂ 中位 344.8 mm vs 实测 161.4 mm，过估约 50×；p2l 方向失效 0.386）。
- 本轮规则：**Primary 只检验方向迁移**（见 EXTERNAL 报告，已强）；**Secondary 允许在 VI-only 上拟合唯一一个过原点标量 α_VI，禁止在 IV/V 重拟合**。脚本 `r9_transfer.py`；`quad_alpha.npz`、`patch_transfer.csv`。

## 1. 唯一 VI 标量
- α_VI = Σ(d̂_t·Δt*)/Σ(d̂_t·d̂_t)（VI raw p2p 平移，过原点）= **0.019994**，冻结进 predictor。

## 2. 外部幅度迁移（α_VI·d̂ vs 实测 Δt*）

| 轨迹 | 集合 | 过原点 slope（理想=1） | 幅度 Spearman（要求≥0.4） | RMSE (mm) |
|---|---|---:|---:|---:|
| IV | IN_SUPPORT(156) | **11.71** | −0.15 | 156.5 |
| V | ALL=OUT(1868) | **0.019** | +0.18 | 285.7 |

## 3. 判定：LEVEL4 不成立
1. 两条轨迹的 slope 严重不一致（IV 11.7、V 0.019，相差 ~600×），说明 GT 处名义 Hessian 对步长的曲率尺度**跨轨迹不稳定**：VI 上 α=0.02 恰好匹配 V 的尺度，却在 IV IN_SUPPORT 上欠缩 11.7×。不存在一个 VI-only 标量能同时标定两条外部轨迹的幅度。
2. 幅度 Spearman 均未达 0.4（−0.15 / +0.18），且 IV 为负。
3. 因此 **Level-4（−H⁻¹g 定量预测 bias 幅度）不支持**；本轮只主张**方向/符号可迁移**。这与 VI 内部"方向强、幅度弱"完全一致，也指明后续若要做幅度，需要 correspondence-updated curvature 或隐式微分（属后续方法阶段，本轮不做）。
4. 方向层面的二次预测仍然是本研究最强结果之一：VI 内部 0.959、IV IN_SUPPORT 0.841/0.982、V 外推 0.902/0.891，跨三轨迹一致为正且置换显著。
