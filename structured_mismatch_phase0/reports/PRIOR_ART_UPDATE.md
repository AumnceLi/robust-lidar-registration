# PRIOR-ART UPDATE — Choate & Rife Vector-Field Paper + Re-classification

- 更新日期：2026-09-09（Asia/Shanghai）
- 触发：Final Rescue Audit §2 强制要求，在任何主实验前补入并单独评估
  **Choate, D. & Rife, J. "Characterizing Lidar Point-Cloud Adversities Using a Vector Field Visualization."**
- 检索/获取：general_search 命中 → arXiv abs + PDF 正文实际抓取阅读（verified-actual-page）。
- 关联文档：`reports/PRIOR_ART_MATRIX.md`（28 篇，0 DIRECT / 6 GENERAL / 22 ADJACENT），本文件是其**增量补丁 + 重新判定**，不推翻原矩阵的检索记录。

---

## 1. 新增文献书目（verified）

| 字段 | 内容 |
|---|---|
| 标题 | Characterizing Lidar Point-Cloud Adversities Using a Vector Field Visualization |
| 作者 / 单位 | Daniel Choate, Jason Rife（Tufts University；与 Rife & McDermott 2024 同组） |
| 出处 | Proc. 37th Int. Technical Meeting of the Satellite Division, **ION GNSS+ 2024**, Sept. 2024；preprint arXiv:2510.13619v1（2025-10-15，cs.RO） |
| DOI | 会议版 10.33012/2024.19864；preprint 10.48550/arXiv.2510.13619 |
| URL | https://arxiv.org/abs/2510.13619 ；https://arxiv.org/pdf/2510.13619 |
| 获取状态 | **verified-actual-page**（摘要 + §1 Introduction + §2 Methodology + Fig.1/2/16/17 正文） |

### 1.1 它实际做了什么（按原文，不夸大）
1. 输入两片点云（scan-to-scan 或 scan-to-HD-map），**先用 truth/GT（载波相位差分 GNSS/INS）对齐**；GT 不可得时才退而用 NDT/ICP/ICET 对齐。
2. 做**球坐标体素化**（voxel over {r,θ,φ}），每个 voxel 内分别求两片云的均值点，逐 voxel 做差得到离散**discrepancy vector {U,V,W}（式 1）**，把全体 voxel 的差向量画成**离散矢量场**。
3. **human-in-the-loop、offline、labor-intensive**：人观察矢量场图案 → 假设一个 adversity 机制 → 提一条 pruning/transformation 规则去除 → 重算矢量场 → 迭代，直到只剩"小而方向随机"的矢量。
4. 用 Fig.2 三个 3×3 示意区分：(左) 全场同向 = bad registration，整体平移即可消；(中) 上下反向 = **任何平移/旋转都消不掉的 systematic error（举例为 calibration scale bias）**；(右) 小而随机 = 终止。
5. 两个 proof-of-concept：一个仿真、一个自动驾驶野外实验；处理 FOV、shadow/运动物体、径向内外伸缩等 adversity；野外场矢量量级到 **8–11 m**（城市驾驶尺度）。动机段明确：面向 **automated driving localization**。

### 1.2 它**没有**做什么（划界关键，全部 verified by absence）
- **不定义任何 rigid-registration objective**：没有 J_p2p / J_p2l，没有代价函数，更没有在 true pose 处求梯度。
- **不出现 ∇J(T_GT)、Hessian、二次近似、−H⁻¹g、local-optimum displacement** 任何一个概念；它从不问"标准配准目标的正确极小值是否仍在 GT"。
- **不预测 6-DoF pose bias 的方向或大小**；矢量场是给人看的定性图，没有跨帧统计、bootstrap/permutation、effect size、CI。
- **不做 object-level nominal-CAD mismatch**：对象是两团**观测**云（或观测云 vs HD map）的场景级差异，不是"单个已知标称刚体 CAD 模型 vs 真实传感器对该物体的观测"。
- **非航天器**：无 MLI 褶皱、镜面双反射/ghost、太阳翼薄结构 mixed-pixel；域是地面自动驾驶。
- 工作流方向相反：它的终点是**把结构化 adversity 逐一 prune 掉、只留随机噪声**（correction/diagnosis）；本 Phase-0 明确**不做 correction**，而是证明残余结构如何使刚性目标本身有偏。

---

## 2. 四条"禁止卖点"逐条核对（Rescue Audit §2）

| 被禁止声称的卖点 | Choate & Rife 是否已覆盖 | 结论 |
|---|---|---|
| (a) 首次发现 **structured residual** | **已覆盖（定性）**：矢量场里"反向/成图案"的局部差即结构化残差，Fig.2 中明确区分 systematic vs random | **禁止主张** |
| (b) 首次把 LiDAR discrepancy **映射为空间场** | **已覆盖且即其标题贡献**：GT 对齐→体素均值差→离散 discrepancy-vector field（式 1） | **禁止主张** |
| (c) 首次**可视化局部 mismatch** | **已覆盖**：核心产物就是给人看的 vector-field plot | **禁止主张** |
| (d) 首次用空间场做 **scan-matching adversity 诊断** | **已覆盖**：明言面向 classify adversity modes that impact scan matching，且 algorithm-agnostic（ICP/NDT/ICET/LOAM） | **禁止主张** |

> 因此本论文**不得**再以"残差有空间结构 / 残差可画成场 / 局部 mismatch 可可视化 / 可用场诊断配准逆境"作为新颖性。这些在地面 LiDAR 域已于 ION GNSS+ 2024 发表。

---

## 3. 重新判定 DIRECT / GENERAL / ADJACENT

