"""sepiolite_separatrix_web — Boundary-to-Interior Hamiltonian Separatrix Network & Trail Decay

Thousands of phase-space tracer filaments nucleate from the four canvas borders
and follow the symplectic Hamiltonian stream function of a time-modulated
multipolar vortex-saddle lattice. Across a full-canvas high-key warm sepiolite
linen ground (#ece7db), persistent calligraphic traces in iron-gall slate,
burnt terracotta, raw mineral ochre, and celadon malachite weave an evolving
network of heteroclinic separatrices and hyperbolic saddle webs.

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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 23
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1380 frames
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_AGENTS = 3200
TRAIL_LEN = 12

AGENT_X: np.ndarray
AGENT_Y: np.ndarray
AGENT_HIST_X: np.ndarray
AGENT_HIST_Y: np.ndarray
AGENT_ROLE: np.ndarray
AGENT_WIDTH: np.ndarray
AGENT_AGE: np.ndarray
AGENT_MAX_AGE: np.ndarray
RNG: np.random.Generator

# Saddle / vortex pole parameters for the Hamiltonian stream function H(x, y, t)
POLE_X0: np.ndarray
POLE_Y0: np.ndarray
POLE_STRENGTH: np.ndarray
POLE_PHASE: np.ndarray


def _spawn_boundary_positions(rng: np.random.Generator, n: int, w: float, h: float) -> tuple[np.ndarray, np.ndarray]:
    """Spawn agents along the four canvas edges with slight inward penetration."""
    side = rng.integers(0, 4, size=n)
    u = rng.uniform(0.02, 0.98, size=n).astype(np.float32)
    inward = rng.exponential(38.0, size=n).astype(np.float32)

    x = np.where(
        side == 0,
        u * w,
        np.where(side == 1, w - inward, np.where(side == 2, u * w, inward)),
    )
    y = np.where(
        side == 0,
        inward,
        np.where(side == 1, u * h, np.where(side == 2, h - inward, u * h)),
    )
    return x.astype(np.float32), y.astype(np.float32)


def _eval_symplectic_velocity(x: np.ndarray, y: np.ndarray, t_sec: float, w: float, h: float) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate divergence-free Hamiltonian velocity (vx = dH/dy, vy = -dH/dx)
    plus gentle inward boundary-to-interior attraction toward interior saddle manifolds.
    """
    aspect = w / h
    nx = (x / w * 2.0 - 1.0) * aspect
    ny = y / h * 2.0 - 1.0

    # 1. Quasi-periodic cellular trigonometric lattice H_lat
    kx1, ky1 = 2.6, 2.6
    kx2, ky2 = 4.2, 4.2
    ph1 = t_sec * 0.45
    ph2 = -t_sec * 0.32

    # H1 = sin(kx1*nx + ph1) * sin(ky1*ny - ph1*0.7)
    s1x = np.sin(kx1 * nx + ph1)
    c1x = np.cos(kx1 * nx + ph1)
    s1y = np.sin(ky1 * ny - ph1 * 0.7)
    c1y = np.cos(ky1 * ny - ph1 * 0.7)

    # H2 = cos(kx2*(nx*0.8 - ny*0.6) + ph2) * sin(ky2*(nx*0.6 + ny*0.8) - ph2)
    u2 = nx * 0.8 - ny * 0.6
    v2 = nx * 0.6 + ny * 0.8
    c2u = np.cos(kx2 * u2 + ph2)
    s2u = np.sin(kx2 * u2 + ph2)
    s2v = np.sin(ky2 * v2 - ph2)
    c2v = np.cos(ky2 * v2 - ph2)

    dH_dnx = 0.65 * kx1 * c1x * s1y + 0.35 * (-0.8 * kx2 * s2u * s2v + 0.6 * ky2 * c2u * c2v)
    dH_dny = 0.65 * ky1 * s1x * c1y + 0.35 * (0.6 * kx2 * s2u * s2v + 0.8 * ky2 * c2u * c2v)

    # 2. Moving Gaussian vortex-saddle poles in interior
    px = POLE_X0[:, None] + 0.22 * np.cos(t_sec * 0.35 + POLE_PHASE[:, None])
    py = POLE_Y0[:, None] + 0.18 * np.sin(t_sec * 0.42 + POLE_PHASE[:, None])
    dx = nx[None, :] - px
    dy = ny[None, :] - py
    r2 = dx * dx + dy * dy + 0.085
    gauss = POLE_STRENGTH[:, None] * np.exp(-r2 * 3.8)
    dH_dnx += np.sum(-7.6 * dx * gauss, axis=0)
    dH_dny += np.sum(-7.6 * dy * gauss, axis=0)

    # Symplectic velocity + mild inward boundary-to-interior drift from canvas edges
    vx_norm = dH_dny - 0.32 * nx * np.exp(-(nx * nx + ny * ny) * 0.6)
    vy_norm = -dH_dnx - 0.32 * ny * np.exp(-(nx * nx + ny * ny) * 0.6)

    speed_px = 4.6
    return (vx_norm * speed_px).astype(np.float32), (vy_norm * speed_px).astype(np.float32)


