"""hypostyle_voussoir_colonnade — 3D Hypostyle Voussoir Colonnade & Risograph Spot Inks (P3D).

A true P3D volumetric architectural colonnade of 24 depth-stacked scalloped
voussoir vaults and corbeled arch ribs suspended over a full-canvas warm cream
Risograph paper ground (#efe9dc). As a perspective camera glides and orbits
through the hypostyle depth bays, 3-channel translucent spot-ink architecture in
fluorescent coral (#f05240), peacock teal (#12948a), and deep federal indigo
(#1a285c) shifts through Act I (Assembly), Act II (Harmonic Torsion), and
Act III (Vault Lock).

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

DURATION_SEC = 22
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS  # 1320 frames (22s @ 60fps)
PREVIEW_FILENAME = preview_filename(work_name=WORK_NAME)
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Keep tonemap low (0.20) so the warm cream Risograph paper ground stays bright
fx = PostFX(
    bloom=0.14,
    bloom_threshold=0.82,
    aberration=0.0010,
    tonemap=0.20,
    vignette=0.08,
    grain=0.018,
)

N_BAYS = 22
N_VOUSSOIRS = 28  # Voussoir wedge blocks per arch ring
N_AISLES = 3      # 3 parallel hypostyle nave/aisle spans

# Risograph Spot-Ink + Paper Palette in [0, 1]
PAPER_RGB = np.array([0.937, 0.914, 0.863], dtype=np.float32)  # #efe9dc
SPOT_INKS = np.array(
    [
        [0.941, 0.322, 0.251],  # 0: Fluorescent Coral (#f05240)
        [0.071, 0.580, 0.541],  # 1: Peacock Teal (#12948a)
        [0.102, 0.157, 0.361],  # 2: Deep Federal Indigo (#1a285c)
        [0.345, 0.243, 0.420],  # 3: Overprint Plum (Coral x Indigo mix)
    ],
    dtype=np.float32,
)

BAY_Z0: np.ndarray
VOUS_ROLE: np.ndarray
VOUS_PHASE: np.ndarray

# Unit hexahedron 6 faces (6, 4, 3) for 3D voussoir wedges
HEX_FACES = np.array(
    [
        [[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]],  # +Z front
        [[1, 0, 0], [0, 0, 0], [0, 1, 0], [1, 1, 0]],  # -Z back
        [[0, 1, 1], [1, 1, 1], [1, 1, 0], [0, 1, 0]],  # outer extrados
        [[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]],  # inner intrados
        [[1, 0, 1], [1, 0, 0], [1, 1, 0], [1, 1, 1]],  # +angle joint
        [[0, 0, 0], [0, 0, 1], [0, 1, 1], [0, 1, 0]],  # -angle joint
    ],
    dtype=np.float32,
)
FACE_LIT = np.array([0.96, 0.72, 1.04, 0.58, 0.84, 0.78], dtype=np.float32)


def _init_colonnade() -> None:
    global BAY_Z0, VOUS_ROLE, VOUS_PHASE
    rng = np.random.default_rng()

    BAY_Z0 = np.linspace(-2200.0, 2200.0, N_BAYS, dtype=np.float32)
    VOUS_ROLE = np.zeros((N_BAYS, N_AISLES, N_VOUSSOIRS), dtype=np.int32)
    for b in range(N_BAYS):
        for a in range(N_AISLES):
            for v in range(N_VOUSSOIRS):
                # Alternate Risograph spot inks across voussoir wedges & bays
                if (v + b) % 4 == 0:
                    VOUS_ROLE[b, a, v] = 0  # Coral
                elif (v + b) % 4 == 1:
                    VOUS_ROLE[b, a, v] = 1  # Teal
                elif (v + b) % 4 == 2:
                    VOUS_ROLE[b, a, v] = 2  # Indigo
                else:
                    VOUS_ROLE[b, a, v] = 3  # Overprint Plum

    VOUS_PHASE = rng.uniform(0.0, math.tau, size=(N_BAYS, N_AISLES, N_VOUSSOIRS)).astype(
        np.float32
    )


def _build_colonnade_geometry(
    u_loop: float, z_travel: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build 3D voussoir wedge hexahedra and structural tie-rod lines."""
    theta = u_loop * math.tau

    # Multi-act temporal envelope:
    # Act I: Radial expansion of voussoirs | Act II: Polyrhythmic torsion wave | Act III: Vault lock
    act_explode = 0.22 * (0.5 - 0.5 * math.cos(theta)) + 0.14 * math.sin(theta * 2.0) ** 2
    torsion_wave = 0.24 * math.sin(theta)

    # Seamless Z-bay wrap in [-2200, 2200] (period = 4400)
    z_bays = np.mod(BAY_Z0 + z_travel + 2200.0, 4400.0) - 2200.0  # (N_BAYS,)

    # 3 aisle X-centers: left aisle (-820), central nave (0), right aisle (+820)
    aisle_x = np.array([-820.0, 0.0, 820.0], dtype=np.float32)
    aisle_r = np.array([360.0, 510.0, 360.0], dtype=np.float32)

    # Voussoir angular intervals along arch ring from -0.08*pi to 1.08*pi
    ang_edges = np.linspace(-0.08 * math.pi, 1.08 * math.pi, N_VOUSSOIRS + 1, dtype=np.float32)
    # Leave crisp mortar gap between adjacent voussoir stones
    ang0 = ang_edges[:-1] + 0.011
    ang1 = ang_edges[1:] - 0.011
    ang_mid = 0.5 * (ang0 + ang1)

    # Broadcast grids to (N_BAYS, N_AISLES, N_VOUSSOIRS)
    B_Z = z_bays[:, None, None]
    A_X = aisle_x[None, :, None]
    A_R = aisle_r[None, :, None]
    V_A0 = ang0[None, None, :]
    V_A1 = ang1[None, None, :]
    V_AM = ang_mid[None, None, :]

    # Bay-dependent harmonic twist & radial breathing
    bay_phase = (B_Z / 2200.0) * math.pi
    twist = torsion_wave * 0.45 * np.sin(bay_phase + theta)
    a0 = V_A0 + twist
    a1 = V_A1 + twist
    am = V_AM + twist

    # Scalloped muqarnas/voussoir radial modulation + multi-act explosion offset
    scallop = 1.0 + 0.09 * np.cos(V_AM * 6.0 - theta * 2.0)
    explode_r = A_R * act_explode * (0.35 + 0.65 * np.sin(VOUS_PHASE + theta * 2.0) ** 2)
    r_inner = A_R * scallop + explode_r * 0.42
    r_outer = r_inner + 68.0 + 34.0 * (np.arange(N_VOUSSOIRS)[None, None, :] % 2)

    # Z thickness of each arch ring + alternating keystone step
    z_half = 36.0
    z_shift = 20.0 * np.sin(V_AM * 3.0 + bay_phase + theta)
    z0 = B_Z - z_half + z_shift
    z1 = B_Z + z_half + z_shift

    # Compute the 8 corners of each voussoir wedge in 3D space
    # Parameterize by u in {a0, a1}, v in {r_inner, r_outer}, w in {z0, z1}
    cos0, sin0 = np.cos(a0), np.sin(a0)
    cos1, sin1 = np.cos(a1), np.sin(a1)

    # In P3D, Y points downward, so arch rises toward negative Y: y = y_base - r * sin(a)
    y_base = 340.0 + 38.0 * np.cos(bay_phase - theta)

    # Build 6 faces per voussoir: shape (N_BAYS, N_AISLES, N_VOUSSOIRS, 6, 4, 3)
    grid_shape = (N_BAYS, N_AISLES, N_VOUSSOIRS)
    M = N_BAYS * N_AISLES * N_VOUSSOIRS
    c0 = np.broadcast_to(cos0, grid_shape).reshape(M)
    s0 = np.broadcast_to(sin0, grid_shape).reshape(M)
    c1_v = np.broadcast_to(cos1, grid_shape).reshape(M)
    s1_v = np.broadcast_to(sin1, grid_shape).reshape(M)
    ri = np.broadcast_to(r_inner, grid_shape).reshape(M)
    ro = np.broadcast_to(r_outer, grid_shape).reshape(M)
    za = np.broadcast_to(z0, grid_shape).reshape(M)
    zb = np.broadcast_to(z1, grid_shape).reshape(M)
    xc = np.broadcast_to(A_X, grid_shape).reshape(M)
    yb = np.broadcast_to(y_base, grid_shape).reshape(M)
    am_flat = np.broadcast_to(am, grid_shape).reshape(M)

    # 8 vertices of wedge: (u_idx, v_idx, w_idx) in {0,1}^3
    c_u = np.stack([c0, c1_v], axis=1)  # (M, 2)
    s_u = np.stack([s0, s1_v], axis=1)  # (M, 2)
    r_v = np.stack([ri, ro], axis=1)    # (M, 2)
    z_w = np.stack([za, zb], axis=1)    # (M, 2)

    # Evaluate all 6 faces (M, 6, 4, 3)
    u_i = HEX_FACES[:, :, 0].astype(np.int32)  # (6, 4)
    v_i = HEX_FACES[:, :, 1].astype(np.int32)
    w_i = HEX_FACES[:, :, 2].astype(np.int32)

    cu_f = c_u[:, u_i]  # (M, 6, 4)
    su_f = s_u[:, u_i]
    rv_f = r_v[:, v_i]
    zw_f = z_w[:, w_i]

    px = xc[:, None, None] + rv_f * cu_f
    py = yb[:, None, None] - rv_f * su_f
    pz = zw_f

    quads = np.stack([px, py, pz], axis=-1).astype(np.float32)  # (M, 6, 4, 3)

    # Depth fog toward warm cream Risograph paper ground
    z_mid = 0.5 * (za + zb)
    depth_fog = np.clip((2350.0 - z_mid) / 4500.0, 0.0, 0.72)  # 0 at front, 0.72 at far horizon

    # Structural tie-rod segments connecting arch intrados across bays
    xm = xc + ri * np.cos(am_flat)
    ym = yb - ri * np.sin(am_flat)
    zm = z_mid
    intrados_pts = np.stack([xm, ym, zm], axis=-1).reshape(N_BAYS, N_AISLES, N_VOUSSOIRS, 3)

    return quads, VOUS_ROLE.reshape(M), depth_fog, intrados_pts


