"""kam_resonance_tori — Symplectic KAM Resonance Tori & Persistent Phase Trails.

A full-bleed continuous mathematical phase-space field spanning 100% of the
3840x2160 canvas over a mid-tone atmospheric dusk and sage-slate ground
(#2e3a40–#3d4e48). Driven by a multi-harmonic symplectic Hamiltonian flow
with 5:3 and 7:4 Kolmogorov-Arnold-Moser (KAM) resonance islands and hyperbolic
heteroclinic tangles, 2,800 advecting phase tracers and 64 invariant-torus
ribbons leave persistent luminous trails in soft chalk (#f2ede0), misty
seafoam (#8eb8b4), warm golden amber (#f0a438), and coral terracotta (#d86242).

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
from lib.sizes import get_sizes

# ── Constants ──────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 24
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1440 frames (24s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# ── Symplectic Phase-Space Constants ───────────────────────────────────
N_PARTICLES = 2800
N_TORI = 64
N_TORUS_PTS = 72

P_X: np.ndarray
P_Y: np.ndarray
P_ROLE: np.ndarray
P_WIDTH: np.ndarray
P_SPEED: np.ndarray
P_AGE: np.ndarray
P_MAX_AGE: np.ndarray

RNG: np.random.Generator


def _sample_kam_positions(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Sample initial particle coordinates concentrated around KAM islands & shear bands."""
    w, h = float(SIZE[0]), float(SIZE[1])
    u = RNG.uniform(0.0, 1.0, size=n).astype(np.float32)
    # Place 75% of tracers along the 4 primary KAM resonance chains in Y
    chain_idx = RNG.integers(0, 4, size=n)
    chain_y = (chain_idx + 0.5) / 4.0
    v_island = chain_y + RNG.normal(0.0, 0.085, size=n).astype(np.float32)
    v_unif = RNG.uniform(0.0, 1.0, size=n).astype(np.float32)
    use_island = RNG.random(size=n) < 0.75
    v = np.mod(np.where(use_island, v_island, v_unif), 1.0)
    return (u * w).astype(np.float32), (v * h).astype(np.float32)


def _init_system() -> None:
    global P_X, P_Y, P_ROLE, P_WIDTH, P_SPEED, P_AGE, P_MAX_AGE, RNG
    RNG = np.random.default_rng()

    P_X, P_Y = _sample_kam_positions(N_PARTICLES)

    # 4 visual roles:
    # 0: Deep Sage-Teal Under-Wash (28%)
    # 1: Misty Seafoam KAM Torus Stream (32%)
    # 2: Soft Chalk Invariant Curves (24%)
    # 3: Golden Amber & Coral Resonance Islands (16%)
    probs = (0.28, 0.32, 0.24, 0.16)
    P_ROLE = RNG.choice(4, size=N_PARTICLES, p=probs).astype(np.int32)

    base_w = np.choose(P_ROLE, [24.0, 5.2, 3.2, 4.6]).astype(np.float32)
    P_WIDTH = base_w * RNG.uniform(0.80, 1.28, size=N_PARTICLES).astype(np.float32)

    base_spd = np.choose(P_ROLE, [10.5, 13.5, 15.0, 14.0]).astype(np.float32)
    P_SPEED = base_spd * RNG.uniform(0.82, 1.22, size=N_PARTICLES).astype(np.float32)

    P_MAX_AGE = RNG.integers(48, 120, size=N_PARTICLES, dtype=np.int32)
    P_AGE = RNG.integers(0, 90, size=N_PARTICLES, dtype=np.int32)


def _hamiltonian_velocity(
    px: np.ndarray, py: np.ndarray, phase: float
) -> tuple[np.ndarray, np.ndarray]:
    """Compute divergence-free symplectic velocity (dH/dy, -dH/dx) across the canvas."""
    w, h = float(SIZE[0]), float(SIZE[1])
    # Normalized torus coordinates in [0, TAU)
    ux = (px / w) * math.tau
    uy = (py / h) * math.tau

    # Hamiltonian H(ux, uy, t) combining:
    # 1) Alternating horizontal shear currents: cos(2 * uy)
    # 2) Primary 3:2 and 5:4 KAM resonance islands
    # 3) Secondary heteroclinic saddle chain
    k_mod = 0.72 + 0.28 * math.sin(phase)

    # dH/duy (horizontal velocity component)
    dh_duy = (
        -1.35 * np.sin(2.0 * uy + 0.35 * math.sin(phase))
        + 0.92 * k_mod * np.cos(3.0 * ux - phase) * np.sin(2.0 * uy)
        + 0.64 * np.sin(5.0 * ux + 2.0 * uy + phase * 2.0)
        - 0.42 * np.cos(2.0 * ux - 4.0 * uy - phase)
    )

    # -dH/dux (vertical velocity component)
    neg_dh_dux = (
        0.92 * k_mod * 1.5 * np.sin(3.0 * ux - phase) * np.cos(2.0 * uy)
        - 0.64 * 2.5 * np.cos(5.0 * ux + 2.0 * uy + phase * 2.0)
        - 0.42 * 1.0 * np.sin(2.0 * ux - 4.0 * uy - phase)
    )

    vx = dh_duy.astype(np.float32)
    vy = (neg_dh_dux * 0.68).astype(np.float32)
    norm = np.maximum(np.hypot(vx, vy), 0.35)
    return vx / norm, vy / norm


