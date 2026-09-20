# PRIOR-ART MATRIX — G1 Novelty Kill
## Candidate Scientific Question: *Spacecraft-specific Structured LiDAR Model Mismatch*

- **检索执行日期**：2026-09-09（Asia/Shanghai）
- **检索员**：Prior-Art Kill Agent（真实联网检索，general_search + web.fetch）
- **锚点论文**：Renaut, Klionovska, Albracht, Frei. *EPOS-Lid: Lidar benchmark dataset for pose estimation during non-cooperative rendezvous*. Acta Astronautica 238-A (2026) 414–423. DOI: [10.1016/j.actaastro.2025.09.030](https://doi.org/10.1016/j.actaastro.2025.09.030)
- **候选 claim 核心机制关系**：real spacecraft LiDAR vs nominal CAD/point-model 之间，由 MLI / 太阳翼 / 薄结构 / 镜面多径等**航天器特有物理**造成的、**有稳定空间结构（structured, spatially repeatable）的 model mismatch** → 诱发 rigid-model pose estimation 中**随机噪声解释不了的系统性 bias / 可辨识性退化**。
- **分级定义**：DIRECT = 航天+LiDAR+material/geometry mismatch+pose/registration impact 且 formulation 基本相同（=STOP_PRIOR_ART）；GENERAL = 非航天但一般理论直接覆盖机制链；ADJACENT = ghost removal / ICP / MLI 仿真 / domain randomization / outlier rejection，未研究 structured mismatch → endpoint pose bias。

---

## 0. 总体判定（Executive Verdict）

| 判定项 | 结论 |
|---|---|
| 是否存在 **DIRECT** 覆盖（航天+LiDAR+structured mismatch→systematic pose bias，formulation 相同） | **否。未发现。** 无 STOP_PRIOR_ART。 |
| 是否存在 **GENERAL** 覆盖（一般理论直接证明 surface-dependent measurement bias → registration/pose bias，可直接套用） | **部分存在（HIGH_PRIOR_ART_RISK）**：Laconte 2019（入射角相关测距偏差→可预测 localization drift，物理建模+校正）与 Rife & McDermott 2024（视角几何→voxel scan-match 系统误差）在**移动机器人 scan-to-map** 层面建立了"非零均值、几何/表面相关的结构化测量偏差→配准/定位系统性误差→建模校正有效"的一般机制链。但其物理机理（Lambertian 回波波形峰偏移 / 视角遮挡）、任务形态（走廊里程计漂移，非物体级 scan-to-nominal-CAD 6-DoF pose）、偏差结构（逐点标量场，非 MLI 褶皱/镜面双反射/薄结构 mixed-pixel 的航天器组合物理）均不同，**不能直接等同于候选问题**。 |
| 航天领域最接近的工作 | (1) Wang et al. 2019 IEEE Access（MLI 包覆非合作目标位姿估计）——但其明确把 MLI 误差定性为 **non-systematic errors**，用滤波+trimmed ICP 剔除，机理立场与候选 claim **相反**；(2) Renaut et al. 2023 smoothed-NDT——承认 MLI 反射降低扫描质量，并在 Discussion 用**一句话猜测**位置误差形态"可能由标定误差与 CAD-mockup 不一致引起"，但从未分析、建模或验证。两者均为 ADJACENT，且恰好构成"缺口证据"。 |
| 8 条 claim 中真正空缺 | ①（structured 形态）③（空间可重复性）④（航天器物体级 systematic pose bias / 可辨识性退化）⑤（aspect/range 调制的 bias 规律）⑥（nominal rigid model 不足的形式化证明）为 **OPEN**；②⑦⑧ 为 **PARTIAL**（测量层/一般层已覆盖，航天器结构化位姿层空缺）。 |
| 新颖性结论 | **G1 存活（NOVEL，附条件）**：新颖性必须押在"真实航天器 LiDAR 上结构化残差场的**刻画** + 其向 rigid 6-DoF pose bias/可辨识性退化的**机制传导** + aspect/range 依赖"三者交集；必须显式与 Laconte 2019 划界（波形入射角偏差 vs 航天器镜面多径/MLI/薄结构物理；里程计漂移 vs 对 nominal CAD 的物体级位姿）。若只讲"MLI 产生更多残差点/反射异常影响配准"，则落入 ADJACENT，不具新颖性（Level A STOP）。 |

---

## 1. 12 组指定检索执行记录

> 工具：general_search；每组检索后阅读返回结果标题/摘要/来源，高相关者 web.fetch 精读。第 1 组精确短语零命中后已放宽重检（见 1.1 与补检）。

| # | 检索式（实际执行） | 命中后人工筛出的相关结果数 | 关键发现 / 最相关条目 |
|---|---|---|---|
| 1 | `"spacecraft lidar" "model mismatch" pose estimation`（精确短语，**0 条**）；放宽为 `spacecraft lidar CAD model mismatch point cloud registration` | 精确短语 0；放宽后 4 篇相关 | 无任何文献使用 "model mismatch" 这一 formulation；最相关为 J-ICP（Applied Sciences 2024）、Tumbling tracking（Sensors 2018, PMC6209945）、2-DoF ENVISAT template matching，均为算法论文，不研究结构化偏差。 |
| 2 | `spacecraft lidar CAD model mismatch point cloud registration` | 4 | J-ICP MDPI 2024；面阵 LiDAR 空间站对接仿真（红外与激光工程 2025，表面统一假设朗伯体 ρ=0.4）；NFRPE-3D（光学学报）；ISPRS PC2Model benchmark（非航天）。 |
| 3 | `spacecraft lidar registration bias systematic pose error` | 5 | **LIRIS 在轨实验**（ESA SDC7，Airbus，提到 fly-under bias correction，但属外参标定级）；NASA Flash LiDAR RelNav（bias dominate error 但为导航级统计）；2-DoF template matching（ENVISAT，仿真）；ISPRS 2023 LDAR 相对位姿（仿真，点云对齐误差 0.038 m 略高于测距误差，未归因材料）。 |
| 4 | `non-cooperative spacecraft lidar multipath effects rendezvous` | 3 | LIRIS flight database（EUCASS 2018）；arXiv:2507.16214 Dual Noise Tuning（**显式建 scalar LiDAR depth bias state**，纯仿真、相机-LiDAR 融合，ADJACENT）；其余为相对导航综述/通用 GNC。 |
| 5 | `spacecraft multilayer insulation MLI lidar laser reflection scattering` | 3 | arXiv:2311.13108 Spacecraft Coatings Optimizing LiDAR Debris Tracking（材料反射率测量，ADJACENT）；Earth & Space Science 2025 航天器材料光度/光谱表征（**实测 MLI/太阳电池强镜面分量**，ADJACENT）；其余为 MLI 热控科普，剔除。 |
| 6 | `spacecraft lidar ghost points false returns reflective surfaces` | 4（航天内 0，通用 4） | **航天领域无 ghost-point 专门研究**；命中全部来自自动驾驶/机器人：Ghost-FWL 全波形 ghost 数据集（arXiv 2026）、De-glaring transient domain（CVPR 2026）、mirror spoofing（USENIX 2026）、Plane-SLAM 反射检测（arXiv 2406.10494）。→ 航天器 ghost 研究缺口的直接证据。 |
| 7 | `spacecraft lidar specular reflection pose estimation point cloud` | 5 | Renaut TAES 2025 CNN pose（trimmed centroid 去 ghost）；Renaut smoothed-NDT（MLI 非正交时表面消失/出反射点）；MDPI Remote Sensing 2025 two-stage registration（纯 CAD 仿真）；FlashPose NASA 专利；均未把镜面反射与系统性 pose bias 挂钩。 |
| 8 | `solar panel lidar multipath spacecraft point cloud artifact` | 1（航天内 0） | 无太阳翼多径专门文献；命中为光伏板点云色彩校正（ISPRS 2026，无关）、自动驾驶投影伪影 RePLAy、通用 ghost 文献。→ 太阳翼镜面多径对航天器位姿影响 = 空白。 |
| 9 | `spacecraft point cloud CAD registration material reflection simulation domain randomization` | 4 | Renaut Acta Astronautica 232 (2025)（**Chamfer 实-仿距离 4.6 cm vs 1°旋转仅 1.4 cm**；MLI 褶皱 vs 仿真平面）；3DGS 少样本航天器位姿（视觉，纹理随机化）；Space: Sci&Tech RGB-D 数据集（BlenSor 仿真）；AIAA DeepCPD。 |
| 10 | `non-cooperative target point cloud systematic error bias lidar relative navigation` | 5 | **Opromolla Sensors 2015（PMC4435155）：multipath 被显式建模为按概率随机抽取、4σ_RANGE 的随机 outlier**——航天主流把多径当随机噪声的代表证据；arXiv 2401.13416 perspective error（GENERAL）；双约束面间投影（Sensors，扫描角错位问题）；Dual Noise Tuning。 |
| 11 | `spacecraft lidar surface material pose bias reflectivity intensity` | 5 | **JAXA ESA SDC8 2021 BRDF LiDAR 仿真器**（5 类材料含 MLI，测量误差与反射强度相关，纯仿真器）；Renaut smoothed-NDT（golden MLI 影响扫描质量）；arXiv:2311.13108 coatings；空间站对接论文（朗伯假设）。无材料→pose bias 传导研究。 |
| 12 | `spacecraft lidar real synthetic gap material mismatch sim-to-real point cloud` | 3 | Renaut Acta 2025（domain randomization 覆盖材料参数）；SynLiDAR（自动驾驶）；RPO 仿真评估（真实/虚拟 LiDAR 目视比较）；均停留在 domain gap 现象学，不做残差结构与位姿偏差机制。 |
| 补 A | `Wang "Pose estimation of non-cooperative target coated with MLI" IEEE Access 2019` + 全文定位 | 6（元数据/摘要多源交叉验证） | 确认 DOI 10.1109/ACCESS.2019.2946346；**摘要原文："Aiming at decreasing the non-systematic errors caused by MLI"**；使用 ToF 相机 + 帧间 ICP；IEEE Xplore 全文被 robots.txt 禁止自动访问 → **claim-only**。 |
| 补 B | General Robotics Kill 6 组（见第 4 节） | 8 | Laconte 2019（最强 GENERAL）、Rife 2024、IMLP、ill-reflecting 实验、de-glaring、ToF multipath 学习校正、mirror navigation、plane SLAM。 |
| 补 C | 引文链：Renaut 系列 / EPOS-Lid 被引 / smoothed-NDT 被引 | 5 | VISAPP 2023 原点；TAES 2025；Acta 232 (2025)；JGCD 2026 invariant filtering（自引）；Kim & Myung TAES 2026（外部使用 EPOS-Lid 做基准，纯算法）。 |

---

## 2. 文献详细列表（28 篇，分级分组）

> 字段：标题 / 作者 / 年份 / 出处 / DOI 或 URL / 分级 / 与 8 条 claim 关系 / 获取状态。
> **verified-actual-page** = 实际抓取并阅读了页面正文（全文或大段正文）；**claim-only** = 仅读到摘要/被其他文献引用的书目信息，全文未能获取（已注明原因）。

### 2.1 DIRECT 组（0 篇）

**无。** 没有任何已检索文献同时满足：(航天) × (真实 LiDAR) × (相对于 nominal CAD 的结构化材料/几何 mismatch) × (rigid 6-DoF pose 系统偏差/可辨识性退化) × (formulation 与候选问题基本相同)。

两个"最接近但降级"的高危近邻（Wang 2019、Renaut 2023）列入 ADJACENT 并在第 5 节专门做对照。

### 2.2 GENERAL 组（6 篇）——非航天一般理论/证据

#### G1. Lidar Measurement Bias Estimation via Return Waveform Modelling in a Context of 3D Mapping
- 作者：Johann Laconte, Simon-Pierre Deschênes, Mathieu Labussière, François Pomerleau
- 年份：2019｜出处：IEEE ICRA 2019（Montreal）
- URL: https://norlab.ulaval.ca/pdf/Laconte2019.pdf
- 分级：**GENERAL（最高 GENERAL_PRIOR_ART_RISK，必须在论文中显式划界）**
- 与 claim 关系：④⑦⑧ 的一般机制先例。证明 LiDAR 测量并非零均值高斯：**高入射角下回波波形峰偏移产生可预测、可重复的测距偏差（可达 20 cm，深度×入射角函数 e(d,θ)），该偏差导致可预测的 localization/mapping drift；用物理模型校正后漂移显著下降**。对应 claim ④"结构化测量偏差→配准/定位系统偏差"、⑦"物理可参数化（闭式波形模型+每传感器 2 标度因子）"、⑧"建模校正改善结果"。
- 不覆盖之处（划界要点）：(i) 物理机理是 Lambertian 平面上光束足迹的回波波形偏斜，**不含镜面双反射/ghost、MLI 褶皱、薄结构 mixed-pixel、表面缺失**；(ii) 任务是移动机器人 2D/3D 建图里程计漂移（scan-to-map、走廊），**不是物体级 scan-to-nominal-CAD 的 6-DoF rigid pose，也无可辨识性退化分析**；(iii) 偏差是逐射线 d,θ 标量函数，不形成"绑定在目标本体坐标系上、随 aspect 复现的空间残差结构"。
- 获取状态：**verified-actual-page**（通读全文主体，含模型推导与实验设置）。

#### G2. Characterizing Perspective Error in Voxel-Based Lidar Scan Matching
- 作者：Jason H. Rife, Matthew McDermott
- 年份：2024｜出处：NAVIGATION (ION), 71(1), navi.627；arXiv:2401.13416
- DOI/URL: https://doi.org/10.33012/navi.627 ；https://arxiv.org/pdf/2401.13416v1
- 分级：**GENERAL**
- 与 claim 关系：④的一般先例——解析证明视角变化造成的可见面/遮挡差异使 NDT/ICET 类 voxel 配准产生**系统性（非零均值、可累积）误差**，量级可达柱径。支持"配准里存在非随机系统项"这一命题。
- 不覆盖之处：机理是纯几何视角/遮挡（perspective），与材料/反射物理无关；场景为城市地物里程计；不涉及 nominal model mismatch。
- 获取状态：**verified-actual-page**（摘要页 + arXiv 正文首段与结论页）。

#### G3. Iterative Most-Likely Point Registration (IMLP): A Robust Algorithm for Computing Optimal Shape Alignment
- 作者：Seth D. Billings, Eric M. Johnson-Roberson（通讯）
- 年份：2015｜出处：PLOS ONE 10(3):e0117688
- DOI/URL: https://doi.org/10.1371/journal.pone.0117688
- 分级：**GENERAL（反向证据/基线）**
- 与 claim 关系：概率配准主流显式假设 source/target 误差为**独立、零均值、各向异性高斯**。这正是候选问题声称"不够用"的标准模型——即文献现状把局部各向异性（仍零均值）做到极致，但不处理非零均值结构化偏差。支撑 claim ⑥ 的问题动机。
- 获取状态：claim-only（摘要页正文）。

#### G4. Assessing the Robustness of LiDAR, Radar and Depth Cameras Against Ill-Reflecting Surfaces in Autonomous Vehicles: An Experimental Study
- 作者：（多作者实验研究，arXiv 预印本）
- 年份：2023｜出处：arXiv:2309.10504
- URL: https://arxiv.org/pdf/2309.10504
- 分级：**GENERAL（测量层）**
- 与 claim 关系：②的一般证据——材料反射率使 LiDAR 静态测距能力退化到名义条件的 33%，即返回质量强材料依赖；但只到检测/测距层，无配准/位姿传导。
- 获取状态：claim-only（摘要页）。

#### G5. Ghosts in the Point Clouds: De-glaring LiDAR in the Transient Domain
- 作者：CMU Wision Lab 等（作者完整名单见论文页，抓取页未逐位核验）
- 年份：2026（CVPR 2026）｜出处：CVPR 2026 / Wision Lab 公开 PDF
- URL: https://wisionlab.com/wp-content/uploads/2026/06/ghosts-in-the-point-clouds.pdf
- 分级：**GENERAL→实为 ADJACENT 性质（artifact removal）**
- 与 claim 关系：①②在通用域的现象学——强反射/逆反射表面引发内部多径 glare，产生 phantom objects；给出瞬态域物理去眩光方法。**只做 artifact 去除，不研究 ghost 残留对刚体配准位姿的系统性偏置**。
- 获取状态：claim-only（摘要+引言页）。

#### G6. Learning the Correction for Multi-Path Deviations in Time-of-Flight Cameras
- 作者：Mojmir Mutny, Rahul Nair, Jens-Malte Gottfried
- 年份：2015（v2 2016-01）｜出处：arXiv:1512.04077（预印本；DOI 10.48550/arXiv.1512.04077）
- URL: https://arxiv.org/abs/1512.04077
- 分级：**GENERAL（像素层结构化偏差可学习校正）**
- 与 claim 关系：⑦⑧的类比——多径偏差是**空间结构化、可预测**的像素深度偏差，Random Forest 学习实值校正显著改善深度。说明"多径→结构化偏差→可参数化/可校正"在 ToF 像素层成立；但不到物体位姿层，更非航天。
- 获取状态：claim-only（正文片段页）。

### 2.3 ADJACENT 组（22 篇）

#### A1. Lidar Pose Tracking of a Tumbling Spacecraft Using the Smoothed Normal Distribution Transform ★关键缺口证据
- 作者：Léo Renaut, Heike Frei, Andreas Nüchter（DLR GSOC / Uni Würzburg）
- 年份：2023｜出处：Remote Sensing 15(9):2286
- DOI/URL: https://doi.org/10.3390/rs15092286
- 分级：**ADJACENT（EPOS-Lid 直接前作，最接近的航天内部近邻）**
- 与 claim 关系：
  - ①②：明确写"beam divergence, sensor noise, **materials on the target**…spacecrafts are often coated with golden MLI sheets, and the resulting reflections and light scattering affects the quality of the scans"；实验节："Due to the high reflectivity of the MLI, whenever the orientation of the sheets is not perpendicular to the sensor, **the surface becomes invisible or displays reflected points**"（Fig.7，aspect 依赖的表面缺失/反射点，支撑 claim ⑤ 现象层）。
  - ④⑥：**Discussion 5.1/5.2 两次出现**："position error decreased during approach…could be induced by slight errors in sensor calibration, and **differences between the real satellite mockup and the provided CAD model**"；"both algorithms might be affected by the same biases, probably **calibration errors and mismatches between the CAD model and real mockup**"。——这是全文献中 EPOS 谱系离候选问题最近的一句话，但只是**未验证的一句猜测**，且与标定误差混为一谈，从未刻画残差空间结构、从未建立到 pose bias 的机制、从未区分随机/系统项。
  - 应对策略：把 MLI 反射当 outlier/quality 问题（引 Wang 2019 trimmed ICP），主线贡献是 motion blur 与 NDT 效率。
- 获取状态：**verified-actual-page**（全文 20 页通读，含参考文献全表）。

#### A2. Smoothed Normal Distribution Transform for Efficient Point Cloud Registration During Space Rendezvous
- 作者：L. Renaut, H. Frei, A. Nüchter
- 年份：2023｜出处：VISIGRAPP/VISAPP 2023, pp.919–930, SciTePress
- URL: https://elib.dlr.de/196292/1/smoothed_ndt.pdf
- 分级：ADJACENT（A1 的会议原点，纯配准算法）
- 与 claim 关系：⑥的工具层（smoothed NDT 即 EPOS-Lid 的 refine/hand-eye 标定器）；不涉及材料偏差机制。
- 获取状态：**verified-actual-page**（正文首段页）。

#### A3. CNN-based Pose Estimation of a Non-Cooperative Spacecraft with Symmetries from Lidar Point Clouds
- 作者：L. Renaut, H. Frei, A. Nüchter
- 年份：2025｜出处：IEEE Transactions on Aerospace and Electronic Systems 61(2):5002–5016
- URL: https://elib.dlr.de/213607/1/taes_renaut_double_column_revision.pdf
- 分级：ADJACENT
- 与 claim 关系：①②现象层——"high reflectivity of…solar panels and golden MLI…point clouds present artifacts or ghost reflections"，对策是 **trimmed centroid 去质心离群**（把 ghost 当离群点丢弃）；对称性导致 ±60°/±120° 误判（这是几何对称可辨识性问题，与材料偏差不同，需在论文中区分）。无 structured residual、无 bias 机制。
- 获取状态：**verified-actual-page**（正文多段）。

#### A4. Deep learning on 3D point clouds for fast pose estimation during satellite rendezvous ★关键缺口证据
- 作者：L. Renaut, H. Frei, A. Nüchter
- 年份：2025｜出处：Acta Astronautica 232:231–243
- URL: https://elib.dlr.de/213609/1/online_version.pdf
- 分级：**ADJACENT（实-仿差距被定量，但归因止步于 reflection 建模难度）**
- 与 claim 关系：
  - ①②⑤：真实点云 vs 同姿态仿真点云 **Chamfer 距离 4.6 cm，而两片真实云转 1° 仅 1.4 cm**；明确"real MLI 上更多点对传感器不可见；MLI 是褶皱的而仿真假设平面"；仿真器用简化 Phong、最多一次反射。
  - ⑥：训练时加 ±15% 各向异性 deformation augmentation 以"account for potential inaccuracies of the target's 3D model"——隐含承认 nominal 模型不足，但用随机形变糊过去，反向证明没人做结构化刻画。
  - ⑦：材料反射率 domain randomization（参数取自 Nakajima/JAXA）。
  - ⑧：trimmed centroid 消融——普通质心因 2 倍距离 ghost 点导致成功率掉 16%（ghost 影响的是**质心预处理**，不是被建模为 pose bias 场）。
- 获取状态：**verified-actual-page**（方法/实验/消融大段正文）。

#### A5. EPOS-Lid: Lidar benchmark dataset for pose estimation during non-cooperative rendezvous（锚点论文本身）
- 作者：L. Renaut, K. Klionovska, M. Albracht, H. Frei
- 年份：2026｜出处：Acta Astronautica 238-A:414–423
- DOI/URL: https://doi.org/10.1016/j.actaastro.2025.09.030 ；全文 https://elib.dlr.de/217446/1/1-s2.0-S0094576525005995-main.pdf
- 分级：ADJACENT（数据集论文；候选问题的数据来源）
- 与 claim 关系：①现象层——mockup 用真实 golden MLI 与太阳翼，"some point clouds…may contain erroneous points due to **specular and multiple reflections**"，并刻意保留这些点以测鲁棒性；仿真器建模 double reflection + 材料随机化；benchmark 误差分析只归因于六边形对称与近距离 FOV 截断，**未做 residual-vs-CAD 的结构化分析，未报告 systematic pose bias**。→ 候选问题正是该数据集"留下没做"的分析。
- 获取状态：**verified-actual-page**（多次抓取，含方法、3.1 节、结果、参考文献）。

#### A6. Pose Estimation of Non-Cooperative Target Coated With MLI ★最危险近邻（已降级）
- 作者：Qishuai Wang, Ting Lei, Xiao-Feng Liu, Guo-Ping Cai, Yifeng Yang, Lihui Jiang, Zhang-Wei Yu（上海交大）
- 年份：2019｜出处：IEEE Access 7:153958–153968
- DOI: https://doi.org/10.1109/ACCESS.2019.2946346
- 分级：**ADJACENT（航天+MLI+位姿估计三要素齐全，但 error philosophy 相反）**
- 与 claim 关系：
  - ①②：唯一标题级直接针对"MLI 包覆非合作目标"做位姿估计的论文；使用 **ToF 相机**（非扫描 LiDAR）获取点云、帧间 ICP 配准。
  - 关键反证：摘要明确方案目标是"**decreasing the non-systematic errors caused by MLI**"——即作者把 MLI 误差定义为**非系统性**随机误差，技术路线为点云滤波 + trimmed ICP 鲁棒剔除。候选问题的核心（MLI 造成**结构化、系统性**偏差）在该文中被显式假定为不成立。
  - ④：无 scan-to-nominal-CAD 残差场、无系统 bias 识别、无可辨识性分析；是 frame-to-frame tracking 而非 model-based endpoint 偏差研究。
- 获取状态：**claim-only**（IEEE Xplore 全文禁止自动抓取；摘要经 SciSpace/Semantic Scholar/R Discovery 多源交叉验证，关键句"non-systematic errors"来自 R Discovery 收录的摘要原文）。

#### A7. A Model-Based 3D Template Matching Technique for Pose Acquisition of an Uncooperative Space Object ★关键缺口证据
- 作者：R. Opromolla, G. Fasano, G. Rufino, M. Grassi（Uni Napoli Federico II）
- 年份：2015｜出处：Sensors 15(3):6360–6382
- DOI/URL: https://doi.org/10.3390/s150306360 ；https://pmc.ncbi.nlm.nih.gov/articles/PMC4435155/
- 分级：**ADJACENT（航天仿真主流把 multipath 当随机 outlier 的范式样本）**
- 与 claim 关系：其 LiDAR 仿真器中"outliers…**simulate possible multipath effects** due to the actual target geometry and are **extracted on the basis of a given outliers probability**…range uncertainty std 4×σ_RANGE"；测距噪声=零均值高斯白噪声。即航天领域先验工作把多径**概率化、随机化、无空间结构**——与候选 claim 的 structured 立场直接对立，构成缺口佐证。目标 ENVISAT，scanning ToF LiDAR 仿真。
- 获取状态：**verified-actual-page**（PMC 全文大段，含噪声模型与结论）。

#### A8. Pose estimation for spacecraft relative navigation using model-based algorithms
- 作者：R. Opromolla, G. Fasano, G. Rufino, M. Grassi
- 年份：2017｜出处：IEEE Trans. Aerospace and Electronic Systems 53(1):431–447
- DOI: https://doi.org/10.1109/TAES.2017.2650785（DOI 经 ORCID/AIAA 引用页核验；书目来自 A1 参考文献表）
- 分级：ADJACENT
- 与 claim 关系：model-based（CAD 模板 + ICP/NS）跟踪算法与精度评估基线；不涉及材料偏差。
- 获取状态：claim-only（书目与方法定位来自 A1/A5 引用）。

#### A9. Uncooperative Spacecraft Relative Navigation with LIDAR-based Unscented Kalman Filter
- 作者：R. Opromolla, A. Nocerino
- 年份：2019｜出处：IEEE Access 7:180012–180026
- DOI: https://doi.org/10.1109/ACCESS.2019.2959438（DOI 经 ORCID/Crossref 核验；书目来自 A1 参考文献表）
- 分级：ADJACENT
- 与 claim 关系：UKF 预测 + ICP 的 tracking 框架；假设点云噪声零均值，无结构化偏差状态。
- 获取状态：claim-only。

#### A10. Development of LiDAR Measurement Simulator Considering Target Surface Reflection
- 作者：Yu Nakajima, Takahiro Sasaki, Naoki Okada, Toru Yamamoto（JAXA）
- 年份：2021｜出处：8th European Conference on Space Debris (SDC8), ESA Space Debris Office, paper 21
- URL: https://conference.sdo.esoc.esa.int/proceedings/sdc8/paper/21
- 分级：**ADJACENT（航天材料 BRDF 测量-仿真，测量层最细的工作）**
- 与 claim 关系：②⑦测量/仿真层——实验测 5 类火箭体表面材料（含 MLI、bulkhead）BRDF，modified Phong 建模漫反射+镜面分量；明确"**measurement errors have a correlation to reflection intensity**"，并给出不同材料/距离的 bias[mm] 表（Table 2，Cepton Vista P-60 实测 vs 仿真）。但终点是**生成更真的仿真点云**，没有把测量偏差向 registration/pose 传导，更无真实非合作目标的结构化残差场。
- 获取状态：**verified-actual-page**（落地页+7 页正文预览图全部读取）。

#### A11. Hardware-in-the-Loop Simulations with Umbra Conditions for Spacecraft Rendezvous with PMD Visual Sensors
- 作者：K. Klionovska, M. Burri（DLR）
- 年份：2021｜出处：Sensors 21(4):1455
- DOI/URL: https://doi.org/10.3390/s21041455
- 分级：ADJACENT（邻近传感器 ToF/PMD 线）
- 与 claim 关系：②弱相关——地影/低照下 PMD 深度数据质量与滤波；传感器是调制 ToF 而非扫描 LiDAR，无材料结构化偏差机制。
- 获取状态：**verified-actual-page**（正文多段）。

#### A12. Relative Pose Estimation of Non-Cooperative Space Targets Using a TOF Camera
- 作者：D. Sun, L. Hu, H. Duan, H. Pei
- 年份：2022｜出处：Remote Sensing 14(23):6100
- DOI/URL: https://doi.org/10.3390/rs14236100
- 分级：ADJACENT
- 与 claim 关系：低 SNR 点剔除 + 边缘保持滤波 + ICP；噪声按随机处理；ToF 相机。
- 获取状态：**verified-actual-page**（方法节片段）。

#### A13. Pose initialization of uncooperative spacecraft by template matching with sparse point cloud
- 作者：W. Guo, W. Hu, C. Liu, T. Lu
- 年份：2021｜出处：Journal of Guidance, Control, and Dynamics 44(9):1707–1720（AIAA）
- DOI/URL: https://doi.org/10.2514/1.G005042（经 AIAA 页面核验；书目另见 A1 参考文献表）
- 分级：ADJACENT
- 与 claim 关系：PCA 降维 + 2D 剪影模板匹配做初始化；in-house LiDAR 仿真器，ENVISAT；无真实材料偏差。
- 获取状态：claim-only。

#### A14. LiDAR-Based Non-Cooperative Tumbling Spacecraft Pose Tracking by Fusing Depth Maps and Point Clouds
- 作者：Gaopeng Zhao, Sixiong Xu, Y. Bo
- 年份：2018｜出处：Sensors 18(10)（PMC6209945）
- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC6209945/
- 分级：ADJACENT
- 与 claim 关系：已知几何模型假设下的 depth-map+点云融合 ICP 跟踪；自适应体素化；不涉及材料/反射偏差。
- 获取状态：**verified-actual-page**（摘要+方法片段）。

#### A15. Application of Micro-Plane Projection Moving Least Squares and Joint ICP Algorithms in Spacecraft Pose Estimation (J-ICP)
- 作者：（多作者，MDPI 开放获取）
- 年份：2024｜出处：Applied Sciences 14(13):5855
- DOI/URL: https://doi.org/10.3390/app14135855
- 分级：ADJACENT
- 与 claim 关系：mpp-MLS 微平面投影降噪 + 多帧 Joint-ICP 解决对称目标小角度转动下 ICP 局部最优；噪声被假设为可平滑的随机扰动；无材料结构偏差。
- 获取状态：**verified-actual-page**（摘要/方法多段）。

#### A16. Neural-Network-Based Pose Estimation During Noncooperative Spacecraft Rendezvous Using Point Cloud (DeepCPD)
- 作者：Shaodong Zhang, Weiduo Hu, Chang Liu（北航）
- 年份：2023｜出处：Journal of Aerospace Information Systems (AIAA)
- DOI/URL: https://doi.org/10.2514/1.I011179
- 分级：ADJACENT
- 与 claim 关系：神经网络替换 GMM 配准 EM 步，scan-to-reference-model；声称对"data imperfections"鲁棒，但未区分系统/随机，未做材料分析。
- 获取状态：**verified-actual-page**（摘要页）。

#### A17. Robust and Accurate 3-D Point Cloud Registration Method for Close-Range Docking of Spacecraft
- 作者：Juhyun Kim, Hyun Myung（KAIST）
- 年份：2026（在线先发）｜出处：IEEE Transactions on Aerospace and Electronic Systems
- DOI: https://doi.org/10.1109/TAES.2026.3656159
- 分级：ADJACENT（**EPOS-Lid 的外部后向被引**，benchmark 用户）
- 与 claim 关系：在 EPOS-Lid 上做 translation[mm]/rotation[deg] 基准对比的配准算法论文；只报精度指标，不分析数据集残差结构。→ 后向追踪证明 EPOS-Lid 的后续使用者也未提出 structured mismatch 问题。
- 获取状态：claim-only（Semantic Scholar 书目+图表片段）。

#### A18. Airbus DS Vision-Based Navigation Solutions Tested on LIRIS Experiment Data
- 作者：Airbus DS 团队
- 年份：2017｜出处：7th ESA Space Debris Conference (SDC7), paper 481
- URL: https://conference.sdo.esoc.esa.int/proceedings/sdc7/paper/481/SDC7-paper481.pdf
- 分级：ADJACENT
- 与 claim 关系：真实在轨 LIRIS 实验（ATV-5），LiDAR 点云畸变标定、fly-under 图像估计外参做 **bias correction**——是真实航天 LiDAR 中"偏差需校正"的罕见在轨记录，但偏差来源被归为传感器标定/外参，不是目标材料结构 mismatch。
- 获取状态：**verified-actual-page**（正文片段）。

#### A19. Adaptive Relative Pose Estimation Framework with Dual Noise Tuning for Uncooperative Target
- 作者：（Iowa State 方向，arXiv 预印本）
- 年份：2025（v3）｜出处：arXiv:2507.16214
- URL: https://arxiv.org/html/2507.16214v3
- 分级：**ADJACENT（航天器内最接近"显式 bias state"的工作，但为标量、融合、纯仿真）**
- 与 claim 关系：⑦⑧——发现 Blender LiDAR 点与投影角点对不齐导致 depth channel "systematic offsets"，于是在 UKF 增广**单个标量** LiDAR depth bias b（random walk），Monte Carlo 显示旋转状态 RMSE/一致性改善。局限：(i) 纯高保真仿真，无真实硬件材料物理；(ii) bias 是**全局限标量**而非绑定目标表面的空间结构场；(iii) 服务于视觉-激光融合，不研究 nominal CAD mismatch 本体。
- 获取状态：**verified-actual-page**（摘要+第 8 节全文）。

#### A20. Spacecraft Coatings Optimizing LiDAR Debris Tracking and Light Pollution Impacts
- 作者：（航天器涂层实验研究）
- 年份：2023｜出处：arXiv:2311.13108
- URL: https://arxiv.org/pdf/2311.13108v1.pdf
- 分级：ADJACENT（材料测量层）
- 与 claim 关系：②——NIRT 涂层在 1064 nm 的反射率可调实验，证明航天器涂层选择直接改变 LiDAR 返回；不到位姿层。
- 获取状态：claim-only（摘要/结果片段）。

#### A21. Photometric and Spectral Characterization of Spacecraft Materials With Application to Lunar Trailblazer
- 作者：（多作者）
- 年份：2026（在线 2025-03）｜出处：Earth and Space Science (AGU)
- DOI/URL: https://doi.org/10.1029/2025EA004732
- 分级：ADJACENT（材料 BRDF/光度实测）
- 与 claim 关系：②——实测"bare aluminum、MLI、solar cell 是 shiny 材料，暗漫反射+极强前向/镜面分量；MLI 后向反射仅 0.05"，为 MLI/太阳翼镜面物理提供独立测量依据；不涉及 LiDAR 位姿。
- 获取状态：claim-only（正文片段）。

#### A22. 面阵激光雷达在空间站对接场景中的探测仿真与点云匹配研究（Research on focal plane arrays lidar simulation and point cloud matching in space station docking scenarios）
- 作者：（中国，红外与激光工程）
- 年份：2025｜出处：红外与激光工程 / Infrared and Laser Engineering，DOI 10.3788/IRLA20250134
- URL: https://www.spacejournal.cn/hwyjggc/article/doi/10.3788/IRLA20250134
- 分级：ADJACENT
- 与 claim 关系：②⑥反向参照——为简化**统一把航天器表面视为朗伯体、ρ=0.4**，系统误差源只列发射角/阵列/畸变/时间抖动/首光子误差；动态权重非线性精配准较 ICP 精度+25%。说明国内仿真路线同样不建模材料相关结构化偏差。目标天和核心舱，单光子面阵仿真。
- 获取状态：**verified-actual-page**（中文正文多段）。

> 文献量合计：0 DIRECT + 6 GENERAL + 22 ADJACENT = **28 篇**（落在 20–30 区间）。

---

## 3. Citation Chaining 记录（以 EPOS-Lid 为种子）

### 3.1 前向（EPOS-Lid 引用了谁）——已实际读取 EPOS-Lid 与 A1 的参考文献表

EPOS-Lid 参考脉络（重点节点，书目经原文参考文献表核对）：

| 节点 | 文献 | 与候选问题关系 | 处理 |
|---|---|---|---|
| 方法主干 | Renaut VISAPP 2023（smoothed NDT 原点，=A2）；Renaut RS 2023（=A1）；Renaut TAES 2025 CNN init（=A3）；Renaut Acta 232 2025 PointNet++（=A4，lidar simulator 细节出处 [20]/[21]） | 本谱系全部把反射当 outlier/domain-gap，无 structured-bias 研究 | 全部精读，列 ADJACENT |
| 航天配准传统 | Opromolla Sensors 2015（=A7，multipath=随机 outlier）；Opromolla TAES 2017（=A8）；Opromolla & Nocerino IEEE Access 2019（=A9）；Liu Sensors 2016 (10.3390/s16060824)；Yin Sensors 2018 (10.3390/s18041009)；Guo JGCD 2021（=A13）；Tecchia et al. AIAA SciTech 2025-1416（point correspondences 比较）；Ruel JFR 2012 TriDAR (10.1002/rob.20420)；Li/Wang/Xie ASR 2019 63:1576（model-less SLAM）；Martínez Acta Astro 2017 139:165（ToF 火箭上面级） | 全部为算法/仿真，噪声零均值假设，无材料结构偏差 | A7/A8/A9/A13 入表；其余（Liu2016/Yin2018/Tecchia2025/Ruel2012/Li2019/Martínez2017）为链上节点，**未入 28 篇正表**（相关度不足或纯书目 claim-only），在此登记 |
| 仿真/材料 | Brazeal Sensors 2021 21:4722（Livox Mid-40 Risley 棱镜观测模型）；Phong 模型 [55][56]；**Nakajima = A10 为材料反射率基线来源 [59]**；domain randomization [44]/[58] | 材料只进入仿真器随机化，不进入真实残差分析 | A10 入表 |
| 数据集对照 | SPEED/SPEED+/URSO/SwissCube/DLVS3/CubeSat-CDT（视觉）；OSIRIS-REx OLA flash lidar；Jena-Optronik RVS3000；MEV Pyrak&Anderson 2022 | 说明公开真实 LiDAR 航天位姿数据集此前为空白 | 背景，不入表 |

### 3.2 后向（谁引用了 EPOS-Lid / A1）——Semantic Scholar/出版商页面检索

- **Kim & Myung, IEEE TAES 2026（=A17）**：外部团队用 EPOS-Lid 做配准算法基准（Table V），只比 mm/deg 精度，未提出材料-结构偏差问题。verified via Semantic Scholar。
- **Renaut 自引延续**：*Minimal Three-Dimensional Increments: Invariant Filtering for Space Rendezvous Pose Estimation*, JGCD 2026, DOI 10.2514/1.G009373（滤波方法，引用 A1；与材料偏差无关，登记不入表）。
- ISPRS Annals 2023 X-1-W1:115（LDAR 自主操作相对位姿，纯仿真，引用 A1，登记不入表）。
- A1（smoothed NDT RS2023）Semantic Scholar 显示被引量级为个位数到十余次，被引文献以航天器配准算法/综述为主，**未发现任何一篇把 MLI/多径残差结构与系统 pose bias 挂钩**（逐篇查看被引标题/片段）。
- Wang 2019（A6）被引约 11 次（Exaly/Semantic Scholar），被引文献为各类航天器 ToF/视觉位姿方法，均沿用"MLI→噪声/离群→鲁棒剔除"范式，无翻案为 systematic 的工作。

### 3.3 链结论
EPOS-Lid 的**前向**所有相关节点共享同一误差哲学：材料反射 = outlier / domain randomization / 滤波剔除；**后向**使用者（含 2026 最新 TAES）只做算法基准。整条链上没有任何节点提出"结构化 mismatch → 系统 pose bias"，且 A1 Discussion 那句 CAD-mockup mismatch 猜测在随后三年（A3/A4/A5）始终未被本团队展开——候选问题在该数据集自己的文献生态中是**明确未被占据的空位**。

---

## 4. General Robotics Kill 结果

按任务要求执行 6 条非航天检索线：

| 检索线 | 检索式要点 | 结论性文献 | Kill 判定 |
|---|---|---|---|
| 反光金属物体 | `automotive lidar shiny reflective metallic object systematic range bias point cloud registration` | G4、white paper arXiv:2309.01346（车漆反射率）、Sensors 24(2):378（表面颜色对测距影响，含 shiny silver） | 材料相关**测距层**偏差证据充分，但无人把它接到对已知 CAD 模型的刚体配准偏差上 |
| 玻璃/镜面/多径 | `glass mirror multipath lidar systematic depth error bias localization mapping correction` | G5、G6、arXiv:2406.10494（Plane-SLAM 反射检测/利用）、Applied Sciences 13:2908（镜面物体导航行为实验）、Cartographer_glass、USENIX Security mirror spoofing | 主流范式 = **检测并去除/利用反射面**，或研究安全欺骗；不研究"未被去除的结构化残差使刚体位姿产生有偏估计" |
| 入射角/表面相关测距偏差→配准 | `lidar incidence angle dependent range bias surface material scan matching error model` | **G1 Laconte 2019（命中 GENERAL 机制链）**、Wiley phor.12460 各向异性误差滤波、Sensors-25-04748 入射角与 ICP 拟合精度 | **唯一在一般意义上打通"表面/几何相关非零均值测量偏差→配准/定位系统偏差→物理建模校正"闭环的工作**。GENERAL_PRIOR_ART_COVERAGE 风险集中于此，但机理/任务双不同（见 G1 划界） |
| 结构化 CAD-to-scan 残差 | structured residual CAD-to-scan mismatch | ISPRS PC2Model benchmark（建筑/工业）、PLOS ONE 离群点去除 | 非航天 CAD-to-scan 关注制造偏差/数字化对比，不研究传感器材料物理导致的系统性配准偏差 |
| 反光材料与检测 | `LiDAR object detection reflective material bias` | G4、PMC10147061 动态工况汽车 LiDAR（白车/黑车强度差） | 检测/强度层，与位姿估计无关 |
| 配准偏差理论 | `ICP registration bias anisotropic heteroscedastic noise theory` | **G3 IMLP（零均值各向异性高斯的最精细形式）**、GICP、Maier 2011 各向异性加权 | 概率配准理论全部建立在**零均值**假设上处理方差结构；非零均值结构化偏差项在配准理论中恰是空白——这从理论侧支持候选问题 |

**General Kill 总结论**：存在一条 GENERAL 机制先例（G1，辅以 G2/G6），说明审稿人可能主张"surface-dependent bias→registration bias 已知，换航天器数据即可"，构成 **HIGH_PRIOR_ART_RISK（但非 STOP）**。其不能直接 kill 的根本原因有三：(1) 物理不同——G1 是朗伯面回波波形峰偏移，候选问题是镜面双反射 ghost、MLI 褶皱导致的整片表面消失/错点、薄结构 mixed-pixel；(2) 估计对象不同——G1 是自车 scan-to-map 里程计漂移，候选问题是目标 scan-to-nominal-CAD 的物体级 6-DoF 位姿与**可辨识性退化**（对称目标 + 结构化残差的耦合是全新点）；(3) 偏差坐标系不同——G1 偏差是传感器坐标系下 (d,θ) 函数，候选问题要求证明残差结构绑定目标本体、在重复 aspect/range 下空间复现。**只要论文把贡献严格限定在这三点交集，GENERAL 文献不构成覆盖。**

---

## 5. 固定 8 行 PRIOR-ART CLAIM MATRIX

| # | Claim | Direct prior art（航天） | General prior art（非航天） | Status |
|---|---|---|---|---|
| ① | Real spacecraft LiDAR exhibits **structured** model mismatch（vs nominal CAD，存在有空间组织的残差结构，而非散点 outlier） | 无。A1/A3/A4/A5 仅展示/提及 MLI 反射点、ghost、表面消失现象（Level A），A4 给出实-仿 Chamfer 4.6 cm 但未对 nominal CAD 做残差结构刻画；A6 明确称其为 non-systematic | G5/G6 证明多径/眩光伪影在通用域有物理结构，但非"对模型的 mismatch 场" | **OPEN**（现象被反复看见，"structured mismatch field"从未被提出/刻画） |
| ② | Mismatch is **surface/material dependent**（MLI/太阳翼/薄结构各有不同偏差签名） | A10（5 类材料 BRDF+测量误差-强度相关，仿真层）、A1/A3（MLI/太阳翼高反射定性）、A20/A21（材料反射率实测） | G4（ill-reflecting 测距退化）、G1（入射角依赖） | **PARTIAL**：测量/仿真层材料依赖已 COVERED；"材料类别→对 CAD 的残差签名差异"OPEN |
| ③ | Mismatch is **spatially repeatable**（同一 aspect/range 下残差空间模式稳定复现） | 无。航天文献无任何重复轨迹残差复现性分析 | G1（偏差给定轨迹 repeatable，可预测弯曲方向）——通用域旁证 | **OPEN**（连通用域也只到轨迹级repeatability，目标本体绑定的空间残差复现无人做） |
| ④ | Mismatch induces **systematic pose bias / identifiability degradation**（随机噪声解释不了的刚体位姿系统偏差） | 无。A1 仅一句未验证猜测且归因混淆（标定 vs CAD mismatch）；A7 把多径当随机 outlier；A6 明确 non-systematic；A19 只在纯仿真里加标量 bias state | **G1（测距偏差→可预测 localization drift，闭环证明）、G2（视角→voxel 配准系统误差解析模型）** | **PARTIAL（最高风险行）**：一般机制链已被证明存在；航天器物体级 6-DoF/可辨识性层 OPEN。论文必须引用 G1/G2 并划界，否则被批"已知机制换数据" |
| ⑤ | Mismatch **varies with aspect/range**（随观测方位角/距离调制） | A1（MLI 非正交时消失/错点，定性 aspect 依赖）、A4（距离影响点密度/质心） | G1（bias 是 d,θ 显式函数） | **PARTIAL**：aspect 依赖现象有定性记录；"aspect/range→pose bias 调制规律"OPEN |
| ⑥ | **Nominal rigid model is insufficient**（名义刚体 CAD 模型从根本上不足以解释观测，需要显式 mismatch 层） | 无。A1 猜测 CAD-mockup mismatch 但未与标定分离；A4 用随机 deformation augmentation 绕过 | G3（主流配准假设零均值各向异性高斯，恰是候选问题声称不足的模型，反向支撑动机） | **OPEN**（无人形式化证明 rigid CAD + 零均值噪声模型对真实航天器 LiDAR 不充分） |
| ⑦ | Physical mismatch can be **parameterized**（偏差可用物理参数化模型描述：材料/几何/aspect 的低维参数） | A10（BRDF/Phong 参数化到仿真测量层）、A19（标量 random-walk bias state，仿真） | **G1（闭式波形 e(d,θ)+2 标度因子，物理参数化样板）**、G6（学习多径校正场） | **PARTIAL**：参数化方法论 GENERAL 已示范；航天器多物理（镜面多径/褶皱/薄结构）耦合参数化 OPEN |
| ⑧ | Correcting/modeling it **improves pose**（显式建模/校正结构化 mismatch 后位姿精度/可辨识性提升） | A6（滤波+trimmed ICP 提升 MLI 目标位姿，但以 non-systematic 立场）、A19（标量 bias state 改善旋转 RMSE，纯仿真） | **G1（去偏差→漂移下降，闭环）**、G6（多径校正→深度改善） | **PARTIAL**："校正有益"在通用域与仿真中成立；真实航天器上"结构化 mismatch 建模→rigid pose 收益"OPEN——这正是候选问题的实验落点 |

### 矩阵汇总
- **OPEN（真正空缺）**：①、③、⑥；④ 的航天器层（物体级 pose bias + 可辨识性）。
- **PARTIAL（上层已覆盖、本问题层空缺，需精准划界）**：②、⑤、⑦、⑧，以及 ④ 的一般层。
- **COVERED**：无任何一行被完全覆盖；**无任何一行触发 STOP_PRIOR_ART**。
- 最脆弱行：**④**（GENERAL 侧 G1/G2 已证明一般机制）；最坚固行：**③ 与 ⑥**（空间可复现性、rigid-model 不足的形式化在航天与通用域均无人做）。

---

## 6. 对候选问题的 G1 建议（Novelty Positioning）

1. **可以继续（G1 pass with conditions）**，但论文 Introduction 必须出现一个显式的"与 Laconte 2019 / Rife 2024 区别"段落：波形入射角偏差（传感器-表面交互、Lambertian、scan-to-map 漂移）vs 航天器特有组合物理（MLI 褶皱双反射、太阳翼镜面、薄结构 mixed-pixel、表面整片缺失）+ scan-to-nominal-CAD 物体级 6-DoF + 对称目标可辨识性耦合。
2. 主张必须落在机制链 **structured residual field（①③）→ rigid pose bias/identifiability（④）**，且用 EPOS-Lid 6 条真实轨迹做**同 aspect/range 重复观测下残差空间复现性**证据——这是所有现有文献（包括 DLR 自己的 A1/A3/A4/A5）都没做的一步，也是最难被 GENERAL 文献覆盖的一步。
3. 主动引用并区分 A1 Discussion 的 CAD-mockup mismatch 猜测、A6 的 non-systematic 立场、A7 的随机 outlier 仿真范式、A19 的标量 bias state——把它们写成"现有处理把该现象当随机/标量/标定问题，本文证明其为绑定目标本体的空间结构项"，既诚实又直接抬高贡献。
4. **红线**：若结果只停在"MLI 区域残差更多/残差比例与 pose error 相关/ghost 影响配准"，则分别落入 Level A STOP 与 generic reliability，不新颖；必须展示残差场的空间组织、跨轨迹复现、以及去掉/加入该结构项后 pose 估计系统偏差与 Fisher/可辨识性的变化（⑧的真实数据闭环）。

---

## 附：检索与获取可靠性说明
- 所有 URL/DOI 均来自实际检索返回；A6（IEEE Access 全文）、A8/A9/A13（出版商页）等因 robots 限制或付费墙未能读全文，已逐篇标注 **claim-only**，未臆造其内容；关键结论仅建立在多源摘要交叉验证或他引全文转引之上。
- 未使用任何模型记忆编造文献；被排除的低相关命中（科普博客、非航天 SLAM、光伏巡检、小天体/着陆 LiDAR、地球科学 LiDAR 标定等）不计入 28 篇正表。
