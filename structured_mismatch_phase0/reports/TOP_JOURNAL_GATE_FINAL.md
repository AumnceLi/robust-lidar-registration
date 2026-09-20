FINAL: PARTIAL_EXTERNAL_REPLICATION
PRIMARY_REASON_CODE: V_ZERO_IN_SUPPORT_RANGE_NONOVERLAP — V range 2.8–7.8 m 与 VI 8.75–14.8 m 无重叠，冻结 τ_support=0.440 下 V confirmatory IN_SUPPORT=0（TJ1-E 无法按预注册规则判定）；IV confirmatory 强 PASS，V 仅能作 out-of-support 外推（强但不可计为 confirmatory）；冻结阈值未回改。

# TOP_JOURNAL_GATE_FINAL.md — IV/V 冻结非循环复现终判

- 日期：2026-09-09。执行顺序严格 `VI non-circular → IV → V`；predictor 在打开 IV/V 前冻结（`VI_ONLY_PREDICTOR_FROZEN.npz` SHA256 `8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe`）；IV/V 当前帧 residual 从未进入主预测器（非循环）。新数据仅 IV+V，合计 341,867,550 B=326 MiB<400 MB。IV、V 全程分别报告。

## 1. TJ1 逐项（A–F）

| 门 | 内容 | 结果 | 关键数值 |
|---|---|---|---|
| TJ1-A | VI 非循环 NC0 | **PASS** | Protocol-A raw/p2p 中位 cos 0.940、block-CI[0.929,0.948]、100% 正向、向量置换 p=0.0005；Protocol-B 整 orientation-block 留出同为 0.940；k\*=16 对网格稳健 |
| TJ1-B | IV objective stationarity | **PASS** | ‖g_real‖/‖g_self‖=5.9×10³–1.3×10⁴，Hotelling p≤3e-35，raw 梯度方向集中 0.86 |
| TJ1-C | V objective stationarity | **PASS** | ratio 5.5×10³–1.3×10⁴，Hotelling p≤1.2e-280，p2p on-bound=0 |
| TJ1-D | VI-only predictor→IV 方向 | **PASS（confirmatory, IN_SUPPORT n=156）** | p2p cos 0.841 CI[0.811,0.866]、p2l 0.982 CI[0.975,0.987]、100% 正向、置换 p=0.0005、−D1 0.778 |
| TJ1-E | VI-only predictor→V 方向 | **CONFIRMATORY 不可评估（IN_SUPPORT n=0）**；外推强 | V 全部 OUT：p2p 0.902 CI[0.887,0.914]、p2l 0.891、91–93% 正向、p=0.0005、−D1 0.828；按 §11 仅为外推附录 |
| TJ1-F | 冻结 patch/influence 方向性复现 | **部分** | residual profile Spearman 0.43(IV)/0.71(V) 复现；influence ranking 0.05(IV IN)/0.44(V) 混合 |

**A–F 未全部满足**（E 的 confirmatory 集为空，F 部分）→ **不满足 GO_TOP_JOURNAL_MECHANISM_CANDIDATE**。
同时并非"现象不复现"（不触发 STOP_SINGLE_TRAJECTORY_ARTIFACT），也非"predictor 不 transfer"（不触发 GO_STANDARD_PAPER_ONLY）：IV 干净 confirmatory 复现、V 经验上强复现但落在预注册支持域外。故取 **PARTIAL_EXTERNAL_REPLICATION**。

## 2. Level-4（幅度定量预测）：不支持
唯一 VI 标量 α_VI=0.0200 在 IV slope=11.7、V slope=0.019（差 ~600×），幅度 Spearman −0.15/+0.18 均<0.4。方向跨三轨迹一致强，幅度尺度跨轨迹不稳定（详见 QUADRATIC_TRANSFER）。

## 3. 核心科学结论（本轮唯一允许的 claim）
1. **机制在第二条轨迹上得到 confirmatory 非循环验证**：只凭 VI 学到的 view-conditioned 失配模板 + 未见帧的 GT 观测几何，就能在 IV 的 VI-支持域内以中位 cos 0.84/0.98、100% 正向、p=0.0005 预测标准 rigid-registration 目标的 bias 方向，且不用该帧任何残差。这排除了"VI 自循环/过拟合"解释。
2. **失配机制主要由观测方向条件化**：V 观测方向与 VI 近乎重合（0.33°）而 range 完全不同，仍达 0.90 方向迁移；反之 IV 中 range 重叠但方向未覆盖的帧只有机会水平（0.14/0.05）。支持域对照（IN 0.84 vs OUT 0.14）本身就是机制特异性的内部证据。
3. **客观存在的覆盖缺口**：VI 训练域（8.75–14.8 m）不含 V 的近距离接近段（2.8–7.8 m），冻结的联合(range,orientation)支持域因此对 V 无 confirmatory 样本。这是**实验设计/数据覆盖**限制，不是机制被证伪；按纪律不回改 τ。

## 4. 弱点（如实记录，不得过度声称）
- V 无 confirmatory in-support 帧，其强结果只能标 extrapolation；IV IN_SUPPORT 仅 156/2428。
- patch-influence 排名迁移不一致（IV IN 0.05，子集仅 32 帧噪声大）；帧内残差–梯度关系外部（0.27/0.13）弱于 VI（0.53）。
- 幅度不可迁移（Level-4 失败）；p2l 在 VI 内部方向本就弱于 p2p。
- IV/V 扫描有时序相关，结论已用 L=5 moving-block bootstrap，未用 pointwise。

## 5. 升级到 GO_TOP 的合规路径（不在本轮执行）
- **唯一**补证方式：取得一条 **range 与 VI（8.75–14.8 m）重叠**的独立轨迹做 confirmatory in-support 复现；或在**新一轮冻结**中先扩展 VI/训练覆盖到近距离（含 2.8–7.8 m）再对 V 做 out-of-fold——二者都必须重新冻结 predictor 与 τ，禁止用本轮 IV/V 回拟合。
- 幅度方向：correspondence-updated curvature / 隐式微分，属后续方法阶段；本轮仍禁止新 ICP、robust loss、NDT、neural、learned correction、bad-patch filtering、tracking。

## 6. 交付物索引
- 报告：STATUS_LEDGER_FINAL.md、FROZEN_REPLICATION_MANIFEST.yaml、VI_NONCIRCULAR_VALIDATION.md、IV_REPLICATION.md、V_REPLICATION.md、EXTERNAL_NONCIRCULAR_PREDICTION.md、PATCH_TRANSFER.md、QUADRATIC_TRANSFER.md（本文件）。
- 机器表：vi_noncircular.csv、iv_prediction.csv、v_prediction.csv、patch_transfer.csv、trajectory_summary.csv。
- 冻结/结果数据：VI_ONLY_PREDICTOR_FROZEN.npz(.json)、cache/ext/ext_objective_{iv,v}.npz、ext_predict_{iv,v}.npz、cache/rescue/ext_stats_*.json。
