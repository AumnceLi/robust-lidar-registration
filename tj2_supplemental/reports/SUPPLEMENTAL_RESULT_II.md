# SUPPLEMENTAL_RESULT_II.md — TJ2 补充外部确认性复现：Dataset II 结果（唯一一次 outcome-bearing test）

- 日期：2026-09-09（Asia/Shanghai）。
- 轨迹：**Dataset II（`epos_dataset_ii.zip`，89,932,451 B，zip SHA256 `3ba539894cdcc5e769fe7de9e74543a9e7bf61b9aeaecb503cd8de1e7555e52b`，1,253 帧，全成员 CRC 通过）**，在 `SUPPLEMENTAL_FROZEN_MANIFEST.yaml` 写死**之后**才下载点云。
- 冻结输入：`VI_ONLY_PREDICTOR_FROZEN.npz` SHA256 `8abcc82d…`（全程未改，结束复算一致），k\*=16，range_std=2.064280 m，**τ_support=0.4403305559611483 未改**，24 frozen patches，PCA normals k=16，FD 5mm/0.25°，盆地 ±0.30m/±15°，nuisance RAW/N1/N2/N3（N4 仅 stress）。未重拟合 predictor、未重拟合 α、未开发任何新 ICP/robust/NDT/neural/bias-correction。
- 前瞻锁定的主分析集：**IN_SUPPORT n=428**（outcome 阶段 `ext_predict_ii.npz` 复算 = 428，与 Phase-1 筛查**逐位一致**），3 个独立时间块 143–197(n=55)/238–510(n=273)/602–701(n=100)，命中全部 6 个 VI 朝向块。OUT n=825、ALL n=1253 仅作附录对照。
- 主 endpoint：**p2p translation-direction cosine**；p2l 仅 confirmatory secondary，不替代；magnitude 非 gate。

---

## 1. Primary：P3 非循环方向预测（VI-only frozen template + II GT 几何 + nominal CAD）

| 集合 | n | median cos | block-CI95 L=5 | **L=10** | **L=20** | frac cos>0 | vector-pairing p | magnitude Spearman |
|---|---:|---:|---|---|---|---:|---:|---:|
| **IN_SUPPORT (p2p, primary)** | **428** | **0.788** | **[0.719, 0.830]** | [0.688, 0.839] | [0.588, 0.844] | **1.000** | **0.0005** | 0.58 |
| OUT (p2p, 附录) | 825 | 0.522 | [0.426, 0.595] | [0.336, 0.610] | [0.268, 0.641] | 0.799 | 0.0005 | 0.10 |
| ALL (p2p, 附录) | 1253 | 0.619 | [0.542, 0.683] | [0.510, 0.698] | [0.466, 0.711] | 0.868 | 0.0005 | 0.17 |

**冻结 external gate（四项全部要求，针对 p2p IN_SUPPORT）：**

| 条件 | 阈值 | 实测 | 结果 |
|---|---|---|---|
| median cosine | ≥ 0.60 | 0.788 | ✅ |
| block-bootstrap 95% CI 下界 | > 0 | 0.719（L=5）；L=10 下界 0.688；L=20 下界 0.588，**均 >0** | ✅ |
| frac cosine>0 | ≥ 0.70 | 1.000 | ✅ |
| vector-pairing permutation p | ≤ 0.01 | 0.0005（B=2000 下限） | ✅ |

> **PRIMARY GATE = PASS。** 较大 block-length 敏感性：把 moving-block 长度从冻结主值 L=5 提到 L=10、L=20，CI 下界分别为 0.688、0.588，**始终 >0，判定对块长稳健**（L=20 时区间变宽但方向结论不变）。

**逐 support 时间块（p2p，全部 frac cos>0 = 1.000）：** 143–197 median **0.906**（n=55）；238–510 **0.815**（n=273）；602–701 **0.374**（n=100）。三个独立时间段方向符号 100% 为正，两个主块强、第三块（最近距离段 8.54–9.12 m）中位幅度偏弱——**如实记为块间异质性弱点**（见 §5），但预注册 gate 以 IN_SUPPORT 全集为准且不要求每块单独过门。

## 2. Secondary：p2l（confirmatory，不替代 p2p）与 −D1 模板方向

- **p2l IN_SUPPORT n=428：median 0.611，L5 CI[0.555,0.651]（L10 [0.517,0.658]、L20 [0.469,0.669]，下界均>0），frac>0=0.956，p=0.0005** → confirmatory 正向。p2l OUT 0.592 / ALL 0.604。
- −D1 纯模板方向 IN：median 0.754，frac>0=0.939，p=0.0005（支持性，非 gate）；其 IN(0.754) 远高于 OUT(0.232)，再次体现支持域特异性。

