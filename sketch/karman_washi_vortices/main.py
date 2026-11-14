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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Asymmetric golden-ratio focal anchor in the upper-left third, shedding diagonally right/down
ANCHOR_X_FRAC = random.uniform(0.20, 0.25)
ANCHOR_Y_FRAC = random.uniform(0.35, 0.42)
STREAM_ANGLE = random.uniform(0.15, 0.23)

NUM_RIBBONS = 520
TRAIL_LEN = 28

RIBBON_X: np.ndarray
RIBBON_Y: np.ndarray
RIBBON_WIDTH: np.ndarray
RIBBON_COLOR_GROUP: np.ndarray
RIBBON_AGE: np.ndarray
RIBBON_MAX_AGE: np.ndarray

VORTEX_X: np.ndarray
VORTEX_Y: np.ndarray
VORTEX_GAMMA: np.ndarray
VORTEX_SIGMA: np.ndarray

WASHI_GRAIN_QUADS: np.ndarray
RNG = np.random.default_rng()


def _spawn_ribbons(indices: np.ndarray, width: float, height: float, initial: bool = False) -> None:
    count = len(indices)
    if count == 0:
        return

    ax = ANCHOR_X_FRAC * width
    ay = ANCHOR_Y_FRAC * height
    cos_a = math.cos(STREAM_ANGLE)
    sin_a = math.sin(STREAM_ANGLE)

    # Mix of boundary-layer shear filaments, vortex-core spiral filaments, and outer streamlines
    mode = RNG.random(count)
    if initial:
        s_along = RNG.uniform(-0.10 * width, 0.68 * width, size=count)
    else:
        # Organic curved inflow distribution + direct vortex-wake seeding (no straight line cutoff)
        s_along = np.where(
            mode < 0.55,
            RNG.normal(-0.04 * width, 0.055 * width, size=count),
            RNG.uniform(0.0, 0.58 * width, size=count),
        )

    cross_spread = np.where(
        mode < 0.72,
        RNG.normal(0.0, 0.085 * height, size=count),
        RNG.normal(0.0, 0.21 * height, size=count),
    )
    # Curve the upstream spawn locus parabolically so there is never a flat edge
    s_along -= 0.18 * (cross_spread**2) / (0.12 * height + 1.0)

    x0 = (ax + s_along * cos_a - cross_spread * sin_a).astype(np.float32)
    y0 = (ay + s_along * sin_a + cross_spread * cos_a).astype(np.float32)

    RIBBON_X[indices, :] = x0[:, None]
    RIBBON_Y[indices, :] = y0[:, None]
    RIBBON_AGE[indices] = RNG.integers(0, 90, size=count) if initial else 0
    RIBBON_MAX_AGE[indices] = RNG.integers(150, 310, size=count)


def _velocity_field(
    px: np.ndarray, py: np.ndarray, width: float, height: float
) -> tuple[np.ndarray, np.ndarray]:
    ax = ANCHOR_X_FRAC * width
    ay = ANCHOR_Y_FRAC * height
    cos_a = math.cos(STREAM_ANGLE)
    sin_a = math.sin(STREAM_ANGLE)

    u_inf = 3.8
    vx = np.full_like(px, u_inf * cos_a)
    vy = np.full_like(py, u_inf * sin_a)

    dx0 = px - ax
    dy0 = py - ay
    r0_sq = dx0 * dx0 + dy0 * dy0 + (0.038 * height) ** 2
    obs_R2 = (0.068 * height) ** 2

    ux_local = dx0 * cos_a + dy0 * sin_a
    uy_local = -dx0 * sin_a + dy0 * cos_a
    du_local = -u_inf * obs_R2 * (ux_local**2 - uy_local**2) / (r0_sq**2 + 1e-4)
    dv_local = -u_inf * obs_R2 * (2.0 * ux_local * uy_local) / (r0_sq**2 + 1e-4)
    vx += du_local * cos_a - dv_local * sin_a
    vy += du_local * sin_a + dv_local * cos_a

    # Strong Lamb-Oseen Biot-Savart rotational velocity + slight spiral inward suction
    dvx = px[:, None] - VORTEX_X[None, :]
    dvy = py[:, None] - VORTEX_Y[None, :]
    r2 = dvx * dvx + dvy * dvy + 48.0
    sigma2 = VORTEX_SIGMA[None, :] ** 2
    gauss = 1.0 - np.exp(-r2 / sigma2)
    swirl = (VORTEX_GAMMA[None, :] / (math.tau * r2)) * gauss
    # Subtle radial entrainment toward vortex eyes for calligraphic spiral roll-up
    suction = -0.14 * np.abs(swirl) * np.exp(-r2 / (2.2 * sigma2))

    vx += np.sum(-dvy * swirl + dvx * suction, axis=1)
    vy += np.sum(dvx * swirl + dvy * suction, axis=1)
    return vx, vy


