# -*- coding: utf-8 -*-
"""g_generality_run.py -- OPTIONAL section G controlled cross-geometry study (generality only; NO predictor,
NO tuning). Tests whether the mechanism chain  structured mismatch -> ||grad J(T_GT)||>0 -> GT-started biased
optimum  holds on >=3 synthetic spacecraft-like geometries that are NOT the EPOS target, across 5 structured
discrepancy types and a magnitude sweep, with (i) magnitude-0 self-null and (ii) matched-RMS UNSTRUCTURED noise
control. Registrations use the FROZEN g_common solvers/config (LS/Huber/Trim, basin, FD) unchanged."""
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

import os, sys, argparse
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, _pp("g_chain/common"))
import g_common as G

OUT = _pp("g_chain/G_GENERALITY/results"); os.makedirs(OUT, exist_ok=True)
SENSOR_NOISE_MM = 2.0
N_REP = 20
VIEW_COS_THR = np.cos(np.deg2rad(75.0))   # front-facing visibility half-angle (realistic partial LiDAR view)

# ------------------------------------------------------------- geometry builders (analytic-normalled panels)
SP = 0.013  # ~13 mm nominal surface sampling (sets a realistic MAD floor comparable to EPOS ~8 mm)

def _n(h, sp=SP):
    return max(6, int(round(2 * h / sp)) + 1)

def _panel(c, u, v, ha, hb, comp, sp=SP):
    u = np.asarray(u, float); u /= np.linalg.norm(u)
    v = np.asarray(v, float); v /= np.linalg.norm(v)
    n = np.cross(u, v); n /= np.linalg.norm(n)
    na, nb = _n(ha, sp), _n(hb, sp)
    a = np.linspace(-ha, ha, na); b = np.linspace(-hb, hb, nb)
    A, B = np.meshgrid(a, b)
    pts = c + A[..., None] * u + B[..., None] * v
    pts = pts.reshape(-1, 3)
    return pts, np.tile(n, (len(pts), 1)), np.full(len(pts), comp, int)

def _box(c, hx, hy, hz, comp, sp=SP):
    c = np.asarray(c, float); P, N, K = [], [], []
    faces = [  # face axis/sign, in-plane axes, half extents
        (0, +1, (1, 2), hy, hz), (0, -1, (1, 2), hy, hz),
        (1, +1, (0, 2), hx, hz), (1, -1, (0, 2), hx, hz),
        (2, +1, (0, 1), hx, hy), (2, -1, (0, 1), hx, hy)]
    ex = np.eye(3)
    for ax, sgn, (a1, a2), h1, h2 in faces:
        h = [hx, hy, hz][ax]
        cc = c + sgn * h * ex[ax]
        p, _, k = _panel(cc, ex[a1], ex[a2], h1, h2, comp, sp)
        nrm = np.tile(sgn * ex[ax], (len(p), 1))
        P.append(p); N.append(nrm); K.append(k)
    return np.concatenate(P), np.concatenate(N), np.concatenate(K)

def _vants(base):
    """Three sensor vantage directions: base and +/-18 deg jitter about z, all facing the target appendage."""
    b = np.asarray(base, float); b /= np.linalg.norm(b)
    out = [b]
    for deg in (+18, -18):
        th = np.deg2rad(deg); c, s = np.cos(th), np.sin(th)
        Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.]])
        v = Rz @ b; out.append(v / np.linalg.norm(v))
    return out

