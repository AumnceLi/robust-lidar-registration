# CLAIM KILL TABLE — Structured Spacecraft LiDAR Model Mismatch
## 逐条 claim 的 Prior-Art Kill 评估

- 日期：2026-09-09｜配套文件：`PRIOR_ART_MATRIX.md`（28 篇文献全字段、检索记录、引文链）
- 文献编号沿用正表：**G1–G6** = GENERAL；**A1–A22** = ADJACENT；DIRECT = 0。
- Verdict 定义：**OPEN**（无覆盖，机制关系空缺）｜**PARTIAL**（部分层被覆盖，本问题层仍空缺）｜**COVERED**（已被完整覆盖，不可作为卖点）｜**STOP_PRIOR_ART**（DIRECT 同 formulation，立即停止）。
- 总判定：**无 STOP、无 COVERED；4 个 OPEN、4 个 PARTIAL；claim ④ 为最高风险行（GENERAL 部分覆盖）。**

---

## Claim ① — Real spacecraft LiDAR exhibits **structured** model mismatch（真实航天器 LiDAR 相对 nominal CAD 存在有空间结构的模型失配）

| 项 | 内容 |
|---|---|
| Novelty 评估 | **OPEN**。"真实航天器 LiDAR 有反射异常/ghost/domain gap"是被反复陈述的 Level A 事实（不新）；但"把观测与 nominal CAD 对齐后，残差不是白噪声散点，而是具有稳定空间组织的 mismatch field"这一**结构化命题**无人提出。 |
| Direct prior art | 无。A1/A3/A5 仅定性描述 MLI 反射点、表面消失、specular/multiple reflections；A4 只给实-仿 Chamfer 4.6 cm 的标量差距，未对 nominal CAD 做逐区域残差结构刻画；**A6（唯一 MLI 专题）显式把 MLI 误差定义为 "non-systematic errors"，立场相反**；A7 在仿真里把 multipath 按概率随机抽取。 |
| General prior art | G5（de-glaring）、G6（ToF 多径校正）证明多径伪影在通用域有物理结构与空间模式，但研究对象是像素/点级 artifact 本身，不是"相对已知 nominal 模型的 mismatch 场"。 |
| Verdict | **OPEN** |
| 为何空缺 | 现有航天工作的目标是"把位姿算出来"，反射点一律走 outlier rejection/trimmed/滤波管线，没人在有 GT pose 的真实数据（EPOS-Lid 恰好首次提供）上把 scan 投回 CAD 检查残差的空间统计；仿真工作（A7/A10/A22）又先验地把材料误差设成随机或朗伯体，结构在建模阶段就被抹掉。 |
| 子 claim 1a "存在非零均值残差（而非零均值白噪声）" | **PARTIAL**：G1 在通用域证明 LiDAR 测距非零均值；航天层 OPEN。 |
| 子 claim 1b "残差在目标本体坐标系上呈区域化/片状结构（MLI 区、太阳翼区、薄边区分异）" | **OPEN**：无任何文献做过该空间分区统计。 |
| 子 claim 1c "ghost/错点不是独立散点而沿特定几何（如双反射镜面像）组织" | **OPEN**（航天）；通用域 G5 有瞬态物理分析但不面向 CAD 模型。 |

---

## Claim ② — Mismatch is **surface/material dependent**（失配随表面/材料变化，有材料签名）

| 项 | 内容 |
|---|---|
| Novelty 评估 | **PARTIAL**。材料决定 LiDAR 返回质量在测量层/仿真层已被充分证明；新点只可能是"材料类别 → 对 nominal CAD 的残差签名（方向、尺度、缺失模式）"。 |
| Direct prior art | 无（无人把材料差异落到 CAD 残差签名）。测量/仿真层：**A10**（JAXA，5 类航天器材料 BRDF，测量误差与反射强度相关，给出 bias[mm] 表）、A1（golden MLI 高反射定性）、A3（MLI+太阳翼）、A20（1064 nm 涂层反射率可调）、A21（MLI 后向反射仅 0.05、强前向镜面实测）、A22（统一朗伯 ρ=0.4 的简化反例）。 |
| General prior art | **G4**（ill-reflecting 表面使测距能力退化至 33%）、G1（入射角-偏差函数）、arXiv:2309.01346 车漆白皮书、Sensors 24(2):378 表面颜色测距实验。 |
| Verdict | **PARTIAL**（测量层 COVERED，残差签名层 OPEN） |
| 为何仍有空间 | 现有材料证据回答"能不能测到、强度多少、仿真怎么随机化"，没有回答"同一标称几何下，MLI 褶皱面与刚性金属面相对 CAD 的偏差方向/空间尺度是否系统性不同"——后者才是本 claim 在论文里可主张的部分。 |
| 风险提示 | 若只写"MLI 产生更多 residual 点"= Level A，立即 STOP，不构成贡献。必须做材料分区的残差分布对比（方向直方图、缺失率、ghost 几何）。 |

