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

DURATION_SEC = 17
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED = random.uniform(10.0, 900.0)

fx = PostFX(
    bloom=0.22,
    bloom_threshold=0.72,
    tonemap=0.92,
    aberration=0.0024,
    vignette=0.08,
    grain=0.022,
)
field_shader = None

# Pre-generate constructivist signal shutter bars that slide and shear across polyptych cells
NUM_BARS = 96
BAR_CELL_X: np.ndarray
BAR_CELL_Y: np.ndarray
BAR_CELL_W: np.ndarray
BAR_CELL_H: np.ndarray
BAR_FREQ: np.ndarray
BAR_PHASE: np.ndarray
BAR_COLOR_ROLE: np.ndarray
BAR_VERTICAL: np.ndarray


def _init_signal_bars(width: int, height: int) -> None:
    global BAR_CELL_X, BAR_CELL_Y, BAR_CELL_W, BAR_CELL_H
    global BAR_FREQ, BAR_PHASE, BAR_COLOR_ROLE, BAR_VERTICAL

    rng = np.random.default_rng()
    cols, rows = 8, 5
    cw = width / float(cols)
    ch = height / float(rows)

    cx = rng.integers(0, cols, size=NUM_BARS)
    cy = rng.integers(0, rows, size=NUM_BARS)

    BAR_CELL_X = (cx * cw).astype(np.float32)
    BAR_CELL_Y = (cy * ch).astype(np.float32)
    BAR_CELL_W = np.full(NUM_BARS, cw, dtype=np.float32)
    BAR_CELL_H = np.full(NUM_BARS, ch, dtype=np.float32)
    BAR_FREQ = rng.uniform(1.2, 3.8, size=NUM_BARS).astype(np.float32)
    BAR_PHASE = rng.uniform(0.0, math.tau, size=NUM_BARS).astype(np.float32)
    BAR_COLOR_ROLE = np.arange(NUM_BARS) % 4  # 0: Vermilion, 1: Bone White, 2: Ultramarine, 3: Ochre
    BAR_VERTICAL = rng.random(NUM_BARS) < 0.5


def _build_shutter_quads(indices: np.ndarray, t_sec: float, act_intensity: float) -> np.ndarray:
    x0 = BAR_CELL_X[indices]
    y0 = BAR_CELL_Y[indices]
    cw = BAR_CELL_W[indices]
    ch = BAR_CELL_H[indices]
    freq = BAR_FREQ[indices]
    phase = BAR_PHASE[indices]
    vert = BAR_VERTICAL[indices]

    # Quantized step motion (digital register stepping)
    raw_u = 0.5 + 0.42 * np.sin(t_sec * freq + phase)
    quant_steps = 8.0
    u_pos = np.where(
        act_intensity > 0.35,
        np.floor(raw_u * quant_steps) / quant_steps,
        raw_u,
    )

    thickness_frac = 0.08 + 0.10 * act_intensity * np.abs(np.cos(t_sec * freq * 0.7 + phase))
    pad = 8.0

    xa = np.where(vert, x0 + cw * u_pos, x0 + pad)
    xb = np.where(vert, np.minimum(x0 + cw - pad, xa + cw * thickness_frac), x0 + cw - pad)
    ya = np.where(vert, y0 + pad, y0 + ch * u_pos)
    yb = np.where(vert, y0 + ch - pad, np.minimum(y0 + ch - pad, ya + ch * thickness_frac))

    n = len(indices)
    quads = np.empty((n, 4, 2), dtype=np.float32)
    quads[:, 0, 0] = xa
    quads[:, 0, 1] = ya
    quads[:, 1, 0] = xb
    quads[:, 1, 1] = ya
    quads[:, 2, 0] = xb
    quads[:, 2, 1] = yb
    quads[:, 3, 0] = xa
    quads[:, 3, 1] = yb
    return quads.reshape(-1, 2)


def setup() -> None:
    global field_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    field_shader = load_shader(SKETCH_DIR / "bitplane_moire_polyptych.glsl")
    fx.setup()
    _init_signal_bars(SIZE[0], SIZE[1])


def draw() -> None:
    t_sec = (py5.frame_count - 1) / float(FPS)
    u = (py5.frame_count - 1) / float(TOTAL_FRAMES)

    # Multi-act intensity envelope (peaks during Act II & Act III, resolves cleanly in Act IV)
    act_intensity = math.sin(u * math.pi) ** 1.3

    # 1. Fullscreen GPU polyptych bitplane XOR & moiré interferometry shader
    draw_fullscreen(
        field_shader,
        duration=float(DURATION_SEC),
        seed=float(SEED),
    )

    # 2. Constructivist quantized signal shutter blocks batched by color role via py5.QUADS
    py5.no_stroke()

    # Role 0: Signal Vermilion (#e63426)
    py5.fill(230, 52, 38, 215)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_shutter_quads(np.flatnonzero(BAR_COLOR_ROLE == 0), t_sec, act_intensity))

    # Role 1: Crisp Bone White (#f2efe9)
    py5.fill(242, 239, 233, 225)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_shutter_quads(np.flatnonzero(BAR_COLOR_ROLE == 1), t_sec, act_intensity))

    # Role 2: International Ultramarine (#183ad4)
    py5.fill(24, 58, 212, 215)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_shutter_quads(np.flatnonzero(BAR_COLOR_ROLE == 2), t_sec, act_intensity))

    # Role 3: Cadmium Ochre Phase Pulse (#f2b418)
    py5.fill(242, 180, 24, 225)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_shutter_quads(np.flatnonzero(BAR_COLOR_ROLE == 3), t_sec, act_intensity))

    # 3. Apply PostFX (subtle RGB chromatic aberration & filmic tone-map)
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

