# -*- coding: utf-8 -*-
"""Prepend SUPERSEDED banner to stale verdict files (never delete)."""
import io,os
REP=os.path.join(os.path.dirname(__file__),os.pardir,"reports")
BANNER=("> **SUPERSEDED_BY_FINAL_RESCUE_AUDIT** — 本文件结论已被 2026-09-09 Final Rescue Audit 取代。\n"
        "> 当前唯一权威状态（CURRENT_SOURCE_OF_TRUTH）：`FINAL_GATE.md` = **GO_STANDARD_PAPER_CORE**；"
        "本文件仅作历史留档，其 STOP/NOT_TRIGGERED 结论不再生效。\n\n---\n\n")
targets={
 "PHASE0_VERDICT.md":"old STOP_NO_PHENOMENON (K3 FPFH+RANSAC baseline 0/101) — 已被 M1–M4 机制证据取代",
 "CROSS_TRAJECTORY_DECISION.md":"old NOT_TRIGGERED — 现已进入 IV/V frozen non-circular replication",
 "TOP_JOURNAL_ASSESSMENT.md":"old STOP-context assessment — 改以 TOP_JOURNAL_GATE_FINAL.md 为准",
}
for fn,note in targets.items():
    p=os.path.join(REP,fn)
    with io.open(p,encoding="utf-8") as f: txt=f.read()
    if "SUPERSEDED_BY_FINAL_RESCUE_AUDIT" in txt:
        print("already banner:",fn); continue
    with io.open(p,"w",encoding="utf-8") as f:
        f.write(BANNER+"> Historical note: "+note+"\n\n---\n\n"+txt)
    print("banner prepended:",fn)
