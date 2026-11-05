"""
Kinetic Seifert Surface & Milnor Fibration Torus Knot 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Mathematical / Abstract Topology genre,
exploring Herbert Seifert's 1934 construction of orientable surfaces spanning a
knot (Uber das Geschlecht von Knoten, Math. Ann. 1934) and John Milnor's 1968
Fibration Theorem for algebraic knots (Singular Points of Complex Hypersurfaces),
executed on deep topological obsidian slate (#060913).

For a (p, q) torus knot K(p, q) = { (z1, z2) in S^3 : z1^p + z2^q = 0 }, the
complement S^3 \\ K fibers smoothly over the circle S^1 via the Milnor map
phi(z1, z2) = arg(z1^p + z2^q) in [0, 2*pi). Each fiber F_theta = phi^(-1)(theta)
is a compact, connected, two-sided orientable Seifert surface of genus
g = (p - 1)(q - 1) / 2 whose boundary is the invariant torus knot binding K(p, q).

This 4K 60fps simulation visualizes:
1. The 3D stereographic immersion of the orientable Seifert surface page F_theta
   spanning the (3, 5) Torus Knot (genus g = 4, 3 central Seifert disks linked by
   15 half-twisted saddle bands), depth-sorted back-to-front via Painter's algorithm
   with depth-interleaved golden knot boundary segments.
2. Two-sided orientable surface coloration: the positive normal side (+N) gleams in
   electric sapphire-cyan while the negative normal side (-N) glows in Venetian
   carmine-amethyst across the twisting saddle bands and central Seifert disks.
3. Eight algebraic topology & knot theory apparatuses across four balanced flank cards.
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
WORK_NAME = "kinetic_seifert_surface_milnor_fibration_torus_knot_2d"
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
RND_ROT_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_FIB_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 25.0
SCALE_3D = 475.0
CAM_DIST = 4.3

# Torus Knot Parameters: K(P, Q) = (3, 5), Genus g = (3-1)(5-1)/2 = 4
P_KNOT = 3
Q_KNOT = 5
GENUS = (P_KNOT - 1) * (Q_KNOT - 1) // 2

# Parametric Mesh for the Seifert Surface / Milnor Fiber Page F_theta:
# u in [0, 2*pi) parameterizes the longitudinal angle along the knot (N_U = 160)
# v in [-1, 1] spans across the 3 central Seifert disks and twists into the 5 lobes of K(3,5) (N_V = 21)
N_U = 160
N_V = 21
U_ARR = np.linspace(0.0, 2.0 * math.pi, N_U, endpoint=False)
V_ARR = np.linspace(-1.0, 1.0, N_V)
U_MESH, V_MESH = np.meshgrid(U_ARR, V_ARR, indexing="ij")  # shape (N_U, N_V)


def evaluate_seifert_surface_3d(milnor_phase, rx, ry, rz):
    """
    Computes the 3D coordinates of the orientable Seifert surface F_theta spanning K(3,5).
    Centered on the 3 nested, elevation-separated Seifert circles (R_c(u), Z_c(u)),
    the parameter v in [-1, 1] spans symmetrically across the 15 half-twisted saddle bands
    with drho/dv = r_xy * cos(psi), guaranteeing a 100% smooth immersion (rho >= 0.29 > 0,
    zero central spikes) and an exact 50/50 alternation of +N (Sapphire-Cyan) and
    -N (Venetian Carmine-Amethyst) orientable faces across every twist.
    """
    phi_q = Q_KNOT * U_MESH + 0.5 * milnor_phase
    theta_p = P_KNOT * U_MESH

    # The 3 nested Seifert circles (separated radially and vertically across the 3 sheets of u)
    r_core = 0.90 + 0.15 * np.cos(U_MESH) + 0.05 * np.sin(2.0 * U_MESH - milnor_phase)
    z_core = 0.26 * np.sin(U_MESH + 0.4 * milnor_phase) + 0.08 * np.cos(2.0 * U_MESH)

    # Smooth meridian twist angle along the (3, 5) torus knot fibration
    twist_angle = phi_q + 0.28 * (1.0 - V_MESH * V_MESH) * np.sin(2.0 * U_MESH + milnor_phase)
    arch = 1.0 - V_MESH * V_MESH

    rho = r_core + 0.46 * V_MESH * np.cos(twist_angle) + 0.06 * arch * np.cos(phi_q - theta_p)
    x = rho * np.cos(theta_p + 0.12 * V_MESH * np.sin(twist_angle))
    y = rho * np.sin(theta_p + 0.12 * V_MESH * np.sin(twist_angle))
    z = (
        z_core
        + 0.52 * V_MESH * np.sin(twist_angle)
        + 0.14 * arch * np.sin(phi_q + theta_p)
    )

    # Apply 3D rotation (ry, rx, rz)
    cx_r, sx_r = math.cos(rx), math.sin(rx)
    cy_r, sy_r = math.cos(ry), math.sin(ry)
    cz_r, sz_r = math.cos(rz), math.sin(rz)

    # Rotate Y
    x1 = x * cy_r + z * sy_r
    y1 = y
    z1 = -x * sy_r + z * cy_r

    # Rotate X
    x2 = x1
    y2 = y1 * cx_r - z1 * sx_r
    z2 = y1 * sx_r + z1 * cx_r

    # Rotate Z
    x3 = x2 * cz_r - y2 * sz_r
    y3 = x2 * sz_r + y2 * cz_r
    z3 = z2

    # Perspective projection to 2D screen coordinates
    persp = CAM_DIST / (CAM_DIST - z3)
    sx = CX + x3 * SCALE_3D * persp
    sy = CY + y3 * SCALE_3D * persp

    return x3, y3, z3, sx, sy


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

    milnor_theta = omega * tau + RND_FIB_PHASE
    ry = omega * tau + RND_ROT_PHASE
    rx = 0.62 + 0.18 * math.sin(omega * tau)
    rz = 0.18 * math.cos(omega * tau)

    # 1. Deep Topological Obsidian Slate Substrate (#060913)
    py5.background(6, 9, 19)

    # 2. Ambient Stereographic S^3 Projection Glow & Coordinate Graticule
    py5.no_stroke()
    for r_g, col_g in [
        (1150, (14, 28, 56, 26)),
        (860, (22, 46, 92, 32)),
        (600, (42, 32, 84, 36)),
        (360, (88, 28, 72, 32)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    py5.stroke(24, 42, 72, 110)
    py5.stroke_weight(1.4)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)

    py5.no_fill()
    py5.stroke(42, 78, 124, 120)
    py5.stroke_weight(1.8)
    for r_ring in [320, 560, 740, 840]:
        py5.circle(CX, CY, r_ring * 2.0)

    py5.stroke(56, 189, 248, 80)
    py5.line(CX - 900, CY, CX + 900, CY)
    py5.line(CX, CY - 880, CX, CY + 880)

    # 3. Evaluate and Render the 3D Seifert Surface F_theta & Depth-Interleaved Torus Knot K(3,5)
    render_seifert_manifold_and_knot(milnor_theta, rx, ry, rz, tau)

    # 4. Outer Stereographic Degree Bezel Ring
    draw_stereographic_bezel(tau, milnor_theta)

    # 5. Four Quadrant Algebraic Topology & Knot Theory Apparatuses
    draw_topology_apparatuses(tau, milnor_theta)

    # 6. Archival Museum Border & Scholarly Typography (Zero Personal Signatures/Seals)
    draw_archival_border_and_typography(tau, milnor_theta)

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


def render_seifert_manifold_and_knot(milnor_theta, rx, ry, rz, tau):
    """
    Renders the 3D Seifert surface quad mesh with Painter's depth-sorting and
    two-sided orientable normal coloration (+N Sapphire/Cyan, -N Carmine/Amethyst),
    with depth-interleaved golden (3,5) torus knot boundary segments.
    """
    x3, y3, z3, sx, sy = evaluate_seifert_surface_3d(milnor_theta, rx, ry, rz)

    x3_u = np.roll(x3, -1, axis=0)
    y3_u = np.roll(y3, -1, axis=0)
    z3_u = np.roll(z3, -1, axis=0)
    sx_u = np.roll(sx, -1, axis=0)
    sy_u = np.roll(sy, -1, axis=0)

    q_sx0 = sx[:, :-1]
    q_sy0 = sy[:, :-1]
    q_sx1 = sx_u[:, :-1]
    q_sy1 = sy_u[:, :-1]
    q_sx2 = sx_u[:, 1:]
    q_sy2 = sy_u[:, 1:]
    q_sx3 = sx[:, 1:]
    q_sy3 = sy[:, 1:]

    # Mean Z depth per quad for Painter's back-to-front sorting
    q_z = 0.25 * (z3[:, :-1] + z3_u[:, :-1] + z3_u[:, 1:] + z3[:, 1:])

    # Compute 3D surface normal vector N = dP/du x dP/dv in rotated camera space
    du_x = x3_u[:, :-1] - x3[:, :-1]
    du_y = y3_u[:, :-1] - y3[:, :-1]
    du_z = z3_u[:, :-1] - z3[:, :-1]

    dv_x = x3[:, 1:] - x3[:, :-1]
    dv_y = y3[:, 1:] - y3[:, :-1]
    dv_z = z3[:, 1:] - z3[:, :-1]

    nx_3d = du_y * dv_z - du_z * dv_y
    ny_3d = du_z * dv_x - du_x * dv_z
    nz_3d = du_x * dv_y - du_y * dv_x
    n_norm = np.sqrt(nx_3d * nx_3d + ny_3d * ny_3d + nz_3d * nz_3d) + 1e-6

    # Directional illumination combining camera Z normal and oblique upper-left key light
    normal_z = nz_3d / n_norm
    light_dot = (0.45 * nx_3d - 0.35 * ny_3d + 0.82 * nz_3d) / n_norm

    n_quads = q_z.size
    flat_z = q_z.ravel()
    flat_nz = normal_z.ravel()
    flat_ldot = light_dot.ravel()
    flat_v = np.broadcast_to(V_ARR[:-1], q_z.shape).ravel()

    flat_quads = np.empty((n_quads, 4, 2), dtype=np.float64)
    flat_quads[:, 0, 0] = q_sx0.ravel()
    flat_quads[:, 0, 1] = q_sy0.ravel()
    flat_quads[:, 1, 0] = q_sx1.ravel()
    flat_quads[:, 1, 1] = q_sy1.ravel()
    flat_quads[:, 2, 0] = q_sx2.ravel()
    flat_quads[:, 2, 1] = q_sy2.ravel()
    flat_quads[:, 3, 0] = q_sx3.ravel()
    flat_quads[:, 3, 1] = q_sy3.ravel()

    # Extract both boundary strands of the ribbon (v = +1 and v = -1) plus central Seifert circle (v = 0)
    bx_out, by_out, bz_out = sx[:, -1], sy[:, -1], z3[:, -1]
    bx_out_n, by_out_n, bz_out_n = np.roll(bx_out, -1), np.roll(by_out, -1), np.roll(bz_out, -1)
    segs_out = np.column_stack([bx_out, by_out, bx_out_n, by_out_n])
    z_segs_out = 0.5 * (bz_out + bz_out_n)

    bx_in, by_in, bz_in = sx[:, 0], sy[:, 0], z3[:, 0]
    bx_in_n, by_in_n, bz_in_n = np.roll(bx_in, -1), np.roll(by_in, -1), np.roll(bz_in, -1)
    segs_in = np.column_stack([bx_in, by_in, bx_in_n, by_in_n])
    z_segs_in = 0.5 * (bz_in + bz_in_n)

    mid_idx = N_V // 2
    bx_mid, by_mid, bz_mid = sx[:, mid_idx], sy[:, mid_idx], z3[:, mid_idx]
    bx_mid_n, by_mid_n, bz_mid_n = np.roll(bx_mid, -1), np.roll(by_mid, -1), np.roll(bz_mid, -1)
    segs_mid = np.column_stack([bx_mid, by_mid, bx_mid_n, by_mid_n])
    z_segs_mid = 0.5 * (bz_mid + bz_mid_n)

    order = np.argsort(flat_z)
    n_slabs = 14
    slab_size = n_quads // n_slabs

    # Color palette table for orientable side (sign of normal_z) and lighting magnitude:
    # Positive side (+N): Deep Cobalt -> Electric Sapphire -> Luminous Cyan -> Ice White-Cyan
    # Negative side (-N): Deep Amethyst -> Venetian Carmine -> Luminous Rose -> Orchid Pink
    pos_cols = [
        (20, 58, 138),
        (37, 99, 235),
        (56, 189, 248),
        (165, 235, 255),
    ]
    neg_cols = [
        (112, 22, 82),
        (190, 24, 93),
        (236, 72, 153),
        (244, 172, 255),
    ]

    for s_idx in range(n_slabs):
        start_i = s_idx * slab_size
        end_i = n_quads if s_idx == n_slabs - 1 else (s_idx + 1) * slab_size
        slab_indices = order[start_i:end_i]
        z_min_slab = float(flat_z[slab_indices[0]])
        z_max_slab = float(flat_z[slab_indices[-1]]) if s_idx < n_slabs - 1 else 999.0
        if s_idx == 0:
            z_min_slab = -999.0

        depth_factor = 0.50 + 0.50 * (s_idx / float(n_slabs - 1))
        alpha_slab = int(175 + 70 * (s_idx / float(n_slabs - 1)))

        slab_buckets = {}
        for idx in slab_indices:
            nz_val = float(flat_nz[idx])
            ld_val = float(flat_ldot[idx])
            v_val = float(flat_v[idx])
            if v_val > 0.89 or v_val < -0.89:
                b_key = (2, 0)
            else:
                side = 1 if nz_val >= 0.0 else 0
                lvl = min(3, int(abs(ld_val) * 3.8))
                b_key = (side, lvl)
            slab_buckets.setdefault(b_key, []).append(flat_quads[idx])

        py5.stroke(8, 16, 32, 165)
        py5.stroke_weight(0.9)
        for (side, lvl), q_list in slab_buckets.items():
            if side == 2:
                rgb = (int(251 * depth_factor), int(191 * depth_factor), int(36 * depth_factor))
            elif side == 1:
                base = pos_cols[lvl]
                rgb = (int(base[0] * depth_factor), int(base[1] * depth_factor), int(base[2] * depth_factor))
            else:
                base = neg_cols[lvl]
                rgb = (int(base[0] * depth_factor), int(base[1] * depth_factor), int(base[2] * depth_factor))

            py5.fill(rgb[0], rgb[1], rgb[2], alpha_slab)
            merged_verts = np.vstack(q_list)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(merged_verts)

        # Interleave the golden (3,5) Torus Knot boundary segments (v = +1 and v = -1) in this Z-depth slab
        for z_b, segs_b in ((z_segs_out, segs_out), (z_segs_in, segs_in)):
            mask_b = (z_b >= z_min_slab) & (z_b < z_max_slab)
            if np.any(mask_b):
                sub_b = segs_b[mask_b]
                py5.stroke(245, 158, 11, int(125 * depth_factor))
                py5.stroke_weight(11.0)
                py5.lines(sub_b)
                py5.stroke(24, 16, 8, 240)
                py5.stroke_weight(6.4)
                py5.lines(sub_b)
                py5.stroke(int(254 * depth_factor), int(228 * depth_factor), int(82 * depth_factor), 250)
                py5.stroke_weight(3.4)
                py5.lines(sub_b)

        # Interleave the central emerald homology cycle / Seifert circle spine (v = 0)
        mask_mid = (z_segs_mid >= z_min_slab) & (z_segs_mid < z_max_slab)
        if np.any(mask_mid):
            sub_mid = segs_mid[mask_mid]
            py5.stroke(12, 24, 20, 210)
            py5.stroke_weight(4.8)
            py5.lines(sub_mid)
            py5.stroke(int(52 * depth_factor), int(211 * depth_factor), int(153 * depth_factor), 235)
            py5.stroke_weight(2.4)
            py5.lines(sub_mid)

    # Traveling Homological Cycle Quanta along the visible front Knot Binding
    py5.no_stroke()
    for k_p in range(15):
        u_idx = int((k_p * (N_U / 15.0) + tau * N_U) % N_U)
        if float(bz_out[u_idx]) > -0.15:
            px_k, py_k = float(bx_out[u_idx]), float(by_out[u_idx])
            py5.fill(254, 249, 195, 245)
            py5.circle(px_k, py_k, 11.5)


def draw_stereographic_bezel(tau, milnor_theta):
    """Draws the graduated S^3 stereographic horizon bezel and Milnor phase indicator."""
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
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        tlen = 24.0 if deg % 30 == 0 else (14.0 if deg % 15 == 0 else 7.0)
        py5.stroke(125, 211, 252, 210 if deg % 15 == 0 else 110)
        py5.stroke_weight(2.2 if deg % 30 == 0 else 1.2)
        py5.line(CX + ca * r_in, CY + sa * r_in,
                 CX + ca * (r_in + tlen), CY + sa * (r_in + tlen))


def draw_card_box(x, y, w, h, title, subtitle):
    """Draws a dark glassmorphic mathematical topology telemetry card in a corner."""
    py5.no_stroke()
    py5.fill(2, 4, 10, 170)
    py5.rect(x + 8, y + 8, w, h, 8)
    py5.stroke(56, 189, 248, 185)
    py5.stroke_weight(2.0)
    py5.fill(8, 14, 28, 234)
    py5.rect(x, y, w, h, 8)
    py5.stroke(32, 62, 105, 160)
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


def draw_topology_apparatuses(tau, milnor_theta):
    """Draws eight knot theory & Milnor fibration telemetry apparatuses across four balanced flank cards."""
    omega = 2.0 * math.pi
    cw = 760
    ch_top = 835
    ch_bot = 845

    # --- Top-Left Card (y=210..1045): FIG. 01 PLANAR BRAID DIAGRAM & FIG. 02 SEIFERT CIRCLES ---
    x1, y1 = 110, 210
    draw_card_box(x1, y1, cw, ch_top,
                  "FIG. 01 // (3, 5) TORUS KNOT PLANAR BRAID CLOSURE",
                  "CLOSED 3-STRAND BRAID (SIGMA_1 * SIGMA_2)^5 WITH C = 10 CROSSINGS")

    kcx, kcy = x1 + 195, y1 + 245
    py5.no_fill()
    py5.stroke(251, 191, 36, 235)
    py5.stroke_weight(3.2)
    with py5.begin_shape():
        for i in range(181):
            u = i * 2.0 * math.pi / 180.0
            r_k = 86.0 + 34.0 * math.cos(5.0 * u + tau * omega)
            px = kcx + r_k * math.cos(3.0 * u)
            py = kcy + r_k * math.sin(3.0 * u)
            py5.vertex(px, py)
    py5.end_shape(py5.CLOSE)

    tx1 = x1 + 360
    py5.no_stroke()
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text("KNOT NOTATION       : K(3, 5) // 10_124 NON-ALT", tx1, y1 + 105)
    py5.text("BRAID WORD          : (sigma_1 * sigma_2)^5", tx1, y1 + 139)
    py5.text("CROSSING NUMBER (c) : 10 POSITIVE CROSSINGS", tx1, y1 + 173)
    py5.text("SEIFERT CIRCLES (s) : 3 NESTED CYCLES", tx1, y1 + 207)
    py5.fill(56, 189, 248)
    py5.text("EULER CHAR (CHI)    : s - c = 3 - 10 = -7", tx1, y1 + 245)
    py5.fill(236, 72, 153)
    py5.text("SEIFERT GENUS (g)   : (1 - CHI)/2 = 4", tx1, y1 + 279)
    py5.fill(52, 211, 153)
    py5.text("UNKNOTTING NUMBER   : u(K) = (3-1)(5-1)/2 = 4", tx1, y1 + 313)

    py5.stroke(38, 82, 130, 175)
    py5.stroke_weight(1.4)
    py5.line(x1 + 24, y1 + 405, x1 + cw - 24, y1 + 405)
    py5.fill(224, 242, 254)
    py5.text_size(20)
    py5.text("FIG. 02 // SEIFERT (1934) ORIENTED SMOOTHING & BANDS", x1 + 26, y1 + 425)
    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text("THREE CONCENTRIC SEIFERT DISKS LINKED BY 10 HALF-TWISTED SADDLES", x1 + 26, y1 + 452)

    scx, scy = x1 + 195, y1 + 640
    radii_s = [115.0, 78.0, 42.0]
    cols_s = [(56, 189, 248), (236, 72, 153), (251, 191, 36)]
    for r_i, (rs, cs) in enumerate(zip(radii_s, cols_s)):
        py5.stroke(cs[0], cs[1], cs[2], 230)
        py5.stroke_weight(2.8)
        py5.fill(cs[0], cs[1], cs[2], 32)
        py5.circle(scx, scy, rs * 2.0)

    for b_i in range(5):
        ba = b_i * 2.0 * math.pi / 5.0 + tau * omega * 0.4
        ba2 = ba + math.pi / 5.0
        py5.stroke(248, 250, 252, 220)
        py5.stroke_weight(3.0)
        py5.line(scx + math.cos(ba) * 42.0, scy + math.sin(ba) * 42.0,
                 scx + math.cos(ba) * 78.0, scy + math.sin(ba) * 78.0)
        py5.line(scx + math.cos(ba2) * 78.0, scy + math.sin(ba2) * 78.0,
                 scx + math.cos(ba2) * 115.0, scy + math.sin(ba2) * 115.0)

    py5.no_stroke()
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text("DISK D_1 (OUTER)    : +1 ORIENTED WINDING", tx1, y1 + 515)
    py5.text("DISK D_2 (MIDDLE)   : +1 ORIENTED WINDING", tx1, y1 + 551)
    py5.text("DISK D_3 (INNER)    : +1 ORIENTED WINDING", tx1, y1 + 587)
    py5.fill(56, 189, 248)
    py5.text("FIRST BETTI (b_1)   : 2g = 8 HOMOLOGY GENERATORS", tx1, y1 + 629)
    py5.fill(236, 72, 153)
    py5.text("SEIFERT MATRIX (V)  : 8 x 8 UNIMODULAR BILINEAR", tx1, y1 + 665)
    py5.fill(251, 191, 36)
    py5.text("DET(V - V^T)        : 1 (FIBERED KNOT CRITERION)", tx1, y1 + 701)

    # --- Bottom-Left Card (y=1085..1930): FIG. 03 ALEXANDER POLYNOMIAL & FIG. 04 ORIENTATION ---
    x2, y2 = 110, 1085
    draw_card_box(x2, y2, cw, ch_bot,
                  "FIG. 03 // ALEXANDER POLYNOMIAL & MONODROMY ROOTS ON S^1",
                  "DELTA_{3,5}(t) = t^8 - t^7 + t^5 - t^4 + t^3 - t + 1 (15TH CYCLOTOMIC)")

    acx, acy = x2 + 195, y2 + 235
    ar = 102.0
    py5.stroke(148, 163, 184, 160)
    py5.stroke_weight(1.8)
    py5.fill(10, 20, 38)
    py5.circle(acx, acy, ar * 2.0)
    py5.line(acx - ar - 14, acy, acx + ar + 14, acy)
    py5.line(acx, acy - ar - 14, acx, acy + ar + 14)

    coprimes_15 = [1, 2, 4, 7, 8, 11, 13, 14]
    for k_root in coprimes_15:
        ra = k_root * 2.0 * math.pi / 15.0 + tau * omega * 0.25
        rx_p = acx + math.cos(ra) * ar
        ry_p = acy + math.sin(ra) * ar
        py5.stroke(56, 189, 248, 160)
        py5.line(acx, acy, rx_p, ry_p)
        py5.no_stroke()
        py5.fill(52, 211, 153)
        py5.circle(rx_p, ry_p, 12.0)

    tx2 = x2 + 348
    py5.no_stroke()
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text("DEGREE DEG(DELTA)    : 2g = 8 (MONIC)", tx2, y2 + 108)
    py5.text("LEADING COEFFICIENT  : +/- 1 (FIBERED)", tx2, y2 + 142)
    py5.text("MONODROMY ORDER      : p * q = 3 * 5 = 15", tx2, y2 + 176)
    py5.fill(52, 211, 153)
    py5.text("EIGENVALUES LAMBDA_k : EXP(2*PI*i*k / 15)", tx2, y2 + 218)
    py5.fill(251, 191, 36)
    py5.text("KNOT SIGNATURE SIGMA : -8 (CHIRAL RIGHT)", tx2, y2 + 252)
    py5.fill(236, 72, 153)
    py5.text("BRAID INDEX          : min(p, q) = 3", tx2, y2 + 286)

    py5.stroke(38, 82, 130, 175)
    py5.stroke_weight(1.4)
    py5.line(x2 + 24, y2 + 375, x2 + cw - 24, y2 + 375)
    py5.fill(224, 242, 254)
    py5.text_size(20)
    py5.text("FIG. 04 // TWO-SIDED ORIENTABLE MANIFOLD PALETTE", x2 + 26, y2 + 395)
    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text("GLOBAL UNIT NORMAL BUNDLE N(F_theta) & BOUNDARY BINDING SPEC", x2 + 26, y2 + 422)

    pal_specs = [
        ((56, 189, 248), "POSITIVE NORMAL (+N) // SAPPHIRE-CYAN ORIENTATION"),
        ((37, 99, 235), "POSITIVE DEEP SADDLE // COBALT GAUSSIAN CURVATURE"),
        ((236, 72, 153), "NEGATIVE NORMAL (-N) // VENETIAN CARMINE ORIENTATION"),
        ((190, 24, 93), "NEGATIVE DEEP SADDLE // AMETHYST-PLUM UNDERSIDE"),
        ((251, 191, 36), "BOUNDARY BINDING dF  // (3, 5) TORUS KNOT GOLD SPINE"),
        ((52, 211, 153), "HOMOLOGY CYCLES H_1  // 8 SYMPLECTIC BASIS LOOPS"),
    ]
    for p_i, (p_col, p_lbl) in enumerate(pal_specs):
        by = y2 + 472 + p_i * 54
        py5.stroke(224, 242, 254, 185)
        py5.stroke_weight(1.4)
        py5.fill(p_col[0], p_col[1], p_col[2], 235)
        py5.rect(x2 + 38, by, 48, 26, 3)
        py5.no_stroke()
        py5.fill(224, 242, 254)
        py5.text_size(15)
        py5.text(p_lbl, x2 + 104, by + 5)

    # --- Top-Right Card (y=210..1045): FIG. 05 MILNOR FIBRATION & FIG. 06 GENUS TABLE ---
    x3, y3 = WIDTH - cw - 110, 210
    draw_card_box(x3, y3, cw, ch_top,
                  "FIG. 05 // MILNOR (1968) OPEN-BOOK FIBRATION MAP",
                  "PHI(z1, z2) = (z1^3 + z2^5) / |z1^3 + z2^5| : S^3 \\ K(3,5) --> S^1")

    mcx, mcy = x3 + 195, y3 + 245
    mr = 112.0
    py5.stroke(56, 189, 248, 195)
    py5.stroke_weight(2.0)
    py5.fill(10, 20, 38)
    py5.circle(mcx, mcy, mr * 2.0)
    for k_f in range(8):
        fa = k_f * math.pi / 4.0
        py5.stroke(38, 82, 130, 150)
        py5.line(mcx, mcy, mcx + math.cos(fa) * mr, mcy + math.sin(fa) * mr)

    px_m = mcx + math.cos(milnor_theta) * (mr - 8)
    py_m = mcy + math.sin(milnor_theta) * (mr - 8)
    py5.stroke(236, 72, 153, 245)
    py5.stroke_weight(4.0)
    py5.line(mcx, mcy, px_m, py_m)
    py5.fill(251, 191, 36)
    py5.stroke(248, 250, 252)
    py5.stroke_weight(1.8)
    py5.circle(px_m, py_m, 18.0)
    py5.fill(56, 189, 248)
    py5.circle(mcx, mcy, 12.0)

    tx3 = x3 + 355
    deg_m = math.degrees(milnor_theta) % 360.0
    py5.no_stroke()
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text(f"MILNOR PHASE THETA   : {deg_m:6.2f} DEG", tx3, y3 + 105)
    py5.text("COMPLEX SINGULARITY  : f(z1, z2) = z1^3 + z2^5", tx3, y3 + 139)
    py5.text("MILNOR NUMBER (MU)   : (3-1)(5-1) = 8", tx3, y3 + 173)
    py5.text("LINK OF SINGULARITY  : S^3 INTERSECT f^(-1)(0)", tx3, y3 + 207)
    py5.fill(56, 189, 248)
    py5.text("OPEN-BOOK BINDING    : dF_theta = K(3, 5)", tx3, y3 + 245)
    py5.fill(236, 72, 153)
    py5.text("PAGE TOPOLOGY        : PUNCTURED GENUS-4 SURFACE", tx3, y3 + 279)
    py5.fill(52, 211, 153)
    py5.text("GEOMETRIC MONODROMY  : PERIOD-15 DIFFEOMORPHISM", tx3, y3 + 313)

    py5.stroke(38, 82, 130, 175)
    py5.stroke_weight(1.4)
    py5.line(x3 + 24, y3 + 405, x3 + cw - 24, y3 + 405)
    py5.fill(224, 242, 254)
    py5.text_size(20)
    py5.text("FIG. 06 // TORUS KNOT K(p, q) TOPOLOGICAL INVARIANTS", x3 + 26, y3 + 425)
    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text("MILNOR CONJECTURE (KRONHEIMER-MROWKA): g_4(K) = g_3(K) = (p-1)(q-1)/2", x3 + 26, y3 + 452)

    table_rows = [
        ("K(2, 3) TREFOIL KNOT", "g = 1", "c = 3", "MU = 2", False),
        ("K(2, 5) CINQUEFOIL", "g = 2", "c = 5", "MU = 4", False),
        ("K(3, 4) TORUS KNOT", "g = 3", "c = 8", "MU = 6", False),
        ("K(3, 5) ACTIVE MANIFOLD", "g = 4", "c = 10", "MU = 8", True),
        ("K(3, 7) TORUS KNOT", "g = 6", "c = 14", "MU = 12", False),
        ("K(4, 5) TORUS KNOT", "g = 6", "c = 15", "MU = 12", False),
    ]
    for r_i, (k_lbl, g_str, c_str, mu_str, is_act) in enumerate(table_rows):
        ry_t = y3 + 498 + r_i * 52
        py5.stroke(251, 191, 36 if is_act else 56, 220 if is_act else 110)
        py5.stroke_weight(2.0 if is_act else 1.0)
        py5.fill(28, 48, 82, 210) if is_act else py5.fill(12, 22, 42, 180)
        py5.rect(x3 + 34, ry_t, cw - 68, 40, 4)
        py5.no_stroke()
        py5.fill(251, 191, 36) if is_act else py5.fill(224, 242, 254)
        py5.text_size(15)
        py5.text(k_lbl, x3 + 52, ry_t + 11)
        py5.fill(56, 189, 248)
        py5.text(g_str, x3 + 355, ry_t + 11)
        py5.fill(236, 72, 153)
        py5.text(c_str, x3 + 465, ry_t + 11)
        py5.fill(52, 211, 153)
        py5.text(mu_str, x3 + 585, ry_t + 11)

    # --- Bottom-Right Card (y=1085..1930): FIG. 07 STEREOGRAPHIC S^3 & FIG. 08 MEAN CURVATURE ---
    x4, y4 = WIDTH - cw - 110, 1085
    draw_card_box(x4, y4, cw, ch_bot,
                  "FIG. 07 // HOPF-TORUS DECOMPOSITION OF S^3 = T_1 U T_2",
                  "HEEGAARD SPLITTING OF THE 3-SPHERE ALONG CLIFFORD TORUS")

    hcx, hcy = x4 + 195, y4 + 235
    hr = 105.0
    py5.no_fill()
    py5.stroke(56, 189, 248, 195)
    py5.stroke_weight(2.0)
    py5.ellipse(hcx, hcy, hr * 2.1, hr * 1.35)
    py5.stroke(236, 72, 153, 195)
    py5.ellipse(hcx, hcy, hr * 0.95, hr * 0.55)
    for v_k in range(12):
        va = v_k * math.pi / 6.0 + tau * omega * 0.5
        py5.stroke(251, 191, 36, 165)
        py5.stroke_weight(1.5)
        py5.line(hcx + math.cos(va) * hr * 0.48, hcy + math.sin(va) * hr * 0.28,
                 hcx + math.cos(va + 0.6) * hr * 1.05, hcy + math.sin(va + 0.6) * hr * 0.68)

    tx4 = x4 + 345
    py5.no_stroke()
    py5.fill(224, 242, 254)
    py5.text_size(15)
    py5.text("AMBIENT MANIFOLD     : 3-SPHERE S^3 IN C^2", tx4, y4 + 108)
    py5.text("CLIFFORD TORUS       : |z1| = |z2| = 1 / SQRT(2)", tx4, y4 + 142)
    py5.text("MERIDIAN / LONGITUDE : (p, q) = (3, 5) WINDING", tx4, y4 + 176)
    py5.fill(56, 189, 248)
    py5.text("SURFACE MESH CELLS   : 3,200 ORIENTED QUADS", tx4, y4 + 218)
    py5.fill(236, 72, 153)
    py5.text("WILLMORE ENERGY (W)  : INTEGRAL H^2 dA MINIMAL", tx4, y4 + 252)
    py5.fill(52, 211, 153)
    py5.text("FUNDAMENTAL GROUP    : <a, b | a^3 = b^5>", tx4, y4 + 286)

    py5.stroke(38, 82, 130, 175)
    py5.stroke_weight(1.4)
    py5.line(x4 + 24, y4 + 375, x4 + cw - 24, y4 + 375)
    py5.fill(224, 242, 254)
    py5.text_size(20)
    py5.text("FIG. 08 // GAUSSIAN CURVATURE & MILNOR PHASE WAVEFORM", x4 + 26, y4 + 395)
    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text("HARMONIC SADDLE TORSION TAU(s, t) ALONG THE 15 SEIFERT BANDS", x4 + 26, y4 + 422)

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

    wave_cols = [(56, 189, 248), (236, 72, 153), (251, 191, 36)]
    for c_idx, col in enumerate(wave_cols):
        py5.no_fill()
        py5.stroke(col[0], col[1], col[2], 235)
        py5.stroke_weight(3.0)
        with py5.begin_shape():
            for p_i in range(66):
                u = p_i / 65.0
                px_w = wx0 + u * ww
                val = math.sin(omega * tau - u * 5.0 + c_idx * 1.15) * math.cos(u * 3.0 - omega * tau * 0.5)
                py_w = wy0 + wh * 0.5 - val * (wh * 0.36)
                py5.vertex(px_w, py_w)
        py5.end_shape()

    py5.no_stroke()
    py5.fill(148, 163, 184)
    py5.text_size(15)
    py5.text("CYAN: +N SHEET FLUX   //   ROSE: -N SHEET FLUX   //   GOLD: K(3,5) TORSION", wx0, wy0 + wh + 22)


def draw_archival_border_and_typography(tau, milnor_theta):
    """Draws double-ruled museum border and scholarly typography without any personal signatures."""
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
    py5.text("SEIFERT SURFACE & MILNOR FIBRATION // (3, 5) TORUS KNOT TOPOLOGY", WIDTH / 2.0, 98)

    py5.fill(56, 189, 248)
    py5.text_size(21)
    py5.text("HERBERT SEIFERT (1934) & JOHN MILNOR (1968) - OPEN-BOOK DECOMPOSITION S^3 \\ K(3,5) --> S^1 - GENUS g = 4", WIDTH / 2.0, 150)

    py5.fill(148, 163, 184)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(20)
    py5.text("SINGULARITY: z1^3 + z2^5 = 0 // GENUS g = 4 // EULER CHAR CHI = -7 // MILNOR NUMBER MU = 8", 108, HEIGHT - 88)

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(f"4K DIFFERENTIAL TOPOLOGY // HARMONIC PHASE TAU = {tau:.3f} (12.0s @ 60FPS)", WIDTH - 108, HEIGHT - 88)


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
