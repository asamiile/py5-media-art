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
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED = random.uniform(10.0, 900.0)
DRIFT_ANGLE = random.uniform(-0.45, 0.45)
DRIFT_DIR = (math.cos(DRIFT_ANGLE), math.sin(DRIFT_ANGLE))

fx = PostFX(
    bloom=0.45,
    bloom_threshold=0.56,
    tonemap=0.95,
    vignette=0.18,
    grain=0.025,
)
field_shader = None

# Pre-generate organic boundary-nucleated wash ribbons that grow inward
NUM_RIBBONS = 56
NUM_NODES = 48
RIBBON_BASE_X: np.ndarray
RIBBON_BASE_Y: np.ndarray
RIBBON_NORMAL_X: np.ndarray
RIBBON_NORMAL_Y: np.ndarray
RIBBON_HALF_W: np.ndarray
RIBBON_PHASE: np.ndarray
RIBBON_IS_ACCENT: np.ndarray


def _init_capillary_ribbons(width: int, height: int) -> None:
    global RIBBON_BASE_X, RIBBON_BASE_Y, RIBBON_NORMAL_X, RIBBON_NORMAL_Y
    global RIBBON_HALF_W, RIBBON_PHASE, RIBBON_IS_ACCENT

    rng = np.random.default_rng()
    s = np.linspace(0.0, 1.0, NUM_NODES, dtype=np.float32)

    bx = np.zeros((NUM_RIBBONS, NUM_NODES), dtype=np.float32)
    by = np.zeros((NUM_RIBBONS, NUM_NODES), dtype=np.float32)
    nx = np.zeros((NUM_RIBBONS, NUM_NODES), dtype=np.float32)
    ny = np.zeros((NUM_RIBBONS, NUM_NODES), dtype=np.float32)
    hw = np.zeros((NUM_RIBBONS, NUM_NODES), dtype=np.float32)

    for i in range(NUM_RIBBONS):
        edge = i % 4
        if edge == 0:  # Left boundary growing right
            x0 = 0.0
            y0 = rng.uniform(0.04, 0.96) * height
            x1 = rng.uniform(0.45, 0.72) * width
            y1 = np.clip(y0 + rng.uniform(-0.28, 0.28) * height, 0.05 * height, 0.95 * height)
        elif edge == 1:  # Right boundary growing left
            x0 = float(width)
            y0 = rng.uniform(0.04, 0.96) * height
            x1 = rng.uniform(0.28, 0.55) * width
            y1 = np.clip(y0 + rng.uniform(-0.28, 0.28) * height, 0.05 * height, 0.95 * height)
        elif edge == 2:  # Top boundary growing down
            x0 = rng.uniform(0.06, 0.94) * width
            y0 = 0.0
            x1 = np.clip(x0 + rng.uniform(-0.22, 0.22) * width, 0.08 * width, 0.92 * width)
            y1 = rng.uniform(0.42, 0.68) * height
        else:  # Bottom boundary growing up
            x0 = rng.uniform(0.06, 0.94) * width
            y0 = float(height)
            x1 = np.clip(x0 + rng.uniform(-0.22, 0.22) * width, 0.08 * width, 0.92 * width)
            y1 = rng.uniform(0.32, 0.58) * height

        dx = x1 - x0
        dy = y1 - y0
        length = math.hypot(dx, dy) + 1e-5
        perp_x = -dy / length
        perp_y = dx / length

        freq1 = rng.uniform(1.8, 3.6) * math.pi
        freq2 = rng.uniform(4.2, 7.5) * math.pi
        p1 = rng.uniform(0.0, math.tau)
        p2 = rng.uniform(0.0, math.tau)
        amp = rng.uniform(42.0, 136.0)

        meander = amp * np.sin(s * freq1 + p1) * np.sin(s * math.pi) + (amp * 0.38) * np.cos(
            s * freq2 + p2
        ) * (s**0.7)

        bx[i] = x0 + dx * s + perp_x * meander
        by[i] = y0 + dy * s + perp_y * meander
        nx[i] = perp_x
        ny[i] = perp_y
        max_w = rng.uniform(3.5, 11.5)
        hw[i] = max_w * np.sin(s * math.pi) * (1.0 - 0.55 * s)

    RIBBON_BASE_X = bx
    RIBBON_BASE_Y = by
    RIBBON_NORMAL_X = nx
    RIBBON_NORMAL_Y = ny
    RIBBON_HALF_W = hw
    RIBBON_PHASE = rng.uniform(0.0, math.tau, size=(NUM_RIBBONS, 1)).astype(np.float32)
    RIBBON_IS_ACCENT = (np.arange(NUM_RIBBONS) % 4 == 0)


