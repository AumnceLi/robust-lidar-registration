# -*- coding: utf-8 -*-
"""r5_download_ivv.py -- GATED download of EPOS Trajectory IV + V ONLY (<400MB).
Run ONLY after VI NC0 PASS. Downloads from DLR/DESY public share, verifies byte size,
extracts; does NOT touch synthetic / I-III / SpaceSense."""
import os,subprocess,sys,zipfile,hashlib,time
import s0_common as C
BASEURL="https://syncandshare.desy.de/public.php/webdav/"
TOKEN="m5qqjcEjXFAAAtR:"
FILES={"iv":("epos_dataset_iv.zip",189777178,2428),"v":("epos_dataset_v.zip",152090372,1868)}
OUT=os.path.join(C.SCRIPTS,"ivv_data"); os.makedirs(OUT,exist_ok=True)

def curl(url,dst):
    p=subprocess.run(["curl.exe","-sL","--retry","3","--max-time","1200","-u",TOKEN,url,"-o",dst])
    return p.returncode

for tag,(fn,expect,nscan) in FILES.items():
    zp=os.path.join(OUT,fn); exdir=os.path.join(OUT,f"epos_dataset_{tag}")
    if not os.path.exists(zp) or os.path.getsize(zp)!=expect:
        print("[download]",fn,flush=True); t0=time.perf_counter()
        rc=curl(BASEURL+fn,zp); got=os.path.getsize(zp) if os.path.exists(zp) else 0
        print(f"  rc={rc} bytes={got} expect={expect} {time.perf_counter()-t0:.0f}s",flush=True)
        assert got==expect, f"SIZE MISMATCH {fn}: {got}!={expect}"
    else: print("[cached]",fn)
    if not os.path.isdir(exdir):
        print("[extract]",fn,flush=True)
        with zipfile.ZipFile(zp) as z: z.extractall(OUT)
    n3d=len([f for f in os.listdir(exdir) if f.endswith(".3d")])
    npo=len([f for f in os.listdir(exdir) if f.endswith(".pose")])
    print(f"[{tag}] extracted .3d={n3d} .pose={npo} expected_scans={nscan}",flush=True)
    assert n3d==nscan and npo==nscan, "scan count mismatch"
print("[done] IV+V ready under",OUT,flush=True)
