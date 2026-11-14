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
from lib.shaders import draw_fullscreen, load_shader
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 16
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED = random.uniform(10.0, 900.0)
CAM_DRIFT = (random.uniform(-2.0, 2.0), random.uniform(-1.0, 1.0))

field_shader = None

# Pre-generate semicircular hyperbolic geodesic ribbon families spanning the full-bleed canvas
NUM_ARCS = 42
ARC_PTS = 56
ARC_CENTER_X: np.ndarray
ARC_HORIZON_Y: np.ndarray
ARC_RADIUS: np.ndarray
ARC_THICKNESS: np.ndarray
ARC_CHANNEL: np.ndarray
ARC_SPEED: np.ndarray


def _init_hyperbolic_arcs(width: int, height: int) -> None:
    global ARC_CENTER_X, ARC_HORIZON_Y, ARC_RADIUS, ARC_THICKNESS, ARC_CHANNEL, ARC_SPEED

    rng = np.random.default_rng()
    ARC_CENTER_X = rng.uniform(-0.15 * width, 1.15 * width, size=NUM_ARCS).astype(np.float32)
    strata = np.linspace(0.14 * height, 0.88 * height, 6, dtype=np.float32)
    ARC_HORIZON_Y = strata[np.arange(NUM_ARCS) % 6] + rng.uniform(-28.0, 28.0, size=NUM_ARCS).astype(
        np.float32
    )
    ARC_RADIUS = rng.uniform(0.16 * height, 0.58 * height, size=NUM_ARCS).astype(np.float32)
    ARC_THICKNESS = rng.uniform(8.0, 24.0, size=NUM_ARCS).astype(np.float32)
    ARC_CHANNEL = np.arange(NUM_ARCS) % 3  # 0: Teal, 1: Coral, 2: Indigo
    ARC_SPEED = rng.uniform(0.18, 0.42, size=NUM_ARCS).astype(np.float32) * np.where(
        np.arange(NUM_ARCS) % 2 == 0, 1.0, -1.0
    )


def _build_geodesic_quads(
    centers_x: np.ndarray,
    horizons_y: np.ndarray,
    radii: np.ndarray,
    thickness: np.ndarray,
    direction: np.ndarray,
) -> np.ndarray:
    theta = np.linspace(0.03 * math.pi, 0.97 * math.pi, ARC_PTS, dtype=np.float32)[None, :]
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    half_w = (thickness[:, None] * 0.5) * (sin_t**0.6)
    r_inner = np.maximum(8.0, radii[:, None] - half_w)
    r_outer = radii[:, None] + half_w

    cx = centers_x[:, None]
    hy = horizons_y[:, None]
    sgn = direction[:, None]

    x_in = cx + r_inner * cos_t
    y_in = hy + sgn * r_inner * sin_t
    x_out = cx + r_outer * cos_t
    y_out = hy + sgn * r_outer * sin_t

    n_arcs = len(centers_x)
    quads = np.empty((n_arcs, ARC_PTS - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_in[:, :-1]
    quads[:, :, 0, 1] = y_in[:, :-1]
    quads[:, :, 1, 0] = x_out[:, :-1]
    quads[:, :, 1, 1] = y_out[:, :-1]
    quads[:, :, 2, 0] = x_out[:, 1:]
    quads[:, :, 2, 1] = y_out[:, 1:]
    quads[:, :, 3, 0] = x_in[:, 1:]
    quads[:, :, 3, 1] = y_in[:, 1:]
    return quads.reshape(-1, 2)


def setup() -> None:
    global field_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    field_shader = load_shader(SKETCH_DIR / "hyperbolic_risograph_geodesics.glsl")
    _init_hyperbolic_arcs(SIZE[0], SIZE[1])


def draw() -> None:
    t_sec = (py5.frame_count - 1) / float(FPS)
    w, _ = float(SIZE[0]), float(SIZE[1])

    # 1. Full-bleed PSL(2, Z) hyperbolic modular tessellation & risograph spot-ink shader
    draw_fullscreen(
        field_shader,
        seed=float(SEED),
        camDrift=CAM_DRIFT,
    )

    # 2. Hyperbolic geodesic arch ribbons drifting in depth across the full canvas
    scale_mod = np.exp(np.mod(t_sec * np.abs(ARC_SPEED) + np.arange(NUM_ARCS) * 0.27, 1.1) - 0.55)
    radii_t = ARC_RADIUS * scale_mod.astype(np.float32)
    centers_t = np.mod(
        ARC_CENTER_X + t_sec * ARC_SPEED * 180.0 + 0.2 * w,
        1.4 * w,
    ) - 0.2 * w
    direction = np.where(np.arange(NUM_ARCS) % 2 == 0, -1.0, 1.0).astype(np.float32)

    py5.no_stroke()
    # Channel 0: Translucent Teal Spot Ink (#169a8e)
    m0 = ARC_CHANNEL == 0
    verts_teal = _build_geodesic_quads(
        centers_t[m0], ARC_HORIZON_Y[m0], radii_t[m0], ARC_THICKNESS[m0], direction[m0]
    )
    py5.fill(22, 154, 142, 78)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(verts_teal)

    # Channel 1: Fluorescent Coral Spot Ink (#f05a46) with slight risograph misregistration
    m1 = ARC_CHANNEL == 1
    verts_coral = _build_geodesic_quads(
        centers_t[m1] + 10.0,
        ARC_HORIZON_Y[m1] - 7.0,
        radii_t[m1],
        ARC_THICKNESS[m1] * 0.9,
        direction[m1],
    )
    py5.fill(240, 90, 70, 84)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(verts_coral)

    # Channel 2: Deep Indigo Overprint Ink (#1e2d5c)
    m2 = ARC_CHANNEL == 2
    verts_indigo = _build_geodesic_quads(
        centers_t[m2] - 7.0,
        ARC_HORIZON_Y[m2] + 6.0,
        radii_t[m2],
        ARC_THICKNESS[m2] * 0.78,
        direction[m2],
    )
    py5.fill(30, 45, 92, 82)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(verts_indigo)

    # 3. Save frame, verify non-blank, and compile MP4 on final frame
    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
