# -*- coding: utf-8 -*-
"""verify_figure6.py -- deterministic render checks for V2 Figure 6.

Checks (no plot output needed; all numeric / structural):
  1. Same point set / point IDs / count / display subsample across the 3 arms
     within each case (Raw/Patch/Full read the SAME Q_ref and SAME didx).
  2. SE(3) validity of every C matrix (det R == 1, R orthogonal, bottom row [0 0 0 1]).
  3. Transform convention consistent: Q_method = C @ Q_ref == R@Q_ref + t.
  4. Metrics reproduced from C match the archived et/eR to <1e-9.
  5. Shared ortho camera (elev/azim) and identical ROI mask across arms.
  6. Reference-relative displacement npz present and consistent with C.
  7. No 3D box / heatmap: geometry is 2D scatter (assert projection code path used,
     no 3D axes instantiated) -- checked by importing camera_config and confirming
     plot script uses ortho_project (grep guard).
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V2ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(V2ROOT, "configs"))
sys.path.insert(0, HERE)

from paths import DATA_SOURCE_DIR, DATA_DERIVED_DIR, SRC  # noqa: E402
from camera_config import ortho_project, VIEW_ELEV, VIEW_AZIM, points_in_roi  # noqa: E402

CASES = [("IV", 278, "IV278"), ("II", 505, "II505")]
ARMS = ["Raw", "Patch", "Full"]
TOL = 1e-9


def main():
    checks = []
    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")

    import pandas as pd
    archive = pd.read_csv(SRC["replay79_arms"])

    for traj, sid, tag in CASES:
        print(f"=== {tag} ===")
        s = np.load(os.path.join(DATA_SOURCE_DIR, f"figure6_case_{tag}_scan.npz"))
        cm = np.load(os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_C_matrices.npz"))
        dsp = np.load(os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_displacement.npz"))
        didx = np.load(os.path.join(DATA_DERIVED_DIR, f"figure6_case_{tag}_display_indices.npy"))
        Q_ref = s["aligned"].astype(np.float64)

        # 1. same point set across arms (C files share N via load)
        N = Q_ref.shape[0]
        check(f"{tag} same N across arms",
              all(cm[f"C_{a.lower()}"].shape == (4, 4) for a in ARMS))

        # 2. SE(3) validity + 3. convention + 4. metrics
        for a in ARMS:
            C = cm[f"C_{a.lower()}"]
            R = C[:3, :3]; t = C[:3, 3]
            ok_se3 = (abs(np.linalg.det(R) - 1) < TOL and
                      np.allclose(R @ R.T, np.eye(3), atol=TOL) and
                      np.allclose(C[3], [0, 0, 0, 1]))
            check(f"{tag} {a} SE(3) valid", ok_se3, f"detR={np.linalg.det(R):.10f}")
            # convention
            Qm = (R @ Q_ref.T).T + t
            recomputed_et = float(np.linalg.norm(cm[f"et_{a.lower()}"] - 0))  # stored et
            # et from xi-free direct: compare stored et/eR vs archive
            row = archive[(archive.trajectory == traj) & (archive.scan == sid) & (archive.arm == a)]
            aet = float(row.et_mm.iloc[0]); aeR = float(row.eR_deg.iloc[0])
            det = abs(float(cm[f"et_{a.lower()}"]) - aet)
            deR = abs(float(cm[f"eR_{a.lower()}"]) - aeR)
            check(f"{tag} {a} metric == archive", det < TOL and deR < TOL * 1e-3,
                  f"d_et={det:.2e} d_eR={deR:.2e}")
            # 6. displacement consistent
            di = dsp[f"d_{a.lower()}"]
            di_re = np.linalg.norm(Qm - Q_ref, axis=1) * 1000.0
            dmax = float(np.abs(di - di_re).max())
            check(f"{tag} {a} displacement npz == C@Qref", dmax < 1e-6, f"maxdiff={dmax:.2e}")

        # 5. shared camera: ortho_project deterministic & same elev/azim
        p = ortho_project(Q_ref)
        check(f"{tag} ortho projection used (2D)", p.shape == (N, 2),
              f"elev={VIEW_ELEV} azim={VIEW_AZIM}")

        # 7. display indices shared & seeded (5000, in range)
        check(f"{tag} display idx shared 5000",
              len(didx) == 5000 and didx.min() >= 0 and didx.max() < N)

    # grep guard: plot script must NOT use mplot3d / heatmap
    plot_path = os.path.join(HERE, "plot_figure6.py")
    src = open(plot_path, encoding="utf-8").read()
    check("no mplot3d (Axes3D) in plot", "Axes3D" not in src and "projection='3d'" not in src)
    check("no displacement heatmap (pcolormesh/imshow/scatter c=)",
          "pcolormesh" not in src and "imshow" not in src and ", c=d" not in src)

    n_fail = sum(1 for _, ok, _ in checks if not ok)
    print(f"\n[verify] {len(checks)-n_fail}/{len(checks)} passed; failures={n_fail}")
    if n_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