---

## Claim ③ — Mismatch is **spatially repeatable**（空间可重复性：同 aspect/range 下残差模式稳定复现）

| 项 | 内容 |
|---|---|
| Novelty 评估 | **OPEN（最坚固的 claim 之一）**。 |
| Direct prior art | 无。EPOS-Lid 有 6 条 20m→3m 真实轨迹、±120° 对称重复观测条件，但 A5 与所有后向使用者（A17 等）均未做跨轨迹残差复现性分析；A1 只展示单帧 Fig.7。 |
| General prior art | G1 证明给定轨迹下偏差弯曲方向可预测/可重复（轨迹级，非目标本体绑定）；G6 证明多径偏差在固定几何下可重复学习。均非"同一目标、重复方位下残差场复现"。 |
| Verdict | **OPEN** |
| 为何空缺 | 需要"真实多轨迹 + 精确 GT pose + nominal CAD"三者同时具备才能检验，EPOS-Lid 之前不存在这样的数据；通用机器人研究的是静态环境自车运动，不存在"绕同一已知物体重复观测并对回本体坐标"的实验设计。 |
| 子 claim 3a "残差场跨轨迹在相同相对位姿处相关（而非轨迹特异）" | **OPEN**——这是建议的核心实验之一。 |
| 子 claim 3b "可重复性随距离收敛（近距残差结构更稳定）" | **OPEN**；A1 只有位置误差随接近减小的现象，未对残差场做该分析。 |

---

## Claim ④ — Mismatch induces **systematic pose bias / identifiability degradation**（诱发随机噪声解释不了的系统位姿偏差/可辨识性退化）★最高风险行

| 项 | 内容 |
|---|---|
| Novelty 评估 | **PARTIAL：一般机制层已被 GENERAL 覆盖，航天器物体级层 OPEN。这是全文最需要防守的 claim。** |
| Direct prior art | **无**。A1 Discussion 仅两句猜测（"could be induced by…differences between the real satellite mockup and the provided CAD model"），且与标定误差混同、从未验证；A6 明确假设 MLI 误差 non-systematic；A7 把多径建成随机 outlier；A8/A9/A12/A14/A15 等所有航天配准/跟踪工作均假设零均值噪声；A19 在**纯仿真**里给 UKF 加**单一标量** depth-bias state，不分析空间结构、不涉及 nominal CAD mismatch 本体。 |
| General prior art | **G1（Laconte ICRA 2019）：高入射角非零均值测距偏差 → 可预测 localization drift，物理建模并校正——一般意义上"结构化测量偏差→配准/定位系统偏差"闭环已存在；G2（Rife & McDermott NAVIGATION 2024）：视角几何导致 voxel 配准系统误差的解析模型与累积分析。** |
| Verdict | **PARTIAL（非 STOP）** |
| 为何 GENERAL 不能直接 kill（必须在论文中显式论证的三条划界） | (i) **物理机理不同**：G1 是 Lambertian 平面回波波形峰偏移（连续、逐射线 d,θ 标量），G2 是纯视角遮挡；候选问题是 MLI 褶皱镜面双反射 ghost、太阳翼强前向反射整片缺失、薄结构 mixed-pixel——离散、片状、绑定材料几何；(ii) **估计对象不同**：G1/G2 是 scan-to-map 自车里程计漂移（无名义物体模型），候选问题是 scan-to-**nominal-CAD** 的**目标物体级 6-DoF 刚性位姿**，并进一步研究与 ±120° 对称性耦合的**可辨识性退化**（错误吸引盆、Fisher 信息下降），该问题在通用文献中不存在；(iii) **偏差坐标系/证据不同**：通用工作没有"同一已知目标重复观测、残差绑定本体坐标复现"的证据链。 |
| 审稿风险 | 若不引用 G1/G2 并划界，会被评为"Laconte for spacecraft，换数据增量工作"= HIGH_PRIOR_ART_RISK。引用并证明机理/对象/坐标系三点不同后，claim ④ 的**航天器物体级与可辨识性部分保持 OPEN**。 |
| 子 claim 4a "偏差在零均值噪声模型下不可解释（白噪声拟合残差仍有方向偏置）" | **OPEN（航天）**；通用 G1 提供方法论样板而非覆盖。 |
| 子 claim 4b "偏差具有可复现的符号/方向（如沿某本体轴恒正）" | **OPEN**：A1 观察到 position error 随接近单调变化但未归因、未给方向模型。 |
| 子 claim 4c "结构化残差与目标对称性耦合，造成特定错误姿态吸引盆/可辨识性退化" | **OPEN**：A3 报告 ±60°/±120° 对称误判但归因纯几何对称，未与材料残差耦合；该耦合点无人触及，是 claim ④ 中最新、最安全的子主张。 |
| 子 claim 4d "标量 bias state（A19 式）不足以吸收空间结构残差" | **OPEN**：可用作对照实验，凸显结构化建模相对标量补偿的必要性。 |

