# -*- coding: utf-8 -*-
"""178 mm print-size proof: native-resolution crops of overlap-prone zones."""
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

import os
from PIL import Image

MAIN = _pp("figure_redesign_v2/figures/main")
OUT = _pp("figure_redesign_v2/checks/_printproof")
os.makedirs(OUT, exist_ok=True)

def crop(name, box, out_name, target_w=1900):
    im = Image.open(os.path.join(MAIN, name)).convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = box
    c = im.crop((int(x0*W), int(y0*H), int(x1*W), int(y1*H)))
    h = int(c.height * target_w / c.width)
    c.resize((target_w, h), Image.LANCZOS).save(os.path.join(OUT, out_name))
    print(out_name, "from", name, "crop-frac", box)

def whole(name, out_name, w=1500):
    im = Image.open(os.path.join(MAIN, name)).convert("RGB")
    h = int(im.height*w/im.width)
    im.resize((w, h), Image.LANCZOS).save(os.path.join(OUT, out_name))

# Fig4: top band = D1-D5 legend vs (b) 'Appendage tilt (deg)' axis title
crop("figure4.png", (0.0, 0.0, 1.0, 0.20), "fig4_topband.png")
# Fig5: top band = method legend + (a)(b) panel labels vs VI points/error bars
crop("figure5.png", (0.0, 0.0, 1.0, 0.22), "fig5_topband.png")
# Fig4: middle band = (b) x-axis title 'Appendage tilt' vs D1-D5 shape legend
crop("figure4.png", (0.0, 0.26, 1.0, 0.60), "fig4_midband.png")
# Fig5: inter-row comparison legend vs (a) lower error bars / (c)
crop("figure5.png", (0.0, 0.40, 1.0, 0.56), "fig5_midband.png")
# Fig1: left inter-row Full annotation vs Query-scan title
crop("figure1.png", (0.0, 0.30, 0.42, 0.62), "fig1_fullbox.png", target_w=1700)
# Fig6: one detail strip (II505 row) to judge layer separation at print size
crop("figure6.png", (0.0, 0.60, 1.0, 1.0), "fig6_detail.png", target_w=1900)
# whole-figure overviews
for i in range(1, 7):
    whole("figure%d.png" % i, "fig%d_overview.png" % i)
print("done")
