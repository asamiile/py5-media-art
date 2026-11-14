"""basalt_fault_strata — Diagonal Basalt Tectonic Strata & Constructivist Shear

A diagonally stratified tectonic fault and columnar shear landscape sweeping at
a 25-degree angle across a stark constructivist carbon-black ground (#0f1116).
Bold graphic fault blocks in crisp bone white (#f3f0e8), signal vermilion
(#e83424), international ultramarine (#1c3ed6), and cadmium ochre (#f2b218)
slip and interlock along propagating seismic shear planes.

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

DURATION_SEC = 22
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1320 frames
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED = random.uniform(10.0, 900.0)
STRATA_ANGLE = -0.42  # ~-24 degrees diagonal tectonic sweep across the 3840x2160 canvas

fx = PostFX(
    bloom=0.22,
    bloom_threshold=0.72,
    aberration=0.0012,
    tonemap=0.94,
    vignette=0.14,
    grain=0.018,
)
strata_shader = None

# Foreground constructivist tectonic shear blocks sliding along the diagonal fault strata
NUM_BANDS = 22
BLOCKS_PER_BAND = 14
NUM_BLOCKS = NUM_BANDS * BLOCKS_PER_BAND  # 308 blocks

BLK_BAND_V: np.ndarray
BLK_U0: np.ndarray
BLK_LEN: np.ndarray
BLK_THICK: np.ndarray
BLK_SPEED: np.ndarray
BLK_ROLE: np.ndarray
BLK_PHASE: np.ndarray


def _init_fault_blocks() -> None:
    global BLK_BAND_V, BLK_U0, BLK_LEN, BLK_THICK, BLK_SPEED, BLK_ROLE, BLK_PHASE
    rng = np.random.default_rng()

    band_vs = np.linspace(-0.88, 0.88, NUM_BANDS, dtype=np.float32)
    band_dirs = np.where(np.arange(NUM_BANDS) % 2 == 0, 1.0, -1.0).astype(np.float32)
    band_speeds = band_dirs * rng.uniform(0.18, 0.42, size=NUM_BANDS).astype(np.float32)

    BLK_BAND_V = np.repeat(band_vs, BLOCKS_PER_BAND) + rng.uniform(-0.012, 0.012, size=NUM_BLOCKS).astype(np.float32)
    BLK_SPEED = np.repeat(band_speeds, BLOCKS_PER_BAND)
    BLK_U0 = rng.uniform(-1.45, 1.45, size=NUM_BLOCKS).astype(np.float32)
    BLK_LEN = rng.uniform(0.06, 0.28, size=NUM_BLOCKS).astype(np.float32)
    BLK_THICK = rng.uniform(0.010, 0.036, size=NUM_BLOCKS).astype(np.float32)
    BLK_PHASE = rng.uniform(0.0, math.tau, size=NUM_BLOCKS).astype(np.float32)

    # Role: 0 = Crisp Bone White (#f3f0e8), 1 = Signal Vermilion (#e83424),
    # 2 = International Ultramarine (#1c3ed6), 3 = Cadmium Ochre (#f2b218)
    r_val = rng.random(NUM_BLOCKS)
    BLK_ROLE = np.zeros(NUM_BLOCKS, dtype=np.int32)
    BLK_ROLE[r_val > 0.34] = 1
    BLK_ROLE[r_val > 0.62] = 2
    BLK_ROLE[r_val > 0.84] = 3


def _build_tectonic_quads(indices: np.ndarray, t_sec: float, w: float, h: float) -> np.ndarray:
    if len(indices) == 0:
        return np.empty((0, 2), dtype=np.float32)

    u_center = np.mod(BLK_U0[indices] + t_sec * BLK_SPEED[indices] + 1.50, 3.00) - 1.50
    v_base = BLK_BAND_V[indices]
    ph = BLK_PHASE[indices]

    # Propagating tectonic fault step offset (matches GLSL fault shear wave)
    fault_step = 0.042 * np.tanh(3.5 * np.sin(u_center * 4.5 - t_sec * 1.4 + v_base * 3.0))
    v_center = v_base + fault_step

    half_l = BLK_LEN[indices] * (0.72 + 0.28 * np.sin(t_sec * 1.8 + ph)) * 0.5
    half_t = BLK_THICK[indices] * 0.5

    # Local corners in rotated (u, v) space with slight constructivist shear slant
    slant = 0.018
    u0 = u_center - half_l
    u1 = u_center + half_l
    v0 = v_center - half_t
    v1 = v_center + half_t

    cu = np.stack([u0 - slant, u1 - slant, u1 + slant, u0 + slant], axis=1)
    cv = np.stack([v0, v0, v1, v1], axis=1)

    cos_a = math.cos(STRATA_ANGLE)
    sin_a = math.sin(STRATA_ANGLE)

    sx = w * 0.5 + (cu * cos_a - cv * sin_a) * h
    sy = h * 0.5 + (cu * sin_a + cv * cos_a) * h

    quads = np.stack([sx, sy], axis=-1).astype(np.float32)
    return quads.reshape(-1, 2)


def setup() -> None:
    global strata_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    strata_shader = load_shader(SKETCH_DIR / "basalt_fault_strata.glsl")
    fx.setup()
    _init_fault_blocks()


def draw() -> None:
    t_sec = (py5.frame_count - 1) / float(FPS)
    w, h = float(SIZE[0]), float(SIZE[1])

    # 1. Fullscreen GPU diagonal constructivist basalt fault strata shader
    draw_fullscreen(
        strata_shader,
        seed=float(SEED),
        strataAngle=float(STRATA_ANGLE),
    )

    # 2. Foreground constructivist tectonic shear blocks batched by color role via py5.QUADS
    py5.no_stroke()

    # Role 2: International Ultramarine (#1c3ed6)
    py5.fill(28, 62, 214, 230)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_tectonic_quads(np.flatnonzero(BLK_ROLE == 2), t_sec, w, h))

    # Role 3: Cadmium Ochre (#f2b218)
    py5.fill(242, 178, 24, 235)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_tectonic_quads(np.flatnonzero(BLK_ROLE == 3), t_sec, w, h))

    # Role 1: Signal Vermilion (#e83424)
    py5.fill(232, 52, 36, 240)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_tectonic_quads(np.flatnonzero(BLK_ROLE == 1), t_sec, w, h))

    # Role 0: Crisp Bone White (#f3f0e8)
    py5.fill(243, 240, 232, 242)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_tectonic_quads(np.flatnonzero(BLK_ROLE == 0), t_sec, w, h))

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

