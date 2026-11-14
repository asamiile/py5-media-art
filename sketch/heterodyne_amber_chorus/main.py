"""heterodyne_amber_chorus — Full-Bleed Heterodyne Carrier Chorus & Phase Interference.

Across a continuous edge-to-edge rich saturated color field of deep ultramarine
(#0a133c - #1e3eb8), crimson magenta (#b81e6c), signal vermilion (#ec4828), and
luminous amber gold (#f8b224), four frequency-modulated (FM) heterodyne carrier
waves drift at poly-rhythmic harmonic ratios (1:2:3:4). Layered over the GLSL
heterodyne beat-interference field, 44 continuous full-bleed vector carrier ribbons
and phase-slip harmonic nodes weave across the 3840x2160 canvas.

100% pure visual art — zero text, zero HUD panels.
"""

from __future__ import annotations

import math
from pathlib import Path
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

# ── Constants ──────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 900 frames (15s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

N_CARRIERS = 44
N_SAMPLES = 220

fx = PostFX(
    bloom=0.28,
    bloom_threshold=0.66,
    aberration=0.0014,
    tonemap=0.86,
    vignette=0.14,
    grain=0.016,
)
_shader = None

X_NORM: np.ndarray
Y_BASE: np.ndarray
CARRIER_ROLE: np.ndarray
CARRIER_PHASE: np.ndarray
CARRIER_K1: np.ndarray
CARRIER_K2: np.ndarray
CARRIER_K3: np.ndarray
CARRIER_DIR: np.ndarray


def _init_carriers() -> None:
    """Precompute 44 full-bleed poly-rhythmic heterodyne carrier wave parameters."""
    global X_NORM, Y_BASE, CARRIER_ROLE, CARRIER_PHASE, CARRIER_K1, CARRIER_K2, CARRIER_K3, CARRIER_DIR
    rng = np.random.default_rng()

    X_NORM = np.linspace(-0.52, 0.52, N_SAMPLES, dtype=np.float32)[None, :]  # (1, N_SAMPLES)
    Y_BASE = np.linspace(-0.48, 0.48, N_CARRIERS, dtype=np.float32)[:, None]  # (N_CARRIERS, 1)

    # Roles: 0 = Luminous Amber Gold (#f8b224), 1 = Signal Vermilion (#ec4828),
    # 2 = Crimson Magenta (#d62878), 3 = Warm Cream Highlight (#fcf2dc)
    roles = [0, 1, 2, 0, 3, 1, 0, 2] * 6
    CARRIER_ROLE = np.array(roles[:N_CARRIERS], dtype=np.int32)
    CARRIER_PHASE = rng.uniform(0.0, math.tau, size=(N_CARRIERS, 1)).astype(np.float32)
    CARRIER_K1 = rng.uniform(3.5, 6.5, size=(N_CARRIERS, 1)).astype(np.float32)
    CARRIER_K2 = rng.uniform(8.0, 13.5, size=(N_CARRIERS, 1)).astype(np.float32)
    CARRIER_K3 = rng.uniform(16.0, 24.0, size=(N_CARRIERS, 1)).astype(np.float32)
    CARRIER_DIR = np.where(np.arange(N_CARRIERS) % 2 == 0, 1.0, -1.0).astype(np.float32)[:, None]


