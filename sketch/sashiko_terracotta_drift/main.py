"""sashiko_terracotta_drift — Full-Bleed Boro Sashiko Stitch Field & Multi-Act Shear

An edge-to-edge procedural craft study of layered boro textile patches and
continuous running sashiko stitch fields across a full-canvas warm alabaster-linen
ground (#ede8dc). Across a 4-act temporal progression, warp and weft stitch lines
in iron-gall slate, burnt terracotta, raw mineral ochre, and celadon sage
nucleate, expand into intersecting hitomezashi geometric lattices, undergo
hydrodynamic shear waves, and resolve into quiet woven harmony.

100% pure visual art — zero text, zero HUD panels.
"""

from __future__ import annotations

import math
from pathlib import Path
import random
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.animation import frames_dir, step_animation_frame
from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.shaders import PostFX, draw_fullscreen, load_shader
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 24
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1440 frames
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED = random.uniform(10.0, 900.0)

fx = PostFX(
    bloom=0.10,
    bloom_threshold=0.88,
    tonemap=0.20,
    vignette=0.06,
    grain=0.018,
)
fabric_shader = None

# Foreground tactile running-stitch thread segments (dash-gap sashiko rows & columns)
NUM_H_ROWS = 42
NUM_V_COLS = 68
DASHES_PER_H = 38
DASHES_PER_V = 24

H_BASE_Y: np.ndarray
H_DASH_X0: np.ndarray
H_ROW_BIT: np.ndarray
H_ROLE: np.ndarray

V_BASE_X: np.ndarray
V_DASH_Y0: np.ndarray
V_COL_BIT: np.ndarray
V_ROLE: np.ndarray


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    u = min(max((x - edge0) / (edge1 - edge0), 0.0), 1.0)
    return u * u * (3.0 - 2.0 * u)


def _init_stitches(w: float, h: float) -> None:
    global H_BASE_Y, H_DASH_X0, H_ROW_BIT, H_ROLE
    global V_BASE_X, V_DASH_Y0, V_COL_BIT, V_ROLE
    rng = np.random.default_rng()

    # Horizontal running stitch rows spanning full canvas width
    H_BASE_Y = np.linspace(28.0, h - 28.0, NUM_H_ROWS, dtype=np.float32)[:, None]
    H_ROW_BIT = rng.integers(0, 2, size=(NUM_H_ROWS, 1)).astype(np.float32)
    step_x = w / float(DASHES_PER_H)
    H_DASH_X0 = (np.arange(DASHES_PER_H, dtype=np.float32)[None, :] * step_x) + H_ROW_BIT * (step_x * 0.5)
    H_ROLE = np.arange(NUM_H_ROWS) % 4

    # Vertical running stitch columns spanning full canvas height
    V_BASE_X = np.linspace(32.0, w - 32.0, NUM_V_COLS, dtype=np.float32)[:, None]
    V_COL_BIT = rng.integers(0, 2, size=(NUM_V_COLS, 1)).astype(np.float32)
    step_y = h / float(DASHES_PER_V)
    V_DASH_Y0 = (np.arange(DASHES_PER_V, dtype=np.float32)[None, :] * step_y) + V_COL_BIT * (step_y * 0.5)
    V_ROLE = (np.arange(NUM_V_COLS) + 1) % 4


