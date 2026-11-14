"""enneper_mineral_petals — 3D Minimal Surface Petals & Multi-Act Bonnet Morphing

A true P3D sculptural minimal-surface study where three harmonic Enneper-Bonnet
surface shells (orders k=2, 3, 4) unfurl, twist through an isometric Bonnet
association angle, and breathe across a full-canvas warm alabaster-linen field
(#ede8dc). Rendered with 12-band smooth mineral shading and crisp iron-gall
geodesic rib lines in mineral ochre, burnt terracotta, iron-gall slate, and
celadon malachite.

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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = frames_dir(SKETCH_DIR)

DURATION_SEC = 22
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1320 frames
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

fx = PostFX(
    bloom=0.10,
    bloom_threshold=0.88,
    tonemap=0.22,
    vignette=0.06,
    grain=0.018,
)

# High-resolution mesh per minimal surface shell
NR = 44
NV = 160

R_GRID: np.ndarray
V_GRID: np.ndarray

# High-Key Mineral & Washi Palette (Base RGB in [0, 1])
PALETTE_RGB = np.array(
    [
        [0.165, 0.224, 0.255],  # 0: Iron-Gall Slate Ink (#2a3941)
        [0.722, 0.290, 0.192],  # 1: Burnt Terracotta Sienna (#b84a31)
        [0.784, 0.525, 0.165],  # 2: Raw Mineral Ochre (#c8862a)
        [0.243, 0.427, 0.408],  # 3: Celadon Malachite Slate (#3e6d68)
    ],
    dtype=np.float32,
)


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    u = min(max((x - edge0) / (edge1 - edge0), 0.0), 1.0)
    return u * u * (3.0 - 2.0 * u)


def _init_grid() -> None:
    global R_GRID, V_GRID
    r_vals = np.linspace(0.06, 1.0, NR, dtype=np.float32)
    v_vals = np.linspace(0.0, math.tau, NV, dtype=np.float32)
    R_GRID, V_GRID = np.meshgrid(r_vals, v_vals, indexing="ij")


def _compute_enneper_shell(
    r_norm: np.ndarray,
    v: np.ndarray,
    order_k: int,
    r_max: float,
    bonnet_angle: float,
    twist_amp: float,
    scale: float,
    offset_xyz: tuple[float, float, float],
    rot_mat: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute generalized harmonic Enneper-Bonnet minimal surface (NR, NV, 3),
    quad vertices (Q, 4, 3), smooth two-sided shading intensity (Q,), and radial coord (Q,).
    """
    r = r_norm * r_max
    k = order_k
    kp1 = k + 1

    r_2kp1 = (r ** (2 * k + 1)) / float(2 * k + 1)
    r_kp1 = (r**kp1) / float(kp1) * 1.45

    ang1 = v
    ang_2kp1 = (2 * k + 1) * v
    ang_kp1 = kp1 * v

    x0 = r * np.cos(ang1) - r_2kp1 * np.cos(ang_2kp1)
    y0 = -r * np.sin(ang1) - r_2kp1 * np.sin(ang_2kp1)
    z0 = 2.0 * r_kp1 * np.cos(ang_kp1)

    x90 = r * np.sin(ang1) - r_2kp1 * np.sin(ang_2kp1)
    y90 = r * np.cos(ang1) - r_2kp1 * np.cos(ang_2kp1)
    z90 = 2.0 * r_kp1 * np.sin(ang_kp1)

    cb = math.cos(bonnet_angle)
    sb = math.sin(bonnet_angle)

    px = (cb * x0 + sb * x90) * scale
    py = (cb * y0 + sb * y90) * scale
    pz = (cb * z0 + sb * z90) * scale

    if abs(twist_amp) > 1e-4:
        tw = twist_amp * (r_norm**1.5) * np.sin(k * v)
        pz = pz + tw * scale * 0.40

    pts = np.stack([px, py, pz], axis=-1)  # (NR, NV, 3)
    pts = pts @ rot_mat.T
    pts[:, :, 0] += offset_xyz[0]
    pts[:, :, 1] += offset_xyz[1]
    pts[:, :, 2] += offset_xyz[2]

    p00 = pts[:-1, :-1]
    p10 = pts[1:, :-1]
    p11 = pts[1:, 1:]
    p01 = pts[:-1, 1:]

    quads = np.stack([p00, p10, p11, p01], axis=2)

    d1 = p11 - p00
    d2 = p01 - p10
    norms = np.cross(d1, d2)
    norm_len = np.linalg.norm(norms, axis=-1, keepdims=True) + 1e-5
    norms = norms / norm_len

    light_key = np.array([0.48, -0.64, 0.60], dtype=np.float32)
    light_fill = np.array([-0.60, 0.45, 0.66], dtype=np.float32)

    dot_key = np.abs(np.sum(norms * light_key, axis=-1))
    dot_fill = np.abs(np.sum(norms * light_fill, axis=-1))

    r_mid = 0.5 * (r_norm[:-1, :-1] + r_norm[1:, 1:])
    shade = 0.34 + 0.50 * dot_key + 0.22 * dot_fill
    return pts, quads.reshape(-1, 4, 3), np.clip(shade.reshape(-1), 0.25, 1.05), r_mid.reshape(-1)