### 3.1 Choate & Rife 2024 的分级：**GENERAL（新增，编号 G7，GENERAL_PRIOR_ART_RISK = 高）**
- 为何**不是 DIRECT**：不同时满足 (航天)×(真实 LiDAR 对 nominal CAD)×(rigid 6-DoF objective 偏置)。它是地面驾驶、两观测云、**定性人因可视化**，全程不触及"配准目标在真姿态处非平稳、其局部极小偏离 GT"这一机制。
- 为何**不是普通 ADJACENT**：它在**一般域**里已经把"GT 对齐后的 discrepancy field + 区分可被刚性配准消掉的平移场 vs 消不掉的系统场"这套语言建立起来了，与本研究的**残差场刻画层**几乎同构，审稿人极可能引用它主张"空间差异场已知"。故必须升到 GENERAL 并在正文显式划界，与 Laconte 2019、Rife & McDermott 2024 并列为本研究三大 GENERAL 近邻。

### 3.2 更新后的总判定
| 判定项 | 原矩阵（28 篇） | 本次更新（+Choate&Rife） |
|---|---|---|
| DIRECT | 0 | **仍为 0**（无 STOP_PRIOR_ART） |
| GENERAL | 6（G1 Laconte / G2 Rife&McDermott / G3 IMLP / G4 ill-reflecting / G5 de-glaring / G6 ToF multipath） | **7（新增 G7 Choate&Rife）** |
| ADJACENT | 22 | 22（不变） |
| 8 行 claim 矩阵受影响行 | ①③ 原判 OPEN | **①下调为 PARTIAL（一般域"结构化差异场"已被 G7 定性占据）；③ 仍 OPEN（G7 无跨 aspect/跨帧定量可重复性，更无目标本体绑定复现）；④ 航天器 objective-bias 层仍 OPEN；⑥ 仍 OPEN** |

### 3.3 与既有四大近邻的并列划界（写论文时必须同段出现）
- **G7 Choate & Rife 2024（本次）**：GT 对齐体素差**矢量场 + 人因迭代去除**；定性、地面、algorithm-agnostic；**止步于"看见并删掉结构"，从不分析结构对刚性目标极小位置的作用**。
- **G1 Laconte 2019**：入射角→回波波形峰偏移→**逐射线标量**测距偏差→scan-to-map 里程计漂移，闭式物理校正；无目标本体 6-DoF、无 Hessian 机制。
- **G2 Rife & McDermott 2024**：纯**视角/遮挡几何**→voxel 配准系统误差的解析模型；城市里程计，与材料/nominal-CAD 无关。
- **Wang 2019（A6，ADJACENT，立场相反）**：明确把 MLI 误差定性为 **non-systematic**，滤波+trimmed ICP 剔除。
- **Renaut 2023 smoothed-NDT（A1，ADJACENT，缺口证据）**：一句未验证猜测"误差可能来自标定与 CAD-mockup 不一致"，从未分析/建模/验证。

> 关键叙事：Choate & Rife 的人因环路（Fig.2 左=整体平移配准误差、中=标定/尺度系统场）**恰好对应本研究 N1–N4 全局 nuisance 自动审计**——我们先自动、定量地消掉"坏配准/全局标定/尺度"能解释的部分（把他们人做的那一步数值化），再走到他们**从未到达**的一步：证明残余的、绑定目标本体的结构场使标准 rigid 6-DoF 目标在 T_GT 处 ∇J≠0、局部极小系统性偏离 GT，且该偏离可由 −H⁻¹g 定量预测。

---

## 4. 新颖性唯一允许落点（更新后，收窄表述）

在 G7 已占据"差异场/可视化/定性诊断"之后，本研究**唯一**允许的核心 claim 进一步收窄为：

> **object-level spacecraft nominal-model mismatch → rigid 6-DoF registration objective 在真姿态处非平稳（∇J(T_GT)≠0）→ 局部极小相对 GT 产生可预测的 6-DoF 位移（δξ*≈−H⁻¹g），且该位移在去除全局 range/SE3/scale nuisance、控制 range/point-count/aspect 后仍被结构化 mismatch 特异解释。**

该落点相对 G7 的三条不可替代差异：
1. **对象不同**：真实航天器 LiDAR 对**单一标称 CAD**（object-level, scan-to-nominal-model），非地面两观测云场景级差异；
2. **机制层不同**：不停留在"看见/画出/人因删除"差异场，而是建立 **objective gradient / Hessian → 6-DoF biased local optimum** 的定量、可证伪机制（含 self/null 对照与二次预测校验）；
3. **坐标系与证据不同**：证明结构**绑定目标本体、跨相似 aspect 定量复现**，并给出 nuisance-corrected 的增量解释量，而非单帧定性矢量图。

### 4.1 降级红线（维持并强化）
- 若最终只证明"residual field 有结构 / 可画成矢量场 / 有图案" → **直接落入 G7 已覆盖范围，判 STOP_PRIOR_ART_INCREMENTAL（=Rescue Audit Level 0）**。
- 必须达到 **objective 非平稳（M1）+ 局部极小系统位移（M2）+ mismatch 特异（M3）**，并最好叠加方向可预测（M4a）或 patch 梯度机制（M4b）与 −H⁻¹g 二次预测，才构成 G1/G2/G7 均未覆盖的独立贡献。

---

## 5. 合规说明
- 本轮主实验**尚未运行**；本更新严格先于任何 M1–M4 计算，符合 Rescue Audit §2"必须先完成"。
- 未使用模型记忆编造：书目、DOI、式(1)、Fig.2 三态、人因迭代流程、8–11 m 量级均来自 arXiv abs/PDF 实际抓取；会议版（ION GNSS+ 2024）正文未能逐页获取，已标注以 preprint 正文为准。
- 新数据下载：0（仅文献页面抓取，非数据集）。
