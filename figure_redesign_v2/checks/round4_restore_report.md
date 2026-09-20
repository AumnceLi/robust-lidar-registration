# 第六轮：恢复已通过表达 + 最终排版（2026-09-14）

## 1. 基线判定与本轮策略

- 上一轮交付目录 `figure_redesign_20260913` 经评估整体不如已认可的“(2) 版”。
  核查磁盘后确认：本机存在**两套相互独立的实现**——
  - `figure_redesign_v2`：脚本/产物带 v2 命名、含 `round3_changes_report.md` 与
    `verify_all_v2.py`，即用户所说“接近定稿”的 **(2) 版**，也是本轮唯一基线；
  - `figure_redesign_20260913`：从更早 V1 另起的一套（`plot_figure1–6`），把 v2
    已修复的问题带回（图 3 线性纵轴到 6000 mm、图 4 错误配对、图 5 缺方法图例、
    图 6 退回 mplot3d 密集色块、图 1 把 Full 画在估计位姿之后）。
- 本轮策略：**以 v2 为基线恢复图 3–6 的清楚布局，保留本轮新增的准确统计说明，
  只做局部修正**；不修改任何数据、不重新挑选案例、不改变统计口径来解决视觉问题。
- 新增**唯一可复现构建入口** `scripts/build_v2_all.py`：按固定依赖顺序重建六主图与
  三补充图，并串联三道校验，任一步失败即以非零码中止。这从流程上杜绝再次调用旧脚本
  或另一套配置。最终一次干净构建 `=== EXIT 0 ===`，且 `figures/` 下无任何 `_v2` 重复成品。

## 2. 逐图处理

| 图 | 本轮处理 | 结果 |
|---|---|---|
| Fig 1 | Node2 标题改为区分两种校正场 `μ_j (Patch) / μ_j(z) (Full)`；在行间**空白带**新增橙色虚线 Full 两阶段注记（stage 1 粗位姿→视角邻域查询→构造 corrected geometry→stage 2 ICP），虚线箭头汇入绿色 corrected-geometry 主干、在 ICP **之前**进入；Estimated pose 之后不出现任何 Full 箭头；聚类等参数移入图注。无文字遮挡、无越界 | 渲染+178mm 裁切确认 |
| Fig 2 | 沿用 v2（距离 8.75–14.80 m、8 等宽 bin、帧数 501/501/484、Patch 3 平坦 27–32 mm、teal 小点 markersize 2.5，不存在红点实心问题）；修正 (e) 子图编号与色条标签的避让；图注显式说明“无误差棒、无拟合/趋势线，浅色带=IQR 非置信带” | `verify_all_v2` ALL PASSED |
| Fig 3 | 沿用 v2：残差 RMS **对数横轴**、实际平移位移**线性纵轴**（28.6–378.6 mm），N=1456（VI501/IV156/II428/III371），FO/FD ECDF 0–160°（FD 26 帧>90°、max151.0°，FO 无>90°）；样本量与 FO/FD 定义保留 | 脚本锚点输出一致 |
| Fig 4 | **最高优先**。图沿用 v2 正确的 Table 3 四组配对、(a)(b) symlog、无遮挡示意框、紧凑布局；重写 `verify_table3.py` 增加 5% RMS 自动核验（见 §3）；废弃错误配对 35.9/36.7、65.5/51.9、9.7/10.7、18.2/15.6；D1–D5 形状图例独立成行，不再挤 “Appendage tilt (deg)” 轴标题 | ALL PASS（§3） |
| Fig 5 | 成品保存名由 `figure5_v2` 统一为 `figure5`（并清理 S2/S3 同类 `_v2` 名）；顶部五方法图例齐全，行间 comparison 图例独立、不遮误差棒；子图编号统一移到绘图区外；保留三层统计区分（marginal IQR / 配对 block-bootstrap 95% CI B=2000 seed42 / 旋转描述性 IQR）、coverage 正确分母与 II 的 Patch-vs-GV 跨零 CI [−8.49,+18.02] | 全部 anchor 自检 OK |
| Fig 6 | 恢复 v2 紧凑 2D 正交布局（elev25/azim−60、共享视口、主图虚线选区对应下方独立放大条、三方法一致渲染）；保留两行案例（IV278 Full 改善、II505 Full 退化说明适用边界）；点径/不透明度适度提升以加深灰色参考层（见 §5），固定点集/位姿/视角/缩放不变；`basin` 措辞改为 solve-path **safeguard**；逐点位移 d_i 定义入图注、诊断 npz 保留 | `verify_figure6` 26/26、gate PASS |
| S1–S3 | 随统一构建重建；成品名统一为 figureS1/S2/S3；编号位置校正；S3 连跑两次数值完全一致（确定性） | 见 §5 |

