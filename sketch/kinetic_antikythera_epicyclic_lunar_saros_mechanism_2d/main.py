"""
Kinetic Antikythera Epicyclic Lunar & Saros Mechanism 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Physical / Micro-Kinetic genre,
simulating the Antikythera Mechanism (c. 150-100 BCE) — the Hellenistic geared
astronomical analog computer and epicyclic planetarium reconstructed via micro-focus
X-ray computed tomography (Price 1974; Wright 2005; Freeth et al., Nature 2006 &
Scientific Reports 2021), executed on warm Aegean papyrus and Pentelic marble
drafting vellum (#f6f1e6).

This 4K 60fps simulation visualizes:
1. The multi-layered coaxial and epicyclic Corinthian bronze gear train with authentic
   Hellenistic 60-degree equilateral triangular gear teeth: the 224-tooth Main Solar
   Drive Wheel (b1), the 254:19 Sidereal-Tropical Metonic Gear Train (b2, c1, c2, d1,
   d2, e2), the 223-month Saros Eclipse Train (e5, f1, g1), the Exeligmos Triple-Saros
   Train (h1, i1), and Hipparchus's eccentric Pin-and-Slot Epicyclic Lunar Anomaly
   Gears (k1, k2, 50 teeth each) mounted on the rotating epicyclic carrier.
2. Concentric graduated Hellenistic 360-degree Zodiac Ring (12 classical Greek constellations)
   and 365-day Egyptian Sothic Calendar Ring framing five deferent-plus-epicycle planetary
   pointers tracing live retrograde station loops, the Golden Helios Solar Ray Pointer,
   and the revolving 3D half-silvered / half-obsidian Lunar Phase Sphere (b0).
3. Eight Hellenistic archaeometric, horological, and astronomical apparatuses across four
   balanced flank cards.
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
WORK_NAME = "kinetic_antikythera_epicyclic_lunar_saros_mechanism_2d"
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

# Non-fixed runtime phase variations (adhering to no-fixed-seed rule)
np.random.seed(int(time.time() * 1000) % 100000)
RND_SOLAR_EPOCH = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_APSIDAL_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 22.0
DIAL_R = 805.0

# Classical Hellenistic Zodiac Names (Romanized Greek inscriptions on the Front Dial)
ZODIAC_NAMES = [
    "KRIOS (ARIES)",
    "TAUROS (TAURUS)",
    "DIDYMOI (GEMINI)",
    "KARKINOS (CANCER)",
    "LEON (LEO)",
    "PARTHENOS (VIRGO)",
    "CHELAI (LIBRA)",
    "SKORPIOS (SCORPIO)",
    "TOXOTES (SAGITTARIUS)",
    "AIGOKEROS (CAPRICORN)",
    "HYDROCHOOS (AQUARIUS)",
    "ICHTHYES (PISCES)",
]

EGYPTIAN_MONTHS = [
    "THOTH", "PHAOPHI", "ATHYR", "CHOIAK",
    "TYBI", "MECHIR", "PHAMENOTH", "PHARMOUTHI",
    "PACHON", "PAYNI", "EPIPHI", "MESORE",
]

# Precomputed Gear Train Specification:
# (id_label, rel_x, rel_y, pitch_radius, teeth_count, speed_mult, phase_off, material_tier, spoke_count)
# material_tier:
#   0 = Deep Verdigris Lower Plate Bronze (#1e5c54)
#   1 = Aged Aegean Patina Bronze (#2b7268)
#   2 = Warm Corinthian Phosphor-Bronze (#b87d3b)
#   3 = Burnished Syracuse Brass-Gold (#d89620)
#   4 = High-Tin Specular Bronze (#8c6232)
FIXED_GEARS = [
    # Main drive & lower Saros / Metonic carrier bed
    ("b1 (224T SOLAR DRIVE)", 0.0, 0.0, 495.0, 112, 1.0, 0.0, 2, 4),
    ("e3 (223T SAROS BED)", 0.0, 0.0, 415.0, 96, -1.0, 0.25, 0, 6),
    # Upper-left Metonic 19-Year & Callippic Gear Train
    ("l1 (38T METONIC)", -285.0, -245.0, 118.0, 38, -2.0, 0.1, 1, 5),
    ("l2 (53T METONIC)", -285.0, -245.0, 74.0, 28, -2.0, 0.4, 3, 4),
    ("m1 (96T CALLIPPIC)", -425.0, -110.0, 128.0, 44, 1.0, 0.2, 2, 6),
    ("n1 (53T OLYMPIAD)", -445.0, -310.0, 88.0, 32, 3.0, 0.5, 0, 4),
    # Upper-right Sidereal Lunar Ratio Train (254 : 19)
    ("c1 (38T LUNAR)", 255.0, -255.0, 115.0, 38, -3.0, 0.0, 2, 5),
    ("c2 (48T LUNAR)", 255.0, -255.0, 78.0, 28, -3.0, 0.3, 3, 4),
    ("d1 (24T LUNAR)", 395.0, -145.0, 92.0, 30, 4.0, 0.2, 1, 4),
    ("d2 (127T HIPPARCHUS)", 395.0, -145.0, 156.0, 56, 2.0, 0.6, 4, 6),
    # Lower-left Saros Eclipse Train (223 Synodic Months)
    ("f1 (54T SAROS)", -265.0, 265.0, 132.0, 44, 2.0, 0.15, 1, 5),
    ("g1 (60T SAROS)", -415.0, 155.0, 118.0, 40, -2.0, 0.35, 2, 5),
    ("h1 (60T EXELIGMOS)", -385.0, 345.0, 86.0, 30, 3.0, 0.0, 3, 4),
    # Lower-right Planetary & Crown Differential Train
    ("e5 (50T ANOMALY)", 265.0, 255.0, 128.0, 42, -2.0, 0.2, 0, 5),
    ("q1 (36T CORONET)", 410.0, 165.0, 102.0, 34, 3.0, 0.4, 2, 4),
    ("r1 (48T SATURN)", 355.0, 355.0, 94.0, 32, -3.0, 0.1, 3, 4),
    # Coaxial central b2 (64T)
    ("b2 (64T COAXIAL)", 0.0, 0.0, 168.0, 48, 2.0, 0.0, 3, 4),
]

# Material palette: (fill_rgb, rim_rgb, tooth_rgb, hub_rgb, stroke_rgb)
MAT_PALETTE = {
    0: ((28, 84, 76), (38, 108, 98), (46, 126, 114), (20, 62, 56), (14, 44, 40)),
    1: ((44, 114, 104), (58, 138, 126), (72, 158, 144), (32, 86, 78), (18, 54, 48)),
    2: ((178, 120, 56), (202, 142, 72), (222, 164, 92), (142, 92, 38), (82, 50, 18)),
    3: ((214, 152, 36), (234, 176, 58), (248, 198, 86), (172, 118, 24), (96, 62, 12)),
    4: ((146, 104, 62), (172, 126, 78), (194, 148, 98), (114, 78, 44), (68, 44, 22)),
}


def build_triangular_gear_ring_verts(cx: float, cy: float, r_pitch: float, n_teeth: int, rot: float):
    """
    Generates vectorized QUADS for an authentic Hellenistic 60-degree equilateral
    triangular-tooth bronze gear rim plus inner annular rim band.
    Returns (tooth_tris_as_degenerate_quads, rim_quads).
    """
    tooth_h = min(18.0, max(7.5, (2.0 * math.pi * r_pitch / n_teeth) * 0.48))
    r_root = r_pitch - 0.45 * tooth_h
    r_tip = r_pitch + 0.55 * tooth_h
    r_inner = max(16.0, r_root - max(12.0, r_pitch * 0.14))

    idx = np.arange(n_teeth, dtype=np.float64)
    dtheta = 2.0 * math.pi / n_teeth
    a0 = rot + idx * dtheta
    a_mid = a0 + 0.5 * dtheta
    a1 = a0 + dtheta

    x_r0 = cx + r_root * np.cos(a0)
    y_r0 = cy + r_root * np.sin(a0)
    x_tip = cx + r_tip * np.cos(a_mid)
    y_tip = cy + r_tip * np.sin(a_mid)
    x_r1 = cx + r_root * np.cos(a1)
    y_r1 = cy + r_root * np.sin(a1)

    x_i0 = cx + r_inner * np.cos(a0)
    y_i0 = cy + r_inner * np.sin(a0)
    x_i1 = cx + r_inner * np.cos(a1)
    y_i1 = cy + r_inner * np.sin(a1)

    # Teeth as QUADS (repeating tip vertex so we can batch with py5.QUADS)
    tooth_quads = np.empty((n_teeth, 4, 2), dtype=np.float64)
    tooth_quads[:, 0, 0] = x_r0
    tooth_quads[:, 0, 1] = y_r0
    tooth_quads[:, 1, 0] = x_tip
    tooth_quads[:, 1, 1] = y_tip
    tooth_quads[:, 2, 0] = x_r1
    tooth_quads[:, 2, 1] = y_r1
    tooth_quads[:, 3, 0] = x_r0
    tooth_quads[:, 3, 1] = y_r0

    # Annular rim quads between r_inner and r_root
    rim_quads = np.empty((n_teeth, 4, 2), dtype=np.float64)
    rim_quads[:, 0, 0] = x_i0
    rim_quads[:, 0, 1] = y_i0
    rim_quads[:, 1, 0] = x_r0
    rim_quads[:, 1, 1] = y_r0
    rim_quads[:, 2, 0] = x_r1
    rim_quads[:, 2, 1] = y_r1
    rim_quads[:, 3, 0] = x_i1
    rim_quads[:, 3, 1] = y_i1

    return tooth_quads, rim_quads, r_inner, r_root


def draw_hellenistic_gear(
    cx: float,
    cy: float,
    r_pitch: float,
    n_teeth: int,
    rot: float,
    mat_id: int,
    n_spokes: int = 4,
    alpha: int = 242,
    draw_arbor: bool = True,
):
    """Renders a bronze Hellenistic gear with triangular teeth, spokes, and square arbor."""
    fill_c, rim_c, tooth_c, hub_c, stroke_c = MAT_PALETTE[mat_id]
    tooth_quads, rim_quads, r_inner, r_root = build_triangular_gear_ring_verts(
        cx, cy, r_pitch, n_teeth, rot
    )

    # Soft cast shadow onto lower plate
    py5.no_stroke()
    py5.fill(42, 34, 24, 38)
    py5.circle(cx + 6.0, cy + 7.5, (r_pitch + 8.0) * 2.0)

    # Spokes connecting hub to inner rim
    r_hub = max(14.0, r_pitch * 0.20)
    spoke_half_w = max(4.5, r_pitch * 0.048)
    spoke_quads = np.empty((n_spokes, 4, 2), dtype=np.float64)
    for s in range(n_spokes):
        ang = rot + s * (2.0 * math.pi / n_spokes)
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa * spoke_half_w, ca * spoke_half_w
        x0, y0 = cx + (r_hub * 0.65) * ca, cy + (r_hub * 0.65) * sa
        x1, y1 = cx + (r_inner + 4.0) * ca, cy + (r_inner + 4.0) * sa
        spoke_quads[s, 0] = (x0 - nx, y0 - ny)
        spoke_quads[s, 1] = (x1 - nx, y1 - ny)
        spoke_quads[s, 2] = (x1 + nx, y1 + ny)
        spoke_quads[s, 3] = (x0 + nx, y0 + ny)

    py5.stroke(stroke_c[0], stroke_c[1], stroke_c[2], 210)
    py5.stroke_weight(1.4)
    py5.fill(fill_c[0], fill_c[1], fill_c[2], alpha)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(spoke_quads.reshape(-1, 2))

    # Teeth and outer rim
    py5.fill(tooth_c[0], tooth_c[1], tooth_c[2], alpha)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(tooth_quads.reshape(-1, 2))

    py5.fill(rim_c[0], rim_c[1], rim_c[2], alpha)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(rim_quads.reshape(-1, 2))

    # Concentric turned bronze engraving rings on rim
    py5.no_fill()
    py5.stroke(252, 232, 186, 130)
    py5.stroke_weight(1.3)
    py5.circle(cx, cy, (r_inner + 0.55 * (r_root - r_inner)) * 2.0)

    # Central stepped bronze hub & square iron arbor with cotter pin
    if draw_arbor:
        py5.fill(hub_c[0], hub_c[1], hub_c[2], 250)
        py5.stroke(stroke_c[0], stroke_c[1], stroke_c[2], 235)
        py5.stroke_weight(1.6)
        py5.circle(cx, cy, r_hub * 2.0)

        sq_r = max(6.5, r_hub * 0.46)
        sq_pts = np.empty((4, 2), dtype=np.float64)
        for k in range(4):
            ak = rot + k * (0.5 * math.pi) + 0.25 * math.pi
            sq_pts[k] = (cx + sq_r * math.cos(ak), cy + sq_r * math.sin(ak))
        py5.fill(48, 56, 66, 250)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(sq_pts)

        # Tiny golden rivet / axle pin
        py5.fill(238, 192, 88, 255)
        py5.circle(cx, cy, max(5.0, sq_r * 0.55))


def compute_pin_and_slot_lunar_kinematics(phi_in: float, apsidal_ang: float):
    """
    Computes Hipparchus's eccentric Pin-and-Slot Lunar Anomaly mechanism (gears k1 & k2).
    Gear k1 rotates at angle phi_in around axis O1; its engaging pin at radius r_pin
    drives the radial slot of gear k2 centered at O2 (offset by eccentricity e_off
    along apsidal_ang), producing the true anomalistic lunar longitude phi_out and
    instantaneous angular velocity ratio d(phi_out)/d(phi_in).
    """
    r_pin = 1.0
    e_off = 0.21  # normalized eccentricity producing +/- 21% lunar velocity anomaly
    px = r_pin * math.cos(phi_in)
    py = r_pin * math.sin(phi_in)
    o2x = e_off * math.cos(apsidal_ang)
    o2y = e_off * math.sin(apsidal_ang)
    dx = px - o2x
    dy = py - o2y
    phi_out = math.atan2(dy, dx)
    dist = math.hypot(dx, dy)
    # Instantaneous angular velocity modulation d(phi_out)/d(phi_in)
    omega_ratio = (r_pin * (r_pin - e_off * math.cos(phi_in - apsidal_ang))) / max(0.2, dist * dist)
    return phi_out, omega_ratio


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

    # 1. Warm Aegean Papyrus & Pentelic Marble Drafting Vellum (#f6f1e6)
    py5.background(246, 241, 230)

    # 2. Subtle Papyrus Fiber Grain & Hellenistic Stereographic Drafting Grid
    draw_vellum_substrate_and_grid(tau)

    # 3. Central Antikythera Mechanism Planisphere, Bronze Gear Train & Pin-and-Slot Carrier
    draw_central_antikythera_planisphere(tau, omega)

    # 4. Eight Archaeometric & Hellenistic Astronomical Apparatuses Across Four Flank Cards
    draw_archaeometric_apparatuses(tau, omega)

    # 5. Archival Museum Border & Scholarly Typography (Zero Personal Signatures/Seals)
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
        print(
            f"[{WORK_NAME}] Frame {frame+1:03d}/{TOTAL_FRAMES} ({(frame+1)/TOTAL_FRAMES*100:.1f}%) | "
            f"Speed: {fps_calc:.2f} fps | ETA: {eta:.1f}s"
        )


def draw_vellum_substrate_and_grid(tau: float):
    """Draws warm papyrus vellum washes, subtle coordinate grid, and meridian ticks."""
    py5.no_stroke()
    for r_g, col_g in [
        (1180, (236, 228, 212, 85)),
        (920, (228, 218, 198, 75)),
        (825, (214, 202, 178, 90)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    # Architectural drafting grid
    py5.stroke(214, 204, 186, 135)
    py5.stroke_weight(1.2)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)

    #Cardinal celestial axis hairlines
    py5.stroke(168, 148, 118, 130)
    py5.stroke_weight(1.6)
    py5.line(CX - 915, CY, CX + 915, CY)
    py5.line(CX, CY - 895, CX, CY + 895)


def draw_central_antikythera_planisphere(tau: float, omega: float):
    """
    Renders the central Antikythera Mechanism:
    - Recessed bronze & marine verdigris instrument bedplate
    - 15 meshing 60-degree triangular-tooth bronze gears
    - Rotating Epicyclic Carrier with eccentric Pin-and-Slot Lunar Anomaly gears k1 & k2
    - Five Planetary Deferent+Epicycle Pointers tracing live retrograde station loops
    - Outer Concentric 365-Day Egyptian Calendar Ring & 360-Degree Hellenistic Zodiac Ring
    - Golden Helios Solar Pointer & 3D Half-Silvered Revolving Lunar Phase Sphere
    """
    # Outer recessed bronze instrument casing bezel
    py5.no_stroke()
    py5.fill(46, 36, 26, 48)
    py5.circle(CX + 8.0, CY + 10.0, (DIAL_R + 30.0) * 2.0)

    # Deep Aegean bronze & verdigris recessed cavity inside the Zodiac dial
    py5.fill(26, 46, 44, 252)
    py5.stroke(96, 66, 32, 245)
    py5.stroke_weight(4.0)
    py5.circle(CX, CY, (DIAL_R + 22.0) * 2.0)

    # Inner stepped verdigris patina well
    py5.no_stroke()
    for r_w, c_w in [
        (685.0, (20, 38, 36, 255)),
        (595.0, (16, 32, 31, 255)),
        (495.0, (24, 44, 42, 255)),
    ]:
        py5.fill(*c_w)
        py5.circle(CX, CY, r_w * 2.0)

    # Internal bronze structural mounting bridges (Fragment A cross-bridges)
    py5.stroke(68, 46, 24, 220)
    py5.stroke_weight(2.2)
    py5.fill(118, 82, 42, 195)
    with py5.begin_shape(py5.QUADS):
        # Diagonal structural bridges holding the Metonic, Saros, and Lunar arbors
        bridges = np.array([
            [CX - 480, CY - 340, CX - 445, CY - 375, CX + 445, CY + 375, CX + 480, CY + 340],
            [CX - 480, CY + 340, CX - 445, CY + 375, CX + 445, CY - 375, CX + 480, CY - 340],
            [CX - 32, CY - 640, CX + 32, CY - 640, CX + 32, CY + 640, CX - 32, CY + 640],
            [CX - 640, CY - 32, CX - 640, CY + 32, CX + 640, CY + 32, CX + 640, CY - 32],
        ], dtype=np.float64).reshape(-1, 2)
        py5.vertices(bridges)

    # Render the 15 fixed-axis bronze gears in back-to-front order
    for label, gx, gy, r_p, n_t, spd, ph_off, mat_id, n_sp in FIXED_GEARS:
        rot_g = spd * omega * tau + ph_off + RND_SOLAR_EPOCH * (1.0 if spd > 0 else -1.0)
        draw_hellenistic_gear(
            CX + gx,
            CY + gy,
            r_p,
            n_t,
            rot_g,
            mat_id,
            n_spokes=n_sp,
            alpha=238,
            draw_arbor=True,
        )

    # Engraved technical callout tags on main gears
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text_size(11)
    for label, gx, gy, r_p, n_t, spd, ph_off, mat_id, n_sp in FIXED_GEARS:
        if r_p >= 115.0 and (abs(gx) + abs(gy) > 50.0):
            py5.fill(246, 238, 218, 215)
            py5.text(label.split(" ")[0], CX + gx, CY + gy - r_p * 0.52)

    # --- Hipparchus Epicyclic Pin-and-Slot Lunar Anomaly Assembly (k1 / k2 on b1/e3 carrier) ---
    carrier_ang = omega * tau + RND_APSIDAL_PHASE
    carrier_r = 250.0
    k1_cx = CX + carrier_r * math.cos(carrier_ang)
    k1_cy = CY + carrier_r * math.sin(carrier_ang)

    # Eccentric offset axis of k2 relative to k1 (representing the ~1.1mm historical offset amplified)
    ecc_px = 26.0
    k2_cx = k1_cx + ecc_px * math.cos(carrier_ang + 0.5 * math.pi)
    k2_cy = k1_cy + ecc_px * math.sin(carrier_ang + 0.5 * math.pi)

    phi_k1 = -3.0 * omega * tau + RND_SOLAR_EPOCH
    phi_k2, lunar_vel_ratio = compute_pin_and_slot_lunar_kinematics(
        phi_k1, carrier_ang + 0.5 * math.pi
    )

    # Draw lower slotted gear k2 (50T) and upper pin gear k1 (50T)
    draw_hellenistic_gear(k2_cx, k2_cy, 112.0, 50, phi_k2, 1, n_spokes=5, alpha=235)
    draw_hellenistic_gear(k1_cx, k1_cy, 106.0, 50, phi_k1, 3, n_spokes=5, alpha=235)

    # Draw the radial slot on k2 and the engaging golden pin on k1
    slot_r_in = 42.0
    slot_r_out = 94.0
    s_x0 = k2_cx + slot_r_in * math.cos(phi_k2)
    s_y0 = k2_cy + slot_r_in * math.sin(phi_k2)
    s_x1 = k2_cx + slot_r_out * math.cos(phi_k2)
    s_y1 = k2_cy + slot_r_out * math.sin(phi_k2)
    py5.stroke(24, 18, 12, 245)
    py5.stroke_weight(14.0)
    py5.line(s_x0, s_y0, s_x1, s_y1)
    py5.stroke(248, 212, 112, 245)
    py5.stroke_weight(7.5)
    py5.line(s_x0, s_y0, s_x1, s_y1)

    pin_r = 68.0
    pin_x = k1_cx + pin_r * math.cos(phi_k1)
    pin_y = k1_cy + pin_r * math.sin(phi_k1)
    py5.fill(184, 52, 42, 255)
    py5.stroke(254, 242, 198, 255)
    py5.stroke_weight(2.5)
    py5.circle(pin_x, pin_y, 17.0)

    # --- Five Classical Planetary Epicycle Loops & Pointers (Mercury, Venus, Mars, Jupiter, Saturn) ---
    draw_planetary_epicycle_loops(tau, omega)

    # --- Outer Concentric Egyptian 365-Day Calendar Ring & 360-Degree Zodiac Dial ---
    draw_zodiac_and_egyptian_rings(tau)

    # --- Central Celestial Pointers: Golden Helios Sun Pointer & 3D Half-Silvered Lunar Sphere ---
    draw_solar_and_lunar_pointers(tau, omega, phi_k2, lunar_vel_ratio)


def draw_planetary_epicycle_loops(tau: float, omega: float):
    """
    Draws the geocentric deferent + epicycle retrograde station loops and live
    epicyclic wheels for the 5 classical planets known to Hellenistic astronomy:
    Hermes (Mercury), Phosphoros (Venus), Pyroeis (Mars), Phaethon (Jupiter), Phainon (Saturn).
    """
    planets = [
        # (name, r_deferent, r_epicycle, n_def, n_epi, color_rgb, phase0)
        ("PHAINON (SATURN)", 558.0, 34.0, 1, -6, (216, 176, 88), 0.4),
        ("PHAETHON (JUPITER)", 498.0, 44.0, 1, -5, (72, 186, 168), 1.6),
        ("PYROEIS (MARS)", 428.0, 62.0, 2, -5, (218, 76, 62), 2.8),
        ("PHOSPHOROS (VENUS)", 348.0, 52.0, 2, 5, (244, 198, 92), 4.1),
        ("HERMES (MERCURY)", 272.0, 38.0, 3, -8, (112, 194, 242), 5.3),
    ]

    t_curve = np.linspace(0.0, 2.0 * math.pi, 240, endpoint=True)
    for p_name, r_def, r_epi, n_def, n_epi, col_rgb, ph0 in planets:
        # Deferent guide circle
        py5.no_fill()
        py5.stroke(col_rgb[0], col_rgb[1], col_rgb[2], 68)
        py5.stroke_weight(1.2)
        py5.circle(CX, CY, r_def * 2.0)

        # Full closed retrograde epicycloid / deferent-epicycle trajectory
        a_def_arr = n_def * t_curve + ph0 + RND_SOLAR_EPOCH * 0.4
        a_epi_arr = n_epi * t_curve - ph0
        px_arr = CX + r_def * np.cos(a_def_arr) + r_epi * np.cos(a_epi_arr)
        py_arr = CY + r_def * np.sin(a_def_arr) + r_epi * np.sin(a_epi_arr)
        segs = np.column_stack([px_arr[:-1], py_arr[:-1], px_arr[1:], py_arr[1:]])

        py5.stroke(col_rgb[0], col_rgb[1], col_rgb[2], 145)
        py5.stroke_weight(2.1)
        py5.lines(segs)

        # Instantaneous deferent center & epicycle wheel at current tau
        cur_def = n_def * omega * tau + ph0 + RND_SOLAR_EPOCH * 0.4
        cur_epi = n_epi * omega * tau - ph0
        dc_x = CX + r_def * np.cos(cur_def)
        dc_y = CY + r_def * np.sin(cur_def)
        pl_x = dc_x + r_epi * np.cos(cur_epi)
        pl_y = dc_y + r_epi * np.sin(cur_epi)

        py5.no_fill()
        py5.stroke(col_rgb[0], col_rgb[1], col_rgb[2], 195)
        py5.stroke_weight(1.8)
        py5.circle(dc_x, dc_y, r_epi * 2.0)
        py5.line(dc_x, dc_y, pl_x, pl_y)

        py5.fill(col_rgb[0], col_rgb[1], col_rgb[2], 255)
        py5.stroke(252, 246, 232, 240)
        py5.stroke_weight(1.8)
        py5.circle(pl_x, pl_y, 13.0)


def draw_zodiac_and_egyptian_rings(tau: float):
    """
    Renders the outer concentric 365-Day Egyptian Calendar Ring (R = 740..805)
    and the 360-Degree Hellenistic Zodiac Ring (R = 665..740) with Parapegma fiducial
    fiducial index holes and classical Greek constellation inscriptions.
    """
    r_z_in = 662.0
    r_z_out = 736.0
    r_e_out = 805.0

    # Annular ring backgrounds (vectorized 120-segment bands)
    n_seg = 120
    ang = np.linspace(0.0, 2.0 * math.pi, n_seg + 1)
    ca, sa = np.cos(ang), np.sin(ang)

    def draw_annulus(r0: float, r1: float, fill_rgba, stroke_rgba):
        quads = np.empty((n_seg, 4, 2), dtype=np.float64)
        quads[:, 0, 0] = CX + r0 * ca[:-1]
        quads[:, 0, 1] = CY + r0 * sa[:-1]
        quads[:, 1, 0] = CX + r1 * ca[:-1]
        quads[:, 1, 1] = CY + r1 * sa[:-1]
        quads[:, 2, 0] = CX + r1 * ca[1:]
        quads[:, 2, 1] = CY + r1 * sa[1:]
        quads[:, 3, 0] = CX + r0 * ca[1:]
        quads[:, 3, 1] = CY + r0 * sa[1:]
        py5.no_stroke()
        py5.fill(*fill_rgba)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(quads.reshape(-1, 2))
        py5.no_fill()
        py5.stroke(*stroke_rgba)
        py5.stroke_weight(2.4)
        py5.circle(CX, CY, r0 * 2.0)
        py5.circle(CX, CY, r1 * 2.0)

    # Zodiac ring (deep Corinthian bronze & lapis band)
    draw_annulus(r_z_in, r_z_out, (34, 52, 68, 245), (214, 162, 68, 245))
    # Egyptian 365-day Sothic calendar ring (warm burnished brass-vellum band)
    draw_annulus(r_z_out, r_e_out, (238, 226, 198, 248), (142, 92, 38, 245))

    # 360 single-degree Zodiac graduation ticks
    deg_idx = np.arange(360, dtype=np.float64)
    deg_rad = np.deg2rad(deg_idx)
    c_d, s_d = np.cos(deg_rad), np.sin(deg_rad)
    tick_len = np.where(deg_idx % 30 == 0, 74.0, np.where(deg_idx % 5 == 0, 18.0, 9.5))
    z_ticks = np.column_stack([
        CX + r_z_in * c_d,
        CY + r_z_in * s_d,
        CX + (r_z_in + tick_len) * c_d,
        CY + (r_z_in + tick_len) * s_d,
    ])
    py5.stroke(236, 194, 104, 195)
    py5.stroke_weight(1.4)
    py5.lines(z_ticks)

    # 365 single-day Egyptian calendar graduation ticks & 365 index pin holes
    day_idx = np.arange(365, dtype=np.float64)
    day_rad = day_idx * (2.0 * math.pi / 365.0)
    c_e, s_e = np.cos(day_rad), np.sin(day_rad)
    e_len = np.where(day_idx % 30 == 0, 69.0, np.where(day_idx % 5 == 0, 16.0, 8.5))
    e_ticks = np.column_stack([
        CX + (r_e_out - e_len) * c_e,
        CY + (r_e_out - e_len) * s_e,
        CX + r_e_out * c_e,
        CY + r_e_out * s_e,
    ])
    py5.stroke(112, 74, 32, 195)
    py5.stroke_weight(1.3)
    py5.lines(e_ticks)

    # 12 Zodiac Sign Inscriptions & 12 Egyptian Month Inscriptions
    py5.text_align(py5.CENTER, py5.CENTER)
    for k in range(12):
        mid_ang = (k + 0.5) * (math.pi / 6.0) - 0.5 * math.pi
        rot_txt = mid_ang + 0.5 * math.pi
        if math.sin(mid_ang) > 0.0:
            rot_txt += math.pi

        # Zodiac inscription at r = 702
        zx = CX + 702.0 * math.cos(mid_ang)
        zy = CY + 702.0 * math.sin(mid_ang)
        py5.push_matrix()
        py5.translate(zx, zy)
        py5.rotate(rot_txt)
        py5.fill(248, 224, 152, 245)
        py5.text_size(12)
        py5.text(ZODIAC_NAMES[k], 0, 0)
        py5.pop_matrix()

        # Egyptian month inscription at r = 768
        ex = CX + 768.0 * math.cos(mid_ang)
        ey = CY + 768.0 * math.sin(mid_ang)
        py5.push_matrix()
        py5.translate(ex, ey)
        py5.rotate(rot_txt)
        py5.fill(86, 54, 22, 245)
        py5.text_size(12)
        py5.text(f"{k+1:02d} {EGYPTIAN_MONTHS[k]}", 0, 0)
        py5.pop_matrix()


def draw_solar_and_lunar_pointers(tau: float, omega: float, phi_lunar: float, lunar_vel_ratio: float):
    """
    Renders the monumental Golden Helios Solar Pointer, the Anomalistic Lunar Pointer
    with its revolving 3D half-silvered / half-obsidian Lunar Phase Sphere (b0),
    and the Draconic Eclipse Node Dragon Hand.
    """
    sun_ang = omega * tau + RND_SOLAR_EPOCH - 0.5 * math.pi
    moon_ang = -phi_lunar - 0.5 * math.pi
    node_ang = -omega * tau + RND_APSIDAL_PHASE

    # 1. Draconic Ascending/Descending Node Hand (Biblical/Hellenistic Dragon Head & Tail)
    nx0, ny0 = CX + 640.0 * math.cos(node_ang), CY + 640.0 * math.sin(node_ang)
    nx1, ny1 = CX - 640.0 * math.cos(node_ang), CY - 640.0 * math.sin(node_ang)
    py5.stroke(184, 52, 42, 185)
    py5.stroke_weight(3.2)
    py5.line(nx0, ny0, nx1, ny1)
    py5.fill(184, 52, 42, 245)
    py5.stroke(252, 236, 212, 240)
    py5.stroke_weight(1.8)
    py5.circle(nx0, ny0, 16.0)
    py5.circle(nx1, ny1, 14.0)

    # 2. Golden Helios Solar Ray Pointer
    sx_tip = CX + 695.0 * math.cos(sun_ang)
    sy_tip = CY + 695.0 * math.sin(sun_ang)
    sx_tail = CX - 145.0 * math.cos(sun_ang)
    sy_tail = CY - 145.0 * math.sin(sun_ang)
    py5.stroke(38, 24, 12, 180)
    py5.stroke_weight(9.0)
    py5.line(sx_tail + 4.0, sy_tail + 5.0, sx_tip + 4.0, sy_tip + 5.0)
    py5.stroke(238, 178, 42, 250)
    py5.stroke_weight(5.5)
    py5.line(sx_tail, sy_tail, sx_tip, sy_tip)

    # Radiant Helios Sunburst Emblem at R = 595 along Solar Pointer
    sun_emblem_x = CX + 595.0 * math.cos(sun_ang)
    sun_emblem_y = CY + 595.0 * math.sin(sun_ang)
    py5.fill(248, 198, 56, 255)
    py5.stroke(96, 56, 12, 245)
    py5.stroke_weight(2.0)
    py5.circle(sun_emblem_x, sun_emblem_y, 34.0)
    for r_i in range(12):
        ra = sun_ang + r_i * (math.pi / 6.0)
        py5.line(
            sun_emblem_x + 17.0 * math.cos(ra),
            sun_emblem_y + 17.0 * math.sin(ra),
            sun_emblem_x + 28.0 * math.cos(ra),
            sun_emblem_y + 28.0 * math.sin(ra),
        )

    # 3. Silver-Bronze Lunar Pointer & Revolving 3D Half-Silvered Lunar Phase Globe (b0)
    mx_tip = CX + 675.0 * math.cos(moon_ang)
    my_tip = CY + 675.0 * math.sin(moon_ang)
    mx_tail = CX - 130.0 * math.cos(moon_ang)
    my_tail = CY - 130.0 * math.sin(moon_ang)
    py5.stroke(24, 34, 46, 220)
    py5.stroke_weight(8.0)
    py5.line(mx_tail, my_tail, mx_tip, my_tip)
    py5.stroke(224, 234, 246, 250)
    py5.stroke_weight(4.2)
    py5.line(mx_tail, my_tail, mx_tip, my_tip)

    # Revolving 3D Lunar Phase Sphere at R = 365 along Lunar Pointer
    moon_gx = CX + 365.0 * math.cos(moon_ang)
    moon_gy = CY + 365.0 * math.sin(moon_ang)
    elongation = (moon_ang - sun_ang) % (2.0 * math.pi)
    draw_3d_lunar_phase_globe(moon_gx, moon_gy, 28.0, elongation)

    # Central Coaxial Turret Cap (Hellenistic Bronze Rosette Boss)
    py5.fill(184, 126, 48, 255)
    py5.stroke(62, 38, 14, 250)
    py5.stroke_weight(2.8)
    py5.circle(CX, CY, 68.0)
    py5.fill(242, 194, 78, 255)
    py5.circle(CX, CY, 36.0)
    py5.fill(44, 54, 66, 255)
    py5.circle(CX, CY, 14.0)


def draw_3d_lunar_phase_globe(gx: float, gy: float, rad: float, elongation: float):
    """
    Renders the Antikythera Mechanism's mechanical 3D Lunar Phase Sphere (gear b0):
    half-silvered, half-obsidian globe rotating in its housing aperture according
    to synodic solar-lunar elongation.
    """
    # Bronze housing bezel
    py5.fill(198, 144, 58, 255)
    py5.stroke(68, 42, 16, 245)
    py5.stroke_weight(2.2)
    py5.circle(gx, gy, (rad + 6.0) * 2.0)

    # Obsidian dark hemisphere base
    py5.no_stroke()
    py5.fill(18, 24, 34, 255)
    py5.circle(gx, gy, rad * 2.0)

    # Illuminated silver hemisphere bounded by terminator ellipse cos(elongation)
    k_term = math.cos(elongation)
    waxing = math.sin(elongation) >= 0.0
    n_pts = 32
    ang = np.linspace(-0.5 * math.pi, 0.5 * math.pi, n_pts)
    limb_x = rad * np.cos(ang) * (1.0 if waxing else -1.0)
    limb_y = rad * np.sin(ang)
    term_x = -k_term * rad * np.cos(ang[::-1]) * (1.0 if waxing else -1.0)
    term_y = rad * np.sin(ang[::-1])

    poly = np.column_stack([
        gx + np.concatenate([limb_x, term_x]),
        gy + np.concatenate([limb_y, term_y]),
    ])
    py5.fill(236, 242, 250, 250)
    with py5.begin_shape():
        py5.vertices(poly)

    py5.no_fill()
    py5.stroke(42, 54, 68, 220)
    py5.stroke_weight(1.8)
    py5.circle(gx, gy, rad * 2.0)


def draw_card_frame(x: float, y: float, w: float, h: float):
    """Draws an archival Aegean vellum & Corinthian bronze museum card frame."""
    py5.no_stroke()
    py5.fill(58, 46, 32, 24)
    py5.rect(x + 6, y + 8, w, h, 8)

    py5.fill(251, 247, 238, 242)
    py5.stroke(148, 108, 62, 215)
    py5.stroke_weight(2.2)
    py5.rect(x, y, w, h, 8)

    py5.no_fill()
    py5.stroke(194, 158, 108, 145)
    py5.stroke_weight(1.1)
    py5.rect(x + 8, y + 8, w - 16, h - 16, 5)


def draw_archaeometric_apparatuses(tau: float, omega: float):
    """
    Renders 8 scholarly Hellenistic astronomy & Antikythera archaeometric apparatuses
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
    # CARD 1 (TOP-LEFT): FIG. 01 PIN-AND-SLOT LUNAR ANOMALY & FIG. 02 SAROS SPIRAL
    # =========================================================================
    draw_card_frame(lx, ty, cw, th)
    py5.text_align(py5.LEFT, py5.TOP)

    # --- FIG. 01: HIPPARCHUS PIN-AND-SLOT LUNAR ANOMALY (k1 / k2) ---
    py5.fill(46, 32, 18)
    py5.text_size(17)
    py5.text("FIG. 01 // HIPPARCHUS PIN-AND-SLOT LUNAR ANOMALY (k1 / k2)", lx + 28, ty + 24)
    py5.fill(42, 98, 90)
    py5.text_size(12)
    py5.text("ECCENTRIC 50-TOOTH EPICYCLIC GEARS k1 & k2 DRIVING ANOMALISTIC LUNAR VELOCITY", lx + 28, ty + 48)

    f1_cx = lx + 175.0
    f1_cy = ty + 215.0
    e_f1 = 24.0
    aps_f1 = 0.35
    o2_x = f1_cx + e_f1 * math.cos(aps_f1)
    o2_y = f1_cy + e_f1 * math.sin(aps_f1)

    phi_in_f1 = -2.0 * omega * tau + RND_SOLAR_EPOCH
    phi_out_f1, vel_ratio_f1 = compute_pin_and_slot_lunar_kinematics(phi_in_f1, aps_f1)

    draw_hellenistic_gear(o2_x, o2_y, 96.0, 50, phi_out_f1, 1, n_spokes=5, alpha=230)
    draw_hellenistic_gear(f1_cx, f1_cy, 88.0, 50, phi_in_f1, 3, n_spokes=5, alpha=220)

    # Radial slot on k2 and pin on k1
    py5.stroke(34, 24, 14, 240)
    py5.stroke_weight(11.0)
    py5.line(
        o2_x + 32.0 * math.cos(phi_out_f1),
        o2_y + 32.0 * math.sin(phi_out_f1),
        o2_x + 82.0 * math.cos(phi_out_f1),
        o2_y + 82.0 * math.sin(phi_out_f1),
    )
    py5.stroke(248, 212, 108, 245)
    py5.stroke_weight(5.5)
    py5.line(
        o2_x + 32.0 * math.cos(phi_out_f1),
        o2_y + 32.0 * math.sin(phi_out_f1),
        o2_x + 82.0 * math.cos(phi_out_f1),
        o2_y + 82.0 * math.sin(phi_out_f1),
    )
    px_f1 = f1_cx + 60.0 * math.cos(phi_in_f1)
    py_f1 = f1_cy + 60.0 * math.sin(phi_in_f1)
    py5.fill(184, 52, 42, 255)
    py5.stroke(252, 242, 212, 255)
    py5.stroke_weight(2.0)
    py5.circle(px_f1, py_f1, 14.0)

    tx1 = lx + 340.0
    ty1 = ty + 88.0
    f1_specs = [
        ("CARRIER TURNTABLE", ": Gear e3 (223T) / b1 (224T)", (46, 32, 18)),
        ("DRIVING PIN GEAR k1", ": 50 Teeth (Sidereal Input)", (168, 106, 24)),
        ("SLOTTED GEAR k2", ": 50 Teeth (Anomalistic Output)", (32, 98, 88)),
        ("AXIS ECCENTRICITY (e)", ": 1.12 mm (r_pin = 9.6 mm)", (46, 32, 18)),
        ("APSIDAL PRECESSION", ": 8.85 Tropical Years (Full Loop)", (28, 68, 110)),
        ("INSTANT VELOCITY RATIO", f": {vel_ratio_f1:0.3f} x MEAN SIDEREAL", (184, 52, 42)),
        ("EQUATION OF CENTER", ": +/- 5.1 DEG HIPPARCHUS MODEL", (32, 98, 88)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f1_specs):
        yy = ty1 + i * 33.0
        py5.fill(96, 78, 56)
        py5.text_size(12)
        py5.text(k_lbl, tx1, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx1 + 178.0, yy)

    py5.stroke(194, 168, 128, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, ty + 390, lx + cw - 24, ty + 390)

    # --- FIG. 02: 223-MONTH SAROS ECLIPSE SPIRAL DIAL & GLYPH PREDICTOR ---
    py5.no_stroke()
    py5.fill(46, 32, 18)
    py5.text_size(17)
    py5.text("FIG. 02 // 223-MONTH SAROS ECLIPSE SPIRAL DIAL (REAR LOWER)", lx + 28, ty + 412)
    py5.fill(42, 98, 90)
    py5.text_size(12)
    py5.text("4-TURN SLOTTED ARCHIMEDEAN SPIRAL PREDICTING LUNAR (S) & SOLAR (H) ECLIPSES", lx + 28, ty + 436)

    f2_cx = lx + 175.0
    f2_cy = ty + 625.0
    # 4-turn Saros spiral (theta from 0 to 8*pi)
    s_ang = np.linspace(0.0, 8.0 * math.pi, 320)
    s_rad = 26.0 + (92.0 / (8.0 * math.pi)) * s_ang
    sp_x = f2_cx + s_rad * np.cos(s_ang)
    sp_y = f2_cy + s_rad * np.sin(s_ang)
    sp_segs = np.column_stack([sp_x[:-1], sp_y[:-1], sp_x[1:], sp_y[1:]])

    py5.stroke(156, 114, 58, 220)
    py5.stroke_weight(5.5)
    py5.lines(sp_segs)
    py5.stroke(38, 28, 18, 235)
    py5.stroke_weight(2.2)
    py5.lines(sp_segs)

    # Eclipse glyph stations along the Saros spiral
    for e_idx in range(0, 223, 6):
        ea = (e_idx / 223.0) * 8.0 * math.pi
        er = 26.0 + (92.0 / (8.0 * math.pi)) * ea
        ex = f2_cx + er * math.cos(ea)
        ey = f2_cy + er * math.sin(ea)
        is_solar = (e_idx % 12 == 0)
        py5.fill(*(184, 52, 42, 235) if is_solar else (28, 68, 110, 235))
        py5.no_stroke()
        py5.circle(ex, ey, 6.5)

    # Sliding pin follower along the 4-turn Saros slot
    cur_saros_a = tau * 8.0 * math.pi
    cur_saros_r = 26.0 + (92.0 / (8.0 * math.pi)) * cur_saros_a
    sx_f2 = f2_cx + cur_saros_r * math.cos(cur_saros_a)
    sy_f2 = f2_cy + cur_saros_r * math.sin(cur_saros_a)
    py5.stroke(184, 126, 42, 245)
    py5.stroke_weight(3.2)
    py5.line(f2_cx, f2_cy, sx_f2, sy_f2)
    py5.fill(184, 52, 42, 255)
    py5.stroke(252, 242, 212, 255)
    py5.stroke_weight(2.0)
    py5.circle(sx_f2, sy_f2, 13.0)

    saros_month = int(tau * 223) % 223 + 1
    tx2 = lx + 340.0
    ty2 = ty + 485.0
    f2_specs = [
        ("SAROS CYCLE LENGTH", ": 223 Synodic Months (18y 11d 8h)", (46, 32, 18)),
        ("DRACONIC RESONANCE", ": 242 Draconic Months (Node Return)", (32, 98, 88)),
        ("ANOMALISTIC RESONANCE", ": 239 Anomalistic Months (Perigee)", (28, 68, 110)),
        ("ACTIVE SPIRAL CELL", f": MONTH {saros_month:03d} / 223", (184, 52, 42)),
        ("GLYPH 'S' (SELENES)", ": 38 Lunar Eclipse Stations", (28, 68, 110)),
        ("GLYPH 'H' (HELIOU)", ": 27 Solar Eclipse Stations", (184, 52, 42)),
        ("EXELIGMOS DIAL (3x)", ": 669 Months (+8h Shift Sub-Dial)", (168, 106, 24)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f2_specs):
        yy = ty2 + i * 33.0
        py5.fill(96, 78, 56)
        py5.text_size(12)
        py5.text(k_lbl, tx2, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx2 + 178.0, yy)

    # =========================================================================
    # CARD 2 (BOTTOM-LEFT): FIG. 03 METONIC & GAMES DIAL & FIG. 04 ALLOY PALETTE
    # =========================================================================
    draw_card_frame(lx, by, cw, bh)

    # --- FIG. 03: 19-YEAR METONIC SPIRAL (235 MONTHS) & PANHELLENIC GAMES ---
    py5.fill(46, 32, 18)
    py5.text_size(17)
    py5.text("FIG. 03 // 19-YEAR METONIC SPIRAL & STEPHANITIC GAMES DIAL", lx + 28, by + 24)
    py5.fill(42, 98, 90)
    py5.text_size(12)
    py5.text("5-TURN 235-MONTH LUNISOLAR CALENDAR & 4-YEAR CROWN GAMES (OLYMPIA/PYTHIA)", lx + 28, by + 48)

    f3_cx = lx + 175.0
    f3_cy = by + 215.0
    m_ang = np.linspace(0.0, 10.0 * math.pi, 360)
    m_rad = 34.0 + (84.0 / (10.0 * math.pi)) * m_ang
    mp_x = f3_cx + m_rad * np.cos(m_ang)
    mp_y = f3_cy + m_rad * np.sin(m_ang)
    mp_segs = np.column_stack([mp_x[:-1], mp_y[:-1], mp_x[1:], mp_y[1:]])
    py5.stroke(42, 98, 90, 210)
    py5.stroke_weight(4.5)
    py5.lines(mp_segs)

    # Inner 4-sector Panhellenic Crown Games dial
    py5.fill(244, 234, 212, 250)
    py5.stroke(148, 98, 42, 235)
    py5.stroke_weight(2.0)
    py5.circle(f3_cx, f3_cy, 58.0)
    py5.line(f3_cx - 29.0, f3_cy, f3_cx + 29.0, f3_cy)
    py5.line(f3_cx, f3_cy - 29.0, f3_cx, f3_cy + 29.0)
    games_ang = 4.0 * omega * tau
    py5.stroke(184, 52, 42, 250)
    py5.stroke_weight(2.8)
    py5.line(f3_cx, f3_cy, f3_cx + 26.0 * math.cos(games_ang), f3_cy + 26.0 * math.sin(games_ang))

    met_month = int(tau * 235) % 235 + 1
    tx3 = lx + 340.0
    ty3 = by + 88.0
    f3_specs = [
        ("METONIC IDENTITY", ": 19 Tropical Years = 235 Months", (46, 32, 18)),
        ("INTERCALARY EMBOLISMIC", ": 7 Intercalary Months per 19 Yr", (32, 98, 88)),
        ("ACTIVE METONIC CELL", f": MONTH {met_month:03d} / 235 (5-Turn Slot)", (168, 106, 24)),
        ("CROWN GAMES SECTOR I", ": OLYMPIA (Year 1 / 4 Quadrennial)", (184, 52, 42)),
        ("CROWN GAMES SECTOR II", ": PYTHIA & NEMEA (Years 2 & 3)", (28, 68, 110)),
        ("CROWN GAMES SECTOR IV", ": ISTHMIA & NAA (Dodona Sanctuary)", (32, 98, 88)),
        ("CALLIPPIC CORRECTION", ": 76 Years = 4 Metonic - 1 Day", (46, 32, 18)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f3_specs):
        yy = ty3 + i * 33.0
        py5.fill(96, 78, 56)
        py5.text_size(12)
        py5.text(k_lbl, tx3, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx3 + 178.0, yy)

    py5.stroke(194, 168, 128, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, by + 390, lx + cw - 24, by + 390)

    # --- FIG. 04: METALLURGICAL ALLOY & ARCHAEOMETRIC CT STRATIGRAPHY ---
    py5.no_stroke()
    py5.fill(46, 32, 18)
    py5.text_size(17)
    py5.text("FIG. 04 // ARCHAEOMETRIC METALLURGY & MARINE PATINA SPEC", lx + 28, by + 412)
    py5.fill(42, 98, 90)
    py5.text_size(12)
    py5.text("X-RAY MICRO-TOMOGRAPHY (82 FRAGMENTS A-G) & CU-SN ALLOY STRATIGRAPHY", lx + 28, by + 436)

    swatches = [
        ((214, 152, 36), "SYRACUSE HIGH-TIN BRONZE (Cu 95% / Sn 5%) // SOLAR & PIN GEARS b1, k1"),
        ((178, 120, 56), "CORINTHIAN PHOSPHOR-BRONZE // METONIC & PLANETARY TRAINS c1, g1, m1"),
        ((44, 114, 104), "AEGEAN MALACHITE PATINA (Cu2CO3(OH)2) // 2,000-YEAR MARINE INCRUSTATION"),
        ((28, 68, 110), "HELLENISTIC ASTRAL LAPIS GLAZE // ZODIAC PARAPEGMA & ECLIPSE RING"),
        ((184, 52, 42), "CARNELIAN SOLAR ECLIPSE & DRACONIC NODE INDEX // HELIOU GLYPH"),
        ((236, 242, 250), "BURNISHED SILVER HEMISPHERE // 3D REVOLVING LUNAR PHASE SPHERE b0"),
    ]
    for i, (rgb_s, desc_s) in enumerate(swatches):
        sy = by + 482.0 + i * 54.0
        py5.fill(*rgb_s)
        py5.stroke(86, 62, 34, 220)
        py5.stroke_weight(1.6)
        py5.rect(lx + 32, sy, 52, 34, 4)
        py5.no_stroke()
        py5.fill(46, 32, 18)
        py5.text_size(13)
        py5.text(desc_s, lx + 104, sy + 9)

    # =========================================================================
    # CARD 3 (TOP-RIGHT): FIG. 05 60-DEG TOOTH PROFILE & FIG. 06 GEAR LEDGER
    # =========================================================================
    draw_card_frame(rx, ty, cw, th)

    # --- FIG. 05: HELLENISTIC 60-DEG EQUILATERAL TRIANGULAR TOOTH PROFILE ---
    py5.fill(46, 32, 18)
    py5.text_size(17)
    py5.text("FIG. 05 // HELLENISTIC 60-DEG EQUILATERAL GEAR TOOTH GEOMETRY", rx + 28, ty + 24)
    py5.fill(42, 98, 90)
    py5.text_size(12)
    py5.text("HAND-FILED BRONZE TRIANGULAR TEETH MESHING ACROSS PITCH CIRCLES R_1, R_2", rx + 28, ty + 48)

    # Close-up meshing diagram of two 60-degree triangular-tooth segments
    f5_x = rx + 175.0
    f5_y = ty + 215.0
    draw_hellenistic_gear(f5_x - 58.0, f5_y, 64.0, 20, 2.0 * omega * tau, 3, n_spokes=4)
    draw_hellenistic_gear(f5_x + 58.0, f5_y, 64.0, 20, -2.0 * omega * tau + math.pi / 20.0, 1, n_spokes=4)

    # Pitch circle tangent line
    py5.stroke(184, 52, 42, 210)
    py5.stroke_weight(1.8)
    py5.line(f5_x, f5_y - 82.0, f5_x, f5_y + 82.0)

    tx5 = rx + 340.0
    ty5 = ty + 88.0
    f5_specs = [
        ("TOOTH PROFILE ANGLE", ": 60.0 DEG Equilateral Triangle", (46, 32, 18)),
        ("CIRCULAR PITCH (p)", ": 1.58 mm Mean Tooth Spacing", (168, 106, 24)),
        ("BRONZE PLATE THICKNESS", ": 1.6 mm to 2.3 mm Hammered Sheet", (32, 98, 88)),
        ("TOTAL SURVIVING GEARS", ": 30 Gears in Fragment A (37 Total)", (28, 68, 110)),
        ("LARGEST GEAR (b1)", ": 224 Teeth (Diameter 130.0 mm)", (184, 52, 42)),
        ("SMALLEST PINION (d1)", ": 15 to 24 Teeth (High-Ratio Stage)", (32, 98, 88)),
        ("ENGRAVED GLYPH COUNT", ": >3,500 Greek Text Characters", (46, 32, 18)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f5_specs):
        yy = ty5 + i * 33.0
        py5.fill(96, 78, 56)
        py5.text_size(12)
        py5.text(k_lbl, tx5, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx5 + 178.0, yy)

    py5.stroke(194, 168, 128, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, ty + 390, rx + cw - 24, ty + 390)

    # --- FIG. 06: BABYLONIAN PERIOD RELATIONS & EXACT GEAR TRAIN RATIOS ---
    py5.no_stroke()
    py5.fill(46, 32, 18)
    py5.text_size(17)
    py5.text("FIG. 06 // BABYLONIAN PERIOD RELATIONS & GEAR TRAIN RATIOS", rx + 28, ty + 412)
    py5.fill(42, 98, 90)
    py5.text_size(12)
    py5.text("EXACT PRIME-FACTORIZATION GEAR TRAINS RECONSTRUCTED BY PRICE, WRIGHT & FREETH", rx + 28, ty + 436)

    rows = [
        ("SIDEREAL LUNAR (254:19)", "(64/38)*(48/24)*(127/32)", "13.368421", "ACTIVE"),
        ("METONIC SPIRAL (5-TURN)", "(64/38)*(53/96)*(54/27)", "5/19 YR", "ACTIVE"),
        ("SAROS ECLIPSE (223M)", "(64/38)*(48/24)*(127/223)", "4/223 M", "ACTIVE"),
        ("EXELIGMOS TRIPLE (669M)", "SAROS * (27/54)*(20/60)", "1/669 M", "ACTIVE"),
        ("OLYMPIAD GAMES (4 YR)", "METONIC * (53/96)*(19/4)", "1/4 YR", "ACTIVE"),
        ("VENUS SYNODIC (5:8 YR)", "(64/40) EPICYCLIC PIN", "288:461", "ACTIVE"),
    ]
    for r_i, (c_name, c_formula, c_ratio, c_stat) in enumerate(rows):
        ry_row = ty + 478.0 + r_i * 55.0
        is_hi = (r_i == 0 or r_i == 2)
        py5.fill(*(242, 232, 206, 240) if is_hi else (249, 245, 236, 210))
        py5.stroke(*(184, 126, 42, 235) if is_hi else (196, 174, 138, 165))
        py5.stroke_weight(1.8 if is_hi else 1.1)
        py5.rect(rx + 28, ry_row, cw - 56, 44, 5)

        py5.no_stroke()
        py5.fill(46, 32, 18)
        py5.text_size(12)
        py5.text(c_name, rx + 44, ry_row + 15)
        py5.fill(28, 68, 110)
        py5.text(c_formula, rx + 285, ry_row + 15)
        py5.fill(184, 52, 42)
        py5.text(f"RATIO = {c_ratio}", rx + 515, ry_row + 15)
        py5.fill(32, 98, 88)
        py5.text(c_stat, rx + 662, ry_row + 15)

    # =========================================================================
    # CARD 4 (BOTTOM-RIGHT): FIG. 07 RETROGRADE LOOP & FIG. 08 LUNAR WAVEFORM
    # =========================================================================
    draw_card_frame(rx, by, cw, bh)

    # --- FIG. 07: PLANETARY EPICYCLE & RETROGRADE STATION LOOP ---
    py5.fill(46, 32, 18)
    py5.text_size(17)
    py5.text("FIG. 07 // APOLLONIUS-HIPPARCHUS PLANETARY RETROGRADE LOOP", rx + 28, by + 24)
    py5.fill(42, 98, 90)
    py5.text_size(12)
    py5.text("GEOCENTRIC DEFERENT + EPICYCLE VECTOR SUM PRODUCING STATION POINTS S1, S2", rx + 28, by + 48)

    f7_cx = rx + 175.0
    f7_cy = by + 215.0
    t7 = np.linspace(0.0, 2.0 * math.pi, 200)
    x7 = f7_cx + 68.0 * np.cos(t7) + 38.0 * np.cos(-4.0 * t7)
    y7 = f7_cy + 68.0 * np.sin(t7) + 38.0 * np.sin(-4.0 * t7)
    segs7 = np.column_stack([x7[:-1], y7[:-1], x7[1:], y7[1:]])
    py5.no_fill()
    py5.stroke(148, 118, 78, 140)
    py5.stroke_weight(1.4)
    py5.circle(f7_cx, f7_cy, 136.0)
    py5.stroke(184, 52, 42, 220)
    py5.stroke_weight(2.4)
    py5.lines(segs7)

    a_d7 = omega * tau
    a_e7 = -4.0 * omega * tau
    dx7 = f7_cx + 68.0 * math.cos(a_d7)
    dy7 = f7_cy + 68.0 * math.sin(a_d7)
    px7 = dx7 + 38.0 * math.cos(a_e7)
    py7 = dy7 + 38.0 * math.sin(a_e7)
    py5.stroke(28, 68, 110, 220)
    py5.stroke_weight(1.8)
    py5.circle(dx7, dy7, 76.0)
    py5.line(f7_cx, f7_cy, dx7, dy7)
    py5.line(dx7, dy7, px7, py7)
    py5.fill(184, 52, 42, 255)
    py5.circle(px7, py7, 11.0)

    tx7 = rx + 340.0
    ty7 = by + 88.0
    f7_specs = [
        ("GEOCENTRIC MODEL", ": Apollonius of Perga Epicycle", (46, 32, 18)),
        ("INFERIOR PLANETS", ": Hermes (Mercury) & Phosphoros", (28, 68, 110)),
        ("SUPERIOR PLANETS", ": Pyroeis, Phaethon, Phainon", (184, 52, 42)),
        ("FIRST STATION (S1)", ": Prograde -> Retrograde Reversal", (168, 106, 24)),
        ("SECOND STATION (S2)", ": Retrograde -> Prograde Resumption", (32, 98, 88)),
        ("FRONT DIAL INSCRIPTION", ": Exact Station Degree Intervals", (46, 32, 18)),
        ("MECHANISM COUPLING", ": Pin-and-Slot Follower on b1 Plate", (28, 68, 110)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f7_specs):
        yy = ty7 + i * 33.0
        py5.fill(96, 78, 56)
        py5.text_size(12)
        py5.text(k_lbl, tx7, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx7 + 178.0, yy)

    py5.stroke(194, 168, 128, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, by + 390, rx + cw - 24, by + 390)

    # --- FIG. 08: LUNAR ANOMALISTIC VELOCITY & ELONGATION PHASE WAVEFORM ---
    py5.no_stroke()
    py5.fill(46, 32, 18)
    py5.text_size(17)
    py5.text("FIG. 08 // LUNAR ANOMALISTIC VELOCITY & ECLIPSE LATITUDE WAVEFORM", rx + 28, by + 412)
    py5.fill(42, 98, 90)
    py5.text_size(12)
    py5.text("HARMONIC VARIATION OF d(THETA_M)/dt (k1/k2), DRACONIC NODE LATITUDE & PHASE", rx + 28, by + 436)

    wx = rx + 36.0
    wy = by + 482.0
    ww = cw - 72.0
    wh = 285.0
    py5.fill(244, 238, 224, 240)
    py5.stroke(164, 134, 92, 200)
    py5.stroke_weight(1.6)
    py5.rect(wx, wy, ww, wh, 6)

    # Grid lines inside waveform plot
    py5.stroke(212, 196, 168, 160)
    py5.stroke_weight(1.1)
    for g_i in range(1, 4):
        gy_w = wy + (wh / 4.0) * g_i
        py5.line(wx, gy_w, wx + ww, gy_w)
    for g_j in range(1, 6):
        gx_w = wx + (ww / 6.0) * g_j
        py5.line(gx_w, wy, gx_w, wy + wh)

    n_w = 180
    u_w = np.linspace(0.0, 2.0 * math.pi, n_w)
    xw_arr = wx + (u_w / (2.0 * math.pi)) * ww
    mid_wy = wy + 0.5 * wh

    # Curve 1: Pin-and-slot anomalistic lunar velocity modulation
    yw1 = mid_wy - 92.0 * (0.78 * np.cos(2.0 * u_w - omega * tau) + 0.22 * np.cos(4.0 * u_w - 2.0 * omega * tau))
    # Curve 2: Draconic nodal eclipse latitude beta(t)
    yw2 = mid_wy - 82.0 * np.sin(3.0 * u_w + omega * tau)
    # Curve 3: Solar-lunar synodic elongation harmonic
    yw3 = mid_wy - 68.0 * np.cos(u_w - omega * tau)

    for y_arr, col_w in [
        (yw1, (184, 52, 42, 235)),
        (yw2, (32, 98, 88, 225)),
        (yw3, (184, 126, 32, 225)),
    ]:
        segs_w = np.column_stack([xw_arr[:-1], y_arr[:-1], xw_arr[1:], y_arr[1:]])
        py5.stroke(*col_w)
        py5.stroke_weight(2.6)
        py5.lines(segs_w)

    # Current phase marker line
    cur_wx = wx + tau * ww
    py5.stroke(28, 68, 110, 210)
    py5.stroke_weight(2.0)
    py5.line(cur_wx, wy, cur_wx, wy + wh)

    py5.no_stroke()
    py5.fill(86, 64, 38)
    py5.text_size(12)
    py5.text(
        "CARNELIAN: k1/k2 ANOMALISTIC VELOCITY  //  VERDIGRIS: DRACONIC LATITUDE  //  GOLD: SYNODIC PHASE",
        wx + 8,
        wy + wh + 18,
    )


def draw_archival_border_and_typography(tau: float):
    """Draws the outer museum architectural frame, title header, and telemetry footer."""
    py5.no_fill()
    py5.stroke(134, 94, 48, 225)
    py5.stroke_weight(3.2)
    py5.rect(52, 48, WIDTH - 104, HEIGHT - 96, 10)

    py5.stroke(184, 146, 96, 165)
    py5.stroke_weight(1.4)
    py5.rect(64, 60, WIDTH - 128, HEIGHT - 120, 6)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(42, 28, 14)
    py5.text_size(30)
    py5.text(
        "THE ANTIKYTHERA MECHANISM // EPICYCLIC LUNAR ANOMALY & SAROS ECLIPSE COMPUTER",
        CX,
        82,
    )

    py5.fill(38, 96, 88)
    py5.text_size(15)
    py5.text(
        "HELLENISTIC GEARED ASTRONOMICAL CALCULATOR (c. 150-100 BCE) - HIPPARCHUS k1/k2 PIN-AND-SLOT & 254:19 METONIC TRAIN",
        CX,
        124,
    )

    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(86, 66, 42)
    py5.text_size(14)
    py5.text(
        "NATIONAL ARCHAEOLOGICAL MUSEUM FRAGMENTS A-G // 30 SURVIVING BRONZE GEARS // METONIC 235M & SAROS 223M SPIRALS",
        96,
        HEIGHT - 74,
    )

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K ARCHAEOMETRIC KINEMATICS // HARMONIC EPOCH TAU = {tau:0.3f} (12.0s @ 60FPS)",
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

