"""eikonal_linen_shocks — Boundary-Nucleated Eikonal Wavefronts & Medial-Axis Shock Network.

Sixteen acoustic/seismic wave sources distributed along the four outer boundaries
of a 100% full-canvas high-key raw linen ground (#ede8dc–#e4ddd0) emit continuous
inward-traveling Eikonal wavefronts. Where opposing fronts collide across the open
interior, sharp Rankine-Hugoniot medial-axis shock ridges, branching dendritic
fracture tendrils, and triple-junction shock nodes emerge in iron-gall slate
(#243440), burnt terracotta (#b84a2e), raw gold ochre (#c98826), and malachite
sage (#387268).

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

DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1200 frames (20s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Keep tonemap low (0.18) and vignette subtle (0.07) to preserve the 100% full-canvas high-key linen ground
fx = PostFX(
    bloom=0.12,
    bloom_threshold=0.84,
    aberration=0.0009,
    tonemap=0.18,
    vignette=0.07,
    grain=0.018,
)

# ── Boundary Source & Shock Network Constants ──────────────────────────
N_SOURCES = 16
N_RAYS_PER_SOURCE = 16
N_RAYS = N_SOURCES * N_RAYS_PER_SOURCE  # 256 inward-growing boundary-to-interior shock rays
N_STEPS = 38

SRC_BASE_POS: np.ndarray
SRC_ORBIT_AMP: np.ndarray
SRC_PHASE: np.ndarray
RAY_SRC_ID: np.ndarray
RAY_ANG_OFFSET: np.ndarray
RAY_ROLE: np.ndarray
RAY_WIDTH: np.ndarray

eikonal_shader = None


def _init_sources() -> None:
    """Place 16 perimeter emitter stations around the 4 outer edges of the canvas."""
    global SRC_BASE_POS, SRC_ORBIT_AMP, SRC_PHASE, RAY_SRC_ID, RAY_ANG_OFFSET, RAY_ROLE, RAY_WIDTH
    rng = np.random.default_rng()

    aspect = float(SIZE[0]) / float(SIZE[1])
    hw = aspect * 0.48
    hh = 0.47

    # 5 top, 5 bottom, 3 left, 3 right perimeter emitter positions in aspect-normalized coords
    pts = []
    for x in np.linspace(-hw * 0.88, hw * 0.88, 5):
        pts.append((x, hh))
    for x in np.linspace(-hw * 0.88, hw * 0.88, 5):
        pts.append((x, -hh))
    for y in np.linspace(-hh * 0.65, hh * 0.65, 3):
        pts.append((-hw, y))
    for y in np.linspace(-hh * 0.65, hh * 0.65, 3):
        pts.append((hw, y))

    SRC_BASE_POS = np.array(pts, dtype=np.float32)  # (16, 2)
    SRC_PHASE = (np.arange(N_SOURCES, dtype=np.float32) * 2.3999632)

    RAY_SRC_ID = np.repeat(np.arange(N_SOURCES, dtype=np.int32), N_RAYS_PER_SOURCE)
    RAY_ANG_OFFSET = np.tile(
        np.linspace(-0.42 * math.pi, 0.42 * math.pi, N_RAYS_PER_SOURCE, dtype=np.float32),
        N_SOURCES,
    )
    # 3 mineral ink roles: 0 = Iron-Gall Slate, 1 = Burnt Terracotta, 2 = Malachite Sage
    RAY_ROLE = (np.arange(N_RAYS, dtype=np.int32) % 3)
    RAY_WIDTH = rng.uniform(1.8, 3.4, size=N_RAYS).astype(np.float32)


def _compute_sources(phase: float) -> tuple[np.ndarray, np.ndarray]:
    """Compute animated boundary source positions and Eikonal phase weights matching GLSL."""
    dx = 0.085 * np.cos(phase + SRC_PHASE)
    dy = 0.075 * np.sin(phase * 2.0 + SRC_PHASE * 1.3)
    pos = SRC_BASE_POS + np.stack([dx, dy], axis=1)
    weights = 0.045 * np.sin(phase - SRC_PHASE)
    return pos.astype(np.float32), weights.astype(np.float32)


def _draw_boundary_to_interior_network(
    src_pos: np.ndarray, src_weights: np.ndarray, phase: float
) -> None:
    """Trace inward-growing rays from the 16 boundary emitters that deflect along medial-axis shocks."""
    w, h = float(SIZE[0]), float(SIZE[1])
    aspect = w / h

    # Start each ray at its boundary source and march inward toward the canvas interior
    s_idx = RAY_SRC_ID
    p0 = src_pos[s_idx]  # (N_RAYS, 2)
    # Inward pointing angle toward center (0, 0) plus fan offset
    inward_ang = np.arctan2(-p0[:, 1], -p0[:, 0]) + RAY_ANG_OFFSET + 0.12 * np.sin(phase + s_idx)

    traj = np.empty((N_RAYS, N_STEPS, 2), dtype=np.float32)
    traj[:, 0, :] = p0

    cur_p = p0.copy()
    cur_dir = np.stack([np.cos(inward_ang), np.sin(inward_ang)], axis=1).astype(np.float32)
    step_ds = 0.024

    for step in range(1, N_STEPS):
        # Compute distances from cur_p (N_RAYS, 2) to all 16 sources (16, 2)
        diff = cur_p[:, None, :] - src_pos[None, :, :]  # (N_RAYS, 16, 2)
        dist = np.linalg.norm(diff, axis=2) + src_weights[None, :]  # (N_RAYS, 16)

        # Find closest and second-closest Eikonal source to detect the medial-axis shock bisector
        order = np.argsort(dist, axis=1)
        i1 = order[:, 0]
        i2 = order[:, 1]
        d1 = dist[np.arange(N_RAYS), i1]
        d2 = dist[np.arange(N_RAYS), i2]

        # Unit gradients from source 1 and source 2
        g1 = diff[np.arange(N_RAYS), i1] / np.maximum(d1[:, None], 1e-4)
        g2 = diff[np.arange(N_RAYS), i2] / np.maximum(d2[:, None], 1e-4)

        # Tangent along the medial-axis shock ridge (perpendicular to g1 - g2)
        bisec_n = g1 - g2
        bn_norm = np.maximum(np.linalg.norm(bisec_n, axis=1, keepdims=True), 1e-4)
        bisec_n = bisec_n / bn_norm
        shock_tan = np.stack([-bisec_n[:, 1], bisec_n[:, 0]], axis=1)
        # Align shock tangent with current ray direction
        dot_sign = np.where(np.sum(shock_tan * cur_dir, axis=1, keepdims=True) >= 0.0, 1.0, -1.0)
        shock_tan = shock_tan * dot_sign

        # As the ray approaches a medial-axis shock (d2 - d1 -> 0), bend smoothly into the shock ridge
        shock_proximity = np.exp(-np.abs(d2 - d1) * 18.0)[:, None]
        curl_perturb = 0.14 * np.stack(
            [
                np.sin(cur_p[:, 1] * 11.0 + phase),
                np.cos(cur_p[:, 0] * 11.0 - phase),
            ],
            axis=1,
        )
        next_dir = (1.0 - 0.72 * shock_proximity) * cur_dir + 0.72 * shock_proximity * shock_tan + curl_perturb
        next_dir /= np.maximum(np.linalg.norm(next_dir, axis=1, keepdims=True), 1e-4)
        cur_dir = next_dir
        cur_p = cur_p + cur_dir * step_ds
        traj[:, step, :] = cur_p

    # Convert aspect-normalized coords to screen pixels
    sx = (traj[:, :, 0] / aspect + 0.5) * w
    sy = (0.5 - traj[:, :, 1]) * h

    dx = np.gradient(sx, axis=1)
    dy = np.gradient(sy, axis=1)
    inv_len = 1.0 / np.maximum(np.hypot(dx, dy), 1e-4)
    nx = -dy * inv_len
    ny = dx * inv_len

    # Advecting wavefront pulse along each filament
    s_lin = np.linspace(0.0, 1.0, N_STEPS, dtype=np.float32)[None, :]
    pulse = 0.65 + 0.45 * np.sin(s_lin * 12.0 - phase * 3.0)
    taper = np.clip(np.sin(s_lin * math.pi), 0.0, 1.0) ** 0.45
    hw = RAY_WIDTH[:, None] * taper * pulse

    x_up = sx + nx * hw
    y_up = sy + ny * hw
    x_dn = sx - nx * hw
    y_dn = sy - ny * hw

    quads = np.empty((N_RAYS, N_STEPS - 1, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_up[:, :-1]
    quads[:, :, 0, 1] = y_up[:, :-1]
    quads[:, :, 1, 0] = x_up[:, 1:]
    quads[:, :, 1, 1] = y_up[:, 1:]
    quads[:, :, 2, 0] = x_dn[:, 1:]
    quads[:, :, 2, 1] = y_dn[:, 1:]
    quads[:, :, 3, 0] = x_dn[:, :-1]
    quads[:, :, 3, 1] = y_dn[:, :-1]

    role_rgba = (
        (36, 52, 64, 175),     # 0: Iron-Gall Slate (#243440)
        (184, 74, 46, 165),    # 1: Burnt Terracotta (#b84a2e)
        (56, 114, 104, 160),   # 2: Malachite Sage (#387268)
    )

    py5.no_stroke()
    for r_id, rgba in enumerate(role_rgba):
        mask = RAY_ROLE == r_id
        py5.fill(*rgba)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(quads[mask].reshape(-1, 2))

    # Draw crisp diamond nodes at the 16 perimeter emitter stations and interior shock tips
    tip_x = sx[:, -6].reshape(-1)
    tip_y = sy[:, -6].reshape(-1)
    rad = 4.2
    n_tips = len(tip_x)
    t_quads = np.empty((n_tips, 4, 2), dtype=np.float32)
    t_quads[:, 0, 0], t_quads[:, 0, 1] = tip_x - rad, tip_y
    t_quads[:, 1, 0], t_quads[:, 1, 1] = tip_x, tip_y - rad
    t_quads[:, 2, 0], t_quads[:, 2, 1] = tip_x + rad, tip_y
    t_quads[:, 3, 0], t_quads[:, 3, 1] = tip_x, tip_y + rad

    py5.fill(184, 74, 46, 205)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(t_quads.reshape(-1, 2))


def setup() -> None:
    global eikonal_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    eikonal_shader = load_shader(str(SKETCH_DIR / "eikonal_linen_shocks.glsl"))
    fx.setup()
    _init_sources()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    phase = u_loop * math.tau

    src_pos, src_weights = _compute_sources(phase)

    eikonal_shader.set("u_resolution", float(SIZE[0]), float(SIZE[1]))
    eikonal_shader.set("u_phase", float(phase))
    draw_fullscreen(eikonal_shader)

    _draw_boundary_to_interior_network(src_pos, src_weights, phase)

    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