def _step_agents(t_sec: float, w: float, h: float) -> None:
    global AGENT_X, AGENT_Y, AGENT_HIST_X, AGENT_HIST_Y, AGENT_AGE
    vx, vy = _eval_symplectic_velocity(AGENT_X, AGENT_Y, t_sec, w, h)
    AGENT_X = AGENT_X + vx
    AGENT_Y = AGENT_Y + vy
    AGENT_AGE += 1

    # Roll history buffer and push new position at index 0
    AGENT_HIST_X[:, 1:] = AGENT_HIST_X[:, :-1]
    AGENT_HIST_Y[:, 1:] = AGENT_HIST_Y[:, :-1]
    AGENT_HIST_X[:, 0] = AGENT_X
    AGENT_HIST_Y[:, 0] = AGENT_Y

    # Respawn agents that exceed max_age or leave canvas back on the perimeter
    out_mask = (
        (AGENT_AGE >= AGENT_MAX_AGE)
        | (AGENT_X < -20.0)
        | (AGENT_X > w + 20.0)
        | (AGENT_Y < -20.0)
        | (AGENT_Y > h + 20.0)
    )
    n_out = int(np.sum(out_mask))
    if n_out > 0:
        bx, by = _spawn_boundary_positions(RNG, n_out, w, h)
        AGENT_X[out_mask] = bx
        AGENT_Y[out_mask] = by
        AGENT_HIST_X[out_mask, :] = bx[:, None]
        AGENT_HIST_Y[out_mask, :] = by[:, None]
        AGENT_AGE[out_mask] = 0