def _step_and_draw_trails(phase: float) -> None:
    """Advance symplectic tracers one step and render batched ribbon segments."""
    global P_X, P_Y, P_AGE
    w, h = float(SIZE[0]), float(SIZE[1])

    vx, vy = _hamiltonian_velocity(P_X, P_Y, phase)
    step_len = P_SPEED * (0.90 + 0.18 * math.sin(phase * 2.0))
    nx_pos = P_X + vx * step_len
    ny_pos = P_Y + vy * step_len

    # Orthogonal unit normal for ribbon quad extrusion
    ux = -vy
    uy = vx
    hw = 0.5 * P_WIDTH

    quads = np.empty((N_PARTICLES, 4, 2), dtype=np.float32)
    quads[:, 0, 0] = P_X + ux * hw
    quads[:, 0, 1] = P_Y + uy * hw
    quads[:, 1, 0] = nx_pos + ux * hw
    quads[:, 1, 1] = ny_pos + uy * hw
    quads[:, 2, 0] = nx_pos - ux * hw
    quads[:, 2, 1] = ny_pos - uy * hw
    quads[:, 3, 0] = P_X - ux * hw
    quads[:, 3, 1] = P_Y - uy * hw

    # Mid-Tone Atmospheric Dusk / Celadon Slate palette roles:
    role_rgba = (
        (64, 92, 90, 56),      # 0: Deep Celadon-Sage Under-Wash (#405c5a)
        (142, 184, 180, 155),  # 1: Misty Seafoam Torus Stream (#8eb8b4)
        (242, 237, 224, 195),  # 2: Soft Chalk Invariant Curves (#f2ede0)
        (240, 164, 56, 215),   # 3: Warm Golden Amber Resonance Islands (#f0a438)
    )

    py5.no_stroke()
    for r_id, rgba in enumerate(role_rgba):
        mask = P_ROLE == r_id
        py5.fill(*rgba)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(quads[mask].reshape(-1, 2))

    # Wrap torus coordinates and recycle aged particles
    P_X = np.mod(nx_pos, w)
    P_Y = np.mod(ny_pos, h)
    P_AGE += 1

    expired = P_AGE >= P_MAX_AGE
    n_exp = int(np.count_nonzero(expired))
    if n_exp > 0:
        rx, ry = _sample_kam_positions(n_exp)
        P_X[expired] = rx
        P_Y[expired] = ry
        P_AGE[expired] = 0


