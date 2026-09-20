> **SUPERSEDED_BY_FINAL_RESCUE_AUDIT** — 本文件结论已被 2026-09-09 Final Rescue Audit 取代。
> 当前唯一权威状态（CURRENT_SOURCE_OF_TRUTH）：`FINAL_GATE.md` = **GO_STANDARD_PAPER_CORE**；本文件仅作历史留档，其 STOP/NOT_TRIGGERED 结论不再生效。

---

> Historical note: old STOP-context assessment — 改以 TOP_JOURNAL_GATE_FINAL.md 为准

---

# TOP JOURNAL ASSESSMENT — Structured Model Mismatch (Phase-0)

**Date:** 2026-09-09
**Verdict context:** STOP_NO_PHENOMENON (K3 endpoint association fails on VI)
**Scoring:** Each dimension 0–5 (5 = strongest/most favorable). Total = 50.

---

## 10-Dimension Assessment

| # | Dimension | Score | Justification |
|---|---|---|---|
| 1 | **Scientific novelty** | 4 | 12组检索+引文链+通用机器人域共28篇文献，0 DIRECT。最危险近邻 Wang 2019 把 MLI 误差定义为 non-systematic（与候选 claim 相反），Renaut smoothed-NDT 仅未验证猜测。核心 claim "structured material mismatch → systematic rigid-pose bias" 在航天+真实LiDAR层未被直接覆盖。扣1分因 GENERAL 线（Laconte ICRA 2019 入射角偏差→定位漂移、Rife 2024 视角几何→配准误差）存在 HIGH_PRIOR_ART_RISK，需显式划界。 |
| 2 | **Theoretical depth potential** | 3 | 物理机理（MLI镜面多径、太阳翼薄结构、signed residual系统性内陷-39.4mm）有理论深度潜力。但当前 Phase-0 未建立 mismatch→endpoint 的因果链（K3失败），理论深度无法从数据中验证。若后续用可收敛baseline建立因果链，可升至4-5。 |
| 3 | **Mechanism clarity** | 2 | 现象层机制较清晰：signed residual 系统性内陷、空间聚集在特定patch（最差/最好=3.69×）、视角依赖（相似aspect Spearman 0.832 vs 不同aspect -0.112）。但因果层机制不清晰：无法证明是 MLI 多径 vs 太阳翼薄结构 vs real-vs-CAD 几何偏差（无 intensity/ring 通道分离物理成因），且无法证明它导致 pose bias（K3/K4失败）。 |
| 4 | **Spacecraft specificity** | 5 | MLI金色包覆镜面多径、太阳翼大平面薄结构、六棱柱+天线稀疏结构、绕X轴对称、非合作翻滚交会场景——全部高度航天器特异。"换车/椅子/工业零件"测试：问题完全改变（汽车无MLI、无太阳翼、无±120°对称、无20m→3m交会走廊）。这是本候选最强的维度。 |
| 5 | **Real-data strength** | 4 | EPOS-Lid 是目前公开唯一真实扫描 LiDAR RPO 基准，GT pose 实测闭合（target→lidar标量首四元数+位置，scan末锚定），target_model.3d 为同源CAD采样（67,870点），6轨迹20m→3m。本轮 VI 实测501帧。扣1分因本轮仅用单轨迹VI，且无 intensity/ring/per-point timestamp 通道。 |
| 6 | **Falsifiability** | 4 | 候选 claim 高度可证伪：K1（空间持久性vs null）、K2（混淆控制）、K3（endpoint关联偏R²）、K4（mismatch特异bias）均有预注册的量化判据。本轮实际运行了全部检验，K3/K4失败即证伪了当前formulation。扣1分因 K3 依赖 baseline 收敛性，而 baseline 选择本身可能影响可证伪性。 |
| 7 | **Method opportunity** | 2 | Phase-0 禁止方法开发，冻结 baseline (FPFH+RANSAC) 在 VI 上 0/101 收敛，方法机会极低。若后续允许开发 tracking 型 baseline（如 NDT tracking、ICP from previous）或利用合成孪生做sim2real分析，方法机会可升至3-4。但当前 Phase-0 框架下，方法是瓶颈而非机会。 |
| 8 | **Reviewer defensibility** | 2 | 当前证据无法支撑顶刊投稿：K3失败意味着不能声称"mismatch影响pose"，K4失败意味着不能声称"systematic bias"。审稿人会立即指出：(a) baseline不收敛如何建立因果？(b) 71.2% R4 如何排除是real-vs-CAD几何偏差而非MLI物理？(c) 单轨迹VI如何排除轨迹特异？若后续 K3/K4 通过且跨轨迹复现，可升至4。 |
| 9 | **Engineering cost** (5=low cost) | 3 | 数据读取成本低（ASCII .3d/.pose，numpy直接load，单轨迹34MB起下），GT契约清晰。但 endpoint baseline 开发成本非平凡：FPFH全局匹配在远距离光滑对称目标上失效，需要 tracking 型方法或更好的初始化策略，这涉及额外工程。本轮因 open3d 无 Python 3.14 wheel 需纯numpy复现FPFH/RANSAC/ICP，增加了工程负担。 |
| 10 | **Dissertation fit** | 3 | 若后续重新触发并通过 K3/K4+跨轨迹验证，可作为博士论文一章（航天器特有LiDAR物理失配对位姿估计的系统性影响），与前两篇（task-calibrated view ranking、shadow方向冻结）形成互补。但当前 STOP 状态下不能直接进入论文写作。扣2分因因果链未闭合、需额外方法开发。 |