def _step_simulation(t_sec: float, width: float, height: float) -> None:
    ax = ANCHOR_X_FRAC * width
    ay = ANCHOR_Y_FRAC * height
    cos_a = math.cos(STREAM_ANGLE)
    sin_a = math.sin(STREAM_ANGLE)

    # Vortex convection speed matched to 0.82 * u_inf (~187 px/sec) so filaments co-orbit and roll up
    n_vort = len(VORTEX_X)
    u_conv = 186.0
    spacing = 0.092 * width
    shed_period = (2.0 * spacing) / u_conv

    for k in range(n_vort):
        age = (t_sec + k * (shed_period * 0.5)) % (shed_period * n_vort * 0.5)
        s_dist = age * u_conv
        sign = 1.0 if (k % 2 == 0) else -1.0

        # Staggered Kármán street ratio h/l ~ 0.281
        lat_offset = sign * (0.056 * height) * (1.0 - math.exp(-s_dist / (0.11 * width)))
        lat_osc = 0.022 * height * math.sin(s_dist * 0.012 - t_sec * 1.9 + k * 0.7)
        cross = lat_offset + lat_osc

        VORTEX_X[k] = ax + s_dist * cos_a - cross * sin_a
        VORTEX_Y[k] = ay + s_dist * sin_a + cross * cos_a
        VORTEX_SIGMA[k] = 58.0 + 0.095 * s_dist
        decay = math.exp(-s_dist / (0.76 * width))
        VORTEX_GAMMA[k] = sign * 31500.0 * decay * (1.0 - math.exp(-age * 3.8))

    RIBBON_X[:, 1:] = RIBBON_X[:, :-1]
    RIBBON_Y[:, 1:] = RIBBON_Y[:, :-1]

    vx, vy = _velocity_field(RIBBON_X[:, 0], RIBBON_Y[:, 0], width, height)
    RIBBON_X[:, 0] += vx
    RIBBON_Y[:, 0] += vy
    RIBBON_AGE[:] += 1

    out_of_bounds = (
        (RIBBON_AGE >= RIBBON_MAX_AGE)
        | (RIBBON_X[:, 0] > width * 0.95)
        | (RIBBON_Y[:, 0] > height * 0.95)
        | (RIBBON_X[:, 0] < width * 0.03)
        | (RIBBON_Y[:, 0] < height * 0.04)
    )
    respawn_idx = np.flatnonzero(out_of_bounds)
    if len(respawn_idx) > 0:
        _spawn_ribbons(respawn_idx, width, height, initial=False)