def _draw_heterodyne_traces(u_loop: float, w: float, h: float) -> None:
    """Draw 44 full-bleed FM heterodyne carrier ribbons and phase-locked beat nodes."""
    theta = u_loop * math.tau

    # Poly-rhythmic phase interference of 3 harmonic wave trains (ratios 1 : 2 : 3)
    w1 = 0.036 * np.sin(X_NORM * math.pi * CARRIER_K1 + theta * CARRIER_DIR + CARRIER_PHASE)
    w2 = 0.022 * np.cos(X_NORM * math.pi * CARRIER_K2 - theta * 2.0 * CARRIER_DIR + CARRIER_PHASE * 1.7)
    w3 = 0.012 * np.sin(X_NORM * math.pi * CARRIER_K3 + theta * 3.0 + Y_BASE * 8.0)

    # Quantized raster step modulation along beat crests
    beat = np.cos(X_NORM * math.pi * 4.0 - theta * CARRIER_DIR + CARRIER_PHASE)
    quant_step = 0.010 * np.round(beat * 3.0) / 3.0

    y_pos = (Y_BASE + w1 + w2 + w3 + quant_step) * h + h * 0.5
    x_pos = (X_NORM + 0.5) * w  # (1, N_SAMPLES) broadcastable to (N_CARRIERS, N_SAMPLES)
    x_grid = np.broadcast_to(x_pos, (N_CARRIERS, N_SAMPLES))

    # Ribbon half-thickness modulated by heterodyne beat envelope
    half_t = (1.6 + 3.2 * (0.5 + 0.5 * np.sin(X_NORM * math.pi * 5.0 + theta * 2.0 + CARRIER_PHASE)) ** 2).astype(
        np.float32
    )

    # Build quads for all 44 ribbons: (N_CARRIERS, N_SAMPLES - 1, 4, 2)
    quads = np.empty((N_CARRIERS, N_SAMPLES - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_grid[:, :-1]
    quads[:, :, 0, 1] = y_pos[:, :-1] - half_t[:, :-1]
    quads[:, :, 1, 0] = x_grid[:, 1:]
    quads[:, :, 1, 1] = y_pos[:, 1:] - half_t[:, 1:]
    quads[:, :, 2, 0] = x_grid[:, 1:]
    quads[:, :, 2, 1] = y_pos[:, 1:] + half_t[:, 1:]
    quads[:, :, 3, 0] = x_grid[:, :-1]
    quads[:, :, 3, 1] = y_pos[:, :-1] + half_t[:, :-1]

    role_colors = [
        (248, 178, 36, 195),   # 0: Luminous Amber Gold (#f8b224)
        (236, 72, 40, 185),    # 1: Signal Vermilion (#ec4828)
        (214, 40, 120, 175),   # 2: Crimson Magenta (#d62878)
        (252, 242, 220, 210),  # 3: Warm Cream Highlight (#fcf2dc)
    ]

    py5.no_stroke()
    for role_id, (rc, gc, bc, ac) in enumerate(role_colors):
        idx = np.flatnonzero(CARRIER_ROLE == role_id)
        if len(idx) > 0:
            py5.fill(rc, gc, bc, ac)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(quads[idx].reshape(-1, 2))

    # Crisp phase-lock harmonic bridge ticks between adjacent carriers at beat antinodes
    sample_cols = list(range(6, N_SAMPLES - 6, 8))
    xs_sub = x_grid[:-1, sample_cols]
    y0_sub = y_pos[:-1, sample_cols]
    y1_sub = y_pos[1:, sample_cols]
    dy_sub = np.abs(y1_sub - y0_sub)

    # Connect adjacent carriers where phase interference pinches them close together
    bridge_mask = dy_sub < (h * 0.042)
    b_r, b_c = np.nonzero(bridge_mask)
    if len(b_r) > 0:
        bridge_segs = np.empty((len(b_r), 2, 2), dtype=np.float32)
        bridge_segs[:, 0, 0] = xs_sub[b_r, b_c]
        bridge_segs[:, 0, 1] = y0_sub[b_r, b_c]
        bridge_segs[:, 1, 0] = xs_sub[b_r, b_c]
        bridge_segs[:, 1, 1] = y1_sub[b_r, b_c]

        py5.no_fill()
        py5.stroke(252, 242, 220, 170)
        py5.stroke_weight(1.6)
        with py5.begin_shape(py5.LINES):
            py5.vertices(bridge_segs.reshape(-1, 2))


def setup() -> None:
    global _shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    _shader = load_shader(SKETCH_DIR / "heterodyne_amber_chorus.glsl")
    fx.setup()
    _init_carriers()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    w, h = float(SIZE[0]), float(SIZE[1])

    draw_fullscreen(_shader, u_loop=float(u_loop))
    _draw_heterodyne_traces(u_loop, w, h)
    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

