"""brutalist_cantilever_polyhedra — 3D Constructivist Cantilevered Trusses & Phase Interference

A true P3D sculptural architecture of interlocking cantilevered concrete-bone slabs,
signal-vermilion tension beams, ultramarine structural fins, and cadmium-ochre
counterweight blocks suspended in stark carbon-black space. Driven by three
incommensurable poly-rhythmic harmonic waves, the monumental brutalist assembly
shears, telescopes, and re-aligns under directional architectural lighting.

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

DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1080 frames
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

fx = PostFX(
    bloom=0.24,
    bloom_threshold=0.72,
    tonemap=0.95,
    vignette=0.16,
    grain=0.018,
)

# Unit cube 6 faces (each 4 vertices in counter-clockwise order) + face normals
CUBE_FACE_VERTS = np.array(
    [
        # +Z front
        [[-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]],
        # -Z back
        [[0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5]],
        # +X right
        [[0.5, -0.5, 0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [0.5, 0.5, 0.5]],
        # -X left
        [[-0.5, -0.5, -0.5], [-0.5, -0.5, 0.5], [-0.5, 0.5, 0.5], [-0.5, 0.5, -0.5]],
        # +Y bottom
        [[-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5]],
        # -Y top
        [[-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5]],
    ],
    dtype=np.float32,
)

CUBE_FACE_NORMS = np.array(
    [
        [0.0, 0.0, 1.0],
        [0.0, 0.0, -1.0],
        [1.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, -1.0, 0.0],
    ],
    dtype=np.float32,
)

# Stark Constructivist High-Contrast Palette (Base RGB in [0, 1])
PALETTE_BASE = np.array(
    [
        [0.949, 0.937, 0.914],  # 0: Bone White Concrete (#f2efe9)
        [0.910, 0.204, 0.141],  # 1: Signal Vermilion (#e83424)
        [0.110, 0.239, 0.831],  # 2: International Ultramarine (#1c3dd4)
        [0.949, 0.690, 0.094],  # 3: Cadmium Ochre (#f2b018)
        [0.200, 0.220, 0.255],  # 4: Dark Graphite Structural Steel (#333841)
    ],
    dtype=np.float32,
)

NUM_BEAMS = 180
BEAM_BASE_POS: np.ndarray
BEAM_BASE_DIM: np.ndarray
BEAM_AXIS_DIR: np.ndarray
BEAM_FREQ: np.ndarray
BEAM_PHASE: np.ndarray
BEAM_ROLE: np.ndarray
BEAM_TIER: np.ndarray


def _init_cantilever_assembly() -> None:
    global BEAM_BASE_POS, BEAM_BASE_DIM, BEAM_AXIS_DIR, BEAM_FREQ, BEAM_PHASE, BEAM_ROLE, BEAM_TIER
    rng = np.random.default_rng()

    pos_list = []
    dim_list = []
    dir_list = []
    role_list = []
    tier_list = []

    # 3 orthogonal constructivist families:
    # Family A (76 beams): Long horizontal X-cantilever slabs and tension rails
    # Family B (56 beams): Vertical/diagonal Y-pilasters and sheer towers
    # Family C (48 beams): Deep Z-cantilever outriggers projecting toward/away from camera
    counts = (76, 56, 48)
    for fam_id, count in enumerate(counts):
        for i in range(count):
            u = (i / max(1, count - 1)) * 2.0 - 1.0
            tier = i % 5
            if fam_id == 0:
                # X-dominant cantilevers
                bx = u * 480.0 + rng.uniform(-140.0, 140.0)
                by = (tier - 2) * 185.0 + rng.uniform(-65.0, 65.0)
                bz = rng.uniform(-520.0, 420.0)
                dx = rng.uniform(320.0, 920.0)
                dy = rng.uniform(18.0, 58.0)
                dz = rng.uniform(36.0, 130.0)
                adir = [1.0, 0.0, 0.0]
                role = 0 if i % 3 == 0 else (1 if i % 4 == 1 else (4 if i % 4 == 2 else 3))
            elif fam_id == 1:
                # Y-dominant vertical constructivist towers & fins
                bx = (tier - 2) * 310.0 + rng.uniform(-110.0, 110.0)
                by = u * 360.0 + rng.uniform(-90.0, 90.0)
                bz = rng.uniform(-480.0, 380.0)
                dx = rng.uniform(24.0, 76.0)
                dy = rng.uniform(260.0, 740.0)
                dz = rng.uniform(32.0, 110.0)
                adir = [0.0, 1.0, 0.0]
                role = 2 if i % 3 == 0 else (0 if i % 3 == 1 else 4)
            else:
                # Z-dominant depth outriggers & counterweights
                bx = u * 640.0 + rng.uniform(-90.0, 90.0)
                by = ((i % 4) - 1.5) * 210.0 + rng.uniform(-50.0, 50.0)
                bz = rng.uniform(-560.0, 440.0)
                dx = rng.uniform(32.0, 95.0)
                dy = rng.uniform(28.0, 82.0)
                dz = rng.uniform(280.0, 780.0)
                adir = [0.0, 0.0, 1.0]
                role = 1 if i % 4 == 0 else (3 if i % 4 == 1 else (2 if i % 4 == 2 else 0))

            pos_list.append([bx, by, bz])
            dim_list.append([dx, dy, dz])
            dir_list.append(adir)
            role_list.append(role)
            tier_list.append(tier)

    BEAM_BASE_POS = np.array(pos_list, dtype=np.float32)
    BEAM_BASE_DIM = np.array(dim_list, dtype=np.float32)
    BEAM_AXIS_DIR = np.array(dir_list, dtype=np.float32)
    BEAM_ROLE = np.array(role_list, dtype=np.int32)
    BEAM_TIER = np.array(tier_list, dtype=np.int32)

    # Golden-ratio poly-rhythmic frequencies per beam
    BEAM_FREQ = rng.choice([1.0, 1.618034, 2.618034], size=(NUM_BEAMS, 3)).astype(np.float32)
    BEAM_PHASE = rng.uniform(0.0, math.tau, size=(NUM_BEAMS, 3)).astype(np.float32)


def setup() -> None:
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    fx.setup()
    _init_cantilever_assembly()


def draw() -> None:
    t_norm = (py5.frame_count - 1) / float(TOTAL_FRAMES)
    tau = math.tau
    w, h = float(SIZE[0]), float(SIZE[1])

    # Stark carbon-black constructivist ground (#0f1115)
    py5.background(15, 17, 21)
    py5.hint(py5.ENABLE_DEPTH_TEST)

    # Perspective camera with subtle architectural tilt and orbital sway
    fov = math.pi / 3.4
    camera_z = (h / 2.0) / math.tan(fov / 2.0)
    py5.perspective(fov, w / h, camera_z / 12.0, camera_z * 12.0)

    cam_x = 340.0 * math.sin(t_norm * tau)
    cam_y = -210.0 + 140.0 * math.cos(t_norm * tau)
    cam_z = 1380.0 + 180.0 * math.sin(t_norm * tau * 2.0)
    py5.camera(cam_x, cam_y, cam_z, 0.0, 0.0, -60.0, 0.14, 1.0, 0.0)

    # Whole-sculpture constructivist rotation in 3D space
    rot_y = -0.46 + 0.34 * math.sin(t_norm * tau)
    rot_x = 0.24 + 0.14 * math.cos(t_norm * tau)
    rot_z = -0.18 + 0.08 * math.sin(t_norm * tau * 2.0)

    cy, sy = math.cos(rot_y), math.sin(rot_y)
    cx, sx = math.cos(rot_x), math.sin(rot_x)
    cz, sz = math.cos(rot_z), math.sin(rot_z)

    # Combined 3x3 rotation matrix R = Rz * Rx * Ry
    ry_mat = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float32)
    rx_mat = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]], dtype=np.float32)
    rz_mat = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)
    rot_mat = rz_mat @ rx_mat @ ry_mat

    # Poly-Rhythmic Phase Interference displacement along each beam's primary cantilever axis
    phase_arg = t_norm * tau * BEAM_FREQ + BEAM_PHASE
    wave1 = np.sin(phase_arg[:, 0] + BEAM_BASE_POS[:, 1] * 0.0045)
    wave2 = np.cos(phase_arg[:, 1] + BEAM_BASE_POS[:, 0] * 0.0035)
    wave3 = np.sin(phase_arg[:, 2] + BEAM_BASE_POS[:, 2] * 0.0040)

    interference = (0.52 * wave1 + 0.31 * wave2 + 0.17 * wave3)[:, None]
    slide_amp = 210.0
    pos = BEAM_BASE_POS + BEAM_AXIS_DIR * (interference * slide_amp)

    # Breathing elongation along primary axis
    scale_mod = 1.0 + 0.24 * BEAM_AXIS_DIR * np.sin(phase_arg[:, 0:1] * 1.0)
    dims = BEAM_BASE_DIM * scale_mod

    # Transform all 180*6 = 1080 quad faces into world space in one vectorized tensor op
    # CUBE_FACE_VERTS: (6, 4, 3), dims: (B, 3), pos: (B, 3) -> world_verts: (B, 6, 4, 3)
    local_verts = CUBE_FACE_VERTS[None, :, :, :] * dims[:, None, None, :] + pos[:, None, None, :]
    world_verts = local_verts @ rot_mat.T  # (B, 6, 4, 3)
    world_norms = CUBE_FACE_NORMS @ rot_mat.T  # (6, 3)

    # Two directional architectural lights + ambient rim light
    l1 = np.array([0.52, -0.68, 0.51], dtype=np.float32)
    l2 = np.array([-0.64, 0.42, 0.64], dtype=np.float32)

    ndotl1 = np.maximum(0.0, world_norms @ l1)  # (6,)
    ndotl2 = np.maximum(0.0, world_norms @ l2)  # (6,)
    face_shade = 0.28 + 0.62 * ndotl1 + 0.22 * ndotl2  # (6,)

    # Broadcast shade across beams and quantize into 18 color/luminance buckets for fast single-pass QUADS rendering
    beam_pulse = 0.92 + 0.08 * wave1  # (B,)
    total_shade = np.clip(beam_pulse[:, None] * face_shade[None, :], 0.18, 1.15)  # (B, 6)

    # Flatten (B, 6) -> F = 1080 faces
    flat_verts = world_verts.reshape(-1, 4, 3)
    flat_roles = np.repeat(BEAM_ROLE, 6)
    flat_shade = total_shade.reshape(-1)

    py5.no_stroke()
    shade_bins = (0.32, 0.52, 0.76, 1.02)
    bin_edges = (0.0, 0.42, 0.64, 0.88, 2.0)

    for role_id in range(len(PALETTE_BASE)):
        base_rgb = PALETTE_BASE[role_id]
        role_mask = flat_roles == role_id
        for b_idx in range(4):
            mask = role_mask & (flat_shade >= bin_edges[b_idx]) & (flat_shade < bin_edges[b_idx + 1])
            face_indices = np.flatnonzero(mask)
            if len(face_indices) > 0:
                s_val = shade_bins[b_idx]
                r = int(min(255, base_rgb[0] * s_val * 255.0))
                g = int(min(255, base_rgb[1] * s_val * 255.0))
                b = int(min(255, base_rgb[2] * s_val * 255.0))
                py5.fill(r, g, b, 255)
                with py5.begin_shape(py5.QUADS):
                    py5.vertices(flat_verts[face_indices].reshape(-1, 3))

    # Crisp constructivist architectural edge wireframes on signal-vermilion & bone-white front cantilevers
    py5.stroke(242, 239, 233, 95)
    py5.stroke_weight(1.4)
    py5.no_fill()
    accent_faces = np.flatnonzero((flat_roles <= 1) & (flat_shade > 0.78))
    if len(accent_faces) > 0:
        with py5.begin_shape(py5.QUADS):
            py5.vertices(flat_verts[accent_faces].reshape(-1, 3))

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