def _draw_invariant_kam_contours(phase: float) -> None:
    """Draw crisp instantaneous KAM invariant-torus and resonance-island contours."""
    w, h = float(SIZE[0]), float(SIZE[1])

    # 1) 18 full-width undulating rotational KAM tori
    n_rot = 18
    s_u = np.linspace(0.0, math.tau, N_TORUS_PTS, dtype=np.float32)[None, :]
    v0 = np.linspace(0.04, 0.96, n_rot, dtype=np.float32)[:, None] * math.tau

    # Perturbed invariant torus height y(u)
    uy = (
        v0
        + 0.24 * np.sin(3.0 * s_u - phase) * np.cos(2.0 * v0)
        + 0.12 * np.cos(5.0 * s_u + 2.0 * v0 + phase * 2.0)
    )
    sx = (s_u / math.tau) * w
    sy = (uy / math.tau) * h
    sx_b = np.broadcast_to(sx, sy.shape)

    dx = np.gradient(sx_b, axis=1)
    dy = np.gradient(sy, axis=1)
    inv_l = 1.0 / np.maximum(np.hypot(dx, dy), 1e-4)
    nx = -dy * inv_l
    ny = dx * inv_l
    hw = 1.6

    q_rot = np.empty((n_rot, N_TORUS_PTS - 1, 4, 2), dtype=np.float32)
    q_rot[:, :, 0, 0] = sx_b[:, :-1] + nx[:, :-1] * hw
    q_rot[:, :, 0, 1] = sy[:, :-1] + ny[:, :-1] * hw
    q_rot[:, :, 1, 0] = sx_b[:, 1:] + nx[:, 1:] * hw
    q_rot[:, :, 1, 1] = sy[:, 1:] + ny[:, 1:] * hw
    q_rot[:, :, 2, 0] = sx_b[:, 1:] - nx[:, 1:] * hw
    q_rot[:, :, 2, 1] = sy[:, 1:] - ny[:, 1:] * hw
    q_rot[:, :, 3, 0] = sx_b[:, :-1] - nx[:, :-1] * hw
    q_rot[:, :, 3, 1] = sy[:, :-1] - ny[:, :-1] * hw

    py5.no_stroke()
    py5.fill(242, 237, 224, 95)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(q_rot.reshape(-1, 2))

    # 2) Nested elliptic KAM resonance islands (3 cols x 2 rows = 6 island vortex centers)
    cx_list = np.mod((np.array([0.5, 1.5, 2.5], dtype=np.float32) * math.tau + phase) / 3.0, math.tau)
    cy_list = np.array([0.25 * math.tau, 0.75 * math.tau], dtype=np.float32)
    c_grid_x, c_grid_y = np.meshgrid(cx_list, cy_list)
    centers_x = (c_grid_x.reshape(-1) / math.tau) * w
    centers_y = (c_grid_y.reshape(-1) / math.tau) * h

    ang = np.linspace(0.0, math.tau, 48, dtype=np.float32)[None, None, :]
    radii = np.array([0.26, 0.52, 0.82, 1.14], dtype=np.float32)[None, :, None]

    # Anisotropic sheared KAM island ellipses in coral-terracotta (#d86242) and amber (#f0a438)
    rx = 210.0 * radii
    ry = 115.0 * radii
    ca = np.cos(ang)
    sa = np.sin(ang) + 0.25 * np.sin(ang * 3.0 - phase)
    ix = centers_x[:, None, None] + rx * ca - 38.0 * radii * sa
    iy = centers_y[:, None, None] + ry * sa

    dx_i = np.gradient(ix, axis=2)
    dy_i = np.gradient(iy, axis=2)
    inv_li = 1.0 / np.maximum(np.hypot(dx_i, dy_i), 1e-4)
    nxi = -dy_i * inv_li
    nyi = dx_i * inv_li
    hwi = 2.1

    q_isl = np.empty((len(centers_x), 4, 47, 4, 2), dtype=np.float32)
    q_isl[:, :, :, 0, 0] = ix[:, :, :-1] + nxi[:, :, :-1] * hwi
    q_isl[:, :, :, 0, 1] = iy[:, :, :-1] + nyi[:, :, :-1] * hwi
    q_isl[:, :, :, 1, 0] = ix[:, :, 1:] + nxi[:, :, 1:] * hwi
    q_isl[:, :, :, 1, 1] = iy[:, :, 1:] + nyi[:, :, 1:] * hwi
    q_isl[:, :, :, 2, 0] = ix[:, :, 1:] - nxi[:, :, 1:] * hwi
    q_isl[:, :, :, 2, 1] = iy[:, :, 1:] - nyi[:, :, 1:] * hwi
    q_isl[:, :, :, 3, 0] = ix[:, :, :-1] - nxi[:, :, :-1] * hwi
    q_isl[:, :, :, 3, 1] = iy[:, :, :-1] - nyi[:, :, :-1] * hwi

    # Inner rings in coral terracotta (#d86242), outer rings in golden amber (#f0a438)
    py5.fill(216, 98, 66, 165)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(q_isl[:, :2, :, :, :].reshape(-1, 2))

    py5.fill(240, 164, 56, 155)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(q_isl[:, 2:, :, :, :].reshape(-1, 2))


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    _init_system()

    # Initialize mid-tone atmospheric dusk / celadon-slate canvas (#2c3840)
    py5.background(44, 56, 64)
    # Pre-warm persistent trail buffer for 32 steps so Frame 1 already has deep layered trails
    for w_step in range(32):
        w_phase = (w_step - 32) * (math.tau / float(TOTAL_FRAMES))
        py5.no_stroke()
        py5.fill(44, 56, 64, 11)
        py5.rect(0, 0, SIZE[0], SIZE[1])
        _step_and_draw_trails(w_phase)


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    phase = u_loop * math.tau

    # Persistent trail decay veil in mid-tone dusk celadon-slate (#2c3840)
    py5.no_stroke()
    py5.fill(44, 56, 64, 11)
    py5.rect(0, 0, SIZE[0], SIZE[1])

    _step_and_draw_trails(phase)
    _draw_invariant_kam_contours(phase)

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