def setup() -> None:
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    fx.setup()
    _init_colonnade()


def draw() -> None:
    frame_idx = py5.frame_count - 1
    u_loop = (frame_idx % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    theta = u_loop * math.tau

    # Warm cream Risograph paper ground (#efe9dc) across 100% of the canvas
    py5.background(239, 233, 220)
    py5.hint(py5.ENABLE_DEPTH_TEST)

    fov = math.radians(62.0)
    aspect = float(SIZE[0]) / float(SIZE[1])
    py5.perspective(fov, aspect, 60.0, 9500.0)

    # Smooth spatial camera depth traversal + gentle lateral sway inside the central nave
    cam_x = 135.0 * math.sin(theta) + 45.0 * math.cos(theta * 2.0)
    cam_y = 95.0 + 55.0 * math.cos(theta)
    cam_z = 1520.0 + 120.0 * math.sin(theta)
    look_x = -110.0 * math.sin(theta)
    look_y = -65.0 + 35.0 * math.sin(theta * 2.0)
    look_z = -750.0
    py5.camera(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0.0, 1.0, 0.0)

    # 1 full colonnade period = 4400 units over the 22-second loop
    z_travel = u_loop * 4400.0
    quads, roles, depth_fog, intrados_pts = _build_colonnade_geometry(u_loop, z_travel)

    # Cull bays that are too close to or behind the camera lens so no stone block occludes the frame
    z_centers = intrados_pts[:, :, :, 2].reshape(-1)
    near_valid = z_centers < (cam_z - 260.0)

    # Bin by 4 depth-fog zones so distant vaults melt softly into the warm cream paper ground
    py5.no_stroke()
    fog_edges = (0.0, 0.18, 0.36, 0.54, 0.80)
    fog_centers = (0.06, 0.24, 0.42, 0.62)

    for role_id in range(len(SPOT_INKS)):
        ink_rgb = SPOT_INKS[role_id]
        r_mask = (roles == role_id) & near_valid
        for z_idx in range(4):
            f_mask = r_mask & (depth_fog >= fog_edges[z_idx]) & (depth_fog < fog_edges[z_idx + 1])
            idx = np.flatnonzero(f_mask)
            if len(idx) == 0:
                continue
            fog_v = fog_centers[z_idx]
            for f_face in range(6):
                lit = float(FACE_LIT[f_face])
                # Blend shaded spot ink with warm paper highlight & atmospheric depth fog
                shaded_ink = np.clip(ink_rgb * lit + PAPER_RGB * max(0.0, lit - 0.84) * 0.38, 0.0, 1.0)
                final_rgb = shaded_ink * (1.0 - fog_v) + PAPER_RGB * fog_v
                rc = int(min(255, final_rgb[0] * 255.0))
                gc = int(min(255, final_rgb[1] * 255.0))
                bc = int(min(255, final_rgb[2] * 255.0))
                py5.fill(rc, gc, bc, 255)
                face_verts = quads[idx, f_face, :, :].reshape(-1, 3)
                with py5.begin_shape(py5.QUADS):
                    py5.vertices(face_verts)

    # Filter intrados rings to visible bays in front of camera
    bay_valid = intrados_pts[:, 1, N_VOUSSOIRS // 2, 2] < (cam_z - 260.0)
    vis_pts = intrados_pts[bay_valid]

    # Crisp federal-indigo & coral Risograph registration lines along arch intrados rings
    py5.no_fill()
    py5.stroke(26, 40, 92, 210)
    py5.stroke_weight(1.8)
    n_vis = len(vis_pts)
    ring_segs = np.empty((n_vis, N_AISLES, N_VOUSSOIRS - 1, 2, 3), dtype=np.float32)
    ring_segs[:, :, :, 0, :] = vis_pts[:, :, :-1, :]
    ring_segs[:, :, :, 1, :] = vis_pts[:, :, 1:, :]
    with py5.begin_shape(py5.LINES):
        py5.vertices(ring_segs.reshape(-1, 3))

    # Transverse tie-beams connecting left aisle, central nave, and right aisle
    py5.stroke(18, 148, 138, 175)
    py5.stroke_weight(1.5)
    tie_segs = np.empty((n_vis, N_AISLES - 1, N_VOUSSOIRS // 2, 2, 3), dtype=np.float32)
    tie_segs[:, :, :, 0, :] = vis_pts[:, :-1, ::2, :]
    tie_segs[:, :, :, 1, :] = vis_pts[:, 1:, ::2, :]
    with py5.begin_shape(py5.LINES):
        py5.vertices(tie_segs.reshape(-1, 3))

    # Misregistered coral echo wire (classic Risograph drum registration offset)
    py5.stroke(240, 82, 64, 155)
    py5.stroke_weight(1.4)
    coral_segs = ring_segs.copy()
    coral_segs[..., 0] += 9.5
    coral_segs[..., 1] -= 6.5
    with py5.begin_shape(py5.LINES):
        py5.vertices(coral_segs.reshape(-1, 3))

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
