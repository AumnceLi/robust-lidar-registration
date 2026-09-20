# FINAL_GATE.md — Structured Spacecraft LiDAR Model-Mismatch，VI Final Rescue Audit 终判

- 日期：2026-09-09　数据：仅 VI（501 scans），0 新下载 / 0 GPU / 0 renderer / 0 新 GT。
- 唯一科学问题：真实 spacecraft LiDAR 与 nominal CAD 的**结构化失配**，是否使标准 rigid-registration 目标在**已知 GT pose 处非平稳**（∇J(T_GT)≠0），并把局部极小系统性推离 GT、且该位移可由失配场预测？

---

## 1. 终判（七选一）

# ✅ GO_STANDARD_PAPER_CORE

**VI 三个硬 gate（M1/M2/M3）全部 PASS，方向机制 M4a 与 patch 机制 M4b 均成立，全局 nuisance gate 通过，数值有效，prior-art 无 DIRECT。证据链达到 Level 3（结构化失配 → 目标梯度 → 可预测方向的 6-DoF 局部极小偏置），构成一篇机制核心的独立论文。**

**未选 GO_TOP_JOURNAL_MECHANISM_CORE 的唯一原因**：Level-4 要求 −H⁻¹g **定量精确**预测极小位移；本轮只在**方向**上达到（p2p 余弦 0.96→0.998），**幅度**在 raw 下系统性过估（slope≈0.02、R²≤0），仅在最大化 nuisance 去除后部分可标定（slope 0.29、R²=0.35），且 point-to-plane 二次预测失效。因此 VI 单轨迹尚不足以顶刊，需 IV/V 外部复现 + 幅度标定补强（见 §6）。

**按 §21，VI 全 gate 已过 → 允许进入 Trajectory IV/V 外部复现（下载 <400 MB，协议全部冻结，只做 replication，不重调）。**

---

## 2. Gate 记分卡

| 关卡 | 结论 | 关键证据 | 报告 |
|---|---|---|---|
| Prior-art（§2） | **0 DIRECT** | Choate&Rife 占"discrepancy 场/可视化/scan-match 诊断"，列为 GENERAL(G7)；无人做 objective-gradient / Hessian / 6-DoF 极小偏置机制 | PRIOR_ART_UPDATE.md |
| Global nuisance（§5–6） | **PASS（不触发 STOP_GLOBAL_NUISANCE）** | 最简全局模型只消~30% 局部 spread，lag1/sim-aspect 持续性几乎不动；N4 清零全局均值却把 patch spread 放大 2.4×（非物理抵消）→ 结构非全局 | GLOBAL_NUISANCE_AUDIT.md |
| **M1 GT 平稳性** | **PASS（强）** | ‖g_real‖/‖g_self‖=1.4×10³–1.0×10⁴，Hotelling p≤1e-3；FD 三档步长方向余弦≥0.984；J1/J2 梯度余弦 0.93–0.99；raw/scale 空间置换使梯度降 2.5–2.8× | OBJECTIVE_STATIONARITY.md |
| **M2 局部极小位移** | **PASS（强）** | raw 平均平移 [+53,−0.7,−0.4]mm、中位 160.8mm、符号一致 0.99、旋转轴集中 0.82、Hotelling p≈0；**self-floor=0.0000mm**；ICP↔L-BFGS 余弦 0.93–1.00、触界 0；combined 后仍残留 58–64mm | LOCAL_OPTIMUM_BIAS.md |
| **M3 失配特异性** | **PASS（强）** | 控制 range/点数/aspect/时间/转速/nuisance 后，方向投影 partial R²=0.90(raw)/0.45–0.48(combined)，bootstrap CI 不含 0，range-bin 置换 p=0.001；Null-D high>low p=6.5e-5 | MISMATCH_SPECIFICITY.md |
| **M4a 方向机制** | **PASS** | cos(D1,Δt)=−0.92/−0.93(raw,p=.0005)、D2 +0.88/+0.90；combined D1 仍 −0.62/−0.66；旋转 combined 后 −0.39/−0.55 | PATCH_INFLUENCE.md |
| **M4b patch 梯度机制** | **PASS（within-scan）** | 梯度分解闭合误差 4.9e-15；逐 scan 残差–‖g_j‖ Spearman 0.53，CI[0.28,0.74]，**100% scan 为正**；最强 patch 影响度 2.5× 中位 | PATCH_INFLUENCE.md |
| 二次预测 −H⁻¹g（§16） | **方向 PASS / 幅度不足** | p2p 方向余弦 0.959→0.998、正向 95–99%；幅度 slope 0.02(raw)→0.29(combined)、R² 0.35(combined)；p2l 失效 | QUADRATIC_BIAS_PREDICTION.md |

