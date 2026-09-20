# Round 3 Changes Report — 投稿前定点收尾

**日期**: 2026-09-13
**范围**: 6张主图定点修正 + 数据精简 + 中文文件说明
**原则**: 保留V2版式与配色，冻结数据/方法/统计不变，只做外观/标签/溯源修正

---

## 改动总表

| # | 图 | 改动项 | 类型 | 说明 |
|---|-----|--------|------|------|
| 1 | Fig1 | Estimated pose节点内容改为 T̂=(R̂,t̂) | 标签 | e_t,e_R移到下游独立标签"Reference-relative evaluation" |
| 2 | Fig1 | 绿色箭头终点落在ICP节点边界 | 外观 | 不穿过"ICP with rematching"标题 |
| 3 | Fig1 | ICP节点改为抽象配对点+迭代符号 | 外观 | 不再用与Query scan相同的点云缩略图 |
| 4 | Fig1 | 底部移除"JᵀWδ: gradient" | 标签 | 解释移入caption |
| 5 | Fig1 | 横向留白收紧、缩略图略放大 | 外观 | COL_GAP 10→7mm, M_LEFT 12→10mm |
| 6 | Fig2 | 新增provenance.md+csv | 溯源 | x轴/残差来源、8bin边界/统计、patch映射、废弃版本说明 |
| 7 | Fig2 | 热图加x轴标签"Patch ID" | 标签 | 此前缺失 |
| 8 | Fig2 | 色条标签"Residual magnitude (mm)"置于色条下 | 标签 | 与热图x标签分开 |
| 9 | Fig2 | 下排三图加(c)(d)(e)面板编号 | 标签 | 与Patch 3/20/8短标题并存 |
| 10 | Fig3 | 散点径 s=13→9.5 | 外观 | 保持对比，不删点不抖动 |
| 11 | Fig3 | 面板编号改为(a)(b)(c)(d)带括号 | 标签 | 与Fig5对齐 |
| 12 | Fig3 | ECDF末样本后沿y=1延到160° | 外观 | 两图共享x右边界160° |
| 13 | Fig3 | caption补FO/FD全称+方向误差定义+有效n+零向量规则 | 标签 | VI=development, III=secondary |
| 14 | Fig4 | (d)ylabel改为"Translation coherence proxy η_t" | 标签字段名 | 去掉"loss"，caption说明非损失函数/通用阈值 |
| 15 | Fig4 | (a)x/(b)y剂量轴改用symlog(明确linthresh) | 坐标 | (a)linthresh=1.0mm, (b)linthresh=0.05°; 0刻度不在正对数位置 |
| 16 | Fig4 | 浅线核实为GA/GB/GC各condition median，保留 | 核实 | caption写明浅线/深线/阴影含义（阴影=min-max范围非CI） |
| 17 | Fig4 | (d)D1–D5图例移到panel外上方 | 外观 | 不压η_t≈1数据点 |
| 18 | Fig5 | 四panel加短标题 | 标签 | Translation error/Rotation error/Paired translation benefit/Paired rotation change |
| 19 | Fig5 | comparison图例移到两行之间空白 | 外观 | figure-level bbox，不压数据不压上排x标签 |
| 20 | Fig5 | 编号统一左上(a)(b)(c)(d) | 标签 | 与标题并存 |
| 21 | Fig5 | caption重写：统计层次三分+coverage正确分母+II跨零 | 标签 | marginal/IQR/paired/bootstrap CI明确区分 |
| 22 | Fig6 | 加共享图例"Gray: reference-aligned scan; color: estimated alignment" | 标签 | 顶部空白带，不压点云 |
| 23 | Fig6 | 确认无orthographic调试字 | 核实 | 上轮已删，本轮确认无残留；相机参数留config+caption |
| 24 | Fig6 | 共享显示范围：Q_ref+三方法并集分位+5%余量 | 外观 | 三方法同范围同缩放，禁止逐方法autoscale；界外稀疏尾打印计数 |
| 25 | Fig6 | 比例尺移到框底空白，按坐标+投影实算mm/px | 外观 | 全景IV278=3.12mm/px, II505=2.82; 局部IV278=1.25, II505=0.65 |
| 26 | Fig6 | inset点径再小、灰参考alpha增强 | 外观 | ref 0.22/result 0.28, 灰alpha 0.35→0.50 |
| 27 | Fig6 | case_selection.csv补齐support/初始化/C矩阵/选帧依据/on_bound | 溯源 | II505 on_bound=1如实记录，不称协议错误 |
| 28 | 全局 | 删除冗余临时文件 | 精简 | recompute_figure2_bins.py、预览PNG、重复.txt等 |
| 29 | 全局 | 新增中文文件说明_FILE_GUIDE.md | 文档 | 逐文件说明+最小重建集合+可选素材区分 |

