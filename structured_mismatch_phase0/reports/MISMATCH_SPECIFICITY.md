# MISMATCH_SPECIFICITY.md — Gate M3：偏置是否被结构化失配特异解释？

- 日期：2026-09-09　样本：501 scans。脚本 `m5_m3_specificity.py`；数值 `cache/rescue/m3_specificity.json`、`m3_summary.csv`。
- 模型：嵌套 OLS，因变量为局部极小位移 Δξ（主终点 **proj = Δt 在跨 scan 平均方向上的有符号投影**；另报 ‖Δt‖、‖Δrot‖）。
  - 控制块 Xc：range、log(point count)、aspect（相对首帧 GT 旋转的测地角）、scan time、tumble rate；raw 模型再加入 **combined-nuisance 残差 J0** 作为全局 nuisance 控制。
  - 失配块 Xm（全部来自冻结特征）：SPS、R4 structured fraction、mean signed residual、excess-return fraction、24-patch profile deviation、残差不对称度。
  - 增量解释量 **partial R² = (SSE_control−SSE_full)/SSE_control**；bootstrap B=2000 得 95%CI；**Null C** 在 range 五分位 bin 内整体置换失配块（保 range 分布）B=1000。
  - **Null D**：按 range/point-count/aspect 最近邻匹配 high vs low 失配 scan，比较 ‖Δt‖（Wilcoxon）。

## 1. 增量 partial R²（失配块 | 控制块）

主终点 proj（有符号方向投影）：

| cond | obj | partial R² | 95% bootstrap CI | Null-C 均值 | permutation p |
|---|---|---:|---:|---:|---:|
| raw | p2p | **0.903** | [0.887, 0.920] | 0.314 | 0.001 |
| raw | p2l | **0.877** | [0.851, 0.906] | 0.290 | 0.001 |
| scale | p2p | 0.667 | [0.500, 0.902] | 0.295 | 0.001 |
| scale | p2l | 0.837 | [0.773, 0.899] | 0.312 | 0.001 |
| **combined** | p2p | **0.447** | **[0.350, 0.653]** | 0.123 | 0.001 |
| **combined** | p2l | **0.482** | **[0.347, 0.623]** | 0.126 | 0.001 |

‖Δt‖：raw 0.888/0.846，scale 0.664/0.753，combined 0.381/0.285（全部 p=0.001、CI 不含 0）。
‖Δrot‖：raw 0.226/0.137，scale 0.217/0.157，combined 0.131/0.296（p=0.001；旋转弱于平移）。

## 2. Null C（range-bin 内置换失配块）
所有真实 partial R² 都远高于其 range-matched 置换零分布（p=0.001，B=1000 的下限）；最大化 nuisance 校正后（combined）真实 0.45–0.48 vs 零 0.12，**CI 完全不含 0**。即：在控制 range/点数/aspect/时间/转速/全局 nuisance 残差后，结构化失配仍独立解释约 45%（combined）到 90%（raw）的系统偏置方向变异，破坏失配↔scan 绑定后效应大幅塌缩。

## 3. Null D（协变量匹配的 high/low 失配对照）
- 104 对匹配（range/point-count/aspect caliper<1.0）；high 失配组 ‖Δt‖ 中位 **0.1635 m**，low 组 **0.1598 m**（均值 0.1627 vs 0.1588），Wilcoxon **p=6.5e-5**。
- 量级差仅 ~3.7 mm：因为共模内缩使所有 scan 的偏置量级都在 ~160 mm，失配主要决定**方向与逐 scan 变异**（proj partial R²=0.90），对总量级的边际影响小。这与 M2（方向高度一致）、M4（局部 patch 主导梯度）自洽。

## 4. Gate M3 判定
> **M3 = PASS。** 冻结的结构化失配特征在控制 range / point-count / aspect / scan-time / tumble / 全局 nuisance 残差后，仍对局部极小的有方向位移提供独立、显著、CI 不含 0、range-permutation 下消失的解释量；即使在最大化全局 nuisance 去除（combined）后仍达 partial R²≈0.45–0.48。Null D 方向一致（high>low，p=6.5e-5），并明确效应主要在方向而非共模量级。不触发 STOP_NO_MISMATCH_SPECIFICITY。

## 5. 复现 / 图
`python m5_m3_specificity.py`；图 `rescue_figs/F7_partialR2.png`。