无 STOP_NUMERICAL_INVALIDITY（FD 稳定、分解机器精度、Hessian 全部正定，eigmin>0）；无 STOP_NO_OBJECTIVE_BIAS；无 STOP_NO_MISMATCH_SPECIFICITY。

## 3. 成功等级（§19）定位
- Level 0（仅结构化残差）：早期已达，非本轮贡献。
- Level 1（g(T_GT)≠0）：达到，M1。
- Level 2（g≠0 且 T*≠T_GT、有系统方向）：达到，M1+M2。
- **Level 3（structured mismatch → g → δξ*，控制 nuisance 后仍成立）：达到——M1+M2+M3+M4，这是本轮落点，对应"较强独立小论文"。**
- Level 4（−H⁻¹g 精确预测 + patch 物理机制 → TOP-JOURNAL）：**部分达到**——方向预测与 patch 机制成立，精确幅度预测未达。

## 4. 唯一允许的核心 claim（novelty 边界）
> **Object-level spacecraft nominal-model mismatch induces a non-stationary rigid 6-DoF registration objective at the true pose: ∇J(T_GT)≠0, the nearest local minimum is displaced from T_GT along a direction predicted by the structured mismatch field (signed residual moment / per-patch gradient), and this association survives removal of global range/SE(3)/scale nuisance.**

禁止主张（已被 Choate&Rife 等占据）：首次发现结构化残差；首次把 LiDAR discrepancy 映射为空间场；首次可视化局部 mismatch；场诊断 scan-matching。symmetry(±120°) 仅用于误差表示，不作为贡献。本轮不提出任何 correction / robust / NDT / neural 方法。

## 5. 必须如实写明的弱点（决定不直升顶刊）
1. **二次幅度过估**：raw 下 −H⁻¹g 幅度 slope≈0.02（GT 处 NN 曲率被低估，移动后对应重连、曲率增大），精确幅度只在 combined 后部分成立（R²=0.35）。
2. **point-to-plane 较弱**：二次预测 cos 仅 0.32–0.41、Hessian 近奇异（切向欠定）；p2l 只作为与 p2p 同向的辅助目标。
3. **combined 的 Null-B 空间置换对比≈1（0.80–0.96）**：最大化全局校正注入平滑残差后，残余梯度幅值不再依赖空间置换（但仍超 self-floor 三个数量级、Hotelling 显著）。
4. **Null-D 量级差仅 3.7 mm**：失配主要决定**方向/逐 scan 变异**，共模偏置量级由整体内缩主导。
5. **patch 影响度与冻结全局 profile 呈负相关（ρ=−0.46,p=.023）**：机制是逐帧几何决定，不存在固定"最坏 patch 地图"。
6. 单轨迹（VI）：外部轨迹复现尚未做。

## 6. 下一步（冻结协议下）
1. **允许下载 IV/V（<400 MB）**，24 patches、nuisance 形式、两目标、扰动尺度、g/H、失配特征、回归、阈值**全部冻结**，只做 external trajectory replication（§22 四项：梯度方向、极小位移、失配特异效应、predicted-vs-measured 关系）。若 IV/V 任一核心项不复现 → STOP_SINGLE_TRAJECTORY_ARTIFACT，方向冻结。
2. 顶刊升级条件（不在本轮做）：在 IV/V 上复现方向链，并把二次模型从"GT 处固定 H"推进为随对应关系更新的曲率/隐式微分，使幅度 slope→1、R² 显著提升；之后才进入 bias-aware / structured-mismatch-aware objective 的方法阶段（§23）。

## 7. 交付物清单
A PRIOR_ART_UPDATE.md｜B GLOBAL_NUISANCE_AUDIT.md｜C OBJECTIVE_STATIONARITY.md｜D LOCAL_OPTIMUM_BIAS.md｜E MISMATCH_SPECIFICITY.md｜F PATCH_INFLUENCE.md｜G QUADRATIC_BIAS_PREDICTION.md｜H FINAL_GATE.md（本文件）；图 reports/rescue_figs/F1–F7；数值 cache/rescue/*.json|*.csv|objective_main.npz|nullA/nullB。
