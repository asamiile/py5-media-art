"""prussian_legendre_strata — Stratified Legendre-Chebyshev Algebraic Horizons.

Across a rich saturated color field of deep Prussian blue (#0a1e40), forest malachite
(#0e5750), burnt sienna (#c04424), and luminous cadmium gold (#f4ac24), diagonally
swept algebraic polynomial strata undergo poly-rhythmic phase interference. Layered
over the GLSL polynomial caustic field, 32 orthogonal-polynomial envelope ribbons and
cusp-singularity tangent struts weave across the 3840x2160 canvas.

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

DURATION_SEC = 23
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1380 frames (23s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SWEEP_ANGLE = 0.314159  # Matches GLSL 18 deg diagonal sweep
N_STRATA = 32
N_SAMPLES = 200

fx = PostFX(
    bloom=0.26,
    bloom_threshold=0.68,
    aberration=0.0012,
    tonemap=0.84,
    vignette=0.14,
    grain=0.016,
)
_shader = None

U_SAMPLES: np.ndarray
V_BASES: np.ndarray
STRATA_ROLE: np.ndarray
STRATA_DEG1: np.ndarray
STRATA_DEG2: np.ndarray
STRATA_DEG3: np.ndarray
STRATA_PHASE: np.ndarray
STRATA_DIR: np.ndarray


def _init_strata() -> None:
    """Precompute 32 stratified orthogonal-polynomial horizon parameters."""
    global U_SAMPLES, V_BASES, STRATA_ROLE, STRATA_DEG1, STRATA_DEG2, STRATA_DEG3, STRATA_PHASE, STRATA_DIR
    rng = np.random.default_rng()

    U_SAMPLES = np.linspace(-1.08, 1.08, N_SAMPLES, dtype=np.float32)
    V_BASES = np.linspace(-0.48, 0.48, N_STRATA, dtype=np.float32)

    # Roles: 0 = Luminous Cadmium Gold (#f4ac24), 1 = Burnt Sienna (#c04424),
    # 2 = Verdigris Turquoise (#24a89e), 3 = Warm Ivory Highlight (#fcf1da)
    roles = [0, 1, 2, 0, 3, 1, 2, 0] * 4
    STRATA_ROLE = np.array(roles[:N_STRATA], dtype=np.int32)
    STRATA_DEG1 = rng.uniform(2.2, 4.2, size=N_STRATA).astype(np.float32)
    STRATA_DEG2 = rng.uniform(5.0, 8.5, size=N_STRATA).astype(np.float32)
    STRATA_DEG3 = rng.uniform(9.5, 14.5, size=N_STRATA).astype(np.float32)
    STRATA_PHASE = rng.uniform(0.0, math.tau, size=N_STRATA).astype(np.float32)
    STRATA_DIR = np.where(np.arange(N_STRATA) % 2 == 0, 1.0, -1.0).astype(np.float32)


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


def _draw_polynomial_strata(u_loop: float, w: float, h: float) -> None:
    """Render 32 diagonally swept polynomial horizon ribbons and caustic tangent rulings."""
    theta = u_loop * math.tau
    cos_a = math.cos(-SWEEP_ANGLE)
    sin_a = math.sin(-SWEEP_ANGLE)

    role_colors = [
        (244, 172, 36, 200),   # 0: Luminous Cadmium Gold (#f4ac24)
        (192, 68, 36, 190),    # 1: Burnt Sienna (#c04424)
        (36, 168, 158, 185),   # 2: Verdigris Turquoise (#24a89e)
        (252, 241, 218, 215),  # 3: Warm Ivory Highlight (#fcf1da)
    ]

    quads_by_role: list[list[np.ndarray]] = [[] for _ in range(4)]
    tangent_segs: list[np.ndarray] = []

    taper = np.clip(np.sin(np.linspace(0.0, math.pi, N_SAMPLES, dtype=np.float32)), 0.0, 1.0) ** 0.45

    for i in range(N_STRATA):
        u = U_SAMPLES
        d = float(STRATA_DIR[i])
        ph = float(STRATA_PHASE[i])
        k1 = float(STRATA_DEG1[i])
        k2 = float(STRATA_DEG2[i])
        k3 = float(STRATA_DEG3[i])

        # Poly-rhythmic 3-wave Chebyshev-Legendre harmonic superposition
        v = (
            float(V_BASES[i])
            + 0.048 * np.cos(u * k1 + theta * d + ph)
            + 0.028 * np.sin(u * k2 - theta * 2.0 * d + ph * 1.6)
            + 0.015 * np.cos(u * k3 + theta * 3.0 + i * 0.7)
        )

        # Calligraphic ribbon thickness peaking at stationary inflection points
        dv_du = (
            -0.048 * k1 * np.sin(u * k1 + theta * d + ph)
            + 0.028 * k2 * np.cos(u * k2 - theta * 2.0 * d + ph * 1.6)
        )
        inflection_boost = np.exp(-np.abs(dv_du) * 6.5)
        half_t = (1.6 + 3.8 * inflection_boost) * taper

        role_id = int(STRATA_ROLE[i])
        quads_by_role[role_id].append(
            _build_ribbon_quads(u, v, half_t, w, h, cos_a, sin_a)
        )

        # Collect caustic envelope tangent rulings every 10th sample on primary strata
        if i % 2 == 0:
            idx_sub = np.arange(8, N_SAMPLES - 8, 10)
            u0 = u[idx_sub]
            v0 = v[idx_sub]
            slope = dv_du[idx_sub]
            span = 0.055
            u1 = u0 + span
            v1 = v0 + slope * span

            sx0 = w * 0.5 + (u0 * cos_a - v0 * sin_a) * h
            sy0 = h * 0.5 + (u0 * sin_a + v0 * cos_a) * h
            sx1 = w * 0.5 + (u1 * cos_a - v1 * sin_a) * h
            sy1 = h * 0.5 + (u1 * sin_a + v1 * cos_a) * h

            segs = np.empty((len(idx_sub), 2, 2), dtype=np.float32)
            segs[:, 0, 0] = sx0
            segs[:, 0, 1] = sy0
            segs[:, 1, 0] = sx1
            segs[:, 1, 1] = sy1
            tangent_segs.append(segs.reshape(-1, 2))

    # Draw batched polynomial ribbons by color role
    py5.no_stroke()
    for role_id, (rc, gc, bc, ac) in enumerate(role_colors):
        if quads_by_role[role_id]:
            py5.fill(rc, gc, bc, ac)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(np.concatenate(quads_by_role[role_id], axis=0))

    # Draw crisp caustic tangent rulings
    if tangent_segs:
        py5.no_fill()
        py5.stroke(252, 241, 218, 135)
        py5.stroke_weight(1.3)
        with py5.begin_shape(py5.LINES):
            py5.vertices(np.concatenate(tangent_segs, axis=0))


def setup() -> None:
    global _shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    _shader = load_shader(SKETCH_DIR / "prussian_legendre_strata.glsl")
    fx.setup()
    _init_strata()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    w, h = float(SIZE[0]), float(SIZE[1])

    draw_fullscreen(_shader, u_loop=float(u_loop))
    _draw_polynomial_strata(u_loop, w, h)
    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