---

## Claim ⑤ — Mismatch **varies with aspect/range**（随观测方位角/距离调制）

| 项 | 内容 |
|---|---|
| Novelty 评估 | **PARTIAL**。 |
| Direct prior art | A1："whenever the orientation of the sheets is not perpendicular to the sensor, the surface becomes invisible or displays reflected points"（aspect 依赖的定性现象，Fig.7）；A4：距离→点密度/质心偏差；A5：近距 FOV 截断。均无 aspect/range → pose bias 的定量规律。 |
| General prior art | G1：bias 是 (d,θ) 显式函数（定量样板）。 |
| Verdict | **PARTIAL**（现象定性有，调制规律与位姿传导 OPEN） |
| 为何空缺 | 需要跨 aspect 网格的重复扫描与残差/位姿联合统计；航天实验数据此前不支持，EPOS-Lid 6 轨迹首次可行但未被这样使用。 |
| 子 claim 5a "存在临界入射角，越过它 MLI 面由缺失转为 ghost 主导" | **OPEN**（A1 仅定性描述垂直/非垂直二分）。 |
| 子 claim 5b "pose bias 的方向随 aspect 周期性变化、range 决定幅值" | **OPEN**。 |

---

## Claim ⑥ — **Nominal rigid model is insufficient**（名义刚体 CAD 模型从根本上不足，需要显式失配层）

| 项 | 内容 |
|---|---|
| Novelty 评估 | **OPEN（与③并列最坚固）**。 |
| Direct prior art | 无形式化证明。A1 两句 CAD-mockup mismatch 猜测但未与标定误差分离；A4 用 ±15% 随机 deformation augmentation 含糊承认"potential inaccuracies of the target's 3D model"，恰证明社区靠随机增广回避该问题；A22 等仿真直接假设表面朗伯、几何精确。 |
| General prior art | **G3（IMLP）代表配准理论的最高标准形态：独立、零均值、各向异性高斯——即整个概率配准范式默认 nominal 几何正确、误差只有零均值随机项**。这从理论反面支撑"rigid + 零均值模型对结构化失配不足"的动机，但没有任何通用工作在"模型本身与观测存在物理结构失配"下重做配准一致性分析。 |
| Verdict | **OPEN** |
| 为何空缺 | 证明"模型不足"需要排除竞争性解释（标定误差、时间同步、运动畸变、随机噪声样本量），在真实数据上做受控残差分解——工程门槛高，且 DLR 谱系三年（A1→A3/A4→A5）始终停在猜测。 |
| 子 claim 6a "标定/运动畸变等竞争解释被控制后，残差结构仍存在" | **OPEN**，是论文可信度的关键实验（A1 把两者混在一起，留下了空白也留下了必须补的对照）。 |
| 子 claim 6b "在 rigid+白噪声模型下残差不通过白噪声/无偏检验，加入结构化失配项后通过" | **OPEN**。 |

---

## Claim ⑦ — Physical mismatch can be **parameterized**（物理失配可参数化）

| 项 | 内容 |
|---|---|
| Novelty 评估 | **PARTIAL**。参数化方法论在通用域与航天仿真层都有样板；航天器多物理耦合的结构化失配参数化无人做。 |
| Direct prior art | A10（modified-Phong BRDF，5 材料，测量层参数化，服务仿真器）；A19（UKF 标量 random-walk bias state，纯仿真融合）；A4（材料反射率 domain randomization 参数）。 |
| General prior art | **G1（闭式回波波形偏差模型 e(d,θ)+每传感器 2 标度因子，物理参数化黄金样板）**；G6（数据驱动学习多径校正场）；G2（柱/墙角 perspective error 解析模型）。 |
| Verdict | **PARTIAL** |
| 为何仍有空间 | 待参数化对象不同：不是逐射线波形偏差，而是绑定目标材料分区的偏差场（缺失概率、ghost 镜像几何、薄边 mixed-pixel 核），且参数要能进入 scan-to-CAD 的位姿似然而非仿真器或像素校正。 |
| 子 claim 7a "可用少量物理可解释参数（材料类、入射角、距离）解释大部分残差结构" | **OPEN（航天）**。 |
| 子 claim 7b "结构化参数模型显著优于同自由度的全局标量/各向同性噪声模型" | **OPEN**（可直接以 A19 标量模型为对照）。 |

---

## Claim ⑧ — Correcting/modeling it **improves pose**（建模/校正后位姿精度或可辨识性提升）

