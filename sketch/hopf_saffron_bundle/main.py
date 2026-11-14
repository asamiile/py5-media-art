"""hopf_saffron_bundle — Asymmetric Stereographic Hopf Torus Bundle & Depth Drift

A 3D stereographic projection of nested Hopf-like linked torus fibers anchored near
the upper-right golden-ratio focal zone across a rich saturated Prussian-cobalt to
raw-ochre atmospheric field. Smooth spatial camera traversal and multi-layered
parallax glide through translucent luminous saffron-gold, coral-persimmon, and
pale turquoise-ice fiber ribbons that sweep from the dense off-center core out
into expansive stereographic loxodromes across the frame.

100% pure visual art — zero text, zero HUD panels.
"""

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
from lib.shaders import PostFX, draw_fullscreen, load_shader
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 16
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 960 frames
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

SEED = random.uniform(10.0, 900.0)

fx = PostFX(
    bloom=0.34,
    bloom_threshold=0.66,
    tonemap=0.95,
    vignette=0.18,
    grain=0.020,
)
bg_shader = None

# Fiber bundle configuration: 6 shells from compact inner core to wide stereographic loxodromes
NUM_SHELLS = 6
FIBERS_PER_SHELL = 22
NUM_FIBERS = NUM_SHELLS * FIBERS_PER_SHELL  # 132 fibers
PTS_PER_FIBER = 128

SHELL_ETA: np.ndarray
FIBER_PHI: np.ndarray
FIBER_THETA_OFFSET: np.ndarray
FIBER_ROLE: np.ndarray
FIBER_BASE_WIDTH: np.ndarray
FIBER_S: np.ndarray


def _init_fiber_bundle() -> None:
    global SHELL_ETA, FIBER_PHI, FIBER_THETA_OFFSET, FIBER_ROLE, FIBER_BASE_WIDTH, FIBER_S
    rng = np.random.default_rng()

    # Eta in [0.22, 1.38] spans compact central tori (eta ~ 0.25) to huge stereographic outer shells (eta -> pi/2)
    eta_vals = np.array([0.24, 0.46, 0.72, 0.98, 1.18, 1.36], dtype=np.float32)
    phi_vals = np.linspace(0.0, math.tau, FIBERS_PER_SHELL, endpoint=False, dtype=np.float32)

    eta_grid, phi_grid = np.meshgrid(eta_vals, phi_vals, indexing="ij")
    SHELL_ETA = eta_grid.reshape(-1, 1)
    FIBER_PHI = phi_grid.reshape(-1, 1) + rng.uniform(-0.05, 0.05, (NUM_FIBERS, 1)).astype(np.float32)
    FIBER_THETA_OFFSET = rng.uniform(0.0, math.tau, (NUM_FIBERS, 1)).astype(np.float32)

    # Role: 0 = Luminous Saffron Gold (#f4b22a), 1 = Warm Coral Persimmon (#eb5a38),
    # 2 = Pale Turquoise Ice (#94ece6), 3 = Deep Amber Ochre (#d88224)
    shell_idx = np.repeat(np.arange(NUM_SHELLS), FIBERS_PER_SHELL)
    fiber_idx = np.tile(np.arange(FIBERS_PER_SHELL), NUM_SHELLS)
    FIBER_ROLE = (shell_idx + fiber_idx) % 4

    # Outer stereographic shells get broader calligraphic sweep; inner core gets crisp fine filaments
    shell_scale = np.repeat(np.array([0.75, 0.9, 1.1, 1.35, 1.65, 2.0], dtype=np.float32), FIBERS_PER_SHELL)[:, None]
    FIBER_BASE_WIDTH = rng.uniform(3.8, 8.2, (NUM_FIBERS, 1)).astype(np.float32) * shell_scale
    FIBER_S = np.linspace(0.0, math.tau, PTS_PER_FIBER, dtype=np.float32)[None, :]


