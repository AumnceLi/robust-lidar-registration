# SUPPLEMENTAL_SELECTION.md — TJ2 前瞻冻结：补充外部轨迹选择（读取任何点云之前）

- 阶段：**TJ2 — SUPPLEMENTAL EXTERNAL CONFIRMATORY REPLICATION，Phase-1 metadata screen → prospective trajectory selection**
- 日期：2026-09-09（Asia/Shanghai）。
- 进入状态（保持不变）：`FINAL: PARTIAL_EXTERNAL_REPLICATION`。原 TJ1 结果**不修改**；Dataset V 的 out-of-support 外推**不**追认成 TJ1-E PASS（TJ1-E 仍为 CONFIRMATORY NOT EVALUABLE，V 的 frozen-support IN_SUPPORT n=0）。
- **排序纪律声明：本选择在下载/读取 I/II/III 任何 `.3d` 点云、residual、objective、local optimum 或任何 registration outcome 之前完成并写死。** 选择过程中从未计算、也无法计算 predictor cosine、residual quality 或“哪个更容易出阳性”——这些量在 Phase-1 根本没有被打开。

---

## 1. Phase-1 只取了什么（合规审计）

仅通过 DESY 公共 WebDAV 共享（与 TJ1 同一 share，IV zip 字节数、target_model 字节数均与冻结记录一致 → 同一数据版本）：

1. **文件列表**：一次 `PROPFIND Depth:1`（根目录清单 + 各 zip 总字节）。
2. **ZIP 中央目录**：对 `epos_dataset_{i,ii,iii}.zip` 仅用 HTTP `Range` 读取 EOCD + central directory（复用既有 `remote_zip_cd.py` 技术），得到成员清单、压缩/原始字节、CRC、偏移。
3. **`.pose` 成员**：仅对每个 `.pose` 成员用 `Range` 取其本地头 + 恰好 `csize` 的压缩字节，raw-inflate 并 **CRC32 逐一校验通过**。

| 轨迹 | zip 总字节（列表） | 帧数（README=中央目录） | 本次取得的 `.pose` | 全部 `.pose` 压缩字节 | **本次取得的 `.3d` 字节** |
|---|---:|---:|---:|---:|---:|
| Dataset I (`epos_dataset_i.zip`)   | 194,066,093 | 2,483 | 2,483（CRC 全通过） | 158,510 | **0** |
| Dataset II (`epos_dataset_ii.zip`) |  89,932,451 | 1,253 | 1,253（CRC 全通过） |  79,926 | **0** |
| Dataset III (`epos_dataset_iii.zip`)| 94,194,038 | 1,302 | 1,302（CRC 全通过） |  82,212 | **0** |

被禁止读取的内容（`.3d` 点云、residual、R4/SPS、objective gradient、local optimum、任何 registration outcome）在 Phase-1 **字节级未触碰**。

## 2. 冻结输入（不重拟合、不改阈值）

- `VI_ONLY_PREDICTOR_FROZEN.npz` SHA256 `8abcc82d3b97a778ae1c00ff15d15aed089bb14ddf9465d9f935ece7fe3bfffe`（已复算一致）。
- k\*=16；range_std=2.064279860893169 m；**τ_support=0.4403305559611483（锁死，不回改）**；24 frozen patches；PCA normals k=16；FD 5mm/0.25°；局部盆地 ±0.30m/±15°；nuisance 主控制 RAW/N1/N2/N3（N4 仅 stress test）。
- 冻结 support 距离（与 TJ1 `r8_ext_predict.py` 同一公式，只用 GT pose/range/观测几何）：
  - 观测几何：`o = -R^T t`（target 系传感器原点），`range=‖o‖`，`u=o/range`；
  - `d(z,VI)= min_{i∈501 VI} sqrt( ((range−vr_i)/range_std)^2 + arccos(clip(u·uview_i))^2 )`；
  - `IN_SUPPORT ⇔ d ≤ τ_support`。
- **实现校验（关键）**：同一几何-only 代码回算 TJ1 已缓存的 IV/V，结果 **IV IN_SUPPORT=156、V IN_SUPPORT=0，且与 TJ1 冻结 `ext_predict_{iv,v}.npz['insup']` 逐位一致（bitwise_agree=True）**。证明本筛查的距离/阈值实现与 TJ1 完全相同，没有引入新口径。

## 3. 筛查结果（`results/SUPPLEMENTAL_METADATA_SCREEN.csv`）

VI 训练域：range 8.7465–14.8022 m，6 个 frozen orientation blocks。

