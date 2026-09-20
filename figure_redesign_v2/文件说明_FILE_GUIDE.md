# figure_redesign_v2 文件说明

本文档按目录逐个说明保留文件的用途、是否重建必需、由哪个脚本生成或来源。
标记 **[必需]** = 最小可重建集合；**[可选]** = 参考/渲染素材/历史记录，不参与重建。

---

## 根目录

| 文件 | 说明 | 必需性 | 来源/生成 |
|------|------|--------|-----------|
| `README.md` | 项目总览：来源、图件清单、设计系统、构建命令、已知缺口 | [必需] | 手写 |
| `data_dictionary.md` | 英文数据字典：所有源/派生数据字段定义、单位、统计约定 | [必需] | 手写 |
| `文件说明_FILE_GUIDE.md` | 本文件，中文逐文件说明 | [可选] | 手写 |
| `checksums.sha256` | 全部交付文件 SHA-256 校验（不含自身） | [可选] | 构建脚本生成 |

---

## configs/ — 共享配置（全部 [必需]）

| 文件 | 说明 |
|------|------|
| `__init__.py` | Python 包标识 |
| `colors.py` | 方法色/标记/线型、轨迹色（VI蓝/IV橙/II青绿/III紫）、Fig6双色叠合色、comparison标记 |
| `figure_style.py` | 统一字体/字号/轴样式/面板编号/各图尺寸(mm)/保存函数 |
| `paths.py` | 所有冻结数据源路径、Table3案例、共同支持域计数、raw池计数、bootstrap块数、冻结场SHA256 |
| `camera_config.py` | Fig6固定2D正交投影(elev25/azim-60)、ROI中心/半宽、显示抽样(5000点/seed12345)、点径/透明度 |

---

## data/source/ — Fig6 必需输入（全部 [必需]）

| 文件 | 说明 |
|------|------|
| `figure6_case_IV278_scan.npz` | IV轨迹第278帧原始扫描（aligned点云+元数据），Fig6复现闸门输入 |
| `figure6_case_II505_scan.npz` | II轨迹第505帧原始扫描，同上 |

> 其余轨迹的全量扫描不复制入包，保留路径于 `configs/paths.py` 与 `manifests/source_assets.csv`。

---

## data/derived/ — 派生数据（全部 [必需]，由脚本从冻结数据计算）

| 文件 | 说明 | 生成脚本 |
|------|------|---------|
| `figure2_residual_stats.npz` | Fig2热图(6×24 block×patch中位残差)+帧级(501×24)+三条range-bin曲线统计(8bin median/IQR/n) | `compute_figure2_data.py` |
| `figure3_anchor_summary.csv` | Fig3锚点：每轨迹 ratio_pa/FO cos/FD cos 中位数 + n | `figure3.py` |
| `figure3_ecdf.csv` | Fig3(c)(d) FO/FD方向误差ECDF点 | `figure3.py` |
| `figure3_scatter_ecdf_source.csv` | Fig3(a)(b) 1456帧散点源数据（残差/位移/轨迹） | `figure3.py` |
| `figure4_matched_rms_cases.csv` | Fig4(c) Table3四案例数据（geometry/dose/RMS/e_t/ratio） | `figure4.py` |
| `figure4_phase_map.csv` | Fig4(d) α–η_t相图（30行聚合中位） | `figure4.py` |
| `figure4_table3_verification.csv` | Table3 e_t与dose_response.csv交叉核对 | `verify_table3.py` |
| `figure5_v2_bootstrap_ci.csv` | Fig5(c) 三对比×四轨迹 paired median + block-bootstrap 95%CI | `make_figure5.py` |
| `figure5_v2_rotation_iqr.csv` | Fig5(d) Patch+Huber−Huber 旋转变化 paired median+IQR | `make_figure5.py` |
| `figure6_case_IV278_C_matrices.npz` | IV278 三方法 SE(3) 校正矩阵 C + e_t/e_R | `reproduce_figure6_gate.py` |
| `figure6_case_II505_C_matrices.npz` | II505 同上 | `reproduce_figure6_gate.py` |
| `figure6_case_IV278_displacement.npz` | IV278 Q_ref/Q_method逐点坐标+参考相对位移（诊断） | `reproduce_figure6_gate.py` |
| `figure6_case_II505_displacement.npz` | II505 同上 | `reproduce_figure6_gate.py` |
| `figure6_case_IV278_display_indices.npy` | IV278 固定5000点显示抽样索引(seed12345) | `reproduce_figure6_gate.py` |
| `figure6_case_II505_display_indices.npy` | II505 同上 | `reproduce_figure6_gate.py` |
| `figureS1_cond_ecdf.csv` | S1(b) 逐轨迹条件数ECDF | `figureS1.py` |
| `figureS1_step_cond_source.csv` | S1(a) 预测vs实现步长+条件数源数据 | `figureS1.py` |
| `figureS1_switchrate.csv` | S1(c) 对应切换率（66帧有效） | `figureS1.py` |
| `figureS2_v2_stats.csv` | S2 初始化敏感性7等级×4轨迹统计 | `make_figureS2.py` |
| `figureS3_v2_gap_stats.csv` | S3 Est.Full差值+配对分布统计 | `make_figureS3.py` |

