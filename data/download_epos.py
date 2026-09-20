# -*- coding: utf-8 -*-
"""
download_epos.py -- public download of EPOS-Lid trajectories VI (development),
IV and V (external transfer) into the exact paths expected by the code.

Pure-stdlib (urllib + zipfile); no third-party packages required.

    python data/download_epos.py            # VI + IV + V
    python data/download_epos.py vi         # only VI
    python data/download_epos.py iv v       # IV and V

Each zip is CRC-tested and its extracted scan count is checked. IV/V additionally
have their exact byte size asserted (these are the frozen sizes used in the paper).
VI is ~33.9 MB; its exact zip size is not pinned in the frozen records, so it is
verified by CRC + scan count (501) instead.

Trajectories II and III follow a pre-registered gated flow and are NOT handled
here -- see data/README.md and the g3_* / tj2_* scripts.
"""
import os, sys, io, zipfile, hashlib, ssl, base64, urllib.request, time

# ---- locate repo root (marker file) ----
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = _HERE
while not os.path.exists(os.path.join(_ROOT, ".repo_root")):
    _p = os.path.dirname(_ROOT)
    if _p == _ROOT:
        raise RuntimeError("repo-root marker .repo_root not found")
    _ROOT = _p

BASE = "https://syncandshare.desy.de/public.php/webdav/"
TOKEN = "m5qqjcEjXFAAAtR:"          # public read-only share token (same as the frozen scripts)
SCRIPTS = os.path.join(_ROOT, "structured_mismatch_phase0", "scripts")

# tag: (zip name, expected bytes or None, expected scan count, destination dir)
SPECS = {
    "vi": ("epos_dataset_vi.zip",  None,         501,
           os.path.join(SCRIPTS, "vi_data")),
    "iv": ("epos_dataset_iv.zip",  189_777_178,  2428,
           os.path.join(SCRIPTS, "ivv_data")),
    "v":  ("epos_dataset_v.zip",   152_090_372,  1868,
           os.path.join(SCRIPTS, "ivv_data")),
}


def _download(url, dst):
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={
        "Authorization": "Basic " + base64.b64encode(TOKEN.encode()).decode()})
    with urllib.request.urlopen(req, context=ctx, timeout=600) as r, open(dst, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def fetch(tag):
    fn, expect_bytes, nscan, outdir = SPECS[tag]
    os.makedirs(outdir, exist_ok=True)
    zp = os.path.join(outdir, fn)
    exdir = os.path.join(outdir, "epos_dataset_" + tag)
    if not os.path.exists(zp) or (expect_bytes and os.path.getsize(zp) != expect_bytes):
        print(f"[download] {fn} ...", flush=True)
        t0 = time.perf_counter()
        _download(BASE + fn, zp)
        print(f"           {os.path.getsize(zp)/1e6:.1f} MB in {time.perf_counter()-t0:.0f}s")
    else:
        print("[cached]", fn)
    got = os.path.getsize(zp)
    if expect_bytes:
        assert got == expect_bytes, f"size mismatch {got} != {expect_bytes}"
    with zipfile.ZipFile(zp) as z:
        bad = z.testzip()
        assert bad is None, f"CRC failure in {bad}"
        if not os.path.isdir(exdir):
            z.extractall(outdir)
    n3 = len([f for f in os.listdir(exdir) if f.endswith(".3d")])
    np_ = len([f for f in os.listdir(exdir) if f.endswith(".pose")])
    print(f"[{tag}] extracted .3d={n3} .pose={np_} (expected {nscan})")
    assert n3 == nscan and np_ == nscan, "scan count mismatch"
    print(f"[{tag}] OK -> {exdir}")


if __name__ == "__main__":
    tags = [a.lower() for a in sys.argv[1:]] or ["vi", "iv", "v"]
    for t in tags:
        if t not in SPECS:
            raise SystemExit(f"unknown trajectory {t!r}; choose from {sorted(SPECS)}")
        fetch(t)
    print("[done] requested trajectories ready")
