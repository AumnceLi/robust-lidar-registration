> **SUPERSEDED_BY_FINAL_RESCUE_AUDIT** — 本文件结论已被 2026-09-09 Final Rescue Audit 取代。
> 当前唯一权威状态（CURRENT_SOURCE_OF_TRUTH）：`FINAL_GATE.md` = **GO_STANDARD_PAPER_CORE**；本文件仅作历史留档，其 STOP/NOT_TRIGGERED 结论不再生效。

---

> Historical note: old NOT_TRIGGERED — 现已进入 IV/V frozen non-circular replication

---

# CROSS-TRAJECTORY DECISION

**Date:** 2026-09-09
**Status:** NOT TRIGGERED

---

## Decision

跨轨迹验证（下载轨迹 IV + V，用 VI 冻结的 patch/statistic/threshold 检验结构复现）**未触发**。

**原因：VI 门禁 K3 失败。**

任务规定："仅当 K1–K3 全过，才允许只下载 IV+V"。K1（空间持久性）和 K2（混淆控制）通过，但 K3（structured mismatch 指标对 endpoint 的独立解释量）失败，因此按纪律不下载 IV/V，不进入跨轨迹验证。

---

## VI 门禁结果回顾

| Gate | 判定 | 关键数值 |
|---|---|---|
| K1 spatial persistence | **PASS** | lag1 patch-rank Spearman = 0.929；vs Null A z = 81.7, p = 0.0099；vs Null B z = 47.6；相似 aspect 0.832，不同 aspect −0.112 |
| K2 confound control | **PASS (weak)** | range/point_count/FOV 在 patch 级仅解释 R² = 0.013；冻结 patch 固定效应偏 R² = 0.133, 95% CI [0.124, 0.148]；最差/最好 patch residual 比 = 3.69× |
| K3 endpoint association | **FAIL** | 冻结 baseline (FPFH+RANSAC+ICP) **0/101 收敛**；GT 下 FPFH 最近特征匹配一致率仅 1.2%；mismatch 块偏 R² = 0.043/0.030；所有单个回归系数 95% CI 含 0；仅事后 ICP-locked 子集 (n=36) 偏 R² 升至 0.072/0.112（事后探索，非预注册） |
| K4 systematic bias | **FAIL** | baseline 确有显著系统 bias（Hotelling p < 1e-3，旋转误差轴半程余弦 0.949），但高/低 mismatch 组 bias 幅值几乎相同（0.284 vs 0.273 m），平移方向半程余弦 0.527 < 0.70——bias 不具 mismatch 特异性 |

---

## K3 失败的根因分析

K3 失败不是因为 structured mismatch 不存在（K1+K2 证明它存在且非随机），而是因为**冻结 baseline 在 VI 上完全无法收敛**，导致无法建立 mismatch → endpoint 的因果关联：

1. **数据固有困难**：VI 距离 8.75–14.79 m，目标在该距离下扫描点稀疏（~9000–10000 点/scan），目标表面光滑（六棱柱主体+MLI包覆），绕 X 轴 ±120° 对称——FPFH 全局特征匹配在 GT 下一致率仅 1.2%，RANSAC 无法找到有效全局对应。
2. **与 EPOS 论文一致**：EPOS-Lid 论文本身报告全局初始化方法在远距离失效，论文协议使用 NDT tracking（需初始位姿）而非纯全局初始化。
3. **实现正确性已验证**：用"目标模型刚性自复制"测试 FPFH/RANSAC 实现，匹配一致率 94%、姿态误差 0°——证明实现无 bug，真实扫描上的失败是数据属性。
4. **参数冻结不可调**：任务规定 baseline 参数全程冻结不调参，因此不能通过调整 voxel_size/RANSAC 阈值/ICP 阈值来挽救。
5. **禁止方法开发**：任务禁止开发新方法（包括 tracking 型 baseline、learned initialization、robust loss 等），因此不能切换到 EPOS 论文使用的 NDT tracking。

---

## 如果重新触发跨轨迹验证，需要满足的条件

以下条件**全部满足**后，可重新考虑下载 IV+V 做跨轨迹验证：

1. **可收敛的 endpoint baseline**：使用 tracking 型方法（如 EPOS 论文的 NDT tracking，或 ICP from previous-frame pose）替代纯全局 FPFH+RANSAC，确保在 VI 上收敛率 > 50%。这需要新方法开发（Phase-0 禁止），应在后续阶段进行。
2. **K3 在 VI 上通过**：用可收敛 baseline 重新计算 endpoint association，确认 structured mismatch 指标在控制 range/tumble/point_count 后仍有独立解释量（偏 R² 显著，系数 CI 不含 0）。
3. **K4 在 VI 上通过**（最好满足）：确认高 mismatch 组的 bias 方向/幅值与低 mismatch 组有统计显著差异，且方向跨帧可重复。
4. **VI 冻结的 patch/statistic/threshold 不变**：跨轨迹验证必须使用 VI 上一次性定义的 24 个 patch、残差统计量、R1-R4 阈值，禁止在 IV/V 上重调。

**注意**：即使上述条件满足，跨轨迹验证的目的是检验 VI-defined structure → IV/V 的方向/effect size/CI/轨迹异质性。如果 IV/V 上不复现，则判 STOP_SINGLE_TRAJECTORY_ARTIFACT。

---

## 诚实声明

- R3 (FOV truncation) 在 VI 上为空集（最近 8.75m 处目标角半径仅 ~6.5° < 19.2° FOV 半角），因此 R3 与 R4 的可分性**无法在 VI 上实证检验**。近距离轨迹（如 I/II 的 3–5m 段）可能存在 R3，但未下载。
- baseline 抽样为每 5 帧等距分层抽样 n=101（residual/null 分析用全部 501 帧），抽样策略已写入 VI_MINIMAL_PHENOMENON.md。
- open3d 对 Python 3.14 无 wheel，FPFH/RANSAC/ICP 按 Rusu 2009 / Besl-McKay 在 numpy/scipy 忠实复现，参数按契约冻结，并用自复制测试验证实现正确。