---

## 类型说明

- **纯外观**: 仅改布局/点径/箭头/留白，不涉及任何文字含义或数据
- **标签/字段名**: 改图面文字、轴标签、图例文字、caption措辞，不改数据
- **坐标**: 改坐标轴刻度方式（如symlog），数据点不变
- **核实**: 查证已有内容是否正确，确认后保留或写明
- **溯源**: 新增文档记录数据来源与版本
- **真实统计变化**: 无（本轮所有数值锚点与第二轮完全一致，verify_all仍ALL PASS）

---

## Fig2 上轮已修说明（本轮不回退）

审核者所见的 Fig2 0–0.6m x轴 / 310mm残差曲线是**第二轮之前已废弃的错误版本**。
第二轮已修复为：x=VI sensor range 8.7465–14.8022m，逐scan patch-median，patch3平坦26.7–31.6mm。
本轮仅补溯源文档与标签，**未改动任何数值**。

### Fig2 before/after 数值对照

| 指标 | 废弃版本(审核者所见) | 当前正确版本 |
|------|---------------------|-------------|
| x轴范围 | 0–0.6m（逐点局部量） | 8.7465–14.8022m（帧级vrange） |
| 观测单位 | 逐点（bin_count 30万级） | 逐帧（patch3/20 n=501, patch8 n=484） |
| patch3中位范围 | ~30→314mm（上升趋势） | 26.67–31.62mm（平坦） |
| 残差定义 | 法向投影\|signed\| | 3D欧氏范数 ‖aligned−model[nnidx]‖ |
| 输入哈希 | 同冻结数据（未换版本） | 同冻结数据 |

> 冻结数据与输入哈希未变，错误出在派生计算脚本的聚合层级，第二轮已修正并通过0.0mm容差一致性断言。

---

## 验证结果

- `verify_all_v2.py`: **ALL CHECKS PASSED ✓**（含Fig2 bin与V1一致性、29+数值锚点）
- `reproduce_figure6_gate.py`: **PASS**, max |Δe_t| = 1.42×10⁻¹⁴ mm
- `verify_figure6.py`: 26/26 PASS
- 所有受影响图重导出 PDF/SVG/PNG（600dpi，文字矢量嵌入，非截图）

---

## 第四轮微调（投稿前最后4项）

| # | 图 | 改动项 | 类型 | 说明 |
|---|-----|--------|------|------|
| 30 | Fig5 | (c) comparison图例与(a)x刻度重叠 | 外观 | hspace 0.55→0.75，图例bbox下移至(0.38,0.48)，落在两行间完全空白带，与VI/IV/II/III刻度和(c)短标题均有清晰间隙 |
| 31 | 全套 | 面板编号统一带括号 | 标签 | Fig4/Fig5/S1/S3由a/b/c/d改为加粗(a)(b)(c)(d)（S1到(c)、S3到(b)），与Fig2/Fig3一致；Fig6用列标题不加编号、Fig1流程图不加编号，保持不变 |
| 32 | Fig1 | 绿色箭头落点仍挨"rematching" | 外观 | 箭头改Z形路径拐到ICP节点**左上角**进入，加绿色小三角input port标记，完全避开居中两行标题 |
| 33 | Fig6 | IV278 Raw顶部散点贴上边框 | 外观 | 共享视口增加顶部额外余量+4%（TOP_EXTRA=0.04×y-range），两案例同规则；六面板xlim/ylim逐位相同断言通过；IV278 y上界0.755→0.835m，目标占比仍>70%；远距尾越界计数IV278=2/5000、II505=111/5000，全量点保留NPZ |

### 第四轮验证
- `verify_all_v2.py`: ALL CHECKS PASSED ✓
- `reproduce_figure6_gate.py`: PASS, max |Δe_t| = 1.42×10⁻¹⁴ mm
- 受影响图：Fig1/Fig4/Fig5/Fig6/S1/S3 重导出 PDF/SVG/PNG

---

## 未解决缺口（如实保留）

1. 无 .tex 源文件，无法编译论文；manuscript/ 为 ready-to-paste 英文文本
2. Fig4 RMS汇总值（7.95/7.70等）不在原始CSV，采用PDF Table3已发表中位数，e_t独立验证
3. Fig6 II505远距散点群（~2%显示点）在主图中用稳健分位窗裁剪以便可辨，全量点保留在NPZ，已如实说明
4. Fig6两案例ROI因场景不同未强制同部位（V2规范为"优先"），均在主体簇上
