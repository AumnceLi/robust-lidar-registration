# STATUS_LEDGER_FINAL.md — 状态版本总台账（唯一权威指针）

- 日期：2026-09-09（Asia/Shanghai）。
- 目的：清理多轮结论并存造成的版本歧义；旧文件**不删除**，只标记 SUPERSEDED。

## 1. 当前权威状态
```
CURRENT_CANONICAL_STATUS: GO_STANDARD_PAPER_CORE
CURRENT_SOURCE_OF_TRUTH:  reports/FINAL_GATE.md
CURRENT_STAGE:            IV/V FROZEN NON-CIRCULAR REPLICATION（Top-Journal Gate）
```

## 2. 已被取代的旧状态（历史留档，不再生效）
| 旧文件 | 旧状态 | 处置标记 |
|---|---|---|
| PHASE0_VERDICT.md | FINAL: STOP_NO_PHENOMENON（基于 K3 FPFH+RANSAC 0/101 初始化失败） | **SUPERSEDED_BY_FINAL_RESCUE_AUDIT**（文件头已加 banner） |
| CROSS_TRAJECTORY_DECISION.md | Status: NOT_TRIGGERED | **SUPERSEDED_BY_FINAL_RESCUE_AUDIT**（现已进入 IV/V 复现） |
| TOP_JOURNAL_ASSESSMENT.md | 评分基于 STOP-context | **SUPERSEDED_BY_FINAL_RESCUE_AUDIT**（以 TOP_JOURNAL_GATE_FINAL.md 为准） |

旧的 K3 问的是"FPFH/RANSAC 能否自主初始化"，该问题已被 Final Rescue Audit 明确**移出研究问题**；本轮唯一问题是"VI 学到并冻结的 mismatch mechanism 能否非循环地预测未见 IV/V 的 objective bias"。

## 3. 结论演进时间线
1. 早期 Phase-0：结构化残差现象成立（24 frozen patches、lag1 ρ=0.929、sim-aspect ρ=0.832），但 K3 自主初始化 0/101 → 旧 STOP_NO_PHENOMENON。
2. Final Rescue Audit（VI-only，2026-09-09）：改问"标准刚性目标在已知 GT 处是否平稳"。结果 M1（∇J(T_GT)≠0，real/self 1.4×10³–10⁴）、M2（局部极小系统偏离 GT，raw 中位 160.8mm、符号一致 0.99、self=0）、M3（控制 nuisance 后失配方向 partial R² 0.45–0.90）、M4a（方向 |cos|0.92）、M4b（逐帧 patch 梯度 ρ=0.53）全过；二次预测方向强、幅度不足 → **GO_STANDARD_PAPER_CORE（Level 3）**，并据此**解锁 IV/V**。
3. 当前轮：IV/V frozen non-circular replication，判定是否升级 GO_TOP_JOURNAL_MECHANISM_CANDIDATE（见 TOP_JOURNAL_GATE_FINAL.md）。

## 4. 不可回退的锁定事实（不得重验）
EPOS-Lid=GREEN；VI=501 scans；24 frozen patches（MiniBatchKMeans k=24 seed42，[xyz,0.3n]）；PCA normals(k=16) 冻结；坐标/残差定义冻结；FD 步长 5mm/0.25°；局部盆地 ±0.30m/±15°；随机种子 42；N4 仅为 over-parameterized stress test，主 nuisance 控制为 RAW/N1/N2/N3。

## 5. 文件权威性优先级
`TOP_JOURNAL_GATE_FINAL.md`（本轮终判）＞`FINAL_GATE.md`（VI 终判）＞本台账＞其余一切旧 verdict。任何冲突以更高级为准。