def _build_ribbon_quads(
    cx: np.ndarray,
    cy: np.ndarray,
    nx: np.ndarray,
    ny: np.ndarray,
    half_w: np.ndarray,
) -> np.ndarray:
    x_left = cx - nx * half_w
    y_left = cy - ny * half_w
    x_right = cx + nx * half_w
    y_right = cy + ny * half_w

    n_ribbons, n_pts = cx.shape
    quads = np.empty((n_ribbons, n_pts - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_left[:, :-1]
    quads[:, :, 0, 1] = y_left[:, :-1]
    quads[:, :, 1, 0] = x_right[:, :-1]
    quads[:, :, 1, 1] = y_right[:, :-1]
    quads[:, :, 2, 0] = x_right[:, 1:]
    quads[:, :, 2, 1] = y_right[:, 1:]
    quads[:, :, 3, 0] = x_left[:, 1:]
    quads[:, :, 3, 1] = y_left[:, 1:]
    return quads.reshape(-1, 2)


def setup() -> None:
    global field_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    field_shader = load_shader(SKETCH_DIR / "cinnabar_ink_fronts.glsl")
    fx.setup()
    _init_capillary_ribbons(SIZE[0], SIZE[1])


def draw() -> None:
    t_sec = (py5.frame_count - 1) / float(FPS)
    progress = (py5.frame_count - 1) / float(TOTAL_FRAMES)

    # 1. Fullscreen GPU domain-warped ink front & collision seam shader
    draw_fullscreen(
        field_shader,
        duration=float(DURATION_SEC),
        seed=float(SEED),
        driftDir=DRIFT_DIR,
    )

    # 2. Tapered organic sumi/cinnabar capillary wash ribbons growing inward from canvas edges
    s = np.linspace(0.0, 1.0, NUM_NODES, dtype=np.float32)[None, :]
    wave_disp = (
        32.0 * np.sin(s * 7.5 - t_sec * 1.85 + RIBBON_PHASE)
        + 14.0 * np.cos(s * 14.0 - t_sec * 2.9 + RIBBON_PHASE * 1.7)
    ) * (s**0.65)

    px = RIBBON_BASE_X + RIBBON_NORMAL_X * wave_disp
    py_coords = RIBBON_BASE_Y + RIBBON_NORMAL_Y * wave_disp

    reach = min(1.0, 0.42 + 0.58 * math.sin(progress * math.pi * 0.92 + 0.15))
    active_nodes = max(8, int(NUM_NODES * reach))

    silver_mask = ~RIBBON_IS_ACCENT
    cinnabar_mask = RIBBON_IS_ACCENT

    silver_verts = _build_ribbon_quads(
        px[silver_mask, :active_nodes],
        py_coords[silver_mask, :active_nodes],
        RIBBON_NORMAL_X[silver_mask, :active_nodes],
        RIBBON_NORMAL_Y[silver_mask, :active_nodes],
        RIBBON_HALF_W[silver_mask, :active_nodes],
    )
    cinnabar_verts = _build_ribbon_quads(
        px[cinnabar_mask, :active_nodes],
        py_coords[cinnabar_mask, :active_nodes],
        RIBBON_NORMAL_X[cinnabar_mask, :active_nodes],
        RIBBON_NORMAL_Y[cinnabar_mask, :active_nodes],
        RIBBON_HALF_W[cinnabar_mask, :active_nodes] * 0.85,
    )

    py5.no_stroke()
    py5.fill(198, 212, 228, 48)  # Frosted silver wash (#c6d4e4)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(silver_verts)

    py5.fill(232, 82, 52, 96)  # Single accent hue: Molten cinnabar front seams (#e85234)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(cinnabar_verts)

    # 3. Apply PostFX finishing pass (subtle bloom on cinnabar ridges + filmic grain)
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
