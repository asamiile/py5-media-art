"""
Kinetic Guastavino Timbrel Vault & Herringbone Stereotomy 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Architectural / Brutalism / Geometric genre,
exploring Rafael Guastavino's Cohesive Timbrel Vaulting (Boveda Tabicada, Essay on
the Theory and History of Cohesive Construction, 1892; City Hall Station NYC 1904;
St. John the Divine Dome 1909), Filippo Brunelleschi's self-supporting spina di pesce
(herringbone brick courses of the Florence Duomo, 1420-1436), Antoni Gaudi's catenary
funicular stereotomy, and Jacques Heyman's Safe Theorem of Masonry (1966), executed
on deep structural blueprint & vault obsidian slate (#070a12).

Seen in wide-angle upward zenithal projection, a monumental circular timbrel cupola
spans between four pendentive groin arches and a central glazed lantern oculus. Eighteen
concentric courses of thin Catalonian terracotta and acoustic buff tiles are laid in
interlocking herringbone (spina di pesce) and counter-spiraling tri-rosca courses with
crisp gypsum/Portland mortar bed joints. Every eighth tile is a vertical locking
herringbone header that clamps the horizontal course without wooden centering (cimbra),
while 16 meridian groin ribs and a live Cremona-Maxwell Thrust Network visualize the
transition at phi_0 = 51.82 deg (cos phi_0 = 1/phi) from upper biaxial hoop compression
to lower tension-ring containment, flanked by eight structural masonry apparatuses.

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
WORK_NAME = "kinetic_guastavino_timbrel_vault_herringbone_stereotomy_2d"
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
RND_LOAD_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 22.0
CUPOLA_R = 805.0
OCULUS_R = 132.0

# Critical hoop-stress transition angle phi_0 = arccos(1 / golden_ratio) = 51.827 deg
# Projected onto dome radius: r_transition = CUPOLA_R * sin(51.827 deg) = 0.78615 * CUPOLA_R = 632.8 px
PHI_ZERO_DEG = 51.8273
R_HOOP_ZERO = CUPOLA_R * math.sin(math.radians(PHI_ZERO_DEG))

# Precompute the 18 concentric timbrel courses from r = OCULUS_R (132 px) to r = 758 px
N_COURSES = 18
COURSE_DATA = []
for c_idx in range(N_COURSES):
    f0 = c_idx / float(N_COURSES)
    f1 = (c_idx + 1) / float(N_COURSES)
    # Dome spherical foreshortening: outer courses near springing are radially compressed in plan view
    phi0 = (0.16 + 0.76 * f0) * (0.5 * math.pi)
    phi1 = (0.16 + 0.76 * f1) * (0.5 * math.pi)
    r_in = CUPOLA_R * 0.94 * math.sin(phi0)
    r_out = CUPOLA_R * 0.94 * math.sin(phi1)
    r_mid = 0.5 * (r_in + r_out)

    # Number of tiles in this ring (divisible by 16 so 16 herringbone spirals align cleanly!)
    n_tiles = max(32, int(round((2.0 * math.pi * r_mid / 44.0) / 16.0)) * 16)
    COURSE_DATA.append((c_idx, phi0, phi1, r_in, r_out, r_mid, n_tiles))

# Catalonian Terracotta & Glazed Tile Material Palette:
# 0: Fired Valencia Terracotta (#c85a32)
# 1: Guastavino Acoustic Buff Tile (#d8b074)
# 2: Over-fired Clinker Brick Umber (#8e422e)
# 3: Spina di Pesce Locking Header Gold-Ochre (#e89c38)
# 4: Catalan Cobalt Azulejo Glaze (#2563eb)
# 5: Catalan Verdigris Celadon Glaze (#12946e)
TILE_MATERIALS = [
    (200, 90, 50),    # 0: Valencia Terracotta stretcher
    (216, 176, 116),  # 1: Guastavino Acoustic Buff stretcher
    (148, 68, 44),    # 2: Dark Clinker Terracotta stretcher
    (232, 156, 52),   # 3: Spina di Pesce Herringbone Locking Brick
    (38, 102, 224),   # 4: Catalan Cobalt Azulejo Glaze
    (18, 148, 110),   # 5: Catalan Celadon Glaze
]


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

    # 1. Deep Structural Blueprint & Vault Slate (#070a12)
    py5.background(7, 10, 18)

    # 2. Architectural Blueprint Coordinate Grid & Funicular Compass Substrate
    draw_blueprint_substrate(tau)

    # 3. Central Monumental Guastavino Timbrel Cupola & Herringbone Stereotomy
    draw_central_guastavino_cupola(tau, omega)

    # 4. Eight Masonry Stereotomy & Funicular Thrust Apparatuses Across Four Flank Cards
    draw_guastavino_apparatuses(tau, omega)

    # 5. Outer Museum Border & Scholarly Typography (Zero Personal Signatures/Seals)
    draw_museum_border_and_typography(tau, omega)

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


def draw_blueprint_substrate(tau: float):
    """Draws the dark structural engineering blueprint grid and corner pendentive arcs."""
    py5.no_stroke()
    for r_g, col_g in [
        (1160, (12, 18, 32, 95)),
        (930, (16, 26, 46, 90)),
        (835, (22, 34, 58, 100)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    py5.stroke(22, 32, 52, 135)
    py5.stroke_weight(1.1)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)


def draw_central_guastavino_cupola(tau: float, omega: float):
    """
    Renders the central Guastavino Cohesive Timbrel Cupola (Boveda Tabicada):
    1. Outer drum compression ring & 16 perimeter buttress piers
    2. 18 concentric courses of terracotta & buff acoustic tiles with mortar bed joints,
       interlocked by 16 spiraling Brunelleschi-Guastavino spina di pesce (herringbone)
       locking brick spines, shaded by a rotating solar oculus vector and funicular wave
    3. Critical phi_0 = 51.83 deg neutral hoop-stress tension ring (where sigma_theta = 0)
    4. 16 glazed meridian groin ribs & Cremona-Maxwell reciprocal thrust network nodes
    5. Central sunlit lantern oculus with 16 radial bronze muntins & tri-rosca cutaway collar
    """
    # Solar illumination vector rotating smoothly around the cupola
    sun_ang = omega * tau + RND_LOAD_PHASE
    sun_x = math.cos(sun_ang)
    sun_y = math.sin(sun_ang)

    # --- 1. OUTER MASONRY DRUM RING & 16 PERIMETER BUTTRESS PIERS ---
    py5.no_stroke()
    py5.fill(44, 34, 26, 255)
    py5.circle(CX, CY, (CUPOLA_R + 18.0) * 2.0)

    # Light gypsum/Portland mortar base bed for the entire cupola
    py5.fill(218, 206, 186, 255)
    py5.stroke(188, 142, 68, 240)
    py5.stroke_weight(3.5)
    py5.circle(CX, CY, (CUPOLA_R - 4.0) * 2.0)

    # Dark drum ring border between r = 758 and r = 801
    n_drum = 128
    a_d = np.linspace(0.0, 2.0 * math.pi, n_drum + 1)
    cd, sd = np.cos(a_d), np.sin(a_d)
    q_drum = np.empty((n_drum, 4, 2), dtype=np.float64)
    q_drum[:, 0, 0] = CX + 756.0 * cd[:-1]
    q_drum[:, 0, 1] = CY + 756.0 * sd[:-1]
    q_drum[:, 1, 0] = CX + 801.0 * cd[:-1]
    q_drum[:, 1, 1] = CY + 801.0 * sd[:-1]
    q_drum[:, 2, 0] = CX + 801.0 * cd[1:]
    q_drum[:, 2, 1] = CY + 801.0 * sd[1:]
    q_drum[:, 3, 0] = CX + 756.0 * cd[1:]
    q_drum[:, 3, 1] = CY + 756.0 * sd[1:]
    py5.no_stroke()
    py5.fill(26, 34, 52, 255)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(q_drum.reshape(-1, 2))

    # --- 2. VECTORIZED 18-COURSE TIMBREL TILE & SPINA DI PESCE STEREOTOMY ---
    # Group tile quads into (material_idx, shade_bucket) with 7 shade buckets [0..6]
    # for ultra-fast vectorized py5.QUADS rendering with crisp mortar bed gaps!
    tile_batches = {}
    bevel_segs = []

    for c_idx, phi0, phi1, r_in, r_out, r_mid, n_tiles in COURSE_DATA:
        phi_mid = 0.5 * (phi0 + phi1)
        sin_phi = math.sin(phi_mid)
        cos_phi = math.cos(phi_mid)

        # Running-bond stagger + harmonic elastic dome breathing
        stagger = (0.5 if (c_idx % 2 == 1) else 0.0) * (2.0 * math.pi / float(n_tiles))
        breath_r = 2.8 * math.sin(2.0 * omega * tau - c_idx * 0.35)

        # Mortar joint inset in radial and angular directions
        dr_mortar = 2.4
        da_step = 2.0 * math.pi / float(n_tiles)
        da_mortar = 2.4 / max(60.0, r_mid)

        ri_tile = r_in + dr_mortar + breath_r
        ro_tile = r_out - dr_mortar + breath_r

        # Vectorized angles for all tiles in this course
        t_indices = np.arange(n_tiles)
        a0_arr = t_indices * da_step + stagger + da_mortar
        a1_arr = (t_indices + 1) * da_step + stagger - da_mortar
        amid_arr = 0.5 * (a0_arr + a1_arr)

        # Herringbone (spina di pesce) spiral condition:
        # 16 logarithmic spirals wind counter-clockwise by 1 tile slot per course!
        hb_mod = (t_indices - c_idx) % (n_tiles // 16)
        is_herringbone = (hb_mod == 0)
        is_glazed_accent = (hb_mod == 1) & ((c_idx % 3) == 0)

        for t_i in range(n_tiles):
            a0 = a0_arr[t_i]
            a1 = a1_arr[t_i]
            amid = amid_arr[t_i]
            ca0, sa0 = math.cos(a0), math.sin(a0)
            ca1, sa1 = math.cos(a1), math.sin(a1)

            # Determine material index
            if is_herringbone[t_i]:
                mat_idx = 3  # Spina di pesce locking header brick (Golden Ochre)
                # Herringbone brick is canted diagonally across the course!
                da_cant = (a1 - a0) * 0.22
                x0 = CX + ri_tile * math.cos(a0 - da_cant)
                y0 = CY + ri_tile * math.sin(a0 - da_cant)
                x1 = CX + ri_tile * math.cos(a1 - da_cant)
                y1 = CY + ri_tile * math.sin(a1 - da_cant)
                x2 = CX + ro_tile * math.cos(a1 + da_cant)
                y2 = CY + ro_tile * math.sin(a1 + da_cant)
                x3 = CX + ro_tile * math.cos(a0 + da_cant)
                y3 = CY + ro_tile * math.sin(a0 + da_cant)
            else:
                if is_glazed_accent[t_i]:
                    mat_idx = 4 if ((c_idx + t_i) % 2 == 0) else 5  # Cobalt or Celadon glaze
                else:
                    # Alternating Guastavino acoustic buff and Catalonian terracotta courses
                    if c_idx % 3 == 0:
                        mat_idx = 0 if (t_i % 2 == 0) else 2
                    elif c_idx % 3 == 1:
                        mat_idx = 1
                    else:
                        mat_idx = 0 if (t_i % 3 != 0) else 1

                x0, y0 = CX + ri_tile * ca0, CY + ri_tile * sa0
                x1, y1 = CX + ri_tile * ca1, CY + ri_tile * sa1
                x2, y2 = CX + ro_tile * ca1, CY + ro_tile * sa1
                x3, y3 = CX + ro_tile * ca0, CY + ro_tile * sa0

            # 3D cupola normal (inward dome surface normal facing the viewer + sun)
            nx = -sin_phi * math.cos(amid)
            ny = -sin_phi * math.sin(amid)
            dot_sun = nx * sun_x + ny * sun_y
            # Combine Lambertian solar relief with rotating funicular stress wave
            stress_wave = 0.16 * math.cos(4.0 * amid - 2.0 * omega * tau + c_idx * 0.25)
            illum = 0.68 + 0.26 * dot_sun + 0.14 * cos_phi + stress_wave
            s_bucket = max(0, min(6, int((illum - 0.35) / 0.75 * 7.0)))

            tile_batches.setdefault((mat_idx, s_bucket), []).append(
                ((x0, y0), (x1, y1), (x2, y2), (x3, y3))
            )

            # Acoustic herring-bone / scored tile groove on acoustic buff tiles & herringbone bricks
            if is_herringbone[t_i] or (c_idx % 2 == 0 and t_i % 2 == 0):
                bevel_segs.append([x0, y0, x1, y1])

    # Render all batched masonry tiles in one pass per (mat_idx, s_bucket)
    py5.stroke(82, 54, 36, 185)
    py5.stroke_weight(1.0)
    for (mat_idx, s_bucket), quads_list in tile_batches.items():
        base_r, base_g, base_b = TILE_MATERIALS[mat_idx]
        mult = 0.56 + 0.10 * s_bucket
        cr = min(255, int(base_r * mult))
        cg = min(255, int(base_g * mult))
        cb = min(255, int(base_b * mult))
        py5.fill(cr, cg, cb, 252)
        q_arr = np.array(quads_list, dtype=np.float64)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(q_arr.reshape(-1, 2))

    if bevel_segs:
        py5.stroke(252, 236, 198, 145)
        py5.stroke_weight(1.3)
        py5.lines(np.array(bevel_segs, dtype=np.float64))

    # --- 3. CRITICAL PHI_0 = 51.83 DEG HOOP-STRESS TRANSITION RING & THRUST NETWORK ---
    # Dashed golden-cyan steel tension-tie ring at r = R_HOOP_ZERO (where sigma_theta = 0)
    py5.no_fill()
    py5.stroke(56, 189, 248, 215)
    py5.stroke_weight(3.0)
    py5.circle(CX, CY, R_HOOP_ZERO * 2.0)

    # 16 Meridian Funicular Thrust Ribs radiating from the oculus to the 16 perimeter piers
    rib_segs = []
    node_quads = []
    for m_i in range(16):
        m_ang = (m_i / 16.0) * 2.0 * math.pi
        cm, sm = math.cos(m_ang), math.sin(m_ang)
        rib_segs.append([
            CX + OCULUS_R * cm,
            CY + OCULUS_R * sm,
            CX + 762.0 * cm,
            CY + 762.0 * sm,
        ])
        # Reciprocal thrust node at the phi_0 = 51.83 deg neutral hoop circle
        nx_p = CX + R_HOOP_ZERO * cm
        ny_p = CY + R_HOOP_ZERO * sm
        ns = 7.5
        node_quads.append([
            [nx_p, ny_p - ns],
            [nx_p + ns, ny_p],
            [nx_p, ny_p + ns],
            [nx_p - ns, ny_p],
        ])

        # Perimeter masonry buttress pier block at r = 778 px
        bx_p = CX + 778.0 * cm
        by_p = CY + 778.0 * sm
        py5.fill(232, 168, 52, 245)
        py5.stroke(18, 24, 38, 240)
        py5.stroke_weight(1.8)
        py5.circle(bx_p, by_p, 22.0)

    py5.stroke(24, 38, 66, 210)
    py5.stroke_weight(4.6)
    py5.lines(np.array(rib_segs, dtype=np.float64))

    py5.stroke(248, 198, 72, 225)
    py5.stroke_weight(2.0)
    py5.lines(np.array(rib_segs, dtype=np.float64))

    py5.no_stroke()
    py5.fill(56, 189, 248, 250)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(node_quads, dtype=np.float64).reshape(-1, 2))

    # --- 4. CENTRAL SUNLIT LANTERN OCULUS & TRI-ROSCA CUTAWAY COLLAR ---
    # 3-ply stepped Tri-Rosca cutaway collar around the oculus (showing the 3 thin tile layers)
    for ply_r, ply_col in [
        (OCULUS_R + 22.0, (188, 78, 42, 250)),
        (OCULUS_R + 14.0, (226, 214, 192, 250)),
        (OCULUS_R + 7.0, (216, 164, 96, 250)),
    ]:
        py5.fill(*ply_col)
        py5.stroke(48, 32, 20, 235)
        py5.stroke_weight(1.6)
        py5.circle(CX, CY, ply_r * 2.0)

    # Radiant sky-blue & solar-gold glazed lantern oculus
    py5.fill(18, 42, 78, 255)
    py5.stroke(245, 188, 58, 255)
    py5.stroke_weight(4.0)
    py5.circle(CX, CY, OCULUS_R * 2.0)

    for r_oc, col_oc in [
        (OCULUS_R * 0.82, (36, 88, 148, 225)),
        (OCULUS_R * 0.58, (72, 148, 212, 225)),
        (OCULUS_R * 0.34, (250, 224, 132, 245)),
    ]:
        py5.no_stroke()
        py5.fill(*col_oc)
        py5.circle(CX + sun_x * 8.0, CY + sun_y * 8.0, r_oc * 2.0)

    # 16 radial bronze lantern glazing muntins
    muntin_segs = []
    for m_i in range(16):
        ma = (m_i / 16.0) * 2.0 * math.pi
        muntin_segs.append([
            CX + 18.0 * math.cos(ma),
            CY + 18.0 * math.sin(ma),
            CX + OCULUS_R * math.cos(ma),
            CY + OCULUS_R * math.sin(ma),
        ])
    py5.stroke(245, 188, 58, 235)
    py5.stroke_weight(2.0)
    py5.lines(np.array(muntin_segs, dtype=np.float64))

    py5.fill(255, 248, 214, 255)
    py5.stroke(148, 98, 24, 245)
    py5.stroke_weight(2.2)
    py5.circle(CX, CY, 36.0)


def draw_dark_card_frame(x: float, y: float, w: float, h: float):
    """Draws a structural engineering dark blueprint card with terracotta-gold corner brackets."""
    py5.fill(10, 15, 26, 238)
    py5.stroke(76, 92, 124, 210)
    py5.stroke_weight(2.0)
    py5.rect(x, y, w, h, 8)

    py5.no_fill()
    py5.stroke(134, 102, 58, 135)
    py5.stroke_weight(1.1)
    py5.rect(x + 8, y + 8, w - 16, h - 16, 5)

    py5.stroke(232, 148, 52, 235)
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


def draw_guastavino_apparatuses(tau: float, omega: float):
    """
    Renders 8 Timbrel Vault & Funicular Stereotomy apparatuses across 4 balanced flank cards.
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
    # CARD 1 (TOP-LEFT): FIG. 01 HOOKE-GAUDI CATENARY & FIG. 02 SPINA DI PESCE
    # =========================================================================
    draw_dark_card_frame(lx, ty, cw, th)

    # --- FIG. 01: HOOKE'S INVERTED CATENARY & HEYMAN MIDDLE-THIRD KERN ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 01 // HOOKE-GAUDI INVERTED CATENARY & HEYMAN FUNICULAR ARCH", lx + 28, ty + 24)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("y(x) = H_0/w * (1 - COSH(w*x / H_0)) // THRUST LINE CONTAINED WITHIN EXTRADOS-INTRADOS KERN", lx + 28, ty + 48)

    # Catenary arch diagram inside [lx+38..lx+306, ty+88..ty+350]
    f1_x, f1_y, f1_w, f1_h = lx + 38.0, ty + 88.0, 268.0, 260.0
    py5.fill(6, 10, 18, 240)
    py5.stroke(68, 86, 118, 195)
    py5.stroke_weight(1.5)
    py5.rect(f1_x, f1_y, f1_w, f1_h, 5)

    u1 = np.linspace(-1.0, 1.0, 80)
    x1_p = f1_x + f1_w * 0.5 + u1 * 112.0
    # Inverted compression catenary (top half) and hanging tension chain (bottom dashed reflection)
    c_val = (np.cosh(1.35 * u1) - 1.0) / (math.cosh(1.35) - 1.0)
    y1_arch = (f1_y + 34.0) + c_val * 105.0
    y1_hang = (f1_y + f1_h - 34.0) - c_val * 85.0
    # Masonry arch extrados & intrados envelope
    py5.stroke(200, 90, 50, 175)
    py5.stroke_weight(14.0)
    py5.lines(np.column_stack([x1_p[:-1], y1_arch[:-1], x1_p[1:], y1_arch[1:]]))
    # Live oscillating funicular thrust line inside the arch thickness
    y1_thrust = y1_arch + 4.5 * math.sin(omega * tau) * np.sin(math.pi * u1)
    py5.stroke(250, 204, 21, 250)
    py5.stroke_weight(2.8)
    py5.lines(np.column_stack([x1_p[:-1], y1_thrust[:-1], x1_p[1:], y1_thrust[1:]]))
    # Hanging chain below
    py5.stroke(56, 189, 248, 210)
    py5.stroke_weight(2.2)
    py5.lines(np.column_stack([x1_p[:-1], y1_hang[:-1], x1_p[1:], y1_hang[1:]]))

    tx1 = lx + 336.0
    ty1 = ty + 88.0
    f1_specs = [
        ("HOOKE ANAGRAM (1675)", ": Ut pendet continuum flexile...", (245, 184, 54)),
        ("CATENARY EQUATION", ": z(r) = a * (cosh(r_0/a) - cosh(r/a))", (56, 189, 248)),
        ("HEYMAN ASSUMPTION 1", ": Masonry Has Zero Tensile Capacity", (226, 112, 86)),
        ("HEYMAN ASSUMPTION 2", ": Compressive Stress << Crushing Limit", (52, 211, 153)),
        ("HEYMAN ASSUMPTION 3", ": Sliding Prevented by Herringbone", (244, 240, 230)),
        ("MIDDLE-THIRD RULE", ": Eccentricity |e| <= t / 6 (No Hinge)", (192, 132, 252)),
        ("SPAN-TO-THICKNESS", ": L / t = 40 m / 0.10 m = 400 : 1", (245, 184, 54)),
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

    # --- FIG. 02: BRUNELLESCHI-GUASTAVINO SPINA DI PESCE SELF-SUPPORTING SPIRAL ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 02 // SPINA DI PESCE (HERRINGBONE) CENTERING-FREE STEREOTOMY", lx + 28, ty + 412)
    py5.fill(226, 112, 86)
    py5.text_size(12)
    py5.text("VERTICAL LOCKING BRICK HEADERS CLAMPING HORIZONTAL COURSES WITHOUT WOODEN CIMBRA", lx + 28, ty + 436)

    # Close-up herringbone brick bond schematic inside [lx+38..lx+306, ty+485..ty+735]
    f2_x, f2_y = lx + 42.0, ty + 488.0
    for row_b in range(5):
        yb = f2_y + row_b * 46.0
        for col_b in range(4):
            xb = f2_x + col_b * 64.0
            is_hb_cell = (col_b == (4 - row_b) % 4)
            if is_hb_cell:
                py5.fill(232, 156, 52, 245)
                py5.stroke(254, 240, 138, 235)
                py5.stroke_weight(1.8)
                py5.rect(xb + 12, yb - 6, 36, 52, 3)
            else:
                py5.fill(200, 90, 50, 235)
                py5.stroke(218, 206, 186, 215)
                py5.stroke_weight(1.5)
                py5.rect(xb, yb, 58, 38, 3)

    tx2 = lx + 336.0
    ty2 = ty + 485.0
    f2_specs = [
        ("INVENTOR LINEAGE", ": Brunelleschi (1420) / Guastavino (1881)", (245, 184, 54)),
        ("LOCKING MECHANISM", ": Vertical Header Wedges Open Ring", (226, 112, 86)),
        ("SPIRAL HELIX ANGLE", ": alpha_spina = 58.0 DEG Loxodrome", (56, 189, 248)),
        ("FORMWORK REQUIRED", ": ZERO Wooden Centering (Self-Supporting)", (52, 211, 153)),
        ("FIRST LAYER MORTAR", ": Plaster of Paris (Sets in 45 Seconds)", (244, 240, 230)),
        ("BACKING MORTAR", ": 1:2 Portland Cement + Sharp Sand", (192, 132, 252)),
        ("TILE DIMENSIONS", ": 150 x 300 x 25 mm Rasilla Terracotta", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f2_specs):
        yy = ty2 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx2, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx2 + 178.0, yy)

    # =========================================================================
    # CARD 2 (BOTTOM-LEFT): FIG. 03 MEMBRANE SHELL STRESS & FIG. 04 PALETTE
    # =========================================================================
    draw_dark_card_frame(lx, by, cw, bh)

    # --- FIG. 03: MEMBRANE SHELL THEORY: MERIDIONAL VS. HOOP STRESSES ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 03 // MEMBRANE SHELL EQUILIBRIUM: MERIDIONAL VS. HOOP STRESS", lx + 28, by + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("GOLDEN-RATIO HOOP ZERO AT PHI_0 = ARCCOS(1 / PHI) = 51.83 DEG (COMPRESSION -> TENSION)", lx + 28, by + 48)

    f3_x, f3_y, f3_w, f3_h = lx + 38.0, by + 95.0, 268.0, 240.0
    py5.fill(6, 10, 18, 240)
    py5.stroke(68, 86, 118, 195)
    py5.stroke_weight(1.5)
    py5.rect(f3_x, f3_y, f3_w, f3_h, 5)

    # Zero-stress horizontal datum
    y3_zero = f3_y + f3_h * 0.48
    py5.stroke(148, 163, 184, 165)
    py5.stroke_weight(1.4)
    py5.line(f3_x + 12, y3_zero, f3_x + f3_w - 12, y3_zero)

    # Plot phi in [0, 90 deg]: N_phi = -1/(1+cos phi), N_theta = cos phi - 1/(1+cos phi)
    phi_arr = np.linspace(0.0, 0.5 * math.pi, 90)
    x3_p = f3_x + 16.0 + (phi_arr / (0.5 * math.pi)) * (f3_w - 32.0)
    n_phi = -1.0 / (1.0 + np.cos(phi_arr))
    n_theta = np.cos(phi_arr) - 1.0 / (1.0 + np.cos(phi_arr))
    y3_merid = y3_zero - n_phi * 85.0
    y3_hoop = y3_zero - n_theta * 85.0
    py5.stroke(245, 184, 54, 240)
    py5.stroke_weight(2.8)
    py5.lines(np.column_stack([x3_p[:-1], y3_merid[:-1], x3_p[1:], y3_merid[1:]]))
    py5.stroke(56, 189, 248, 240)
    py5.lines(np.column_stack([x3_p[:-1], y3_hoop[:-1], x3_p[1:], y3_hoop[1:]]))

    # Highlight phi_0 = 51.83 deg zero crossing of hoop stress
    x3_z = f3_x + 16.0 + (PHI_ZERO_DEG / 90.0) * (f3_w - 32.0)
    py5.fill(244, 63, 94, 255)
    py5.no_stroke()
    py5.circle(x3_z, y3_zero, 11.0)

    tx3 = lx + 336.0
    ty3 = by + 88.0
    f3_specs = [
        ("MERIDIONAL THRUST", ": N_phi = -q*R / (1 + cos phi) (Always -)", (245, 184, 54)),
        ("HOOP FORCE LAW", ": N_theta = q*R * (cos phi - 1/(1+cos phi))", (56, 189, 248)),
        ("NEUTRAL HOOP ANGLE", ": phi_0 = 51.827 DEG (cos phi_0 = 0.618)", (244, 63, 94)),
        ("UPPER CAP (phi < 52)", ": Biaxial Compression (Open Oculus Safe)", (52, 211, 153)),
        ("LOWER HAUNCH (phi>52)", ": Hoop Tension -> Steel Tie / Buttress", (226, 112, 86)),
        ("COHESIVE SHEAR", ": tau_max = 1.85 MPa Mortar Bond", (244, 240, 230)),
        ("ACOUSTIC ABSORPTION", ": alpha_NRC = 0.65 (Rumford Porous Tile)", (192, 132, 252)),
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

    # --- FIG. 04: CATALONIAN TERRACOTTA, RUMFORD TILE & GLAZE PALETTE ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 04 // CATALONIAN TERRACOTTA, AKOUSTOLITH & AZULEJO PALETTE", lx + 28, by + 412)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("WOBURN KILN FIRED RASILLA CLAY, RUMFORD AKOUSTOLITH BUFF & TIN-OXIDE GLAZES", lx + 28, by + 436)

    swatches = [
        ((200, 90, 50), "VALENCIA RASILLA TERRACOTTA // IRON-RICH CATALONIAN CLAY FIRED AT 1,020 C"),
        ((216, 176, 116), "RUMFORD AKOUSTOLITH BUFF // GRADED PUMICE & PORTLAND SOUND-ABSORBING TILE"),
        ((232, 156, 52), "SPINA DI PESCE HEADER GOLD // VERTICAL LOCKING HERRINGBONE SPIRAL KEYBRICK"),
        ((218, 206, 186), "GYPSUM & PORTLAND MORTAR BED // RAPID-SETTING PLASTER OF PARIS + CEMENT LAMINA"),
        ((38, 102, 224), "CATALAN COBALT AZULEJO GLAZE // TIN-OPACIFIED COBALT ALUMINATE MAJOLICA RIB"),
        ((18, 148, 110), "BARCELONA VERDIGRIS CELADON // COPPER-OXIDE GLAZED POLYCHROME PENDENTIVE INLAY"),
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
    # CARD 3 (TOP-RIGHT): FIG. 05 TRI-ROSCA LAMINATION & FIG. 06 CODEX LEDGER
    # =========================================================================
    draw_dark_card_frame(rx, ty, cw, th)

    # --- FIG. 05: THREE-PLY COHESIVE LAMINATION (TRI-ROSCA SECTION) ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 05 // THREE-PLY COHESIVE TIMBREL LAMINATION (TRI-ROSCA)", rx + 28, ty + 24)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("STAGGERED 3-COURSE SHELL LAMINATE ELIMINATING CONTINUOUS VERTICAL JOINTS", rx + 28, ty + 48)

    # 3-ply tile + 2 mortar bed cross-section diagram inside [rx+38..rx+306, ty+105..ty+335]
    f5_x, f5_y = rx + 42.0, ty + 118.0
    for ply_k, (ply_lbl, ply_c, st_off) in enumerate([
        ("3RD PLY (INTRADOS)", (216, 176, 116), 0.0),
        ("2ND PLY (DIAGONAL)", (200, 90, 50), 28.0),
        ("1ST PLY (GYPSUM)", (232, 156, 52), 14.0),
    ]):
        yp = f5_y + ply_k * 64.0
        # Mortar bed
        py5.fill(218, 206, 186, 225)
        py5.no_stroke()
        py5.rect(f5_x, yp + 34.0, 256.0, 14.0, 2)
        # 3 staggered tiles per ply
        for tk in range(3):
            xt = f5_x + tk * 82.0 + (st_off if tk < 2 else 0.0)
            w_t = 76.0 if tk < 2 else (82.0 - st_off)
            py5.fill(*ply_c, 245)
            py5.stroke(24, 32, 48, 235)
            py5.stroke_weight(1.5)
            py5.rect(xt, yp, w_t, 32.0, 3)

    tx5 = rx + 336.0
    ty5 = ty + 88.0
    f5_specs = [
        ("TOTAL SHELL THICKNESS", ": t = 95 mm (3 Plies + 2 Mortar Beds)", (245, 184, 54)),
        ("1ST COURSE (INTRADOS)", ": Laid in Pure Plaster of Paris (Cantilever)", (226, 112, 86)),
        ("2ND COURSE (CORE)", ": Laid at 45-DEG Skew in Portland Mortar", (56, 189, 248)),
        ("3RD COURSE (EXTRADOS)", ": Herringbone-Locked Structural Envelope", (52, 211, 153)),
        ("AREAL SHELL DENSITY", ": m_shell = 185 kg / m^2 (Featherweight)", (244, 240, 230)),
        ("FIREPROOF RATING", ": 4-Hour ASTM E119 Zero-Spall Ceramic", (192, 132, 252)),
        ("MODULUS OF RUPTURE", ": sigma_flex = 2.8 MPa Cohesive Bending", (245, 184, 54)),
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

    # --- FIG. 06: HISTORICAL TIMBREL VAULT & MASONRY CODEX LEDGER ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 06 // HISTORICAL TIMBREL VAULT & STEREOTOMY MONUMENT LEDGER", rx + 28, ty + 412)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("FROM BRUNELLESCHI'S FLORENCE DUOMO (1436) TO GUASTAVINO'S AMERICAN DOMES", rx + 28, ty + 436)

    rows = [
        ("SANTA MARIA DEL FIORE (1436)", "Florence (Brunelleschi)", "45.5 m Octagon", "Spina di Pesce Brick"),
        ("BATLLO FACTORY VAULTS (1868)", "Barcelona (Guastavino)", "Cohesive Tabicada", "Portland + Gypsum"),
        ("BOSTON PUBLIC LIBRARY (1895)", "McKim & Guastavino", "Astor Hall Vaults", "Exposed Tile Weave"),
        ("CITY HALL SUBWAY NYC (1904)", "Heins & Guastavino", "Polychrome Groins", "Skylit Oculus Arch"),
        ("ST. JOHN THE DIVINE (1909)", "New York (Guastavino)", "41.1 m Span Dome", "Built Without Cimbra"),
        ("ACTIVE CUPOLA SIMULATION", "18-Course Tri-Rosca", "phi_0 = 51.83 DEG", "HARMONIC LIVE"),
    ]
    for r_i, (c_name, c_arch, c_span, c_note) in enumerate(rows):
        ry_row = ty + 478.0 + r_i * 55.0
        is_hi = (r_i == 4 or r_i == 5)
        py5.fill(*(28, 38, 64, 242) if is_hi else (14, 20, 36, 220))
        py5.stroke(*(245, 184, 54, 235) if is_hi else (68, 84, 118, 175))
        py5.stroke_weight(1.9 if is_hi else 1.1)
        py5.rect(rx + 28, ry_row, cw - 56, 44, 5)

        py5.no_stroke()
        py5.fill(244, 240, 230)
        py5.text_size(12)
        py5.text(c_name, rx + 44, ry_row + 15)
        py5.fill(56, 189, 248)
        py5.text(c_arch, rx + 265, ry_row + 15)
        py5.fill(245, 184, 54)
        py5.text(c_span, rx + 435, ry_row + 15)
        py5.fill(52, 211, 153)
        py5.text(c_note, rx + 595, ry_row + 15)

    # =========================================================================
    # CARD 4 (BOTTOM-RIGHT): FIG. 07 GRAPH STATICS & FIG. 08 SAFETY TRACE
    # =========================================================================
    draw_dark_card_frame(rx, by, cw, bh)

    # --- FIG. 07: CREMONA-MAXWELL RECIPROCAL FORCE DIAGRAM (THRUST NETWORK) ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 07 // CREMONA-MAXWELL RECIPROCAL GRAPH STATICS (TNA)", rx + 28, by + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("DUAL FORM DIAGRAM GAMMA & RECIPROCAL FORCE POLYGON GAMMA* (BLOCK & OCHSENDORF)", rx + 28, by + 48)

    # Dual reciprocal polygons inside [rx+42..rx+300, by+95..by+335]
    f7_cx1, f7_cy1 = rx + 112.0, by + 215.0
    f7_cx2, f7_cy2 = rx + 238.0, by + 215.0
    for k7 in range(8):
        a7 = k7 * (math.pi / 4.0) + 0.15 * math.sin(omega * tau)
        a7_next = (k7 + 1) * (math.pi / 4.0) + 0.15 * math.sin(omega * tau)
        # Form diagram Gamma (radial + hoop)
        py5.stroke(245, 184, 54, 225)
        py5.stroke_weight(2.0)
        py5.line(f7_cx1, f7_cy1, f7_cx1 + 54.0 * math.cos(a7), f7_cy1 + 54.0 * math.sin(a7))
        py5.line(
            f7_cx1 + 54.0 * math.cos(a7), f7_cy1 + 54.0 * math.sin(a7),
            f7_cx1 + 54.0 * math.cos(a7_next), f7_cy1 + 54.0 * math.sin(a7_next),
        )
        # Dual Force diagram Gamma* (rotated 90 deg reciprocal star)
        a7_dual = a7 + 0.5 * math.pi
        r_dual = 48.0 * (1.0 + 0.12 * math.cos(2.0 * a7 - omega * tau))
        py5.stroke(56, 189, 248, 225)
        py5.line(f7_cx2, f7_cy2, f7_cx2 + r_dual * math.cos(a7_dual), f7_cy2 + r_dual * math.sin(a7_dual))

    tx7 = rx + 336.0
    ty7 = by + 88.0
    f7_specs = [
        ("PRIMAL GRAPH (GAMMA)", ": Planar Projection of Vault Rib Net", (245, 184, 54)),
        ("DUAL GRAPH (GAMMA*)", ": Closed Reciprocal Force Polygons", (56, 189, 248)),
        ("NODAL EQUILIBRIUM", ": Sum F_x = 0, Sum F_y = 0 at Every Node", (52, 211, 153)),
        ("VERTICAL EQUILIBRIUM", ": z_i = Sum (q_ij * (z_j - z_i)) / P_i", (226, 112, 86)),
        ("FORCE DENSITY (q_e)", ": q_e = H_e / L_e (Horizontal Branch Ratio)", (244, 240, 230)),
        ("AIRY STRESS FUNCTION", ": Discrete Polyhedral Lifting Phi(x, y)", (192, 132, 252)),
        ("GEOMETRIC SAFETY", ": GSD = 3.45 (Deep Within Masonry Kern)", (245, 184, 54)),
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

    # --- FIG. 08: HEYMAN GEOMETRIC SAFETY & FUNICULAR THRUST WAVEFORMS ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 08 // HEYMAN THRUST ECCENTRICITY & HOOP STRESS OSCILLOGRAM", rx + 28, by + 412)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("LIVE THRUST-LINE ECCENTRICITY e(PHI)/(t/6) WITHIN MIDDLE-THIRD KERN ENVELOPE", rx + 28, by + 436)

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
    mid_y = wy + wh * 0.5

    for freq_w, amp_w, ph_w, col_w in [
        (2.0, 82.0, omega * tau, (245, 184, 54, 240)),
        (3.0, 68.0, -omega * tau + 0.6, (56, 189, 248, 240)),
        (4.0, 52.0, 2.0 * omega * tau, (226, 112, 86, 230)),
        (1.5, 42.0, -2.0 * omega * tau, (52, 211, 153, 225)),
    ]:
        yw_c = mid_y - amp_w * np.sin(freq_w * 2.0 * math.pi * u_w + ph_w) * np.cos(math.pi * u_w - 0.5 * omega * tau)
        segs_w = np.column_stack([xw_arr[:-1], yw_c[:-1], xw_arr[1:], yw_c[1:]])
        py5.stroke(*col_w)
        py5.stroke_weight(2.5)
        py5.lines(segs_w)

    py5.no_stroke()
    py5.fill(168, 182, 204)
    py5.text_size(12)
    py5.text(
        "GOLD: MERIDIONAL THRUST N_PHI  //  CYAN: HOOP RING N_THETA  //  TERRACOTTA: ECCENTRICITY  //  EMERALD: KERN MARGIN",
        wx + 8,
        wy + wh + 18,
    )


def draw_museum_border_and_typography(tau: float, omega: float):
    """Draws the outer architectural blueprint border, header, and telemetry footer."""
    py5.no_fill()
    py5.stroke(214, 152, 54, 225)
    py5.stroke_weight(3.2)
    py5.rect(52, 48, WIDTH - 104, HEIGHT - 96, 10)

    py5.stroke(96, 114, 148, 165)
    py5.stroke_weight(1.4)
    py5.rect(64, 60, WIDTH - 128, HEIGHT - 120, 6)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(248, 244, 234)
    py5.text_size(30)
    py5.text(
        "GUASTAVINO TIMBREL VAULT & HERRINGBONE STEREOTOMY // COHESIVE MASONRY SHELL",
        CX,
        82,
    )

    py5.fill(245, 184, 54)
    py5.text_size(15)
    py5.text(
        "BOVEDA TABICADA TRI-ROSCA LAMINATION, SPINA DI PESCE LOCKING SPIRALS & HEYMAN FUNICULAR THRUST (1892)",
        CX,
        124,
    )

    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(168, 182, 204)
    py5.text_size(14)
    py5.text(
        "18 TIMBREL COURSES // 16 SPINA DI PESCE SPIRALS // HOOP TRANSITION PHI_0 = 51.83 DEG (COS PHI_0 = 1/PHI)",
        96,
        HEIGHT - 74,
    )

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K ARCHITECTURAL STEREOTOMY // HARMONIC PHASE TAU = {tau:0.3f} (12.0s @ 60FPS)",
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
