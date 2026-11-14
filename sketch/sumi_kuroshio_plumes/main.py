"""sumi_kuroshio_plumes — Persistent Nocturnal Ink-Wash Plumes & Curl-Vortex Trails.

Across a continuous edge-to-edge deep nocturnal indigo and sumi-charcoal ground
(#0b0e15), 2,600 divergence-free curl-vortex brush filaments advect along vortex
separatrix ridges and gyre cores of a breathing multi-dipole streamfunction ψ(x, y, t).
Through persistent translucent frame-fading accumulation, layered sumi-graphite,
silver-mist, and luminous moonlit-chalk washes build up glowing atmospheric ink
plumes while high-vorticity shear streams ignite with a single restrained
vermilion-cinnabar accent (#f04e32).

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

# ── Constants ──────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 21
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1260 frames (21s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PLUMES = 2600
SUBSTEPS = 6

PX: np.ndarray
PY: np.ndarray
P_ROLE: np.ndarray
P_WIDTH: np.ndarray
P_SPEED: np.ndarray
P_PHASE: np.ndarray
RNG: np.random.Generator


def _sample_ridge_positions(rng: np.random.Generator, n: int, w: float, h: float) -> tuple[np.ndarray, np.ndarray]:
    """Sample particle positions concentrated along diagonal Kuroshio jet streams & gyres."""
    # Mix 75% concentrated stream-band seeds + 25% ambient field seeds
    x = rng.uniform(0.0, w, size=n).astype(np.float32)
    band_id = rng.integers(0, 5, size=n)
    band_y = (band_id + 0.5) * (h / 5.0) + 0.16 * h * np.sin((x / w) * math.tau * 1.5 + band_id * 1.2)
    y_stream = np.mod(band_y + rng.normal(0.0, h * 0.048, size=n), h).astype(np.float32)
    y_unif = rng.uniform(0.0, h, size=n).astype(np.float32)
    is_stream = rng.random(n) < 0.78
    y = np.where(is_stream, y_stream, y_unif)
    return x, y


def _init_plumes(w: float, h: float) -> None:
    """Initialize 2,600 ink-wash plume filaments across the full 3840x2160 canvas."""
    global PX, PY, P_ROLE, P_WIDTH, P_SPEED, P_PHASE, RNG
    RNG = np.random.default_rng()

    PX, PY = _sample_ridge_positions(RNG, NUM_PLUMES, w, h)
    P_SPEED = RNG.uniform(7.5, 16.5, size=NUM_PLUMES).astype(np.float32)
    P_PHASE = RNG.uniform(0.0, math.tau, size=NUM_PLUMES).astype(np.float32)

    # Roles for Deep Nocturnal Monochrome + Single Accent:
    # 0 = Deep Slate-Blue Ink Wash (#2c3e5a, wide atmospheric brush)
    # 1 = Luminous Silver-Mist Wash (#94abc7, medium brush)
    # 2 = Moonlit Chalk Highlight (#eef4fc, crisp calligraphic filament)
    # 3 = Single Accent Vermilion Flare (#ff5232, restrained 14% of filaments)
    r = RNG.random(NUM_PLUMES)
    P_ROLE = np.zeros(NUM_PLUMES, dtype=np.int32)
    P_ROLE[r >= 0.30] = 1
    P_ROLE[r >= 0.62] = 2
    P_ROLE[r >= 0.86] = 3

    P_WIDTH = np.where(
        P_ROLE == 0,
        RNG.uniform(22.0, 42.0, size=NUM_PLUMES),
        np.where(
            P_ROLE == 1,
            RNG.uniform(8.5, 16.5, size=NUM_PLUMES),
            np.where(
                P_ROLE == 2,
                RNG.uniform(2.8, 5.8, size=NUM_PLUMES),
                RNG.uniform(4.2, 8.8, size=NUM_PLUMES),
            ),
        ),
    ).astype(np.float32)


def _curl_velocity(
    x: np.ndarray, y: np.ndarray, w: float, h: float, theta: float
) -> tuple[np.ndarray, np.ndarray]:
    """Compute divergence-free curl velocity (vx, vy) = (dpsi/dy, -dpsi/dx) on the torus."""
    nx = (x / w) * math.tau
    ny = (y / h) * math.tau

    c1 = math.cos(theta)
    s1 = math.sin(theta)
    c2 = math.cos(theta * 2.0)
    s2 = math.sin(theta * 2.0)

    a1 = 0.56
    a2 = 0.38
    a3 = 0.24
    a4 = 0.18

    u1 = nx + c1 * 1.1
    v1 = ny + s1 * 1.1
    u2 = 2.0 * nx - ny - s1 * 1.4
    v2 = nx + 2.0 * ny + c1 * 1.4
    u3 = 3.0 * nx + 2.0 * ny + c2 * 1.2
    u4 = nx - 3.0 * ny - s2 * 1.2

    dpsi_dx = (
        a1 * np.cos(u1) * np.cos(v1)
        + a2 * (-2.0 * np.sin(u2) * np.sin(v2) + np.cos(u2) * np.cos(v2))
        + a3 * 3.0 * np.cos(u3)
        - a4 * np.sin(u4)
    )
    dpsi_dy = (
        -a1 * np.sin(u1) * np.sin(v1)
        + a2 * (np.sin(u2) * np.sin(v2) + 2.0 * np.cos(u2) * np.cos(v2))
        + a3 * 2.0 * np.cos(u3)
        + a4 * 3.0 * np.sin(u4)
    )

    vx = dpsi_dy + 0.34 * math.cos(theta)
    vy = -dpsi_dx + 0.18 * math.sin(theta * 2.0)

    mag = np.hypot(vx, vy) + 1e-5
    return vx / mag, vy / mag


def _step_and_build_quads(
    w: float, h: float, theta: float
) -> list[np.ndarray]:
    """Advance all 2,600 plumes through SUBSTEPS and build ribbon QUADS per color role."""
    global PX, PY

    role_quads: list[list[np.ndarray]] = [[] for _ in range(4)]
    pulse = 0.68 + 0.32 * np.sin(theta * 2.0 + P_PHASE)
    half_w = (P_WIDTH * pulse * 0.5).astype(np.float32)

    for _ in range(SUBSTEPS):
        vx, vy = _curl_velocity(PX, PY, w, h, theta)
        dt = P_SPEED / float(SUBSTEPS)
        x1 = PX + vx * dt
        y1 = PY + vy * dt

        nx = -vy * half_w
        ny = vx * half_w

        q = np.empty((NUM_PLUMES, 4, 2), dtype=np.float32)
        q[:, 0, 0] = PX - nx
        q[:, 0, 1] = PY - ny
        q[:, 1, 0] = PX + nx
        q[:, 1, 1] = PY + ny
        q[:, 2, 0] = x1 + nx
        q[:, 2, 1] = y1 + ny
        q[:, 3, 0] = x1 - nx
        q[:, 3, 1] = y1 - ny

        for r_id in range(4):
            idx = np.flatnonzero(P_ROLE == r_id)
            if len(idx) > 0:
                role_quads[r_id].append(q[idx].reshape(-1, 2))

        PX = np.mod(x1, w)
        PY = np.mod(y1, h)

    reseed_mask = RNG.random(NUM_PLUMES) < 0.012
    n_reseed = int(np.sum(reseed_mask))
    if n_reseed > 0:
        rx, ry = _sample_ridge_positions(RNG, n_reseed, w, h)
        PX[reseed_mask] = rx
        PY[reseed_mask] = ry

    return [
        np.concatenate(rq, axis=0) if rq else np.empty((0, 2), dtype=np.float32)
        for rq in role_quads
    ]


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    w, h = float(SIZE[0]), float(SIZE[1])
    # Deep Nocturnal Indigo-Obsidian Ground (#090c14)
    py5.background(9, 12, 20)
    _init_plumes(w, h)


def draw() -> None:
    fc = py5.frame_count
    w, h = float(SIZE[0]), float(SIZE[1])

    # On frame 1, pre-accumulate 28 historical steps so frame 1 opens with rich luminous ink-wash plumes
    n_passes = 28 if fc == 1 else 1
    base_frame = fc - 1

    # Role colors (R, G, B, A):
    # 0 = Deep Slate-Blue Ink Wash (#2c3e5a)
    # 1 = Luminous Silver-Mist Wash (#94abc7)
    # 2 = Moonlit Chalk Highlight (#eef4fc)
    # 3 = Single Accent Vermilion-Cinnabar (#ff5232)
    role_colors = [
        (44, 62, 90, 48),
        (148, 171, 199, 88),
        (238, 244, 252, 165),
        (255, 82, 50, 205),
    ]

    py5.no_stroke()
    for p_idx in range(n_passes):
        # Persistent Trail Accumulation & Decay via translucent nocturnal obsidian veil
        py5.fill(9, 12, 20, 12)
        py5.rect(0.0, 0.0, w, h)

        step_num = base_frame - (n_passes - 1 - p_idx)
        u_loop = (step_num % TOTAL_FRAMES) / float(TOTAL_FRAMES)
        theta = u_loop * math.tau

        quad_batches = _step_and_build_quads(w, h, theta)
        for r_id, (rc, gc, bc, ac) in enumerate(role_colors):
            verts = quad_batches[r_id]
            if len(verts) > 0:
                py5.fill(rc, gc, bc, ac)
                with py5.begin_shape(py5.QUADS):
                    py5.vertices(verts)

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
