# -*- coding: utf-8 -*-
"""g3_download_cache.py -- ONE-TIME acquisition + frozen-pipeline caching of the untouched Dataset III.
Steps: download zip (DESY webdav) -> verify byte size + per-entry CRC -> extract -> verify pose-only SHA256
against the metadata-screen fingerprint -> build GT-aligned scan cache with the IDENTICAL r6 external pipeline
-> frozen-library support (ndist/insup). No registration outcome is read here."""
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

import os, sys, io, zipfile, hashlib, glob, time, ssl, base64, urllib.request
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, _pp("g_chain/common"))
sys.path.insert(0, _pp("structured_mismatch_phase0/scripts"))
import g_common as G, s0_common as C, m_common as M

ROOT = _pp("g_chain/G3_FINAL_CONFIRMATION")
DL = os.path.join(ROOT, "download"); CACHE = os.path.join(ROOT, "iii_cache")
os.makedirs(DL, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
URL = "https://syncandshare.desy.de/public.php/webdav/epos_dataset_iii.zip"
TOKEN = "m5qqjcEjXFAAAtR:"
EXPECT_BYTES = 94_194_038; EXPECT_N = 1302
EXPECT_POSE_SHA = "cf1f0d3afc94f24222fd964a4931fe809aa9128023875552b393f648eda64f2c"
ZIP = os.path.join(DL, "epos_dataset_iii.zip"); DATA = os.path.join(DL, "epos_dataset_iii")

def download():
    if os.path.exists(ZIP) and os.path.getsize(ZIP) == EXPECT_BYTES:
        print("[dl] zip present, size OK"); return
    print("[dl] downloading III ..."); t0 = time.perf_counter()
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(URL, headers={
        "Authorization": "Basic " + base64.b64encode(TOKEN.encode()).decode()})
    with urllib.request.urlopen(req, context=ctx, timeout=300) as r, open(ZIP, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk: break
            f.write(chunk)
    got = os.path.getsize(ZIP)
    print(f"[dl] {got} bytes in {time.perf_counter()-t0:.0f}s")
    assert got == EXPECT_BYTES, f"size mismatch {got} != {EXPECT_BYTES}"

def verify_and_extract():
    with open(ZIP, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print("[zip] sha256", sha)
    with zipfile.ZipFile(ZIP) as z:
        bad = z.testzip()  # CRC32 every entry
        assert bad is None, f"CRC failure at {bad}"
        n3 = sum(1 for n in z.namelist() if n.endswith(".3d")); np_ = sum(1 for n in z.namelist() if n.endswith(".pose"))
        print(f"[zip] CRC OK; .3d={n3} .pose={np_}")
        assert n3 == EXPECT_N and np_ == EXPECT_N
        z.extractall(DL)
    print("[zip] extracted ->", DATA)

def pose_sha():
    ps = sorted(glob.glob(os.path.join(DATA, "*.pose")))
    h = hashlib.sha256()
    for p in ps:
        with open(p, "rb") as f: h.update(f.read())
    got = h.hexdigest()
    print("[pose] concat-sha256", got, "n=", len(ps))
    assert got == EXPECT_POSE_SHA, "pose fingerprint mismatch -> STOP"
    print("[pose] matches frozen metadata-screen fingerprint")

# ---- frozen r6 external cache pipeline ----
_G = {}
def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    mc = np.load(os.path.join(M.CACHE, "model_cache.npz"))
    _G["model"] = mc["xyz"].astype(np.float64); _G["nrm"] = mc["normals"].astype(np.float64)
    _G["plab"] = np.load(os.path.join(M.CACHE, "patches.npz"))["lab"]
    _G["tree"] = cKDTree(_G["model"])

def _cache_one(i):
    pc = np.loadtxt(os.path.join(DATA, f"{i:04d}.3d"))
    t, q = G.load_pose_dir(os.path.join(DATA, f"{i:04d}.pose")); R = C.quat_to_R(q)
    aligned = ((R.T) @ (pc - t).T).T                    # IDENTICAL to r6
    dd, nn = _G["tree"].query(aligned, k=1, workers=2)
    signed = ((aligned - _G["model"][nn]) * _G["nrm"][nn]).sum(1)
    patch = _G["plab"][nn]
    o = -R.T @ t; rng = np.linalg.norm(o); u = o / rng
    np.savez_compressed(os.path.join(CACHE, f"scan_{i:04d}.npz"),
                        aligned=aligned.astype(np.float32), nnidx=nn.astype(np.int32),
                        patch=patch.astype(np.int16), signed=signed.astype(np.float32), d=dd.astype(np.float32))
    return dict(scan=i, range_m=rng, n=len(pc), ux=u[0], uy=u[1], uz=u[2])

def build_cache(nw=26):
    ids = sorted(int(os.path.basename(f)[:4]) for f in glob.glob(os.path.join(DATA, "*.3d")))
    assert len(ids) == EXPECT_N
    have = set(int(os.path.basename(f)[5:9]) for f in glob.glob(os.path.join(CACHE, "scan_*.npz")))
    todo = [i for i in ids if i not in have]
    print(f"[cache] {len(ids)} frames, {len(todo)} to build")
    rows = []; t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, r in enumerate(ex.map(_cache_one, todo, chunksize=2)):
            rows.append(r)
            if (k + 1) % 200 == 0: print(f"[cache] {k+1}/{len(todo)} {time.perf_counter()-t0:.0f}s", flush=True)
    # merge meta (include pre-existing rows)
    allrows = []
    for i in ids:
        z = np.load(os.path.join(CACHE, f"scan_{i:04d}.npz"))
        t, q = G.load_pose_dir(os.path.join(DATA, f"{i:04d}.pose")); R = C.quat_to_R(q)
        o = -R.T @ t; rng = np.linalg.norm(o); u = o / rng
        allrows.append(dict(scan=i, range_m=rng, n=z["aligned"].shape[0], ux=u[0], uy=u[1], uz=u[2]))
    pd.DataFrame(allrows).to_csv(os.path.join(CACHE, "meta_iii.csv"), index=False)
    print(f"[cache] meta_iii.csv n={len(allrows)}")

def support():
    fz = G.load_frozen(); meta = pd.read_csv(os.path.join(CACHE, "meta_iii.csv"))
    zr = meta.range_m.values; zu = meta[["ux", "uy", "uz"]].values
    # identical to r8._mu distance and r8 support: Dv already /sr inside; insup = Dv.min() <= tau
    ang = np.arccos(np.clip(fz["uview"] @ zu.T, -1, 1))           # (501,n)
    ndist = np.sqrt(((fz["vrange"][:, None] - zr[None, :]) / G.RANGE_STD) ** 2 + ang ** 2).min(0)
    insup = ndist <= G.TAU_SUPPORT
    ids = meta.scan.values
    np.savez(os.path.join(CACHE, "ext_predict_iii.npz"), ids=ids, ndist=ndist, insup=insup)
    print(f"[support] in-support={int(insup.sum())}/{len(ids)} (metadata screen expected 371)")

if __name__ == "__main__":
    download(); verify_and_extract(); pose_sha(); build_cache(); support()
    print("[g3_download_cache] COMPLETE")
