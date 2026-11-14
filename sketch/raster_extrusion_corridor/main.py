"""raster_extrusion_corridor — 3D Volumetric Raster Deflection & Phase-Slip Slabs (P3D).

A true P3D volumetric constructivist signal sculpture where 28 depth-stacked raster
deflection ribbon curtains and 220 quantized phase-slip voxel blocks are extruded into
three-dimensional perspective space over a carbon-black void (#0d0f14). An orbiting
perspective camera traverses the depth corridor while electromagnetic scanline shears
and staircase quantization steps deform the 3D raster planes in bone white (#f3f0e8),
signal vermilion (#e83424), international ultramarine (#1c3ed6), and cadmium ochre (#f2b218).

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
from lib.shaders import PostFX
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

fx = PostFX(
    bloom=0.24,
    bloom_threshold=0.68,
    aberration=0.0014,
    tonemap=0.88,
    vignette=0.18,
    grain=0.018,
)

# 3D Volumetric Raster Ribbon Curtains
N_LAYERS = 28
N_COLS = 96

# Stark Constructivist High-Contrast Palette (Base RGB in [0, 1])
PALETTE_RGB = np.array(
    [
        [0.953, 0.941, 0.910],  # 0: Crisp Bone White (#f3f0e8)
        [0.910, 0.204, 0.141],  # 1: Signal Vermilion (#e83424)
        [0.110, 0.243, 0.839],  # 2: International Ultramarine (#1c3ed6)
        [0.949, 0.698, 0.094],  # 3: Cadmium Ochre (#f2b218)
        [0.196, 0.224, 0.275],  # 4: Dark Constructivist Steel (#323946)
    ],
    dtype=np.float32,
)

X_GRID: np.ndarray
Z_BASE: np.ndarray
LAYER_ROLE: np.ndarray
LAYER_FREQ: np.ndarray
LAYER_PHASE: np.ndarray
LAYER_HEIGHT: np.ndarray
LAYER_Y_OFFSET: np.ndarray

# Floating 3D Quantized Signal Blocks (cuboids)
N_BLOCKS = 180
BLK_X0: np.ndarray
BLK_Y0: np.ndarray
BLK_Z0: np.ndarray
BLK_SX: np.ndarray
BLK_SY: np.ndarray
BLK_SZ: np.ndarray
BLK_ROLE: np.ndarray
BLK_PHASE: np.ndarray

# Unit cube 6 faces (each face has 4 vertices + 1 normal)
CUBE_FACES = np.array(
    [
        # +Z front
        [[-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]],
        # -Z back
        [[0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5]],
        # +Y bottom
        [[-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5]],
        # -Y top
        [[-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5]],
        # +X right
        [[0.5, -0.5, 0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [0.5, 0.5, 0.5]],
        # -X left
        [[-0.5, -0.5, -0.5], [-0.5, -0.5, 0.5], [-0.5, 0.5, 0.5], [-0.5, 0.5, -0.5]],
    ],
    dtype=np.float32,
)
CUBE_FACE_SHADE = np.array([1.0, 0.58, 0.48, 0.92, 0.78, 0.72], dtype=np.float32)


def _init_scene() -> None:
    global X_GRID, Z_BASE, LAYER_ROLE, LAYER_FREQ, LAYER_PHASE, LAYER_HEIGHT, LAYER_Y_OFFSET
    global BLK_X0, BLK_Y0, BLK_Z0, BLK_SX, BLK_SY, BLK_SZ, BLK_ROLE, BLK_PHASE

    rng = np.random.default_rng()

    x_vals = np.linspace(-1850.0, 1850.0, N_COLS, dtype=np.float32)
    z_vals = np.linspace(-1500.0, 1500.0, N_LAYERS, dtype=np.float32)
    Z_BASE, X_GRID = np.meshgrid(z_vals, x_vals, indexing="ij")

    # Assign constructivist color roles across the 28 Z-planes
    roles = [0, 1, 2, 0, 3, 4, 1, 0, 2, 3, 0, 1, 4, 2] * 2
    LAYER_ROLE = np.array(roles[:N_LAYERS], dtype=np.int32)
    LAYER_FREQ = rng.uniform(1.8, 4.4, size=(N_LAYERS, 1)).astype(np.float32)
    LAYER_PHASE = rng.uniform(0.0, math.tau, size=(N_LAYERS, 1)).astype(np.float32)
    LAYER_HEIGHT = rng.uniform(44.0, 96.0, size=(N_LAYERS, 1)).astype(np.float32)
    LAYER_Y_OFFSET = np.linspace(-560.0, 560.0, N_LAYERS, dtype=np.float32).reshape(N_LAYERS, 1)

    # Initialize 180 floating 3D constructivist signal cuboids
    BLK_X0 = rng.uniform(-1680.0, 1680.0, size=N_BLOCKS).astype(np.float32)
    BLK_Y0 = rng.uniform(-680.0, 680.0, size=N_BLOCKS).astype(np.float32)
    BLK_Z0 = rng.uniform(-1450.0, 1450.0, size=N_BLOCKS).astype(np.float32)
    BLK_SX = rng.uniform(65.0, 260.0, size=N_BLOCKS).astype(np.float32)
    BLK_SY = rng.uniform(16.0, 54.0, size=N_BLOCKS).astype(np.float32)
    BLK_SZ = rng.uniform(28.0, 95.0, size=N_BLOCKS).astype(np.float32)
    BLK_PHASE = rng.uniform(0.0, math.tau, size=N_BLOCKS).astype(np.float32)
    BLK_ROLE = rng.choice([0, 1, 2, 3], size=N_BLOCKS, p=[0.32, 0.28, 0.22, 0.18]).astype(
        np.int32
    )


def _compute_raster_ribbons(
    u_loop: float, z_travel: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute 3D extruded raster ribbon curtains with quantized scanline deflection."""
    theta = u_loop * math.tau
    x_norm = X_GRID / 1850.0  # (N_LAYERS, N_COLS)

    # Seamless Z-corridor wrap in [-1500, 1500]
    z_wrapped = np.mod(Z_BASE + z_travel + 1500.0, 3000.0) - 1500.0

    # Quantized horizontal scanline phase-slip shear per layer
    slip_gate = np.round(np.sin(theta * 2.0 + LAYER_PHASE)) * np.power(
        np.abs(np.sin(theta + LAYER_PHASE * 0.5)), 2.0
    )
    x_sheared = X_GRID + slip_gate * 135.0

    # Continuous carrier wave + staircase quantization
    carrier = (
        np.sin(x_norm * math.pi * LAYER_FREQ + theta * 2.0 + LAYER_PHASE)
        + 0.55 * np.cos(x_norm * math.pi * (LAYER_FREQ * 1.7) - theta + z_wrapped * 0.0025)
    )
    quant_carrier = np.round(carrier * 3.5) / 3.5

    # Y deflection and Z harmonic ripple
    y_center = (
        LAYER_Y_OFFSET
        + 155.0 * quant_carrier
        + 65.0 * np.sin(x_norm * math.pi * 1.5 - theta + LAYER_PHASE)
    )
    z_pos = z_wrapped + 52.0 * np.cos(x_norm * math.pi * 3.0 + theta * 2.0 + LAYER_PHASE)

    # Ribbon vertical thickness modulated by signal envelope
    half_h = LAYER_HEIGHT * (
        0.55 + 0.45 * np.abs(np.cos(x_norm * math.pi * 2.5 - theta + LAYER_PHASE))
    )

    # Top and bottom 3D edges of each ribbon curtain: (N_LAYERS, N_COLS, 3)
    pts_top = np.stack([x_sheared, y_center - half_h, z_pos], axis=-1).astype(np.float32)
    pts_bot = np.stack([x_sheared, y_center + half_h, z_pos - 28.0], axis=-1).astype(np.float32)

    # Build quads (N_LAYERS, N_COLS - 1, 4, 3)
    quads = np.empty((N_LAYERS, N_COLS - 1, 4, 3), dtype=np.float32)
    quads[:, :, 0, :] = pts_top[:, :-1, :]
    quads[:, :, 1, :] = pts_top[:, 1:, :]
    quads[:, :, 2, :] = pts_bot[:, 1:, :]
    quads[:, :, 3, :] = pts_bot[:, :-1, :]

    # Compute surface normals for two-sided directional lighting
    u_vec = quads[:, :, 1, :] - quads[:, :, 0, :]
    v_vec = quads[:, :, 3, :] - quads[:, :, 0, :]
    normals = np.cross(u_vec, v_vec)
    n_len = np.linalg.norm(normals, axis=-1, keepdims=True) + 1e-6
    normals = normals / n_len

    light_dir = np.array([0.42, -0.58, 0.70], dtype=np.float32)
    ndotl = np.abs(np.sum(normals * light_dir, axis=-1))

    # Depth fog attenuation for spatial depth sense
    z_mid = 0.5 * (z_pos[:, :-1] + z_pos[:, 1:])
    depth_fade = np.clip((z_mid + 1650.0) / 3150.0, 0.25, 1.0)
    shade = np.clip((0.32 + 0.72 * ndotl) * depth_fade, 0.22, 1.05)

    role_grid = np.broadcast_to(LAYER_ROLE[:, None], (N_LAYERS, N_COLS - 1))
    return quads, shade, role_grid, pts_top


