# -*- coding: utf-8 -*-
"""TJ2 Phase-1 (part A): read ONLY the ZIP central directories of EPOS datasets I/II/III.

Strict compliance with TJ2 frozen protocol:
  * HTTP Range requests ONLY. We never download the full zip.
  * We fetch: (1) tail for EOCD, (2) central directory bytes -> full file listing.
  * We DO NOT fetch any ".3d" point-cloud bytes here (that is a later, gated stage and
    only for the single selected trajectory).
Outputs per tag: metadata/cd_<tag>.csv  (one row per zip member) + summary printed.
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

import os, struct, io, json, base64, urllib.request, time
from collections import Counter

ROOT = _pp("tj2_supplemental")
META = os.path.join(ROOT, "metadata")
os.makedirs(META, exist_ok=True)

BASE = "https://syncandshare.desy.de/public.php/webdav/"
TOKEN_B64 = base64.b64encode(b"m5qqjcEjXFAAAtR:").decode()
TOTAL = {"i": 194066093, "ii": 89932451, "iii": 94194038}   # from PROPFIND (authoritative listing)
EXPECT_N = {"i": 2483, "ii": 1253, "iii": 1302}

opener = urllib.request.build_opener()

def get_range(url, start, end, retries=4, timeout=120):
    """inclusive byte range, returns raw bytes."""
    last = None
    for k in range(retries):
        req = urllib.request.Request(
            url, headers={"Range": f"bytes={start}-{end}",
                          "Authorization": f"Basic {TOKEN_B64}",
                          "User-Agent": "curl/8.0"})
        try:
            with opener.open(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e; time.sleep(1.5 * (k + 1))
    raise last

def parse_central_dir(cd):
    entries, p = [], 0
    while p + 4 <= len(cd) and cd[p:p+4] == b"PK\x01\x02":
        hdr = cd[p:p+46]
        (ver_made, ver_need, flag, method, mtime, mdate, crc, csize, usize,
         nlen, elen, clen, dsk, iattr, eattr, lho) = struct.unpack("<HHHHHHIIIHHHHHII", hdr[4:46])
        name = cd[p+46:p+46+nlen].decode("utf-8", "replace")
        extra = cd[p+46+nlen:p+46+nlen+elen]
        csize64, usize64, lho64 = csize, usize, lho
        ep = 0
        while ep + 4 <= len(extra):
            eid, esz = struct.unpack("<HH", extra[ep:ep+4]); ev = extra[ep+4:ep+4+esz]
            if eid == 0x0001:
                q = 0
                if usize == 0xFFFFFFFF: (usize64,) = struct.unpack("<Q", ev[q:q+8]); q += 8
                if csize == 0xFFFFFFFF: (csize64,) = struct.unpack("<Q", ev[q:q+8]); q += 8
                if lho == 0xFFFFFFFF:  (lho64,) = struct.unpack("<Q", ev[q:q+8]); q += 8
            ep += 4 + esz
        entries.append(dict(name=name, method=method, flag=flag, crc=crc,
                            csize=csize64, usize=usize64, lho=lho64))
        p += 46 + nlen + elen + clen
    return entries

def process(tag):
    url = BASE + f"epos_dataset_{tag}.zip"
    total = TOTAL[tag]
    tail_len = min(131072, total)
    tail = get_range(url, total - tail_len, total - 1)
    eocd = tail.rfind(b"PK\x05\x06"); assert eocd >= 0, "EOCD not found"
    (disk, cd_disk, n_disk, n_total, cd_size, cd_off, comment_len) = struct.unpack(
        "<HHHHIIH", tail[eocd+4:eocd+22])
    if cd_off == 0xFFFFFFFF or cd_size == 0xFFFFFFFF or n_total == 0xFFFF:
        loc = tail.rfind(b"PK\x06\x07"); assert loc >= 0, "zip64 locator missing"
        z64_off = struct.unpack("<Q", tail[loc+8:loc+16])[0]
        rec = get_range(url, z64_off, z64_off+55)
        n_total = struct.unpack("<Q", rec[32:40])[0]
        cd_size = struct.unpack("<Q", rec[40:48])[0]
        cd_off  = struct.unpack("<Q", rec[48:56])[0]
    cd = get_range(url, cd_off, cd_off + cd_size - 1)
    entries = parse_central_dir(cd)
    # write listing csv
    out = os.path.join(META, f"cd_{tag}.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("name,method,flag,crc,csize,usize,lho\n")
        for e in entries:
            f.write(f"{e['name']},{e['method']},{e['flag']},{e['crc']},{e['csize']},{e['usize']},{e['lho']}\n")
    ext = Counter(os.path.splitext(e["name"])[1].lower() for e in entries)
    methods = Counter(e["method"] for e in entries)
    poses = [e for e in entries if e["name"].lower().endswith(".pose")]
    p3d   = [e for e in entries if e["name"].lower().endswith(".3d")]
    pose_cbytes = sum(e["csize"] for e in poses)
    p3d_cbytes  = sum(e["csize"] for e in p3d)
    summ = dict(tag=tag, zip_bytes=total, n_entries=len(entries), ext=dict(ext),
                methods=dict(methods), n_pose=len(poses), n_3d=len(p3d),
                expect_n=EXPECT_N[tag],
                pose_compressed_bytes=pose_cbytes, p3d_compressed_bytes=p3d_cbytes,
                pose_ubytes=sum(e["usize"] for e in poses),
                first_entries=[e["name"] for e in entries[:4]],
                pose_first=poses[0] if poses else None, pose_last=poses[-1] if poses else None)
    print(json.dumps(summ, indent=2, default=str))
    return summ

if __name__ == "__main__":
    allsum = {}
    for tag in ["i", "ii", "iii"]:
        print(f"\n===== dataset_{tag} =====", flush=True)
        allsum[tag] = process(tag)
    with open(os.path.join(META, "cd_summary.json"), "w", encoding="utf-8") as f:
        json.dump(allsum, f, indent=2, default=str)
    print("\n[done] central directories parsed; no .3d bytes fetched.")
