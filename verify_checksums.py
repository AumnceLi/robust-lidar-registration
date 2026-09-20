# -*- coding: utf-8 -*-
"""Verify SHA256SUMS.txt for the frozen code, artifacts and result tables.

Usage:  python verify_checksums.py
Exit code is non-zero if any listed file is missing or changed.
"""
import os, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(HERE, "SHA256SUMS.txt")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    if not os.path.exists(MAN):
        print("SHA256SUMS.txt not found"); return 2
    ok = bad = miss = 0
    with open(MAN, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            digest, rel = parts[0].strip(), parts[1].strip().lstrip("*").strip()
            p = os.path.join(HERE, rel.replace("/", os.sep))
            if not os.path.exists(p):
                print("MISSING ", rel); miss += 1; continue
            got = sha256(p)
            if got == digest:
                ok += 1
            else:
                print("CHANGED ", rel); bad += 1
    print(f"verified={ok} changed={bad} missing={miss}")
    return 1 if (bad or miss) else 0


if __name__ == "__main__":
    sys.exit(main())