---

## figures/main/ — 主图（全部 [必需]，每图 PDF+SVG+PNG 600dpi）

| 图 | 尺寸(mm) | 说明 | 生成脚本 |
|----|---------|------|---------|
| `figure1.{pdf,svg,png}` | 180×95 | 机制流程图：Calibration+Registration两行，底部机制条 | `draw_figure1.py` |
| `figure2.{pdf,svg,png}` | 180×108 | VI残差结构：(a)分区+(b)6×24 Blues热图+(c)(d)(e)三条range-bin曲线 | `compute_figure2_data.py`+`draw_figure2.py` |
| `figure3.{pdf,svg,png}` | 180×110 | 局部机制：(a)(b)残差log-x vs位移线性+(c)(d)FO/FD方向ECDF | `figure3.py` |
| `figure4.{pdf,svg,png}` | 180×100 | 受控不匹配：(a)(b)D1/D5剂量响应+(c)Table3 matched-RMS+(d)α–η_t相图 | `figure4.py` |
| `figure5.{pdf,svg,png}` | 180×112 | 效果：(a)(b)边际误差+(c)paired forest+(d)旋转代价 | `make_figure5.py` |
| `figure6.{pdf,svg,png}` | 180×125 | 真实EPOS-LiDAR：2D正交双色叠合，IV278/II505，全景+细节+数值 | `plot_figure6.py`（需先跑gate） |

---

## figures/supplementary/ — 补充图（全部 [必需]）

| 图 | 说明 | 生成脚本 |
|----|------|---------|
| `figureS1.{pdf,svg,png}` | 预测步长+逐轨迹条件数ECDF+对应切换率 | `figureS1.py` |
| `figureS2.{pdf,svg,png}` | 初始化敏感性7等级×4轨迹（VI/IV零保留） | `make_figureS2.py` |
| `figureS3.{pdf,svg,png}` | Est.Full差值+trajectory×method分组箱线 | `make_figureS3.py` |

---

## manifests/ — 清单与溯源（全部 [必需]）

| 文件 | 说明 |
|------|------|
| `source_assets.csv` | 16项输入资产的路径+SHA256+描述 |
| `frame_roster.csv` | 4轨迹共同支持域帧数/raw池/覆盖率/块数/角色 |
| `figure_manifest.csv` | 9图的尺寸/脚本/数据源/描述映射 |
| `case_selection.csv` | Fig6 IV278/II505选帧溯源（median-neighborhood规则+support+on_bound+协议说明） |

---

## manuscript/ — 英文图注与文稿变更（全部 [必需]）

| 文件 | 说明 |
|------|------|
| `figure1_caption.md` ~ `figure6_caption.md` | 6张主图英文图注（未烘焙进图） |
| `figureS1_caption.md` ~ `figureS3_caption.md` | 3张补充图英文图注 |
| `figure_reference_mapping.md` | V1→V2图号/面板引用映射 |
| `manuscript_changes.md` | 文稿变更说明（Sec5.3 Fig4、Sec5.4 Fig6、Fig3 log轴、coverage） |
| `table3_move_note.md` | Table3→Supplementary Table S1迁移说明+四案例完整数值表 |