def _build_tapered_ribbon_quads(indices: np.ndarray) -> np.ndarray:
    rx = RIBBON_X[indices]
    ry = RIBBON_Y[indices]
    rw = RIBBON_WIDTH[indices][:, None]

    dx = rx[:, :-1] - rx[:, 1:]
    dy = ry[:, :-1] - ry[:, 1:]
    seg_len = np.hypot(dx, dy) + 1e-4
    nx = -dy / seg_len
    ny = dx / seg_len

    nx = np.concatenate([nx, nx[:, -1:]], axis=1)
    ny = np.concatenate([ny, ny[:, -1:]], axis=1)

    s = np.linspace(0.0, 1.0, TRAIL_LEN, dtype=np.float32)[None, :]
    taper = np.sin(s * math.pi) * (1.0 - 0.42 * s)
    half_w = rw * taper

    x_l = rx - nx * half_w
    y_l = ry - ny * half_w
    x_r = rx + nx * half_w
    y_r = ry + ny * half_w

    n_rib = len(indices)
    quads = np.empty((n_rib, TRAIL_LEN - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_l[:, :-1]
    quads[:, :, 0, 1] = y_l[:, :-1]
    quads[:, :, 1, 0] = x_r[:, :-1]
    quads[:, :, 1, 1] = y_r[:, :-1]
    quads[:, :, 2, 0] = x_r[:, 1:]
    quads[:, :, 2, 1] = y_r[:, 1:]
    quads[:, :, 3, 0] = x_l[:, 1:]
    quads[:, :, 3, 1] = y_l[:, 1:]
    return quads.reshape(-1, 2)


def _build_vortex_eye_rings() -> np.ndarray:
    """Delicate translucent mineral-wash rings around active shed vortex eyes."""
    n_seg = 28
    ang = np.linspace(0.0, math.tau, n_seg, endpoint=False, dtype=np.float32)[None, :]
    ang_next = np.roll(ang, -1, axis=1)

    # Use the first 8 strongest downstream vortices
    vx = VORTEX_X[:8, None]
    vy = VORTEX_Y[:8, None]
    r_in = VORTEX_SIGMA[:8, None] * 0.42
    r_out = VORTEX_SIGMA[:8, None] * 0.56

    quads = np.empty((8, n_seg, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = vx + r_in * np.cos(ang)
    quads[:, :, 0, 1] = vy + r_in * np.sin(ang)
    quads[:, :, 1, 0] = vx + r_out * np.cos(ang)
    quads[:, :, 1, 1] = vy + r_out * np.sin(ang)
    quads[:, :, 2, 0] = vx + r_out * np.cos(ang_next)
    quads[:, :, 2, 1] = vy + r_out * np.sin(ang_next)
    quads[:, :, 3, 0] = vx + r_in * np.cos(ang_next)
    quads[:, :, 3, 1] = vy + r_in * np.sin(ang_next)
    return quads.reshape(-1, 2)


def setup() -> None:
    global RIBBON_X, RIBBON_Y, RIBBON_WIDTH, RIBBON_COLOR_GROUP, RIBBON_AGE, RIBBON_MAX_AGE
    global VORTEX_X, VORTEX_Y, VORTEX_GAMMA, VORTEX_SIGMA, WASHI_GRAIN_QUADS

    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    w, h = float(SIZE[0]), float(SIZE[1])

    # Full-canvas High-Key Pale Celadon-Sage Washi ground (#e8ede6)
    py5.background(232, 237, 230)

    n_vort = 14
    VORTEX_X = np.zeros(n_vort, dtype=np.float32)
    VORTEX_Y = np.zeros(n_vort, dtype=np.float32)
    VORTEX_GAMMA = np.zeros(n_vort, dtype=np.float32)
    VORTEX_SIGMA = np.full(n_vort, 64.0, dtype=np.float32)

    RIBBON_X = np.zeros((NUM_RIBBONS, TRAIL_LEN), dtype=np.float32)
    RIBBON_Y = np.zeros((NUM_RIBBONS, TRAIL_LEN), dtype=np.float32)
    RIBBON_WIDTH = RNG.uniform(2.0, 6.8, size=NUM_RIBBONS).astype(np.float32)
    u = RNG.random(NUM_RIBBONS)
    RIBBON_COLOR_GROUP = np.where(u < 0.58, 0, np.where(u < 0.86, 1, 2))
    RIBBON_AGE = np.zeros(NUM_RIBBONS, dtype=np.int32)
    RIBBON_MAX_AGE = np.zeros(NUM_RIBBONS, dtype=np.int32)

    _spawn_ribbons(np.arange(NUM_RIBBONS), w, h, initial=True)

    # Pre-generate handmade washi paper deckle fibers across negative space
    n_fibers = 480
    fx0 = RNG.uniform(0.0, w, size=n_fibers).astype(np.float32)
    fy0 = RNG.uniform(0.0, h, size=n_fibers).astype(np.float32)
    fang = RNG.uniform(0.0, math.tau, size=n_fibers).astype(np.float32)
    flen = RNG.uniform(18.0, 64.0, size=n_fibers).astype(np.float32)
    fw = RNG.uniform(1.0, 2.2, size=n_fibers).astype(np.float32)
    dx = np.cos(fang) * flen
    dy = np.sin(fang) * flen
    nx = -np.sin(fang) * fw
    ny = np.cos(fang) * fw
    fquads = np.empty((n_fibers, 4, 2), dtype=np.float32)
    fquads[:, 0, 0] = fx0 - nx
    fquads[:, 0, 1] = fy0 - ny
    fquads[:, 1, 0] = fx0 + nx
    fquads[:, 1, 1] = fy0 + ny
    fquads[:, 2, 0] = fx0 + dx + nx
    fquads[:, 2, 1] = fy0 + dy + ny
    fquads[:, 3, 0] = fx0 + dx - nx
    fquads[:, 3, 1] = fy0 + dy - ny
    WASHI_GRAIN_QUADS = fquads.reshape(-1, 2)

    # Pre-warm the vortex street so frame 1 already displays rolled-up spiral eddies
    py5.no_stroke()
    for step in range(130):
        _step_simulation(step / float(FPS), w, h)
        if step >= 35:
            _draw_ink_step(w, h)


def _draw_ink_step(w: float, h: float) -> None:
    # 1. Translucent pale-sage washi veil for persistent trail accumulation & soft decay
    py5.fill(232, 237, 230, 8)
    py5.rect(0.0, 0.0, w, h)

    # 2. Subtle raw linen fiber whispers across the expansive negative space
    py5.fill(212, 219, 208, 12)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(WASHI_GRAIN_QUADS)

    # 3. Delicate mineral-wash halos around the shed vortex eyes
    py5.fill(200, 132, 40, 9)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_vortex_eye_rings())

    # 4. Draw advected mineral ink ribbons batched by pigment family
    idx_slate = np.flatnonzero(RIBBON_COLOR_GROUP == 0)
    idx_ochre = np.flatnonzero(RIBBON_COLOR_GROUP == 1)
    idx_terra = np.flatnonzero(RIBBON_COLOR_GROUP == 2)

    py5.fill(38, 52, 60, 46)  # Dominant (60%): Iron-Gall Slate Ink (#26343c)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_tapered_ribbon_quads(idx_slate))

    py5.fill(200, 132, 40, 50)  # Secondary (30%): Raw Mineral Ochre (#c88428)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_tapered_ribbon_quads(idx_ochre))

    py5.fill(184, 72, 48, 60)  # Accent (10%): Burnt Terracotta Sienna (#b84830)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(_build_tapered_ribbon_quads(idx_terra))


def draw() -> None:
    w, h = float(SIZE[0]), float(SIZE[1])
    t_sec = (py5.frame_count + 130) / float(FPS)

    py5.no_stroke()
    _step_simulation(t_sec, w, h)
    _draw_ink_step(w, h)

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
