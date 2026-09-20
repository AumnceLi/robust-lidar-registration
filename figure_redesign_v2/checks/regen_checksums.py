# -*- coding: utf-8 -*-
"""Regenerate checksums.sha256 over all deliverables (relative POSIX paths)."""
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

import os, hashlib

ROOT = _pp("figure_redesign_v2")
OUT = os.path.join(ROOT, "checksums.sha256")

# Top-level files / directories that constitute the deliverable set.
INCLUDE_DIRS = ["assets", "configs", "scripts", "data", "figures",
                "manifests", "manuscript", "originals"]
INCLUDE_ROOT_EXT = (".md",)
# Under checks/, keep durable records but drop throwaway preview folders.
CHECKS_KEEP_EXT = (".md", ".csv", ".txt", ".log", ".py")
CHECKS_SKIP_DIRS = ("_preview", "_v2preview", "_printproof")
SKIP_DIR_NAMES = ("__pycache__",)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

records = []

def add(abspath):
    rel = os.path.relpath(abspath, ROOT).replace("\\", "/")
    if rel == "checksums.sha256":
        return
    records.append((rel, sha256(abspath)))

for name in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, name)
    if os.path.isfile(p) and name.endswith(INCLUDE_ROOT_EXT):
        add(p)

for d in INCLUDE_DIRS + ["checks"]:
    base = os.path.join(ROOT, d)
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIR_NAMES
                       and not (d == "checks" and x in CHECKS_SKIP_DIRS)]
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            if d == "checks" and not fn.endswith(CHECKS_KEEP_EXT):
                continue
            add(p)

records.sort(key=lambda r: r[0])
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for rel, digest in records:
        f.write("%s  %s\n" % (digest, rel))
print("wrote %d records -> checksums.sha256" % len(records))
