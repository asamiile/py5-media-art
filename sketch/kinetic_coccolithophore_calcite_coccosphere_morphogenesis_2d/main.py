"""
Kinetic Coccolithophore Calcite Coccosphere Morphogenesis 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Organic / Morphogenesis genre,
exploring marine phytoplankton biomineralization of Emiliania huxleyi
(Haptophyta, Coccolithales) executed on deep pelagic photic-abyssal slate (#050a14).

Coccolithophores are unicellular marine algae that construct intricate spherical
exoskeletons (coccospheres) from interlocking wheel-like calcium carbonate (CaCO3
calcite) scales called heterococcoliths. Each coccolith is synthesized internally
within a specialized Golgi-derived coccolith vesicle via a base organic scale
and proto-coccolith ring of alternating V-units and R-units, then extruded
(exocytosed) through the cell membrane to interlock into a multi-layered geodesic
armor shield.

This 4K 60fps simulation visualizes:
1. A 3D rotating coccosphere of 38 interlocking heterococcolith shields distributed
   via Fibonacci spherical phyllotaxis, rendered in strict Painter's back-to-front
   depth order so adjacent shields physically imbricate and overlap.
2. Each heterococcolith shield features a recessed proximal shield disc, a central
   slotted calcite grill, a proto-coccolith tube collar, and an elevated distal
   rosette of 26 T-shaped hammer-head calcite crystal rays (R-units).
3. Translucent intracellular view of the golden-amber haptophyte plastids, nucleus,
   and nascent intracellular coccolith vesicle undergoing rhythmic exocytosis,
   accompanied by two undulating flagella and a coiled haptonema filament.
4. Eight marine biomineralization & crystallography telemetry apparatuses across
   four balanced flank cards.
Completely free of human author signatures, seals (hanko), or watermarks.
"""

import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import py5

# --- Artwork Constants ---
WORK_NAME = "kinetic_coccolithophore_calcite_coccosphere_morphogenesis_2d"
WIDTH = 3840
HEIGHT = 2160
FPS = 60
TOTAL_FRAMES = 720
DURATION_SEC = 12.0

SKETCH_DIR = Path(__file__).resolve().parent
FRAMES_DIR = SKETCH_DIR / "frames"
PREVIEW_FILE = SKETCH_DIR / f"{WORK_NAME}_p1.png"
OUTPUT_MP4 = SKETCH_DIR / "output.mp4"

START_TIME = 0.0

# Non-fixed runtime phase variations
np.random.seed(int(time.time() * 1000) % 100000)
RND_ROT_OFFSET = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_BIO_OFFSET = float(np.random.uniform(0.0, 2.0 * math.pi))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 25.0
SPHERE_R = 545.0

# Generate 38 Fibonacci sphere points for imbricated heterococcolith centers
NUM_COCCOLITHS = 38
GOLDEN_ANGLE = math.pi * (3.0 - math.sqrt(5.0))
SHIELD_DIRS = []
SHIELD_TANGENTS = []

for i in range(NUM_COCCOLITHS):
    y = 1.0 - (i / float(NUM_COCCOLITHS - 1)) * 2.0
    r_xz = math.sqrt(max(0.0, 1.0 - y * y))
    theta = GOLDEN_ANGLE * i
    nx = math.cos(theta) * r_xz
    ny = y
    nz = math.sin(theta) * r_xz
    n_vec = np.array([nx, ny, nz], dtype=np.float64)
    up = np.array([0.0, 1.0, 0.0]) if abs(ny) < 0.9 else np.array([1.0, 0.0, 0.0])
    u_vec = np.cross(up, n_vec)
    u_vec /= np.linalg.norm(u_vec)
    v_vec = np.cross(n_vec, u_vec)
    SHIELD_DIRS.append(n_vec)
    SHIELD_TANGENTS.append((u_vec, v_vec))

SHIELD_DIRS = np.array(SHIELD_DIRS, dtype=np.float64)

# Precompute unit circle & spoke angles for each heterococcolith (26 spokes)
N_SPOKES = 26
SPOKE_ANGLES = np.linspace(0.0, 2.0 * math.pi, N_SPOKES, endpoint=False)
SPOKE_COS = np.cos(SPOKE_ANGLES)
SPOKE_SIN = np.sin(SPOKE_ANGLES)
SPOKE_COS_NEXT = np.cos(SPOKE_ANGLES + (2.0 * math.pi / N_SPOKES) * 0.72)
SPOKE_SIN_NEXT = np.sin(SPOKE_ANGLES + (2.0 * math.pi / N_SPOKES) * 0.72)
SPOKE_COS_PREV = np.cos(SPOKE_ANGLES - (2.0 * math.pi / N_SPOKES) * 0.28)
SPOKE_SIN_PREV = np.sin(SPOKE_ANGLES - (2.0 * math.pi / N_SPOKES) * 0.28)

# Palette for the 4 cross-polarized calcite birefringence orders:
# 0: Calcite Ice White-Cyan, 1: Polarized Turquoise-Cobalt, 2: Interference Rose-Amethyst, 3: Biomineral Gold-Amber
BIREF_PALETTES = [
    np.array([226.0, 244.0, 255.0]),
    np.array([56.0, 189.0, 248.0]),
    np.array([232.0, 121.0, 249.0]),
    np.array([251.0, 191.0, 36.0]),
]

# Marine snow / detached free coccolith platelets drifting in pelagic suspension
NUM_SNOW = 140
SNOW_X = np.random.uniform(90.0, WIDTH - 90.0, NUM_SNOW)
SNOW_Y = np.random.uniform(90.0, HEIGHT - 90.0, NUM_SNOW)
SNOW_R = np.random.uniform(3.0, 9.5, NUM_SNOW)
SNOW_PHASE = np.random.uniform(0.0, 2.0 * math.pi, NUM_SNOW)