**Total: 32 / 50**

---

## Dimension Profile

```
Novelty          ████░░  4
Theory depth     ███░░░  3
Mechanism        ██░░░░  2
Spacecraft spec  █████░  5
Real data        ████░░  4
Falsifiability   ████░░  4
Method opp       ██░░░░  2
Reviewer def     ██░░░░  2
Eng cost (low=5) ███░░░  3
Dissertation     ███░░░  3
                  ─────
Total            32 / 50
```

---

## Interpretation

- **最强维度**：Spacecraft specificity (5)、Scientific novelty (4)、Real-data strength (4)、Falsifiability (4)。候选问题在"是不是航天器特有"和"有没有人做过"上没有问题。
- **最弱维度**：Mechanism clarity (2)、Method opportunity (2)、Reviewer defensibility (2)。全部根源于 K3/K4 失败——因果链未闭合，无法从现象跳到机制和结论。
- **关键瓶颈**：Method opportunity (2) 是当前的核心约束。冻结的 FPFH+RANSAC baseline 在 VI 上完全不收敛，阻断了 endpoint association。这不是科学问题本身的缺陷，而是 Phase-0 实验设计的约束（禁止方法开发、参数冻结）。
- **重开路径**：如果在后续阶段开发可收敛的 tracking 型 baseline（不违反 Phase-0 禁令，因为 Phase-0 已结束），K3/K4 可能通过，Method opportunity 和 Reviewer defensibility 可升至 4，总分可升至 ~40/50，达到 GO_SMALLER_PAPER_ONLY 门槛。若再加上跨轨迹复现和物理成因分离（intensity/ring），可冲击 GO_TOP_JOURNAL_CORE。

---

## Comparison to Innovation Level Thresholds

| Level | Description | Current status | Threshold met? |
|---|---|---|---|
| A | "MLI产生更多residual点" | 远超此层（残差中位64.8mm，85%超采样地板，空间结构稳定） | N/A (已超越) |
| B | "residual比例与pose error相关" | 未达到（K3失败，无法建立相关） | ❌ |
| C | "可重复target-frame结构化mismatch并独立降低rigid registration" | 前半达到（K1+K2），后半未达到（K3） | ❌ (partial) |
| D | "structured physical mismatch→可预测systematic pose bias，多轨迹复现，可principled correction" | 未达到（K3+K4+跨轨迹均未通过） | ❌ |

**当前定位：Level A 与 Level B 之间。** 结构化现象本身存在（超越 Level A），但无法证明与 endpoint 的关联（未达 Level B）。
