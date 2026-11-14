"""escarpment_halftone_strata — Stratified Risograph Overprint Escarpment & Depth Drift.

Across a full-canvas warm cream Risograph paper ground (#f0e9dc), nine diagonally
swept escarpment horizons in translucent fluorescent coral (#f25240), peacock teal
(#10968c), and deep federal indigo (#1c2a62) undergo continuous spatial camera depth
traversal. Layered over the subtractive halftone GLSL overprint field, 27 misregistered
spot-ink contour ribbons and halftone stipple ridges glide from the distant upper
horizon toward the foreground.

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

DURATION_SEC = 16
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 960 frames (16s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

TILT_ANGLE = -0.26  # Matches GLSL -15 deg diagonal sweep
N_HORIZONS = 9
N_SAMPLES = 180

# Keep tonemap low (0.20) so the warm cream Risograph paper stays bright
fx = PostFX(
    bloom=0.14,
    bloom_threshold=0.80,
    aberration=0.0010,
    tonemap=0.20,
    vignette=0.10,
    grain=0.018,
)
_shader = None
_horizons: list[dict] = []


def _init_horizons() -> None:
    """Precompute 9 stratified escarpment horizon profiles for 3-channel Risograph overprint."""
    global _horizons
    rng = np.random.default_rng()
    _horizons = []

    u_samples = np.linspace(-1.08, 1.08, N_SAMPLES, dtype=np.float64)

    for i in range(N_HORIZONS):
        direction = 1.0 if (i % 2 == 0) else -1.0
        k1 = float(rng.uniform(2.5, 4.6))
        k2 = float(rng.uniform(5.2, 8.8))
        ph1 = float(rng.uniform(0.0, math.tau))
        ph2 = float(rng.uniform(0.0, math.tau))

        # Halftone stipple dot positions along the escarpment crest
        n_dots = 44
        dot_u = rng.uniform(-1.02, 1.02, size=n_dots)
        dot_v_off = rng.uniform(-0.028, 0.012, size=n_dots)
        dot_size = rng.uniform(3.5, 8.5, size=n_dots)
        dot_role = rng.integers(0, 3, size=n_dots)

        _horizons.append(
            {
                "idx": i,
                "dir": direction,
                "u": u_samples,
                "k1": k1,
                "k2": k2,
                "ph1": ph1,
                "ph2": ph2,
                "dot_u": dot_u,
                "dot_v_off": dot_v_off,
                "dot_size": dot_size,
                "dot_role": dot_role,
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
    """Transform rotated (u, v) ridge line into screen-space QUADS."""
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


def _draw_risograph_contours(u_loop: float, w: float, h: float) -> None:
    """Draw 3-channel misregistered Risograph spot-ink escarpment contours and halftone dots."""
    theta = u_loop * math.tau
    cos_a = math.cos(-TILT_ANGLE)
    sin_a = math.sin(-TILT_ANGLE)

    # 3 Translucent Risograph Spot Inks: Coral (#f25240), Teal (#10968c), Indigo (#1c2a62)
    spot_inks = [
        (242, 82, 64),   # 0: Fluorescent Coral
        (16, 150, 140),  # 1: Peacock Teal
        (28, 42, 98),    # 2: Deep Federal Indigo
    ]

    py5.no_stroke()
    py5.rect_mode(py5.CENTER)

    for hz in _horizons:
        i = hz["idx"]
        d_depth = ((i + u_loop) % float(N_HORIZONS)) / float(N_HORIZONS)
        # Smooth fade at top horizon entry and bottom foreground exit
        fade = min(1.0, d_depth / 0.14) * min(1.0, (1.0 - d_depth) / 0.14)
        if fade <= 0.02:
            continue

        y_hor = 0.44 * (1.0 - d_depth ** 1.15) - 0.48 * (d_depth ** 1.15)
        amp_y = 0.022 + 0.062 * d_depth
        thick_scale = (1.6 + 4.2 * d_depth) * fade

        u = hz["u"]
        dir_s = hz["dir"]
        v_base = (
            y_hor
            + amp_y * 0.62 * np.sin(u * hz["k1"] + theta * dir_s + hz["ph1"])
            + amp_y * 0.38 * np.cos(u * hz["k2"] - theta * dir_s + hz["ph2"])
        )

        # Render 3 slightly misregistered spot-ink contour ribbons per escarpment horizon
        reg_offsets = [
            (0.005 * math.cos(theta + i), 0.004 * math.sin(theta + i), 0, 155),
            (-0.005 * math.sin(theta - i), -0.004 * math.cos(theta - i), 1, 155),
            (0.002 * math.sin(theta * 2.0), -0.002 * math.cos(theta * 2.0), 2, 185),
        ]

        taper = np.sin(np.linspace(0.0, math.pi, len(u))) ** 0.45
        for du_reg, dv_reg, ink_id, base_alpha in reg_offsets:
            rc, gc, bc = spot_inks[ink_id]
            alpha = int(base_alpha * fade)
            half_t = thick_scale * (0.55 + 0.45 * np.cos(u * 4.0 + theta * dir_s + ink_id)) * taper
            quads = _build_ribbon_quads(
                u + du_reg, v_base + dv_reg, half_t, w, h, cos_a, sin_a
            )
            py5.fill(rc, gc, bc, alpha)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(quads)

        # Halftone registration dots along escarpment ridge
        du = hz["dot_u"]
        dv = (
            y_hor
            + hz["dot_v_off"]
            + amp_y * 0.62 * np.sin(du * hz["k1"] + theta * dir_s + hz["ph1"])
            + amp_y * 0.38 * np.cos(du * hz["k2"] - theta * dir_s + hz["ph2"])
        )
        dsx = w * 0.5 + (du * cos_a - dv * sin_a) * h
        dsy = h * 0.5 + (du * sin_a + dv * cos_a) * h
        dsize = hz["dot_size"] * (0.55 + 0.75 * d_depth)
        drole = hz["dot_role"]

        for j in range(len(du)):
            rc, gc, bc = spot_inks[int(drole[j])]
            py5.fill(rc, gc, bc, int(175 * fade))
            s_val = float(dsize[j])
            py5.rect(float(dsx[j]), float(dsy[j]), s_val, s_val)

    py5.rect_mode(py5.CORNER)


def setup() -> None:
    global _shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    _shader = load_shader(SKETCH_DIR / "escarpment_halftone_strata.glsl")
    fx.setup()
    _init_horizons()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    w, h = float(SIZE[0]), float(SIZE[1])

    draw_fullscreen(_shader, u_loop=float(u_loop))
    _draw_risograph_contours(u_loop, w, h)
    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

