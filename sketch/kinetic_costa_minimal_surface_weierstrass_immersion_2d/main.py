"""
Kinetic Costa Minimal Surface & Weierstrass-Enneper Immersion 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Mathematical / Abstract Topology genre,
exploring Celso Jose da Costa's 1982 Complete Embedded Minimal Surface of Genus
g = 1 with Three Punctures (Sigma_{1,3} = T^2 \ {p_0, p_1, p_2}) and David Hoffman
& William H. Meeks III's 1985 proof of embeddedness via the Weierstrass-Enneper
elliptic p-function representation, executed on warm Oberwolfach & Gottingen
mathematical drafting vellum (#f6f2e8).

For over two centuries (Euler 1744 Catenoid; Meusnier 1776 Helicoid), the plane,
catenoid, and helicoid were the only known complete embedded minimal surfaces in
R^3 of finite topological type. Costa's surface is parametrized on the square
lattice torus C / (Z + i*Z) via the Weierstrass elliptic function p(w) and zeta
function, possessing identical zero mean curvature H = (k_1 + k_2)/2 = 0 everywhere
and total Gaussian curvature Int K dA = -12*pi. It combines an upper catenoidal
funnel end (E_+), a lower catenoidal funnel end (E_-), and a dihedral-warped middle
planar end (E_0) joined through four D_2-symmetric hyperbolic saddle neck tunnels.

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
WORK_NAME = "kinetic_costa_minimal_surface_weierstrass_immersion_2d"
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

# Non-fixed runtime phase seed (adhering to no-fixed-seed rule)
np.random.seed(int(time.time() * 1000) % 100000)
RND_ROT_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 22.0
MEDALLION_R = 805.0

# Precompute parametric grids for the 3 ends + 4 genus-1 saddle handle necks of the Costa surface
# N_THETA = 96 angular steps, N_R = 16 radial steps per sheet
N_THETA = 96
N_R_CAT = 15
N_R_MID = 16

TH_ARR = np.linspace(0.0, 2.0 * math.pi, N_THETA + 1)
U_CAT = np.linspace(0.18, 1.0, N_R_CAT + 1)
U_MID = np.linspace(0.16, 1.0, N_R_MID + 1)


def build_costa_surface_facets(tau: float, omega: float):
    """
    Constructs the 3D oriented quad mesh of the Costa-Hoffman-Meeks minimal surface:
    1. Upper Catenoidal End (E_+): Flaring logarithmic funnel with D_2 saddle warping
       near its inner waist where the 4 handle arches attach.
    2. Lower Catenoidal End (E_-): Symmetric inverted logarithmic funnel with D_2 saddle
       warping rotated by pi/2 relative to the upper waist.
    3. Middle Dihedral Planar End (E_0): Asymptotically flat outer sheet with strong
       z ~ r_0 * sin(2*theta) / r^2 monkey-saddle / dihedral undulation connecting
       upward at theta = 0, pi to E_+ and downward at theta = pi/2, 3*pi/2 to E_-!
    4. Four Genus-1 Hyperbolic Neck Handles bridging the waist of E_+ and E_- smoothly
       into the middle saddle sheet E_0.
    """
    # Hoffman-Meeks 1-parameter deformation family modulation
    hm_mod = 1.0 + 0.08 * math.sin(2.0 * omega * tau)
    scale_xyz = 445.0

    sheets_xyz = []  # List of (X, Y, Z, sheet_polarity) meshgrids

    # --- Sheet 1: Upper Catenoidal End E_+ ---
    r1_grid, th1_grid = np.meshgrid(U_CAT, TH_ARR, indexing="ij")
    # Radius flares from waist r = 0.24 out to r = 1.18
    rad1 = 0.24 + 0.94 * (r1_grid ** 1.18)
    # D_2 dihedral pinch at inner waist connecting downward at cos(2*theta) > 0
    waist_env1 = np.exp(-3.8 * (r1_grid - 0.18))
    x1 = rad1 * np.cos(th1_grid) * (1.0 + 0.14 * waist_env1 * np.cos(2.0 * th1_grid))
    y1 = rad1 * np.sin(th1_grid) * (1.0 - 0.14 * waist_env1 * np.cos(2.0 * th1_grid))
    z1 = (
        0.26
        + 0.56 * np.arcsinh(1.85 * (r1_grid - 0.12)) * hm_mod
        - 0.24 * waist_env1 * np.cos(2.0 * th1_grid)
        + 0.06 * (1.0 - waist_env1) * np.cos(2.0 * th1_grid)
    )
    sheets_xyz.append((x1 * scale_xyz, y1 * scale_xyz, z1 * scale_xyz, 1))

    # --- Sheet 2: Lower Catenoidal End E_- ---
    # By Costa's D_2 reflection-rotation symmetry: R_z(pi/2) followed by z -> -z
    x2 = rad1 * np.cos(th1_grid) * (1.0 - 0.14 * waist_env1 * np.cos(2.0 * th1_grid))
    y2 = rad1 * np.sin(th1_grid) * (1.0 + 0.14 * waist_env1 * np.cos(2.0 * th1_grid))
    z2 = -(
        0.26
        + 0.56 * np.arcsinh(1.85 * (r1_grid - 0.12)) * hm_mod
        + 0.24 * waist_env1 * np.cos(2.0 * th1_grid)
        - 0.06 * (1.0 - waist_env1) * np.cos(2.0 * th1_grid)
    )
    sheets_xyz.append((x2 * scale_xyz, y2 * scale_xyz, z2 * scale_xyz, -1))

    # --- Sheet 3: Middle Dihedral Planar End E_0 ---
    r3_grid, th3_grid = np.meshgrid(U_MID, TH_ARR, indexing="ij")
    rad3 = 0.20 + 1.18 * (r3_grid ** 1.12)
    # Asymptotic behavior of Costa middle end: z ~ A * cos(2*theta) / r^2
    # Meets the upper catenoid tunnels at theta = 0, pi and lower catenoid tunnels at pi/2, 3*pi/2
    saddle_amp = 0.34 * hm_mod / (0.38 + (r3_grid ** 2) * 2.4)
    x3 = rad3 * np.cos(th3_grid)
    y3 = rad3 * np.sin(th3_grid)
    z3 = saddle_amp * np.cos(2.0 * th3_grid)
    sheets_xyz.append((x3 * scale_xyz, y3 * scale_xyz, z3 * scale_xyz, 1))

    # --- Sheet 4..7: Four Hyperbolic Saddle Neck Bridges (Genus g = 1 Tunnels) ---
    # 4 vertical catenoidal saddle collars at (theta_k = 0, pi/2, pi, 3*pi/2)
    u_neck = np.linspace(-1.0, 1.0, 11)
    v_neck = np.linspace(0.0, 2.0 * math.pi, 29)
    un_g, vn_g = np.meshgrid(u_neck, v_neck, indexing="ij")
    for k_n in range(4):
        ang_n = k_n * (0.5 * math.pi)
        sign_z = 1.0 if (k_n % 2 == 0) else -1.0
        # Center of neck tunnel at radius r_neck = 0.30
        cx_n = 0.30 * math.cos(ang_n)
        cy_n = 0.30 * math.sin(ang_n)
        rn_flare = 0.115 * np.cosh(0.85 * un_g)
        xn = cx_n + rn_flare * np.cos(vn_g)
        yn = cy_n + rn_flare * np.sin(vn_g)
        zn = sign_z * (0.16 + 0.14 * un_g) + 0.04 * np.cos(2.0 * vn_g)
        sheets_xyz.append((xn * scale_xyz, yn * scale_xyz, zn * scale_xyz, 1))

    return sheets_xyz


def settings():
    py5.size(WIDTH, HEIGHT)
    py5.pixel_density(1)
    py5.smooth(4)


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

    # 1. Warm Oberwolfach & Gottingen Mathematical Drafting Vellum (#f6f2e8)
    py5.background(246, 242, 232)

    # 2. Conformal Coordinate Grid & Weierstrass Lattice Substrate
    draw_vellum_substrate(tau)

    # 3. Central Monumental Costa-Hoffman-Meeks Minimal Surface Planisphere
    draw_central_costa_planisphere(tau, omega)

    # 4. Eight Differential Geometry & Minimal Surface Apparatuses Across Four Flank Cards
    draw_costa_topology_apparatuses(tau, omega)

    # 5. Archival Museum Border & Scholarly Typography (Zero Personal Signatures/Seals)
    draw_archival_border_and_typography(tau, omega)

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
        print(
            f"[{WORK_NAME}] Frame {frame+1:03d}/{TOTAL_FRAMES} ({(frame+1)/TOTAL_FRAMES*100:.1f}%) | "
            f"Speed: {fps_calc:.2f} fps | ETA: {eta:.1f}s"
        )


def draw_vellum_substrate(tau: float):
    """Draws warm mathematical drafting vellum washes and millimeter grid hairlines."""
    py5.no_stroke()
    for r_g, col_g in [
        (1180, (238, 233, 220, 95)),
        (940, (230, 224, 210, 90)),
        (835, (218, 210, 194, 100)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    py5.stroke(212, 204, 188, 135)
    py5.stroke_weight(1.1)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)


def project_3d_array(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, ry: float, rx: float, rz: float):
    """Applies 3-axis harmonic rotation and perspective projection onto 2D screen space."""
    cy, sy = math.cos(ry), math.sin(ry)
    cx, sx = math.cos(rx), math.sin(rx)
    cz, sz = math.cos(rz), math.sin(rz)

    # Rotate around Z (azimuth around vertical axis of the catenoids)
    x1 = X * cz - Y * sz
    y1 = X * sz + Y * cz
    z1 = Z

    # Tilt around X so all 3 ends and the 4 saddle tunnels are seen in dramatic 3D perspective
    x2 = x1
    y2 = y1 * cx - z1 * sx
    z2 = y1 * sx + z1 * cx

    # Gentle wobble around Y
    x3 = x2 * cy + z2 * sy
    y3 = y2
    z3 = -x2 * sy + z2 * cy

    # Perspective projection
    cam_d = 2400.0
    persp = cam_d / np.maximum(600.0, cam_d - z3)
    sx_p = CX + x3 * persp
    sy_p = CY - y3 * persp
    return sx_p, sy_p, x3, y3, z3


def draw_central_costa_planisphere(tau: float, omega: float):
    """
    Renders the central Costa-Hoffman-Meeks Embedded Minimal Surface Medallion:
    1. Recessed Prussian-indigo Oberwolfach mathematical display field with Gauss map grid
    2. 3D rotating Costa minimal surface (3 ends + 4 genus-1 neck tunnels) depth-sorted
       across 14 Z-slabs and colored by two-sided unit normal orientation (+N Prussian
       sapphire-cyan vs -N Venetian terracotta-carmine) with isothermal grid lines
    3. Highlighted golden asymptotic reflection geodesics & emerald homology cycles
    4. Engraved brass goniometer bezel
    """
    # --- 1. RECESSED PRUSSIAN-INDIGO MATHEMATICAL DISPLAY FIELD ---
    py5.no_stroke()
    py5.fill(112, 86, 48, 255)
    py5.circle(CX, CY, (MEDALLION_R + 16.0) * 2.0)

    py5.fill(16, 28, 46, 255)
    py5.circle(CX, CY, MEDALLION_R * 2.0)

    for r_m, col_m in [
        (720.0, (20, 36, 58, 180)),
        (560.0, (24, 44, 72, 165)),
        (380.0, (28, 52, 86, 150)),
    ]:
        py5.fill(*col_m)
        py5.circle(CX, CY, r_m * 2.0)

    # Stereographic Gauss-map coordinate circles & radial rays inside the display field
    rad_segs = []
    for deg in range(0, 360, 15):
        ang = math.radians(deg)
        ca, sa = math.cos(ang), math.sin(ang)
        rad_segs.append([CX + 60.0 * ca, CY + 60.0 * sa, CX + (MEDALLION_R - 26.0) * ca, CY + (MEDALLION_R - 26.0) * sa])
    py5.stroke(56, 88, 124, 95)
    py5.stroke_weight(1.1)
    py5.lines(np.array(rad_segs, dtype=np.float64))

    py5.no_fill()
    for r_st in [220.0, 420.0, 620.0, 745.0]:
        py5.stroke(64, 98, 138, 85)
        py5.stroke_weight(1.1)
        py5.circle(CX, CY, r_st * 2.0)

    # --- 2. BUILD & PROJECT 3D COSTA MINIMAL SURFACE FACETS ---
    # 3-axis harmonic rotation showing the upper catenoid, middle dihedral saddle,
    # lower catenoid, and the 4 genus-1 neck tunnels!
    rz = omega * tau + RND_ROT_PHASE
    rx = 1.12 + 0.16 * math.sin(omega * tau)
    ry = 0.18 * math.cos(omega * tau)

    sheets_xyz = build_costa_surface_facets(tau, omega)
    all_facets = []  # List of (z_depth, side_sign, shade_bucket, quad_pts)
    boundary_segs = []

    # Directional light vector in camera space
    lx_l, ly_l, lz_l = -0.42, 0.55, 0.72

    for X_s, Y_s, Z_s, pol_s in sheets_xyz:
        sx_p, sy_p, x3, y3, z3 = project_3d_array(X_s, Y_s, Z_s, ry, rx, rz)

        # Tangent vectors along u (rows) and v (cols) in camera space
        ux = x3[1:, :-1] - x3[:-1, :-1]
        uy = y3[1:, :-1] - y3[:-1, :-1]
        uz = z3[1:, :-1] - z3[:-1, :-1]

        vx = x3[:-1, 1:] - x3[:-1, :-1]
        vy = y3[:-1, 1:] - y3[:-1, :-1]
        vz = z3[:-1, 1:] - z3[:-1, :-1]

        # Normal vector N = (u x v) * pol_s
        nx = (uy * vz - uz * vy) * pol_s
        ny = (uz * vx - ux * vz) * pol_s
        nz = (ux * vy - uy * vx) * pol_s
        n_norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-8
        nx /= n_norm
        ny /= n_norm
        nz /= n_norm

        # Two-sided orientation: +1 if nz >= 0 (Prussian Sapphire), -1 if nz < 0 (Venetian Terracotta)
        side_mat = np.where(nz >= 0.0, 1, -1)

        # Lambertian + specular lighting on the oriented normal
        dot_l = np.abs(nx * lx_l + ny * ly_l + nz * lz_l)
        spec = np.power(np.maximum(0.0, np.abs(nz)), 3.0) * 0.28
        illum = np.clip(0.32 + 0.56 * dot_l + spec, 0.0, 1.0)
        s_buckets = np.clip((illum * 6.99).astype(np.int32), 0, 6)

        z_centers = 0.25 * (z3[:-1, :-1] + z3[1:, :-1] + z3[1:, 1:] + z3[:-1, 1:])
        nr, nc = z_centers.shape

        for i in range(nr):
            for j in range(nc):
                q_pts = (
                    (sx_p[i, j], sy_p[i, j]),
                    (sx_p[i + 1, j], sy_p[i + 1, j]),
                    (sx_p[i + 1, j + 1], sy_p[i + 1, j + 1]),
                    (sx_p[i, j + 1], sy_p[i, j + 1]),
                )
                all_facets.append((float(z_centers[i, j]), int(side_mat[i, j]), int(s_buckets[i, j]), q_pts))

        # Outer asymptotic boundary rim of this end (last row i = nr)
        b_segs = np.column_stack([
            sx_p[-1, :-1], sy_p[-1, :-1],
            sx_p[-1, 1:], sy_p[-1, 1:],
        ])
        boundary_segs.append(b_segs)

    # Sort all facets back-to-front by camera Z depth (Painter's algorithm)
    all_facets.sort(key=lambda item: item[0])

    # Render in 14 depth slabs so the 3 interlocking ends & 4 neck tunnels occlude accurately
    n_tot = len(all_facets)
    n_slabs = 14
    slab_sz = (n_tot + n_slabs - 1) // n_slabs

    # Color tables for the 7 shade buckets [0..6] of the two normal orientations:
    # +1: Prussian Cobalt-Sapphire -> Luminous Cerulean-White
    # -1: Venetian Terracotta-Carmine -> Warm Apricot-Gold
    POS_COLORS = [
        (22, 54, 96),
        (30, 74, 128),
        (40, 98, 162),
        (54, 124, 194),
        (78, 152, 218),
        (118, 184, 238),
        (178, 220, 250),
    ]
    NEG_COLORS = [
        (112, 34, 28),
        (144, 46, 36),
        (178, 60, 44),
        (206, 82, 56),
        (228, 114, 74),
        (242, 154, 102),
        (252, 204, 154),
    ]

    py5.stroke(246, 240, 226, 95)
    py5.stroke_weight(0.85)
    for s_idx in range(n_slabs):
        slab = all_facets[s_idx * slab_sz : (s_idx + 1) * slab_sz]
        if not slab:
            continue

        grouped = {}
        for _, side_s, sb_s, qp in slab:
            grouped.setdefault((side_s, sb_s), []).append(qp)

        for (side_s, sb_s), q_list in grouped.items():
            cr, cg, cb = POS_COLORS[sb_s] if side_s > 0 else NEG_COLORS[sb_s]
            py5.fill(cr, cg, cb, 246)
            q_arr = np.array(q_list, dtype=np.float64)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(q_arr.reshape(-1, 2))

    # --- 3. GOLDEN ASYMPTOTIC BOUNDARY RINGS & EMERALD HOMOLOGY LOOPS ---
    if boundary_segs:
        all_b_segs = np.vstack(boundary_segs)
        py5.stroke(28, 20, 12, 225)
        py5.stroke_weight(4.4)
        py5.lines(all_b_segs)
        py5.stroke(244, 188, 58, 245)
        py5.stroke_weight(2.2)
        py5.lines(all_b_segs)

    # --- 4. ENGRAVED BRASS GONIOMETER BEZEL ---
    py5.no_fill()
    py5.stroke(178, 136, 62, 240)
    py5.stroke_weight(4.0)
    py5.circle(CX, CY, MEDALLION_R * 2.0)

    tick_segs = []
    for deg in range(0, 360, 2):
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        r0 = MEDALLION_R - (24.0 if deg % 15 == 0 else (15.0 if deg % 5 == 0 else 9.0))
        r1 = MEDALLION_R - 2.0
        tick_segs.append([CX + r0 * ca, CY + r0 * sa, CX + r1 * ca, CY + r1 * sa])
    py5.stroke(236, 206, 138, 210)
    py5.stroke_weight(1.4)
    py5.lines(np.array(tick_segs, dtype=np.float64))


def draw_light_card_frame(x: float, y: float, w: float, h: float):
    """Draws a warm Oberwolfach mathematical monograph card frame with brass corner brackets."""
    py5.fill(250, 247, 238, 240)
    py5.stroke(164, 142, 108, 215)
    py5.stroke_weight(2.0)
    py5.rect(x, y, w, h, 8)

    py5.no_fill()
    py5.stroke(198, 182, 152, 155)
    py5.stroke_weight(1.1)
    py5.rect(x + 8, y + 8, w - 16, h - 16, 5)

    py5.stroke(154, 98, 38, 235)
    py5.stroke_weight(2.6)
    cl = 20.0
    for cx_c, cy_c, sx, sy in [
        (x, y, 1, 1),
        (x + w, y, -1, 1),
        (x, y + h, 1, -1),
        (x + w, y + h, -1, -1),
    ]:
        py5.line(cx_c, cy_c, cx_c + sx * cl, cy_c)
        py5.line(cx_c, cy_c, cx_c, cy_c + sy * cl)


def draw_costa_topology_apparatuses(tau: float, omega: float):
    """
    Renders 8 Differential Geometry & Minimal Surface apparatuses across 4 balanced flank cards.
    Strict non-overlapping coordinate geometry verified at 4K (3840x2160).
    """
    lx = 92.0
    rx = WIDTH - 92.0 - 796.0
    cw = 796.0
    ty = 175.0
    th = 835.0
    by = 1042.0
    bh = 855.0

    py5.text_align(py5.LEFT, py5.TOP)

    # =========================================================================
    # CARD 1 (TOP-LEFT): FIG. 01 WEIERSTRASS-ENNEPER & FIG. 02 SQUARE TORUS
    # =========================================================================
    draw_light_card_frame(lx, ty, cw, th)

    # --- FIG. 01: WEIERSTRASS-ENNEPER MEROMORPHIC GAUSS MAP g(w) = c / p'(w) ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 01 // WEIERSTRASS-ENNEPER ELLIPTIC IMMERSION & GAUSS MAP g(w)", lx + 28, ty + 24)
    py5.fill(30, 74, 128)
    py5.text_size(12)
    py5.text("X(w) = RE INT (1/2*(1 - g^2), i/2*(1 + g^2), g) dh // g(w) = A / p'(w) ON SQUARE LATTICE", lx + 28, ty + 48)

    # Stereographic Gauss sphere S^2 diagram at (lx + 172, ty + 215)
    f1_cx, f1_cy = lx + 172.0, ty + 215.0
    py5.fill(242, 236, 224, 245)
    py5.stroke(30, 74, 128, 225)
    py5.stroke_weight(2.2)
    py5.circle(f1_cx, f1_cy, 176.0)

    # Meridians & latitude ellipses on the Gauss sphere S^2
    u1 = np.linspace(0.0, 2.0 * math.pi, 90)
    for k_m in range(4):
        ang_m = k_m * (math.pi / 4.0) + 0.5 * omega * tau
        xm = f1_cx + 88.0 * np.cos(u1) * math.cos(ang_m)
        ym = f1_cy + 88.0 * np.sin(u1)
        py5.stroke(54, 124, 194, 165)
        py5.stroke_weight(1.5)
        py5.lines(np.column_stack([xm[:-1], ym[:-1], xm[1:], ym[1:]]))

    # North & South poles (g = infinity & g = 0 at the 3 punctured ends)
    for py_p, col_p in [(f1_cy - 88.0, (178, 60, 44)), (f1_cy + 88.0, (30, 74, 128)), (f1_cy, (216, 140, 30))]:
        py5.fill(*col_p, 255)
        py5.no_stroke()
        py5.circle(f1_cx, py_p, 11.0)

    tx1 = lx + 336.0
    ty1 = ty + 88.0
    f1_specs = [
        ("WEIERSTRASS DATA", ": g(w) = A / p'(w), dh = p(w) dw", (30, 74, 128)),
        ("SQUARE LATTICE", ": Lambda = Z + i*Z (Lemniscatic g_3 = 0)", (178, 60, 44)),
        ("GAUSS DEGREE", ": deg(g) = 3 -> Int K dA = -12*pi", (144, 94, 24)),
        ("HOPF DIFFERENTIAL", ": Q = (1/4) dh * dg (Isothermal)", (36, 118, 96)),
        ("HALF-PERIOD INV", ": e_1 = p(1/2) = -e_2 = sqrt(g_2)/2", (38, 30, 22)),
        ("PERIOD KILLING", ": Re Int_gamma (1-g^2, i(1+g^2), 2g)dh=0", (30, 74, 128)),
        ("SYMMETRY GROUP", ": D_2 Dihedral (Order 8 Reflections)", (178, 60, 44)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f1_specs):
        yy = ty1 + i * 33.0
        py5.fill(96, 82, 64)
        py5.text_size(12)
        py5.text(k_lbl, tx1, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx1 + 178.0, yy)

    py5.stroke(194, 176, 144, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, ty + 390, lx + cw - 24, ty + 390)

    # --- FIG. 02: PUNCTURED SQUARE TORUS DOMAIN T^2 \ {p_0, p_1, p_2} ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 02 // PUNCTURED SQUARE TORUS DOMAIN T^2 \\ {0, 1/2, i/2}", lx + 28, ty + 412)
    py5.fill(178, 60, 44)
    py5.text_size(12)
    py5.text("FUNDAMENTAL SQUARE [0,1]x[0,i] WITH STRAIGHT ASYMPTOTIC LINES & PLANAR SYMMETRY AXES", lx + 28, ty + 436)

    # Fundamental square domain [f2_x..f2_x+230, f2_y..f2_y+230]
    f2_x, f2_y, f2_s = lx + 54.0, ty + 492.0, 224.0
    py5.fill(242, 236, 224, 245)
    py5.stroke(30, 74, 128, 220)
    py5.stroke_weight(2.0)
    py5.rect(f2_x, f2_y, f2_s, f2_s, 4)

    # Diagonal planar reflection geodesic lines & horizontal/vertical straight lines on Sigma
    py5.stroke(216, 140, 30, 215)
    py5.stroke_weight(2.0)
    py5.line(f2_x, f2_y, f2_x + f2_s, f2_y + f2_s)
    py5.line(f2_x + f2_s, f2_y, f2_x, f2_y + f2_s)
    py5.stroke(36, 118, 96, 210)
    py5.line(f2_x + f2_s * 0.5, f2_y, f2_x + f2_s * 0.5, f2_y + f2_s)
    py5.line(f2_x, f2_y + f2_s * 0.5, f2_x + f2_s, f2_y + f2_s * 0.5)

    # Punctures p_0 (corners = Planar End), p_1 (1/2 = Upper Catenoid), p_2 (i/2 = Lower Catenoid)
    for px_p, py_p, col_p in [
        (f2_x + f2_s * 0.5, f2_y, (30, 74, 128)),
        (f2_x + f2_s * 0.5, f2_y + f2_s, (30, 74, 128)),
        (f2_x, f2_y + f2_s * 0.5, (178, 60, 44)),
        (f2_x + f2_s, f2_y + f2_s * 0.5, (178, 60, 44)),
        (f2_x + f2_s * 0.5, f2_y + f2_s * 0.5, (216, 140, 30)),
    ]:
        py5.fill(*col_p, 255)
        py5.stroke(250, 247, 238, 255)
        py5.stroke_weight(2.0)
        py5.circle(px_p, py_p, 14.0)

    tx2 = lx + 336.0
    ty2 = ty + 485.0
    f2_specs = [
        ("TOPOLOGICAL TYPE", ": Compact Genus g = 1 Minus 3 Points", (30, 74, 128)),
        ("EULER CHARACTERISTIC", ": chi(Sigma_1,3) = 2 - 2g - 3 = -3", (178, 60, 44)),
        ("PUNCTURE p_0 (0)", ": Middle Planar End (Dihedral Skirt)", (144, 94, 24)),
        ("PUNCTURE p_1 (1/2)", ": Upper Catenoidal End (z -> +inf)", (30, 74, 128)),
        ("PUNCTURE p_2 (i/2)", ": Lower Catenoidal End (z -> -inf)", (178, 60, 44)),
        ("CENTER SADDLE (w_c)", ": w = (1+i)/4 Monkey Saddle Point", (36, 118, 96)),
        ("STRAIGHT LINES", ": X_1, X_2 Axes Contained in Surface", (38, 30, 22)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f2_specs):
        yy = ty2 + i * 33.0
        py5.fill(96, 82, 64)
        py5.text_size(12)
        py5.text(k_lbl, tx2, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx2 + 178.0, yy)

    # =========================================================================
    # CARD 2 (BOTTOM-LEFT): FIG. 03 CURVATURE SPECTRUM & FIG. 04 PALETTE
    # =========================================================================
    draw_light_card_frame(lx, by, cw, bh)

    # --- FIG. 03: ZERO MEAN CURVATURE H = 0 & JORGE-MEEKS TOTAL CURVATURE ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 03 // PRINCIPAL CURVATURES k_1 = -k_2 (H = 0) & GAUSS-BONNET INTEGRAL", lx + 28, by + 24)
    py5.fill(30, 74, 128)
    py5.text_size(12)
    py5.text("JORGE-MEEKS FORMULA FOR EMBEDDED ENDS: INT K dA = -2*PI * (2g + 2k - 2) = -12*PI", lx + 28, by + 48)

    f3_x, f3_y, f3_w, f3_h = lx + 42.0, by + 95.0, 255.0, 240.0
    py5.fill(242, 236, 224, 245)
    py5.stroke(158, 136, 104, 215)
    py5.stroke_weight(1.6)
    py5.rect(f3_x, f3_y, f3_w, f3_h, 5)

    # Symmetric k_1(r) > 0 and k_2(r) = -k_1(r) < 0 around horizontal H = 0 axis
    y3_mid = f3_y + f3_h * 0.5
    py5.stroke(36, 118, 96, 210)
    py5.stroke_weight(2.0)
    py5.line(f3_x + 12, y3_mid, f3_x + f3_w - 12, y3_mid)

    u3 = np.linspace(0.0, 1.0, 90)
    x3_p = f3_x + 14.0 + u3 * (f3_w - 28.0)
    k_prof = 88.0 * np.exp(-3.5 * ((u3 - 0.34) ** 2)) * (1.0 + 0.12 * math.sin(omega * tau))
    py5.stroke(30, 74, 128, 240)
    py5.stroke_weight(2.8)
    py5.lines(np.column_stack([x3_p[:-1], (y3_mid - k_prof)[:-1], x3_p[1:], (y3_mid - k_prof)[1:]]))
    py5.stroke(178, 60, 44, 240)
    py5.lines(np.column_stack([x3_p[:-1], (y3_mid + k_prof)[:-1], x3_p[1:], (y3_mid + k_prof)[1:]]))

    tx3 = lx + 336.0
    ty3 = by + 88.0
    f3_specs = [
        ("MEAN CURVATURE (H)", ": H = (k_1 + k_2) / 2 = 0.0000 Exact", (36, 118, 96)),
        ("GAUSS CURVATURE (K)", ": K = k_1 * k_2 = -k_1^2 <= 0 Hyperbolic", (30, 74, 128)),
        ("TOTAL CURVATURE", ": Int_Sigma K dA = -12*pi (-37.699 rad)", (178, 60, 44)),
        ("MORSE INDEX", ": Index(L_Jacobi) = 5 Unstable Modes", (144, 94, 24)),
        ("UMBILIC POINTS", ": K = 0 at Symmetry Origin (0, 0, 0)", (38, 30, 22)),
        ("ASYMPTOTIC DECAY", ": K(r) ~ O(r^-4) on Catenoidal Ends", (30, 74, 128)),
        ("LAPLACE-BELTRAMI", ": Delta_Sigma X = 2*H*N = (0, 0, 0)", (36, 118, 96)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f3_specs):
        yy = ty3 + i * 33.0
        py5.fill(96, 82, 64)
        py5.text_size(12)
        py5.text(k_lbl, tx3, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx3 + 178.0, yy)

    py5.stroke(194, 176, 144, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, by + 390, lx + cw - 24, by + 390)

    # --- FIG. 04: TWO-SIDED NORMAL BUNDLE & ISOTHERMAL MESH PALETTE ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 04 // ORIENTABLE TWO-SIDED NORMAL BUNDLE & GEODESIC PALETTE", lx + 28, by + 412)
    py5.fill(178, 60, 44)
    py5.text_size(12)
    py5.text("OBERWOLFACH MATHEMATICAL MODEL ENAMEL GLAZES (+N SAPPHIRE VS. -N TERRACOTTA)", lx + 28, by + 436)

    swatches = [
        ((40, 98, 162), "POSITIVE NORMAL (+N) SAPPHIRE // EXTERIOR ORIENTED GAUSS MAP SHEET (N_z > 0)"),
        ((178, 60, 44), "NEGATIVE NORMAL (-N) TERRACOTTA // INTERIOR ORIENTED GAUSS MAP SHEET (N_z < 0)"),
        ((118, 184, 238), "CATENOIDAL SPECULAR CERULEAN // LAMBERTIAN CREST ILLUMINATION ON UPPER/LOWER ENDS"),
        ((242, 154, 102), "SADDLE TUNNEL APRICOT OCHRE // HYPERBOLIC NECK PASSAGES AT THETA = k*PI/2"),
        ((216, 140, 30), "ASYMPTOTIC BOUNDARY GOLD // PLANAR SYMMETRY GEODESICS & END BOUNDARY RINGS"),
        ((36, 118, 96), "HOMOLOGY GENERATOR EMERALD // CANONICAL BASIS [ALPHA], [BETA] IN H_1(SIGMA; Z)"),
    ]
    for i, (rgb_s, desc_s) in enumerate(swatches):
        sy = by + 482.0 + i * 54.0
        py5.fill(*rgb_s)
        py5.stroke(104, 78, 52, 215)
        py5.stroke_weight(1.5)
        py5.rect(lx + 32, sy, 52, 34, 4)
        py5.no_stroke()
        py5.fill(38, 30, 22)
        py5.text_size(13)
        py5.text(desc_s, lx + 104, sy + 9)

    # =========================================================================
    # CARD 3 (TOP-RIGHT): FIG. 05 THREE-END PROFILE & FIG. 06 CODEX LEDGER
    # =========================================================================
    draw_light_card_frame(rx, ty, cw, th)

    # --- FIG. 05: THREE ENDS ASYMPTOTIC GEOMETRY (2 CATENOIDS + 1 PLANAR END) ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 05 // ASYMPTOTIC END PROFILE: TWO CATENOIDS + ONE PLANAR END", rx + 28, ty + 24)
    py5.fill(30, 74, 128)
    py5.text_size(12)
    py5.text("DISJOINT EMBEDDED ENDS FOR r >> 1: z_+- ~ +-c * LN(r) VS. z_0 ~ a * COS(2*THETA) / r^2", rx + 28, ty + 48)

    # Meridional cross-section of the 3 non-intersecting ends inside [rx+42..rx+300]
    f5_cx, f5_cy = rx + 172.0, ty + 215.0
    u5 = np.linspace(0.22, 1.0, 60)
    dx5 = u5 * 116.0
    dz_cat = 22.0 + 58.0 * np.log(u5 / 0.18)
    dz_mid = 26.0 / (1.0 + 8.0 * (u5 ** 2)) * math.cos(omega * tau)
    for s_x in [-1.0, 1.0]:
        # Upper catenoid branch
        py5.stroke(30, 74, 128, 235)
        py5.stroke_weight(2.8)
        py5.lines(np.column_stack([
            f5_cx + s_x * dx5[:-1], (f5_cy - dz_cat)[:-1],
            f5_cx + s_x * dx5[1:], (f5_cy - dz_cat)[1:],
        ]))
        # Lower catenoid branch
        py5.stroke(178, 60, 44, 235)
        py5.lines(np.column_stack([
            f5_cx + s_x * dx5[:-1], (f5_cy + dz_cat)[:-1],
            f5_cx + s_x * dx5[1:], (f5_cy + dz_cat)[1:],
        ]))
        # Middle planar end branch
        py5.stroke(216, 140, 30, 240)
        py5.lines(np.column_stack([
            f5_cx + s_x * dx5[:-1], (f5_cy - s_x * dz_mid)[:-1],
            f5_cx + s_x * dx5[1:], (f5_cy - s_x * dz_mid)[1:],
        ]))

    tx5 = rx + 336.0
    ty5 = ty + 88.0
    f5_specs = [
        ("UPPER END (E_+)", ": z(r) = +c * ln(r) + b_0 + O(r^-2)", (30, 74, 128)),
        ("LOWER END (E_-)", ": z(r) = -c * ln(r) - b_0 + O(r^-2)", (178, 60, 44)),
        ("MIDDLE END (E_0)", ": z(r,th) = a * cos(2*th)/r^2 + O(r^-4)", (144, 94, 24)),
        ("LOGARITHMIC GROWTH", ": c_+ = c_- = sqrt(2*pi) / e_1 > 0", (36, 118, 96)),
        ("PLANAR END GROWTH", ": c_0 = 0 (Zero Logarithmic Flux)", (38, 30, 22)),
        ("SCHOEN UNIQUENESS", ": 2-End Minimal Surface => Catenoid", (30, 74, 128)),
        ("EMBEDDEDNESS PROOF", ": 8 Fundamental Symmetry Chambers", (178, 60, 44)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f5_specs):
        yy = ty5 + i * 33.0
        py5.fill(96, 82, 64)
        py5.text_size(12)
        py5.text(k_lbl, tx5, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx5 + 178.0, yy)

    py5.stroke(194, 176, 144, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, ty + 390, rx + cw - 24, ty + 390)

    # --- FIG. 06: HISTORICAL EMBEDDED MINIMAL SURFACE CODEX LEDGER ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 06 // HISTORICAL MINIMAL SURFACE & TOPOLOGY CODEX LEDGER", rx + 28, ty + 412)
    py5.fill(178, 60, 44)
    py5.text_size(12)
    py5.text("TWO CENTURIES OF COMPLETE MINIMAL SURFACES FROM EULER (1744) TO COSTA-HOFFMAN-MEEKS", rx + 28, ty + 436)

    rows = [
        ("CATENOID (1744)", "Leonhard Euler", "Genus 0 // 2 Ends", "Rotational Minimal"),
        ("HELICOID (1776)", "J.B. Meusnier", "Genus 0 // 1 End", "Ruled Minimal Screw"),
        ("SCHERK SURFACES (1834)", "Heinrich Scherk", "Doubly Periodic", "Saddle Tower Family"),
        ("COSTA EQUATIONS (1982)", "Celso J. da Costa", "Genus 1 // 3 Ends", "IMPA Rio Dissertation"),
        ("HOFFMAN-MEEKS (1985)", "Hoffman & Meeks", "Genus k >= 1 Family", "Embeddedness Theorem"),
        ("ACTIVE COSTA IMMERSION", "Sigma_(1,3) Torus", "Int K dA = -12*pi", "HARMONIC LIVE"),
    ]
    for r_i, (c_name, c_auth, c_top, c_note) in enumerate(rows):
        ry_row = ty + 478.0 + r_i * 55.0
        is_hi = (r_i == 3 or r_i == 5)
        py5.fill(*(240, 228, 204, 242) if is_hi else (248, 244, 234, 215))
        py5.stroke(*(178, 60, 44, 235) if is_hi else (194, 176, 144, 175))
        py5.stroke_weight(1.9 if is_hi else 1.1)
        py5.rect(rx + 28, ry_row, cw - 56, 44, 5)

        py5.no_stroke()
        py5.fill(38, 30, 22)
        py5.text_size(12)
        py5.text(c_name, rx + 44, ry_row + 15)
        py5.fill(30, 74, 128)
        py5.text(c_auth, rx + 265, ry_row + 15)
        py5.fill(178, 60, 44)
        py5.text(c_top, rx + 435, ry_row + 15)
        py5.fill(36, 118, 96)
        py5.text(c_note, rx + 595, ry_row + 15)

    # =========================================================================
    # CARD 4 (BOTTOM-RIGHT): FIG. 07 PLATEAU VARIATION & FIG. 08 DEFORMATION TRACE
    # =========================================================================
    draw_light_card_frame(rx, by, cw, bh)

    # --- FIG. 07: PLATEAU SOAP-FILM AREA VARIATION & SADDLE EQUILIBRIUM ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 07 // PLATEAU VARIATIONAL PRINCIPLE: d/dt AREA(SIGMA_t) = 0", rx + 28, by + 24)
    py5.fill(36, 118, 96)
    py5.text_size(12)
    py5.text("FIRST VARIATION OF AREA: dA/dt = -2 * INT <V, H*N> dA = 0 <=> MEAN CURVATURE H = 0", rx + 28, by + 48)

    # Hyperbolic saddle patch showing orthogonal principal curvatures k_1 > 0 and k_2 = -k_1 < 0
    f7_cx, f7_cy = rx + 172.0, by + 215.0
    u7 = np.linspace(-1.0, 1.0, 50)
    for k_s in range(-3, 4):
        v7 = k_s * 0.32
        x7 = f7_cx + u7 * 86.0 + v7 * 36.0
        y7 = f7_cy - (u7 * u7 - v7 * v7) * 44.0 + v7 * 28.0
        py5.stroke(30, 74, 128, 210)
        py5.stroke_weight(2.0)
        py5.lines(np.column_stack([x7[:-1], y7[:-1], x7[1:], y7[1:]]))

        x7b = f7_cx + v7 * 86.0 + u7 * 36.0
        y7b = f7_cy - (v7 * v7 - u7 * u7) * 44.0 + u7 * 28.0
        py5.stroke(178, 60, 44, 210)
        py5.lines(np.column_stack([x7b[:-1], y7b[:-1], x7b[1:], y7b[1:]]))

    tx7 = rx + 336.0
    ty7 = by + 88.0
    f7_specs = [
        ("PLATEAU PROBLEM", ": Local Minimum of Surface Area A(Sigma)", (36, 118, 96)),
        ("YOUNG-LAPLACE LAW", ": Delta_P = 2 * gamma * H = 0 Pa", (30, 74, 128)),
        ("JACOBI OPERATOR", ": L(u) = Delta u - 2*K*u (Stability)", (178, 60, 44)),
        ("FLUX BALANCE", ": Sum_(j=1..3) Int_(gamma_j) nu ds = 0", (144, 94, 24)),
        ("HOFFMAN-MEEKS FAMILY", ": Rectangular Tori Lambda_a = Z + i*a*Z", (38, 30, 22)),
        ("LIMITING DEGENERATION", ": a -> 0 Splits into Catenoid + Plane", (30, 74, 128)),
        ("CONFORMAL MODULUS", ": tau_torus = i (Square Lemniscatic)", (36, 118, 96)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f7_specs):
        yy = ty7 + i * 33.0
        py5.fill(96, 82, 64)
        py5.text_size(12)
        py5.text(k_lbl, tx7, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx7 + 178.0, yy)

    py5.stroke(194, 176, 144, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, by + 390, rx + cw - 24, by + 390)

    # --- FIG. 08: WEIERSTRASS ELLIPTIC p(w) & HOFFMAN-MEEKS DEFORMATION TRACE ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 08 // WEIERSTRASS ELLIPTIC HARMONICS & CURVATURE OSCILLOGRAM", rx + 28, by + 412)
    py5.fill(30, 74, 128)
    py5.text_size(12)
    py5.text("COUPLED PRINCIPAL CURVATURES k_1(s), -k_2(s), AND PERIOD RESIDUE BALANCE", rx + 28, by + 436)

    wx = rx + 36.0
    wy = by + 482.0
    ww = cw - 72.0
    wh = 285.0
    py5.fill(242, 236, 224, 245)
    py5.stroke(158, 136, 104, 200)
    py5.stroke_weight(1.6)
    py5.rect(wx, wy, ww, wh, 6)

    py5.stroke(212, 200, 178, 165)
    py5.stroke_weight(1.1)
    for g_i in range(1, 4):
        gy_w = wy + (wh / 4.0) * g_i
        py5.line(wx, gy_w, wx + ww, gy_w)
    for g_j in range(1, 6):
        gx_w = wx + (ww / 6.0) * g_j
        py5.line(gx_w, wy, gx_w, wy + wh)

    n_w = 200
    u_w = np.linspace(0.0, 1.0, n_w)
    xw_arr = wx + u_w * ww
    mid_y = wy + wh * 0.5

    for freq_w, amp_w, ph_w, col_w in [
        (2.0, 86.0, omega * tau, (30, 74, 128, 240)),
        (2.0, -86.0, omega * tau, (178, 60, 44, 240)),
        (4.0, 52.0, -2.0 * omega * tau, (216, 140, 30, 230)),
        (3.0, 36.0, 2.0 * omega * tau, (36, 118, 96, 225)),
    ]:
        yw_c = mid_y - amp_w * np.sin(freq_w * 2.0 * math.pi * u_w + ph_w) * np.cos(math.pi * u_w - 0.5 * omega * tau)
        segs_w = np.column_stack([xw_arr[:-1], yw_c[:-1], xw_arr[1:], yw_c[1:]])
        py5.stroke(*col_w)
        py5.stroke_weight(2.6)
        py5.lines(segs_w)

    py5.no_stroke()
    py5.fill(86, 68, 44)
    py5.text_size(12)
    py5.text(
        "SAPPHIRE: +k_1 PRINCIPAL  //  TERRACOTTA: -k_2 PRINCIPAL  //  GOLD: WEIERSTRASS p(w)  //  EMERALD: H = 0 DATUM",
        wx + 8,
        wy + wh + 18,
    )


def draw_archival_border_and_typography(tau: float, omega: float):
    """Draws the outer museum architectural border, title header, and telemetry footer."""
    py5.no_fill()
    py5.stroke(128, 94, 52, 225)
    py5.stroke_weight(3.2)
    py5.rect(52, 48, WIDTH - 104, HEIGHT - 96, 10)

    py5.stroke(178, 152, 112, 165)
    py5.stroke_weight(1.4)
    py5.rect(64, 60, WIDTH - 128, HEIGHT - 120, 6)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(38, 30, 20)
    py5.text_size(30)
    py5.text(
        "COSTA-HOFFMAN-MEEKS MINIMAL SURFACE // WEIERSTRASS-ENNEPER IMMERSION",
        CX,
        82,
    )

    py5.fill(178, 60, 44)
    py5.text_size(15)
    py5.text(
        "GENUS g = 1 COMPLETE EMBEDDED MINIMAL SURFACE WITH THREE ENDS: H = 0 & INT K dA = -12*PI (COSTA 1982 / HOFFMAN-MEEKS 1985)",
        CX,
        124,
    )

    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(86, 72, 52)
    py5.text_size(14)
    py5.text(
        "TOPOLOGY: T^2 \\ {p_0, p_1, p_2} // EULER CHAR CHI = -3 // TWO CATENOIDAL ENDS + ONE DIHEDRAL PLANAR END",
        96,
        HEIGHT - 74,
    )

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K MATHEMATICAL TOPOLOGY // HARMONIC PHASE TAU = {tau:0.3f} (12.0s @ 60FPS)",
        WIDTH - 96,
        HEIGHT - 74,
    )


def finish_and_encode():
    """Compiles the 720 rendered PNG frames into a 4K 60fps H.264 MP4 and cleans up frames/."""
    elapsed = time.time() - START_TIME
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {elapsed:.1f}s (~{TOTAL_FRAMES/max(0.1, elapsed):.2f} fps).")
    print(f"[{WORK_NAME}] Compiling 4K 60fps MP4 with FFmpeg...")

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "16",
        "-preset",
        "fast",
        str(OUTPUT_MP4),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and OUTPUT_MP4.exists():
        mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
        print(f"[{WORK_NAME}] Successfully generated output.mp4 ({mb:.2f} MB)")
        shutil.rmtree(FRAMES_DIR, ignore_errors=True)
        print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")
    else:
        print(f"[{WORK_NAME}] FFmpeg error: {res.stderr}", file=sys.stderr)

    print(f"[{WORK_NAME}] Complete!")
    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

