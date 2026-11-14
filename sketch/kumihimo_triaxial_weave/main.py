"""kumihimo_triaxial_weave — 3D Triaxial Kumihimo Silk & Bamboo Plaiting Lattice (P3D).

A volumetric P3D sculptural suspension of 54 interwoven triaxial ribbons
arranged along three 60-degree symmetry axes (0 deg, +60 deg, -60 deg) over a
deep obsidian lacquer ground (#0d1016). Driven by poly-rhythmic phase
interference (1:2:3 harmonic wave ratios), the three ribbon families undulate
in 3D space with true over-under interlacing depth offsets, casting crisp
directional facet shading in raw bone ivory (#f4efe4), vermilion lacquer
(#e63826), imperial gold (#f2b01e), and cobalt ultramarine (#1e46c8).

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
    bloom=0.22,
    bloom_threshold=0.72,
    aberration=0.0011,
    tonemap=0.28,
    vignette=0.14,
    grain=0.016,
)

# ── Triaxial Weave Geometry Constants ──────────────────────────────────
N_AXES = 3             # 0 deg, +60 deg, -60 deg
STRANDS_PER_AXIS = 19  # 57 total 3D volumetric ribbons across 2 canopy layers
N_LAYERS = 2           # Upper main triaxial lattice + lower shadow counter-lattice
N_SEGS = 96            # Longitudinal subdivisions per ribbon

PITCH = 148.0          # Spacing between parallel strands within an axis family
SPAN = 1880.0          # Half-length of each strand in 3D space

# Stark Constructivist / Lacquer Palette in [0, 1]
BG_RGB = np.array([0.051, 0.063, 0.086], dtype=np.float32)  # #0d1016
AXIS_PALETTE = np.array(
    [
        [0.957, 0.937, 0.894],  # Axis 0 (0 deg): Raw Bone Ivory (#f4efe4)
        [0.902, 0.220, 0.149],  # Axis 1 (+60 deg): Vermilion Lacquer (#e63826)
        [0.949, 0.690, 0.118],  # Axis 2 (-60 deg): Imperial Gold (#f2b01e)
        [0.145, 0.345, 0.820],  # Accent Strand: Ultramarine (#2558d1)
    ],
    dtype=np.float32,
)

S_LIN: np.ndarray
STRAND_OFFSET: np.ndarray


def _init_weave() -> None:
    global S_LIN, STRAND_OFFSET
    S_LIN = np.linspace(-SPAN, SPAN, N_SEGS + 1, dtype=np.float32)
    idx = np.arange(STRANDS_PER_AXIS, dtype=np.float32) - (STRANDS_PER_AXIS - 1) * 0.5
    STRAND_OFFSET = idx * PITCH


def _build_triaxial_ribbons(u_loop: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute 3D volumetric ribbon slabs (top, bottom, +side, -side faces) and node pins."""
    theta = u_loop * math.tau

    # 3 symmetry axes at 0, +60, -60 degrees in the (X, Z) sculptural plane
    angles = (0.0, math.pi / 3.0, -math.pi / 3.0)

    all_quads = []
    all_roles = []
    all_shades = []

    s_row = S_LIN[None, :]          # (1, N_SEGS+1)
    t_col = STRAND_OFFSET[:, None]  # (STRANDS_PER_AXIS, 1)

    for layer_id in range(N_LAYERS):
        y_layer_base = -95.0 if layer_id == 0 else 235.0
        layer_phase = 0.0 if layer_id == 0 else math.pi * 0.65
        rib_half_w = 22.0 if layer_id == 0 else 15.0
        rib_half_h = 9.5 if layer_id == 0 else 6.5

        for ax_id, ang in enumerate(angles):
            ca = math.cos(ang)
            sa = math.sin(ang)
            # Tangent u = (ca, sa), transverse normal v = (-sa, ca) in (X, Z)
            px = ca * s_row - sa * t_col
            pz = sa * s_row + ca * t_col

            # Poly-rhythmic phase interference across the 3 axes (1x, 2x, 3x temporal harmonics)
            k_wave = math.tau / (PITCH * 1.7320508)
            interlock_phase = s_row * k_wave + (t_col / PITCH) * (math.pi / 3.0) + ax_id * (math.tau / 3.0)

            # True over-under triaxial kumihimo interlock height + global poly-rhythmic dome wave
            over_under = 34.0 * np.sin(interlock_phase + theta * (ax_id + 1) + layer_phase)
            macro_dome = (
                95.0 * np.sin(px * 0.0016 + theta) * np.cos(pz * 0.0016 - theta * 2.0)
                + 58.0 * np.cos((px * 0.866 + pz * 0.5) * 0.0022 - theta * 3.0 + layer_phase)
            )
            py = y_layer_base + over_under + macro_dome

            # Twist angle along ribbon for dynamic specular catchlights
            twist = 0.34 * np.cos(interlock_phase * 0.5 - theta)
            ct = np.cos(twist)
            st = np.sin(twist)

            # Transverse vector W (width) and vertical vector H (thickness) in 3D
            wx = -sa * rib_half_w * ct
            wy = rib_half_w * st
            wz = ca * rib_half_w * ct

            hx = -sa * (-rib_half_h * st)
            hy = rib_half_h * ct
            hz = ca * (-rib_half_h * st)

            # 4 corners of ribbon cross-section at each station:
            # 0: (+w, -h) top-right, 1: (-w, -h) top-left, 2: (-w, +h) bot-left, 3: (+w, +h) bot-right
            c0x, c0y, c0z = px + wx - hx, py + wy - hy, pz + wz - hz
            c1x, c1y, c1z = px - wx - hx, py - wy - hy, pz - wz - hz
            c2x, c2y, c2z = px - wx + hx, py - wy + hy, pz - wz + hz
            c3x, c3y, c3z = px + wx + hx, py + wy + hy, pz + wz + hz

            # Build 3 visible faces per segment: Top face (0-1), Right side (3-0), Left side (1-2)
            # Shape per face: (STRANDS_PER_AXIS, N_SEGS, 4, 3)
            def _seg_quads(ax0, ay0, az0, bx0, by0, bz0):
                q = np.empty((STRANDS_PER_AXIS, N_SEGS, 4, 3), dtype=np.float32)
                q[:, :, 0, 0], q[:, :, 0, 1], q[:, :, 0, 2] = ax0[:, :-1], ay0[:, :-1], az0[:, :-1]
                q[:, :, 1, 0], q[:, :, 1, 1], q[:, :, 1, 2] = bx0[:, :-1], by0[:, :-1], bz0[:, :-1]
                q[:, :, 2, 0], q[:, :, 2, 1], q[:, :, 2, 2] = bx0[:, 1:], by0[:, 1:], bz0[:, 1:]
                q[:, :, 3, 0], q[:, :, 3, 1], q[:, :, 3, 2] = ax0[:, 1:], ay0[:, 1:], az0[:, 1:]
                return q

            q_top = _seg_quads(c0x, c0y, c0z, c1x, c1y, c1z)
            q_side_a = _seg_quads(c3x, c3y, c3z, c0x, c0y, c0z)
            q_side_b = _seg_quads(c1x, c1y, c1z, c2x, c2y, c2z)

            # Assign role: every 4th strand in Axis 0 or lower layer gets Ultramarine accent (#2558d1)
            strand_roles = np.full((STRANDS_PER_AXIS, N_SEGS), ax_id, dtype=np.int32)
            if layer_id == 1:
                strand_roles[::2, :] = 3
            else:
                strand_roles[2::5, :] = 3

            # Directional slope shading + depth fog toward obsidian background
            dy_ds = np.diff(py, axis=1) / (SPAN * 2.0 / N_SEGS)
            z_mid = 0.5 * (pz[:, :-1] + pz[:, 1:])
            fog = np.clip((1550.0 - z_mid) / 3400.0, 0.0, 0.72)
            layer_dim = 1.0 if layer_id == 0 else 0.62

            shade_top = np.clip((0.96 - 0.28 * dy_ds) * (1.0 - fog) * layer_dim, 0.18, 1.12)
            shade_side = np.clip(0.62 * (1.0 - fog) * layer_dim, 0.14, 0.85)

            for q_face, s_val in ((q_top, shade_top), (q_side_a, shade_side), (q_side_b, shade_side)):
                all_quads.append(q_face.reshape(-1, 4, 3))
                all_roles.append(strand_roles.reshape(-1))
                all_shades.append(s_val.reshape(-1))

    quads_arr = np.concatenate(all_quads, axis=0)
    roles_arr = np.concatenate(all_roles, axis=0)
    shades_arr = np.concatenate(all_shades, axis=0)

    # Vertical tension filaments connecting upper and lower triaxial lattices at hex vertices
    gx, gz = np.meshgrid(
        np.linspace(-1350.0, 1350.0, 14, dtype=np.float32),
        np.linspace(-1350.0, 1350.0, 14, dtype=np.float32),
    )
    gx_f = gx.reshape(-1)
    gz_f = gz.reshape(-1)
    dome_top = -95.0 + 95.0 * np.sin(gx_f * 0.0016 + theta) * np.cos(gz_f * 0.0016 - theta * 2.0)
    dome_bot = 235.0 + 95.0 * np.sin(gx_f * 0.0016 + theta) * np.cos(gz_f * 0.0016 - theta * 2.0)
    pins = np.empty((len(gx_f), 2, 3), dtype=np.float32)
    pins[:, 0, 0], pins[:, 0, 1], pins[:, 0, 2] = gx_f, dome_top, gz_f
    pins[:, 1, 0], pins[:, 1, 1], pins[:, 1, 2] = gx_f, dome_bot, gz_f

    return quads_arr, roles_arr, shades_arr, pins


