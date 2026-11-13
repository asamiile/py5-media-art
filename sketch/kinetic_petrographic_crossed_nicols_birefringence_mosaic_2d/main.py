"""
Kinetic Petrographic Crossed-Nicols Birefringence Mosaic 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Physical / Micro-Kinetic genre, exploring
polarized optical mineralogy, thin-section petrography, and anisotropic crystal
birefringence (William Nicol 1828 calcite prism; Henry Clifton Sorby 1858 rock thin
sections; Auguste Michel-Levy 1888 birefringence interference chart), executed on
deep optical bench & extinction obsidian (#060912).

A 30-micrometer thin section of abyssal olivine-plagioclase-clinopyroxene gabbro
(troctolite) rotates on a graduated 360-degree petrographic goniometer stage between
crossed polarizer (P: 0 deg N-S) and analyzer (A: 90 deg E-W) with a diagonal 530 nm
First-Order Red (gypsum lambda-plate) compensator. Over 110 interlocking polycrystalline
mineral grains—zoned Forsterite Olivine (Delta n = 0.036), polysynthetically twinned
Labradorite Plagioclase (Delta n = 0.008, Albite (010) twin lamellae), and cleaved
Augite Clinopyroxene (Delta n = 0.025)—modulate their transmitted interference spectra
via the Fresnel-Malus retardation law I(lambda, theta) = I_0 * sin^2(2*(theta - phi_0))
* sin^2(pi * d * Delta_n / lambda), flanked by eight optical crystallography apparatuses.

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
WORK_NAME = "kinetic_petrographic_crossed_nicols_birefringence_mosaic_2d"
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
RND_STAGE_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_GRAIN_SEED = int(np.random.randint(100, 99999))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 22.0
STAGE_R = 805.0
SLIDE_R = 735.0


def clip_polygon_halfplane(poly: list, a: float, b: float, c: float):
    """
    Sutherland-Hodgman clips 2D polygon `poly` against the half-plane a*x + b*y <= c.
    """
    if not poly:
        return []
    out = []
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        d1 = a * x1 + b * y1 - c
        d2 = a * x2 + b * y2 - c
        in1 = (d1 <= 0.0)
        in2 = (d2 <= 0.0)
        if in1 and in2:
            out.append((x2, y2))
        elif in1 and not in2:
            t = d1 / (d1 - d2 + 1e-12)
            out.append((x1 + t * (x2 - x1), y1 + t * (y2 - y1)))
        elif not in1 and in2:
            t = d1 / (d1 - d2 + 1e-12)
            out.append((x1 + t * (x2 - x1), y1 + t * (y2 - y1)))
            out.append((x2, y2))
    return out


def build_polycrystalline_thin_section():
    """
    Generates ~112 well-spaced mineral seed sites inside SLIDE_R using sunflower
    phyllotaxis + jitter, computes their exact clipped Voronoi crystal polygons,
    and precomputes:
    - Mineral phase:
      0 = Forsterite Olivine (zoned concentric rings + irregular fractures, high birefringence)
      1 = Labradorite Plagioclase (polysynthetic Albite twin lamellae strips)
      2 = Augite Clinopyroxene (orthogonal 87/93 deg cleavage & exsolution lamellae)
    - Optic axis orientation phi_0, retardationGamma (nm), and sub-facet triangles/quads
      for ultra-fast vectorized rendering!
    """
    np.random.seed(RND_GRAIN_SEED)
    n_grains = 112
    golden_ang = math.pi * (3.0 - math.sqrt(5.0))

    seeds = []
    for i in range(n_grains):
        r_base = SLIDE_R * 0.94 * math.sqrt((i + 0.5) / float(n_grains))
        ang_base = i * golden_ang + np.random.uniform(-0.14, 0.14)
        r_jit = max(12.0, min(SLIDE_R - 22.0, r_base + np.random.uniform(-18.0, 18.0)))
        sx = CX + r_jit * math.cos(ang_base)
        sy = CY + r_jit * math.sin(ang_base)
        seeds.append((sx, sy))

    # Add 36 outer boundary guard points just outside SLIDE_R so border grains clip cleanly to the circle
    for b_i in range(36):
        ba = (b_i / 36.0) * 2.0 * math.pi
        seeds.append((CX + (SLIDE_R + 62.0) * math.cos(ba), CY + (SLIDE_R + 62.0) * math.sin(ba)))

    seeds_arr = np.array(seeds, dtype=np.float64)
    grains = []

    # Initial bounding box polygon
    R_box = SLIDE_R + 80.0
    init_poly = [
        (CX - R_box, CY - R_box),
        (CX + R_box, CY - R_box),
        (CX + R_box, CY + R_box),
        (CX - R_box, CY + R_box),
    ]

    for i in range(n_grains):
        sx, sy = seeds_arr[i]
        poly = list(init_poly)

        # Sort neighbors by distance and clip against perpendicular bisectors (inset by 2.2 px for grain boundary rim)
        dx = seeds_arr[:, 0] - sx
        dy = seeds_arr[:, 1] - sy
        dists = np.hypot(dx, dy)
        order = np.argsort(dists)

        for j in order[1:28]:
            nx_j, ny_j = seeds_arr[j]
            vx = nx_j - sx
            vy = ny_j - sy
            v_len = math.hypot(vx, vy)
            if v_len < 1e-6:
                continue
            ux, uy = vx / v_len, vy / v_len
            mx = 0.5 * (sx + nx_j) - ux * 2.2
            my = 0.5 * (sy + ny_j) - uy * 2.2
            c_val = ux * mx + uy * my
            poly = clip_polygon_halfplane(poly, ux, uy, c_val)
            if not poly:
                break

        if len(poly) < 3:
            continue

        # Assign mineral phase: 38% Plagioclase (twinned), 34% Olivine (zoned), 28% Clinopyroxene (cleaved)
        phase_mod = i % 10
        if phase_mod in (0, 2, 5, 8):
            m_type = 1  # Labradorite Plagioclase (Polysynthetic Albite Twin Lamellae)
        elif phase_mod in (1, 4, 7):
            m_type = 0  # Forsterite Olivine (Concentric Chemical Zoning + Fractures)
        else:
            m_type = 2  # Augite Clinopyroxene (Prismatic Cleavage + Exsolution)

        phi_optic = float(np.random.uniform(0.0, math.pi))
        gamma_nm = float(np.random.uniform(280.0, 1450.0))

        # Centroid of the clipped grain polygon
        pts_np = np.array(poly, dtype=np.float64)
        cx_g = float(np.mean(pts_np[:, 0]))
        cy_g = float(np.mean(pts_np[:, 1]))

        # Precompute sub-polygons & internal microstructural line segments for this grain!
        sub_quads = []  # List of (quad_4x2, delta_phi_offset, gamma_mult)
        cleavage_lines = []

        n_v = len(poly)
        if m_type == 0:
            # Forsterite Olivine: 3 concentric chemical zoning shells (core, mantle, rim)
            # represented as quad rings between centroid and vertices
            scales = [1.0, 0.72, 0.44, 0.0]
            gamma_mults = [0.78, 1.00, 1.24]
            phi_offs = [0.08, 0.0, -0.06]
            for ring_k in range(3):
                s_out = scales[ring_k]
                s_in = scales[ring_k + 1]
                for v_i in range(n_v):
                    p0 = poly[v_i]
                    p1 = poly[(v_i + 1) % n_v]
                    q0 = (cx_g + (p0[0] - cx_g) * s_out, cy_g + (p0[1] - cy_g) * s_out)
                    q1 = (cx_g + (p1[0] - cx_g) * s_out, cy_g + (p1[1] - cy_g) * s_out)
                    q2 = (cx_g + (p1[0] - cx_g) * s_in, cy_g + (p1[1] - cy_g) * s_in)
                    q3 = (cx_g + (p0[0] - cx_g) * s_in, cy_g + (p0[1] - cy_g) * s_in)
                    sub_quads.append(((q0, q1, q2, q3), phi_offs[ring_k], gamma_mults[ring_k]))

            # Irregular olivine serpentinization fracture lines across the grain
            for v_i in range(0, n_v, max(2, n_v // 3)):
                p_v = poly[v_i]
                p_opp = poly[(v_i + n_v // 2) % n_v]
                mx_f = cx_g + np.random.uniform(-8.0, 8.0)
                my_f = cy_g + np.random.uniform(-8.0, 8.0)
                cleavage_lines.append([p_v[0], p_v[1], mx_f, my_f])
                cleavage_lines.append([mx_f, my_f, p_opp[0], p_opp[1]])

        elif m_type == 1:
            # Labradorite Plagioclase: Slice the polygon into 7 to 11 parallel Albite twin lamellae!
            ca_t, sa_t = math.cos(phi_optic), math.sin(phi_optic)
            # Project vertices onto normal direction (-sa_t, ca_t)
            proj = -(pts_np[:, 0] - cx_g) * sa_t + (pts_np[:, 1] - cy_g) * ca_t
            p_min, p_max = float(np.min(proj)), float(np.max(proj))
            n_twins = int(max(6, min(11, (p_max - p_min) / 11.5)))
            bounds = np.linspace(p_min - 1.0, p_max + 1.0, n_twins + 1)

            nx_t, ny_t = -sa_t, ca_t
            c_base = nx_t * cx_g + ny_t * cy_g

            for tw_k in range(n_twins):
                d0, d1 = bounds[tw_k], bounds[tw_k + 1]
                # Clip poly to c_base + d0 <= nx_t*x + ny_t*y <= c_base + d1
                strip = clip_polygon_halfplane(poly, nx_t, ny_t, c_base + d1)
                strip = clip_polygon_halfplane(strip, -nx_t, -ny_t, -(c_base + d0))
                if len(strip) < 3:
                    continue
                # Triangulate convex strip as quads/degenerated quads from strip[0]
                twin_sign = 1.0 if (tw_k % 2 == 0) else -1.0
                phi_off = twin_sign * 0.42  # Symmetric extinction angle +/- 24 deg!
                g_mult = 0.85 if (tw_k % 2 == 0) else 1.15
                s0 = strip[0]
                for sv in range(1, len(strip) - 1):
                    sub_quads.append(((s0, strip[sv], strip[sv + 1], strip[sv + 1]), phi_off, g_mult))
                # Twin composition plane line
                if len(strip) >= 2:
                    cleavage_lines.append([strip[0][0], strip[0][1], strip[1][0], strip[1][1]])

        else:
            # Augite Clinopyroxene: Simple sector quads + 87/93 deg orthogonal cleavage grid
            for v_i in range(n_v):
                p0 = poly[v_i]
                p1 = poly[(v_i + 1) % n_v]
                sect_off = 0.12 if (v_i % 2 == 0) else -0.12
                sub_quads.append(((p0, p1, (cx_g, cy_g), (cx_g, cy_g)), sect_off, 1.0))

            # Orthogonal cleavage planes at phi_optic and phi_optic + 87 deg
            for ang_c in [phi_optic, phi_optic + math.radians(87.0)]:
                nx_c, ny_c = -math.sin(ang_c), math.cos(ang_c)
                c_b = nx_c * cx_g + ny_c * cy_g
                for off_c in [-28.0, -14.0, 0.0, 14.0, 28.0]:
                    st_c = clip_polygon_halfplane(poly, nx_c, ny_c, c_b + off_c + 0.5)
                    st_c = clip_polygon_halfplane(st_c, -nx_c, -ny_c, -(c_b + off_c - 0.5))
                    if len(st_c) >= 2:
                        pts_c = np.array(st_c, dtype=np.float64)
                        cleavage_lines.append([pts_c[0, 0], pts_c[0, 1], pts_c[-1, 0], pts_c[-1, 1]])

        # Grain boundary segments
        rim_segs = []
        for v_i in range(n_v):
            p0 = poly[v_i]
            p1 = poly[(v_i + 1) % n_v]
            rim_segs.append([p0[0], p0[1], p1[0], p1[1]])

        grains.append((m_type, phi_optic, gamma_nm, sub_quads, cleavage_lines, rim_segs))

    return grains


GRAINS_DATA = build_polycrystalline_thin_section()


def michel_levy_rgb(gamma_eff: float, ext_factor: float):
    """
    Maps effective optical path retardation `gamma_eff` (in nm) and crossed-Nicols
    Malus extinction factor `ext_factor` in [0, 1] to authentic Michel-Levy interference
    RGB colors (with 530 nm sensitive-tint gypsum compensator richness).
    """
    # Normalized wavelength interference phase across R (650nm), G (540nm), B (450nm)
    # under crossed polarizers: I(lambda) = sin^2(pi * Gamma / lambda)
    r_w = math.sin(math.pi * gamma_eff / 645.0) ** 2
    g_w = math.sin(math.pi * gamma_eff / 535.0) ** 2
    b_w = math.sin(math.pi * gamma_eff / 455.0) ** 2

    # Base dark extinction residual (slight deep Prussian-indigo scatter at extinction)
    bright = 0.08 + 0.92 * ext_factor
    cr = int(min(255, (14.0 + 242.0 * (0.85 * r_w + 0.15 * g_w)) * bright))
    cg = int(min(255, (18.0 + 235.0 * (0.82 * g_w + 0.18 * b_w)) * bright))
    cb = int(min(255, (28.0 + 230.0 * (0.88 * b_w + 0.12 * r_w)) * bright))
    return cr, cg, cb


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

    # Stage rotation angle theta_stage completes 180 deg (pi rad) per loop
    # Since crossed-Nicols intensity depends on 2*theta_stage, a pi rotation produces
    # 2 full extinction/interference cycles and loops 100% seamlessly at tau = 1!
    theta_stage = math.pi * tau + RND_STAGE_PHASE

    # 1. Deep Optical Bench & Extinction Obsidian (#060912)
    py5.background(6, 9, 18)

    # 2. Optical Crystallography Coordinate Grid & Polarized Halo
    draw_optical_bench_substrate(tau)

    # 3. Central Rotating Petrographic Thin-Section Mosaic & Goniometer Stage
    draw_central_petrographic_stage(tau, omega, theta_stage)

    # 4. Eight Optical Mineralogy & Birefringence Apparatuses Across Four Flank Cards
    draw_petrographic_apparatuses(tau, omega, theta_stage)

    # 5. Outer Museum Border & Scholarly Typography (Zero Personal Signatures/Seals)
    draw_museum_border_and_typography(tau, theta_stage)

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


def draw_optical_bench_substrate(tau: float):
    """Draws the dark optical bench ambient rings and precision micrometer grid."""
    py5.no_stroke()
    for r_g, col_g in [
        (1160, (12, 18, 34, 95)),
        (930, (16, 26, 48, 90)),
        (835, (22, 34, 62, 100)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    py5.stroke(22, 32, 52, 135)
    py5.stroke_weight(1.1)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)


def draw_central_petrographic_stage(tau: float, omega: float, theta_stage: float):
    """
    Renders the central Petrographic Microscope Rotating Goniometer Stage & Thin Section:
    1. Outer graduated 360-degree brass-and-steel rotating goniometer ring with vernier ticks
    2. 112 interlocking polycrystalline mineral grains (Olivine, Plagioclase, Clinopyroxene)
       rotated by subtle harmonic oscillation and colored in real time via the Fresnel-Malus
       crossed-polarizer retardation equation I(lambda, theta)
    3. Cleavage networks, olivine fracture veins, and dark opaque magnetite/chromite grain rims
    4. Crossed-Nicols ocular reticle crosshairs (P: N-S, A: E-W) with micrometer ticks and
       diagonal 45-deg 530nm Gypsum sensitive-tint axis vector
    """
    # --- 1. OUTER PETROGRAPHIC GONIOMETER STAGE BEZEL ---
    py5.no_stroke()
    py5.fill(32, 40, 58, 255)
    py5.circle(CX, CY, (STAGE_R + 18.0) * 2.0)

    py5.fill(16, 22, 36, 255)
    py5.stroke(214, 162, 54, 240)
    py5.stroke_weight(3.5)
    py5.circle(CX, CY, STAGE_R * 2.0)

    # Dark extinction slide bed inside SLIDE_R
    py5.fill(5, 7, 14, 255)
    py5.stroke(88, 108, 144, 225)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, SLIDE_R * 2.0)

    # Rotating degree graduations on the outer stage rim (STAGE_R - 65 to STAGE_R - 4)
    tick_segs = []
    for deg in range(0, 360, 2):
        rad = math.radians(deg) + 0.18 * math.sin(omega * tau)
        ca, sa = math.cos(rad), math.sin(rad)
        is_15 = (deg % 15 == 0)
        is_5 = (deg % 5 == 0)
        r0 = STAGE_R - (32.0 if is_15 else (20.0 if is_5 else 12.0))
        r1 = STAGE_R - 4.0
        tick_segs.append([CX + r0 * ca, CY + r0 * sa, CX + r1 * ca, CY + r1 * sa])
    py5.stroke(236, 198, 112, 205)
    py5.stroke_weight(1.5)
    py5.lines(np.array(tick_segs, dtype=np.float64))

    # --- 2. RENDER POLYCRYSTALLINE MINERAL GRAINS UNDER CROSSED NICOLS ---
    # Quantize grain sub-quads into 64 color buckets for fast vectorized py5.QUADS rendering
    color_batches = {}
    all_cleavage_segs = []
    all_rim_segs = []

    # Gypsum 530 nm compensator modulation wave
    gypsum_shift = 185.0 * math.sin(omega * tau)

    for m_type, phi_optic, gamma_nm, sub_quads, cleavage_lines, rim_segs in GRAINS_DATA:
        all_cleavage_segs.extend(cleavage_lines)
        all_rim_segs.extend(rim_segs)

        for q_pts, phi_off, g_mult in sub_quads:
            # Angle of mineral fast axis relative to lower polarizer P
            delta_theta = theta_stage - (phi_optic + phi_off)
            # Fresnel-Malus crossed-polarizer extinction factor: sin^2(2 * delta_theta)
            sin_2th = math.sin(2.0 * delta_theta)
            ext_factor = sin_2th * sin_2th

            # Effective retardation Gamma with additive/subtractive gypsum plate shift
            sign_gyp = 1.0 if math.cos(2.0 * delta_theta) >= 0.0 else -1.0
            gamma_eff = max(40.0, gamma_nm * g_mult + sign_gyp * gypsum_shift)

            cr, cg, cb = michel_levy_rgb(gamma_eff, ext_factor)
            # Quantize to 16-step RGB grid to batch similar colors together
            key_rgb = ((cr // 12) * 12, (cg // 12) * 12, (cb // 12) * 12)
            color_batches.setdefault(key_rgb, []).append(q_pts)

    py5.no_stroke()
    for (cr, cg, cb), q_list in color_batches.items():
        py5.fill(cr, cg, cb, 250)
        q_arr = np.array(q_list, dtype=np.float64)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(q_arr.reshape(-1, 2))

    # Render internal cleavage planes, twin composition planes, and olivine fracture veins
    if all_cleavage_segs:
        py5.stroke(10, 14, 24, 170)
        py5.stroke_weight(1.3)
        py5.lines(np.array(all_cleavage_segs, dtype=np.float64))

    # Render bold dark polycrystalline grain boundaries (Beckeline & intergranular rims)
    if all_rim_segs:
        py5.stroke(6, 9, 18, 245)
        py5.stroke_weight(3.2)
        py5.lines(np.array(all_rim_segs, dtype=np.float64))
        py5.stroke(238, 246, 255, 85)
        py5.stroke_weight(1.0)
        py5.lines(np.array(all_rim_segs, dtype=np.float64))

    # --- 3. OCULAR MICROMETER CROSSHAIRS (P: N-S, A: E-W) & GYPSUM COMPENSATOR AXIS ---
    # Orthogonal Polarizer (N-S) and Analyzer (E-W) crosshairs
    py5.stroke(248, 250, 252, 210)
    py5.stroke_weight(2.0)
    py5.line(CX - STAGE_R, CY, CX + STAGE_R, CY)
    py5.line(CX, CY - STAGE_R, CX, CY + STAGE_R)

    # Ocular micrometer scale ticks along horizontal and vertical crosshairs
    mic_segs = []
    for d_m in range(-700, 701, 25):
        if d_m == 0:
            continue
        t_len = 14.0 if (d_m % 100 == 0) else 7.0
        mic_segs.append([CX + d_m, CY - t_len, CX + d_m, CY + t_len])
        mic_segs.append([CX - t_len, CY + d_m, CX + t_len, CY + d_m])
    py5.stroke(248, 250, 252, 185)
    py5.stroke_weight(1.4)
    py5.lines(np.array(mic_segs, dtype=np.float64))

    # Diagonal 45-degree 530nm Gypsum First-Order Red (lambda-plate) slow axis indicator
    gyp_r = SLIDE_R - 18.0
    gx0 = CX - gyp_r * 0.7071
    gy0 = CY + gyp_r * 0.7071
    gx1 = CX + gyp_r * 0.7071
    gy1 = CY - gyp_r * 0.7071
    py5.stroke(244, 63, 94, 185)
    py5.stroke_weight(2.2)
    py5.line(gx0, gy0, gx1, gy1)

    # Central Bertrand crosshair bullseye ring
    py5.no_fill()
    py5.stroke(250, 204, 21, 235)
    py5.stroke_weight(2.2)
    py5.circle(CX, CY, 48.0)


def draw_dark_card_frame(x: float, y: float, w: float, h: float):
    """Draws a dark optical mineralogy telemetry card frame with gold corner brackets."""
    py5.fill(10, 15, 26, 238)
    py5.stroke(76, 92, 124, 210)
    py5.stroke_weight(2.0)
    py5.rect(x, y, w, h, 8)

    py5.no_fill()
    py5.stroke(134, 102, 58, 135)
    py5.stroke_weight(1.1)
    py5.rect(x + 8, y + 8, w - 16, h - 16, 5)

    py5.stroke(234, 179, 58, 235)
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


def draw_petrographic_apparatuses(tau: float, omega: float, theta_stage: float):
    """
    Renders 8 Optical Mineralogy & Birefringence apparatuses across 4 balanced flank cards.
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
    stage_deg = (math.degrees(theta_stage) % 360.0)

    # =========================================================================
    # CARD 1 (TOP-LEFT): FIG. 01 FRESNEL-MALUS LAW & FIG. 02 ALBITE TWINNING
    # =========================================================================
    draw_dark_card_frame(lx, ty, cw, th)

    # --- FIG. 01: FRESNEL-MALUS CROSSED-NICOLS RETARDATION GAMMA = d * DELTA_n ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 01 // FRESNEL-MALUS CROSSED-NICOLS OPTICAL RETARDATION GAMMA", lx + 28, ty + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("I(LAMBDA, THETA) = I_0 * SIN^2(2 * (THETA - PHI_0)) * SIN^2(PI * d * (n_GAMMA - n_ALPHA) / LAMBDA)", lx + 28, ty + 48)

    # Vector polarization splitting diagram inside [lx+38..lx+306, ty+88..ty+348]
    f1_cx, f1_cy = lx + 172.0, ty + 218.0
    py5.fill(6, 10, 18, 240)
    py5.stroke(68, 86, 118, 195)
    py5.stroke_weight(1.5)
    py5.rect(lx + 38.0, ty + 88.0, 268.0, 260.0, 5)

    # Polarizer P (Vertical N-S) and Analyzer A (Horizontal E-W) axes
    py5.stroke(148, 163, 184, 160)
    py5.stroke_weight(1.5)
    py5.line(f1_cx - 108.0, f1_cy, f1_cx + 108.0, f1_cy)
    py5.line(f1_cx, f1_cy - 108.0, f1_cx, f1_cy + 108.0)

    # Rotating fast (n_alpha, cyan) and slow (n_gamma, gold) crystal vibration axes
    ca_f, sa_f = math.cos(theta_stage), math.sin(theta_stage)
    py5.stroke(56, 189, 248, 245)
    py5.stroke_weight(3.2)
    py5.line(f1_cx - 92.0 * ca_f, f1_cy - 92.0 * sa_f, f1_cx + 92.0 * ca_f, f1_cy + 92.0 * sa_f)
    py5.stroke(245, 184, 54, 245)
    py5.line(f1_cx + 92.0 * sa_f, f1_cy - 92.0 * ca_f, f1_cx - 92.0 * sa_f, f1_cy + 92.0 * ca_f)

    tx1 = lx + 336.0
    ty1 = ty + 88.0
    f1_specs = [
        ("SECTION THICKNESS (d)", ": d = 30.0 um Standard Petrographic", (245, 184, 54)),
        ("OLIVINE BIREFRINGENCE", ": Delta_n = 0.036 (Gamma = 1,080 nm)", (52, 211, 153)),
        ("AUGITE BIREFRINGENCE", ": Delta_n = 0.025 (Gamma = 750 nm)", (56, 189, 248)),
        ("PLAGIOCLASE (An62)", ": Delta_n = 0.008 (Gamma = 240 nm)", (244, 240, 230)),
        ("EXTINCTION LOCUS", ": theta = phi_0 + k * 90 DEG (4 / rev)", (244, 63, 94)),
        ("MAX ILLUMINATION", ": theta = phi_0 + 45 DEG (sin^2 = 1.0)", (245, 184, 54)),
        ("GYPSUM COMPENSATOR", ": Lambda_plate = 530 nm First-Order Red", (192, 132, 252)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f1_specs):
        yy = ty1 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx1, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx1 + 178.0, yy)

    py5.stroke(68, 84, 118, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, ty + 390, lx + cw - 24, ty + 390)

    # --- FIG. 02: POLYSYNTHETIC ALBITE TWINNING & MICHEL-LEVY METHOD ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 02 // POLYSYNTHETIC ALBITE (010) TWIN LAMELLAE & EXTINCTION", lx + 28, ty + 412)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("SYMMETRIC EXTINCTION ANGLES +-ALPHA_EXT DETERMINING ANORTHITE CONTENT (An%)", lx + 28, ty + 436)

    # Alternating twinned plagioclase grain schematic in [lx+42..lx+300, ty+488..ty+728]
    f2_x, f2_y = lx + 42.0, ty + 488.0
    for tw_i in range(8):
        xw_t = f2_x + tw_i * 32.0
        sgn_t = 1.0 if (tw_i % 2 == 0) else -1.0
        ext_t = math.sin(2.0 * (theta_stage + sgn_t * 0.42)) ** 2
        cr_t, cg_t, cb_t = michel_levy_rgb(260.0 + sgn_t * 140.0, ext_t)
        py5.fill(cr_t, cg_t, cb_t, 245)
        py5.stroke(24, 34, 54, 235)
        py5.stroke_weight(1.6)
        py5.rect(xw_t, f2_y, 30.0, 236.0, 3)

    tx2 = lx + 336.0
    ty2 = ty + 485.0
    f2_specs = [
        ("TWINNING LAW", ": Albite Law // Twin Axis perp (010)", (245, 184, 54)),
        ("COMPOSITION PLANE", ": (010) Pinacoid Cleavage Plane", (56, 189, 248)),
        ("EXTINCTION ANGLE", ": alpha_ext = +/- 34.5 DEG (An_62)", (52, 211, 153)),
        ("SOLID SOLUTION", ": NaAlSi3O8 (Ab) - CaAl2Si2O8 (An)", (244, 240, 230)),
        ("PERICLINE TWINNING", ": Rhombic Section Cross-Hatching", (244, 63, 94)),
        ("STAGE ROTATION", f": theta_stage = {stage_deg:0.1f} DEG Azimuth", (192, 132, 252)),
        ("IGNEOUS LITHOLOGY", ": Abyssal Olivine-Plagioclase Gabbro", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f2_specs):
        yy = ty2 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx2, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx2 + 178.0, yy)

    # =========================================================================
    # CARD 2 (BOTTOM-LEFT): FIG. 03 SPECTRAL TRANSMISSION & FIG. 04 PALETTE
    # =========================================================================
    draw_dark_card_frame(lx, by, cw, bh)

    # --- FIG. 03: SPECTRAL TRANSMISSION I(LAMBDA) = SIN^2(PI * GAMMA / LAMBDA) ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 03 // SPECTRAL RETARDATION TRANSMISSION CURVES I(LAMBDA)", lx + 28, by + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("DESTRUCTIVE WAVELENGTH NOTCHES GENERATING COMPLEMENTARY NEWTON-LEVY HUES", lx + 28, by + 48)

    f3_x, f3_y, f3_w, f3_h = lx + 38.0, by + 95.0, 268.0, 240.0
    py5.fill(6, 10, 18, 240)
    py5.stroke(68, 86, 118, 195)
    py5.stroke_weight(1.5)
    py5.rect(f3_x, f3_y, f3_w, f3_h, 5)

    lam_arr = np.linspace(400.0, 700.0, 90)
    x3_p = f3_x + 14.0 + ((lam_arr - 400.0) / 300.0) * (f3_w - 28.0)
    for gam_c, col_c in [
        (530.0, (244, 63, 94, 235)),
        (820.0, (56, 189, 248, 235)),
        (1120.0, (52, 211, 153, 235)),
    ]:
        t_spec = np.sin(math.pi * (gam_c + 80.0 * math.sin(omega * tau)) / lam_arr) ** 2
        y3_p = (f3_y + f3_h - 18.0) - t_spec * (f3_h - 38.0)
        py5.stroke(*col_c)
        py5.stroke_weight(2.5)
        py5.lines(np.column_stack([x3_p[:-1], y3_p[:-1], x3_p[1:], y3_p[1:]]))

    tx3 = lx + 336.0
    ty3 = by + 88.0
    f3_specs = [
        ("1ST ORDER (0-550 nm)", ": Iron-Grey -> White -> Straw -> Red", (245, 184, 54)),
        ("TEINTE SENSIBLE (530)", ": 1st-Order Violet-Red (Gypsum Plate)", (244, 63, 94)),
        ("2ND ORDER (550-1100)", ": Indigo -> Cyan -> Emerald -> Carmine", (56, 189, 248)),
        ("3RD ORDER (1100-1650)", ": Pastel Violet -> Jade -> Flesh Pink", (52, 211, 153)),
        ("4TH+ ORDER (>1650 nm)", ": High-Order Pearl White (Calcite)", (244, 240, 230)),
        ("ANOMALOUS DISPERSION", ": Berlin Blue in Chlorite / Melilite", (192, 132, 252)),
        ("BECKE LINE TEST", ": Halo Moves into Higher n on Lowering", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f3_specs):
        yy = ty3 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx3, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx3 + 178.0, yy)

    py5.stroke(68, 84, 118, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, by + 390, lx + cw - 24, by + 390)

    # --- FIG. 04: MICHEL-LEVY BIREFRINGENCE INTERFERENCE ORDER PALETTE ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 04 // AUGUSTE MICHEL-LEVY INTERFERENCE ORDER PALETTE (1888)", lx + 28, by + 412)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("CHARACTERISTIC RETARDATION CHROMATICITY ACROSS 30-MICRON GABBRO PHASES", lx + 28, by + 436)

    swatches = [
        ((234, 179, 58), "1ST-ORDER STRAW GOLD (GAMMA = 310 nm) // LABRADORITE PLAGIOCLASE TWIN LAMELLA"),
        ((225, 42, 108), "1ST-ORDER SENSITIVE MAGENTA (GAMMA = 530 nm) // GYPSUM ACCESSORY COMPENSATOR"),
        ((38, 118, 228), "2ND-ORDER SAPPHIRE INDIGO (GAMMA = 620 nm) // AUGITE CLINOPYROXENE PRISM SECTOR"),
        ((22, 188, 216), "2ND-ORDER PEACOCK CYAN (GAMMA = 740 nm) // FORSTERITE OLIVINE MANTLE ZONE"),
        ((24, 196, 134), "2ND-ORDER VIVID EMERALD (GAMMA = 860 nm) // FORSTERITE OLIVINE HIGH-Mg CORE"),
        ((168, 85, 247), "3RD-ORDER IMPERIAL AMETHYST (GAMMA = 1,180 nm) // BASAL OLIVINE MAX BIREFRINGENCE"),
    ]
    for i, (rgb_s, desc_s) in enumerate(swatches):
        sy = by + 482.0 + i * 54.0
        py5.fill(*rgb_s)
        py5.stroke(234, 179, 58, 215)
        py5.stroke_weight(1.5)
        py5.rect(lx + 32, sy, 52, 34, 4)
        py5.no_stroke()
        py5.fill(236, 232, 224)
        py5.text_size(13)
        py5.text(desc_s, lx + 104, sy + 9)

    # =========================================================================
    # CARD 3 (TOP-RIGHT): FIG. 05 BIAXIAL INDICATRIX & FIG. 06 CODEX LEDGER
    # =========================================================================
    draw_dark_card_frame(rx, ty, cw, th)

    # --- FIG. 05: BIAXIAL OPTICAL INDICATRIX ELLIPSOID & 2V OPTIC ANGLE ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 05 // BIAXIAL OPTICAL INDICATRIX ELLIPSOID (n_ALPHA, n_BETA, n_GAMMA)", rx + 28, ty + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("TWO CIRCULAR SECTIONS OF RADIUS n_BETA & OPTIC AXIAL ANGLE 2V_z BISECTED BY Z", rx + 28, ty + 48)

    f5_cx, f5_cy = rx + 172.0, ty + 218.0
    u5 = np.linspace(0.0, 2.0 * math.pi, 100)
    # Triaxial ellipsoid outer contour + two tilted circular sections of radius n_beta
    py5.no_fill()
    py5.stroke(245, 184, 54, 230)
    py5.stroke_weight(2.4)
    py5.ellipse(f5_cx, f5_cy, 210.0, 152.0)

    for s_ang in [-0.48, 0.48]:
        ca5, sa5 = math.cos(s_ang), math.sin(s_ang)
        x5 = f5_cx + 95.0 * np.cos(u5) * ca5 - 32.0 * np.sin(u5) * sa5
        y5 = f5_cy + 95.0 * np.cos(u5) * sa5 + 32.0 * np.sin(u5) * ca5
        py5.stroke(56, 189, 248, 215)
        py5.stroke_weight(1.8)
        py5.lines(np.column_stack([x5[:-1], y5[:-1], x5[1:], y5[1:]]))
        # Optic axis normal to circular section
        oa_ang = s_ang + 0.5 * math.pi
        py5.stroke(244, 63, 94, 245)
        py5.stroke_weight(2.4)
        py5.line(
            f5_cx - 98.0 * math.cos(oa_ang), f5_cy - 98.0 * math.sin(oa_ang),
            f5_cx + 98.0 * math.cos(oa_ang), f5_cy + 98.0 * math.sin(oa_ang),
        )

    tx5 = rx + 336.0
    ty5 = ty + 88.0
    f5_specs = [
        ("INDICATRIX EQUATION", ": x^2/n_a^2 + y^2/n_b^2 + z^2/n_g^2 = 1", (245, 184, 54)),
        ("FORSTERITE INDICES", ": n_a=1.635, n_b=1.651, n_g=1.670", (52, 211, 153)),
        ("OPTIC AXIAL ANGLE", ": cos^2(V_z) = n_a^2(n_g^2-n_b^2)/...", (56, 189, 248)),
        ("OLIVINE 2V ANGLE", ": 2V_z = 86.5 DEG (Biaxial Positive)", (244, 63, 94)),
        ("ISOTROPIC SECTIONS", ": 2 Circular Planes of Index n_beta", (244, 240, 230)),
        ("UNIAXIAL LIMIT", ": n_alpha = n_beta => 2V = 0 DEG", (192, 132, 252)),
        ("DISPERSION TYPE", ": r < v Weak Orthorhombic Dispersion", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f5_specs):
        yy = ty5 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx5, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx5 + 178.0, yy)

    py5.stroke(68, 84, 118, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, ty + 390, rx + cw - 24, ty + 390)

    # --- FIG. 06: HISTORICAL OPTICAL MINERALOGY & PETROGRAPHY CODEX LEDGER ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 06 // HISTORICAL OPTICAL MINERALOGY & PETROGRAPHY LEDGER", rx + 28, ty + 412)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("FROM BARTHOLIN'S ICELAND SPAR (1669) & NICOL PRISM (1828) TO MICHEL-LEVY (1888)", rx + 28, ty + 436)

    rows = [
        ("ICELAND SPAR (1669)", "Erasmus Bartholin", "Calcite CaCO3", "Double Refraction"),
        ("NICOL PRISM (1828)", "William Nicol", "Canada Balsam Cut", "Polarized Light"),
        ("ROCK THIN SECTIONS (1858)", "Henry C. Sorby", "30 um Ground Slide", "Micro-Petrography"),
        ("MICHEL-LEVY CHART (1888)", "A. Michel-Levy", "Nomogram d vs Dn", "Interference Orders"),
        ("UNIVERSAL STAGE (1891)", "E.S. Fedorov", "4-Axis Goniometer", "3D Optic Orientation"),
        ("ACTIVE GABBRO MOSAIC", f"theta = {stage_deg:0.1f} DEG", "112 Mineral Grains", "HARMONIC LIVE"),
    ]
    for r_i, (c_name, c_auth, c_inst, c_note) in enumerate(rows):
        ry_row = ty + 478.0 + r_i * 55.0
        is_hi = (r_i == 3 or r_i == 5)
        py5.fill(*(28, 38, 64, 242) if is_hi else (14, 20, 36, 220))
        py5.stroke(*(245, 184, 54, 235) if is_hi else (68, 84, 118, 175))
        py5.stroke_weight(1.9 if is_hi else 1.1)
        py5.rect(rx + 28, ry_row, cw - 56, 44, 5)

        py5.no_stroke()
        py5.fill(244, 240, 230)
        py5.text_size(12)
        py5.text(c_name, rx + 44, ry_row + 15)
        py5.fill(56, 189, 248)
        py5.text(c_auth, rx + 265, ry_row + 15)
        py5.fill(245, 184, 54)
        py5.text(c_inst, rx + 435, ry_row + 15)
        py5.fill(52, 211, 153)
        py5.text(c_note, rx + 595, ry_row + 15)

    # =========================================================================
    # CARD 4 (BOTTOM-RIGHT): FIG. 07 CONOSCOPIC FIGURE & FIG. 08 OSCILLOGRAM
    # =========================================================================
    draw_dark_card_frame(rx, by, cw, bh)

    # --- FIG. 07: CONOSCOPIC BIAXIAL INTERFERENCE FIGURE (ISOGYRES & MELATOPES) ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 07 // CONOSCOPIC BIAXIAL INTERFERENCE FIGURE (BERTRAND LENS)", rx + 28, by + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("CASSINI-LEMNISCATE ISOCHROMES & ROTATING HYPERBOLIC BLACK ISOGYRES", rx + 28, by + 48)

    f7_cx, f7_cy = rx + 172.0, by + 218.0
    # Concentric Cassini oval isochromatic rings around the two melatope eyes
    for r_iso, col_iso in [
        (96.0, (168, 85, 247, 195)),
        (76.0, (52, 211, 153, 210)),
        (56.0, (56, 189, 248, 225)),
        (36.0, (245, 184, 54, 240)),
    ]:
        py5.no_fill()
        py5.stroke(*col_iso)
        py5.stroke_weight(4.5)
        py5.ellipse(f7_cx, f7_cy, r_iso * 2.1, r_iso * 1.55)

    # Rotating hyperbolic black isogyre branches passing through the two melatopes
    u7 = np.linspace(-1.0, 1.0, 60)
    for s7 in [-1.0, 1.0]:
        hx_loc = s7 * (22.0 + 62.0 * (u7 ** 2))
        hy_loc = 78.0 * u7
        ca7, sa7 = math.cos(theta_stage), math.sin(theta_stage)
        hx_w = f7_cx + hx_loc * ca7 - hy_loc * sa7
        hy_w = f7_cy + hx_loc * sa7 + hy_loc * ca7
        py5.stroke(6, 9, 18, 245)
        py5.stroke_weight(10.0)
        py5.lines(np.column_stack([hx_w[:-1], hy_w[:-1], hx_w[1:], hy_w[1:]]))

    tx7 = rx + 336.0
    ty7 = by + 88.0
    f7_specs = [
        ("OPTICAL CONFIGURATION", ": Substage Condenser + Bertrand Lens", (245, 184, 54)),
        ("ISOCHROMATIC CURVES", ": Cassini Ovals r_1 * r_2 = const", (56, 189, 248)),
        ("MELATOPE EYES", ": Emergence of Primary Optic Axes OA", (244, 63, 94)),
        ("ISOGYRE GEOMETRY", ": Bertin's Equi-Azimuth Hyperbolas", (52, 211, 153)),
        ("0 / 90 DEG POSITION", ": Isogyres Form Symmetric Dark Cross", (244, 240, 230)),
        ("45 DEG DIAGONAL", ": Cross Splits into 2 Hyperbolic Arcs", (192, 132, 252)),
        ("OPTIC SIGN TEST", ": Gypsum Blue in Acute Bisectrix (+)", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f7_specs):
        yy = ty7 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx7, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx7 + 178.0, yy)

    py5.stroke(68, 84, 118, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, by + 390, rx + cw - 24, by + 390)

    # --- FIG. 08: HARMONIC STAGE EXTINCTION SIN^2(2*THETA) OSCILLOGRAM ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 08 // HARMONIC STAGE EXTINCTION & TWIN LAMINA CONTRAST TRACE", rx + 28, by + 412)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("FOUR-CYCLE MALUS TRANSMISSION SIN^2(2*(THETA - PHI_i)) ACROSS TWINNED DOMAINS", rx + 28, by + 436)

    wx = rx + 36.0
    wy = by + 482.0
    ww = cw - 72.0
    wh = 285.0
    py5.fill(6, 10, 18, 242)
    py5.stroke(68, 84, 118, 200)
    py5.stroke_weight(1.6)
    py5.rect(wx, wy, ww, wh, 6)

    py5.stroke(24, 34, 56, 165)
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
    base_y = wy + wh - 24.0

    for ph_off, col_w in [
        (0.0, (245, 184, 54, 240)),
        (0.42, (56, 189, 248, 240)),
        (-0.42, (244, 63, 94, 230)),
        (0.85, (52, 211, 153, 225)),
    ]:
        val_w = np.sin(2.0 * (math.pi * u_w + theta_stage - ph_off)) ** 2
        yw_c = base_y - val_w * (wh - 48.0)
        segs_w = np.column_stack([xw_arr[:-1], yw_c[:-1], xw_arr[1:], yw_c[1:]])
        py5.stroke(*col_w)
        py5.stroke_weight(2.5)
        py5.lines(segs_w)

    py5.no_stroke()
    py5.fill(168, 182, 204)
    py5.text_size(12)
    py5.text(
        "GOLD: OLIVINE CORE  //  CYAN: ALBITE TWIN A (+34 DEG)  //  ROSE: ALBITE TWIN B (-34 DEG)  //  EMERALD: AUGITE",
        wx + 8,
        wy + wh + 18,
    )


