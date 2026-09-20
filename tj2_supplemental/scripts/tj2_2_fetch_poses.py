# -*- coding: utf-8 -*-
"""TJ2 Phase-1 (part B): fetch ONLY *.pose members of EPOS datasets I/II/III via HTTP Range.

For every .pose central-directory record we issue, over a reused TLS connection:
  (1) a tiny range at the local-header offset to read the LOCAL name/extra lengths,
  (2) a range of exactly csize compressed bytes, then raw-inflate and CRC-check.
We never request any byte range that intersects a ".3d" member: each request starts at the
pose member's own local-header offset and stops at data_start+csize.
"""
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

import os, csv, struct, zlib, base64, time, threading, http.client, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = _pp("tj2_supplemental")
META = os.path.join(ROOT, "metadata")
HOST = "syncandshare.desy.de"
PATH = "/public.php/webdav/epos_dataset_{tag}.zip"
AUTH = "Basic " + base64.b64encode(b"m5qqjcEjXFAAAtR:").decode()
NL = threading.local()

def conn():
    c = getattr(NL, "c", None)
    if c is None:
        c = http.client.HTTPSConnection(HOST, timeout=60)
        NL.c = c
    return c

def _range(path, start, end, retries=5):
    last = None
    for k in range(retries):
        try:
            c = conn()
            c.request("GET", path, headers={"Range": f"bytes={start}-{end}",
                                            "Authorization": AUTH, "User-Agent": "curl/8.0"})
            r = c.getresponse(); body = r.read(); status = r.status
            if status == 206:
                return body
            last = f"status {status}"
            try: c.close()
            except Exception: pass
            NL.c = None
        except Exception as e:
            last = repr(e)
            try: NL.c.close()
            except Exception: pass
            NL.c = None
        time.sleep(0.8 * (k + 1))
    raise RuntimeError(f"range fail {start}-{end}: {last}")

def read_cd(tag):
    rows = []
    with open(os.path.join(META, f"cd_{tag}.csv"), encoding="utf-8") as f:
        for e in csv.DictReader(f):
            if e["name"].lower().endswith(".pose"):
                rows.append(dict(name=e["name"], method=int(e["method"]), crc=int(e["crc"]),
                                 csize=int(e["csize"]), usize=int(e["usize"]), lho=int(e["lho"])))
    rows.sort(key=lambda r: r["name"])
    return rows

def fetch_one(tag, row, outdir):
    path = PATH.format(tag=tag)
    base = os.path.basename(row["name"])
    dst = os.path.join(outdir, base)
    if os.path.exists(dst) and os.path.getsize(dst) == row["usize"]:
        return base, "cached"
    lho = row["lho"]
    lh = _range(path, lho, lho + 159)           # local header window (names ~24B)
    assert lh[:4] == b"PK\x03\x04", f"bad local sig {base}: {lh[:4]!r}"
    nlen, elen = struct.unpack("<HH", lh[26:30])
    data_start = lho + 30 + nlen + elen
    comp = _range(path, data_start, data_start + row["csize"] - 1)
    assert len(comp) == row["csize"], f"{base}: got {len(comp)} != csize {row['csize']}"
    if row["method"] == 8:
        raw = zlib.decompress(comp, -15)
    elif row["method"] == 0:
        raw = comp
    else:
        raise RuntimeError(f"{base}: unsupported method {row['method']}")
    assert len(raw) == row["usize"], f"{base}: usize {len(raw)}!={row['usize']}"
    assert (zlib.crc32(raw) & 0xffffffff) == row["crc"], f"{base}: CRC mismatch"
    with open(dst, "wb") as f:
        f.write(raw)
    return base, "ok"

def run(tag, workers=4):
    rows = read_cd(tag)
    outdir = os.path.join(META, f"poses_{tag}"); os.makedirs(outdir, exist_ok=True)
    t0 = time.perf_counter(); done = 0; nok = 0; errs = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_one, tag, r, outdir): r for r in rows}
        for fu in as_completed(futs):
            r = futs[fu]; done += 1
            try:
                _, st = fu.result(); nok += 1 if st == "ok" else 0
            except Exception as e:
                errs.append((r["name"], repr(e)))
            if done % 250 == 0:
                print(f"[{tag}] {done}/{len(rows)} ({nok} new) {time.perf_counter()-t0:.0f}s", flush=True)
    nfiles = len([x for x in os.listdir(outdir) if x.endswith(".pose")])
    print(f"[{tag}] DONE requested={len(rows)} files_on_disk={nfiles} errors={len(errs)} "
          f"{time.perf_counter()-t0:.0f}s", flush=True)
    if errs:
        for n, e in errs[:20]: print("  ERR", n, e)
        raise SystemExit(1)
    assert nfiles == len(rows), "pose count mismatch"

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("tags", nargs="*", default=["i", "ii", "iii"])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    for t in a.tags:
        run(t, a.workers)
