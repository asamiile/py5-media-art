"""sienna_capillary_glaze — Asymmetric Wet-on-Wet Sienna Glaze & Capillary Bloom.

An atmospheric, painterly color-field animation anchored by asymmetric off-center
tension: a concentrated lapis-ultramarine (#143474) and verdigris-turquoise
(#189c90) wet-on-wet pigment bloom nucleates in the upper-left golden-ratio
focal zone, sending concentric Naples-gold (#f6c438) capillary tide rings and
210 organic pigment veins sweeping across an expansive burnt-sienna (#701e12),
alizarin-madder (#a8281e), and raw-amber (#d66820) glaze field.

100% pure visual media art — zero text, zero HUD panels, zero bezels.
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

DURATION_SEC = 19
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1140 frames (19s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

fx = PostFX(
    bloom=0.16,
    bloom_threshold=0.76,
    aberration=0.0010,
    tonemap=0.24,
    vignette=0.12,
    grain=0.020,
)

# ── Asymmetric Capillary Vein & Granulation Constants ──────────────────
N_VEINS = 210
N_STEPS = 48
N_FLOCCULES = 420

VEIN_ANGLE0: np.ndarray
VEIN_R_START: np.ndarray
VEIN_R_SPAN: np.ndarray
VEIN_FREQ: np.ndarray
VEIN_PHASE: np.ndarray
VEIN_ROLE: np.ndarray
VEIN_WIDTH: np.ndarray
S_GRID: np.ndarray

FLOC_R0: np.ndarray
FLOC_ANG0: np.ndarray
FLOC_PHASE: np.ndarray
FLOC_SIZE: np.ndarray
FLOC_ROLE: np.ndarray

glaze_shader = None


def _init_capillaries() -> None:
    """Initialize asymmetric capillary veins radiating from the left-third anchor."""
    global VEIN_ANGLE0, VEIN_R_START, VEIN_R_SPAN, VEIN_FREQ, VEIN_PHASE, VEIN_ROLE, VEIN_WIDTH, S_GRID
    global FLOC_R0, FLOC_ANG0, FLOC_PHASE, FLOC_SIZE, FLOC_ROLE

    rng = np.random.default_rng()

    # 72% of capillary veins sweep rightward/diagonally into the expansive sienna negative space
    right_count = int(N_VEINS * 0.72)
    left_count = N_VEINS - right_count
    ang_right = rng.uniform(-0.42 * math.pi, 0.38 * math.pi, size=right_count)
    ang_other = rng.uniform(0.38 * math.pi, 1.58 * math.pi, size=left_count)
    VEIN_ANGLE0 = np.concatenate([ang_right, ang_other]).astype(np.float32)

    VEIN_R_START = rng.uniform(0.05, 0.34, size=N_VEINS).astype(np.float32)
    # Rightward veins stretch much farther across the canvas
    span_base = np.where(np.cos(VEIN_ANGLE0) > 0.0, 0.78, 0.36)
    VEIN_R_SPAN = (span_base * rng.uniform(0.55, 1.25, size=N_VEINS)).astype(np.float32)
    VEIN_FREQ = rng.uniform(2.2, 5.4, size=N_VEINS).astype(np.float32)
    VEIN_PHASE = rng.uniform(0.0, math.tau, size=N_VEINS).astype(np.float32)

    # 3 pigment roles: 0 = Naples Gold, 1 = Verdigris Turquoise, 2 = Warm Cream Highlight
    VEIN_ROLE = (np.arange(N_VEINS, dtype=np.int32) % 3)
    VEIN_WIDTH = rng.uniform(1.8, 3.8, size=N_VEINS).astype(np.float32)
    S_GRID = np.linspace(0.0, 1.0, N_STEPS, dtype=np.float32)

    # Mineral pigment floccules drifting along the wet-edge tide rings
    FLOC_R0 = rng.uniform(0.14, 0.92, size=N_FLOCCULES).astype(np.float32)
    FLOC_ANG0 = rng.uniform(-math.pi, math.pi, size=N_FLOCCULES).astype(np.float32)
    FLOC_PHASE = rng.uniform(0.0, math.tau, size=N_FLOCCULES).astype(np.float32)
    FLOC_SIZE = rng.uniform(2.6, 6.4, size=N_FLOCCULES).astype(np.float32)
    FLOC_ROLE = (np.arange(N_FLOCCULES, dtype=np.int32) % 3)


def _draw_capillary_overlays(u_loop: float, act_bloom: float, act_front: float) -> None:
    """Render vectorized capillary dendrites and wet-edge pigment floccules."""
    w, h = float(SIZE[0]), float(SIZE[1])
    aspect = w / h
    phase = u_loop * math.tau

    # Golden-ratio anchor matching GLSL: p = (-0.34, 0.12) in bottom-up aspect space
    ax = -0.34 + 0.04 * math.cos(phase)
    ay = 0.12 + 0.04 * math.sin(phase)

    s = S_GRID[None, :]  # (1, N_STEPS)
    # Outward capillary progression pulsed by multi-act envelope
    r_reach = VEIN_R_START[:, None] + s * VEIN_R_SPAN[:, None] * (0.78 + 0.26 * act_bloom)
    ang_meander = (
        VEIN_ANGLE0[:, None]
        + 0.18 * np.sin(s * VEIN_FREQ[:, None] * math.pi - phase + VEIN_PHASE[:, None])
        + 0.08 * np.cos(s * 7.0 + phase * 2.0)
    )

    # Anisotropic horizontal stretch matching GLSL (d1.x /= 0.72 -> 1.38x wider reach)
    px = ax + r_reach * np.cos(ang_meander) * 1.36
    py = ay + r_reach * np.sin(ang_meander) * 0.94

    # Convert bottom-up aspect space to top-down screen pixels
    sx = (px / aspect + 0.5) * w
    sy = (0.5 - py) * h

    dx = np.gradient(sx, axis=1)
    dy = np.gradient(sy, axis=1)
    inv_len = 1.0 / np.maximum(np.hypot(dx, dy), 1e-4)
    nx = -dy * inv_len
    ny = dx * inv_len

    # Taper width smoothly at root and tip
    taper = np.clip(np.sin(s * math.pi), 0.0, 1.0) ** 0.55
    hw = VEIN_WIDTH[:, None] * taper * (0.75 + 0.30 * act_front)

    x_up = sx + nx * hw
    y_up = sy + ny * hw
    x_dn = sx - nx * hw
    y_dn = sy - ny * hw

    quads = np.empty((N_VEINS, N_STEPS - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_up[:, :-1]
    quads[:, :, 0, 1] = y_up[:, :-1]
    quads[:, :, 1, 0] = x_up[:, 1:]
    quads[:, :, 1, 1] = y_up[:, 1:]
    quads[:, :, 2, 0] = x_dn[:, 1:]
    quads[:, :, 2, 1] = y_dn[:, 1:]
    quads[:, :, 3, 0] = x_dn[:, :-1]
    quads[:, :, 3, 1] = y_dn[:, :-1]

    role_rgba = (
        (246, 196, 56, 155),   # 0: Naples Gold (#f6c438)
        (24, 168, 154, 150),   # 1: Verdigris Turquoise (#18a89a)
        (249, 238, 218, 135),  # 2: Warm Cream Highlight (#f9eeda)
    )

    py5.no_stroke()
    for r_id, rgba in enumerate(role_rgba):
        mask = VEIN_ROLE == r_id
        verts = quads[mask].reshape(-1, 2)
        py5.fill(*rgba)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(verts)

    # Draw wet-edge pigment granulation floccules drifting along the capillary tide fronts
    r_floc = FLOC_R0 * (0.82 + 0.24 * act_bloom) + 0.04 * np.sin(FLOC_PHASE + phase)
    a_floc = FLOC_ANG0 + 0.12 * np.cos(FLOC_PHASE - phase)
    fpx = ax + r_floc * np.cos(a_floc) * 1.38
    fpy = ay + r_floc * np.sin(a_floc) * 0.94
    fsx = (fpx / aspect + 0.5) * w
    fsy = (0.5 - fpy) * h
    frad = FLOC_SIZE * (0.75 + 0.35 * np.sin(FLOC_PHASE + phase * 2.0))

    f_quads = np.empty((N_FLOCCULES, 4, 2), dtype=np.float32)
    f_quads[:, 0, 0] = fsx - frad
    f_quads[:, 0, 1] = fsy
    f_quads[:, 1, 0] = fsx
    f_quads[:, 1, 1] = fsy - frad
    f_quads[:, 2, 0] = fsx + frad
    f_quads[:, 2, 1] = fsy
    f_quads[:, 3, 0] = fsx
    f_quads[:, 3, 1] = fsy + frad

    floc_rgba = (
        (246, 196, 56, 185),
        (28, 182, 168, 175),
        (249, 238, 218, 170),
    )
    for r_id, rgba in enumerate(floc_rgba):
        mask = FLOC_ROLE == r_id
        py5.fill(*rgba)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(f_quads[mask].reshape(-1, 2))


def setup() -> None:
    global glaze_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    glaze_shader = load_shader(str(SKETCH_DIR / "sienna_capillary_glaze.glsl"))
    fx.setup()
    _init_capillaries()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    phase = u_loop * math.tau

    # Multi-act temporal envelopes (seamless periodic over [0, TAU]):
    # Act I: Nucleation | Act II: Peak capillary bloom at u_loop = 0.5 | Act III: Glaze settling
    act_bloom = 0.5 - 0.5 * math.cos(phase)
    act_front = 0.5 + 0.5 * math.sin(phase * 2.0 - 0.4)

    glaze_shader.set("u_resolution", float(SIZE[0]), float(SIZE[1]))
    glaze_shader.set("u_phase", float(phase))
    glaze_shader.set("u_act_bloom", float(act_bloom))
    glaze_shader.set("u_act_front", float(act_front))
    draw_fullscreen(glaze_shader)

    _draw_capillary_overlays(u_loop, act_bloom, act_front)

    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