def draw_museum_border_and_typography(tau: float, theta_stage: float):
    """Draws the outer optical bench border, header, and telemetry footer."""
    py5.no_fill()
    py5.stroke(214, 158, 52, 225)
    py5.stroke_weight(3.2)
    py5.rect(52, 48, WIDTH - 104, HEIGHT - 96, 10)

    py5.stroke(96, 114, 148, 165)
    py5.stroke_weight(1.4)
    py5.rect(64, 60, WIDTH - 128, HEIGHT - 120, 6)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(248, 244, 234)
    py5.text_size(30)
    py5.text(
        "PETROGRAPHIC CROSSED-NICOLS BIREFRINGENCE MOSAIC // OPTICAL MINERALOGY",
        CX,
        82,
    )

    py5.fill(245, 184, 54)
    py5.text_size(15)
    py5.text(
        "30-MICRON OLIVINE-PLAGIOCLASE GABBRO THIN SECTION, ALBITE TWIN LAMELLAE & MICHEL-LEVY RETARDATION (SORBY 1858)",
        CX,
        124,
    )

    stage_deg = (math.degrees(theta_stage) % 360.0)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(168, 182, 204)
    py5.text_size(14)
    py5.text(
        f"STAGE AZIMUTH THETA = {stage_deg:0.1f} DEG // CROSSED POLARIZERS (P perp A) // 530 nm GYPSUM COMPENSATOR",
        96,
        HEIGHT - 74,
    )

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K PHYSICAL CRYSTALLOGRAPHY // HARMONIC PHASE TAU = {tau:0.3f} (12.0s @ 60FPS)",
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

