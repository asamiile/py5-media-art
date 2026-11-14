"""celadon_soliton_estuary — Asymmetric Soliton Wavefronts & Advected Mist Plumes

Propagating internal soliton wave packets radiate from an off-center tidal mouth
near the lower-left golden-ratio focal zone and sweep diagonally across a
mid-tone atmospheric celadon-slate dusk field (#2c3840 - #3d4e48). Hundreds of
buoyant soft chalk-mist and warm amber-ochre drift filaments ride along the
curved traveling phase crests across expansive textured negative space.

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

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 900 frames
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED = random.uniform(10.0, 900.0)

fx = PostFX(
    bloom=0.22,
    bloom_threshold=0.74,
    tonemap=0.92,
    vignette=0.14,
    grain=0.020,
)
field_shader = None

# Two complementary ribbon families:
# 1) Tangential soliton crest foam arcs riding the propagating wave packets
# 2) Diagonal shear-current drift streamers flowing from lower-left to upper-right
NUM_CREST_ARCS = 160
NUM_STREAMERS = 180
NODES_PER_RIBBON = 36

CREST_PACKET_IDX: np.ndarray
CREST_R_OFFSET: np.ndarray
CREST_THETA_CENTER: np.ndarray
CREST_THETA_SPAN: np.ndarray
CREST_WIDTH: np.ndarray
CREST_ROLE: np.ndarray
CREST_PHASE: np.ndarray

STRM_R0: np.ndarray
STRM_THETA0: np.ndarray
STRM_SPEED: np.ndarray
STRM_WIDTH: np.ndarray
STRM_ROLE: np.ndarray
STRM_PHASE: np.ndarray

U_NODE: np.ndarray


def _init_ribbons() -> None:
    global CREST_PACKET_IDX, CREST_R_OFFSET, CREST_THETA_CENTER, CREST_THETA_SPAN, CREST_WIDTH, CREST_ROLE, CREST_PHASE
    global STRM_R0, STRM_THETA0, STRM_SPEED, STRM_WIDTH, STRM_ROLE, STRM_PHASE, U_NODE
    rng = np.random.default_rng()

    U_NODE = np.linspace(0.0, 1.0, NODES_PER_RIBBON, dtype=np.float32)[None, :]

    # 1. Tangential crest arcs locked near the 9 soliton wave crests across r in [0.12, 1.85]
    CREST_PACKET_IDX = rng.integers(0, 9, size=(NUM_CREST_ARCS, 1)).astype(np.float32)
    CREST_R_OFFSET = rng.normal(0.0, 0.018, size=(NUM_CREST_ARCS, 1)).astype(np.float32)
    CREST_THETA_CENTER = rng.normal(-0.42, 0.58, size=(NUM_CREST_ARCS, 1)).astype(np.float32)
    CREST_THETA_SPAN = rng.uniform(0.22, 0.64, size=(NUM_CREST_ARCS, 1)).astype(np.float32)
    CREST_WIDTH = rng.uniform(4.5, 13.5, size=(NUM_CREST_ARCS, 1)).astype(np.float32)
    CREST_PHASE = rng.uniform(0.0, math.tau, size=(NUM_CREST_ARCS, 1)).astype(np.float32)

    r_c = rng.random(NUM_CREST_ARCS)
    CREST_ROLE = np.zeros(NUM_CREST_ARCS, dtype=np.int32)
    CREST_ROLE[r_c > 0.42] = 1  # Warm Amber Ochre
    CREST_ROLE[r_c > 0.78] = 2  # Pale Celadon Crest

    # 2. Diagonal shear-current streamers advecting across the estuary
    STRM_R0 = rng.uniform(0.06, 1.88, size=(NUM_STREAMERS, 1)).astype(np.float32)
    STRM_THETA0 = rng.normal(-0.42, 0.54, size=(NUM_STREAMERS, 1)).astype(np.float32)
    STRM_SPEED = rng.uniform(0.28, 0.46, size=(NUM_STREAMERS, 1)).astype(np.float32)
    STRM_WIDTH = rng.uniform(3.2, 8.8, size=(NUM_STREAMERS, 1)).astype(np.float32)
    STRM_PHASE = rng.uniform(0.0, math.tau, size=(NUM_STREAMERS, 1)).astype(np.float32)

    r_s = rng.random(NUM_STREAMERS)
    STRM_ROLE = np.zeros(NUM_STREAMERS, dtype=np.int32)
    STRM_ROLE[r_s > 0.46] = 2
    STRM_ROLE[r_s > 0.76] = 1


def _ribbons_to_quads(cx: np.ndarray, cy: np.ndarray, half_w: np.ndarray) -> np.ndarray:
    if len(cx) == 0:
        return np.empty((0, 2), dtype=np.float32)
    dx = cx[:, 1:] - cx[:, :-1]
    dy = cy[:, 1:] - cy[:, :-1]
    seg_len = np.hypot(dx, dy) + 1e-4
    nx = -dy / seg_len
    ny = dx / seg_len
    nx = np.concatenate([nx, nx[:, -1:]], axis=1)
    ny = np.concatenate([ny, ny[:, -1:]], axis=1)

    x_top = cx - nx * half_w
    y_top = cy - ny * half_w
    x_bot = cx + nx * half_w
    y_bot = cy + ny * half_w

    n_r = len(cx)
    quads = np.empty((n_r, NODES_PER_RIBBON - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_top[:, :-1]
    quads[:, :, 0, 1] = y_top[:, :-1]
    quads[:, :, 1, 0] = x_bot[:, :-1]
    quads[:, :, 1, 1] = y_bot[:, :-1]
    quads[:, :, 2, 0] = x_bot[:, 1:]
    quads[:, :, 2, 1] = y_bot[:, 1:]
    quads[:, :, 3, 0] = x_top[:, 1:]
    quads[:, :, 3, 1] = y_top[:, 1:]
    return quads.reshape(-1, 2)


def _build_crest_quads(indices: np.ndarray, t_sec: float, w: float, h: float) -> np.ndarray:
    if len(indices) == 0:
        return np.empty((0, 2), dtype=np.float32)
    ax, ay = w * 0.26, h * 0.68
    u = U_NODE - 0.5  # [-0.5, 0.5]

    # Wave crest radial position propagating outward at speed c = 3.2 / 18.0 = 0.1778 / sec
    wavelength = math.tau / 18.0
    r_crest = np.mod(CREST_PACKET_IDX[indices] * wavelength + t_sec * 0.1778, 9.0 * wavelength) + 0.10
    theta = CREST_THETA_CENTER[indices] + u * CREST_THETA_SPAN[indices] / np.sqrt(r_crest + 0.25)

    # Organic curvature along the soliton crest matching shader refraction
    ph = CREST_PHASE[indices]
    r_mod = (
        r_crest
        + CREST_R_OFFSET[indices]
        + 0.032 * np.sin(theta * 3.0 + r_crest * 5.0 - t_sec * 0.9)
        + 0.016 * np.cos(theta * 7.0 + ph)
    )

    cx = ax + r_mod * np.cos(theta) * h * 0.96
    cy = ay + r_mod * np.sin(theta) * h * 0.96

    taper = np.sin(U_NODE * math.pi)
    env = np.clip((1.65 - r_crest) * 2.5, 0.0, 1.0) * np.clip((r_crest - 0.10) * 6.0, 0.0, 1.0)
    half_w = CREST_WIDTH[indices] * taper * env * 0.5
    return _ribbons_to_quads(cx, cy, half_w)


def _build_streamer_quads(indices: np.ndarray, t_sec: float, w: float, h: float) -> np.ndarray:
    if len(indices) == 0:
        return np.empty((0, 2), dtype=np.float32)
    ax, ay = w * 0.26, h * 0.68
    s = U_NODE * 0.26

    r_base = np.mod(STRM_R0[indices] + t_sec * STRM_SPEED[indices] * 0.25 - s, 1.88) + 0.08
    theta_base = STRM_THETA0[indices]
    ph = STRM_PHASE[indices]

    soliton_phase = r_base * 18.0 - t_sec * 3.2 + ph
    theta = theta_base + 0.075 * np.sin(soliton_phase) / (r_base + 0.35) + 0.04 * np.cos(r_base * 6.0 - t_sec * 1.4)
    r = r_base + 0.024 * np.cos(soliton_phase)

    cx = ax + r * np.cos(theta) * h * 0.96
    cy = ay + r * np.sin(theta) * h * 0.96

    taper = np.sin(U_NODE * math.pi)
    edge_fade = np.clip((1.88 - r_base) * 3.2, 0.0, 1.0) * np.clip((r_base - 0.08) * 6.0, 0.0, 1.0)
    half_w = STRM_WIDTH[indices] * taper * edge_fade * 0.5
    return _ribbons_to_quads(cx, cy, half_w)


def setup() -> None:
    global field_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    field_shader = load_shader(SKETCH_DIR / "celadon_soliton_estuary.glsl")
    fx.setup()
    _init_ribbons()


def draw() -> None:
    t_sec = (py5.frame_count - 1) / float(FPS)
    w, h = float(SIZE[0]), float(SIZE[1])

    # 1. Render continuous celadon-slate dusk field & traveling soliton wave packets in GLSL
    draw_fullscreen(
        field_shader,
        seed=float(SEED),
    )

    # 2. Render both tangential soliton crest foam arcs and diagonal shear streamers via py5.QUADS
    py5.no_stroke()

    # Role 2: Pale Celadon Crest (#94bebf)
    py5.fill(148, 190, 191, 118)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_streamer_quads(np.flatnonzero(STRM_ROLE == 2), t_sec, w, h))
        py5.vertices(_build_crest_quads(np.flatnonzero(CREST_ROLE == 2), t_sec, w, h))

    # Role 0: Soft Chalk Mist (#ece6da)
    py5.fill(236, 230, 218, 165)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_streamer_quads(np.flatnonzero(STRM_ROLE == 0), t_sec, w, h))
        py5.vertices(_build_crest_quads(np.flatnonzero(CREST_ROLE == 0), t_sec, w, h))

    # Role 1: Warm Amber Ochre Highlights (#e69232)
    py5.fill(230, 146, 50, 195)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_streamer_quads(np.flatnonzero(STRM_ROLE == 1), t_sec, w, h))
        py5.vertices(_build_crest_quads(np.flatnonzero(CREST_ROLE == 1), t_sec, w, h))

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
