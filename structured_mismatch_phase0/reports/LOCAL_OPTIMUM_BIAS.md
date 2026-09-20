# LOCAL_OPTIMUM_BIAS.md — Gate M2：局部极小相对 GT 的系统性位移

- 日期：2026-09-09　数据：VI 全部 501 scans × 两目标 × 三 nuisance 条件。
- 定位声明（Rescue Audit §10）：**GT is intentionally used to probe whether the nominal registration objective is unbiased at the true physical pose. This is NOT a pose-initialization benchmark.** 从 ξ=0（=GT）出发做纯局部优化，得到 T_t*，位移 Δξ_t=log(T_GT⁻¹T_t*)。
- 两个**独立**局部优化器交叉验证：(i) 目标的自然 ICP 求解（p2p=Kabsch、p2l=线性化 Gauss-Newton，全部 501 scan，主结果）；(ii) 带界 L-BFGS-B（预注册 every-5th n=101）。统一裁剪在声明的局部盆地 ‖t‖≤0.30 m、‖rot‖≤15°（9–15 m 距离上仅约 1.4–1.9°，远离 ±120° 对称盆地）；**L-BFGS 触界率=0**。脚本 `m2_objective.py`、`m2c_rebound.py`、`m4_m2_localopt.py`。

## 1. 位移主结果（Δξ，mean vector / magnitude / 方向集中）

| cond | obj | 平均平移向量 (mm) | ‖Δt‖ 中位 [95%CI] mm | 符号一致率 | 方向集中 R (Rayleigh p) | ‖Δrot‖ 均值 (deg) | 旋转轴集中 | Hotelling p |
|---|---|---|---:|---:|---:|---:|---:|---:|
| raw | p2p | **[+53.0, −0.7, −0.4]** | 160.8 [160.0,161.7] | **0.99** | 0.328 (≈0) | 4.46 | **0.815** | 7.6e-182 |
| raw | p2l | [+58.9, −0.4, −0.5] | 159.5 [158.4,160.7] | 0.98 | 0.365 (≈0) | 4.06 | 0.826 | 1.0e-180 |
| scale | p2p | [+33.2,−0.4,−0.4] | 139.6 [138.7,140.5] | 0.79 | 0.239 (≈0) | 4.47 | 0.806 | 1.1e-98 |
| scale | p2l | [+40.7,−0.3,−0.6] | 136.6 [135.5,137.6] | 0.82 | 0.296 (≈0) | 4.06 | 0.838 | 6.1e-111 |
| combined | p2p | [−10.3,−1.2,+2.1] | 63.9 [63.3,64.5] | 0.64 | 0.148 (2.5e-15) | 3.07 | 0.495 | 1.4e-21 |
| combined | p2l | [−8.0,−0.4,+2.2] | 58.1 [57.4,58.8] | 0.59 | 0.117 (8.5e-10) | 2.84 | 0.261 | 3.9e-12 |

**Null A self-floor：模型自配准的局部极小位移中位数 = 0.0000 mm**（real/self 比值 5.8×10⁷–1.6×10⁸）。

## 2. 关键判读（E[Δξ]≠0，而非仅 E‖Δξ‖>0）
1. **平均位移向量显著非零**：raw 两目标一致地沿目标本体 +x 方向偏 53–59 mm（y/z 分量≈0），Hotelling p≤1e-180；这是"有方向的系统偏置"，不是零均值随机抖动。
2. **符号一致率 0.98–0.99（raw）**：99% 的 scan 局部极小都落在平均方向同侧；方向集中 R 的 Rayleigh 检验 p≈0（n=501 下即使 R=0.33 也极强拒绝均匀）。旋转轴集中 0.82（raw）——旋转偏置同样有一致轴。
3. **跨目标一致**：p2p 与 p2l 的平均向量、量级（~160 mm）、方向高度吻合。
4. **独立优化器一致**：ICP 与 L-BFGS 位移方向余弦 0.93–1.00，量级 Spearman 0.82–0.999（raw），触界率 0 → 该局部极小是目标的真实驻点，不是某求解器产物。（L-BFGS 的 success 标志在非光滑 NN 目标上偏保守，故以两求解器一致性作为收敛依据。）
5. **nuisance 稳健性**：去掉全局尺度（scale）后偏置仍 137–140 mm、方向集中显著；即使最大化全局校正（combined，已清零全局 signed mean），残余局部极小仍系统性偏离 GT 约 58–64 mm、Hotelling p≤1e-12。方向一致率降到 0.59–0.64、轴集中降到 0.26–0.50，说明**全局 nuisance 承担了一部分共模偏置，但无法把局部极小移回 GT**。

## 3. 为什么位移量级（~160 mm）大于 signed mean（−38 mm）
J 是平方距离目标，且 R4 结构化失配点（p95≈190 mm、占 71%）权重高；刚性 6-DoF 极小是对全点云的"折中"，故其位移由大残差结构化点主导，量级自然超过平均法向内缩。这与 M3（失配越重、偏置越大）和 M4（高残差 patch 不成比例贡献梯度）一致。

## 4. Gate M2 判定
> **M2 = PASS。** E[Δξ]≠0：局部极小相对 GT 存在显著、方向一致（raw 符号率 0.98–0.99、旋转轴集中 0.82、Hotelling p≈0）、跨两目标与两独立优化器一致、self-floor=0，且在全局 nuisance 去除后仍残留约 58–64 mm 系统位移。不触发 STOP_NO_OBJECTIVE_BIAS，进入 M3。

## 5. 复现 / 图
`m2_objective.py → m2c_rebound.py → m4_m2_localopt.py`；图 `rescue_figs/F3_displacement_direction.png`、`F6_landscape.png`。