| 指标 | Dataset I | **Dataset II** | Dataset III |
|---|---:|---:|---:|
| n_scans | 2,483 | 1,253 | 1,302 |
| **N_IN_SUPPORT** | 313 | **428** | 371 |
| IN_SUPPORT fraction | 12.6% | **34.2%** | 28.5% |
| 连续 support block 数 | 1 | **3** | 1 |
| 各 block 长度 | [313] | **[55, 273, 100]** | [371] |
| support block 扫描区间 | 103–415（单段） | **143–197 / 238–510 / 602–701（三段，有间隙）** | 154–524（单段） |
| 覆盖时间十分位数 | 2/10 | **5/10** | 4/10 |
| 命中不同 VI 朝向块数 | 2/6 | **6/6** | 6/6 |
| IN_SUPPORT range 区间 (m) | 14.81–14.89（极窄边缘条带） | **8.54–15.69（宽）** | 8.25–15.46 |
| 全轨迹 range (m) | 2.85–16.82 | 3.85–19.78 | 3.84–19.78 |
| dmin 中位 | 1.168 | **0.782** | 1.512 |
| zip 下载体积 (B) | 194,066,093 | **89,932,451（最小）** | 94,194,038 |

## 4. 预注册选择规则（在看结果前已固定层级）

1. **首要**：选 `N_IN_SUPPORT` 最大者。
2. **仅当接近时**（预注册定义：次高 ≥ 最高的 0.90，即相对差 ≤10%）才进入第 2 条——优先选 IN_SUPPORT **跨越更多独立时间/朝向 block**、而非挤在单一连续段者。
3. **仍接近时**：选下载体积最小者。
4. 明确禁止：不得用预计 predictor cosine、residual quality 或“哪个更容易出阳性”来选。

## 5. 规则适用过程（机械执行，无主观挑拣）

- **规则 1**：N 排序 II=428 > III=371 > I=313。相对比 III/II=0.867、I/II=0.731，**均 < 0.90，不构成“接近”**，因此规则 1 已单独决定：**选 Dataset II**。
- 即便采用更宽松的“接近”解释，规则 2 同样指向 II：II 有 **3 个被 OUT 间隙分开的独立时间块**、覆盖 5/10 时间十分位、命中全部 6 个 VI 朝向块；而 I、III 的 IN_SUPPORT 都挤在**单一连续段**（I 还只压在 14.81–14.89 m 的 VI 远距边缘窄条带、仅 2 个朝向块）。规则 3 也指向 II（89.93 MB 最小）。**三条规则一致指向 II，结论对 tie-break 阈值不敏感。**
- **覆盖充分性（go/no-go）**：II 的 IN_SUPPORT n=428，分布于 3 个独立时间块、6 个朝向块，量级高于 TJ1 中已成功 confirmatory 的 IV（IN n=156），足以支撑 L=5 moving-block bootstrap 与 vector-pairing permutation。**不存在“I/II/III 均无足够 frozen-support coverage”的情形 → 不触发“停止下载、保持 PARTIAL、进入论文写作”分支。**

## 6. 选择决定（前瞻冻结）

```
SELECTED_TRAJECTORY: Dataset II  (epos_dataset_ii.zip, 89,932,451 B, 1,253 scans)
PROSPECTIVE_IN_SUPPORT_PLAN: primary confirmatory analysis on the 428 frozen IN_SUPPORT scans
                             (3 temporal blocks: 143-197 n=55, 238-510 n=273, 602-701 n=100)
NOT_SELECTED_NEVER_TESTED: Dataset I, Dataset III
```

选定后**立即**写 `SUPPLEMENTAL_FROZEN_MANIFEST.yaml`（记录选择依据、全部 predictor hash、τ、P1/P2/P3、bootstrap/permutation、gate），**之后**才下载 Dataset II 的点云。

## 7. 一次性纪律（失败处理，预承诺）

- 整个 TJ2 **只进行一次** outcome-bearing trajectory test（即 Dataset II）。
- 若 II 的 IN_SUPPORT 主分析 **PASS** → 状态升级 `GO_TOP_JOURNAL_MECHANISM_CANDIDATE`，来源链 = VI internal non-circular PASS + IV confirmatory external PASS + **本次一条前瞻选择的 supplemental external PASS** + V supportive out-of-support 外推；历史仍写明 **original TJ1-E on Dataset V = NOT EVALUABLE（V frozen-support n=0）**。
- 若 II 下载后 P3 **FAIL**：**不得**再依次尝试 I 或 III 直到出现正结果；立即回到并保持 `PARTIAL_EXTERNAL_REPLICATION`，把该 failure 作为 mechanism transfer boundary 报告。
- p2p translation-direction cosine 为唯一 primary endpoint；p2l 仅 confirmatory secondary，不得替代；magnitude 不作本轮 gate；不重拟合 α；不开发新 ICP/robust loss/NDT/neural predictor/bias correction。
