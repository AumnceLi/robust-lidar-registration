# VI_NONCIRCULAR_VALIDATION.md — VI 内部非循环验证（Gate NC0）

- 日期：2026-09-09。**TRAIN/DEFINE ON VI ONLY**：预测 scan t 时，绝不使用 t 自身的 residual；只用 nominal CAD、t 的 GT 观测几何（range / target 系观测方向 / 每点 NN model 索引与冻结 patch，均为几何）以及**其他 VI scan** 学到的 mismatch template。
- 脚本：`r3_vi_template.py`（模板+Protocol A/B）、`r4_nc0.py`（统计+NC0）、`r_freeze_predictor.py`（冻结）。数值：`cache/rescue/r3_*.npz`、`nc0_vi.json`、机器表 `reports/vi_noncircular.csv`。

## 1. VI-only view-conditioned mismatch template
- 观测描述子 z=(range, target 系观测方向单位向量 u)，u 由 GT 位姿的传感器原点 o=−Rᵀt 归一化得到。
- 对每个冻结 patch j，模板 μ_j(z)=k 个最近观测 VI scan 的**每 patch 平均失配 3-向量**的自适应高斯核局部均值（w=exp[−½(d/d_k)²]，d²=(Δrange/σ_range)²+观测夹角²，σ_range=2.064 m 为 VI 自身 std）；无神经网络。
- 预测云 Q̂_i = m_nn(i) + μ_{j(i)}(z_t)；ĝ=∇J(Q̂)|GT；**Δξ̂=−pinv(H_nom)ĝ，H_nom 只由 nominal 支撑云 m_nn 构造（不含被预测 scan 的残差）**。
- 超参数 k 只在 VI 内由 Protocol-A 中位方向余弦选择：网格 {8,16,32,64} → 中位 cos 0.937 / **0.940** / 0.931 / 0.898，**k\*=16**（对 k 稳健，非尖峰调参）。

## 2. 两套非循环协议
- **Protocol A**：留一 scan，并 embargo [t−10,t+10]（时间近邻全部剔除）。
- **Protocol B**：按 GT 姿态观测方向的累计角行程把 VI 切成 6 个时序连续 orientation block（70/70/79/96/103/83 scan），整 block hold-out，其余 block 建模板。

## 3. NC0 主结果（主终点：平移方向 cos(Δt̂, Δt*)）

| 协议 | condition/obj | median cos | mean | moving-block 95%CI | cos>0 比例 | 向量配对置换 p | 幅度 Spearman（次要） |
|---|---|---:|---:|---:|---:|---:|---:|
| A | **raw / p2p（主）** | **0.940** | 0.935 | **[0.929, 0.948]** | **1.00** | **0.0005** | −0.04 |
| A | raw / p2l | 0.984 | 0.927 | [0.982,0.986] | 0.97 | 0.0005 | −0.06 |
| A | N3-scale / p2p | 0.909 | 0.905 | [0.895,0.921] | 1.00 | 0.0005 | −0.20 |
| A | N3-scale / p2l | 0.983 | 0.924 | [0.981,0.984] | 0.97 | 0.0005 | −0.05 |
| A | N4-combined / p2p | 0.328 | 0.334 | [0.297,0.360] | 0.98 | 0.0005 | −0.27 |
| A | N4-combined / p2l | 0.468 | 0.424 | [0.432,0.505] | 0.95 | 0.0005 | −0.04 |
| B | raw / p2p | **0.940** | 0.928 | [0.927,0.947] | 1.00 | 0.0005 | −0.09 |
| B | raw / p2l | 0.982 | 0.926 | [0.979,0.984] | 0.97 | 0.0005 | −0.16 |
| B | N3-scale / p2p | 0.904 | 0.896 | [0.892,0.915] | 1.00 | 0.0005 | −0.26 |
| B | N4-combined / p2p | 0.317 | 0.317 | [0.284,0.352] | 0.97 | 0.0005 | −0.28 |

- 置换零分布为**向量级**配对零：把预测向量按 scan 置换后再与固定实测向量求 cos（B=2000），p=(1+#null≥obs)/(B+1)=0.0005（下限）。
- moving-block bootstrap：block 长度由 VI 实测位移自相关确定（=5 scan），非 pointwise。

## 4. NC0 判定（阈值：median≥0.70、block-CI 下界>0、≥75% 正向、p≤0.01）
> **NC0 = PASS（四项全过）。** 主终点 raw/p2p median cos=**0.940**、block-CI [0.929,0.948] 下界远大于 0、**100%** scan 方向为正、置换 p=0.0005；整 orientation-block 留出（Protocol B）结果几乎相同（0.940），证明不是时间近邻泄漏。p2l 方向更强（0.98）。
>
> **因此不触发 STOP_CIRCULAR_MECHANISM，允许下载 IV/V。**

## 5. 诚实的边界
1. **方向强、幅度弱**：‖Δt̂‖ 与 ‖Δt*‖ 的 Spearman≈0（−0.04…−0.27），与 VI 既有结论一致——VI template 能非循环地预测"往哪偏"，但 GT 处 H 对步长幅度过估；幅度只允许后续用**单一 VI 标量 α_VI=0.0200** 标定（冻结，见 QUADRATIC_TRANSFER）。
2. **N4-combined 明显较弱（0.32–0.47）**：N4 是 over-parameterized stress test，其互相补偿参数破坏了 view-conditioned 模板；主 nuisance 控制为 RAW/N1/N2/N3，raw 与 N3-scale 均强（0.91–0.98），结论不依赖 N4。
3. 预测器已在打开 IV/V **之前**冻结：`VI_ONLY_PREDICTOR_FROZEN.npz`（SHA256 `8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe`），k\*=16、σ_range、τ_support=0.4403、α_VI 全部锁定，IV/V 上禁止再调。