def _compute_projected_ribbons(t_norm: float, w: float, h: float):
    """Compute 4D S^3 Hopf circle fibers, apply SO(4) Clifford rotation + 3D camera depth traversal,
    and return screen-space quad vertices.
    """
    tau = math.tau
    s = FIBER_S  # (1, P)
    eta = SHELL_ETA  # (F, 1)
    phi = FIBER_PHI + t_norm * tau * 0.5  # Precession around base S^2

    # Base circle in S^3: (z1, z2) = (cos(eta)*e^{i*(s + phi/2)}, sin(eta)*e^{i*(s - phi/2)})
    a1 = s + phi * 0.5 + FIBER_THETA_OFFSET * 0.12
    a2 = s - phi * 0.5 - FIBER_THETA_OFFSET * 0.12

    cos_eta = np.cos(eta)
    sin_eta = np.sin(eta)

    x1 = cos_eta * np.cos(a1)
    x2 = cos_eta * np.sin(a1)
    x3 = sin_eta * np.cos(a2)
    x4 = sin_eta * np.sin(a2)

    # Smooth 4D Clifford rotation in (x1, x4) and (x2, x3) planes so outer shells sweep close to the projection pole (1,0,0,1)
    rot_w = 0.52 * math.sin(t_norm * tau) + 0.38
    cw, sw = math.cos(rot_w), math.sin(rot_w)
    y1 = x1 * cw - x4 * sw
    y4 = x1 * sw + x4 * cw
    y2 = x2 * cw + x3 * sw
    y3 = -x2 * sw + x3 * cw

    # True stereographic projection S^3 -> R^3 with pole at y4 -> 1.08:
    # Outer shells (high sin(eta)) approach y4 ~ 0.92..0.98 and blossom into sweeping multi-scale arcs across the whole canvas
    denom = 1.18 - np.clip(y4, -0.98, 0.96)
    px = y1 / denom
    py = y2 / denom
    pz = y3 / denom

    # Asymmetric stereographic drift: pull the outer sweeping lobes toward the lower-left negative space
    r3_sq = px * px + py * py + pz * pz
    flare = np.tanh(r3_sq * 0.18)
    px = px - flare * 0.65
    py = py + flare * 0.28

    # 3D Spatial Camera / Depth Traversal orbit
    cam_yaw = -0.48 + 0.42 * math.sin(t_norm * tau)
    cam_pitch = 0.32 + 0.20 * math.cos(t_norm * tau)
    cy, sy = math.cos(cam_yaw), math.sin(cam_yaw)
    cp, sp = math.cos(cam_pitch), math.sin(cam_pitch)

    rx = px * cy + pz * sy
    rz0 = -px * sy + pz * cy
    ry = py * cp - rz0 * sp
    rz = py * sp + rz0 * cp

    # Camera close enough to glide inside the outer stereographic arches while viewing the off-center nexus
    cam_dist = 2.85 - 0.35 * math.sin(t_norm * tau)
    z_cam = np.maximum(0.55, cam_dist - rz * 0.55)
    persp = 1.0 / z_cam

    # Asymmetric Off-Center Tension: anchor primary focal nexus near upper-right rule-of-thirds (0.64, 0.40)
    anchor_x = w * (0.64 + 0.025 * math.cos(t_norm * tau))
    anchor_y = h * (0.40 + 0.025 * math.sin(t_norm * tau))
    scale = h * 0.96

    sx = anchor_x + rx * persp * scale
    sy_scr = anchor_y + ry * persp * scale

    # Tangent and normal in screen space
    dx = sx[:, 1:] - sx[:, :-1]
    dy = sy_scr[:, 1:] - sy_scr[:, :-1]
    seg_len = np.hypot(dx, dy) + 1e-4
    nx = -dy / seg_len
    ny = dx / seg_len
    nx = np.concatenate([nx, nx[:, -1:]], axis=1)
    ny = np.concatenate([ny, ny[:, -1:]], axis=1)

    # Ribbon width modulated by perspective depth and harmonic pulse along fiber
    pulse = 0.55 + 0.45 * np.sin(s * 2.0 - t_norm * tau * 2.0 + FIBER_PHI)
    half_w = np.clip(FIBER_BASE_WIDTH * persp * 1.35 * pulse, 0.9, 18.0)

    x_top = sx - nx * half_w
    y_top = sy_scr - ny * half_w
    x_bot = sx + nx * half_w
    y_bot = sy_scr + ny * half_w

    mean_persp = np.mean(persp, axis=1)
    return x_top, y_top, x_bot, y_bot, mean_persp


