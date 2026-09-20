# PATCH_INFLUENCE.md — Gate M4：方向可预测性（M4a）与 patch 梯度机制（M4b）

- 日期：2026-09-09　脚本 `m6_direction_patch.py`；数值 `cache/rescue/m4_direction_patch.json`。
- 本节是 **mechanistic influence analysis（机制影响分析）**，不是滤波/剔除算法（Rescue Audit §14、§23）：Phase-0 不做任何 correction，不主张"删除坏 patch 可提高位姿"。

## A. M4a — mismatch 空间取向能否预测 pose-bias 方向？

冻结空间不平衡描述子（target 系）：
- D1 signed-residual moment：m_t = mean_i s_i p_i；
- D2 |s|-weighted centroid：c_t = Σ|s_i|p_i / Σ|s_i|；
- torque：τ_t = mean_i s_i (p_i × n_i)（对应旋转方向）。
与实测局部极小位移 Δt_t / Δr_t 求跨 scan 平均方向余弦，配 B=2000 双侧置换零分布（随机重绑描述子↔位移）。

| cond | obj | cos(D1, Δt) | p | cos(D2, Δt) | p | cos(τ, Δr) | p |
|---|---|---:|---:|---:|---:|---:|---:|
| raw | p2p | **−0.922** | 0.0005 | **+0.877** | 0.0005 | −0.021 | 0.792 |
| raw | p2l | **−0.929** | 0.0005 | **+0.902** | 0.0005 | −0.114 | 0.0005 |
| combined | p2p | −0.618 | 0.0005 | −0.002 | 1.000 | −0.392 | 0.0005 |
| combined | p2l | −0.656 | 0.0005 | +0.042 | 0.985 | −0.553 | 0.0005 |

判读：
1. **平移方向高度可预测（raw）**：signed moment 与平移偏置方向 |cos|=0.92–0.93，|s|-质心 +0.88–0.90，双侧置换 p=0.0005（B=2000 下限）。符号稳定为负：局部优化器把**源点云**沿"内缩矩的反方向"移动以最小化平方距离，物理方向可预期。
2. **对全局 nuisance 稳健**：最大化校正后 D1 仍达 |cos|=0.62–0.66（p=0.0005）；D2 归零，说明 D2 主要承载共模内缩，而 D1 承载真正的结构化方向。
3. **旋转**：raw 下 torque 与 Δr 近乎无关（−0.02）；去除全局 nuisance 后变为 −0.39/−0.55（p=0.0005），即残余旋转偏置方向可被残差力矩预测，但强度弱于平移。
> **M4a = PASS（平移方向，强；旋转方向，combined 后中等）。**

## B. M4b — 高残差 patch 是否不成比例地贡献目标梯度？

对每 scan 用 12 个共享有限差分探针，把 GT 处梯度**精确分解**到 24 个冻结 patch：g_t = Σ_j g_{t,j}（点云不相交划分，分解恒等）。
- **分解数值闭合**：‖Σ_j g_j − g_t‖ 中位 = **4.9e-15**（机器精度）。
- **within-scan 残差–梯度相关**：每 scan 内 24 patch 的残差水平 vs ‖g_{t,j}‖ 的 Spearman，跨 scan 均值 **0.530，bootstrap 95%CI [0.278, 0.740]，100% 的 scan 为正** → 在**每一帧**里，残差越大的 patch 对目标梯度的贡献都越大，CI 不含 0。
- **leave-one-patch-out 影响度** I_j=‖g_t−g_t^{(−j)}‖：最强 patch 的影响度是中位 patch 的 **2.50×（p2p）/ 2.46×（p2l）**，贡献向少数 patch 集中。
- **与冻结全局 profile 的关系（重要限制）**：跨 scan 平均影响度 vs 冻结 24-patch 残差 profile 的 Spearman = **−0.461（p=0.023）**；影响度 top patch {21,15,2,5,10,17} 与全局残差 top patch {19,14,12,22,7,1} 几乎不重叠。
  - 含义：机制是**逐帧、由当前可见几何/法向决定**的——"这一帧里更坏的 patch 梯度贡献更大"成立（0.53），但不存在一张固定的"全局最坏 patch 地图"能静态指定主导 patch（−0.46）。这避免了把结果过度声称成"某几个固定坏区域"。
> **M4b = PASS（within-scan 不成比例贡献：ρ=0.53、CI 不含 0、100% 正向、2.5× 集中、分解机器精度闭合）；同时如实记录：静态冻结 profile 不预测影响度（ρ=−0.46）。**

## C. 结论
M4a 与 M4b 至少其一的要求由**两者共同满足**：结构化失配的空间取向能定量预测偏置方向（平移 |cos|≈0.92），且目标梯度可闭合分解到 patch、由当帧高残差 patch 不成比例地产生。这把链条补成
`structured mismatch field → per-patch gradient g → predictable bias direction`。

## D. 复现 / 图
`python m6_direction_patch.py`；图 `rescue_figs/F5_patch_influence.png`。