| 项 | 内容 |
|---|---|
| Novelty 评估 | **PARTIAL**。"校正有益"在通用域和航天仿真中已成立；**真实航天器数据上、对结构化失配建模后的 rigid pose 收益无人给出**。 |
| Direct prior art | A6（滤波+trimmed ICP 提升 MLI 目标位姿——但以 non-systematic 立场，是剔除而非建模，且 ToF/帧间）；A19（标量 bias state 改善旋转 RMSE 与 SNEES 一致性——纯 Blender 仿真）；A4（trimmed centroid 使成功率 +16 个百分点——质心离群剔除层面）。 |
| General prior art | **G1（偏差建模→地图/定位漂移显著下降，真实数据闭环）**；G6（多径校正→逐像素误差下降）；G2（解析模型预测累积误差）。 |
| Verdict | **PARTIAL**（真实数据、物体级、结构化建模的收益 OPEN） |
| 为何空缺/实验落点 | 在 EPOS-Lid 上对比：(a) 标准零均值配准（NDT/ICP/IMLP 式）、(b) 全局标量 bias（A19 式）、(c) 本文结构化失配模型，报告 6-DoF 系统偏差消除、对称误判率下降、可辨识性/Fisher 信息改善——该对照实验在检索范围内不存在。 |
| 子 claim 8a "系统偏差（误差均值）下降而非仅方差下降" | **OPEN**：现有航天消融只报 RMSE/成功率，不分离均值与方差。 |
| 子 claim 8b "可辨识性改善（错误姿态吸引盆缩小/收敛域扩大）" | **OPEN**。 |

---

## 跨 claim 汇总表

| Claim | Direct | General | Verdict | 可否作为核心卖点 |
|---|---|---|---|---|
| ① structured mismatch 存在 | 无 | G5/G6 仅 artifact 层 | **OPEN** | 可（与③④绑定陈述） |
| ② 材料/表面依赖 | A10/A20/A21（测量层） | G1/G4 | **PARTIAL** | 仅"残差签名"子点可，测量层不可 |
| ③ 空间可重复性 | 无 | G1/G6 弱旁证 | **OPEN** | **可，核心支柱** |
| ④ →系统位姿偏差/可辨识性 | 无（A1 仅未验证猜测；A6 立场相反） | **G1、G2（机制先例）** | **PARTIAL** | **可，但必须显式与 G1/G2 三点划界；4c 可辨识性耦合最安全** |
| ⑤ aspect/range 调制 | A1/A4 定性 | G1 定量样板 | **PARTIAL** | 调制规律子点可 |
| ⑥ rigid nominal 模型不足 | 无（A4 随机增广回避） | G3 反向动机 | **OPEN** | **可，核心支柱（需竞争解释对照）** |
| ⑦ 物理可参数化 | A10/A19（层不同） | G1/G2/G6 | **PARTIAL** | 结构化场参数化子点可 |
| ⑧ 建模改善位姿 | A6/A19（剔除/仿真/标量） | G1 真实闭环 | **PARTIAL** | 真实数据均值偏差消除+可辨识性子点可 |

## 最终 Kill 结论

1. **未发现 STOP_PRIOR_ART**：没有任何航天文献持有与候选问题相同的核心 formulation（structured, material-driven, spatially repeatable CAD mismatch → systematic rigid pose bias / identifiability loss）。最接近的 A6（Wang 2019 MLI）在误差哲学上显式对立（non-systematic），A1（Renaut 2023）只留下未验证的一句猜测——二者都是缺口证据而非覆盖。
2. **存在 HIGH_PRIOR_ART_RISK 而非 kill 的 GENERAL 线**：G1 Laconte 2019 + G2 Rife 2024 已在移动机器人域证明"结构化（非零均值、几何相关）测量偏差→配准系统偏差→建模校正有效"。claim ④⑦⑧ 的一般层因此只能主张 PARTIAL；论文必须以"物理机理（镜面多径/MLI/薄结构 vs 波形入射角）、估计对象（scan-to-nominal-CAD 物体级 6-DoF+对称可辨识性 vs scan-to-map 里程计）、偏差坐标系（目标本体绑定可复现 vs 传感器射线函数）"三条划界自保。
3. **真正空缺、可立为核心贡献的是 ③、⑥ 与 ④c（可辨识性耦合），以及 ①b 的材料分区残差结构**；②⑤⑦⑧ 只能以"航天器物体级结构化"子主张出现，且必须配真实数据对照实验（零均值模型 vs 标量 bias vs 结构化失配模型；分离标定竞争解释；跨轨迹复现）。
4. **明确的自我禁令**：不得把 claim 降格为"MLI 残差更多""残差比例与 pose error 相关""反射影响配准"——这些分别是 Level A STOP 与 generic reliability，检索已证明它们被 ADJACENT 文献充分占据。