def _pack_quads(indices: np.ndarray, x_top, y_top, x_bot, y_bot) -> np.ndarray:
    if len(indices) == 0:
        return np.empty((0, 2), dtype=np.float32)
    n_f = len(indices)
    n_seg = PTS_PER_FIBER - 1
    quads = np.empty((n_f, n_seg, 4, 2), dtype=np.float32)
    quads[:, :, 0, 0] = x_top[indices, :-1]
    quads[:, :, 0, 1] = y_top[indices, :-1]
    quads[:, :, 1, 0] = x_bot[indices, :-1]
    quads[:, :, 1, 1] = y_bot[indices, :-1]
    quads[:, :, 2, 0] = x_bot[indices, 1:]
    quads[:, :, 2, 1] = y_bot[indices, 1:]
    quads[:, :, 3, 0] = x_top[indices, 1:]
    quads[:, :, 3, 1] = y_top[indices, 1:]
    return quads.reshape(-1, 2)


def setup() -> None:
    global bg_shader
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    bg_shader = load_shader(SKETCH_DIR / "hopf_saffron_bundle.glsl")
    fx.setup()
    _init_fiber_bundle()


def draw() -> None:
    t_norm = (py5.frame_count - 1) / float(TOTAL_FRAMES)
    w, h = float(SIZE[0]), float(SIZE[1])

    # 1. Render rich saturated Prussian-cobalt to burnt-ochre color field & stereographic caustic aura in GLSL
    draw_fullscreen(
        bg_shader,
        seed=float(SEED),
        phase=float(t_norm * math.tau),
    )

    # 2. Compute 3D stereographic Hopf fiber ribbons with depth traversal
    x_top, y_top, x_bot, y_bot, mean_persp = _compute_projected_ribbons(t_norm, w, h)

    # Split into 3 depth layers (far, mid, near) for deep parallax separation
    q33, q66 = np.quantile(mean_persp, [0.33, 0.66])
    far_mask = mean_persp <= q33
    mid_mask = (mean_persp > q33) & (mean_persp <= q66)
    near_mask = mean_persp > q66

    py5.no_stroke()

    # Color table (R, G, B, far_alpha, mid_alpha, near_alpha)
    palette = [
        (244, 178, 42, 78, 145, 225),   # Role 0: Luminous Saffron Gold (#f4b22a)
        (235, 90, 56, 74, 140, 215),    # Role 1: Warm Coral Persimmon (#eb5a38)
        (148, 236, 230, 72, 138, 215),  # Role 2: Pale Turquoise Ice (#94ece6)
        (216, 130, 36, 68, 128, 198),   # Role 3: Deep Amber Ochre (#d88224)
    ]

    for mask, alpha_idx in ((far_mask, 3), (mid_mask, 4), (near_mask, 5)):
        for role_id, entry in enumerate(palette):
            idx = np.flatnonzero(mask & (FIBER_ROLE == role_id))
            if len(idx) > 0:
                py5.fill(entry[0], entry[1], entry[2], entry[alpha_idx])
                with py5.begin_shape(py5.QUADS):
                    py5.vertices(_pack_quads(idx, x_top, y_top, x_bot, y_bot))

    # High-luminance core filaments on foreground saffron/turquoise fibers
    cx = 0.5 * (x_top + x_bot)
    cy = 0.5 * (y_top + y_bot)
    core_top_x = cx + (x_top - cx) * 0.26
    core_top_y = cy + (y_top - cy) * 0.26
    core_bot_x = cx + (x_bot - cx) * 0.26
    core_bot_y = cy + (y_bot - cy) * 0.26
    core_idx = np.flatnonzero(near_mask & ((FIBER_ROLE == 0) | (FIBER_ROLE == 2)))
    if len(core_idx) > 0:
        py5.fill(255, 246, 224, 195)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(_pack_quads(core_idx, core_top_x, core_top_y, core_bot_x, core_bot_y))

    # 3. Apply PostFX finishing pass
    fx.apply()

    # 4. Save frame, verify non-blank, and compile MP4 on final frame
    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