## 3. 图 4：Table 3 四组“5% RMS 匹配”自动核验（最高优先）

`scripts/verify_table3.py` 对每对配对做三项独立检查并落盘：
1. **e_t 对原始表核验**：从 `g_chain/G_GENERALITY/results/dose_response.csv`（form=ls）
   取最接近发表值的剂量，要求 |e_t_raw − e_t_pub| ≤ 0.002 mm；
2. **5% RMS 匹配**：rel = |RMS_A−RMS_B| / max(RMS_A,RMS_B) ×100%，断言 ≤ 5%；
3. **误差比**：按“较大/较小”重算并与发表值比对（容差 0.15）。

| 配对 | e_t A/B（raw, mm） | RMS A/B（mm） | RMS 相对差 | ≤5% | 重算误差比 / 发表 |
|---|---|---|---|---|---|
| GA · D1/D3 | 8.9285 / 0.9013 | 7.95 / 7.70 | **3.145%** | 是 | 9.91 / 9.9 |
| GB · D4/D3 | 0.0584 / 0.6206 | 4.06 / 3.97 | **2.217%** | 是 | 10.63 / 10.6 |
| GB · D4/D5 | 0.1839 / 1.5282 | 5.33 / 5.08 | **4.690%** | 是 | 8.31 / 8.3 |
| GC · D3/D4 | 0.9885 / 0.1161 | 3.75 / 3.80 | **1.316%** | 是 | 8.51 / 8.5 |

**VERDICT: ALL PASS（4/4）**。记录：`data/derived/figure4_table3_verification.csv`、
`checks/figure4_table3_5pct_check.log`。
口径说明（已写入图注与脚本）：原始 CSV 只存误差中位数、**不存 surface RMS 字段**，
RMS 采用论文 Table 3 已发表的条件中位数；e_t 则对原始表独立复核。配对严格取自冻结源、
未为放大倍率重新挑案例。

## 4. 图 6：on_bound 与 safeguard 的证据链