def rotate_3d_points(pts, rx, ry, rz):
    """Applies 3-axis rotation to an (N, 3) array of 3D points."""
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    x1 = pts[:, 0] * cy + pts[:, 2] * sy
    y1 = pts[:, 1]
    z1 = -pts[:, 0] * sy + pts[:, 2] * cy

    x2 = x1
    y2 = y1 * cx - z1 * sx
    z2 = y1 * sx + z1 * cx

    x3 = x2 * cz - y2 * sz
    y3 = x2 * sz + y2 * cz
    z3 = z2

    return np.column_stack([x3, y3, z3])


def settings():
    py5.size(WIDTH, HEIGHT)
    py5.smooth(8)


def setup():
    global START_TIME
    START_TIME = time.time()
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")


def draw():
    frame = py5.frame_count - 1
    if frame >= TOTAL_FRAMES:
        finish_and_encode()
        return

    tau = frame / float(TOTAL_FRAMES)
    omega = 2.0 * math.pi

    ry = omega * tau + RND_ROT_OFFSET
    rx = 0.36 * math.sin(omega * tau) + 0.22
    rz = 0.18 * math.cos(omega * tau)

    # 1. Deep Pelagic Photic-Abyssal Slate Substrate (#050a14)
    py5.background(5, 10, 20)

    # 2. Cross-Polarized Microscope Illumination & Pelagic Caustic Glow
    py5.no_stroke()
    for r_g, col_g in [
        (1180, (12, 32, 58, 28)),
        (880, (16, 52, 86, 34)),
        (640, (24, 88, 128, 38)),
        (420, (180, 115, 28, 32)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    # Optical Microscope Polarizer Graticule Grid & Concentric Micrometer Rings
    py5.stroke(24, 46, 72, 110)
    py5.stroke_weight(1.4)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)

    py5.no_fill()
    py5.stroke(42, 82, 118, 120)
    py5.stroke_weight(1.8)
    for r_ring in [360, 620, 760, 860]:
        py5.circle(CX, CY, r_ring * 2.0)

    # Crossed Nicols Polarization Axes (P-P' and A-A' through CX, CY)
    py5.stroke(56, 189, 248, 85)
    py5.stroke_weight(1.6)
    py5.line(CX - 920, CY, CX + 920, CY)
    py5.line(CX, CY - 900, CX, CY + 900)

    # Ambient Drifting Detached Coccolith Platelets & Marine Snow
    for s_i in range(NUM_SNOW):
        sx = SNOW_X[s_i] + 18.0 * math.sin(omega * tau + SNOW_PHASE[s_i])
        sy = SNOW_Y[s_i] + 14.0 * math.cos(omega * tau + SNOW_PHASE[s_i] * 1.3)
        if math.hypot(sx - CX, sy - CY) > 680.0:
            sr = SNOW_R[s_i]
            py5.no_stroke()
            py5.fill(125, 211, 252, 75)
            py5.circle(sx, sy, sr * 2.0)
            py5.stroke(224, 242, 254, 110)
            py5.stroke_weight(1.2)
            py5.no_fill()
            py5.circle(sx, sy, sr * 3.2)

    # 3. Undulating Haptophyte Flagella (2 Smooth Flagella + 1 Coiled Haptonema)
    draw_haptophyte_flagella(tau)

    # 4. Compute Rotated 3D Coccosphere Shields & Depth-Sort Back-to-Front
    rot_dirs = rotate_3d_points(SHIELD_DIRS, rx, ry, rz)
    order = np.argsort(rot_dirs[:, 2])  # Strict Painter's back-to-front by Z

    back_indices = [idx for idx in order if rot_dirs[idx, 2] < 0.0]
    front_indices = [idx for idx in order if rot_dirs[idx, 2] >= 0.0]

    # 4A. Render Back Hemisphere Heterococcolith Shields
    render_coccolith_batch(back_indices, rot_dirs, rx, ry, rz, tau, is_front=False)

    # 4B. Render Intracellular Haptophyte Protoplast, Golden-Brown Chloroplasts & Golgi Vesicle
    draw_intracellular_core(tau)

    # 4C. Render Front Hemisphere Heterococcolith Shields in strict Painter's imbrication order
    render_coccolith_batch(front_indices, rot_dirs, rx, ry, rz, tau, is_front=True)

    # 5. Outer Polarized Micrometer Bezel Ring around the Coccosphere
    draw_polarizer_bezel_ring(tau)

    # 6. Four Quadrant Marine Biomineralization & Crystallography Apparatuses
    draw_biomineral_apparatuses(tau)

    # 7. Archival Museum Border & Scholarly Typography (Zero Personal Signatures/Seals)
    draw_archival_border_and_typography(tau)

    # Save frame
    frame_path = FRAMES_DIR / f"frame_{frame:04d}.png"
    py5.save_frame(str(frame_path))

    # Save preview image at frame 0
    if frame == 0:
        py5.save_frame(str(PREVIEW_FILE))
        print(f"[{WORK_NAME}] Saved preview image: {PREVIEW_FILE}")

    if (frame + 1) % 60 == 0 or frame + 1 == TOTAL_FRAMES:
        elapsed = time.time() - START_TIME
        fps_calc = (frame + 1) / max(0.1, elapsed)
        eta = (TOTAL_FRAMES - (frame + 1)) / max(0.01, fps_calc)
        print(f"[{WORK_NAME}] Frame {frame+1:03d}/{TOTAL_FRAMES} ({(frame+1)/TOTAL_FRAMES*100:.1f}%) | Speed: {fps_calc:.2f} fps | ETA: {eta:.1f}s")


def draw_haptophyte_flagella(tau):
    """Draws the two undulating swimming flagella and central coiled haptonema emerging from the apical pole."""
    omega = 2.0 * math.pi
    base_ang = -math.pi * 0.28 + 0.08 * math.sin(omega * tau)

    for f_sign, col_f in [(-1.0, (56, 189, 248)), (1.0, (52, 211, 153))]:
        py5.no_fill()
        py5.stroke(col_f[0], col_f[1], col_f[2], 95)
        py5.stroke_weight(7.0)
        pts = []
        for s_i in range(45):
            u = s_i / 44.0
            r_pos = SPHERE_R * 0.85 + u * 360.0
            ang = base_ang + f_sign * (0.14 + u * 0.28)
            wave = (18.0 + u * 36.0) * math.sin(u * 9.5 - 2.0 * omega * tau + f_sign * 0.8)
            tx = -math.sin(ang)
            ty = math.cos(ang)
            px = CX + math.cos(ang) * r_pos + tx * wave
            py = CY + math.sin(ang) * r_pos + ty * wave
            pts.append((px, py))
        with py5.begin_shape():
            for px, py in pts:
                py5.vertex(px, py)
        py5.end_shape()
        py5.stroke(224, 242, 254, 195)
        py5.stroke_weight(2.2)
        with py5.begin_shape():
            for px, py in pts:
                py5.vertex(px, py)
        py5.end_shape()

    py5.no_fill()
    py5.stroke(251, 191, 36, 210)
    py5.stroke_weight(2.8)
    with py5.begin_shape():
        for h_i in range(55):
            u = h_i / 54.0
            r_pos = SPHERE_R * 0.85 + u * 230.0
            coil_r = 16.0 * (1.0 - 0.3 * u)
            coil_a = u * 10.0 * math.pi - 2.0 * omega * tau
            px = CX + math.cos(base_ang) * r_pos + math.cos(coil_a) * coil_r
            py = CY + math.sin(base_ang) * r_pos + math.sin(coil_a) * coil_r
            py5.vertex(px, py)
    py5.end_shape()


def draw_intracellular_core(tau):
    """Draws the golden-amber haptophyte chloroplast lobes and nascent Golgi coccolith vesicle."""
    omega = 2.0 * math.pi
    pulse = 1.0 + 0.04 * math.sin(2.0 * omega * tau)
    core_r = SPHERE_R * 0.72 * pulse

    py5.no_stroke()
    for mult, col in [
        (1.18, (14, 116, 144, 55)),
        (1.04, (16, 185, 129, 65)),
        (0.90, (217, 119, 6, 85)),
        (0.72, (245, 158, 11, 115)),
        (0.48, (254, 240, 138, 135)),
    ]:
        py5.fill(*col)
        py5.circle(CX, CY, core_r * 2.0 * mult)

    for lobe_sign in (-1.0, 1.0):
        lobe_ang = omega * tau * 0.5 + (0.0 if lobe_sign > 0 else math.pi)
        lx = CX + math.cos(lobe_ang) * (core_r * 0.36)
        ly = CY + math.sin(lobe_ang) * (core_r * 0.36)
        py5.stroke(253, 224, 71, 165)
        py5.stroke_weight(2.2)
        py5.fill(180, 83, 9, 145)
        py5.circle(lx, ly, core_r * 0.82)
        py5.stroke(254, 240, 138, 120)
        py5.stroke_weight(1.5)
        for k_lam in range(-3, 4):
            off = k_lam * 22.0
            py5.line(lx - 65, ly + off, lx + 65, ly + off)

    exocytose_r = core_r * 0.55 * (0.5 + 0.5 * math.sin(omega * tau))
    vx = CX + math.cos(-omega * tau) * exocytose_r
    vy = CY + math.sin(-omega * tau) * exocytose_r
    vr = 78.0 * (0.65 + 0.35 * math.sin(omega * tau))
    py5.stroke(236, 72, 153, 220)
    py5.stroke_weight(2.5)
    py5.fill(244, 114, 182, 65)
    py5.circle(vx, vy, vr * 2.0)
    py5.no_stroke()
    for k_v in range(16):
        va = k_v * 2.0 * math.pi / 16.0 + omega * tau
        py5.fill(248, 250, 252, 230) if k_v % 2 == 0 else py5.fill(56, 189, 248, 230)
        py5.circle(vx + math.cos(va) * vr * 0.78, vy + math.sin(va) * vr * 0.78, 8.5)


def render_coccolith_batch(indices, rot_dirs, rx, ry, rz, tau, is_front=True):
    """
    Renders heterococcolith shields in strict back-to-front Painter's depth order
    so adjacent shields imbricate and overlap cleanly like Roman armor scales.
    """
    omega = 2.0 * math.pi

    for idx in indices:
        n_rot = rot_dirs[idx]
        nz = float(n_rot[2])

        phase = omega * tau + idx * 0.52 + RND_BIO_OFFSET
        breath = 1.0 + 0.055 * math.sin(phase)
        extrude = 1.0 + 0.04 * math.cos(phase)

        u_base, v_base = SHIELD_TANGENTS[idx]
        uv_rot = rotate_3d_points(np.array([u_base, v_base]), rx, ry, rz)
        u_r = uv_rot[0]
        v_r = uv_rot[1]

        c3d = n_rot * (SPHERE_R * extrude)
        cx_s = CX + float(c3d[0])
        cy_s = CY + float(c3d[1])

        # Generous imbricated shield radii so adjacent heterococcoliths interlock
        r_distal = 188.0 * breath
        r_proximal = 158.0 * breath
        r_hammer_in = 148.0 * breath
        r_tube = 66.0 * breath
        r_pore = 30.0 * breath
        rim_lift = 16.0 * n_rot[:2]

        ux, uy = float(u_r[0]), float(u_r[1])
        vx, vy = float(v_r[0]), float(v_r[1])

        # Proximal shield points (lower flange resting on cell membrane)
        prox_x = cx_s + (SPOKE_COS * ux + SPOKE_SIN * vx) * r_proximal
        prox_y = cy_s + (SPOKE_COS * uy + SPOKE_SIN * vy) * r_proximal
        prox_nx = np.roll(prox_x, -1)
        prox_ny = np.roll(prox_y, -1)

        # Inner tube points
        in_x = cx_s + (SPOKE_COS * ux + SPOKE_SIN * vx) * r_tube
        in_y = cy_s + (SPOKE_COS * uy + SPOKE_SIN * vy) * r_tube
        in_next_x = np.roll(in_x, -1)
        in_next_y = np.roll(in_y, -1)

        # Outer hammer-neck points on elevated distal shield
        neck_x = cx_s + rim_lift[0] + (SPOKE_COS * ux + SPOKE_SIN * vx) * r_hammer_in
        neck_y = cy_s + rim_lift[1] + (SPOKE_COS * uy + SPOKE_SIN * vy) * r_hammer_in
        neck_next_x = np.roll(neck_x, -1)
        neck_next_y = np.roll(neck_y, -1)

        # T-bar Hammer-head outer tips
        tip1_x = cx_s + rim_lift[0] + (SPOKE_COS_PREV * ux + SPOKE_SIN_PREV * vx) * r_distal
        tip1_y = cy_s + rim_lift[1] + (SPOKE_COS_PREV * uy + SPOKE_SIN_PREV * vy) * r_distal
        tip2_x = cx_s + rim_lift[0] + (SPOKE_COS_NEXT * ux + SPOKE_SIN_NEXT * vx) * r_distal
        tip2_y = cy_s + rim_lift[1] + (SPOKE_COS_NEXT * uy + SPOKE_SIN_NEXT * vy) * r_distal

        # Pore points
        pore_x = cx_s + (SPOKE_COS * ux + SPOKE_SIN * vx) * r_pore
        pore_y = cy_s + (SPOKE_COS * uy + SPOKE_SIN * vy) * r_pore
        p_nx = np.roll(pore_x, -1)
        p_ny = np.roll(pore_y, -1)

        # Cross-polarized birefringence color selection
        azim = math.atan2(float(n_rot[1]), float(n_rot[0]))
        b_mode = int(((azim + math.pi) / (2.0 * math.pi) * 8.0 + tau * 4.0) % 4)
        depth_shade = 0.45 + 0.55 * max(0.0, (nz + 0.85) / 1.85)
        if not is_front:
            depth_shade *= 0.45

        rgb_dist = np.clip(BIREF_PALETTES[b_mode] * depth_shade, 18.0, 255.0)
        rgb_prox = np.clip(BIREF_PALETTES[(b_mode + 1) % 4] * (depth_shade * 0.65), 14.0, 240.0)
        rgb_tube = np.clip(BIREF_PALETTES[(b_mode + 3) % 4] * (depth_shade * 0.85), 20.0, 250.0)
        alpha = 228 if is_front else 90

        # 1. Proximal lower flange ring (provides dark/translucent backing so imbrication is clear)
        q_prox = np.empty((N_SPOKES * 4, 2), dtype=np.float64)
        q_prox[0::4, 0], q_prox[0::4, 1] = in_x, in_y
        q_prox[1::4, 0], q_prox[1::4, 1] = in_next_x, in_next_y
        q_prox[2::4, 0], q_prox[2::4, 1] = prox_nx, prox_ny
        q_prox[3::4, 0], q_prox[3::4, 1] = prox_x, prox_y
        py5.stroke(8, 18, 34, alpha)
        py5.stroke_weight(0.9 if is_front else 0.6)
        py5.fill(float(rgb_prox[0]), float(rgb_prox[1]), float(rgb_prox[2]), int(alpha * 0.72))
        with py5.begin_shape(py5.QUADS):
            py5.vertices(q_prox)

        # 2. Distal T-shaped hammer-head crystal rays & spokes
        q_shaft = np.empty((N_SPOKES * 8, 2), dtype=np.float64)
        q_shaft[0::8, 0], q_shaft[0::8, 1] = in_x, in_y
        q_shaft[1::8, 0], q_shaft[1::8, 1] = in_x * 0.62 + in_next_x * 0.38, in_y * 0.62 + in_next_y * 0.38
        q_shaft[2::8, 0], q_shaft[2::8, 1] = neck_x * 0.62 + neck_next_x * 0.38, neck_y * 0.62 + neck_next_y * 0.38
        q_shaft[3::8, 0], q_shaft[3::8, 1] = neck_x, neck_y

        q_shaft[4::8, 0], q_shaft[4::8, 1] = neck_x, neck_y
        q_shaft[5::8, 0], q_shaft[5::8, 1] = tip1_x, tip1_y
        q_shaft[6::8, 0], q_shaft[6::8, 1] = tip2_x, tip2_y
        q_shaft[7::8, 0], q_shaft[7::8, 1] = neck_x * 0.48 + neck_next_x * 0.52, neck_y * 0.48 + neck_next_y * 0.52

        py5.stroke(10, 22, 40, alpha)
        py5.stroke_weight(1.1 if is_front else 0.7)
        py5.fill(float(rgb_dist[0]), float(rgb_dist[1]), float(rgb_dist[2]), alpha)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(q_shaft)

        # 3. Central proto-coccolith tube collar & central bridge grill
        q_ring = np.empty((N_SPOKES * 4, 2), dtype=np.float64)
        q_ring[0::4, 0], q_ring[0::4, 1] = pore_x, pore_y
        q_ring[1::4, 0], q_ring[1::4, 1] = p_nx, p_ny
        q_ring[2::4, 0], q_ring[2::4, 1] = in_next_x, in_next_y
        q_ring[3::4, 0], q_ring[3::4, 1] = in_x, in_y
        py5.fill(float(rgb_tube[0]), float(rgb_tube[1]), float(rgb_tube[2]), alpha)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(q_ring)

        # 4. Specular crystal arris highlights & central grill bars
        segs = np.empty((N_SPOKES * 2 + 5, 4), dtype=np.float64)
        segs[0:N_SPOKES] = np.column_stack([in_x, in_y, neck_x, neck_y])
        segs[N_SPOKES:2 * N_SPOKES] = np.column_stack([tip1_x, tip1_y, tip2_x, tip2_y])
        for g_k in range(5):
            segs[2 * N_SPOKES + g_k] = [
                pore_x[g_k * 2], pore_y[g_k * 2],
                pore_x[N_SPOKES // 2 + g_k * 2], pore_y[N_SPOKES // 2 + g_k * 2]
            ]
        py5.stroke(245, 250, 255, 205 if is_front else 75)
        py5.stroke_weight(1.3 if is_front else 0.8)
        py5.lines(segs)


def draw_polarizer_bezel_ring(tau):
    """Draws the graduated cross-polarized optical microscope stage bezel around the coccosphere."""
    r_in = 765.0
    r_out = 805.0
    py5.no_fill()
    py5.stroke(56, 189, 248, 175)
    py5.stroke_weight(2.4)
    py5.circle(CX, CY, r_in * 2.0)
    py5.stroke(148, 163, 184, 145)
    py5.stroke_weight(1.6)
    py5.circle(CX, CY, r_out * 2.0)

    for deg in range(0, 360, 5):
        rad = math.radians(deg) + tau * 2.0 * math.pi * 0.25
        ca, sa = math.cos(rad), math.sin(rad)
        tlen = 24.0 if deg % 30 == 0 else (14.0 if deg % 15 == 0 else 7.0)
        py5.stroke(125, 211, 252, 210 if deg % 15 == 0 else 110)
        py5.stroke_weight(2.2 if deg % 30 == 0 else 1.2)
        py5.line(CX + ca * r_in, CY + sa * r_in,
                 CX + ca * (r_in + tlen), CY + sa * (r_in + tlen))


def draw_card_box(x, y, w, h, title, subtitle):
    """Draws a dark pelagic glassmorphic scientific telemetry card in a corner."""
    py5.no_stroke()
    py5.fill(2, 5, 12, 165)
    py5.rect(x + 8, y + 8, w, h, 8)
    py5.stroke(56, 189, 248, 185)
    py5.stroke_weight(2.0)
    py5.fill(8, 16, 30, 232)
    py5.rect(x, y, w, h, 8)
    py5.stroke(30, 64, 105, 160)
    py5.stroke_weight(1.2)
    py5.no_fill()
    py5.rect(x + 10, y + 10, w - 20, h - 20, 4)
    py5.fill(224, 242, 254)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(21)
    py5.text(title, x + 26, y + 22)
    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text(subtitle, x + 26, y + 50)
    py5.stroke(38, 82, 130, 175)
    py5.stroke_weight(1.4)
    py5.line(x + 24, y + 76, x + w - 24, y + 76)


def draw_biomineral_apparatuses(tau):
    """Draws four full-flank marine biomineralization & crystallography telemetry cards."""
    omega = 2.0 * math.pi
    cw = 760
    ch_top = 835
    ch_bot = 845

    # --- Top-Left Card (y=210..1045): FIG. 01 HETEROCOCCOLITH PLAN VIEW & FIG. 02 V/R CRYSTAL NUCLEATION ---
    x1, y1 = 110, 210
    draw_card_box(x1, y1, cw, ch_top,
                  "FIG. 01 // EMILIANIA HUXLEYI HETEROCOCCOLITH ROSETTE",
                  "26-RAY DISTAL SHIELD HAMMER-HEAD INTERLOCKING GEOMETRY")

    mcx, mcy = x1 + 195, y1 + 245
    mr_out = 126.0
    mr_in = 50.0
    for k in range(26):
        a1 = k * 2.0 * math.pi / 26.0 + tau * omega * 0.25
        a2 = a1 + (2.0 * math.pi / 26.0) * 0.68
        py5.stroke(56, 189, 248, 220)
        py5.stroke_weight(2.2)
        py5.line(mcx + math.cos(a1) * mr_in, mcy + math.sin(a1) * mr_in,
                 mcx + math.cos(a1) * mr_out, mcy + math.sin(a1) * mr_out)
        py5.stroke(224, 242, 254, 240)
        py5.stroke_weight(3.5)
        py5.line(mcx + math.cos(a1 - 0.05) * mr_out, mcy + math.sin(a1 - 0.05) * mr_out,
                 mcx + math.cos(a2) * mr_out, mcy + math.sin(a2) * mr_out)
    py5.stroke(251, 191, 36, 230)
    py5.stroke_weight(2.8)
    py5.fill(15, 28, 48, 220)
    py5.circle(mcx, mcy, mr_in * 2.0)
    py5.stroke(232, 121, 249, 210)
    py5.circle(mcx, mcy, mr_in * 0.95)

    tx1 = x1 + 365
    py5.no_stroke()
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text("SPECIES         : EMILIANIA HUXLEYI (TYPE A)", tx1, y1 + 105)
    py5.text("SHIELD DIAMETER : 3.85 microns (DISTAL)", tx1, y1 + 139)
    py5.text("RADIAL SEGMENTS : 26 R-UNIT CRYSTAL RAYS", tx1, y1 + 173)
    py5.text("MINERAL PHASE   : TRIGONAL CALCITE (R-3c)", tx1, y1 + 207)
    py5.fill(56, 189, 248)
    py5.text("DISTAL SLITS    : HAMMER-HEAD T-FLANGES", tx1, y1 + 245)
    py5.fill(251, 191, 36)
    py5.text("CENTRAL AREA    : SLOTTED GRILL & TUBE", tx1, y1 + 279)
    py5.fill(52, 211, 153)
    py5.text("COCCOSPHERE     : 38 IMBRICATED SHIELDS", tx1, y1 + 313)

    # Lower section of Top-Left Card: FIG. 02 V/R Crystal Unit Nucleation Ring
    py5.stroke(38, 82, 130, 175)
    py5.stroke_weight(1.4)
    py5.line(x1 + 24, y1 + 405, x1 + cw - 24, y1 + 405)
    py5.fill(224, 242, 254)
    py5.text_size(20)
    py5.text("FIG. 02 // V/R PROTO-COCCOLITH NUCLEATION MODEL", x1 + 26, y1 + 425)
    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text("YOUNG & HENRIKSEN (2003) ALTERNATING C-AXIS ORIENTATION", x1 + 26, y1 + 452)

    vcx, vcy = x1 + 195, y1 + 640
    vr_ring = 110.0
    py5.no_fill()
    py5.stroke(148, 163, 184, 140)
    py5.stroke_weight(1.8)
    py5.circle(vcx, vcy, vr_ring * 2.0)
    for k_u in range(16):
        ua = k_u * 2.0 * math.pi / 16.0 - tau * omega * 0.5
        ux_p = vcx + math.cos(ua) * vr_ring
        uy_p = vcy + math.sin(ua) * vr_ring
        is_r_unit = (k_u % 2 == 0)
        py5.push_matrix()
        py5.translate(ux_p, uy_p)
        py5.rotate(ua if is_r_unit else ua + math.pi / 2.0)
        py5.stroke(248, 250, 252, 230)
        py5.stroke_weight(1.6)
        if is_r_unit:
            py5.fill(56, 189, 248, 230)
            py5.rect(-12, -7, 24, 14, 2)
        else:
            py5.fill(232, 121, 249, 230)
            py5.rect(-10, -10, 20, 20, 2)
        py5.pop_matrix()

    py5.no_stroke()
    py5.fill(56, 189, 248)
    py5.rect(tx1, y1 + 520, 22, 22, 3)
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text("R-UNIT (RADIAL C-AXIS // DOMINANT)", tx1 + 34, y1 + 522)

    py5.fill(232, 121, 249)
    py5.rect(tx1, y1 + 568, 22, 22, 3)
    py5.fill(224, 242, 254)
    py5.text("V-UNIT (VERTICAL C-AXIS // VESTIGIAL)", tx1 + 34, y1 + 570)

    py5.fill(148, 163, 184)
    py5.text("BASE PLATE  : ACID POLYSACCHARIDE SCALE", tx1, y1 + 625)
    py5.text("EPITAXY     : Ca2+ ION SPATIAL TEMPLATE", tx1, y1 + 659)
    py5.text("EXOCYTOSIS  : ~1 COCCOLITH / 45 MINUTES", tx1, y1 + 693)

    # --- Bottom-Left Card (y=1085..1930): FIG. 03 AXIAL CROSS-SECTION & FIG. 04 BIREFRINGENCE ---
    x2, y2 = 110, 1085
    draw_card_box(x2, y2, cw, ch_bot,
                  "FIG. 03 // HETEROCOCCOLITH DOUBLE-SHIELD CROSS-SECTION",
                  "INTERLOCKING DISTAL & PROXIMAL FLANGES AROUND CENTRAL TUBE")

    cs_y = y2 + 235
    cs_x = x2 + 380
    spread = 16.0 * math.sin(omega * tau)
    for side in (-1.0, 1.0):
        bx = cs_x + side * (145.0 + spread)
        py5.stroke(224, 242, 254, 230)
        py5.stroke_weight(2.4)
        py5.fill(56, 189, 248, 195) if side < 0 else py5.fill(251, 191, 36, 195)
        with py5.begin_shape():
            py5.vertex(bx - side * 120, cs_y - 48)
            py5.vertex(bx + side * 65, cs_y - 36)
            py5.vertex(bx + side * 35, cs_y - 10)
            py5.vertex(bx + side * 58, cs_y + 28)
            py5.vertex(bx - side * 95, cs_y + 38)
            py5.vertex(bx - side * 42, cs_y + 6)
        py5.end_shape(py5.CLOSE)

    py5.no_stroke()
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text(f"DISTAL-PROXIMAL INTERLOCK GAP : {1.25 + 0.35*math.sin(omega*tau):.2f} microns   //   SELF-WEDGING CURVATURE : 14.5 DEG", x2 + 48, cs_y + 72)

    py5.stroke(38, 82, 130, 175)
    py5.stroke_weight(1.4)
    py5.line(x2 + 24, y2 + 375, x2 + cw - 24, y2 + 375)
    py5.fill(224, 242, 254)
    py5.text_size(20)
    py5.text("FIG. 04 // CROSSED-NICOLS CALCITE BIREFRINGENCE (DELTA n = -0.172)", x2 + 26, y2 + 395)
    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text("UNIAXIAL NEGATIVE EXTINCTION CROSS (ISOGYRE) & INTERFERENCE ORDERS", x2 + 26, y2 + 422)

    bcx2, bcy2 = x2 + 205, y2 + 625
    br2 = 116.0
    quad_cols = [(56, 189, 248), (251, 191, 36), (56, 189, 248), (232, 121, 249)]
    for q_i in range(4):
        qa = q_i * math.pi / 2.0 + math.pi / 4.0 + tau * omega * 0.5
        c_q = quad_cols[q_i]
        py5.no_stroke()
        py5.fill(c_q[0], c_q[1], c_q[2], 195)
        py5.arc(bcx2, bcy2, br2 * 2.0, br2 * 2.0, qa - 0.52, qa + 0.52, py5.PIE)
    py5.stroke(224, 242, 254, 210)
    py5.stroke_weight(2.0)
    py5.no_fill()
    py5.circle(bcx2, bcy2, br2 * 2.0)
    py5.line(bcx2 - br2 - 14, bcy2, bcx2 + br2 + 14, bcy2)
    py5.line(bcx2, bcy2 - br2 - 14, bcx2, bcy2 + br2 + 14)

    tx2 = x2 + 370
    py5.no_stroke()
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text("ORDINARY INDEX (n_o)     : 1.6584", tx2, y2 + 505)
    py5.text("EXTRAORDINARY (n_e)      : 1.4864", tx2, y2 + 539)
    py5.text("BIREFRINGENCE (DELTA n)  : -0.1720 (HIGH)", tx2, y2 + 573)
    py5.fill(232, 121, 249)
    py5.text("GYPSUM LAMBDA PLATE      : 530 nm ADDITIVE", tx2, y2 + 615)
    py5.fill(251, 191, 36)
    py5.text("EXTINCTION ISOGYRES      : 4 ORTHOGONAL ARMS", tx2, y2 + 649)
    py5.fill(52, 211, 153)
    py5.text("ALBEDO BACKSCATTER       : +0.28 W/m2 FORCING", tx2, y2 + 683)

    # --- Top-Right Card (y=210..1045): FIG. 05 GOLGI EXOCYTOSIS & FIG. 06 CARBONATE PUMP ---
    x3, y3 = WIDTH - cw - 110, 210
    draw_card_box(x3, y3, cw, ch_top,
                  "FIG. 05 // INTRACELLULAR COCCOLITHOGENESIS & EXOCYTOSIS",
                  "GOLGI-DERIVED COCCOLITH VESICLE (CV) MORPHOGENETIC STAGE CYCLE")

    stage_names = ["I. ORGANIC SCALE", "II. PROTO-RING", "III. R-UNIT GROWTH", "IV. EXOCYTOSIS"]
    active_st = int((tau * 4.0) % 4)
    for st_i in range(4):
        sx = x3 + 112 + st_i * 178
        sy = y3 + 215
        sr = 64.0
        is_act = (st_i == active_st)
        py5.stroke(56, 189, 248 if is_act else 100, 240 if is_act else 150)
        py5.stroke_weight(3.0 if is_act else 1.6)
        py5.fill(15, 32, 56, 230)
        py5.circle(sx, sy, sr * 2.0)
        r_grow = sr * (0.28 + 0.22 * st_i)
        for k_r in range(12):
            ra = k_r * math.pi / 6.0 + tau * omega
            py5.stroke(251, 191, 36 if is_act else 180, 220)
            py5.stroke_weight(2.2)
            py5.line(sx, sy, sx + math.cos(ra) * r_grow, sy + math.sin(ra) * r_grow)
        py5.no_stroke()
        py5.fill(224, 242, 254 if is_act else 160)
        py5.text_align(py5.CENTER, py5.TOP)
        py5.text_size(14)
        py5.text(stage_names[st_i], sx, sy + sr + 16)

    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(148, 163, 184)
    py5.text_size(15)
    py5.text("REACTION : Ca2+ + 2 HCO3-  -->  CaCO3 (CALCITE) + CO2 (PHOTOSYNTHESIS) + H2O", x3 + 38, y3 + 345)

    py5.stroke(38, 82, 130, 175)
    py5.stroke_weight(1.4)
    py5.line(x3 + 24, y3 + 405, x3 + cw - 24, y3 + 405)
    py5.fill(224, 242, 254)
    py5.text_size(20)
    py5.text("FIG. 06 // HAPTOPHYTE ORGANELLE & CALCITE SATURATION", x3 + 26, y3 + 425)
    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text("OMEGA_CALCITE ARAGONITE HORIZON & PIGMENT CHROMATOGRAPHY", x3 + 26, y3 + 452)

    specs = [
        ((224, 242, 254), "DISTAL SHIELD R-UNITS // TRIGONAL CaCO3 (CALCITE)"),
        ((56, 189, 248), "PROXIMAL TUBE COLLAR  // INTERLOCKING SUTURE"),
        ((245, 158, 11), "CHRYSOPLASTID LOBES   // 19'-HEXANOYLOXYFUCOXANTHIN"),
        ((232, 121, 249), "GOLGI COCCOLITH VESICLE // ACID POLYSACCHARIDE MATRIX"),
        ((52, 211, 153), "ISOKONT FLAGELLA PAIR // 9+2 AXONEME MICROTUBULES"),
        ((251, 191, 36), "COILED HAPTONEMA      // 7-MICROTUBULE SENSORY ORGAN"),
    ]
    for s_i, (s_col, s_lbl) in enumerate(specs):
        by = y3 + 502 + s_i * 50
        py5.stroke(224, 242, 254, 180)
        py5.stroke_weight(1.4)
        py5.fill(s_col[0], s_col[1], s_col[2], 235)
        py5.rect(x3 + 38, by, 44, 25, 3)
        py5.no_stroke()
        py5.fill(224, 242, 254)
        py5.text_size(15)
        py5.text(s_lbl, x3 + 98, by + 4)

    # --- Bottom-Right Card (y=1085..1930): FIG. 07 GOLDBERG POLYHEDRON & FIG. 08 CALCIFICATION WAVE ---
    x4, y4 = WIDTH - cw - 110, 1085
    draw_card_box(x4, y4, cw, ch_bot,
                  "FIG. 07 // SPHERICAL PACKING TOPOLOGY & OVERLAP RATIO",
                  "EULER CHARACTERISTIC V - E + F = 2 ON 38-SHIELD COCCOSPHERE")

    gcx, gcy = x4 + 195, y4 + 235
    gr = 105.0
    py5.no_fill()
    py5.stroke(56, 189, 248, 195)
    py5.stroke_weight(2.0)
    py5.circle(gcx, gcy, gr * 2.0)
    for lat_k in (-0.55, 0.0, 0.55):
        py5.ellipse(gcx, gcy + lat_k * gr, gr * 2.0 * math.sqrt(1.0 - lat_k * lat_k), gr * 0.38)
    for lon_k in range(6):
        la = lon_k * math.pi / 6.0 + tau * omega * 0.5
        py5.ellipse(gcx, gcy, gr * 2.0 * abs(math.cos(la)), gr * 2.0)

    tx4 = x4 + 345
    py5.no_stroke()
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text("SHIELD PACKING NUMBER   : N = 38 PLATES", tx4, y4 + 108)
    py5.text("MEAN COORDINATION (Z)   : 5.68 NEIGHBORS", tx4, y4 + 142)
    py5.text("SHIELD OVERLAP RATIO    : 1.38 (IMBRICATED)", tx4, y4 + 176)
    py5.fill(56, 189, 248)
    py5.text("CALCITE MASS / CELL     : 23.6 picograms", tx4, y4 + 218)
    py5.fill(251, 191, 36)
    py5.text("PIC : POC CARBON RATIO  : 1.18 +/- 0.06", tx4, y4 + 252)
    py5.fill(52, 211, 153)
    py5.text("OMEGA_CALCITE SATURATION: 4.82 (SUPERSATURATED)", tx4, y4 + 286)

    py5.stroke(38, 82, 130, 175)
    py5.stroke_weight(1.4)
    py5.line(x4 + 24, y4 + 375, x4 + cw - 24, y4 + 375)
    py5.fill(224, 242, 254)
    py5.text_size(20)
    py5.text("FIG. 08 // DIURNAL CALCIFICATION & EXOCYTOSIS FLUX WAVE", x4 + 26, y4 + 395)
    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text("COUPLED Ca2+ VESICLE TRANSPORT, R-UNIT EXTENSION & DMSP OSCILLATION", x4 + 26, y4 + 422)

    wx0, wy0, ww, wh = x4 + 55, y4 + 475, 650, 260
    py5.stroke(38, 82, 130, 180)
    py5.stroke_weight(1.6)
    py5.fill(6, 12, 24)
    py5.rect(wx0, wy0, ww, wh, 4)
    py5.stroke(24, 48, 78, 150)
    py5.stroke_weight(1.0)
    for gy_i in range(1, 4):
        py5.line(wx0, wy0 + gy_i * wh / 4.0, wx0 + ww, wy0 + gy_i * wh / 4.0)
    for gx_i in range(1, 6):
        py5.line(wx0 + gx_i * ww / 6.0, wy0, wx0 + gx_i * ww / 6.0, wy0 + wh)

    wave_cols = [(56, 189, 248), (251, 191, 36), (232, 121, 249)]
    for c_idx, col in enumerate(wave_cols):
        py5.no_fill()
        py5.stroke(col[0], col[1], col[2], 235)
        py5.stroke_weight(3.0)
        with py5.begin_shape():
            for p_i in range(66):
                u = p_i / 65.0
                px_w = wx0 + u * ww
                val = math.sin(omega * tau - u * 5.2 + c_idx * 1.2) * math.cos(u * 2.4 - omega * tau * 0.5)
                py_w = wy0 + wh * 0.5 - val * (wh * 0.36)
                py5.vertex(px_w, py_w)
        py5.end_shape()

    py5.no_stroke()
    py5.fill(148, 163, 184)
    py5.text_size(15)
    py5.text("CYAN: Ca2+ PUMP FLUX   //   GOLD: PHOTOSYNTHETIC HCO3-   //   ROSE: EXOCYTOSIS STRAIN", wx0, wy0 + wh + 22)


def draw_archival_border_and_typography(tau):
    """Draws double-ruled museum border and scholarly typography without any personal marks."""
    py5.no_fill()
    py5.stroke(56, 189, 248, 195)
    py5.stroke_weight(3.2)
    py5.rect(64, 64, WIDTH - 128, HEIGHT - 128, 6)

    py5.stroke(38, 82, 130, 160)
    py5.stroke_weight(1.5)
    py5.rect(78, 78, WIDTH - 156, HEIGHT - 156, 4)

    py5.fill(240, 249, 255)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(38)
    py5.text("EMILIANIA HUXLEYI // COCCOLITHOPHORE CALCITE COCCOSPHERE MORPHOGENESIS", WIDTH / 2.0, 98)

    py5.fill(56, 189, 248)
    py5.text_size(21)
    py5.text("IMBRICATED HETEROCOCCOLITH CALCITE SHIELDS - V/R CRYSTAL NUCLEATION - CROSSED-NICOLS BIREFRINGENCE", WIDTH / 2.0, 150)

    py5.fill(148, 163, 184)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(20)
    py5.text("PHYLUM: HAPTOPHYTA // ORDER: ISOCHRYSIDALES // MINERAL: TRIGONAL CALCITE (CaCO3) // 38 HETEROCOCCOLITHS", 108, HEIGHT - 88)

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(f"4K GENERATIVE BIOMINERALIZATION // HARMONIC PHASE TAU = {tau:.3f} (12.0s @ 60FPS)", WIDTH - 108, HEIGHT - 88)


def finish_and_encode():
    global START_TIME
    total_elapsed = time.time() - START_TIME
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {total_elapsed:.1f}s (~{TOTAL_FRAMES/total_elapsed:.2f} fps).")
    print(f"[{WORK_NAME}] Compiling 4K 60fps MP4 with FFmpeg...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "fast",
        str(OUTPUT_MP4)
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mp4_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
        print(f"[{WORK_NAME}] Successfully generated output.mp4 ({mp4_size_mb:.2f} MB)")
    except Exception as e:
        print(f"[{WORK_NAME}] Error encoding video: {e}")
    finally:
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")

    print(f"[{WORK_NAME}] Complete!")
    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