def setup() -> None:
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    fx.setup()
    _init_scene()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    theta = u_loop * math.tau

    # Stark Constructivist Carbon-Black Ground (#0d0f14)
    py5.background(13, 15, 20)
    py5.hint(py5.ENABLE_DEPTH_TEST)

    # Spatial Camera / Depth Traversal: smooth cyclic orbit + seamless Z-corridor traversal
    fov = math.radians(50.0)
    aspect = float(SIZE[0]) / float(SIZE[1])
    py5.perspective(fov, aspect, 20.0, 9000.0)

    cam_x = 460.0 * math.sin(theta) + 140.0 * math.cos(theta * 2.0)
    cam_y = -240.0 * math.cos(theta) + 95.0 * math.sin(theta * 2.0)
    cam_z = 1320.0 + 220.0 * math.sin(theta)
    look_x = 120.0 * math.cos(theta)
    look_y = 65.0 * math.sin(theta)
    look_z = -240.0
    py5.camera(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0.0, 1.0, 0.0)

    # Seamless 1-cycle Z-advection over the 16-second loop (3000 units = full corridor period)
    z_travel = u_loop * 3000.0

    quads, shade, role_grid, pts_top = _compute_raster_ribbons(u_loop, z_travel)

    # 1. Render opaque 3D extruded raster ribbons batched by color role & 7 shading bins
    py5.no_stroke()
    n_bins = 7
    s_edges = np.linspace(0.20, 1.06, n_bins + 1)
    s_centers = 0.5 * (s_edges[:-1] + s_edges[1:])

    q_flat = quads.reshape(-1, 4, 3)
    s_flat = shade.reshape(-1)
    r_flat = role_grid.reshape(-1)

    for role_id in range(len(PALETTE_RGB)):
        base_rgb = PALETTE_RGB[role_id]
        r_mask = r_flat == role_id
        for b_idx in range(n_bins):
            mask = r_mask & (s_flat >= s_edges[b_idx]) & (s_flat < s_edges[b_idx + 1])
            idx = np.flatnonzero(mask)
            if len(idx) > 0:
                sv = float(s_centers[b_idx])
                rc = int(min(255, base_rgb[0] * sv * 255.0))
                gc = int(min(255, base_rgb[1] * sv * 255.0))
                bc = int(min(255, base_rgb[2] * sv * 255.0))
                py5.fill(rc, gc, bc, 255)
                with py5.begin_shape(py5.QUADS):
                    py5.vertices(q_flat[idx].reshape(-1, 3))

    # 2. Crisp bone-white & vermilion quantized scanline edge rails along ribbon crests
    py5.no_fill()
    py5.stroke(243, 240, 232, 215)
    py5.stroke_weight(1.9)
    top_segs = np.empty((N_LAYERS, N_COLS - 1, 2, 3), dtype=np.float32)
    top_segs[:, :, 0, :] = pts_top[:, :-1, :]
    top_segs[:, :, 1, :] = pts_top[:, 1:, :]
    with py5.begin_shape(py5.LINES):
        py5.vertices(top_segs.reshape(-1, 3))

    # Vertical quantization step struts every 6th column
    strut_cols = list(range(0, N_COLS, 6))
    strut_segs = np.empty((N_LAYERS - 1, len(strut_cols), 2, 3), dtype=np.float32)
    strut_segs[:, :, 0, :] = pts_top[:-1, strut_cols, :]
    strut_segs[:, :, 1, :] = pts_top[1:, strut_cols, :]
    py5.stroke(232, 52, 36, 145)
    py5.stroke_weight(1.3)
    with py5.begin_shape(py5.LINES):
        py5.vertices(strut_segs.reshape(-1, 3))

    # 3. Render 180 floating 3D quantized signal voxel cuboids traversing the corridor
    py5.no_stroke()
    bz = np.mod(BLK_Z0 + z_travel * 2.0 + 1500.0, 3000.0) - 1500.0
    bx = BLK_X0 + 95.0 * np.round(np.sin(theta * 2.0 + BLK_PHASE))
    by = BLK_Y0 + 48.0 * np.cos(theta + BLK_PHASE)
    b_depth = np.clip((bz + 1650.0) / 3150.0, 0.30, 1.0)

    centers = np.stack([bx, by, bz], axis=-1)[:, None, None, :]  # (N_BLOCKS, 1, 1, 3)
    scales = np.stack([BLK_SX, BLK_SY, BLK_SZ], axis=-1)[:, None, None, :]
    cube_verts = centers + CUBE_FACES[None, :, :, :] * scales  # (N_BLOCKS, 6, 4, 3)

    for role_id in range(4):
        base_rgb = PALETTE_RGB[role_id]
        r_idx = np.flatnonzero(BLK_ROLE == role_id)
        if len(r_idx) == 0:
            continue
        for f_idx in range(6):
            sv = float(CUBE_FACE_SHADE[f_idx]) * 0.92
            rc = int(min(255, base_rgb[0] * sv * 255.0))
            gc = int(min(255, base_rgb[1] * sv * 255.0))
            bc = int(min(255, base_rgb[2] * sv * 255.0))
            py5.fill(rc, gc, bc, 255)
            face_quads = cube_verts[r_idx, f_idx, :, :].reshape(-1, 3)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(face_quads)

    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.camera()
    py5.perspective()

    fx.apply()

    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()

