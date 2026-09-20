# -*- coding: utf-8 -*-
"""TJ2 gated download: ONLY the selected Dataset II. Run strictly AFTER
SUPPLEMENTAL_FROZEN_MANIFEST.yaml is written. Verifies byte size, extracts, counts members,
hashes the zip, and cross-checks extracted .pose files against the Phase-1 Range-fetched ones."""
# ==== portable repo root (auto-added; replaces hard-coded D:\doubao) ====
import os as _os
def _repo_root():
    _d = _os.path.dirname(_os.path.abspath(__file__))
    while not _os.path.exists(_os.path.join(_d, '.repo_root')):
        _p = _os.path.dirname(_d)
        if _p == _d:
            raise RuntimeError('repo-root marker .repo_root not found')
        _d = _p
    return _d
_REPO = _repo_root()
def _pp(*_a):
    return _os.path.join(_REPO, *_a).replace('\\', '/')
# ==== end portable root ====

import os, subprocess, zipfile, hashlib, glob, filecmp, sys

ROOT = _pp("tj2_supplemental")
OUT = os.path.join(ROOT, "ii_data"); os.makedirs(OUT, exist_ok=True)
BASE = "https://syncandshare.desy.de/public.php/webdav/"
TOKEN = "m5qqjcEjXFAAAtR:"
FN, EXPECT, NSCAN = "epos_dataset_ii.zip", 89932451, 1253
zp = os.path.join(OUT, FN); exdir = os.path.join(OUT, "epos_dataset_ii")

if not os.path.exists(zp) or os.path.getsize(zp) != EXPECT:
    print("[download]", FN, flush=True)
    rc = subprocess.run(["curl.exe", "-sL", "--retry", "3", "--max-time", "1800",
                         "-u", TOKEN, BASE + FN, "-o", zp]).returncode
    got = os.path.getsize(zp) if os.path.exists(zp) else 0
    print(f"  rc={rc} bytes={got} expect={EXPECT}", flush=True)
    assert got == EXPECT, f"SIZE MISMATCH {got}!={EXPECT}"
else:
    print("[cached]", FN)

h = hashlib.sha256()
with open(zp, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
print("zip_sha256:", h.hexdigest())

if not os.path.isdir(exdir):
    with zipfile.ZipFile(zp) as z:
        bad = z.testzip()
        assert bad is None, f"CRC failure in member {bad}"
        z.extractall(OUT)
    print("[extracted] with full CRC testzip pass")
else:
    print("[extracted dir exists]")

n3d = len(glob.glob(os.path.join(exdir, "*.3d")))
npo = len(glob.glob(os.path.join(exdir, "*.pose")))
print(f"members: .3d={n3d} .pose={npo} expected={NSCAN}")
assert n3d == NSCAN and npo == NSCAN, "scan count mismatch"

# cross-check extracted poses vs Phase-1 range-fetched poses (must be byte-identical)
refdir = os.path.join(ROOT, "metadata", "poses_ii")
mismatch = []
for rp in sorted(glob.glob(os.path.join(refdir, "*.pose"))):
    ep = os.path.join(exdir, os.path.basename(rp))
    if not os.path.exists(ep) or not filecmp.cmp(rp, ep, shallow=False):
        mismatch.append(os.path.basename(rp))
print("pose cross-check vs phase-1 range fetch: mismatches =", len(mismatch))
assert not mismatch, f"pose mismatch {mismatch[:5]}"
print("[OK] Dataset II ready; point clouds now on disk for the single outcome test.")
