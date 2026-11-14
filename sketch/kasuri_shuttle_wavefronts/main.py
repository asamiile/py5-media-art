"""kasuri_shuttle_wavefronts — Stratified Kasuri Ikat Bands & Traveling Shuttle Wavefronts.

Across a full-canvas high-key warm kozo washi ground (#eee8db - #e2dac9), seven
diagonally swept kasuri (ikat) resist-dyed textile strata in iron-gall slate
(#24333d), mineral indigo (#324e62), burnt sienna (#bc4e30), raw gold ochre
(#ce8e2a), and celadon sage (#46736c) experience continuous directional advection
and traveling shed wavefronts. Layered over the GLSL twill-weave shader, 35
calligraphic warp ribbons and 420 advecting weft-shuttle thread segments sweep
diagonally across the 3840x2160 canvas.

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

DURATION_SEC = 17
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1020 frames (17s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SWEEP_ANGLE = -0.3316125  # Matches GLSL -19 deg diagonal sweep
N_WARP_RIBBONS = 35
N_SAMPLES = 180
N_SHUTTLES = 420

# Keep tonemap low (0.20) so the high-key warm washi paper stays luminous
fx = PostFX(
    bloom=0.15,
    bloom_threshold=0.78,
    aberration=0.0010,
    tonemap=0.20,
    vignette=0.10,
    grain=0.016,
)
_shader = None

U_SAMPLES: np.ndarray
WARP_V0: np.ndarray
WARP_DIR: np.ndarray
WARP_PHASE: np.ndarray
WARP_ROLE: np.ndarray

SHUTTLE_U0: np.ndarray
SHUTTLE_BAND: np.ndarray
SHUTTLE_V_JITTER: np.ndarray
SHUTTLE_LEN: np.ndarray
SHUTTLE_THICK: np.ndarray
SHUTTLE_ROLE: np.ndarray
SHUTTLE_DIR: np.ndarray


def _init_weave() -> None:
    """Precompute 35 stratified warp ribbons and 420 directional weft shuttle threads."""
    global U_SAMPLES, WARP_V0, WARP_DIR, WARP_PHASE, WARP_ROLE
    global SHUTTLE_U0, SHUTTLE_BAND, SHUTTLE_V_JITTER, SHUTTLE_LEN, SHUTTLE_THICK, SHUTTLE_ROLE, SHUTTLE_DIR

    rng = np.random.default_rng()

    U_SAMPLES = np.linspace(-1.12, 1.12, N_SAMPLES, dtype=np.float32)
    WARP_V0 = np.linspace(-0.48, 0.48, N_WARP_RIBBONS, dtype=np.float32)
    WARP_DIR = np.where((np.arange(N_WARP_RIBBONS) // 5) % 2 == 0, 1.0, -1.0).astype(np.float32)
    WARP_PHASE = (np.arange(N_WARP_RIBBONS, dtype=np.float32) // 5) * 1.1
    WARP_ROLE = (np.arange(N_WARP_RIBBONS) % 4).astype(np.int32)

    # 420 directional weft-shuttle threads advecting continuously along the 7 strata
    SHUTTLE_BAND = rng.integers(0, 7, size=N_SHUTTLES).astype(np.int32)
    SHUTTLE_DIR = np.where(SHUTTLE_BAND % 2 == 0, 1.0, -1.0).astype(np.float32)
    SHUTTLE_U0 = rng.uniform(-1.15, 1.15, size=N_SHUTTLES).astype(np.float32)
    SHUTTLE_V_JITTER = rng.uniform(-0.042, 0.042, size=N_SHUTTLES).astype(np.float32)
    SHUTTLE_LEN = rng.uniform(0.055, 0.165, size=N_SHUTTLES).astype(np.float32)
    SHUTTLE_THICK = rng.uniform(0.0025, 0.0068, size=N_SHUTTLES).astype(np.float32)
    SHUTTLE_ROLE = rng.integers(0, 4, size=N_SHUTTLES).astype(np.int32)


def _build_ribbon_quads(
    u: np.ndarray,
    v: np.ndarray,
    half_t: np.ndarray,
    w: float,
    h: float,
    cos_a: float,
    sin_a: float,
) -> np.ndarray:
    """Convert rotated (u, v) curve and half-thickness into screen-space QUADS."""
    sx = w * 0.5 + (u * cos_a - v * sin_a) * h
    sy = h * 0.5 + (u * sin_a + v * cos_a) * h

    dx = np.gradient(sx)
    dy = np.gradient(sy)
    norm = np.hypot(dx, dy) + 1e-6
    nx = -dy / norm * half_t
    ny = dx / norm * half_t

    x_top = sx + nx
    y_top = sy + ny
    x_bot = sx - nx
    y_bot = sy - ny

    quads = np.empty(((len(u) - 1) * 4, 2), dtype=np.float32)
    quads[0::4, 0] = x_top[:-1]
    quads[0::4, 1] = y_top[:-1]
    quads[1::4, 0] = x_top[1:]
    quads[1::4, 1] = y_top[1:]
    quads[2::4, 0] = x_bot[1:]
    quads[2::4, 1] = y_bot[1:]
    quads[3::4, 0] = x_bot[:-1]
    quads[3::4, 1] = y_bot[:-1]
    return quads


def _draw_kasuri_wavefronts(u_loop: float, w: float, h: float) -> None:
    """Draw 35 warp ribbons and 420 continuously advecting kasuri weft-shuttle threads."""
    theta = u_loop * math.tau
    cos_a = math.cos(-SWEEP_ANGLE)
    sin_a = math.sin(-SWEEP_ANGLE)

    # High-key Mineral & Washi Pigment Roles (R, G, B, A):
    # 0 = Iron-Gall Slate Ink (#24333d)
    # 1 = Burnt Terracotta Sienna (#bc4e30)
    # 2 = Raw Gold Ochre (#ce8e2a)
    # 3 = Celadon Sage (#46736c)
    role_colors = [
        (36, 51, 61, 195),
        (188, 78, 48, 190),
        (206, 142, 42, 195),
        (70, 115, 108, 185),
    ]

    warp_quads_by_role: list[list[np.ndarray]] = [[] for _ in range(4)]
    taper = np.clip(np.sin(np.linspace(0.0, math.pi, N_SAMPLES, dtype=np.float32)), 0.0, 1.0) ** 0.4

    u = U_SAMPLES
    for i in range(N_WARP_RIBBONS):
        d = float(WARP_DIR[i])
        ph = float(WARP_PHASE[i])
        v0 = float(WARP_V0[i])

        # Traveling shed wavefront sweeping along u
        v = (
            v0
            + 0.052 * np.sin(u * 3.8 - theta * d + ph)
            + 0.028 * np.cos(u * 7.2 - theta * 2.0 * d + ph * 2.09)
        )
        # Calligraphic thickness pulsing with the traveling shuttle crest
        crest_pulse = 0.5 + 0.5 * np.cos(u * 6.0 - theta * 2.0 * d + i * 0.4)
        half_t = (1.4 + 2.8 * (crest_pulse ** 2)) * taper

        r_id = int(WARP_ROLE[i])
        warp_quads_by_role[r_id].append(
            _build_ribbon_quads(u, v, half_t, w, h, cos_a, sin_a)
        )

    py5.no_stroke()
    for r_id, (rc, gc, bc, ac) in enumerate(role_colors):
        if warp_quads_by_role[r_id]:
            py5.fill(rc, gc, bc, ac)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(np.concatenate(warp_quads_by_role[r_id], axis=0))

    # 2. Render 420 continuously advecting kasuri ikat weft-shuttle threads (1 full period = 2.30 units)
    period = 2.30
    u_shuttle = np.mod(SHUTTLE_U0 + u_loop * SHUTTLE_DIR * period + 1.15, period) - 1.15
    band_f = SHUTTLE_BAND.astype(np.float32)
    y_center = -0.45 + band_f * 0.15

    v_shuttle = (
        y_center
        + SHUTTLE_V_JITTER
        + 0.052 * np.sin(u_shuttle * 3.8 - theta * SHUTTLE_DIR + band_f * 1.1)
        + 0.028 * np.cos(u_shuttle * 7.2 - theta * 2.0 * SHUTTLE_DIR + band_f * 2.3)
    )

    half_l = SHUTTLE_LEN * 0.5
    half_th = SHUTTLE_THICK * 0.5
    u0 = u_shuttle - half_l
    u1 = u_shuttle + half_l
    v0 = v_shuttle - half_th
    v1 = v_shuttle + half_th

    cu = np.stack([u0, u1, u1, u0], axis=1)
    cv = np.stack([v0, v0, v1, v1], axis=1)

    sx = w * 0.5 + (cu * cos_a - cv * sin_a) * h
    sy = h * 0.5 + (cu * sin_a + cv * cos_a) * h
    shuttle_quads = np.stack([sx, sy], axis=-1).astype(np.float32)

    for r_id, (rc, gc, bc, _) in enumerate(role_colors):
        idx = np.flatnonzero(SHUTTLE_ROLE == r_id)
        if len(idx) > 0:
            py5.fill(rc, gc, bc, 225)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(shuttle_quads[idx].reshape(-1, 2))


def setup() -> None:
    global _shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    _shader = load_shader(SKETCH_DIR / "kasuri_shuttle_wavefronts.glsl")
    fx.setup()
    _init_weave()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    w, h = float(SIZE[0]), float(SIZE[1])

    draw_fullscreen(_shader, u_loop=float(u_loop))
    _draw_kasuri_wavefronts(u_loop, w, h)
    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

