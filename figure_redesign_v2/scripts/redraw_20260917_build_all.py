"""One-command rebuild of the 2026-09-17 redraw (Figure 2, Figure 6, supp)."""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
steps = [
    "redraw_20260917_fig2.py",
    "redraw_20260917_fig6.py",
    "redraw_20260917_figS_threshold.py",
    "redraw_20260917_export_csvs.py",
]
for s in steps:
    print(f"\n=== {s} ===")
    r = subprocess.run([sys.executable, os.path.join(HERE, s)])
    if r.returncode != 0:
        sys.exit(r.returncode)
print("\nAll figures and CSVs rebuilt.")