def build_geometry(name):
    """Return nominal model points M, normals Nm, component labels comp, and target-appendage spec."""
    P, N, K = [], [], []
    if name == "GA":   # box bus + twin solar wings + antenna; target = +x wing
        p, n, k = _box(np.zeros(3), .5, .5, .5, 0); P.append(p); N.append(n); K.append(k)
        for sx, cid in [(+1, 1), (-1, 2)]:
            p, n, k = _panel(np.array([sx * 1.3, 0, 0.]), (0, 1, 0), (0, 0, 1), 1.0, .4, cid)
            P.append(p); N.append(n); K.append(k)
        p, n, k = _panel(np.array([0., 0., .55]), (1, 0, 0), (0, 1, 0), .15, .15, 3)
        P.append(p); N.append(n); K.append(k)
        spec = dict(tcomp=1, hinge=np.array([.5, 0., 0.]), haxis=np.array([0, 0, 1.]), longax=np.array([0, 1, 0.]),
                    normal=np.array([1., 0, 0]), face_axis=2, face_sign=+1, face_c=np.array([.15, .15]),
                    vants=_vants((1, .35, .4)))
    elif name == "GB":  # elongated bus + single big wing + tilted dish + boom; target = wing
        p, n, k = _box(np.zeros(3), .7, .4, .4, 0); P.append(p); N.append(n); K.append(k)
        p, n, k = _panel(np.array([1.5, 0, 0.]), (0, 1, 0), (0, 0, 1), 1.1, .5, 1)
        P.append(p); N.append(n); K.append(k)
        nd = np.array([-1., 0, .3]); nd /= np.linalg.norm(nd)
        u = np.array([0, 1., 0]); v = np.cross(nd, u); v /= np.linalg.norm(v)
        p, n, k = _panel(np.array([-.9, 0, .2]), u, v, .35, .35, 2); n = np.tile(nd, (len(p), 1))
        P.append(p); N.append(n); K.append(k)
        p, n, k = _panel(np.array([0., 0., .75]), (1, 0, 0), (0, 0, 1), .25, .05, 3)
        P.append(p); N.append(n); K.append(k)
        spec = dict(tcomp=1, hinge=np.array([.4, 0., 0.]), haxis=np.array([0, 0, 1.]), longax=np.array([0, 1, 0.]),
                    normal=np.array([1., 0, 0]), face_axis=2, face_sign=+1, face_c=np.array([.2, .1]),
                    vants=_vants((1, .3, .35)))
    elif name == "GC":  # asymmetric cubesat + 4 varied brackets; target = bracket b1
        p, n, k = _box(np.zeros(3), .3, .3, .3, 0); P.append(p); N.append(n); K.append(k)
        p, n, k = _panel(np.array([.42, 0., .1]), (0, 1, 0), (0, 0, 1), .18, .1, 1)
        P.append(p); N.append(n); K.append(k)
        p, n, k = _panel(np.array([0., -.42, -.05]), (1, 0, 0), (0, 0, 1), .14, .08, 2)
        P.append(p); N.append(n); K.append(k)
        p, n, k = _panel(np.array([-.1, .12, .42]), (1, 0, 0), (0, 1, 0), .1, .1, 3)
        P.append(p); N.append(n); K.append(k)
        nd = np.array([.7, 0, .7]); nd /= np.linalg.norm(nd); u = np.array([0, 1., 0]); v = np.cross(nd, u)
        p, n, k = _panel(np.array([.28, -.2, .28]), u, v, .09, .09, 4); n = np.tile(nd, (len(p), 1))
        P.append(p); N.append(n); K.append(k)
        spec = dict(tcomp=1, hinge=np.array([.3, 0., .1]), haxis=np.array([0, 0, 1.]), longax=np.array([0, 1, 0.]),
                    normal=np.array([1., 0, 0]), face_axis=2, face_sign=+1, face_c=np.array([.08, .08]),
                    vants=_vants((.8, .3, .6)))
    else:
        raise ValueError(name)
    M = np.concatenate(P); Nm = np.concatenate(N); comp = np.concatenate(K)
    return M, Nm, comp, spec

# ------------------------------------------------------------- structured discrepancy operators
def _rot_about(a, th):
    a = a / np.linalg.norm(a)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * (K @ K)