def setup() -> None:
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    fx.setup()
    _init_weave()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    theta = u_loop * math.tau

    # Deep obsidian lacquer ground (#0d1016) across 100% of the canvas
    py5.background(13, 16, 22)
    py5.hint(py5.ENABLE_DEPTH_TEST)

    fov = math.radians(54.0)
    aspect = float(SIZE[0]) / float(SIZE[1])
    py5.perspective(fov, aspect, 40.0, 8500.0)

    # Elevated oblique P3D vantage orbiting smoothly above the dual triaxial canopies
    cam_x = 420.0 * math.sin(theta)
    cam_y = -680.0 + 110.0 * math.cos(theta)
    cam_z = 1320.0 + 180.0 * math.cos(theta)
    look_x = 85.0 * math.cos(theta)
    look_y = 35.0 + 30.0 * math.sin(theta * 2.0)
    look_z = -120.0
    py5.camera(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0.0, 1.0, 0.0)

    quads, roles, shades, pins = _build_triaxial_ribbons(u_loop)

    # Bin by 5 luminance/fog bands per color role for fast batched P3D rendering
    py5.no_stroke()
    shade_edges = (0.0, 0.34, 0.52, 0.70, 0.88, 1.25)
    shade_vals = (0.26, 0.43, 0.61, 0.79, 0.98)

    for role_id in range(len(AXIS_PALETTE)):
        base_rgb = AXIS_PALETTE[role_id]
        r_mask = roles == role_id
        for b_idx in range(5):
            s_mask = r_mask & (shades >= shade_edges[b_idx]) & (shades < shade_edges[b_idx + 1])
            idx = np.flatnonzero(s_mask)
            if len(idx) == 0:
                continue
            sv = shade_vals[b_idx]
            rgb = np.clip(base_rgb * sv + BG_RGB * max(0.0, 1.0 - sv) * 0.65, 0.0, 1.0)
            rc = int(min(255, rgb[0] * 255.0))
            gc = int(min(255, rgb[1] * 255.0))
            bc = int(min(255, rgb[2] * 255.0))
            py5.fill(rc, gc, bc, 255)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(quads[idx].reshape(-1, 3))

    # Crisp gold-leaf vertical tension filaments linking the upper and lower triaxial canopies
    py5.no_fill()
    py5.stroke(242, 176, 30, 145)
    py5.stroke_weight(1.4)
    with py5.begin_shape(py5.LINES):
        py5.vertices(pins.reshape(-1, 3))

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

