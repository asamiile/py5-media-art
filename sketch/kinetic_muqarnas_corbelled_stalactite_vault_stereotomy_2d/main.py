"""
Kinetic Muqarnas Corbelled Stalactite Vault Stereotomy 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Architectural / Brutalism / Geometric genre,
exploring the 3D stereotomy and corbelled vault geometry of Muqarnas (honeycomb /
stalactite vaulting) formulated by Ghiyath al-Din Jamshid al-Kashi in his 1427
treatise Miftah al-Hisab ("The Key of Arithmetic", Book IV, Chapter 9) and
exemplified by the Hall of the Abencerrajes in the Alhambra (Granada) and the
Shah Mosque (Isfahan), executed on warm Andalusian limestone drafting vellum (#f6f2e8).

In Islamic architectural stereotomy, a Muqarnas dome projects a 2D planar radial
tessellation (Tasarim) upward into stepped 3D corbelled tiers (tabaqat). Each tier
cantilevers inward over the tier below using curved concave niche hoods (tasa),
rhomboid squinches, almond facets (badam), and hanging stalactite pendants (shabaka),
culminating in a central 16-pointed sunlit star cupola (shamsa).

This 4K 60fps simulation visualizes:
1. A monumental 8-tier 16-fold / 32-fold symmetric Muqarnas vault rendered in 3D
   upward perspective with deep star-polygon interlocking niches, fluted muqarnas
   fan ribs, 16 sunlit clerestory lancet windows, and an interlaced Abencerrajes
   {16/5} star rib vault.
2. Vectorized Lambertian solar relief shading across carved gypsum stucco ivory,
   Nasrid lapis cobalt, Alhambra celadon emerald, terracotta ochre, and burnished
   gold leaf.
3. Eight architectural stereotomy blueprint apparatuses across four balanced flank
   cards detailing Al-Kashi's modular scale (miqyas), vertical profile templates,
   planar Tasarim projection, and structural cantilever thrust lines.
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
WORK_NAME = "kinetic_muqarnas_corbelled_stalactite_vault_stereotomy_2d"
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
RND_SUN_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_VAULT_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 24.0
MAX_VAULT_R = 810.0

# Palette of Architectural Materials (RGB):
# 0: Carved Gypsum Stucco Ivory (Yeseria)
# 1: Warm Limestone Travertine Riser
# 2: Nasrid Lapis Cobalt Glazed Tile
# 3: Alhambra Celadon Emerald Glaze
# 4: Andalusian Terracotta Ochre
# 5: Burnished Shamsa Gold Leaf
# 6: Sunlit Clerestory Alabaster Lancet Window
MATERIALS = np.array([
    [244.0, 238.0, 224.0],  # 0: Gypsum Stucco Ivory
    [216.0, 202.0, 178.0],  # 1: Limestone Travertine
    [26.0, 66.0, 114.0],    # 2: Nasrid Lapis Cobalt
    [28.0, 108.0, 84.0],    # 3: Alhambra Celadon Emerald
    [204.0, 102.0, 42.0],   # 4: Terracotta Ochre
    [222.0, 162.0, 38.0],   # 5: Burnished Gold Leaf
    [255.0, 249.0, 218.0],  # 6: Sunlit Clerestory Lancet
], dtype=np.float64)

# Precompute Limestone Paper Grain Lines
NUM_GRAIN = 280
GR_X1 = np.random.uniform(70.0, WIDTH - 70.0, NUM_GRAIN)
GR_Y1 = np.random.uniform(70.0, HEIGHT - 70.0, NUM_GRAIN)
GR_ANG = np.random.uniform(0.0, math.pi, NUM_GRAIN)
GR_LEN = np.random.uniform(60.0, 220.0, NUM_GRAIN)
GR_SEGMENTS = np.column_stack([
    GR_X1, GR_Y1,
    GR_X1 + np.cos(GR_ANG) * GR_LEN,
    GR_Y1 + np.sin(GR_ANG) * GR_LEN,
])

# 8 Concentric Corbelled Star-Interlocked Muqarnas Tiers (Tabaqat)
# (n_sym, r_outer_peak, r_mid_shoulder, r_inner_pendant, z_height, mat_left, mat_right, mat_almond, phase_shift)
TIERS_SPEC = [
    (32, 790.0, 705.0, 595.0, 0.14, 0, 1, 2, 0.0),          # Tier 0: 32-cell Outer Drum Squinch Ring
    (32, 695.0, 595.0, 485.0, 0.28, 1, 0, 3, 0.5),          # Tier 1: 32-cell Corbelled Stalactite Ring
    (16, 590.0, 480.0, 365.0, 0.42, 0, 2, 5, 0.0),          # Tier 2: 16-cell Major Abencerrajes Star Bracket
    (32, 475.0, 382.0, 288.0, 0.56, 3, 0, 4, 0.5),          # Tier 3: 32-cell Honeycomb Badam Vault Ring
    (16, 378.0, 290.0, 202.0, 0.70, 0, 1, 2, 0.25),         # Tier 4: 16-cell Deep Almond Squinch Ring
    (16, 282.0, 205.0, 132.0, 0.82, 6, 4, 5, 0.75),         # Tier 5: 16-cell Clerestory Lancet Window Lantern
    (16, 192.0, 128.0, 64.0, 0.92, 5, 0, 2, 0.0),           # Tier 6: 16-pointed Shamsa Star Rosette
    (16, 108.0, 58.0, 16.0, 1.00, 5, 4, 0, 0.5),            # Tier 7: Central Polar Shamsa Keystone
]


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

    sun_angle = omega * tau + RND_SUN_PHASE
    sun_dx = math.cos(sun_angle)
    sun_dy = math.sin(sun_angle)

    apex_ox = 26.0 * math.cos(omega * tau)
    apex_oy = 26.0 * math.sin(omega * tau)

    # 1. Warm Andalusian Limestone & Architectural Drafting Vellum (#f6f2e8)
    py5.background(246, 242, 232)

    # 2. Limestone Vellum Grain & Sacred Geometry Construction Compass Lines
    py5.stroke(226, 218, 202, 125)
    py5.stroke_weight(1.4)
    py5.lines(GR_SEGMENTS)

    py5.stroke(220, 212, 196, 135)
    py5.stroke_weight(1.5)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)

    # Radial 16-fold Star Construction Rays behind the Muqarnas Dome
    py5.stroke(210, 198, 178, 150)
    py5.stroke_weight(1.6)
    for k_ray in range(16):
        ra = k_ray * math.pi / 8.0
        py5.line(CX - math.cos(ra) * 890, CY - math.sin(ra) * 890,
                 CX + math.cos(ra) * 890, CY + math.sin(ra) * 890)

    # 3. Outer 16-Sided Drum Buttress Wall & Recessed Archway Squinch Border
    draw_outer_drum_wall(sun_dx, sun_dy, tau)

    # 4. Render All 8 Corbelled Muqarnas Tiers (Tabaqat) with Deep Star-Polygon Interlocking
    render_muqarnas_tiers(tau, sun_dx, sun_dy, apex_ox, apex_oy)

    # 5. Four Quadrant Al-Kashi Stereotomy & Architectural Blueprint Apparatuses
    draw_stereotomy_apparatuses(tau, sun_angle)

    # 6. Archival Architectural Border & Scholarly Typography (Zero Personal Signatures/Seals)
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


def draw_outer_drum_wall(sun_dx, sun_dy, tau):
    """Draws the monumental 16-sided structural masonry drum and degree calibration ring."""
    r_drum_out = MAX_VAULT_R + 46.0
    r_drum_mid = MAX_VAULT_R + 12.0
    r_drum_in = MAX_VAULT_R - 20.0
    n_sides = 16

    py5.no_stroke()
    py5.fill(42, 34, 24, 58)
    with py5.begin_shape():
        for i in range(n_sides):
            a = i * 2.0 * math.pi / n_sides + math.pi / 32.0
            py5.vertex(CX + math.cos(a) * r_drum_out - sun_dx * 14.0,
                       CY + math.sin(a) * r_drum_out - sun_dy * 14.0)
    py5.end_shape(py5.CLOSE)

    py5.stroke(58, 44, 30, 215)
    py5.stroke_weight(2.0)
    for i in range(n_sides):
        a1 = i * 2.0 * math.pi / n_sides
        a2 = (i + 1) * 2.0 * math.pi / n_sides
        amid = 0.5 * (a1 + a2)
        dot = math.cos(amid) * sun_dx + math.sin(amid) * sun_dy

        col_out = np.clip(MATERIALS[1] * (0.94 + 0.18 * dot), 30, 250)
        py5.fill(float(col_out[0]), float(col_out[1]), float(col_out[2]))
        with py5.begin_shape():
            py5.vertex(CX + math.cos(a1) * r_drum_mid, CY + math.sin(a1) * r_drum_mid)
            py5.vertex(CX + math.cos(a2) * r_drum_mid, CY + math.sin(a2) * r_drum_mid)
            py5.vertex(CX + math.cos(a2) * r_drum_out, CY + math.sin(a2) * r_drum_out)
            py5.vertex(CX + math.cos(a1) * r_drum_out, CY + math.sin(a1) * r_drum_out)
        py5.end_shape(py5.CLOSE)

        mat_in = MATERIALS[2] if i % 2 == 0 else MATERIALS[3]
        col_in = np.clip(mat_in * (0.95 + 0.20 * dot), 15, 245)
        py5.fill(float(col_in[0]), float(col_in[1]), float(col_in[2]))
        with py5.begin_shape():
            py5.vertex(CX + math.cos(a1) * r_drum_in, CY + math.sin(a1) * r_drum_in)
            py5.vertex(CX + math.cos(a2) * r_drum_in, CY + math.sin(a2) * r_drum_in)
            py5.vertex(CX + math.cos(a2) * r_drum_mid, CY + math.sin(a2) * r_drum_mid)
            py5.vertex(CX + math.cos(a1) * r_drum_mid, CY + math.sin(a1) * r_drum_mid)
        py5.end_shape(py5.CLOSE)

    py5.no_stroke()
    py5.fill(22, 18, 15, 248)
    py5.circle(CX, CY, r_drum_in * 2.0)

    r_tick = r_drum_out + 14.0
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        tlen = 18.0 if deg % 22.5 == 0 else (11.0 if deg % 15 == 0 else 6.0)
        py5.stroke(96, 76, 54, 195 if deg % 15 == 0 else 115)
        py5.stroke_weight(2.0 if deg % 15 == 0 else 1.2)
        py5.line(CX + ca * r_tick, CY + sa * r_tick,
                 CX + ca * (r_tick + tlen), CY + sa * (r_tick + tlen))


def render_muqarnas_tiers(tau, sun_dx, sun_dy, apex_ox, apex_oy):
    """
    Renders all 8 corbelled Muqarnas tiers with deep star-polygon indentation:
    - Outer pointed arch apex at (r_out, a_mid)
    - Shoulder brackets at (r_mid, angles) and (r_mid, a_next)
    - Deep cantilevered stalactite pendant tip at (r_in, a_mid)
    - Interlocking valley recess at (r_mid * 0.88, angles)
    This geometry turns every niche into a pointed 3D diamond/almond (badam) and star bracket!
    """
    omega = 2.0 * math.pi
    boss_list = []

    for t_idx, (n_sym, r_out_b, r_mid_b, r_in_b, z_h, m_l, m_r, m_s, p_shift) in enumerate(TIERS_SPEC):
        wave = math.sin(omega * tau - t_idx * 0.65 + RND_VAULT_PHASE)
        breath = 1.0 + 0.036 * wave
        rot_twist = 0.022 * math.sin(omega * tau + t_idx * 0.5) * (1 if t_idx % 2 == 0 else -1)

        r_out = r_out_b * breath
        r_mid = r_mid_b * (1.0 + 0.048 * wave)
        r_in = r_in_b * (1.0 - 0.035 * wave)

        tcx = CX + apex_ox * (z_h ** 1.3)
        tcy = CY + apex_oy * (z_h ** 1.3)

        sh_x = tcx - sun_dx * (13.0 * (1.0 - 0.35 * z_h))
        sh_y = tcy - sun_dy * (13.0 * (1.0 - 0.35 * z_h))

        d_theta = 2.0 * math.pi / n_sym
        angles = np.arange(n_sym, dtype=np.float64) * d_theta + p_shift * d_theta + rot_twist
        a_q1 = angles + 0.25 * d_theta
        a_mid = angles + 0.50 * d_theta
        a_q3 = angles + 0.75 * d_theta
        a_next = angles + d_theta

        co_l, si_l = np.cos(angles), np.sin(angles)
        co_q1, si_q1 = np.cos(a_q1), np.sin(a_q1)
        co_m, si_m = np.cos(a_mid), np.sin(a_mid)
        co_q3, si_q3 = np.cos(a_q3), np.sin(a_q3)
        co_r, si_r = np.cos(a_next), np.sin(a_next)

        # True Star-Polygon Muqarnas Vertices:
        # Outer arch peak (out_mx, out_my) projects to r_out; outer shoulders sit at r_mid * 1.04
        r_shoulder = r_mid * 1.04
        out_lx, out_ly = tcx + co_l * r_shoulder, tcy + si_l * r_shoulder
        out_mx, out_my = tcx + co_m * r_out, tcy + si_m * r_out
        out_rx, out_ry = tcx + co_r * r_shoulder, tcy + si_r * r_shoulder

        # Intermediate groin ridge at r_mid * 0.88
        r_groin = r_mid * 0.86
        mid_lx, mid_ly = tcx + co_q1 * r_mid, tcy + si_q1 * r_mid
        mid_mx, mid_my = tcx + co_m * r_groin, tcy + si_m * r_groin
        mid_rx, mid_ry = tcx + co_q3 * r_mid, tcy + si_q3 * r_mid

        # Inner cantilevered stalactite pendant tip (in_mx, in_my) projects deeply inward to r_in
        # while valley corners (in_lx, in_ly) sit at r_groin, forming crisp diamond badam squinches!
        in_lx, in_ly = tcx + co_l * r_groin, tcy + si_l * r_groin
        in_mx, in_my = tcx + co_m * r_in, tcy + si_m * r_in
        in_rx, in_ry = tcx + co_r * r_groin, tcy + si_r * r_groin

        # 1. Deep Star-Shaped Cast Overhang Shadow onto the Tier Below
        py5.no_stroke()
        py5.fill(14, 10, 8, 105)
        with py5.begin_shape():
            for k in range(n_sym):
                py5.vertex(float(sh_x + co_l[k] * (r_shoulder + 12.0)), float(sh_y + si_l[k] * (r_shoulder + 12.0)))
                py5.vertex(float(sh_x + co_m[k] * (r_out + 16.0)), float(sh_y + si_m[k] * (r_out + 16.0)))
        py5.end_shape(py5.CLOSE)

        # 2. Group the 4 Diamond/Almond Facets per Cell into Quantized Shade Buckets for Fast Rendering
        facet_buckets = {}
        elev_boost = 0.86 + 0.22 * z_h

        for k in range(n_sym):
            n_left_ang = a_mid[k] - 0.48
            n_right_ang = a_mid[k] + 0.48
            dot_l = -(math.cos(n_left_ang) * sun_dx + math.sin(n_left_ang) * sun_dy)
            dot_r = -(math.cos(n_right_ang) * sun_dx + math.sin(n_right_ang) * sun_dy)
            dot_s = -(co_m[k] * sun_dx + si_m[k] * sun_dy)

            b_l = 2 if dot_l > 0.28 else (0 if dot_l < -0.28 else 1)
            b_r = 2 if dot_r > 0.28 else (0 if dot_r < -0.28 else 1)
            b_s1 = 2 if dot_s > 0.25 else (0 if dot_s < -0.25 else 1)
            b_s2 = 0 if dot_s > 0.25 else (2 if dot_s < -0.25 else 1)

            # Facet A: Outer Left Pointed Hood (out_L -> out_M -> mid_M -> in_L)
            key_a = (m_l, b_l)
            facet_buckets.setdefault(key_a, []).extend([
                [out_lx[k], out_ly[k]],
                [out_mx[k], out_my[k]],
                [mid_mx[k], mid_my[k]],
                [in_lx[k], in_ly[k]],
            ])

            # Facet B: Outer Right Pointed Hood (out_M -> out_R -> in_R -> mid_M)
            key_b = (m_r, b_r)
            facet_buckets.setdefault(key_b, []).extend([
                [out_mx[k], out_my[k]],
                [out_rx[k], out_ry[k]],
                [in_rx[k], in_ry[k]],
                [mid_mx[k], mid_my[k]],
            ])

            # Facet C: Inner Left Badam Diamond Squinch (in_L -> mid_L -> mid_M -> in_M)
            mat_c = m_s if (k % 2 == 0) else m_l
            key_c = (mat_c, b_s1)
            facet_buckets.setdefault(key_c, []).extend([
                [in_lx[k], in_ly[k]],
                [mid_lx[k], mid_ly[k]],
                [mid_mx[k], mid_my[k]],
                [in_mx[k], in_my[k]],
            ])

            # Facet D: Inner Right Badam Diamond Squinch (mid_M -> mid_R -> in_R -> in_M)
            mat_d = m_s if (k % 2 == 0) else m_r
            key_d = (mat_d, b_s2)
            facet_buckets.setdefault(key_d, []).extend([
                [mid_mx[k], mid_my[k]],
                [mid_rx[k], mid_ry[k]],
                [in_rx[k], in_ry[k]],
                [in_mx[k], in_my[k]],
            ])

        py5.stroke(38, 28, 18, 220)
        py5.stroke_weight(1.4)
        shade_factors = (0.78 * elev_boost, 0.96 * elev_boost, 1.14 * elev_boost)
        for (mat_i, sh_i), v_list in facet_buckets.items():
            rgb = np.clip(MATERIALS[mat_i] * shade_factors[sh_i], 16.0, 255.0)
            py5.fill(float(rgb[0]), float(rgb[1]), float(rgb[2]))
            with py5.begin_shape(py5.QUADS):
                py5.vertices(np.array(v_list, dtype=np.float64))

        # 3. Internal Fluted Muqarnas Fan Ribs & Gilded Star Arch Ribs
        segs = np.empty((n_sym * 5, 4), dtype=np.float64)
        segs[0::5] = np.column_stack([out_mx, out_my, mid_mx, mid_my])
        segs[1::5] = np.column_stack([mid_mx, mid_my, in_mx, in_my])
        segs[2::5] = np.column_stack([in_mx, in_my, mid_lx, mid_ly])
        segs[3::5] = np.column_stack([in_mx, in_my, mid_rx, mid_ry])
        segs[4::5] = np.column_stack([out_mx, out_my, in_lx, in_ly])
        py5.stroke(252, 245, 225, 205)
        py5.stroke_weight(1.5)
        py5.lines(segs)

        if t_idx in (1, 2, 4, 5, 6):
            for k in range(n_sym):
                if n_sym == 32 and k % 2 != 0:
                    continue
                boss_list.append((float(in_mx[k]), float(in_my[k]), t_idx))

    # 4. Grand Interlaced {16/5} Abencerrajes Gilded Star Vault Ribs across the Cupola
    r_star_out = 485.0
    r_star_in = 205.0
    star_segs = []
    for k_s in range(16):
        a1 = k_s * math.pi / 8.0 + 0.018 * math.sin(omega * tau)
        a2 = ((k_s + 5) % 16) * math.pi / 8.0 + 0.018 * math.sin(omega * tau)
        star_segs.append([
            CX + apex_ox * 0.55 + math.cos(a1) * r_star_out,
            CY + apex_oy * 0.55 + math.sin(a1) * r_star_out,
            CX + apex_ox * 0.75 + math.cos(a2) * r_star_in,
            CY + apex_oy * 0.75 + math.sin(a2) * r_star_in,
        ])
    star_arr = np.array(star_segs, dtype=np.float64)
    py5.stroke(42, 30, 18, 210)
    py5.stroke_weight(5.2)
    py5.lines(star_arr)
    py5.stroke(238, 188, 62, 235)
    py5.stroke_weight(2.6)
    py5.lines(star_arr)

    # 5. Hanging Stalactite Pendant Bosses (Shabaka Finials)
    py5.stroke(45, 32, 18, 230)
    py5.stroke_weight(1.5)
    for (bx, by, t_idx) in boss_list:
        py5.fill(222, 162, 38) if t_idx % 2 == 0 else py5.fill(244, 238, 224)
        r_b = 7.5 if t_idx < 5 else 6.0
        py5.circle(bx, by, r_b * 2.0)

    # Central Sunlit Shamsa Rosette Apex Jewel
    apex_x = CX + apex_ox
    apex_y = CY + apex_oy
    py5.stroke(48, 34, 18, 235)
    py5.stroke_weight(2.2)
    py5.fill(254, 240, 138)
    py5.circle(apex_x, apex_y, 30.0)
    py5.fill(26, 66, 114)
    py5.circle(apex_x, apex_y, 14.0)


def draw_card_box(x, y, w, h, title, subtitle):
    """Draws a warm architectural stereotomy drafting card in a corner."""
    py5.no_stroke()
    py5.fill(58, 44, 30, 32)
    py5.rect(x + 8, y + 8, w, h, 8)
    py5.stroke(128, 102, 74, 215)
    py5.stroke_weight(2.2)
    py5.fill(250, 246, 238, 242)
    py5.rect(x, y, w, h, 8)
    py5.stroke(182, 158, 128, 155)
    py5.stroke_weight(1.2)
    py5.no_fill()
    py5.rect(x + 10, y + 10, w - 20, h - 20, 4)
    py5.fill(48, 36, 24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(21)
    py5.text(title, x + 26, y + 22)
    py5.fill(186, 78, 32)
    py5.text_size(15)
    py5.text(subtitle, x + 26, y + 50)
    py5.stroke(168, 142, 112, 165)
    py5.stroke_weight(1.4)
    py5.line(x + 24, y + 76, x + w - 24, y + 76)


def draw_stereotomy_apparatuses(tau, sun_angle):
    """Draws eight Al-Kashi (1427) Muqarnas stereotomy apparatuses across four balanced flank cards."""
    omega = 2.0 * math.pi
    cw = 760
    ch_top = 835
    ch_bot = 845

    # --- Top-Left Card (y=210..1045): FIG. 01 AL-KASHI MODULAR ELEMENTS & FIG. 02 PROFILE CURVE ---
    x1, y1 = 110, 210
    draw_card_box(x1, y1, cw, ch_top,
                  "FIG. 01 // AL-KASHI (1427) PLANAR MODULAR TAXONOMY",
                  "MIFTAH AL-HISAB ELEMENT SET: SQUARE, RHOMBUS, ALMOND (BADAM) & BIPED")

    elem_specs = [
        ("SQUARE (MURABBA)", 90.0, (26, 66, 114)),
        ("ALMOND (BADAM)", 45.0, (28, 108, 84)),
        ("BARLEYCORN (SHA'IRA)", 22.5, (204, 102, 42)),
        ("BIPED (SHABAKA)", 67.5, (222, 162, 38)),
    ]
    for e_i, (e_name, e_deg, e_col) in enumerate(elem_specs):
        ex = x1 + 112 + e_i * 178
        ey = y1 + 195
        er = 54.0
        rad_half = math.radians(e_deg * 0.5)
        py5.stroke(48, 36, 24, 220)
        py5.stroke_weight(2.2)
        py5.fill(e_col[0], e_col[1], e_col[2], 215)
        with py5.begin_shape():
            py5.vertex(ex, ey - er)
            py5.vertex(ex + er * math.sin(rad_half), ey)
            py5.vertex(ex, ey + er)
            py5.vertex(ex - er * math.sin(rad_half), ey)
        py5.end_shape(py5.CLOSE)
        py5.no_stroke()
        py5.fill(48, 36, 24)
        py5.text_align(py5.CENTER, py5.TOP)
        py5.text_size(13)
        py5.text(e_name, ex, ey + er + 14)
        py5.fill(186, 78, 32)
        py5.text(f"APEX = {e_deg:.1f} DEG", ex, ey + er + 34)

    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(62, 48, 34)
    py5.text_size(15)
    py5.text("MIQYAS (MODULAR UNIT m) : BASE = 1.000 m   //   DIAGONAL = SQRT(2) m   //   COMPLEMENT = (2 - SQRT(2)) m", x1 + 32, y1 + 335)

    py5.stroke(168, 142, 112, 165)
    py5.stroke_weight(1.4)
    py5.line(x1 + 24, y1 + 405, x1 + cw - 24, y1 + 405)
    py5.fill(48, 36, 24)
    py5.text_size(20)
    py5.text("FIG. 02 // AL-KASHI CONCAVE NICHE HOOD PROFILE (TASA)", x1 + 26, y1 + 425)
    py5.fill(186, 78, 32)
    py5.text_size(15)
    py5.text("GEOMETRIC CONSTRUCTION OF CORBELLED OVERHANG & POINTED ARCH CURVATURE", x1 + 26, y1 + 452)

    px0, py0 = x1 + 75, y1 + 755
    pw, ph = 240.0, 230.0
    py5.stroke(175, 152, 125, 160)
    py5.stroke_weight(1.4)
    py5.no_fill()
    py5.rect(px0, py0 - ph, pw, ph)
    py5.stroke(26, 66, 114, 235)
    py5.stroke_weight(3.5)
    py5.fill(222, 162, 38, 65)
    with py5.begin_shape():
        py5.vertex(px0, py0)
        py5.vertex(px0, py0 - ph * 0.38)
        for s_i in range(25):
            u = s_i / 24.0
            ang_p = u * math.pi * 0.48
            cx_p = px0 + pw * (1.0 - math.cos(ang_p))
            cy_p = py0 - ph * 0.38 - (ph * 0.62) * math.sin(ang_p)
            py5.vertex(cx_p, cy_p)
        py5.vertex(px0 + pw, py0 - ph)
        py5.vertex(px0, py0 - ph)
    py5.end_shape(py5.CLOSE)

    tx1 = x1 + 355
    py5.no_stroke()
    py5.fill(48, 36, 24)
    py5.text_size(15)
    py5.text("TIER HEIGHT (H)       : 2.00 MIQYAS UNITS", tx1, y1 + 515)
    py5.text("CANTILEVER SPAN (S)   : 1.00 MIQYAS UNIT", tx1, y1 + 549)
    py5.text("VERTICAL RISER (R)    : 0.382 H (GOLDEN STEP)", tx1, y1 + 583)
    py5.fill(26, 66, 114)
    py5.text("ARCH RADIUS (R_ARC)   : 1.155 S (2 / SQRT 3)", tx1, y1 + 625)
    py5.fill(28, 108, 84)
    py5.text("SURFACE AREA FACTOR   : 1.685 x PLANAR FOOTPRINT", tx1, y1 + 659)
    py5.fill(186, 78, 32)
    py5.text("TREATISE SOURCE       : SAMARKAND, 1427 CE", tx1, y1 + 693)

    # --- Bottom-Left Card (y=1085..1930): FIG. 03 STEPPED CORBEL CANTILEVER & FIG. 04 NASRID GLAZES ---
    x2, y2 = 110, 1085
    draw_card_box(x2, y2, cw, ch_bot,
                  "FIG. 03 // EIGHT-TIER CORBELLED CANTILEVER ELEVATION (TABAQAT)",
                  "STEPPED STEREOTOMIC OVERHANG FROM OCTAGONAL DRUM TO SHAMSA KEYSTONE")

    sec_cx = x2 + 380
    sec_by = y2 + 325
    breath_sec = 0.5 + 0.5 * math.sin(omega * tau)
    for t_i in range(7):
        y_bot_t = sec_by - t_i * 28.0
        y_top_t = y_bot_t - 28.0
        span_b = 275.0 - t_i * 34.0 - 6.0 * breath_sec
        span_t = 275.0 - (t_i + 1) * 34.0 - 6.0 * breath_sec
        py5.stroke(48, 36, 24, 220)
        py5.stroke_weight(1.8)
        col_t = MATERIALS[t_i % 6]
        py5.fill(float(col_t[0]), float(col_t[1]), float(col_t[2]), 225)
        py5.quad(sec_cx - 310, y_bot_t, sec_cx - span_b, y_bot_t,
                 sec_cx - span_t, y_top_t, sec_cx - 310, y_top_t)
        py5.quad(sec_cx + span_b, y_bot_t, sec_cx + 310, y_bot_t,
                 sec_cx + 310, y_top_t, sec_cx + span_t, y_top_t)

    py5.fill(222, 162, 38)
    py5.rect(sec_cx - 38, sec_by - 7 * 28.0 - 18, 76, 22, 2)
    py5.no_stroke()
    py5.fill(48, 36, 24)
    py5.text_size(15)
    py5.text("CATENARY THRUST LINE : CONTAINED WITHIN MIDDLE THIRD OF MASONRY DRUM WALL", x2 + 48, sec_by + 16)

    py5.stroke(168, 142, 112, 165)
    py5.stroke_weight(1.4)
    py5.line(x2 + 24, y2 + 375, x2 + cw - 24, y2 + 375)
    py5.fill(48, 36, 24)
    py5.text_size(20)
    py5.text("FIG. 04 // NASRID STUCCO (YESERIA) & CERAMIC GLAZE PALETTE", x2 + 26, y2 + 395)
    py5.fill(186, 78, 32)
    py5.text_size(15)
    py5.text("MINERAL PIGMENTATION & CARVED GYPSUM POLYCHROMY OF THE ALHAMBRA", x2 + 26, y2 + 422)

    mat_labels = [
        (0, "YESERIA GYPSUM STUCCO // CARVED CALCIUM SULFATE DIHYDRATE"),
        (1, "SIERRA ELVIRA LIMESTONE // STRUCTURAL SQUINCH RISERS"),
        (2, "LAJWARD LAPIS COBALT // GLAZED ZELLIJ CERAMIC INLAY"),
        (3, "ALHAMBRA CELADON EMERALD // COPPER OXIDE TIN GLAZE"),
        (4, "GRANADA TERRACOTTA OCHRE // FIRED IRON-CLAY BRACKET"),
        (5, "SHAMSA BURNISHED GOLD LEAF // 24K GILDED CUPOLA RIBS"),
    ]
    for m_i, (m_idx, m_lbl) in enumerate(mat_labels):
        by = y2 + 472 + m_i * 54
        rgb = MATERIALS[m_idx]
        py5.stroke(48, 36, 24, 210)
        py5.stroke_weight(1.6)
        py5.fill(float(rgb[0]), float(rgb[1]), float(rgb[2]))
        py5.rect(x2 + 38, by, 48, 28, 3)
        py5.no_stroke()
        py5.fill(48, 36, 24)
        py5.text_size(15)
        py5.text(m_lbl, x2 + 104, by + 6)

    # --- Top-Right Card (y=210..1045): FIG. 05 16-FOLD SHAMSA STAR & FIG. 06 CLERESTORY SUN COMPASS ---
    x3, y3 = WIDTH - cw - 110, 210
    draw_card_box(x3, y3, cw, ch_top,
                  "FIG. 05 // 16-POINTED SHAMSA CUPOLA GEOMETRY ({16/6} STAR)",
                  "DIHEDRAL GROUP D_16 SYMMETRY & INTERLACED CHORD PROPORTIONS")

    scx, scy = x3 + 205, y3 + 245
    sr3 = 122.0
    py5.stroke(168, 142, 112, 160)
    py5.stroke_weight(1.6)
    py5.fill(245, 239, 226)
    py5.circle(scx, scy, sr3 * 2.0)
    py5.stroke(26, 66, 114, 225)
    py5.stroke_weight(2.2)
    for k_s in range(16):
        a1 = k_s * math.pi / 8.0 + tau * omega * 0.25
        a2 = ((k_s + 6) % 16) * math.pi / 8.0 + tau * omega * 0.25
        py5.line(scx + math.cos(a1) * sr3, scy + math.sin(a1) * sr3,
                 scx + math.cos(a2) * sr3, scy + math.sin(a2) * sr3)
    py5.fill(222, 162, 38)
    py5.circle(scx, scy, 32.0)

    tx3 = x3 + 368
    py5.no_stroke()
    py5.fill(48, 36, 24)
    py5.text_size(15)
    py5.text("SYMMETRY GROUP       : DIHEDRAL D_16 / D_32", tx3, y3 + 105)
    py5.text("FUNDAMENTAL SECTOR   : 360 / 32 = 11.25 DEG", tx3, y3 + 139)
    py5.text("STAR POLYGRAM        : {16/6} & {16/5} ROSETTE", tx3, y3 + 173)
    py5.text("CORBEL TIER COUNT    : 8 TABAQAT RINGS", tx3, y3 + 207)
    py5.fill(26, 66, 114)
    py5.text("TOTAL VAULT NICHES   : 176 CONCAVE CELLS", tx3, y3 + 245)
    py5.fill(28, 108, 84)
    py5.text("FACET POLYGON COUNT  : 704 STEREOTOMIC QUADS", tx3, y3 + 279)
    py5.fill(186, 78, 32)
    py5.text("CLERESTORY WINDOWS   : 16 OCULUS LANCETS", tx3, y3 + 313)

    py5.stroke(168, 142, 112, 165)
    py5.stroke_weight(1.4)
    py5.line(x3 + 24, y3 + 405, x3 + cw - 24, y3 + 405)
    py5.fill(48, 36, 24)
    py5.text_size(20)
    py5.text("FIG. 06 // CLERESTORY SOLAR INCIDENCE & SHADOW COMPASS", x3 + 26, y3 + 425)
    py5.fill(186, 78, 32)
    py5.text_size(15)
    py5.text("DIURNAL LIGHT SHAFT ROTATION ACROSS CONCAVE MUQARNAS FACETS", x3 + 26, y3 + 452)

    ccx, ccy = x3 + 205, y3 + 640
    cr = 114.0
    py5.stroke(120, 96, 72, 195)
    py5.stroke_weight(2.0)
    py5.fill(245, 238, 224)
    py5.circle(ccx, ccy, cr * 2.0)
    py5.stroke(170, 148, 120, 140)
    py5.circle(ccx, ccy, cr * 1.35)
    py5.line(ccx - cr - 12, ccy, ccx + cr + 12, ccy)
    py5.line(ccx, ccy - cr - 12, ccx, ccy + cr + 12)

    sx_tip = ccx + math.cos(sun_angle) * (cr - 10)
    sy_tip = ccy + math.sin(sun_angle) * (cr - 10)
    py5.stroke(204, 102, 42, 240)
    py5.stroke_weight(4.0)
    py5.line(ccx, ccy, sx_tip, sy_tip)
    py5.fill(222, 162, 38)
    py5.stroke(120, 45, 25)
    py5.stroke_weight(1.8)
    py5.circle(sx_tip, sy_tip, 18)
    py5.fill(48, 36, 24)
    py5.circle(ccx, ccy, 10)

    py5.no_stroke()
    py5.fill(48, 36, 24)
    py5.text_size(15)
    az_deg = math.degrees(sun_angle) % 360.0
    py5.text(f"SOLAR AZIMUTH ANGLE  : {az_deg:6.2f} DEG", tx3, y3 + 520)
    py5.text("CLERESTORY ALTITUDE  : 42.50 DEG OBLIQUE", tx3, y3 + 556)
    py5.text("SHADOW PARALLAX      : 13.0 px / TIER STEP", tx3, y3 + 592)
    py5.fill(26, 66, 114)
    py5.text("ACOUSTIC DIFFUSION   : OMNI-DIRECTIONAL", tx3, y3 + 634)
    py5.fill(28, 108, 84)
    py5.text("THERMAL CONVECTION   : STACK VENTILATION", tx3, y3 + 670)
    py5.fill(186, 78, 32)
    py5.text("EXEMPLAR MONUMENT    : ALHAMBRA, GRANADA", tx3, y3 + 706)

    # --- Bottom-Right Card (y=1085..1930): FIG. 07 TASARIM PROJECTION & FIG. 08 HARMONIC WAVE ---
    x4, y4 = WIDTH - cw - 110, 1085
    draw_card_box(x4, y4, cw, ch_bot,
                  "FIG. 07 // 2D TASARIM TO 3D TABAQAT STEREOTOMIC MAPPING",
                  "ORTHOGONAL PLANAR PROJECTION OF OVERHANGING VAULT BRACKETS")

    mp_x, mp_y = x4 + 55, y4 + 115
    py5.stroke(148, 122, 92, 190)
    py5.stroke_weight(1.8)
    py5.fill(244, 238, 226)
    py5.rect(mp_x, mp_y, 260, 215, 4)
    p_cx, p_cy = mp_x + 130, mp_y + 108
    for k_p in range(8):
        pa = k_p * math.pi / 4.0 + tau * omega * 0.25
        pa2 = ((k_p + 3) % 8) * math.pi / 4.0 + tau * omega * 0.25
        py5.stroke(26, 66, 114, 200)
        py5.line(p_cx + math.cos(pa) * 85, p_cy + math.sin(pa) * 85,
                 p_cx + math.cos(pa2) * 85, p_cy + math.sin(pa2) * 85)
    py5.stroke(204, 102, 42, 220)
    py5.no_fill()
    py5.circle(p_cx, p_cy, 95)

    tx4 = x4 + 345
    py5.no_stroke()
    py5.fill(48, 36, 24)
    py5.text_size(15)
    py5.text("PLANAR GRAPH (G)     : V = 145, E = 288, F = 144", tx4, y4 + 118)
    py5.text("LIFTING OPERATOR     : Z(r) = H_max * (1 - (r/R)^2)", tx4, y4 + 152)
    py5.text("PENDANT DROP (DELTA) : -0.22 * H_tier AT VERTICES", tx4, y4 + 186)
    py5.fill(26, 66, 114)
    py5.text("RECIPROCAL EQUILIBRIUM: ZERO TENSILE HOOP STRESS", tx4, y4 + 228)
    py5.fill(28, 108, 84)
    py5.text("MORTAR JOINT WIDTH   : 2.0 mm GYPSUM PLASTER", tx4, y4 + 262)
    py5.fill(186, 78, 32)
    py5.text("DOME SPAN RATIO      : H / D = 0.618 (GOLDEN)", tx4, y4 + 296)

    py5.stroke(168, 142, 112, 165)
    py5.stroke_weight(1.4)
    py5.line(x4 + 24, y4 + 375, x4 + cw - 24, y4 + 375)
    py5.fill(48, 36, 24)
    py5.text_size(20)
    py5.text("FIG. 08 // HARMONIC CORBEL CANTILEVER DISPLACEMENT WAVE", x4 + 26, y4 + 395)
    py5.fill(186, 78, 32)
    py5.text_size(15)
    py5.text("COUPLED RADIAL OVERHANG & ILLUMINATION INTENSITY ACROSS TIERS 1 - 8", x4 + 26, y4 + 422)

    wx0, wy0, ww, wh = x4 + 55, y4 + 475, 650, 260
    py5.stroke(145, 122, 95, 180)
    py5.stroke_weight(1.6)
    py5.fill(245, 239, 228)
    py5.rect(wx0, wy0, ww, wh, 4)
    py5.stroke(210, 195, 175, 140)
    py5.stroke_weight(1.0)
    for gy_i in range(1, 4):
        py5.line(wx0, wy0 + gy_i * wh / 4.0, wx0 + ww, wy0 + gy_i * wh / 4.0)
    for gx_i in range(1, 6):
        py5.line(wx0 + gx_i * ww / 6.0, wy0, wx0 + gx_i * ww / 6.0, wy0 + wh)

    wave_cols = [(26, 66, 114), (28, 108, 84), (204, 102, 42)]
    for c_idx, col in enumerate(wave_cols):
        py5.no_fill()
        py5.stroke(col[0], col[1], col[2], 235)
        py5.stroke_weight(3.0)
        with py5.begin_shape():
            for p_i in range(66):
                u = p_i / 65.0
                px_w = wx0 + u * ww
                val = math.sin(omega * tau - u * 5.0 + c_idx * 1.15) * math.cos(u * 2.5 - omega * tau * 0.5)
                py_w = wy0 + wh * 0.5 - val * (wh * 0.36)
                py5.vertex(px_w, py_w)
        py5.end_shape()

    py5.no_stroke()
    py5.fill(62, 48, 34)
    py5.text_size(15)
    py5.text("LAPIS: DRUM SQUINCHES   //   EMERALD: HONEYCOMB TIERS   //   OCHRE: SHAMSA CUPOLA", wx0, wy0 + wh + 22)


def draw_archival_border_and_typography(tau):
    """Draws double-ruled museum border and scholarly typography without any personal signatures."""
    py5.no_fill()
    py5.stroke(96, 74, 52, 215)
    py5.stroke_weight(3.5)
    py5.rect(64, 64, WIDTH - 128, HEIGHT - 128, 6)

    py5.stroke(148, 122, 92, 165)
    py5.stroke_weight(1.5)
    py5.rect(78, 78, WIDTH - 156, HEIGHT - 156, 4)

    py5.fill(48, 36, 24)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(38)
    py5.text("MUQARNAS // CORBELLED STALACTITE VAULT STEREOTOMY & AL-KASHI GEOMETRY", WIDTH / 2.0, 98)

    py5.fill(186, 78, 32)
    py5.text_size(21)
    py5.text("MIFTAH AL-HISAB (1427) - EIGHT-TIER TABAQAT CANTILEVER - 16-FOLD SHAMSA CUPOLA PROJECTION", WIDTH / 2.0, 150)

    py5.fill(78, 58, 42)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(20)
    py5.text("TREATISE: JAMSHID AL-KASHI (1427) // EXEMPLAR: HALL OF THE ABENCERRAJES (ALHAMBRA) // 704 VAULT FACETS", 108, HEIGHT - 88)

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(f"4K ARCHITECTURAL STEREOTOMY // HARMONIC PHASE TAU = {tau:.3f} (12.0s @ 60FPS)", WIDTH - 108, HEIGHT - 88)


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
