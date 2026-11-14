"""ochre_littoral_strata — Stratified Mineral Wash & Poly-Rhythmic Littoral Horizons.

Across a full-canvas warm alabaster and raw linen ground (#ede8dc - #e5dfcf), eight
diagonally swept mineral wash horizons in raw ochre, burnt sienna, celadon sage,
and iron-gall slate undergo poly-rhythmic phase interference. Layered over the
wet-into-wet GLSL pigment diffusion field, crisp vector capillary tide lines and
mineral granulation ribbons trace the interference nodes of three harmonic wave trains.

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

DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1200 frames (20s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

TILT_ANGLE = -0.21  # Matches GLSL -12 deg diagonal sweep
NUM_RIBBONS = 28
NUM_SAMPLES = 180

# Keep tonemap low (0.18) so the high-key warm alabaster ground stays luminous
fx = PostFX(
    bloom=0.16,
    bloom_threshold=0.78,
    aberration=0.0009,
    tonemap=0.18,
    vignette=0.10,
    grain=0.016,
)
_shader = None
_ribbons: list[dict] = []


def _init_ribbons() -> None:
    """Precompute stratified poly-rhythmic capillary tide ribbons and mineral specks."""
    global _ribbons
    rng = np.random.default_rng()
    _ribbons = []

    # High-key mineral & washi pigment palette (R, G, B, A)
    palette = [
        (38, 54, 64, 175),    # Iron-Gall Slate Ink (#263640)
        (184, 76, 49, 170),   # Burnt Terracotta Sienna (#b84c31)
        (202, 138, 42, 180),  # Raw Mineral Ochre (#ca8a2a)
        (72, 116, 110, 165),  # Celadon Sage (#48746e)
    ]

    y_bases = np.linspace(-0.48, 0.48, NUM_RIBBONS)
    u_samples = np.linspace(-1.05, 1.05, NUM_SAMPLES, dtype=np.float64)

    for i in range(NUM_RIBBONS):
        direction = 1.0 if (i % 2 == 0) else -1.0
        k1 = float(rng.uniform(2.4, 4.8))
        k2 = float(rng.uniform(5.0, 8.2))
        k3 = float(rng.uniform(9.0, 13.5))
        ph1 = float(rng.uniform(0.0, math.tau))
        ph2 = float(rng.uniform(0.0, math.tau))
        ph3 = float(rng.uniform(0.0, math.tau))
        thick = float(rng.uniform(2.2, 6.4))
        color = palette[i % len(palette)]

        # Mineral granulation stipple nodes anchored along the tide line
        n_dots = 36
        dot_u = rng.uniform(-0.98, 0.98, size=n_dots)
        dot_jitter = rng.normal(0.0, 0.008, size=n_dots)
        dot_size = rng.uniform(3.2, 7.8, size=n_dots)

        _ribbons.append(
            {
                "y_base": float(y_bases[i]),
                "dir": direction,
                "u": u_samples,
                "k1": k1,
                "k2": k2,
                "k3": k3,
                "ph1": ph1,
                "ph2": ph2,
                "ph3": ph3,
                "thick": thick,
                "color": color,
                "dot_u": dot_u,
                "dot_jitter": dot_jitter,
                "dot_size": dot_size,
            }
        )


def _build_ribbon_quads(
    u: np.ndarray,
    v: np.ndarray,
    half_t: np.ndarray,
    w: float,
    h: float,
    cos_a: float,
    sin_a: float,
) -> np.ndarray:
    """Convert rotated (u, v) centerline and thickness profile into screen-space QUADS."""
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


def _draw_capillary_strata(u_loop: float, w: float, h: float) -> None:
    """Draw poly-rhythmic capillary tide ribbons and mineral pigment granulation."""
    theta = u_loop * math.tau
    # Inverse rotation from tilted q-space back to screen p-space
    cos_a = math.cos(-TILT_ANGLE)
    sin_a = math.sin(-TILT_ANGLE)

    py5.no_stroke()
    py5.rect_mode(py5.CENTER)

    for rb in _ribbons:
        u = rb["u"]
        d = rb["dir"]
        v = (
            rb["y_base"]
            + 0.044 * np.sin(u * rb["k1"] + theta * d + rb["ph1"])
            + 0.026 * np.cos(u * rb["k2"] - theta * 2.0 * d + rb["ph2"])
            + 0.015 * np.sin(u * rb["k3"] + theta * 3.0 + rb["ph3"])
        )

        # Calligraphic thickness modulation along interference envelope
        env = 0.45 + 0.55 * np.sin(u * 3.5 - theta * d + rb["ph1"]) ** 2
        taper = np.sin(np.linspace(0.0, math.pi, len(u))) ** 0.5
        half_t = rb["thick"] * env * taper

        r, g, b, a = rb["color"]
        py5.fill(r, g, b, a)
        quads = _build_ribbon_quads(u, v, half_t, w, h, cos_a, sin_a)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(quads)

        # Mineral pigment granulation specks along crest
        du = rb["dot_u"]
        dv = (
            rb["y_base"]
            + rb["dot_jitter"]
            + 0.044 * np.sin(du * rb["k1"] + theta * d + rb["ph1"])
            + 0.026 * np.cos(du * rb["k2"] - theta * 2.0 * d + rb["ph2"])
            + 0.015 * np.sin(du * rb["k3"] + theta * 3.0 + rb["ph3"])
        )
        dsx = w * 0.5 + (du * cos_a - dv * sin_a) * h
        dsy = h * 0.5 + (du * sin_a + dv * cos_a) * h
        dsize = rb["dot_size"]

        py5.fill(r, g, b, min(230, a + 35))
        for j in range(len(du)):
            py5.rect(float(dsx[j]), float(dsy[j]), float(dsize[j]), float(dsize[j] * 0.65))

    py5.rect_mode(py5.CORNER)


def setup() -> None:
    global _shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    _shader = load_shader(SKETCH_DIR / "ochre_littoral_strata.glsl")
    fx.setup()
    _init_ribbons()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    w, h = float(SIZE[0]), float(SIZE[1])

    draw_fullscreen(_shader, u_loop=float(u_loop))
    _draw_capillary_strata(u_loop, w, h)
    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

