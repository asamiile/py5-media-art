"""scanline_overprint_matrix — Multi-Plane Risograph Scanline Polyptych & Depth Drift

An edge-to-edge rhythmic cellular matrix of analog cathode scanlines, halftone
signal registers, and phase-slipped frequency gratings printed across a warm cream
paper ground (#efe9dc) in three translucent overlapping Risograph spot inks:
fluorescent coral (#f05442), peacock teal (#14968c), and deep indigo (#1c2a5e).
A smooth spatial camera traverses through three depth-parallax register planes.

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

DURATION_SEC = 19
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1140 frames
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED = random.uniform(10.0, 900.0)

fx = PostFX(
    bloom=0.14,
    bloom_threshold=0.82,
    aberration=0.0014,
    tonemap=0.25,
    vignette=0.08,
    grain=0.022,
)
matrix_shader = None

# Parallax foreground register bars in three Risograph spot-ink channels
NUM_BARS = 144
BAR_U: np.ndarray
BAR_V: np.ndarray
BAR_W: np.ndarray
BAR_H: np.ndarray
BAR_DEPTH: np.ndarray
BAR_ROLE: np.ndarray
BAR_FREQ: np.ndarray
BAR_PHASE: np.ndarray


def _init_register_bars() -> None:
    global BAR_U, BAR_V, BAR_W, BAR_H, BAR_DEPTH, BAR_ROLE, BAR_FREQ, BAR_PHASE
    rng = np.random.default_rng()

    # Align bars to a rhythmic 12x6 cellular grid in world space u, v in [-1.5, 1.5]
    cols = rng.integers(-6, 6, size=NUM_BARS)
    rows = rng.integers(-4, 4, size=NUM_BARS)

    BAR_U = (cols + 0.5) * 0.28 + rng.choice([-0.06, 0.0, 0.06], size=NUM_BARS).astype(np.float32)
    BAR_V = (rows + 0.5) * 0.28 + rng.choice([-0.05, 0.0, 0.05], size=NUM_BARS).astype(np.float32)
    BAR_W = rng.uniform(0.035, 0.22, size=NUM_BARS).astype(np.float32)
    BAR_H = rng.uniform(0.008, 0.042, size=NUM_BARS).astype(np.float32)
    BAR_DEPTH = rng.choice([0.75, 1.15, 1.65], size=NUM_BARS).astype(np.float32)

    # Role: 0 = Fluorescent Coral (#f05442), 1 = Peacock Teal (#14968c), 2 = Deep Indigo (#1c2a5e)
    BAR_ROLE = np.arange(NUM_BARS) % 3
    BAR_FREQ = rng.uniform(2.0, 6.0, size=NUM_BARS).astype(np.float32)
    BAR_PHASE = rng.uniform(0.0, math.tau, size=NUM_BARS).astype(np.float32)


def _build_parallax_quads(indices: np.ndarray, t_norm: float, cam_x: float, cam_y: float, cam_zoom: float, w: float, h: float) -> np.ndarray:
    if len(indices) == 0:
        return np.empty((0, 2), dtype=np.float32)

    tau = math.tau
    depth = BAR_DEPTH[indices]
    # Parallax projection matching camera traversal
    u_rel = np.mod(BAR_U[indices] - cam_x * depth + 1.68, 3.36) - 1.68
    v_rel = np.mod(BAR_V[indices] - cam_y * depth + 1.12, 2.24) - 1.12

    # Signal phase slip & quantized scanline jitter
    jitter = 0.035 * np.sin(t_norm * tau * BAR_FREQ[indices] + BAR_PHASE[indices])
    u_scr = (u_rel + jitter) * cam_zoom * (0.65 + 0.35 * depth)
    v_scr = v_rel * cam_zoom * (0.65 + 0.35 * depth)

    cx = w * 0.5 + u_scr * h
    cy = h * 0.5 + v_scr * h

    pulse = 0.65 + 0.35 * np.cos(t_norm * tau * 3.0 + BAR_PHASE[indices])
    hw = BAR_W[indices] * h * 0.5 * cam_zoom * pulse
    hh = BAR_H[indices] * h * 0.5 * cam_zoom

    n_b = len(indices)
    quads = np.empty((n_b, 4, 2), dtype=np.float32)
    quads[:, 0, 0] = cx - hw
    quads[:, 0, 1] = cy - hh
    quads[:, 1, 0] = cx + hw
    quads[:, 1, 1] = cy - hh
    quads[:, 2, 0] = cx + hw
    quads[:, 2, 1] = cy + hh
    quads[:, 3, 0] = cx - hw
    quads[:, 3, 1] = cy + hh
    return quads.reshape(-1, 2)


def setup() -> None:
    global matrix_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    matrix_shader = load_shader(SKETCH_DIR / "scanline_overprint_matrix.glsl")
    fx.setup()
    _init_register_bars()


def draw() -> None:
    t_norm = (py5.frame_count - 1) / float(TOTAL_FRAMES)
    tau = math.tau
    w, h = float(SIZE[0]), float(SIZE[1])

    # Smooth Spatial Camera / Depth Traversal trajectory
    cam_x = t_norm * 0.85 + 0.14 * math.sin(t_norm * tau)
    cam_y = t_norm * 0.42 + 0.10 * math.cos(t_norm * tau)
    cam_zoom = 1.0 + 0.22 * math.sin(t_norm * tau)

    # 1. Fullscreen GPU multi-plane Risograph scanline & halftone polyptych shader
    draw_fullscreen(
        matrix_shader,
        seed=float(SEED),
        camX=float(cam_x),
        camY=float(cam_y),
        camZoom=float(cam_zoom),
    )

    # 2. Foreground parallax signal registration bars in translucent Risograph spot inks
    py5.no_stroke()

    # Spot Ink 0: Fluorescent Coral (#f05442)
    py5.fill(240, 84, 66, 138)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_parallax_quads(np.flatnonzero(BAR_ROLE == 0), t_norm, cam_x, cam_y, cam_zoom, w, h))

    # Spot Ink 1: Peacock Teal (#14968c)
    py5.fill(20, 150, 140, 138)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_parallax_quads(np.flatnonzero(BAR_ROLE == 1), t_norm, cam_x, cam_y, cam_zoom, w, h))

    # Spot Ink 2: Deep Indigo (#1c2a5e)
    py5.fill(28, 42, 94, 152)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_parallax_quads(np.flatnonzero(BAR_ROLE == 2), t_norm, cam_x, cam_y, cam_zoom, w, h))

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
