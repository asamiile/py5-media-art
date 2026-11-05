"""
Kinetic Parhelia & Ice-Crystal Halo Refraction Dome 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Atmospheric / Painterly / Color Field genre,
exploring atmospheric ice-crystal halo optics, parhelia (sundogs), circumzenithal
arcs, Parry arcs, and minimum-deviation prismatic dispersion (Rene Descartes 1637
Les Meteores; Tobias Lowitz 1790; Auguste Bravais 1847 Memoire sur les halos;
Walter Tape 1994 Atmospheric Halos), executed on sunlit Arctic cirrostratus sky
and archival meteorological vellum (#f4f1ea).

In high-altitude cirrostratus clouds, millions of hexagonal ice crystals (plates,
columns, and Parry-oriented prisms) refract and reflect sunlight. Because hexagonal
ice I_h is dispersive (n_red = 1.307 at 656 nm to n_violet = 1.317 at 410 nm) and
exhibits a sharp minimum-deviation caustic at D_min = 21.84 deg (60-deg prism faces)
and 45.7 deg (90-deg basal-prism faces), the sky dome blooms into luminous, painterly
spectral color-field ribbons: the 22-deg and 46-deg Circular Halos, blazing Left &
Right Parhelia (Sundogs), the 360-deg White Parhelic Circle, the gull-wing Upper
Tangent and Parry Arcs, the Circumzenithal Arc, and the Anthelic Wegener Arcs.

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
WORK_NAME = "kinetic_parhelia_ice_crystal_halo_refraction_dome_2d"
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
RND_SOLAR_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_CRYSTAL_SEED = int(np.random.randint(100, 99999))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 22.0
DOME_R = 805.0

# Precompute 90 drifting hexagonal ice-crystal glints inside the sky dome
np.random.seed(RND_CRYSTAL_SEED)
GLINT_R = np.sqrt(np.random.uniform(0.04, 0.92, 90)) * (DOME_R - 45.0)
GLINT_THETA = np.random.uniform(0.0, 2.0 * math.pi, 90)
GLINT_SIZE = np.random.uniform(5.5, 13.5, 90)
GLINT_PHASE = np.random.uniform(0.0, 2.0 * math.pi, 90)

# Painterly 6-band spectral dispersion palette (from inner red minimum-deviation caustic
# outward through amber, saffron, celadon-viridian, cerulean, and alpine ultramarine):
# (radial_offset_fraction, r, g, b, alpha_scale)
SPECTRAL_BANDS = [
    (-0.42, 198, 54, 42, 0.92),   # 656 nm Cinnabar Red (sharp inner caustic edge)
    (-0.20, 232, 126, 34, 0.96),  # 605 nm Warm Terracotta Amber
    (0.02, 244, 196, 62, 1.00),   # 575 nm Luminous Saffron Gold
    (0.28, 72, 178, 138, 0.90),   # 520 nm Viridian Celadon Green
    (0.56, 42, 134, 206, 0.85),   # 475 nm Cerulean Sky Azure
    (0.88, 56, 78, 172, 0.72),    # 420 nm Alpine Ultramarine Violet (outer dispersion veil)
]


def draw_spectral_ribbon_arc(
    cx: float,
    cy: float,
    r_inner_arr: np.ndarray,
    ang_arr: np.ndarray,
    band_width: float,
    alpha_base: int = 165,
    invert_spectrum: bool = False,
):
    """
    Renders a painterly, multi-band dispersive Color-Field arc using vectorized
    py5.QUADS across the 6 spectral wavelengths (Red -> Gold -> Viridian -> Ultramarine).
    """
    n_pts = len(ang_arr)
    ca = np.cos(ang_arr)
    sa = np.sin(ang_arr)

    bands = SPECTRAL_BANDS[::-1] if invert_spectrum else SPECTRAL_BANDS
    n_b = len(bands)
    dr = band_width / float(n_b)

    py5.no_stroke()
    for b_idx, (off_frac, cr, cg, cb, a_sc) in enumerate(bands):
        r0 = r_inner_arr + (b_idx - 0.5 * n_b) * dr
        r1 = r0 + dr * 1.35  # 35% overlap for seamless painterly color-field blending

        x0 = cx + r0 * ca
        y0 = cy + r0 * sa
        x1 = cx + r1 * ca
        y1 = cy + r1 * sa

        # Envelope taper at the ends of open arcs
        quads = np.empty((n_pts - 1, 4, 2), dtype=np.float64)
        quads[:, 0, 0] = x0[:-1]
        quads[:, 0, 1] = y0[:-1]
        quads[:, 1, 0] = x1[:-1]
        quads[:, 1, 1] = y1[:-1]
        quads[:, 2, 0] = x1[1:]
        quads[:, 2, 1] = y1[1:]
        quads[:, 3, 0] = x0[1:]
        quads[:, 3, 1] = y0[1:]

        py5.fill(cr, cg, cb, int(alpha_base * a_sc))
        with py5.begin_shape(py5.QUADS):
            py5.vertices(quads.reshape(-1, 2))


def draw_custom_curve_spectral_ribbon(
    x_center: np.ndarray,
    y_center: np.ndarray,
    nx_arr: np.ndarray,
    ny_arr: np.ndarray,
    half_width_arr: np.ndarray,
    alpha_base: int = 175,
):
    """
    Renders a painterly 6-band spectral ribbon along an arbitrary parametric curve
    (x_center, y_center) with unit normal (nx_arr, ny_arr) pointing away from the Sun.
    """
    n_pts = len(x_center)
    n_b = len(SPECTRAL_BANDS)
    py5.no_stroke()
    for b_idx, (off_frac, cr, cg, cb, a_sc) in enumerate(SPECTRAL_BANDS):
        s0 = (b_idx / float(n_b) - 0.5) * 2.0
        s1 = ((b_idx + 1.35) / float(n_b) - 0.5) * 2.0
        w0 = s0 * half_width_arr
        w1 = s1 * half_width_arr

        x0 = x_center + nx_arr * w0
        y0 = y_center + ny_arr * w0
        x1 = x_center + nx_arr * w1
        y1 = y_center + ny_arr * w1

        quads = np.empty((n_pts - 1, 4, 2), dtype=np.float64)
        quads[:, 0, 0] = x0[:-1]
        quads[:, 0, 1] = y0[:-1]
        quads[:, 1, 0] = x1[:-1]
        quads[:, 1, 1] = y1[:-1]
        quads[:, 2, 0] = x1[1:]
        quads[:, 2, 1] = y1[1:]
        quads[:, 3, 0] = x0[1:]
        quads[:, 3, 1] = y0[1:]

        py5.fill(cr, cg, cb, int(alpha_base * a_sc))
        with py5.begin_shape(py5.QUADS):
            py5.vertices(quads.reshape(-1, 2))


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

    # Solar elevation angle e_sun oscillates harmonically between 19 deg and 31 deg
    solar_elev_deg = 25.0 + 6.0 * math.sin(omega * tau + RND_SOLAR_PHASE)

    # 1. Sunlit Polar Cirrostratus & Archival Meteorological Vellum (#f4f1ea)
    py5.background(244, 241, 234)

    # 2. Painterly Atmospheric Color-Field Washes & Stereographic Sky Grid
    draw_atmospheric_vellum_substrate(tau)

    # 3. Central All-Sky Ice-Crystal Halo & Parhelia Refraction Dome
    draw_central_halo_refraction_dome(tau, omega, solar_elev_deg)

    # 4. Eight Atmospheric Optics & Ice Crystallography Apparatuses Across Four Flank Cards
    draw_halo_optics_apparatuses(tau, omega, solar_elev_deg)

    # 5. Archival Museum Border & Scholarly Typography (Zero Personal Signatures/Seals)
    draw_archival_border_and_typography(tau, solar_elev_deg)

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


def draw_atmospheric_vellum_substrate(tau: float):
    """Draws soft painterly sky washes and delicate solar-altitude coordinate hairlines."""
    py5.no_stroke()
    for r_g, col_g in [
        (1220, (236, 231, 220, 90)),
        (960, (226, 232, 238, 85)),
        (835, (212, 224, 236, 95)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    py5.stroke(212, 206, 194, 130)
    py5.stroke_weight(1.2)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)


def draw_central_halo_refraction_dome(tau: float, omega: float, solar_elev_deg: float):
    """
    Renders the central All-Sky Atmospheric Halo & Parhelia Color-Field Dome:
    - Painterly cerulean-to-ivory cirrostratus sky-dome gradient
    - Sun position S at (CX, sun_y) and Zenith Z at (CX, z_y)
    - 22-Degree & 46-Degree Minimum-Deviation Dispersive Circular Halos
    - 360-Degree White Parhelic Circle passing through the Sun, Parhelia, 120-deg Parhelia, and Anthelion
    - Upper & Lower Tangent Arcs + Singly-Curved Parry Arc
    - Circumzenithal Arc ("Upside-Down Zenith Rainbow") & Supralateral/Infralateral Arcs
    - Wegener & Tricker Anthelic Arcs crossing at the Anthelion
    - Blazing Left & Right Parhelia (Sundogs) with chromatic dispersion wings
    """
    # Sky dome atmospheric color-field gradient (deep zenith cerulean-slate to luminous horizon ivory-azure)
    py5.no_stroke()
    sky_layers = [
        (DOME_R, (28, 52, 86, 252)),
        (730.0, (34, 66, 108, 235)),
        (640.0, (44, 84, 134, 210)),
        (540.0, (58, 106, 158, 185)),
        (430.0, (78, 132, 182, 155)),
        (310.0, (112, 162, 204, 125)),
        (190.0, (168, 202, 226, 95)),
    ]
    for r_s, col_s in sky_layers:
        py5.fill(*col_s)
        py5.circle(CX, CY, r_s * 2.0)

    # Coordinate setup inside the sky dome:
    # 1 degree of angular distance in sky = 11.4 pixels (so 22 deg = 251 px, 46 deg = 524 px)
    deg_px = 11.4
    sun_y = CY + 135.0 - (solar_elev_deg - 25.0) * 3.8
    zenith_y = CY - 285.0

    # Subtle almucantar (altitude) and azimuth graticule inside the sky dome
    py5.no_fill()
    py5.stroke(186, 214, 242, 65)
    py5.stroke_weight(1.2)
    for r_alm in [251.0, 524.0, 665.0, 745.0]:
        py5.circle(CX, CY, r_alm * 2.0)
    for az_k in range(12):
        az_a = az_k * (math.pi / 6.0)
        py5.line(
            CX + 90.0 * math.cos(az_a),
            CY + 90.0 * math.sin(az_a),
            CX + (DOME_R - 30.0) * math.cos(az_a),
            CY + (DOME_R - 30.0) * math.sin(az_a),
        )

    # Soft Painterly Cirrostratus Ice-Crystal Veil Washes around the Sun
    py5.no_stroke()
    for r_w, col_w in [
        (560.0, (248, 216, 142, 26)),
        (390.0, (252, 228, 168, 34)),
        (225.0, (254, 242, 198, 48)),
    ]:
        py5.fill(*col_w)
        py5.circle(CX, sun_y, r_w * 2.0)

    # --- 1. 46-Degree Circular Halo & Supralateral/Infralateral Color-Field Veil ---
    r_46 = 46.0 * deg_px  # ~524.4 px
    ang_full = np.linspace(0.0, 2.0 * math.pi, 180)
    r46_arr = np.full_like(ang_full, r_46) + 5.0 * np.cos(2.0 * ang_full + omega * tau)
    draw_spectral_ribbon_arc(CX, sun_y, r46_arr, ang_full, band_width=64.0, alpha_base=158)

    # Infralateral & Supralateral tangential dispersion arcs flanking the 46-deg halo out to the dome rim
    for side_sgn in (-1.0, 1.0):
        a_lat = np.linspace(-0.38 * math.pi, 0.38 * math.pi, 90) + (0.0 if side_sgn > 0 else math.pi)
        r_lat = r_46 + 24.0 + 92.0 * (np.sin(a_lat) ** 2)
        draw_spectral_ribbon_arc(CX, sun_y, r_lat, a_lat, band_width=44.0, alpha_base=132)

    # --- 2. 22-Degree Circular Halo (Minimum Deviation D_min = 21.84 deg) ---
    r_22 = 22.0 * deg_px  # ~250.8 px
    r22_arr = np.full_like(ang_full, r_22)
    draw_spectral_ribbon_arc(CX, sun_y, r22_arr, ang_full, band_width=48.0, alpha_base=205)

    # Circumscribed Oval Halo Envelope (column crystals wrapping outside the 22-deg halo)
    ecc_circ = 0.28 + 0.06 * math.cos(omega * tau)
    r_circ_arr = r_22 * (1.0 + ecc_circ * (np.cos(ang_full) ** 2))
    draw_spectral_ribbon_arc(CX, sun_y, r_circ_arr, ang_full, band_width=32.0, alpha_base=115)

    # Darkened sky inside the 22-deg halo ("Babinet's dark inner sky zone" where no rays refract < 21.84 deg)
    py5.no_stroke()
    py5.fill(18, 36, 64, 76)
    py5.circle(CX, sun_y, (r_22 - 22.0) * 2.0)

    # --- 3. Upper & Lower Tangent Arcs & Singly-Curved Parry Arc (Non-Crossing Gull-Wing Geometry) ---
    u_tan = np.linspace(-1.0, 1.0, 120)
    wing_open = 0.28 + 0.12 * math.sin(omega * tau + RND_SOLAR_PHASE)
    xt_up = CX + u_tan * 465.0
    yt_up = (sun_y - r_22) - 108.0 * (u_tan ** 2) + 42.0 * wing_open * (u_tan ** 4)
    dx_t = np.gradient(xt_up)
    dy_t = np.gradient(yt_up)
    norm_t = np.hypot(dx_t, dy_t) + 1e-6
    nx_t = dy_t / norm_t
    ny_t = -dx_t / norm_t
    hw_t = 26.0 * (1.0 - 0.42 * (u_tan ** 2))
    draw_custom_curve_spectral_ribbon(xt_up, yt_up, nx_t, ny_t, hw_t, alpha_base=205)

    # Singly-Curved Sunvex Parry Arc (arching cleanly above the Upper Tangent Arc without crossing)
    u_parry = np.linspace(-0.82, 0.82, 100)
    xp_arr = CX + u_parry * 365.0
    yp_arr = (sun_y - r_22 - 58.0) - 72.0 * (u_parry ** 2)
    dx_p = np.gradient(xp_arr)
    dy_p = np.gradient(yp_arr)
    norm_p = np.hypot(dx_p, dy_p) + 1e-6
    nx_p = dy_p / norm_p
    ny_p = -dx_p / norm_p
    hw_p = 21.0 * (1.0 - 0.50 * (u_parry ** 2))
    draw_custom_curve_spectral_ribbon(xp_arr, yp_arr, nx_p, ny_p, hw_p, alpha_base=175)

    # Lower Tangent Arc (touching bottom of the 22-deg halo at (CX, sun_y + r_22))
    u_low = np.linspace(-0.85, 0.85, 90)
    xl_dn = CX + u_low * 340.0
    yl_dn = (sun_y + r_22) + 96.0 * (u_low ** 2)
    dx_l = np.gradient(xl_dn)
    dy_l = np.gradient(yl_dn)
    norm_l = np.hypot(dx_l, dy_l) + 1e-6
    nx_l = -dy_l / norm_l
    ny_l = dx_l / norm_l
    hw_l = 22.0 * (1.0 - 0.48 * (u_low ** 2))
    draw_custom_curve_spectral_ribbon(xl_dn, yl_dn, nx_l, ny_l, hw_l, alpha_base=185)

    # --- 4. Circumzenithal Arc (CZA — Bravais's "Upside-Down Rainbow" centered on Zenith) ---
    r_cza = 185.0 + (solar_elev_deg - 25.0) * 3.0
    cza_center_y = sun_y - r_46 - r_cza + 12.0
    ang_cza = np.linspace(0.18 * math.pi, 0.82 * math.pi, 110)
    r_cza_arr = np.full_like(ang_cza, r_cza)
    draw_spectral_ribbon_arc(
        CX,
        cza_center_y,
        r_cza_arr,
        ang_cza,
        band_width=44.0,
        alpha_base=230,
        invert_spectrum=True,
    )

    # --- 5. 360-Degree White Parhelic Circle & Anthelic Wegener / Tricker Arcs ---
    r_pc_ring = 415.0
    pc_center_y = sun_y - r_pc_ring
    for w_pc, a_pc in [(20.0, 42), (10.0, 84), (4.0, 195)]:
        py5.no_fill()
        py5.stroke(248, 250, 255, a_pc)
        py5.stroke_weight(w_pc)
        py5.circle(CX, pc_center_y, r_pc_ring * 2.0)

    # Extended Horizontal Parhelic Axis Band through the Sun and Left/Right Sundogs
    for w_hb, a_hb in [(24.0, 38), (11.5, 76), (4.0, 185)]:
        py5.stroke(250, 248, 240, a_hb)
        py5.stroke_weight(w_hb)
        py5.line(CX - 755.0, sun_y, CX + 755.0, sun_y)

    # Vertical Solar Pillar (reflection off horizontal plate crystal basal faces)
    for w_sp, a_sp in [(28.0, 36), (13.5, 72), (4.4, 175)]:
        py5.stroke(254, 232, 156, a_sp)
        py5.stroke_weight(w_sp)
        py5.line(CX, sun_y - 680.0, CX, sun_y + 520.0)

    # Wegener & Tricker Anthelic Arcs crossing at the Anthelion (CX, pc_center_y - r_pc_ring)
    anthelion_y = pc_center_y - r_pc_ring
    for sgn_w in (-1.0, 1.0):
        t_w = np.linspace(0.0, 1.0, 90)
        xw = CX + sgn_w * 525.0 * np.sin(math.pi * t_w)
        yw = anthelion_y + (sun_y - anthelion_y) * (t_w ** 1.12)
        segs_weg = np.column_stack([xw[:-1], yw[:-1], xw[1:], yw[1:]])
        py5.stroke(226, 238, 252, 130)
        py5.stroke_weight(3.6)
        py5.lines(segs_weg)

        # Tricker inner anthelic loop
        xt_r = CX + sgn_w * 245.0 * np.sin(math.pi * t_w)
        yt_r = anthelion_y + (sun_y - r_22 - anthelion_y) * t_w
        segs_trk = np.column_stack([xt_r[:-1], yt_r[:-1], xt_r[1:], yt_r[1:]])
        py5.stroke(252, 238, 198, 120)
        py5.stroke_weight(2.8)
        py5.lines(segs_trk)

    # Anthelion & 120-Degree Parhelia bright white nodes on the Parhelic Circle
    py5.no_stroke()
    for a_node in [-0.5 * math.pi, -0.5 * math.pi + 2.0 * math.pi / 3.0, -0.5 * math.pi - 2.0 * math.pi / 3.0]:
        nx_p = CX + r_pc_ring * math.cos(a_node)
        ny_p = pc_center_y + r_pc_ring * math.sin(a_node)
        py5.fill(248, 252, 255, 105)
        py5.circle(nx_p, ny_p, 44.0)
        py5.fill(255, 255, 255, 245)
        py5.circle(nx_p, ny_p, 15.0)

    # --- 6. Left & Right Parhelia (22-Degree Sundogs / Mock Suns) ---
    sundog_offset = r_22 + 22.0 + (solar_elev_deg - 19.0) * 2.4
    for sgn_sd in (-1.0, 1.0):
        sd_x = CX + sgn_sd * sundog_offset
        sd_y = sun_y

        n_wing = 42
        for k_w in range(n_wing):
            frac = k_w / float(n_wing - 1)
            wx_c = sd_x + sgn_sd * (frac * 185.0)
            wy_h = 40.0 * (1.0 - 0.65 * frac)
            if frac < 0.18:
                col_sd = (218, 58, 42, 225)
            elif frac < 0.38:
                col_sd = (248, 168, 46, 230)
            elif frac < 0.58:
                col_sd = (254, 234, 118, 215)
            elif frac < 0.78:
                col_sd = (88, 206, 178, 185)
            else:
                col_sd = (148, 212, 252, int(165 * (1.0 - (frac - 0.78) / 0.22)))
            py5.fill(*col_sd)
            py5.ellipse(wx_c, sd_y, 20.0, wy_h * 2.0)

        # Lowitz Arc passing through each Sundog
        u_lowitz = np.linspace(-0.45, 0.45, 60)
        lx_arr = sd_x + sgn_sd * 28.0 * (u_lowitz ** 2)
        ly_arr = sd_y + u_lowitz * 245.0
        segs_low = np.column_stack([lx_arr[:-1], ly_arr[:-1], lx_arr[1:], ly_arr[1:]])
        py5.stroke(252, 224, 142, 155)
        py5.stroke_weight(3.5)
        py5.lines(segs_low)

        py5.no_stroke()
        py5.fill(255, 248, 212, 175)
        py5.circle(sd_x, sd_y, 62.0)
        py5.fill(255, 255, 255, 255)
        py5.circle(sd_x, sd_y, 24.0)
        py5.stroke(255, 250, 224, 230)
        py5.stroke_weight(2.4)
        py5.line(sd_x - 48.0, sd_y, sd_x + 48.0, sd_y)
        py5.line(sd_x, sd_y - 48.0, sd_x, sd_y + 48.0)

    # --- 7. The True Sun (Helios Core at CX, sun_y) ---
    py5.no_stroke()
    for r_sun, col_sun in [
        (96.0, (254, 218, 112, 70)),
        (60.0, (254, 238, 164, 140)),
        (32.0, (255, 252, 232, 248)),
        (17.0, (255, 255, 255, 255)),
    ]:
        py5.fill(*col_sun)
        py5.circle(CX, sun_y, r_sun * 2.0)

    py5.stroke(255, 250, 228, 210)
    py5.stroke_weight(2.2)
    for k_r in range(8):
        ar = k_r * (math.pi / 4.0) + 0.15 * math.sin(omega * tau)
        r_len = 78.0 if k_r % 2 == 0 else 48.0
        py5.line(CX - r_len * math.cos(ar), sun_y - r_len * math.sin(ar), CX + r_len * math.cos(ar), sun_y + r_len * math.sin(ar))

    # --- 8. Complete Closed Hexagonal Ice-Crystal Glints Across the Sky Dome ---
    hex_edge_segs = []
    for g_i in range(len(GLINT_R)):
        ga = GLINT_THETA[g_i] + 0.12 * math.sin(omega * tau + GLINT_PHASE[g_i])
        gx_c = CX + GLINT_R[g_i] * math.cos(ga)
        gy_c = CY + GLINT_R[g_i] * math.sin(ga)
        gs = GLINT_SIZE[g_i] * (0.80 + 0.25 * math.sin(2.0 * omega * tau + GLINT_PHASE[g_i]))
        rot_c = omega * tau * 0.5 + GLINT_PHASE[g_i]
        vx = [gx_c + gs * math.cos(rot_c + k * (math.pi / 3.0)) for k in range(6)]
        vy = [gy_c + gs * math.sin(rot_c + k * (math.pi / 3.0)) for k in range(6)]
        for k in range(6):
            kn = (k + 1) % 6
            hex_edge_segs.append([vx[k], vy[k], vx[kn], vy[kn]])
        for k in range(3):
            hex_edge_segs.append([vx[k], vy[k], vx[k + 3], vy[k + 3]])

    py5.stroke(236, 246, 255, 145)
    py5.stroke_weight(1.4)
    py5.lines(np.array(hex_edge_segs, dtype=np.float64))

    # --- 9. Outer Graduated 360-Degree Horizon Compass Bezel Ring ---
    draw_sky_dome_compass_bezel(tau, solar_elev_deg)


def draw_sky_dome_compass_bezel(tau: float, solar_elev_deg: float):
    """Renders the graduated 360-degree horizon bezel framing the sky dome."""
    r_in = DOME_R - 22.0
    r_out = DOME_R + 12.0

    n_seg = 120
    ang = np.linspace(0.0, 2.0 * math.pi, n_seg + 1)
    ca, sa = np.cos(ang), np.sin(ang)
    quads = np.empty((n_seg, 4, 2), dtype=np.float64)
    quads[:, 0, 0] = CX + r_in * ca[:-1]
    quads[:, 0, 1] = CY + r_in * sa[:-1]
    quads[:, 1, 0] = CX + r_out * ca[:-1]
    quads[:, 1, 1] = CY + r_out * sa[:-1]
    quads[:, 2, 0] = CX + r_out * ca[1:]
    quads[:, 2, 1] = CY + r_out * sa[1:]
    quads[:, 3, 0] = CX + r_in * ca[1:]
    quads[:, 3, 1] = CY + r_in * sa[1:]

    py5.no_stroke()
    py5.fill(238, 232, 218, 248)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(quads.reshape(-1, 2))

    py5.no_fill()
    py5.stroke(118, 92, 58, 235)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, r_in * 2.0)
    py5.circle(CX, CY, r_out * 2.0)

    deg_idx = np.arange(360, dtype=np.float64)
    deg_rad = np.deg2rad(deg_idx)
    c_d, s_d = np.cos(deg_rad), np.sin(deg_rad)
    t_len = np.where(deg_idx % 30 == 0, 34.0, np.where(deg_idx % 5 == 0, 15.0, 8.0))
    ticks = np.column_stack([
        CX + r_in * c_d,
        CY + r_in * s_d,
        CX + (r_in + t_len) * c_d,
        CY + (r_in + t_len) * s_d,
    ])
    py5.stroke(96, 74, 44, 195)
    py5.stroke_weight(1.3)
    py5.lines(ticks)


def draw_light_card_frame(x: float, y: float, w: float, h: float):
    """Draws an archival sunlit vellum & brass meteorological card frame."""
    py5.no_stroke()
    py5.fill(54, 44, 32, 22)
    py5.rect(x + 6, y + 8, w, h, 8)

    py5.fill(251, 249, 243, 244)
    py5.stroke(142, 114, 76, 215)
    py5.stroke_weight(2.1)
    py5.rect(x, y, w, h, 8)

    py5.no_fill()
    py5.stroke(188, 162, 122, 145)
    py5.stroke_weight(1.1)
    py5.rect(x + 8, y + 8, w - 16, h - 16, 5)


def draw_halo_optics_apparatuses(tau: float, omega: float, solar_elev_deg: float):
    """
    Renders 8 scholarly atmospheric optics & hexagonal ice crystallography apparatuses
    across 4 balanced flank cards (Left Top/Bottom, Right Top/Bottom).
    """
    lx = 110.0
    rx = WIDTH - 870.0
    cw = 760.0
    ty = 210.0
    th = 835.0
    by = 1085.0
    bh = 845.0

    # =========================================================================
    # CARD 1 (TOP-LEFT): FIG. 01 60-DEG PRISM RAY TRACE & FIG. 02 90-DEG CZA
    # =========================================================================
    draw_light_card_frame(lx, ty, cw, th)
    py5.text_align(py5.LEFT, py5.TOP)

    # --- FIG. 01: 60-DEG HEXAGONAL PLATE MINIMUM-DEVIATION REFRACTION ---
    py5.fill(38, 32, 24)
    py5.text_size(17)
    py5.text("FIG. 01 // 60-DEG HEXAGONAL PRISM MINIMUM-DEVIATION RAY TRACE", lx + 28, ty + 24)
    py5.fill(36, 96, 148)
    py5.text_size(12)
    py5.text("ALTERNATE PRISM FACES (ALPHA = 60 DEG) -> D_min = 21.84 DEG (RED) TO 22.54 DEG (VIOLET)", lx + 28, ty + 48)

    f1_cx = lx + 175.0
    f1_cy = ty + 215.0
    r_hex = 76.0
    rot_h = 0.08 * math.sin(omega * tau)
    pts_h1 = np.empty((7, 2), dtype=np.float64)
    for k in range(7):
        ak = rot_h + (k % 6) * (math.pi / 3.0)
        pts_h1[k] = (f1_cx + r_hex * math.cos(ak), f1_cy + r_hex * math.sin(ak))

    py5.fill(218, 236, 250, 210)
    py5.stroke(42, 98, 156, 235)
    py5.stroke_weight(2.4)
    with py5.begin_shape():
        py5.vertices(pts_h1)

    # Incident white solar ray and dispersive refracted fan (Red -> Gold -> Viridian -> Blue)
    in_x, in_y = f1_cx - 46.0, f1_cy - 34.0
    py5.stroke(218, 158, 32, 245)
    py5.stroke_weight(3.8)
    py5.line(f1_cx - 125.0, f1_cy - 68.0, in_x, in_y)

    for idx_c, (ang_out, col_ray) in enumerate([
        (0.28, (198, 54, 42, 240)),
        (0.35, (238, 158, 38, 240)),
        (0.42, (58, 168, 128, 240)),
        (0.50, (42, 98, 196, 240)),
    ]):
        ex_x = f1_cx + 46.0
        ex_y = f1_cy - 28.0 + idx_c * 6.5
        py5.stroke(*col_ray)
        py5.stroke_weight(2.4)
        py5.line(in_x, in_y, ex_x, ex_y)
        py5.line(ex_x, ex_y, ex_x + 75.0 * math.cos(ang_out), ex_y + 75.0 * math.sin(ang_out))

    tx1 = lx + 340.0
    ty1 = ty + 88.0
    f1_specs = [
        ("CRYSTAL SYMMETRY", ": Hexagonal Ice I_h (P6_3/mmc)", (38, 32, 24)),
        ("PRISM APEX ANGLE", ": alpha = 60.0 DEG (Alternate Faces)", (36, 96, 148)),
        ("RED INDEX (656 nm)", ": n_C = 1.3078 -> D_min = 21.84 DEG", (198, 54, 42)),
        ("YELLOW INDEX (589 nm)", ": n_D = 1.3098 -> D_min = 22.00 DEG", (196, 134, 24)),
        ("VIOLET INDEX (410 nm)", ": n_h = 1.3170 -> D_min = 22.54 DEG", (56, 78, 172)),
        ("DISPERSION SPREAD", ": Delta D = 0.70 DEG Chromatic Band", (42, 138, 104)),
        ("BABINET DARK ZONE", ": Zero Refracted Rays for D < 21.84 DEG", (38, 32, 24)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f1_specs):
        yy = ty1 + i * 33.0
        py5.fill(98, 86, 68)
        py5.text_size(12)
        py5.text(k_lbl, tx1, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx1 + 178.0, yy)

    py5.stroke(194, 176, 144, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, ty + 390, lx + cw - 24, ty + 390)

    # --- FIG. 02: 90-DEG BASAL-PRISM REFRACTION & CIRCUMZENITHAL ARC ---
    py5.no_stroke()
    py5.fill(38, 32, 24)
    py5.text_size(17)
    py5.text("FIG. 02 // 90-DEG BASAL-TO-PRISM REFRACTION (CIRCUMZENITHAL ARC)", lx + 28, ty + 412)
    py5.fill(36, 96, 148)
    py5.text_size(12)
    py5.text("SUNLIGHT ENTERING HORIZONTAL UPPER BASAL FACE & EXITING VERTICAL PRISM FACE", lx + 28, ty + 436)

    f2_cx = lx + 175.0
    f2_cy = ty + 625.0
    # Rectangular cross-section of a horizontally oriented plate crystal
    py5.fill(218, 236, 250, 215)
    py5.stroke(42, 98, 156, 235)
    py5.stroke_weight(2.4)
    py5.rect(f2_cx - 78.0, f2_cy - 34.0, 156.0, 68.0, 3)

    # Incident ray on top basal face and exiting dispersed rays through right vertical prism face
    py5.stroke(218, 158, 32, 245)
    py5.stroke_weight(3.8)
    py5.line(f2_cx - 110.0, f2_cy - 98.0, f2_cx - 18.0, f2_cy - 34.0)

    for idx_c, (ang_out, col_ray) in enumerate([
        (0.52, (198, 54, 42, 240)),
        (0.62, (238, 158, 38, 240)),
        (0.72, (58, 168, 128, 240)),
        (0.84, (42, 98, 196, 240)),
    ]):
        ex_x = f2_cx + 78.0
        ex_y = f2_cy - 6.0 + idx_c * 7.5
        py5.stroke(*col_ray)
        py5.stroke_weight(2.4)
        py5.line(f2_cx - 18.0, f2_cy - 34.0, ex_x, ex_y)
        py5.line(ex_x, ex_y, ex_x + 68.0 * math.cos(ang_out), ex_y + 68.0 * math.sin(ang_out))

    tx2 = lx + 340.0
    ty2 = ty + 485.0
    f2_specs = [
        ("EFFECTIVE PRISM ANGLE", ": alpha = 90.0 DEG (Basal-to-Prism)", (38, 32, 24)),
        ("MINIMUM DEVIATION", ": D_min = 45.74 DEG (46-DEG Halo)", (36, 96, 148)),
        ("CRITICAL ELEVATION", ": e_sun < 32.3 DEG (Total Refl Limit)", (198, 54, 42)),
        ("PEAK CZA BRILLIANCE", ": e_sun = 22.0 DEG (Purest Spectrum)", (196, 134, 24)),
        ("ACTIVE SOLAR ELEVATION", f": e_sun = {solar_elev_deg:0.2f} DEG (CZA ACTIVE)", (42, 138, 104)),
        ("ANGULAR DISPERSION", ": 1.85 DEG (2.6x Wider than 22-Halo)", (56, 78, 172)),
        ("DISCOVERER", ": Auguste Bravais (1847 Treatise)", (38, 32, 24)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f2_specs):
        yy = ty2 + i * 33.0
        py5.fill(98, 86, 68)
        py5.text_size(12)
        py5.text(k_lbl, tx2, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx2 + 178.0, yy)

    # =========================================================================
    # CARD 2 (BOTTOM-LEFT): FIG. 03 BRAVAIS SKEW INDEX & FIG. 04 PALETTE
    # =========================================================================
    draw_light_card_frame(lx, by, cw, bh)

    # --- FIG. 03: BRAVAIS EFFECTIVE REFRACTIVE INDEX n'(gamma) FOR SKEW RAYS ---
    py5.fill(38, 32, 24)
    py5.text_size(17)
    py5.text("FIG. 03 // BRAVAIS SKEW-RAY REFRACTIVE INDEX & PARHELION OFFSET", lx + 28, by + 24)
    py5.fill(36, 96, 148)
    py5.text_size(12)
    py5.text("n'(e) = SQRT((n^2 - SIN^2(e)) / COS^2(e)) DRIVING SUNDOG SEPARATION FROM 22-DEG HALO", lx + 28, by + 48)

    f3_x = lx + 42.0
    f3_y = by + 95.0
    f3_w = 255.0
    f3_h = 240.0
    py5.fill(244, 240, 230, 240)
    py5.stroke(168, 148, 118, 210)
    py5.stroke_weight(1.5)
    py5.rect(f3_x, f3_y, f3_w, f3_h, 5)

    # Plot of Sundog azimuth offset vs solar elevation e in [0, 55 deg]
    e_arr = np.linspace(0.0, 55.0, 90)
    e_rad = np.deg2rad(e_arr)
    n_eff = np.sqrt((1.31 ** 2 - np.sin(e_rad) ** 2) / (np.cos(e_rad) ** 2))
    x3_p = f3_x + (e_arr / 55.0) * f3_w
    y3_p = (f3_y + f3_h - 18.0) - (n_eff - 1.31) * 420.0
    segs3 = np.column_stack([x3_p[:-1], y3_p[:-1], x3_p[1:], y3_p[1:]])
    py5.stroke(198, 54, 42, 235)
    py5.stroke_weight(2.8)
    py5.lines(segs3)

    cur_x3 = f3_x + (solar_elev_deg / 55.0) * f3_w
    cur_neff = math.sqrt((1.31 ** 2 - math.sin(math.radians(solar_elev_deg)) ** 2) / (math.cos(math.radians(solar_elev_deg)) ** 2))
    cur_y3 = (f3_y + f3_h - 18.0) - (cur_neff - 1.31) * 420.0
    py5.fill(36, 96, 148, 255)
    py5.no_stroke()
    py5.circle(cur_x3, cur_y3, 12.0)

    tx3 = lx + 340.0
    ty3 = by + 88.0
    f3_specs = [
        ("SOLAR ELEVATION (e)", f": {solar_elev_deg:0.2f} DEG Above Horizon", (198, 54, 42)),
        ("BRAVAIS INDEX n'(e)", f": n'(e) = {cur_neff:0.4f} (vs n_0 = 1.3098)", (36, 96, 148)),
        ("SUNDOG AZIMUTH", f": +/- {22.0 / math.cos(math.radians(solar_elev_deg)):0.2f} DEG From Sun", (196, 134, 24)),
        ("HALO SEPARATION", f": +{(22.0 / math.cos(math.radians(solar_elev_deg)) - 22.0):0.2f} DEG Outside 22-Halo", (42, 138, 104)),
        ("MAX SUNDOG ALTITUDE", ": e_max = 60.8 DEG (Total Internal Refl)", (38, 32, 24)),
        ("PLATE CRYSTAL TILT", ": < 0.5 DEG Aerodynamic Wobble", (56, 78, 172)),
        ("PARHELIC TAIL LENGTH", ": 12.0 to 18.0 DEG Skew Glint Wing", (38, 32, 24)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f3_specs):
        yy = ty3 + i * 33.0
        py5.fill(98, 86, 68)
        py5.text_size(12)
        py5.text(k_lbl, tx3, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx3 + 178.0, yy)

    py5.stroke(194, 176, 144, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, by + 390, lx + cw - 24, by + 390)

    # --- FIG. 04: CAUCHY ICE DISPERSION & PAINTERLY COLOR-FIELD PALETTE ---
    py5.no_stroke()
    py5.fill(38, 32, 24)
    py5.text_size(17)
    py5.text("FIG. 04 // CAUCHY ICE DISPERSION & COLOR-FIELD SPECTRUM PALETTE", lx + 28, by + 412)
    py5.fill(36, 96, 148)
    py5.text_size(12)
    py5.text("WAVELENGTH-DEPENDENT REFRACTION n(LAMBDA) ACROSS THE 6 PAINTERLY HALO BANDS", lx + 28, by + 436)

    swatches = [
        ((198, 54, 42), "656 nm H-ALPHA CINNABAR RED (n = 1.3078) // SHARP INNER CAUSTIC BOUNDARY"),
        ((232, 126, 34), "605 nm TERRACOTTA AMBER (n = 1.3091) // PRIMARY PARHELION CORE"),
        ((244, 196, 62), "575 nm SAFFRON SOLAR GOLD (n = 1.3102) // UPPER TANGENT & PARRY CREST"),
        ((72, 178, 138), "520 nm VIRIDIAN CELADON (n = 1.3122) // MID-BAND CIRCUMZENITHAL ARC"),
        ((42, 134, 206), "475 nm CERULEAN SKY AZURE (n = 1.3144) // OUTER 22-DEG & 46-DEG VEIL"),
        ((56, 78, 172), "420 nm ALPINE ULTRAMARINE (n = 1.3170) // OUTERMOST DISPERSION CORONA"),
    ]
    for i, (rgb_s, desc_s) in enumerate(swatches):
        sy = by + 482.0 + i * 54.0
        py5.fill(*rgb_s)
        py5.stroke(96, 78, 52, 215)
        py5.stroke_weight(1.5)
        py5.rect(lx + 32, sy, 52, 34, 4)
        py5.no_stroke()
        py5.fill(38, 32, 24)
        py5.text_size(13)
        py5.text(desc_s, lx + 104, sy + 9)

    # =========================================================================
    # CARD 3 (TOP-RIGHT): FIG. 05 ICE CRYSTAL HABITS & FIG. 06 HALO LEDGER
    # =========================================================================
    draw_light_card_frame(rx, ty, cw, th)

    # --- FIG. 05: AERODYNAMIC ICE-CRYSTAL HABIT ORIENTATION TAXONOMY ---
    py5.fill(38, 32, 24)
    py5.text_size(17)
    py5.text("FIG. 05 // HEXAGONAL ICE-CRYSTAL HABITS & AERODYNAMIC ORIENTATION", rx + 28, ty + 24)
    py5.fill(36, 96, 148)
    py5.text_size(12)
    py5.text("REYNOLDS NUMBER (1 < Re < 100) DRIVING PLATE, COLUMN & PARRY ORIENTATIONS", rx + 28, ty + 48)

    # Three crystal habit diagrams: Plate (left), Column (middle), Parry Column (right)
    habits = [
        ("HEX PLATE (c-VERTICAL)", rx + 105.0, ty + 195.0, 44.0, 16.0),
        ("HEX COLUMN (c-HORIZ)", rx + 225.0, ty + 195.0, 24.0, 56.0),
    ]
    for h_lbl, hx, hy, hw, hh in habits:
        py5.fill(218, 236, 250, 225)
        py5.stroke(36, 96, 148, 235)
        py5.stroke_weight(2.2)
        py5.rect(hx - hw, hy - hh, hw * 2.0, hh * 2.0, 3)
        py5.stroke(198, 54, 42, 210)
        py5.stroke_weight(1.8)
        py5.line(hx, hy - 72.0, hx, hy + 72.0)

    tx5 = rx + 340.0
    ty5 = ty + 88.0
    f5_specs = [
        ("HEXAGONAL PLATES", ": c-Axis Vertical -> Sundogs & CZA", (198, 54, 42)),
        ("HEXAGONAL COLUMNS", ": c-Axis Horizontal -> Tangent Arcs", (36, 96, 148)),
        ("PARRY COLUMNS", ": c & Prism Horiz -> Parry & Supras", (42, 138, 104)),
        ("RANDOM 3D TUMBLING", ": Re < 1 -> 22-DEG & 46-DEG Rings", (196, 134, 24)),
        ("SPINNING LOWITZ PLATES", ": Major Axis Spin -> Lowitz Arcs", (56, 78, 172)),
        ("CLOUD TEMPERATURE", ": -45 C to -25 C Cirrostratus Layer", (38, 32, 24)),
        ("CRYSTAL DIAMETER", ": d = 40 um to 250 um Pristine Faces", (36, 96, 148)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f5_specs):
        yy = ty5 + i * 33.0
        py5.fill(98, 86, 68)
        py5.text_size(12)
        py5.text(k_lbl, tx5, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx5 + 178.0, yy)

    py5.stroke(194, 176, 144, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, ty + 390, rx + cw - 24, ty + 390)

    # --- FIG. 06: HISTORICAL HALO COMPLEX OBSERVATION LEDGER ---
    py5.no_stroke()
    py5.fill(38, 32, 24)
    py5.text_size(17)
    py5.text("FIG. 06 // HISTORICAL HALO COMPLEX & CODEX OBSERVATION LEDGER", rx + 28, ty + 412)
    py5.fill(36, 96, 148)
    py5.text_size(12)
    py5.text("MONUMENTAL ATMOSPHERIC DISPLAYS FROM STOCKHOLM (1535) TO AMUNDSEN-SCOTT", rx + 28, ty + 436)

    rows = [
        ("VADERSOLSTAVLAN (1535)", "Stockholm, Sweden", "22/Parhelia/Circle", "Earliest Painting"),
        ("ROMAN PHENOMENON (1630)", "Rome (Scheiner)", "22/46/CZA/Parhelia", "Descartes Theory"),
        ("DANZIG SEVEN SUNS (1661)", "Gdansk (Hevelius)", "Full Anthelic Set", "Mercurius In Sole"),
        ("LOWITZ COMPLEX (1790)", "St. Petersburg, RU", "Lowitz/Parry/CZA", "18 Distinct Arcs"),
        ("SOUTH POLE DISPLAY (1990)", "Antarctica (Tape)", "Diamond Dust Ice", "Crystallographic"),
        ("ACTIVE DOME SIMULATION", f"e_sun = {solar_elev_deg:0.1f} DEG", "14 Spectral Arcs", "HARMONIC LIVE"),
    ]
    for r_i, (c_name, c_loc, c_arcs, c_note) in enumerate(rows):
        ry_row = ty + 478.0 + r_i * 55.0
        is_hi = (r_i == 0 or r_i == 5)
        py5.fill(*(240, 230, 206, 242) if is_hi else (248, 245, 236, 215))
        py5.stroke(*(196, 134, 24, 235) if is_hi else (194, 176, 144, 175))
        py5.stroke_weight(1.9 if is_hi else 1.1)
        py5.rect(rx + 28, ry_row, cw - 56, 44, 5)

        py5.no_stroke()
        py5.fill(38, 32, 24)
        py5.text_size(12)
        py5.text(c_name, rx + 44, ry_row + 15)
        py5.fill(36, 96, 148)
        py5.text(c_loc, rx + 265, ry_row + 15)
        py5.fill(198, 54, 42)
        py5.text(c_arcs, rx + 445, ry_row + 15)
        py5.fill(42, 138, 104)
        py5.text(c_note, rx + 595, ry_row + 15)

    # =========================================================================
    # CARD 4 (BOTTOM-RIGHT): FIG. 07 TANGENT MORPHOLOGY & FIG. 08 CAUSTIC SPIKE
    # =========================================================================
    draw_light_card_frame(rx, by, cw, bh)

    # --- FIG. 07: UPPER TANGENT ARC MORPHOLOGY VS. SOLAR ELEVATION ---
    py5.fill(38, 32, 24)
    py5.text_size(17)
    py5.text("FIG. 07 // TANGENT ARC TO CIRCUMSCRIBED HALO MORPHOLOGY", rx + 28, by + 24)
    py5.fill(36, 96, 148)
    py5.text_size(12)
    py5.text("GULL-WING UPPER TANGENT ARC WRAPPING INTO CLOSED OVAL AS SOLAR ALTITUDE RISES", rx + 28, by + 48)

    f7_cx = rx + 175.0
    f7_cy = by + 215.0
    # 22-deg reference circle
    py5.no_fill()
    py5.stroke(148, 168, 192, 170)
    py5.stroke_weight(1.6)
    py5.circle(f7_cx, f7_cy, 116.0)

    # Overlay 3 tangent/circumscribed envelopes for e = 10 deg, 25 deg, 45 deg
    t7 = np.linspace(0.0, 2.0 * math.pi, 140)
    for k_m, (ecc_m, col_m) in enumerate([
        (0.55, (198, 54, 42, 225)),
        (0.32, (238, 158, 38, 225)),
        (0.14, (36, 96, 148, 225)),
    ]):
        rx7 = (58.0 + 38.0 * ecc_m * (np.cos(t7) ** 2)) * np.cos(t7)
        ry7 = 58.0 * np.sin(t7) - 18.0 * ecc_m * np.cos(2.0 * t7)
        segs7 = np.column_stack([
            f7_cx + rx7[:-1], f7_cy + ry7[:-1],
            f7_cx + rx7[1:], f7_cy + ry7[1:],
        ])
        py5.stroke(*col_m)
        py5.stroke_weight(2.2)
        py5.lines(segs7)

    tx7 = rx + 340.0
    ty7 = by + 88.0
    f7_specs = [
        ("LOW SUN (e < 15 DEG)", ": Sharp V-Shaped Gull-Wing Tangent", (198, 54, 42)),
        ("MID SUN (e = 25 DEG)", ": Drooping Wing-Tips Toward Lower Arc", (196, 134, 24)),
        ("MERGER THRESHOLD", ": e_sun = 29.2 DEG (Upper+Lower Join)", (42, 138, 104)),
        ("HIGH SUN (e > 35 DEG)", ": Closed Circumscribed Oval Halo", (36, 96, 148)),
        ("ZENITH LIMIT (e -> 90)", ": Merges Identically with 22-Halo", (56, 78, 172)),
        ("COLUMN c-AXIS DOF", ": 1 Rotational Degree of Freedom", (38, 32, 24)),
        ("CAUSTIC ENVELOPE", ": Jacobian Determinant det(J) = 0", (198, 54, 42)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f7_specs):
        yy = ty7 + i * 33.0
        py5.fill(98, 86, 68)
        py5.text_size(12)
        py5.text(k_lbl, tx7, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx7 + 178.0, yy)

    py5.stroke(194, 176, 144, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, by + 390, rx + cw - 24, by + 390)

    # --- FIG. 08: ANGULAR INTENSITY CAUSTIC SPIKE I(theta) AT MINIMUM DEVIATION ---
    py5.no_stroke()
    py5.fill(38, 32, 24)
    py5.text_size(17)
    py5.text("FIG. 08 // DESCARTES-AIRY CAUSTIC INTENSITY PROFILE I(THETA)", rx + 28, by + 412)
    py5.fill(36, 96, 148)
    py5.text_size(12)
    py5.text("INVERSE-SQUARE-ROOT SINGULARITY I(D) ~ (D - D_min)^(-1/2) ACROSS WAVELENGTHS", rx + 28, by + 436)

    wx = rx + 36.0
    wy = by + 482.0
    ww = cw - 72.0
    wh = 285.0
    py5.fill(244, 240, 230, 240)
    py5.stroke(164, 142, 108, 200)
    py5.stroke_weight(1.6)
    py5.rect(wx, wy, ww, wh, 6)

    py5.stroke(214, 202, 182, 165)
    py5.stroke_weight(1.1)
    for g_i in range(1, 4):
        gy_w = wy + (wh / 4.0) * g_i
        py5.line(wx, gy_w, wx + ww, gy_w)
    for g_j in range(1, 6):
        gx_w = wx + (ww / 6.0) * g_j
        py5.line(gx_w, wy, gx_w, wy + wh)

    n_w = 220
    u_w = np.linspace(0.0, 1.0, n_w)
    xw_arr = wx + u_w * ww
    base_y = wy + wh - 24.0

    # Four wavelength caustic curves shifted by chromatic dispersion d_min
    for shift_u, col_c in [
        (0.22, (198, 54, 42, 240)),
        (0.30, (232, 148, 34, 240)),
        (0.38, (58, 168, 128, 240)),
        (0.46, (42, 98, 196, 240)),
    ]:
        du = u_w - (shift_u + 0.04 * math.sin(omega * tau))
        intensity = np.where(du > 0.0, np.exp(-3.8 * du) / np.sqrt(np.maximum(0.018, du + 0.018)), np.exp(-180.0 * (du ** 2)) * 2.2)
        intensity = np.clip(intensity / 7.5, 0.0, 0.92)
        yw_c = base_y - intensity * (wh - 42.0)
        segs_c = np.column_stack([xw_arr[:-1], yw_c[:-1], xw_arr[1:], yw_c[1:]])
        py5.stroke(*col_c)
        py5.stroke_weight(2.6)
        py5.lines(segs_c)

    py5.no_stroke()
    py5.fill(86, 68, 44)
    py5.text_size(12)
    py5.text(
        "RED (21.84 DEG): INNER EDGE  //  GOLD (22.00 DEG)  //  VIRIDIAN (22.25 DEG)  //  COBALT (22.54 DEG)",
        wx + 8,
        wy + wh + 18,
    )


def draw_archival_border_and_typography(tau: float, solar_elev_deg: float):
    """Draws the outer museum architectural border, title header, and telemetry footer."""
    py5.no_fill()
    py5.stroke(128, 98, 58, 225)
    py5.stroke_weight(3.2)
    py5.rect(52, 48, WIDTH - 104, HEIGHT - 96, 10)

    py5.stroke(178, 152, 112, 165)
    py5.stroke_weight(1.4)
    py5.rect(64, 60, WIDTH - 128, HEIGHT - 120, 6)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(38, 30, 20)
    py5.text_size(30)
    py5.text(
        "PARHELIA & ICE-CRYSTAL HALO DOME // MINIMUM-DEVIATION ATMOSPHERIC OPTICS",
        CX,
        82,
    )

    py5.fill(36, 96, 148)
    py5.text_size(15)
    py5.text(
        "HEXAGONAL ICE I_h DISPERSION CAUSTICS - 22/46-DEG HALOS, SUNDOGS, PARRY & CIRCUMZENITHAL ARCS (BRAVAIS 1847)",
        CX,
        124,
    )

    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(86, 72, 52)
    py5.text_size(14)
    py5.text(
        f"SOLAR ELEVATION e = {solar_elev_deg:0.2f} DEG // MINIMUM DEVIATION D_min = 21.84 DEG // CAUCHY ICE DISPERSION n(LAMBDA)",
        96,
        HEIGHT - 74,
    )

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K ATMOSPHERIC COLOR FIELD // HARMONIC PHASE TAU = {tau:0.3f} (12.0s @ 60FPS)",
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