def apply_discrepancy(M, Nm, comp, spec, dtype, mag):
    """Return (true cloud, true normals, nominal-model keep-mask). GT=identity.
    D1/D4/D5 act on the whole APPENDAGE ASSEMBLY (all non-bus components) coherently vs the bus -- a realistic
    partial-systematic as-built deviation affecting a large visible fraction; D3 is a deliberately small LOCAL
    bus-face offset; D2 is an UNMODELED component (present in scan, absent from nominal CAD)."""
    P = M.copy(); N = Nm.copy(); model_keep = np.ones(len(P), bool)
    amask = comp != 0                                   # appendage assembly (everything but central bus)
    if dtype == "D1_appendage_disp":      # whole appendage assembly translated along assembly normal
        P[amask] = P[amask] + spec["normal"] * (mag / 1000.0)
    elif dtype == "D2_missing_component":  # unmodeled component: scan KEEPS it, nominal CAD DROPS fraction f
        if mag > 0:
            idx = np.where(comp == spec["tcomp"])[0]
            d = np.linalg.norm(P[idx] - spec["hinge"], axis=1); thr = np.quantile(d, 1 - mag)
            model_keep[idx[d >= thr]] = False          # CAD lacks this part of the feature; scan still has it
    elif dtype == "D3_local_surface_off":  # offset a LOCAL bus-face region outward
        ax = spec["face_axis"]; ax1, ax2 = {2: (0, 1), 0: (1, 2), 1: (0, 2)}[ax]
        cc = np.zeros(3); cc[ax1] = spec["face_c"][0]; cc[ax2] = spec["face_c"][1]; cc[ax] = spec["face_sign"] * 0.5
        w = 0.22
        loc = (comp == 0) & (np.abs(P[:, ax1] - cc[ax1]) < w) & (np.abs(P[:, ax2] - cc[ax2]) < w)
        P[loc, ax] += spec["face_sign"] * mag / 1000.0
    elif dtype == "D4_appendage_scale":   # one-sided span growth of the assembly about the body axis
        la = spec["longax"]; s = P[amask] @ la
        P[amask] += np.outer(np.maximum(s, 0) * mag, la)
    elif dtype == "D5_appendage_tilt":    # coherent assembly yaw about body hinge axis
        R = _rot_about(spec["haxis"], np.deg2rad(mag))
        P[amask] = (R @ P[amask].T).T; N[amask] = (R @ N[amask].T).T
    else:
        raise ValueError(dtype)
    return P, N, model_keep

def _observe(P, N, vant, rng, extra_noise_mm=0.0):
    """Realistic partial LiDAR view: front-facing surfaces only, plus sensor noise."""
    vis = N @ vant > VIEW_COS_THR
    Po = P[vis]
    sig = np.sqrt(SENSOR_NOISE_MM ** 2 + extra_noise_mm ** 2) / 1000.0
    return Po + rng.normal(0, sig, Po.shape)

DTYPES = {
 "D1_appendage_disp": ([0, 2, 5, 10, 25, 50, 100], "mm"),
 "D2_missing_component": ([0, .25, .5, .75, .9, 1.0], "frac"),
 "D3_local_surface_off": ([0, 2, 5, 10, 25, 50, 100], "mm"),
 "D4_appendage_scale": ([0, .005, .01, .025, .05, .10], "frac"),
 "D5_appendage_tilt": ([0, .1, .25, .5, 1, 2], "deg"),
}
GEOMS = ["GA", "GB", "GC"]
_G = {}
def _init():
    import os as _os
    _os.cpu_count = lambda: int(_os.environ.get("QTHREADS", "2"))
    for g in GEOMS:
        M, Nm, comp, spec = build_geometry(g)
        tree = cKDTree(M); sf = float(np.median(cKDTree(M).query(M, k=2)[0][:, 1]))
        _G[g] = dict(M=M, Nm=Nm, comp=comp, spec=spec, tree=tree, sfloor=sf)

def _measure(M, Nm, tree, sf, P):
    rows = {}
    for kind, form in [("p2p", "ls"), ("p2p", "huber"), ("p2p", "trim"), ("p2l", "ls")]:
        r = G.robust_icp(M, Nm, tree, P, kind, form, s_floor=sf)
        gls = G.robust_grad_norm(M, Nm, tree, P, kind, form, sf)[0] if form in ("ls", "huber") else np.nan
        J0 = G.robust_objective(M, Nm, tree, P, np.zeros(6), kind, form, sf)
        rows[f"{kind}_{form}"] = dict(et=np.linalg.norm(r["xi"][:3]) * 1000, eR=np.degrees(np.linalg.norm(r["xi"][3:])),
                                      grad=gls, J0=J0, Js=r["Jlast"], dJ=J0 - r["Jlast"], onb=int(r["on_bound"]), n=len(P))
    return rows