def _build_ribbon_quads(indices: np.ndarray) -> np.ndarray:
    if len(indices) == 0:
        return np.empty((0, 2), dtype=np.float32)

    cx = AGENT_HIST_X[indices]  # (M, TRAIL_LEN)
    cy = AGENT_HIST_Y[indices]

    dx = cx[:, :-1] - cx[:, 1:]
    dy = cy[:, :-1] - cy[:, 1:]
    seg_len = np.hypot(dx, dy) + 1e-4

    # Clamp zero-length segments (newly respawned)
    valid = (seg_len < 35.0).astype(np.float32)
    nx = -dy / seg_len
    ny = dx / seg_len
    nx = np.concatenate([nx, nx[:, -1:]], axis=1)
    ny = np.concatenate([ny, ny[:, -1:]], axis=1)
    valid_node = np.concatenate([valid, valid[:, -1:]], axis=1)

    taper = np.sin(np.linspace(0.05, 0.95, TRAIL_LEN, dtype=np.float32) * math.pi)[None, :]
    half_w = AGENT_WIDTH[indices] * taper * valid_node * 0.5

    x_top = cx - nx * half_w
    y_top = cy - ny * half_w
    x_bot = cx + nx * half_w
    y_bot = cy + ny * half_w

    m = len(indices)
    quads = np.empty((m, TRAIL_LEN - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_top[:, :-1]
    quads[:, :, 0, 1] = y_top[:, :-1]
    quads[:, :, 1, 0] = x_bot[:, :-1]
    quads[:, :, 1, 1] = y_bot[:, :-1]
    quads[:, :, 2, 0] = x_bot[:, 1:]
    quads[:, :, 2, 1] = y_bot[:, 1:]
    quads[:, :, 3, 0] = x_top[:, 1:]
    quads[:, :, 3, 1] = y_top[:, 1:]
    return quads.reshape(-1, 2)


def setup() -> None:
    global AGENT_X, AGENT_Y, AGENT_HIST_X, AGENT_HIST_Y, AGENT_ROLE, AGENT_WIDTH, AGENT_AGE, AGENT_MAX_AGE
    global POLE_X0, POLE_Y0, POLE_STRENGTH, POLE_PHASE, RNG
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    RNG = np.random.default_rng()
    w, h = float(SIZE[0]), float(SIZE[1])

    # Full-canvas warm sepiolite-washi ground (#ece7db)
    py5.background(236, 231, 219)

    # 9 interior vortex-saddle poles
    POLE_X0 = np.array([-1.05, -0.42, 0.38, 1.08, -0.82, 0.0, 0.85, -0.35, 0.48], dtype=np.float32)
    POLE_Y0 = np.array([-0.52, -0.48, -0.55, -0.42, 0.12, 0.05, 0.18, 0.56, 0.52], dtype=np.float32)
    POLE_STRENGTH = np.array([1.1, -1.0, 1.15, -0.95, -1.1, 1.25, -1.05, 0.95, -1.1], dtype=np.float32)
    POLE_PHASE = RNG.uniform(0.0, math.tau, size=len(POLE_X0)).astype(np.float32)

    # Seed 65% of agents near boundaries and 35% along interior separatrices so early frames are already rich
    n_bound = int(NUM_AGENTS * 0.65)
    n_inner = NUM_AGENTS - n_bound
    bx, by = _spawn_boundary_positions(RNG, n_bound, w, h)
    ix = RNG.uniform(w * 0.08, w * 0.92, size=n_inner).astype(np.float32)
    iy = RNG.uniform(h * 0.08, h * 0.92, size=n_inner).astype(np.float32)

    AGENT_X = np.concatenate([bx, ix])
    AGENT_Y = np.concatenate([by, iy])
    AGENT_HIST_X = np.repeat(AGENT_X[:, None], TRAIL_LEN, axis=1)
    AGENT_HIST_Y = np.repeat(AGENT_Y[:, None], TRAIL_LEN, axis=1)

    # Role: 0 = Iron-Gall Slate (#26353d, 44%), 1 = Raw Mineral Ochre (#c88428, 25%),
    # 2 = Burnt Terracotta (#b84830, 17%), 3 = Celadon Malachite (#3b6964, 14%)
    r_val = RNG.random(NUM_AGENTS)
    AGENT_ROLE = np.zeros(NUM_AGENTS, dtype=np.int32)
    AGENT_ROLE[r_val > 0.44] = 1
    AGENT_ROLE[r_val > 0.69] = 2
    AGENT_ROLE[r_val > 0.86] = 3

    AGENT_WIDTH = RNG.uniform(2.2, 6.4, size=(NUM_AGENTS, 1)).astype(np.float32)
    AGENT_MAX_AGE = RNG.integers(140, 340, size=NUM_AGENTS)
    AGENT_AGE = RNG.integers(0, 120, size=NUM_AGENTS)

    # Pre-advance 14 steps to populate trail history
    for s_i in range(14):
        _step_agents(s_i * 0.016, w, h)


def draw() -> None:
    fc = py5.frame_count
    t_sec = (fc - 1) / float(FPS)
    w, h = float(SIZE[0]), float(SIZE[1])

    # On frame 1, lay down 10 pre-settled layers so the persistent canvas begins with an established boundary-to-interior web
    n_sub = 8 if fc == 1 else 1
    py5.no_stroke()

    for sub in range(n_sub):
        if fc > 1 or sub > 0:
            # Persistent Trail Accumulation & Decay via translucent warm sepiolite-washi veil
            py5.fill(236, 231, 219, 7)
            py5.rect(0.0, 0.0, w, h)

        _step_agents(t_sec + sub * 0.01, w, h)

        # Role 3: Celadon Malachite (#3b6964)
        py5.fill(59, 105, 100, 56)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(_build_ribbon_quads(np.flatnonzero(AGENT_ROLE == 3)))

        # Role 1: Raw Mineral Ochre (#c88428)
        py5.fill(200, 132, 40, 62)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(_build_ribbon_quads(np.flatnonzero(AGENT_ROLE == 1)))

        # Role 2: Burnt Terracotta Sienna (#b84830)
        py5.fill(184, 72, 48, 68)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(_build_ribbon_quads(np.flatnonzero(AGENT_ROLE == 2)))

        # Role 0: Iron-Gall Slate Ink (#26353d)
        py5.fill(38, 53, 61, 64)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(_build_ribbon_quads(np.flatnonzero(AGENT_ROLE == 0)))

    # Save frame, verify non-blank, and compile MP4 on final frame
    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