## 3. P1 — GT 处 objective 非平稳（Dataset II）

| cond | obj | ‖g_real‖/‖g_self‖ | Hotelling p | 梯度方向集中度 |
|---|---|---:|---:|---:|
| raw | p2p | **2639** | 5.4e-281 | 0.843 |
| raw | p2l | 5724 | 5.1e-29 | 0.763 |
| N1 | p2p / p2l | 1994 / 4128 | 9.7e-113 / 1.0e-5 | 0.372 / 0.347 |
| N2 | p2p / p2l | 2026 / 3954 | 7.8e-178 / 9.9e-5 | 0.397 / 0.327 |
| N3 | p2p / p2l | 1408 / 3099 | 5.1e-67 / 8.0e-12 | 0.190 / 0.208 |

> **P1 PASS**：真实扫描在 GT 的目标梯度比 model-self 数值零基线大 1.4×10³–5.7×10³ 倍，Hotelling 全部拒绝零梯度；任一单一全局 nuisance（range offset / 共享 SE3 / 各向同性尺度）都无法把梯度压回零基线。

## 4. P2 — GT-started 局部极小相对 GT 的位移（basin-clipped）

| cond | obj | median ‖Δt‖ (mm) | block-CI95 L5 | mean Δt (mm) | median ‖Δr‖ (°) | 符号一致 | on-bound |
|---|---|---:|---|---|---:|---:|---:|
| raw | p2p | **55.0** | [48.9, 59.8] | [+44.5,+0.7,−9.4] | 1.36 | 0.736 | **0.050** |
| raw | p2l | 59.3 | [54.4, 64.4] | [+30.2,+12.5,−14.3] | 1.44 | 0.749 | 0.125 |
| N1 | p2p | 44.2 | [42.7, 46.3] | [−4.0,−0.1,−1.1] | 1.38 | 0.540 | 0.050 |
| N2 | p2p | 47.5 | [45.8, 49.3] | [+0.1,+1.3,−3.1] | 2.78 | 0.494 | 0.053 |
| N3 | p2p | 34.2 | [30.7, 36.3] | [+21.5,−1.3,−3.3] | 1.41 | 0.469 | 0.050 |

> **P2 PASS（幅度更小，如实报告）**：raw 下局部极小稳定偏离 GT 约 55 mm，p2p 触盆地比例仅 5.0%（非 clipping 人造）；三类 nuisance 各自校正后仍残留 34–47 mm 位移，即全局标定解释不了逐帧被推离 GT 的结构。**注意**：II 的位移幅度（~55 mm）小于 VI(~161)/IV(148)/V(155–174)，与其更近、更混合的工作距离有关；本轮 gate 只看方向，不把幅度差异计为失败，也不据此重拟合 α。

## 5. 弱点与边界（不夸大）

1. **块间异质性**：第三段（602–701，最近距离 8.54–9.12 m）p2p median 仅 0.374，虽 100% 正向但显著弱于前两段；正向结论主要由 n=328 的前两块承载。
2. **OUT 并非零**：p2p OUT median 0.522、frac+0.80，仍偏正——说明方向机制在支持域外并非立刻失效（与 V 远距离外推仍强一致），但 IN(0.788) 明显高于 OUT(0.522)，且幅度 Spearman IN 0.58 vs OUT 0.10，**定量强度仍由支持域覆盖决定**。
3. P2 绝对幅度跨轨迹不稳（延续 TJ1 Level-4 结论）：本轮不以 magnitude 为 gate，α 保持 VI-only 不重拟合。
4. 仅一条补充轨迹、一次 outcome test；I、III 按预承诺**永不**因 II 的结果而被打开测试。

## 6. 独立复核

- Phase-1 support 代码回算 TJ1 已缓存 IV/V：**IV IN=156、V IN=0，与冻结 `ext_predict_{iv,v}.npz['insup']` 逐位一致**。
- outcome 后用**独立路径**（直接从扁平 `ii_prediction.csv` 用 pandas 重算）复算主门限：median 0.7881、frac+1.0、L=5/10/20 CI 与逐块结果**完全一致**。
- 下载完整性：字节数精确、`ZipFile.testzip()` 全 CRC 通过、解压 `.pose` 与 Phase-1 Range 取得版本**逐字节一致（0 处不同）**。
- 范围审计：本机仅 Dataset II 落地 `.3d`（1253）；Dataset I/III 全程只有 `.pose`（`.3d`=0），其 point-cloud outcome 从未被打开。

## 7. 结论

**Dataset II 的 frozen IN_SUPPORT 主分析 P1/P2/P3 全部复现，primary p2p 方向门限四项全过且对更大 block-length 稳健 → TJ2 唯一一次 supplemental outcome-bearing test = PASS。**