- **on_bound 来自日志+重跑双重核实，不是看图推断**：源运行表
  `FOLLOWUP_6_9/scripts/replay79_arms.csv` 中 II/order505 的 Full 为 `on_bound=1, iters=9`，
  IV/order278 的 Full 为 `on_bound=0, iters=37`；`reproduce_figure6_gate.py` 用冻结求解器
  **重跑** robust ICP，并把 e_t/e_R/**on_bound** 与归档逐项比对，最终
  max|Δe_t|=1.42e-14 mm、max|Δe_R|=1.78e-16 deg、on_bound 全部一致（PASS）。
- **机制与正名**：`g_chain/common/g_common.py` 中这是逐迭代对**累积步**的保护
  （平移 0.30 m、旋转 15°；`_basin` 返回 f=min(0.30/‖t‖,15°/‖r‖)，f<1 即把该步截到边界并
  提前 break、置 on_bound）。II505 Full 在第 9 次迭代累积旋转逼近 15° 触发提前停止。
  科学上应称 **solve-path step safeguard（求解路径步长保护阈值）**，并非已确定的
  “registration/ convergence basin”。门控记录与图注中的 “basin” 已全部改为 safeguard
  （仅保留一句“NOT a convergence basin”的否定说明）。
- **逐点位移定义**：d_i = ‖C·Q_ref_i − Q_ref_i‖·1000 mm（相对参考的逐点全向量位移），
  区别于点到模型残差与整体平移误差 e_t；d_i 作为诊断 npz 保留，视觉编码仍为
  灰参考层+方法色估计层双层叠加（不使用位移色条）。

## 5. 数值 / 渲染校验与点云可读性

- 三道校验随统一构建全部通过：`verify_table3` ALL PASS；`verify_all_v2` ALL CHECKS
  PASSED（bin 边界、各 bin 中位数、帧数 501/501/484、热图 6×24）；`verify_figure6`
  26/26（SE(3) 合法、metric==归档、displacement npz==C@Q_ref、2D 正交、共享 5000 点
  索引、无 mplot3d、无位移热图）。
- 图 6 点径/不透明度适度提升（仍为离散点、不成色块）：
  主图 reference s 0.10→0.13 / α 0.35→0.45，result s 0.13→0.16 / α 0.55→0.62；
  放大条 reference s 0.22→0.26 / α 0.50→0.58，result s 0.28→0.32 / α 0.55→0.62。
  三方法共用同一渲染规则、点集/位姿/视角/缩放/案例不变。
- 导出：每图同时输出 PDF（字体内嵌 Type42）、SVG（字体不转曲）、600 dpi PNG；
  主图原生宽度对应约 172–187 mm@600dpi，匹配 178 mm 排版。

## 6. 178 mm 印刷尺寸终检

`checks/make_print_proof.py` 在原生分辨率下裁切易重叠区并等宽复核：
- 图 4：Raw/Huber/Trim 线型图例与 D1–D5 形状图例各自独立成行，与 (b) “Appendage tilt”
  横轴标题清晰分离；(c) 四组配对与 ×倍率无遮挡。
- 图 5：(a)–(d) 编号在轴框外，不挡 VI 的 Raw 点与误差棒；顶部方法图例、行间
  comparison 图例均不遮数据；无右侧大片空白。
- 图 1：Full 注记框与 Query scan 标题分离、箭头在 ICP 前汇入，无越界。
- 图 6：放大条中灰参考层与方法色层及其错位在印刷尺寸下可辨、不融合成色块；
  主图虚线选区与放大条一一对应。
- 图 2/3：编号避让色条/标题，散点-对数轴与 ECDF 舒展可读。

## 7. 复现方法与产物

```powershell
cd D:\doubao\figure_redesign_v2
python scripts\build_v2_all.py     # 固定顺序重建 + 三道校验，EXIT 0 即通过
```
- 主图：`figures/main/figure1–6.{pdf,svg,png}`；补充图：`figures/supplementary/figureS1–S3.*`。
- 源数据、绘图脚本、插图素材（`assets/renders`）、点云/位姿/逐点位移 npz
  （`data/source`、`data/derived`）、渲染配置（`configs`）、构建与校验日志（`checks`）均保留。
- 图注：`manuscript/figure{1..6}_caption.md`（本轮补强 1/2/4/6）。

## 8. 口径与依赖说明

- v2 的图 2/图 5 复用 `figure_redesign_20260913\data\derived` 下的派生 CSV
  （`configs/paths.py::V1_DERIVED_DIR`），**该目录为依赖项，不可删除**；本轮未改动其中数据。
- 图 4 的 surface RMS 为论文 Table 3 发表中位数（原始 CSV 无该字段），e_t 已对原始表复核；
  这一区分在脚本、日志、图注中均明确标注。
- 图 6 未采用逐点位移色条（用户措辞为“若保留则需定义”，属可选项）；d_i 定义已备且 npz 保留，
  如后续需要色条可直接取用。
- 补充图 S3 为纯描述性中位数、无随机源，连跑两次结果逐位一致。
