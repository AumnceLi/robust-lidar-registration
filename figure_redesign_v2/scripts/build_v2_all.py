# -*- coding: utf-8 -*-
"""Single reproducible build entry for the V2 figure set (the approved baseline).

Run from anywhere:  python scripts/build_v2_all.py
It rebuilds EVERY main figure (1-6) and supplementary figure (S1-S3) from the
frozen source data in a fixed dependency order, then runs every numerical /
rendering gate. It never edits data, re-selects cases, or changes statistics to
fix visuals. Any failure aborts the build with a non-zero exit code.

Stages
  data+plot: compute_figure2_data -> reproduce_figure6_gate -> draw_figure1 ->
             draw_figure2 -> figure3 -> figure4 -> make_figure5 -> plot_figure6
             -> figureS1 -> make_figureS2 -> make_figureS3
  verify:    verify_table3 (asserts 5% RMS match, e_t and ratios)
             verify_all_v2 (Fig2 bins/medians/frame counts/heatmap shape)
             verify_figure6 (2-D orthographic render, shared viewport, etc.)
"""
import os, re, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")

BUILD = [
    "compute_figure2_data.py",   # Fig2 derived stats from frozen scans
    "reproduce_figure6_gate.py", # re-run frozen solver, match archive incl. on_bound
    "draw_figure1.py",
    "draw_figure2.py",
    "figure3.py",
    "figure4.py",
    "make_figure5.py",
    "plot_figure6.py",
    "figureS1.py",
    "make_figureS2.py",
    "make_figureS3.py",
]
# verifier -> predicate over combined stdout that returns an error message or None
def _v2_check(out):
    return "verify_all_v2 reported failure" if "SOME CHECKS FAILED" in out else None

def _fig6_check(out):
    m = re.search(r"failures=(\d+)", out)
    if m and int(m.group(1)) > 0:
        return "verify_figure6 reported %s failure(s)" % m.group(1)
    if "[FAIL]" in out:
        return "verify_figure6 reported a [FAIL] check"
    return None

VERIFY = [
    ("verify_table3.py", None),   # uses assert -> non-zero exit on failure
    ("verify_all_v2.py", _v2_check),
    ("verify_figure6.py", _fig6_check),
]

def run(name, predicate=None):
    print("\n" + "=" * 64 + "\n>>> %s" % name)
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, name)],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    tail = (p.stdout or "")
    if tail:
        print("\n".join(tail.splitlines()[-12:]))
    if p.returncode != 0:
        print(p.stderr)
        raise SystemExit("[BUILD ABORT] %s exited %s" % (name, p.returncode))
    if predicate is not None:
        err = predicate(tail)
        if err:
            raise SystemExit("[BUILD ABORT] %s: %s" % (name, err))
    print("[ok] %s" % name)

def main():
    for s in BUILD:
        run(s)
    for name, pred in VERIFY:
        run(name, pred)
    # list deliverables
    print("\n" + "=" * 64 + "\nBUILD OK — deliverables:")
    for sub in ("main", "supplementary"):
        d = os.path.join(ROOT, "figures", sub)
        for f in sorted(os.listdir(d)):
            if f.lower().endswith((".pdf", ".svg", ".png")):
                print("  figures/%s/%s" % (sub, f))

if __name__ == "__main__":
    main()
