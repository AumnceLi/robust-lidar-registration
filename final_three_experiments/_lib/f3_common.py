# -*- coding: utf-8 -*-
"""f3_common.py -- shared FROZEN plumbing for the FINAL-THREE experiment round.

Hard rules honored here (identical to the rest of the repo):
  * READ-ONLY on every frozen artifact; nothing outside final_three_experiments/ is written.
  * Reuses the frozen numerical cores unchanged (g_common / m_common / s0_common via rev_common)
    and reuses the EXACT instrumented frozen solver + sign-balanced perturbation family from the
    existing local-initialization experiment (final_targeted/t3_common). No solver / K / w / seed /
    support / basin / iteration parameter is changed.
  * Every new experiment records exact command, config, seed, input SHA-256, output SHA-256,
    framewise raw results, an aggregate CSV and a provenance JSON (Prov helper below).

Frozen main config (re-asserted, never re-tuned):
  K_PATCH=24, NORM_W=0.30, MiniBatchKMeans seed=42 (frozen partition `plab`, never re-clustered),
  robust ICP 40 iters, basin safeguard 0.30 m / 15 deg, p2p tol 1e-8, Huber delta=1.345.
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

import os
# fair single-thread BLAS defaults (E3 mandates single-thread; harmless/deterministic for E1/E2)
for _v in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_v, "1")
os.environ.setdefault("QTHREADS", "2")
import sys, json, time, hashlib, platform, datetime
import numpy as np, pandas as pd

class OneThreadTree:
    """Wrap a scipy cKDTree and force query(workers=1) (fair/deterministic thread pinning; the brief
    explicitly permits fixing thread counts). Delegates every other attribute to the wrapped tree.
    NN results are identical regardless of worker count, so no algorithm/result changes."""
    __slots__ = ("_t", "data", "n", "m")
    def __init__(self, tree):
        object.__setattr__(self, "_t", tree)
        object.__setattr__(self, "data", getattr(tree, "data", None))
        object.__setattr__(self, "n", getattr(tree, "n", None))
        object.__setattr__(self, "m", getattr(tree, "m", None))
    def query(self, x, k=1, *args, **kw):
        kw["workers"] = 1
        return self._t.query(x, k=k, *args, **kw)
    def query_ball_tree(self, *a, **k): return self._t.query_ball_tree(*a, **k)
    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_t"), name)

def kdtree1(points):
    from scipy.spatial import cKDTree
    return OneThreadTree(cKDTree(np.asarray(points)))

ROOT = _pp("")
F3 = os.path.join(ROOT, "final_three_experiments")
E1_OUT = os.path.join(F3, "01_coarse_initialization")
E2_OUT = os.path.join(F3, "02_vi_leave_block_out")
E3_OUT = os.path.join(F3, "03_runtime_memory")
LIB = os.path.join(F3, "_lib")

REV = os.path.join(ROOT, "revision_experiments")
FT = os.path.join(REV, "final_targeted")
for _p in (LIB, REV, FT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import rev_common as Rv            # frozen bundle / loaders / constants
import t3_common as T              # EXACT instrumented frozen solver + perturbation family
M, G = Rv.M, Rv.G
TRAJS = Rv.TRAJS                   # ["VI","IV","II","III"]
METHODS4 = T.METHODS               # ["Raw","Huber","Patch","PatchHuber"]

# ---------------------------------------------------------------- frozen configuration (locked)
FROZEN_CFG = dict(
    patch_count=int(G.N_PATCH), normal_feature_weight=0.30, kmeans_seed=42,
    kmeans_n_init=20, kmeans_batch_size=4096,
    max_iter=int(G.MAX_ITER), basin_t_m=float(G.BASIN_T), basin_r_deg=float(G.BASIN_R_DEG),
    tol_p2p=float(G.TOL_P2P), huber_delta=float(G.HUBER_DELTA), kstar=int(G.KSTAR),
    predictor_sha256=G.PREDICTOR_SHA,
)

# ---------------------------------------------------------------- initialization grid (E1)
# L0 = reference (zero perturbation); L1-L3 reused verbatim from the existing local experiment;
# L4-L6 are the only NEW coarse levels. Directions / rotation-axis pairing are the SAME family
# (imported from t3_common, not redefined) so old and new levels are directly comparable.
LEVELS = {"L0": (0.0, 0.0)}
LEVELS.update(T.LEVELS)                                   # L1(10,0.5) L2(30,1) L3(50,2)
LEVELS.update({"L4": (100.0, 5.0), "L5": (200.0, 10.0), "L6": (300.0, 15.0)})
LEVEL_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
NEW_COARSE = ["L4", "L5", "L6"]
REUSED_LOCAL = ["L0", "L1", "L2", "L3"]
DIR_IDS = T.DIR_IDS                                       # v1..v4 (identical sign-balanced family)

def single_thread_worker():
    """Process-pool initializer: load the frozen instrumented-solver bundle, then wrap its KD-trees
    so every NN query is single-threaded (fair, deterministic; avoids process/thread oversubscription)."""
    os.cpu_count = lambda: 1
    T.init_worker()
    T._G["tree_raw"] = OneThreadTree(T._G["tree_raw"])
    T._G["tree_patch"] = OneThreadTree(T._G["tree_patch"])

def perturb_x0(level, dir_id):
    """Same construction as t3_common.perturb_x0 (same DIRS vectors and cyclic rotation-axis
    pairing), extended to L4-L6; L0 returns the zero (reference) chart."""
    if level == "L0":
        return np.zeros(6)
    t_mm, r_deg = LEVELS[level]
    tv = T.DIRS[dir_id]
    rv = T.DIRS[T.ROT_PAIR[dir_id]]
    return np.concatenate([(t_mm / 1000.0) * tv, np.deg2rad(r_deg) * rv])

# ---------------------------------------------------------------- capture criteria (FIXED before running E1)
CAPTURE_B_T_MM = 50.0     # previously tested LOCAL regime upper bound = L3 (50 mm / 2 deg)
CAPTURE_B_R_DEG = 2.0

def capture_A(init_t_mm, init_r_deg, fin_t_mm, fin_r_deg):
    """Relative capture: final error strictly smaller than the injected error on BOTH axes."""
    return bool(fin_t_mm < init_t_mm and fin_r_deg < init_r_deg)

def capture_B(fin_t_mm, fin_r_deg, t_mm=CAPTURE_B_T_MM, r_deg=CAPTURE_B_R_DEG):
    """Recovery into the previously validated local basin (<= L3). Experimental recovery criterion,
    NOT a mission tolerance."""
    return bool(fin_t_mm <= t_mm and fin_r_deg <= r_deg)

# ---------------------------------------------------------------- roster (frozen 20/traj)
ROSTER = os.path.join(FT, "initialization_frames.json")
def load_roster():
    return json.load(open(ROSTER))

def roster_tasks():
    sel = load_roster()
    return [(tr, int(o)) for tr in TRAJS for o in sel["trajectories"][tr]["selected_order"]]

# ---------------------------------------------------------------- small stats
def iqr(x):
    x = np.asarray(x, float); q1, q3 = np.percentile(x, [25, 75]); return float(q3 - q1)
def pct(x, q):
    return float(np.percentile(np.asarray(x, float), q))

# ---------------------------------------------------------------- view geometry helper (Full / Est.Full)
def view_geometry(traj, order):
    """Return oracle view (r,u) and GT pose (t,R) for frame `order`, matching g1/g2 frozen flow."""
    cfg = Rv.REG[traj]
    _, t_gt, q_gt = Rv.load_pose(cfg["pose_dir"], order)
    R_gt = Rv.C.quat_to_R(q_gt)
    meta = Rv.meta_frame(traj)
    if meta is not None:
        row = meta[meta.scan == order].iloc[0]
        zr = float(row.range_m); zu = np.array([row.ux, row.uy, row.uz], float)
    else:
        o = -R_gt.T @ t_gt; zr = float(np.linalg.norm(o)); zu = o / zr
    return zr, zu, t_gt, R_gt

# ---------------------------------------------------------------- hashing / provenance
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()

def sha256_bytes(b):
    return hashlib.sha256(bytes(b)).hexdigest()

def machine_env():
    import psutil
    try:
        cpu = platform.processor()
        # prefer the marketing name via WMI is avoided; psutil gives logical/physical counts
        info = dict(
            python=platform.python_version(), numpy=np.__version__,
            scipy=__import__("scipy").__version__, sklearn=__import__("sklearn").__version__,
            pandas=pd.__version__, psutil=psutil.__version__,
            platform=platform.platform(), os_arch=platform.machine(),
            cpu_processor=cpu, cpu_logical=int(os.cpu_count() or -1),
            cpu_physical=int(psutil.cpu_count(logical=False) or -1),
            ram_total_gb=round(psutil.virtual_memory().total / 1e9, 3),
            env_threads={k: os.environ.get(k) for k in
                         ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS",
                          "NUMEXPR_NUM_THREADS", "QTHREADS"]},
        )
    except Exception as e:  # psutil missing
        info = dict(python=platform.python_version(), numpy=np.__version__,
                    pandas=pd.__version__, platform=platform.platform(), error=str(e))
    return info

class Prov:
    """Collects exact command / config / seed / input hashes and, on write, hashes every output."""
    def __init__(self, experiment, script, config=None, seed=None, note=""):
        self.experiment = experiment
        self.d = dict(
            experiment=experiment, generator_script=script,
            exact_argv=sys.argv, cwd=os.getcwd(),
            start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            seed=seed, config=config or {}, frozen_config=FROZEN_CFG,
            machine=machine_env(), note=note, inputs={}, outputs={})
    def add_input(self, key, path):
        self.d["inputs"][key] = dict(path=path, exists=os.path.exists(path),
                                     size_b=(os.path.getsize(path) if os.path.exists(path) else None),
                                     sha256=(sha256_file(path) if os.path.exists(path) else None))
    def add_input_value(self, key, value):
        b = json.dumps(value, sort_keys=True).encode()
        self.d["inputs"][key] = dict(inline=True, sha256=sha256_bytes(b))
    def register_outputs(self, paths):
        for p in paths:
            self.d["outputs"][os.path.basename(p)] = dict(
                path=p, size_b=os.path.getsize(p), sha256=sha256_file(p))
    def finish(self, prov_path, output_paths, extra=None):
        self.d["end_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if extra:
            self.d.update(extra)
        self.register_outputs(output_paths)
        with open(prov_path, "w", encoding="utf-8") as f:
            json.dump(self.d, f, indent=2, default=_json_default)
        # self-hash last (prov file contains others' hashes but not its own)
        return prov_path

def _json_default(o):
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, np.ndarray): return o.tolist()
    return str(o)
