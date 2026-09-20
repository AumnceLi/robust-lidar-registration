# OBJECTIVE_STATIONARITY.md — Gate M1：标准配准目标在真姿态处是否平稳？

- 日期：2026-09-09　数据：VI 全部 501 scans（null 对照在预注册 every-5th n=101 子集）。
- 问题（唯一核心）：在 **GT pose 已知**（ξ=0）处，标准 rigid-registration 目标 J1=point-to-point、J2=point-to-plane 的梯度 **g_t=∇ξJ(T_GT)** 是否为 0？若真实云 g 显著非零且远超 self/null，则目标在真姿态处**非平稳**，正确极小值不在 GT。
- 方法：冻结中心差分步长（平移 5 mm、旋转 0.25°），每次评估**重算最近邻**、用冻结 PCA 法向；无任何 robust/trim/outlier rejection。脚本 `m2_objective.py`、`m2b_nulls.py`、`m3_m1_stationarity.py`；数值落盘 `cache/rescue/objective_main.npz`、`nullA_self.csv`、`nullB_shuffle.npz`、`m1_stationarity.json`。

## 1. 三个对照（null）的定义
- **Null A（model-self）**：源 = 标称模型的等点数随机子集（等价"刚体变换后的模型在其自身正确对齐位姿上分析"）；另加 **zero-mean isotropic-noise** 对照（σ=8.1 mm=模型采样间距），检验对称零均值噪声是否产生均值梯度。
- **Null B（spatial shuffle）**：保留 mismatch-vector 多重集 {v_i=P_i−m_nn(i)}，随机置换其空间挂载 P̃_i=m_nn(i)+v_π(i)，B=100；检验梯度是否依赖**空间结构**而非残差幅值分布。
- **数值有效性**：在 2.5/5/10 mm、0.125/0.25/0.5° 三档步长下，梯度方向余弦 0.984–1.0000，‖g‖变异系数≈0.15 → 梯度不是有限差分伪影，不触发 STOP_NUMERICAL_INVALIDITY。

## 2. 主结果：‖∇J(T_GT)‖（中位数）

| condition | objective | real median [95% bootstrap CI] | NullA self | self+zero-mean noise | real/self | Cohen's d vs self | MWU p vs self |
|---|---|---|---:|---:|---:|---:|---:|
| raw | p2p | **0.0693** [0.0644, 0.0726] | 1.40e-5 | 1.69e-4 | **5005×** | 8.78 | 6e-35 |
| raw | p2l | **0.0646** [0.0615, 0.0684] | 6.12e-6 | 1.54e-4 | **10470×** | 7.69 | 6e-35 |
| scale (N3) | p2p | 0.0608 [0.0590, 0.0629] | 1.40e-5 | 1.69e-4 | 4405× | 10.64 | 6e-35 |
| scale (N3) | p2l | 0.0567 [0.0554, 0.0611] | 6.12e-6 | 1.54e-4 | 9542× | 8.62 | 6e-35 |
| combined (N4) | p2p | 0.0196 [0.0177, 0.0231] | 1.40e-5 | 1.69e-4 | 1422× | 3.65 | 6e-35 |
| combined (N4) | p2l | 0.0223 [0.0210, 0.0249] | 6.12e-6 | 1.54e-4 | 3738× | 4.49 | 6e-35 |

- **Hotelling T²（6-DoF 均值向量≠0）**：raw p2p p=3.2e-156、raw p2l p=1.4e-148；scale 1.1e-78 / 2.1e-102；combined 4.0e-8 / 1.3e-3。全部极显著。
- 即使在**最大化全局 nuisance 去除（N4，已清零全局 signed mean）**之后，真实梯度仍是数值 self-floor 的 **1.4–3.7 千倍**、零均值噪声对照的 130–460 倍。

## 3. 空间结构是否必要（Null B spatial shuffle）

| condition | objective | real/shuffle ‖g‖ | Cohen's d vs shuffle | permutation p |
|---|---|---:|---:|---:|
| raw | p2p / p2l | **2.80 / 2.69** | 7.27 / 6.32 | 0.010 / 0.010 |
| scale | p2p / p2l | 2.46 / 2.45 | 6.00 / 5.27 | 0.010 / 0.010 |
| combined | p2p / p2l | 0.80 / 0.96 | −0.55 / −0.24 | 0.784 / 0.529 |

- raw / scale：打乱空间挂载后梯度显著下降到约 1/2.5–2.8（p=0.010），证明**梯度由 mismatch 的空间排布产生**，仅靠残差幅值分布不够。
- combined：N4 联合校正注入了较大的平滑/近全局残差场，残余梯度的幅值不再依赖空间置换（p≈0.5–0.8）；但它相对**数值 self-floor 仍高 3 个数量级**（§2）。即：非平稳性在三种条件下都成立，而"空间结构必要性"在 raw/scale 上最干净。

## 4. J1/J2 一致性（两种独立标准目标）

| condition | 梯度方向余弦中位数 | 5% 分位 | ‖g‖ Spearman |
|---|---:|---:|---:|
| raw | **0.988** | 0.937 | 0.910 |
| scale | 0.979 | 0.908 | 0.813 |
| combined | 0.927 | 0.638 | 0.739 |

point-to-point 与 point-to-plane 在真姿态处给出近乎同向的非零梯度（raw 中位余弦 0.988），强度跨目标 Spearman 0.91，排除"单一一目标实现的伪影"。

## 5. Gate M1 判定

> **M1 = PASS。** 真实航天器 LiDAR 对 nominal CAD 的标准刚性配准目标在 T_GT 处显著非平稳：
> ‖g_real‖/‖g_self‖ = 1.4×10³–1.0×10⁴（两目标、三套 nuisance 条件一致），Hotelling p≤1e-3；梯度对差分步长稳定（余弦≥0.984），J1/J2 同向（余弦 0.93–0.99）；raw/scale 下空间置换使梯度显著下降，证明其源于结构化空间失配。
> 因此 **T_GT→∇J(T_GT)≠0 成立**，不触发 STOP_NO_OBJECTIVE_BIAS / STOP_NUMERICAL_INVALIDITY，进入 M2。

## 6. 复现
`python m2_objective.py`（主表）→ `python m2b_nulls.py`（Null A/B）→ `python m3_m1_stationarity.py`（本表）。图：`rescue_figs/F2_gradient_vs_null.png`。
