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

DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED = random.uniform(10.0, 900.0)
SWEEP_ANGLE = random.uniform(-0.34, -0.22)  # Diagonal stratification across the 3840x2160 canvas

fx = PostFX(
    bloom=0.28,
    bloom_threshold=0.68,
    tonemap=0.94,
    vignette=0.14,
    grain=0.022,
)
field_shader = None

# Pre-generate diagonal scalloped rimstone contour ribbons spanning the full canvas width
NUM_STRATA = 32
NUM_PTS = 84
STRATA_U: np.ndarray
STRATA_BASE_V: np.ndarray
STRATA_PHASE: np.ndarray
STRATA_FREQ: np.ndarray
STRATA_WIDTH: np.ndarray
STRATA_ROLE: np.ndarray


def _init_strata_contours() -> None:
    global STRATA_U, STRATA_BASE_V, STRATA_PHASE, STRATA_FREQ, STRATA_WIDTH, STRATA_ROLE

    rng = np.random.default_rng()
    STRATA_U = np.linspace(-1.25, 1.25, NUM_PTS, dtype=np.float32)[None, :]
    STRATA_BASE_V = np.linspace(-0.78, 0.78, NUM_STRATA, dtype=np.float32)[:, None]
    STRATA_PHASE = rng.uniform(0.0, math.tau, size=(NUM_STRATA, 1)).astype(np.float32)
    STRATA_FREQ = rng.uniform(3.2, 6.4, size=(NUM_STRATA, 1)).astype(np.float32)
    STRATA_WIDTH = rng.uniform(3.5, 9.5, size=(NUM_STRATA, 1)).astype(np.float32)
    # 0: Travertine Chalk Lip (#e4dfd4), 1: Amber-Ochre Lichen (#d88c32), 2: Celadon-Mist Crest (#96b4b6)
    STRATA_ROLE = np.arange(NUM_STRATA) % 3


def _build_strata_quads(indices: np.ndarray, t_sec: float, w: float, h: float) -> np.ndarray:
    u = STRATA_U
    v0 = np.mod(STRATA_BASE_V[indices] + (t_sec * 0.025) + 0.80, 1.60) - 0.80
    ph = STRATA_PHASE[indices]
    freq = STRATA_FREQ[indices]
    half_w = STRATA_WIDTH[indices] * (0.55 + 0.45 * np.sin((u + 1.25) / 2.5 * math.pi))

    # Scalloped rimstone dam profile in rotated (u, v) coordinates
    scallop = -0.028 * np.abs(np.sin(u * freq + ph + t_sec * 0.25)) + 0.018 * np.sin(
        u * (freq * 0.5) - ph + t_sec * 0.18
    )
    v = v0 + scallop

    cos_a = math.cos(-SWEEP_ANGLE)
    sin_a = math.sin(-SWEEP_ANGLE)

    cx = w * 0.5 + (u * cos_a - v * sin_a) * h
    cy = h * 0.5 + (u * sin_a + v * cos_a) * h

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

    n_s = len(indices)
    quads = np.empty((n_s, NUM_PTS - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_top[:, :-1]
    quads[:, :, 0, 1] = y_top[:, :-1]
    quads[:, :, 1, 0] = x_bot[:, :-1]
    quads[:, :, 1, 1] = y_bot[:, :-1]
    quads[:, :, 2, 0] = x_bot[:, 1:]
    quads[:, :, 2, 1] = y_bot[:, 1:]
    quads[:, :, 3, 0] = x_top[:, 1:]
    quads[:, :, 3, 1] = y_top[:, 1:]
    return quads.reshape(-1, 2)


def setup() -> None:
    global field_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    field_shader = load_shader(SKETCH_DIR / "lichen_travertine_terraces.glsl")
    fx.setup()
    _init_strata_contours()


def draw() -> None:
    t_sec = (py5.frame_count - 1) / float(FPS)
    w, h = float(SIZE[0]), float(SIZE[1])

    # 1. Fullscreen GPU diagonal terraced travertine & lichen morphogenesis shader
    draw_fullscreen(
        field_shader,
        seed=float(SEED),
        sweepAngle=float(SWEEP_ANGLE),
    )

    # 2. Sculpted diagonal rimstone lip ribbons batched by mineral/lichen role via py5.QUADS
    py5.no_stroke()

    # Role 0: Calcified Travertine Chalk Lip (#e4dfd4)
    py5.fill(228, 223, 212, 72)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_strata_quads(np.flatnonzero(STRATA_ROLE == 0), t_sec, w, h))

    # Role 1: Thermophilic Amber-Ochre Lichen (#d88c32)
    py5.fill(216, 140, 50, 76)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_strata_quads(np.flatnonzero(STRATA_ROLE == 1), t_sec, w, h))

    # Role 2: Celadon-Mist Pool Crest (#96b4b6)
    py5.fill(150, 180, 182, 58)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_strata_quads(np.flatnonzero(STRATA_ROLE == 2), t_sec, w, h))

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