def _one(args):
    geom, dtype, mag, unit, rep = args
    Gd = _G[geom]; M, Nm, comp, spec, tree0, sf0 = Gd["M"], Gd["Nm"], Gd["comp"], Gd["spec"], Gd["tree"], Gd["sfloor"]
    rng = np.random.default_rng(10_000 + (hash((geom, dtype)) % 100000) + rep)
    Ptrue, Ntrue, model_keep = apply_discrepancy(M, Nm, comp, spec, dtype, mag)
    if model_keep.all():
        Mreg, Nreg, tree, sf = M, Nm, tree0, sf0
    else:  # D2: nominal CAD lacks the unmodeled feature -> register scan against reduced CAD
        Mreg, Nreg = M[model_keep], Nm[model_keep]; tree = cKDTree(Mreg)
        sf = float(np.median(cKDTree(Mreg).query(Mreg, k=2)[0][:, 1]))
    vant = spec["vants"][rep % 3]
    P = _observe(Ptrue, Ntrue, vant, rng)
    rows = _measure(Mreg, Nreg, tree, sf, P)
    out = []
    for arm, d in rows.items():
        kind, form = arm.split("_", 1)
        out.append(dict(geometry=geom, dtype=dtype, mag=mag, unit=unit, rep=rep, kind=kind, form=form,
                        grad_gt=d["grad"], et_mm=d["et"], eR_deg=d["eR"], J0=d["J0"], Jstar=d["Js"],
                        dJ=d["dJ"], on_bound=d["onb"], n_obs=d["n"], condition="structured"))
    return out

def _one_noise(args):
    """Matched-RMS UNSTRUCTURED isotropic noise control: no coherent component deviation."""
    geom, mag, rep = args
    Gd = _G[geom]; M, Nm, spec, tree, sf = Gd["M"], Gd["Nm"], Gd["spec"], Gd["tree"], Gd["sfloor"]
    rng = np.random.default_rng(40_000 + (hash(geom) % 100000) + rep)
    vant = spec["vants"][rep % 3]
    P = _observe(M, Nm, vant, rng, extra_noise_mm=mag)   # isotropic RMS == structured linear magnitude
    rows = _measure(M, Nm, tree, sf, P); out = []
    for arm, d in rows.items():
        kind, form = arm.split("_", 1)
        out.append(dict(geometry=geom, dtype="CTRL_random_noise", mag=mag, unit="mm", rep=rep, kind=kind, form=form,
                        grad_gt=d["grad"], et_mm=d["et"], eR_deg=d["eR"], J0=d["J0"], Jstar=d["Js"],
                        dJ=d["dJ"], on_bound=d["onb"], n_obs=d["n"], condition="unstructured_noise"))
    return out

def run(nw=24):
    tasks = []
    for geom in GEOMS:
        for dtype, (mags, unit) in DTYPES.items():
            for mag in mags:
                for rep in range(N_REP):
                    tasks.append((geom, dtype, mag, unit, rep))
    ctrl_mags = [2, 5, 10, 25, 50, 100]
    tasks_n = [(geom, mag, rep) for geom in GEOMS for mag in ctrl_mags for rep in range(N_REP)]
    print(f"[G] {len(tasks)} structured + {len(tasks_n)} control cells"); t0 = __import__("time").perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=nw, initializer=_init) as ex:
        for k, r in enumerate(ex.map(_one, tasks, chunksize=4)):
            rows.extend(r)
        for k, r in enumerate(ex.map(_one_noise, tasks_n, chunksize=4)):
            rows.extend(r)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "geometry_results.csv"), index=False)
    print(f"[G] saved geometry_results.csv rows={len(df)} in {__import__('time').perf_counter()-t0:.0f}s")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--nw", type=int, default=24); a = ap.parse_args()
    run(a.nw)
