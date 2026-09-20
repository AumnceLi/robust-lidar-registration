# GLOBAL_NUISANCE_AUDIT.md — 去除全局 nuisance（Rescue Audit §5–§6）

- 日期：2026-09-09　数据：VI 全部 501 scans，pooled 点数 **5,026,085**；拟合用固定种子 42 的等量子样本 300,600 点，诊断在**全部点**上计算。
- 硬约束：所有 nuisance 参数 **501 scans 全局共享**（绝不逐帧拟合）；复杂度冻结为 1 标量 range + 6-DoF SE(3) + 1 标量 scale = **8 DoF**，禁止任何高阶形变。
- 诊断指标与已冻结 K1 完全一致（24 patch 下中位数 unsigned residual、跨帧 lag-1 patch-rank Spearman、similar-aspect<30° Spearman）；脚本 `scripts/m1_nuisance.py`，数值落盘 `cache/rescue/nuisance_diagnostics.csv`、`nuisance_params.json`。

## 1. 拟合到的全局 nuisance 参数（全局唯一，非逐帧）

| 模型 | 参数 | 数值 |
|---|---|---|
| N1 单一 range offset b_r | 沿 lidar 视线标量 | **+58.33 mm** |
| N2 单一共享 SE(3) | 平移 t (mm) / 旋转 | t=(45.67, −0.96, −5.76)，‖t‖=**46.04 mm**，**2.414°** |
| N3 单一 isotropic scale s | 相对 nominal CAD | s=0.96558，即 **−3.442%**（实物比标称小约 3.4%） |
| N4 联合 (b_r,ΔT,s) | 8-DoF joint Gauss-Newton（12 步，AtA cond≈43–46） | b_r=**+330.6 mm**，s=1.0635（**+6.35%**），t=(−174.84,1.96,−4.39) ‖t‖=**174.9 mm**，2.576°；法向 RMS 98.3→63.3 mm |

> N4 内部存在明显的参数互相抵消（range +331 mm、scale 符号与 N3 相反且达 +6.35%、平移 175 mm），是"用平滑全局场去拟合结构化残差"的典型过拟合征兆；下面的结构诊断证实了这一点。

## 2. 去除前后结构诊断（核心表）

| variant | signed mean (mm) | unsigned median (mm) | **24-patch spread std (mm)** | worst/best ratio | **lag-1 rank Spearman** | **similar-aspect Spearman** |
|---|---:|---:|---:|---:|---:|---:|
| **raw** | −38.19 | 63.62 | **21.44** | 3.62 | **0.929** | **0.833** |
| N1 range (+58mm) | −20.09 | 63.99 | 16.22 | 1.95 | 0.911 | 0.805 |
| N2 shared SE3 | −20.84 | 71.55 | 18.13 | 2.21 | 0.914 | 0.809 |
| N3 scale (−3.44%) | −23.84 | 64.41 | **15.10** | 2.23 | 0.907 | 0.786 |
| N4 combined (8-DoF) | **−0.87** | 34.76 | **51.60 ↑** | 8.95 ↑ | **0.943 ↑** | **0.873 ↑** |

参考地板：model 自最近邻间距 d_nn=8.11 mm；K1 已证空间置换 null 的 persistence≈0。

## 3. 判定推理

1. **三个最简全局模型都只能解释一部分全局内缩，且无法消除空间结构。**
   - signed mean：−38.2 → −20～−24 mm（仅消除 38%–48%）；
   - patch spread：最优（N3 scale）也只把 21.44→15.10 mm（−30%），仍是采样地板 8.1 mm 的 **1.86×**；
   - 跨帧空间持续性几乎不动：lag-1 0.929→0.907～0.914，similar-aspect 0.833→0.786～0.809，距离 null≈0 极远。
2. **最强的联合全局模型 N4 把"全局均值"清零（−0.87 mm），代价是把"局部结构"显著放大**：patch spread 21.44→51.60 mm（×2.41）、worst/best 3.62→8.95、lag-1→0.943、similar-aspect→0.873。它需要 range/scale/SE3 三者大值互相抵消（且 scale 符号与独立 N3 相反），说明残差里**不存在**一组自洽的全局刚体/尺度/距离参数；全局模型为压低均值而把结构化差异转嫁成了更剧烈的局部空间场。这本身即"结构非全局"的证据。
3. 结论按 Rescue Audit §6：去除任何合理全局 nuisance 后，**structured patch effect 不趋于 0**（持续性维持 0.79–0.94，局部 spread 最低仍 15 mm 量级）。

## 4. Nuisance Gate 结论

> **不触发 STOP_GLOBAL_NUISANCE —— 结构化失配在全局 range/SE3/scale nuisance 去除后依然明显存在，继续进入 M1–M4。**

为使后续机制结论对 nuisance 稳健（保守），下游 objective 分析同时在三套点云上进行：
- **raw**（未校正）；
- **scale**：最简约、物理可解释、真正降低局部 spread 的 N3 单标量校正（−3.44%）；
- **combined**：最大化全局解释（清零全局 signed mean）的 N4 8-DoF 校正。
若 objective 偏置在三套点云上方向一致、显著超过 self/null，才认定其非全局 nuisance 产物。

## 5. 与 prior art 的关系
Choate & Rife (ION GNSS+ 2024) 的人因矢量场环路把"全场同向=坏配准、上下反向=标定/尺度"作为**人工**第一步剔除；本节正是把该步骤**自动化、定量化**（N1–N4），并走到其未到达的结论：剔除/拟合完全局可解释项后，残余结构仍在，下一步检验它是否使刚性 6-DoF 目标在真姿态处非平稳。

## 6. 复现
`python scripts/m1_nuisance.py`（约 40 s；输出本表 CSV/JSON 与 `cache/rescue/corr/{scale,combined}/corr_XXXX.npz`）。