def setup() -> None:
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    fx.setup()
    _init_grid()


def draw() -> None:
    t_norm = (py5.frame_count - 1) / float(TOTAL_FRAMES)
    tau = math.tau
    w, h = float(SIZE[0]), float(SIZE[1])

    # Full-canvas High-Key Mineral & Washi warm alabaster ground (#ede8dc)
    py5.background(237, 232, 220)
    py5.hint(py5.ENABLE_DEPTH_TEST)

    # Multi-Act Temporal Evolution envelope:
    # Act I (0..0.24): Nucleation & unfolding
    # Act II (0.24..0.58): Expansive Bonnet isometric sweep
    # Act III (0.58..0.84): Harmonic torsion & counter-rotating petal interpenetration
    # Act IV (0.84..1.00): Serene crystalline equilibrium
    unfold = 0.84 + 0.18 * _smoothstep(0.0, 0.26, t_norm) - 0.08 * _smoothstep(0.84, 1.0, t_norm)
    bonnet_phase = t_norm * tau + 0.38 * math.sin(t_norm * tau * 2.0)
    act3_twist = 0.42 * _smoothstep(0.35, 0.68, t_norm) * (1.0 - 0.65 * _smoothstep(0.82, 1.0, t_norm))

    fov = math.pi / 3.5
    camera_z = (h / 2.0) / math.tan(fov / 2.0)
    py5.perspective(fov, w / h, camera_z / 10.0, camera_z * 10.0)

    cam_x = 180.0 * math.sin(t_norm * tau)
    cam_y = -110.0 + 85.0 * math.cos(t_norm * tau)
    cam_z = 1480.0 - 90.0 * math.sin(t_norm * tau)
    py5.camera(cam_x, cam_y, cam_z, 0.0, 0.0, 0.0, 0.06, 1.0, 0.0)

    # Three well-proportioned minimal-surface sculptures across the 3D volume:
    # r_max kept in [0.88, 1.02] so the saddle petals curl gracefully within the frame
    shell_configs = [
        # (order_k, r_max, bonnet_offset, scale, offset_xyz, rot_angles, role_inner, role_mid, role_outer)
        (
            3,
            0.94 * unfold,
            bonnet_phase,
            340.0,
            (-390.0, -35.0, 40.0),
            (0.46 + 0.22 * math.sin(t_norm * tau), -0.48 + t_norm * tau * 0.5, 0.18),
            1,  # Burnt Terracotta core
            2,  # Mineral Ochre body
            0,  # Iron-Gall Slate rim
        ),
        (
            2,
            0.98 * unfold,
            -bonnet_phase * 0.8 + 0.7,
            310.0,
            (440.0, -145.0, -60.0),
            (-0.40 + 0.20 * math.cos(t_norm * tau), 0.58 - t_norm * tau * 0.5, -0.22),
            0,  # Iron-Gall Slate core
            3,  # Celadon Malachite body
            2,  # Mineral Ochre rim
        ),
        (
            4,
            0.90 * unfold,
            bonnet_phase * 1.2 - 0.5,
            275.0,
            (130.0, 275.0, 140.0),
            (0.56 - 0.18 * math.sin(t_norm * tau), -0.26 + t_norm * tau * 0.5, 0.28),
            2,  # Mineral Ochre core
            1,  # Burnt Terracotta body
            3,  # Celadon Malachite rim
        ),
    ]

    # 8 smooth shading bins + 5 radial mineral transition zones -> seamless silk/ceramic gradation
    n_shade_bins = 8
    shade_edges = np.linspace(0.24, 1.06, n_shade_bins + 1)
    shade_centers = 0.5 * (shade_edges[:-1] + shade_edges[1:])

    r_zone_edges = (0.0, 0.34, 0.56, 0.78, 1.05)
    r_zone_mix = (
        (1.0, 0.0, 0.0),
        (0.45, 0.55, 0.0),
        (0.0, 0.75, 0.25),
        (0.0, 0.20, 0.80),
    )
    alabaster_tint = np.array([0.935, 0.914, 0.870], dtype=np.float32)

    for order_k, r_max, b_ang, scale, offset_xyz, (rx, ry, rz), role_in, role_mid, role_out in shell_configs:
        cx, sx = math.cos(rx), math.sin(rx)
        cy, sy = math.cos(ry), math.sin(ry)
        cz, sz = math.cos(rz), math.sin(rz)

        ry_m = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float32)
        rx_m = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]], dtype=np.float32)
        rz_m = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)
        rot_mat = rz_m @ rx_m @ ry_m

        pts, quads, shade, r_mid = _compute_enneper_shell(
            R_GRID,
            V_GRID,
            order_k=order_k,
            r_max=r_max,
            bonnet_angle=b_ang,
            twist_amp=act3_twist,
            scale=scale,
            offset_xyz=offset_xyz,
            rot_mat=rot_mat,
        )

        # Render opaque (alpha=255) smooth-shaded mineral surface quads so hardware Z-buffer resolves cleanly
        py5.no_stroke()
        c_in = PALETTE_RGB[role_in]
        c_mid = PALETTE_RGB[role_mid]
        c_out = PALETTE_RGB[role_out]

        for z_idx in range(4):
            w_in, w_mid, w_out = r_zone_mix[z_idx]
            base_col = w_in * c_in + w_mid * c_mid + w_out * c_out
            z_mask = (r_mid >= r_zone_edges[z_idx]) & (r_mid < r_zone_edges[z_idx + 1])
            for s_idx in range(n_shade_bins):
                mask = z_mask & (shade >= shade_edges[s_idx]) & (shade < shade_edges[s_idx + 1])
                idx = np.flatnonzero(mask)
                if len(idx) > 0:
                    sv = float(shade_centers[s_idx])
                    rgb = base_col * sv + alabaster_tint * max(0.0, sv - 0.58) * 0.42
                    r_c = int(min(255, rgb[0] * 255.0))
                    g_c = int(min(255, rgb[1] * 255.0))
                    b_c = int(min(255, rgb[2] * 255.0))
                    py5.fill(r_c, g_c, b_c, 255)
                    with py5.begin_shape(py5.QUADS):
                        py5.vertices(quads[idx].reshape(-1, 3))

        # Crisp iron-gall ink geodesic rib lines along constant-r rings and outer petal boundary
        py5.no_fill()
        py5.stroke(34, 46, 54, 195)
        py5.stroke_weight(1.6)
        ring_indices = list(range(0, NR, 4)) + [NR - 1]
        ring_segs = np.empty((len(ring_indices), NV - 1, 2, 3), dtype=np.float32)
        for i_r, r_idx in enumerate(ring_indices):
            ring_segs[i_r, :, 0, :] = pts[r_idx, :-1, :]
            ring_segs[i_r, :, 1, :] = pts[r_idx, 1:, :]
        with py5.begin_shape(py5.LINES):
            py5.vertices(ring_segs.reshape(-1, 3))

        # Constant-v radial rulings (every 4th ray)
        ray_indices = list(range(0, NV, 4))
        ray_segs = np.empty((len(ray_indices), NR - 1, 2, 3), dtype=np.float32)
        for i_v, v_idx in enumerate(ray_indices):
            ray_segs[i_v, :, 0, :] = pts[:-1, v_idx, :]
            ray_segs[i_v, :, 1, :] = pts[1:, v_idx, :]
        py5.stroke(34, 46, 54, 130)
        py5.stroke_weight(1.15)
        with py5.begin_shape(py5.LINES):
            py5.vertices(ray_segs.reshape(-1, 3))

    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.camera()
    py5.perspective()

    # Apply PostFX finishing pass
    fx.apply()

    # Save frame, verify non-blank, and compile MP4 on final frame
    step_animation_frame(
        SKETCH_DIR,
        FRAMES_DIR,
        fps=FPS,
        total_frames=TOTAL_FRAMES,
        preview_name=PREVIEW_FILENAME,
    )


py5.run_sketch()
