# TJ2_STATUS_LEDGER.md — TJ2 后程序级科学状态（新权威指针，不覆盖 TJ1 历史文件）

- 日期：2026-09-09（Asia/Shanghai）。
- 本文件**新增**，不修改、不删除任何 TJ1 产物；TJ1 的 `TOP_JOURNAL_GATE_FINAL.md` / `STATUS_LEDGER_FINAL.md` 原样留档。

## 1. 当前权威科学状态

```
PREVIOUS (TJ1, preserved): PARTIAL_EXTERNAL_REPLICATION
CURRENT (after TJ2):       GO_TOP_JOURNAL_MECHANISM_CANDIDATE
```

## 2. 升级依据（证据链，按时间顺序，全部非循环）

```
GO_TOP_JOURNAL_MECHANISM_CANDIDATE  =
    VI internal non-circular PASS  (NC0 Protocol-A/B: median cos 0.940, CI[0.929,0.948], 100% pos, p=0.0005)
  + IV confirmatory external PASS  (TJ1-D, IN_SUPPORT n=156: p2p cos 0.841 CI[0.811,0.866], 100% pos, p=0.0005)
  + one PROSPECTIVELY SELECTED supplemental external trajectory PASS
        (TJ2 Dataset II, chosen by metadata-only screen BEFORE any point-cloud read;
         IN_SUPPORT n=428: p2p cos 0.788 CI_L5[0.719,0.830], L10 lo 0.688, L20 lo 0.588 all >0,
         100% pos, vector-pairing p=0.0005; P1 ratio 2.6e3 Hotelling 5.4e-281; P2 55mm on-bound 5%)
  + V supportive OUT-OF-SUPPORT extrapolation (p2p cos 0.902; labeled extrapolation ONLY)
```

## 3. 不可改写的历史记录（必须继续写明）

- **original TJ1-E on Dataset V = NOT EVALUABLE because V had zero frozen-support samples.**
  V range 2.79–7.76 m 与 VI 训练域 8.75–14.80 m 无重叠，冻结 τ_support=0.4403 下 V 的 confirmatory IN_SUPPORT=0；
  V 的强结果（p2p 0.902）**永远只标注为 out-of-support extrapolation，不追认成 TJ1-E PASS**。
- TJ1 的 PARTIAL_EXTERNAL_REPLICATION 是当时的正确判定；本次升级**仅**因新增了一条按纪律前瞻选中、且真正落在冻结支持域内的独立外部轨迹（II），并非回溯修改 V 或阈值。
- τ_support=0.4403305559611483、k*=16、predictor SHA256 `8abcc82d…` 全程未改；未用 II（或 IV/V）回拟合 predictor 或 α。

## 4. TJ2 纪律合规自检

- Phase-1 仅取 PROPFIND 文件列表 + ZIP 中央目录 + `.pose`（CRC 校验）；I/II/III 的 `.3d` 在选择前字节级零读取。
- 选择规则在读点云前执行并写死（`SUPPLEMENTAL_SELECTION.md`）：规则1 N_IN_SUPPORT 最大即选中 II（428>371>313，比值 0.867/0.731<0.90 不构成接近），规则2/3 同样指向 II；未使用任何 predictor cosine/residual/出阳性难易信息。
- `SUPPLEMENTAL_FROZEN_MANIFEST.yaml` 在下载前冻结（pre-download SHA256 `4e28b2a8c65d2266a930d5bbaabc7a3b79be26ed4bb49e61f4c8064098c3bebf`）。
- 整个 TJ2 只进行**一次** outcome-bearing trajectory test（Dataset II）。Dataset I、III 的点云**从未下载/打开**，且无论 II 成败都不再测试（本例 II PASS，故亦不再测试）。
- primary 仅 p2p translation-direction cosine；p2l 为 confirmatory secondary（IN 0.611）；magnitude 非 gate；无新 ICP/robust/NDT/neural/bias-correction。

## 5. 仍需在论文中如实陈述的限制（不阻断 GO_TOP，但限制 claim 强度）

1. 补充外部 confirmatory 轨迹数量 = 1（II），加上 IV 共 2 条真正 in-support 的独立外部轨迹；V 仅外推支持。
2. II 第三 support 时间段（602–701）方向中位偏弱（0.374，仍 100% 正向），存在块间异质性。
3. 幅度（Level-4）跨轨迹仍不可定量迁移；本轮只立“方向机制”claim，不立幅度预测 claim。
4. patch/influence 排名迁移在 TJ1 即呈混合（IV IN 0.05 / V 0.44），TJ2 未重测该项，不作为升级依据。

## 6. 交付物索引（TJ2，目录 `D:\doubao\tj2_supplemental\`）

- 流程/选择/冻结：`reports/SUPPLEMENTAL_SELECTION.md`、`reports/SUPPLEMENTAL_FROZEN_MANIFEST.yaml`
- 结果：`reports/SUPPLEMENTAL_RESULT_II.md`、`results/SUPPLEMENTAL_METADATA_SCREEN.csv`、`results/SUPPLEMENTAL_support_perscan.csv`、`results/ii_prediction.csv`、`results/ext_stats_ii.json`、`results/gate_ii.json`、`results/SUPPLEMENTAL_RESULT_TABLE.csv`
- 脚本（薄驱动，复用已哈希锁定的 phase0 数值核心）：`scripts/tj2_1..8_*.py`
- 数据：仅 `ii_data/epos_dataset_ii/` 含点云；`metadata/poses_{i,ii,iii}/` 仅 `.pose`。