def _build_h_stitch_quads(role_id: int, t_sec: float, act_shear: float, act_density: float, w: float, h: float) -> np.ndarray:
    rows = np.flatnonzero(H_ROLE == role_id)
    if len(rows) == 0:
        return np.empty((0, 2), dtype=np.float32)

    step_x = w / float(DASHES_PER_H)
    dash_len = step_x * (0.42 + 0.18 * act_density)
    thick = 4.6

    # Traveling stitch phase along row
    drift = (t_sec * 36.0) * (1.0 - 2.0 * H_ROW_BIT[rows])
    x0 = np.mod(H_DASH_X0[rows] + drift, w)
    x1 = np.minimum(w, x0 + dash_len)
    xm = 0.5 * (x0 + x1)

    base_y = H_BASE_Y[rows]
    # Multi-act undulating wave shear
    wave_y = act_shear * 26.0 * np.sin(xm * 0.0032 + base_y * 0.0045 - t_sec * 1.4)
    ym = base_y + wave_y

    # Local slope dy/dx for tilted stitch quads
    slope = act_shear * 26.0 * 0.0032 * np.cos(xm * 0.0032 + base_y * 0.0045 - t_sec * 1.4)
    dy_end = slope * (x1 - x0) * 0.5

    y0 = ym - dy_end
    y1 = ym + dy_end
    hh = thick * 0.5

    m, n_d = x0.shape
    quads = np.empty((m, n_d, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x0
    quads[:, :, 0, 1] = y0 - hh
    quads[:, :, 1, 0] = x1
    quads[:, :, 1, 1] = y1 - hh
    quads[:, :, 2, 0] = x1
    quads[:, :, 2, 1] = y1 + hh
    quads[:, :, 3, 0] = x0
    quads[:, :, 3, 1] = y0 + hh
    return quads.reshape(-1, 2)


def _build_v_stitch_quads(role_id: int, t_sec: float, act_shear: float, act_density: float, w: float, h: float) -> np.ndarray:
    cols = np.flatnonzero(V_ROLE == role_id)
    if len(cols) == 0:
        return np.empty((0, 2), dtype=np.float32)

    step_y = h / float(DASHES_PER_V)
    dash_len = step_y * (0.40 + 0.18 * act_density)
    thick = 4.2

    drift = (t_sec * 30.0) * (1.0 - 2.0 * V_COL_BIT[cols])
    y0 = np.mod(V_DASH_Y0[cols] + drift, h)
    y1 = np.minimum(h, y0 + dash_len)
    ym = 0.5 * (y0 + y1)

    base_x = V_BASE_X[cols]
    wave_x = act_shear * 24.0 * np.cos(ym * 0.0036 - base_x * 0.0030 + t_sec * 1.2)
    xm = base_x + wave_x

    slope = -act_shear * 24.0 * 0.0036 * np.sin(ym * 0.0036 - base_x * 0.0030 + t_sec * 1.2)
    dx_end = slope * (y1 - y0) * 0.5

    x0 = xm - dx_end
    x1 = xm + dx_end
    hw = thick * 0.5

    m, n_d = y0.shape
    quads = np.empty((m, n_d, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x0 - hw
    quads[:, :, 0, 1] = y0
    quads[:, :, 1, 0] = x0 + hw
    quads[:, :, 1, 1] = y0
    quads[:, :, 2, 0] = x1 + hw
    quads[:, :, 2, 1] = y1
    quads[:, :, 3, 0] = x1 - hw
    quads[:, :, 3, 1] = y1
    return quads.reshape(-1, 2)


def setup() -> None:
    global fabric_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    fabric_shader = load_shader(SKETCH_DIR / "sashiko_terracotta_drift.glsl")
    fx.setup()
    _init_stitches(float(SIZE[0]), float(SIZE[1]))


def draw() -> None:
    t_norm = (py5.frame_count - 1) / float(TOTAL_FRAMES)
    t_sec = (py5.frame_count - 1) / float(FPS)
    w, h = float(SIZE[0]), float(SIZE[1])

    # Multi-Act Temporal Evolution:
    # Act I (0..0.22): Nucleation of boro linen patches & orthogonal seed stitches
    # Act II (0.22..0.52): Expansion into dense hitomezashi & persimmon-flower geometric weave
    # Act III (0.52..0.82): Turbulent wave shear & diagonal textile billowing
    # Act IV (0.82..1.00): Serene taut resolution
    act_density = 0.35 + 0.65 * _smoothstep(0.0, 0.35, t_norm) * (1.0 - 0.25 * _smoothstep(0.85, 1.0, t_norm))
    act_shear = _smoothstep(0.20, 0.62, t_norm) * (1.0 - 0.65 * _smoothstep(0.82, 1.0, t_norm))

    # 1. Fullscreen GPU high-key washi/linen boro patchwork & geometric sashiko under-weave shader
    draw_fullscreen(
        fabric_shader,
        seed=float(SEED),
        actDensity=float(act_density),
        actShear=float(act_shear),
    )

    # 2. Foreground tactile running-stitch threads batched by mineral pigment role via py5.QUADS
    py5.no_stroke()

    # Role: (R, G, B, Alpha)
    # 0 = Iron-Gall Slate Ink (#263640), 1 = Burnt Terracotta (#ba4a30),
    # 2 = Raw Mineral Ochre (#ca8628), 3 = Celadon Sage (#46726a)
    palette = [
        (38, 54, 64, 225),
        (186, 74, 48, 225),
        (202, 134, 40, 220),
        (70, 114, 106, 210),
    ]

    for role_id, (r, g, b, a) in enumerate(palette):
        py5.fill(r, g, b, a)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(_build_h_stitch_quads(role_id, t_sec, act_shear, act_density, w, h))
            py5.vertices(_build_v_stitch_quads(role_id, t_sec, act_shear, act_density, w, h))

    # 3. Apply PostFX finishing pass
    fx.apply()

    # 4. Save frame, verify non-blank, and compile MP4 on final frame
    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