---

## originals/ — 原始参考输入（全部 [可选]，不参与重建）

| 文件 | 说明 |
|------|------|
| `Ast.pdf` | 论文PDF原件（16页，已核实标题一致），Table3来源 |
| `v1_figure1.png` ~ `v1_figure6.png` | V1六张主图，作为V2设计参考与before/after对照 |

---

## scripts/ — 构建与验证脚本（全部 [必需]）

| 文件 | 说明 |
|------|------|
| `compute_figure2_data.py` | Fig2数据计算：3D欧氏残差→帧内patch中位→vrange分8bin跨帧统计 |
| `draw_figure1.py` | Fig1绘制 |
| `draw_figure2.py` | Fig2绘制 |
| `figure3.py` | Fig3+数据计算 |
| `figure4.py` | Fig4+数据计算 |
| `figureS1.py` | S1+数据计算 |
| `make_figure5.py` | Fig5+bootstrap CI计算 |
| `make_figureS2.py` | S2+数据计算 |
| `make_figureS3.py` | S3+数据计算 |
| `plot_figure6.py` | Fig6绘制（2D正交投影+双色叠合） |
| `reproduce_figure6_gate.py` | Fig6复现闸门（冻结代码重算+断言+存C矩阵） |
| `verify_all_v2.py` | 统一数值核对（29+锚点+Fig2 bin一致性） |
| `verify_figure6.py` | Fig6渲染一致性26项检查 |
| `verify_table3.py` | Table3 e_t与dose_response交叉核对 |

---

## checks/ — 验证报告与日志（全部 [可选]，重建后可重新生成）

| 文件 | 说明 |
|------|------|
| `numerical_verification_report.md` | 统一数值核对报告（29/29 PASS） |
| `figure2_provenance.md` + `.csv` | Fig2数据溯源：x轴/残差来源、8bin边界/统计、patch映射一致性、废弃版本说明 |
| `figure4_table3_verification.md` | Table3核对详情 |
| `figure5_anchor_checks.txt` | Fig5锚点检查记录 |
| `figure6_render_check.md` | Fig6渲染一致性26/26检查 |
| `figure6_reproduction_gate.log` | Fig6复现闸门日志（max Δe_t=1.42e-14mm） |
| `scientific_issues_resolution.md` | 两个科学口径问题：Fig4错案根因+Fig6选帧溯源 |

---

## assets/renders/ — Fig6无标注渲染素材（全部 [可选]）

12张PNG：6张无标注全景（IV278/II505 × Raw/Patch/Full）+ 6张ROI局部放大。
用于论文排版时单独引用或二次标注，不参与主图重建。

---

## 最小可重建必需集合

重建全部9张图所需的最小文件集：
- `configs/` 全部5个文件
- `data/source/` 2个扫描NPZ（仅Fig6需要）
- `data/derived/` 全部派生CSV/NPZ/NPY（或从冻结数据重算）
- `scripts/` 全部14个脚本
- `manifests/case_selection.csv`（Fig6选帧）
- 冻结数据源（在 `D:\doubao\` 下，路径见 `configs/paths.py`）

**重建命令**：
```powershell
cd D:\doubao\figure_redesign_v2
python scripts\reproduce_figure6_gate.py    # Fig6闸门（必须先通过）
python scripts\compute_figure2_data.py       # Fig2数据
python scripts\draw_figure1.py
python scripts\draw_figure2.py
python scripts\figure3.py
python scripts\figure4.py
python scripts\make_figure5.py
python scripts\plot_figure6.py
python scripts\figureS1.py
python scripts\make_figureS2.py
python scripts\make_figureS3.py
python scripts\verify_all_v2.py              # 验证
```

## 已删除的冗余/临时文件（第三轮精简）

- `scripts/recompute_figure2_bins.py` — 与 `compute_figure2_data.py` 重复的临时脚本
- `checks/figure2_preview.png` — 临时预览图
- `checks/_preview_r3.png` — Fig6临时预览
- `manuscript/figure5_caption.txt` — 与 .md 重复的旧格式
- 各轮 `_v2` 后缀文件已统一重命名为标准名
