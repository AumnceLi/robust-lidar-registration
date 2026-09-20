> **SUPERSEDED_BY_FINAL_RESCUE_AUDIT** — 本文件结论已被 2026-09-09 Final Rescue Audit 取代。
> 当前唯一权威状态（CURRENT_SOURCE_OF_TRUTH）：`FINAL_GATE.md` = **GO_STANDARD_PAPER_CORE**；本文件仅作历史留档，其 STOP/NOT_TRIGGERED 结论不再生效。

---

> Historical note: old STOP_NO_PHENOMENON (K3 FPFH+RANSAC baseline 0/101) — 已被 M1–M4 机制证据取代

---

FINAL: STOP_NO_PHENOMENON
PRIMARY_REASON_CODE: STRUCTURED_MISMATCH_EXISTS_BUT_ENDPOINT_CAUSAL_CHAIN_NOT_CLOSED_K3_FAILS_BASELINE_ZERO_CONVERGENCE

---

## G1 / G2 / G3 对照

### G1 Novelty — PASS

- 12组指定检索 + EPOS-Lid论文引文链（前向/后向各一层）+ 通用机器人域 kill，共筛出 **28 篇真正相关文献**。
- 分级：**0 DIRECT / 6 GENERAL / 22 ADJACENT**。
- 无任何一篇持有"航天+真实LiDAR+结构化材料失配→rigid pose系统偏差"的相同 formulation。
- 最危险近邻均被降级：
  - **Wang et al. 2019 IEEE Access**（MLI包覆非合作目标位姿估计）：标题三要素齐全，但摘要明确把 MLI 误差定义为 **"non-systematic errors"**，用滤波+trimmed ICP 剔除——误差哲学与候选 claim 相反；且用 ToF 相机、帧间配准。
  - **Renaut et al. 2023 smoothed-NDT**（EPOS-Lid直接前作）：Discussion 仅用一句"位置误差可能源于标定误差与 CAD-mockup 不一致"的**未验证猜测**，此后三年 DLR 自己的 TAES 2025 / Acta 2025 / EPOS-Lid 均未展开。
- HIGH_PRIOR_ART_RISK（非kill）：Laconte ICRA 2019（入射角相关测距偏差→可预测定位漂移）+ Rife NAVIGATION 2024（视角几何→配准系统误差）。claim ④⑦⑧ 的一般机制层判 PARTIAL，论文必须从物理机理、估计对象、偏差坐标系三点显式划界。
- 8行 claim 矩阵：OPEN = ①③⑥ + ④航天器层；PARTIAL = ②④⑤⑦⑧；无 COVERED。
- 详见 `reports/PRIOR_ART_MATRIX.md`、`reports/CLAIM_KILL_TABLE.md`。

### G2 Identifiability — PARTIAL PASS

- 坐标变换已从 README 原文验证：`.pose` 给出 target→lidar 旋转（标量首四元数 q_s,q_x,q_y,q_z）+ target 在 lidar 系位置；GT 对齐 P_target = R^T(P_lidar - t)。pose 锚定 scan 末时刻。
- R1-R4 可分性：
  - **R1 sampling**：模型自NN中位 8.11mm，R1界 16.2mm；15.2% 点归为 R1。可分。
  - **R2 occlusion/partial visibility**：法向背向lidar判定；13.3% 点归为 R2。可分（但法向从点云估计，有不确定性）。
  - **R3 FOV truncation**：**VI 上为空集**（最近8.75m处目标角半径仅~6.5° < 19.2° FOV半角）。R3 与 R4 的可分性**无法在 VI 上实证检验**。
  - **R4 candidate physical mismatch**：控制 R1-R3 后仍残留且空间聚集；71.2% 点归为 R4。与 R1/R2 可分，与 R3 不可分（R3为空）。
