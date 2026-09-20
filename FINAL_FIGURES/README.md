# 最终科研图交付

Figure1–Figure8 均已输出矢量 PDF、矢量 SVG、600 dpi PNG、英文 caption 草稿和可追溯 notes；定量图另附绘图数值 CSV。全部图宽 178 mm，适用于双栏排版。85 mm 单栏尺寸模板保存在 master_style 中。

推荐先看 Figure7（工程结果）、Figure4（理论与证据边界），再通读 figure_manifest.md。PDF 是投稿用矢量主文件，PNG 用于预览。本轮已完成编辑审阅后的视觉精修：Figure1 机制总图重画，Figure5 按 mismatch regime 重构，Figure6 聚焦 DirectBias 风险，Figure7 使用 paired-improvement forest plot，Figure8 将数字矩阵移到补充数据表并放大 phase map。

## 复现

在项目根目录执行：

```powershell
python FINAL_FIGURES/build_all_figures.py
python FINAL_FIGURES/verify_figures.py
```

脚本只读取冻结结果，不运行配准、不训练、不调参。源文件 SHA256 记录在每张图目录中，构建结束和验证阶段均检查不变。

## 必须随图保留的科学边界

- Figure4：合成 CSV 未保留逐条件解析的 JᵀWδ 向量，因此使用明确标注的冻结有限差分梯度诊断量，不能在论文中偷换为精确解析投影。梯度范数依赖冻结的 m/rad 坐标尺度。
- Figure4 的 96 个合成条件支持更强的梯度关联；VI 单轨迹的相关排序相反，已记录于 notes。不能写成普遍规律。
- Figure6/7：III 使用原确认性 371 个 in-support 帧，未混入 DBS 汇总表中的 1302 帧全量补充口径；III DBS 明确 N/A。
- Figure7：II Full 比 Raw 略差；Patch 的旋转也不是所有轨迹都改善。图中均保留。
- 误差棒按图注区分 IQR、现有 block-aware CI、跨几何范围，不能统一称为 95% CI。Figure7D 是逐帧配对 Raw-method 差的中位数与 IQR；Figure7A 仍显示各方法边际中位数，因此 II Full 的轻微恶化不会被掩盖。
- D2 完全部件缺失是 exploratory endpoint；部分冻结位移范数超过名义 300 mm，保留原值并注明 solver-bound，不能截成整齐的 300 mm。
- 校准/GT 不确定度未独立量化，不能补造误差预算。

## 主图与补充材料

八张现在具有明确分工：F1 概念机制，F2 真实 mismatch，F3 GT 非平稳性，F4 pose-active 理论，F5 robust falsification，F6 DirectBias 上限/风险，F7 最终 pose performance 与 III，F8 synthetic regime boundary。Figure8 的完整数值矩阵、p2l 细节、V 上 DBS 外支持结果、bootstrap 分布、calibration budget、B2-v2/Hessian damping 负面结果建议放入 Supplementary。

## 验证

299 项自动检查通过；已检查全部 PDF 的渲染和彩色/灰度总览。全部 PDF 精确为 178 mm 宽，普通单词文字最小 7.3 pt，主要 tick/legend 为 8 pt，轴标题为 9 pt，panel label 为 10 pt。qa/print_preview_178mm_96dpi 提供 673 px 宽的 1:1 参考预览。QA 详情见 qa/validation_report.md 和 qa/visual_review.md。作者仍应复核上述科学口径及最终选定期刊的具体提交要求。