- 可辨识性边界：R4 内部无法区分 MLI镜面多径 vs 太阳翼薄结构 vs real-vs-CAD几何偏差（无 intensity/ring 通道）。signed residual 系统性内陷 -39.4mm 且随距离增大（r=-0.60），提示真实物理效应而非随机噪声。
- 详见 `reports/IDENTIFIABILITY_AUDIT.md`。

### G3 Phenomenon — FAIL

G3 要求同时满足：(a) residual 非随机、空间结构稳定、跨 frame/aspect 可重复；(b) 与 endpoint degradation 有统计关系。(a) 通过，(b) 失败。

---

## K1 – K4 门禁判定

### K1 spatial persistence — PASS ✅

- lag1 patch-rank Spearman = **0.929**（24个冻结patch，501帧）
- vs Null A（iid空间打乱，N=100）：z = **81.7**，percentile > 99th，p = 0.0099
- vs Null B（range-matched重排，N=100）：z = **47.6**，percentile > 99th
- 相似 aspect：Spearman = 0.832；不同 aspect：Spearman = −0.112（视角依赖，符合物理预期）
- 最差 patch (#12) / 最好 patch (#3) 中位残差比 = **3.69×**
- 结论：空间结构极其稳定，远超两个 null 模型，effect size 有实际意义。

### K2 confound control — PASS (weak) ✅

- range / point_count / FOV 在 patch 级仅解释 R² = **0.013**（1.3%）
- 加入冻结 patch 固定效应后偏 R² = **0.133**，95% CI [0.124, 0.148]
- patch 身份解释的变异远超混淆变量
- 结论：异常不能被 range/point_count/FOV 完全解释。但偏 R²=0.133 意味着仍有 ~87% 变异未被 patch 身份解释，效应偏弱。

### K3 endpoint association — FAIL ❌

- 冻结 baseline（FPFH + RANSAC + ICP，参数全程冻结）：**0/101 收敛**（RANSAC fitness > 0.3 且 ICP fitness > 0.5 的帧数为0）
- GT 下 FPFH 最近特征匹配一致率仅 **1.2%**（光滑对称目标+cm级real-vs-CAD偏差，全局匹配固有困难）
- 平移误差：0/101 < 0.1m；姿态误差中位 **62.5°**
- mismatch 块（excess_fraction + spatial_persistence + r4_fraction）偏 R² = 0.043（平移）/ 0.030（姿态）
- **所有单个回归系数 95% CI 含 0**
- 仅事后 ICP-locked 子集（n=36，ICP 从 GT 附近启动——注意这违反"GT不泄漏给初始化"原则，仅作探索）偏 R² 升至 0.072/0.112
- 根因：FPFH 全局初始化在 VI 远距离（8.75–14.79m）光滑对称目标上完全失败，与 EPOS 论文"全局法在远距离失效"一致。实现正确性已用"模型刚性自复制"验证（94%匹配、0°误差），真实扫描上的失败是数据属性。
- 结论：无法建立 structured mismatch → endpoint degradation 的因果关联。K3 失败。

### K4 systematic bias (best-to-have) — FAIL ❌

- baseline 确有显著系统 bias：高 mismatch 组 Hotelling p < 1e-3，旋转误差轴半程余弦 0.949（方向高度一致）
- 但**不具 mismatch 特异性**：
  - 高 mismatch 组 bias 幅值 = 0.284m；低 mismatch 组 = 0.273m（几乎相同）
  - 平移 bias 方向半程余弦 = 0.527 < 0.70（方向跨帧不一致）
  - 高/低 mismatch 组的 bias 方向无统计显著差异
- 结论：系统 bias 存在，但它是 baseline 自身的系统性失败（全局匹配落入错误局部极小），而非由 structured mismatch 特异诱发。K4 失败。

---

## Level A – D 创新分级判定

| Level | Description | Status |
|---|---|---|
| A | "MLI产生更多residual点" | **已超越**：残差中位64.8mm（8×采样地板），85%点超R1界，空间结构稳定 |
| B | "residual比例与pose error相关" | **未达到**：K3失败，无法建立相关 |
| C | "可重复target-frame结构化mismatch并独立降低rigid registration" | **前半达到，后半未达到**：K1+K2证明结构化mismatch可重复，但K3无法证明独立降低registration |
| D | "structured physical mismatch→可预测systematic pose bias，多轨迹复现，可principled correction" | **未达到**：K3+K4+跨轨迹均未通过 |

**当前定位：Level A 与 Level B 之间。** 结构化现象本身真实存在，但因果链到 endpoint 未闭合。

---

## 10维评分（详见 TOP_JOURNAL_ASSESSMENT.md）

| Dimension | Score |
|---|---|
| Scientific novelty | 4/5 |
| Theoretical depth potential | 3/5 |
| Mechanism clarity | 2/5 |
| Spacecraft specificity | 5/5 |
| Real-data strength | 4/5 |
| Falsifiability | 4/5 |
| Method opportunity | 2/5 |
| Reviewer defensibility | 2/5 |
| Engineering cost (5=low) | 3/5 |
| Dissertation fit | 3/5 |
| **Total** | **32/50** |

---

## 下一步：STOP，不自动进入下一阶段

### 为什么 STOP

1. **G3 失败**：K3（endpoint association）和 K4（mismatch-specific bias）均失败，无法建立"structured mismatch → endpoint degradation"的因果链。这是候选科学问题的核心 claim，未经验证不能继续。
2. **K3 失败的根因是 baseline 不收敛**，不是现象不存在。但 Phase-0 纪律禁止方法开发、禁止调参、禁止用 GT 初始化，因此在 Phase-0 框架内无法挽救。
3. **未触发跨轨迹验证**：K1-K3 未全过，按纪律不下载 IV/V。
4. **不靠换名字/换metric/换baseline/多画曲线制造虚假创新**：现象层（K1+K2）的结果是真实的，但不足以支撑 Level C/D 的论文主张。

### 如果未来重新考虑，需要的最小条件

以下条件**全部满足**后，可重新评估此候选方向（作为新任务，不是 Phase-0 的延续）：

1. **可收敛的 tracking 型 baseline**：开发或使用 EPOS 论文的 NDT tracking（需初始位姿，从第一帧 GT 或手动给定启动），或 ICP from previous-frame pose，确保在 VI 上收敛率 > 50%。这是方法开发，Phase-0 禁止，但后续阶段允许。
2. **K3 在 VI 上通过**：用可收敛 baseline 重新计算 endpoint association，确认 mismatch 指标在控制 range/tumble/point_count 后偏 R² 显著、系数 CI 不含 0。
3. **K4 在 VI 上通过**（最好满足）：确认高 mismatch 组的 bias 方向/幅值与低 mismatch 组有统计显著差异，且方向跨帧可重复。
4. **跨轨迹复现**：下载 IV+V（单轨迹 ~190MB/~152MB），用 VI 冻结的 patch/statistic/threshold 检验结构复现。若不复现 → STOP_SINGLE_TRAJECTORY_ARTIFACT。
5. **物理成因分离**（可选但强烈推荐）：若能获取 intensity/ring 通道（EPOS-Lid 原始数据可能有，但公开 .3d 仅 xyz），或用合成孪生做材料消融，分离 MLI多径 vs 太阳翼薄结构 vs real-vs-CAD。

### 估计重新评估的最小成本

- tracking baseline 开发：1-2周（NDT或ICP tracking，Python/C++）
- VI 上 K3/K4 重跑：1-2天（数据已在本地）
- IV+V 下载与跨轨迹验证：~350MB 下载，2-3天
- 总计：~3周，<1GB 下载

### 替代方向建议

如果此方向最终无法通过 K3/K4，EPOS-Lid 资产仍可支撑其他科学问题（详见上一轮 `POSSIBLE_UNUSED_RELATIONS.md`）：
- P1：距离分层位姿/几何误差包络（无需 baseline 收敛，用 GT 直接分析可观测性边界）
- P2：主动传感器 sim2real 间隙分解（用合成孪生 vs 真实扫描）
- P3：扫描密度/自适应帧率与端点稳定性交互
这些方向不依赖"mismatch→endpoint"因果链，可能更易在 EPOS-Lid 上闭合。

---

## 实测下载量与执行合规

- **本轮零新数据下载**：仅复用本地已有的 VI zip（33.9MB，501×2文件）、target_model.3d（1.5MB）、README。
- open3d 对 Python 3.14 无 wheel，FPFH/RANSAC/ICP 按 Rusu 2009 / Besl-McKay 在 numpy/scipy 忠实复现，参数按契约冻结，并用"模型刚性自复制"验证实现正确（94%匹配、0°误差）。
- residual/null 分析用全部 501 帧；baseline 因纯 Python RANSAC 按任务许可做每5帧等距分层抽样 n=101（0.86s/帧）。
- GT 仅用于 residual 对齐与 endpoint 打分，未泄漏给 baseline 初始化/调参。
- 全部 9 个 Python 脚本保存到 `scripts/`，可复现。
- 全部结论区分 verified-file/computed 与 paper-claim。

---

## 交付物清单

### reports/
1. `PRIOR_ART_MATRIX.md` — 28篇文献分级+8行claim矩阵+总体新颖性判定
2. `CLAIM_KILL_TABLE.md` — 8条claim+子claim逐条kill评估
3. `IDENTIFIABILITY_AUDIT.md` — R1-R4可分性判决+patch冻结+可辨识性边界
4. `VI_MINIMAL_PHENOMENON.md` — 最小现象全数值报告+K1-K4门禁+STOP判定
5. `CROSS_TRAJECTORY_DECISION.md` — 跨轨迹验证未触发说明+重开条件
6. `TOP_JOURNAL_ASSESSMENT.md` — 10维评分+创新分级定位
7. `PHASE0_VERDICT.md` — 本文件

### results/
8. `residual_per_scan.csv` — 501帧残差统计+R1-R4分类
9. `patch_persistence.csv` — 501×24冻结patch统计（12,024行）
10. `null_tests.csv` — Null A/B各100次置换检验
11. `baseline_endpoints.csv` — FPFH+RANSAC+ICP，101帧分层抽样
12. `bias_variance.csv` — 高/低mismatch组bias向量与旋转轴
13. `confound_control.csv` — 混淆控制回归+patch固定效应偏R²
14. `endpoint_association.csv` — endpoint-mismatch回归系数与CI
15. `endpoint_association_robust.csv` — ICP-locked子集稳健性
16. `patch_definition.csv` — 一次性冻结的24 patch定义
17. `figures/fig1_residual_map.png` — target-frame残差地图（双视角）
18. `figures/fig1b_patch_profile.png` — 24个冻结patch残差剖面
19. `figures/fig2_null_persistence.png` — 真实持久性 vs Null A/B
20. `figures/fig3_error_vs_mismatch.png` — endpoint error vs mismatch（range分层）
21. `figures/fig4_bias_vectors.png` — bias向量与旋转误差轴分布
22. `figures/fig5_classification.png` — R1-R4沿轨迹占比+残差分布

### scripts/
23. `s0_common.py` — IO/变换/PCA法向/FPFH/RANSAC/ICP公共库
24. `s1_residuals.py` — GT对齐残差+R1-R4分类
25. `s3_patches.py` — patch冻结与聚合
26. `s4_null_tests.py` — Null A/B置换检验
27. `s5_confound.py` — 混淆控制回归
28. `s6_baseline.py` — 冻结baseline (FPFH+RANSAC+ICP)
29. `s7_endpoint_bias.py` — endpoint关联+bias/variance
30. `s8_figures.py` — 全部绘图
31. `s9_summary.py` — 数值聚合
