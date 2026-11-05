"""
Kinetic Nipkow Mechanical Television & Selenium Scan-Disc 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Signal / Glitch / Digital Artifacts genre,
exploring Paul Gottlieb Nipkow's 1884 German Imperial Patent No. 30105 Elektrisches
Teleskop (spinning spiral-perforated raster scanning disc), Arthur Korn's 1904
crystalline selenium phototelegraphy (Bildtelegraphie), and John Logie Baird's 1926
30-line mechanical Televisor with neon Glimmlampe glow-discharge reconstruction,
executed on warm archival patent vellum (#f5f1e6).

Inside a recessed Prussian-vulcanite electro-optical housing, a monumental spoked
Nipkow disc of radius R = 740 px rotates with 30 square bevel-framed scanning
apertures arranged along a single turn of an Archimedean spiral:
    r_k = R_outer - k * (H_gate / 30),   theta_k = 2*pi * k / 30
Positioned across the upper-central viewing sector is the curved 30-line arcuate
Televisor Bildfenster (image gate), where 30 concentric arc scanlines reconstruct
a high-contrast geometric television test pattern in neon-discharge vermilion-orange,
sodium amber, and selenium carrier teal. Periodic phonic-wheel motor phase slip
(Delta_phi) induces horizontal raster line-tearing glitches, while crystalline
selenium photoconductive lag creates glowing exponential persistence wakes behind
the sweeping flying-spot apertures, flanked by eight early television apparatuses.

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
WORK_NAME = "kinetic_nipkow_mechanical_television_selenium_scan_disc_2d"
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
RND_DISC_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_GLITCH_SEED = int(np.random.randint(100, 99999))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 22.0
HOUSING_R = 805.0
DISC_R = 742.0

# 30-line Nipkow spiral parameters spanning radial band r in [275 px, 685 px]
N_LINES = 30
R_SCAN_OUTER = 685.0
R_SCAN_INNER = 275.0
DR_LINE = (R_SCAN_OUTER - R_SCAN_INNER) / float(N_LINES)


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

    # 1. Warm Imperial Patent & Phototelegraphy Vellum (#f5f1e6)
    py5.background(245, 241, 230)

    # 2. Patent Blueprint Coordinate Grid & Electro-Optical Halo
    draw_patent_vellum_substrate(tau)

    # 3. Central Monumental Nipkow Spiral Scan-Disc & 30-Line Arcuate Televisor Gate
    draw_central_nipkow_televisor(tau, omega)

    # 4. Eight Mechanical Television & Selenium Phototelegraphy Apparatuses Across Four Flank Cards
    draw_nipkow_apparatuses(tau, omega)

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


def draw_patent_vellum_substrate(tau: float):
    """Draws warm patent vellum toning washes and precision millimeter coordinate hairlines."""
    py5.no_stroke()
    for r_g, col_g in [
        (1180, (238, 232, 218, 95)),
        (940, (230, 224, 208, 90)),
        (835, (218, 210, 192, 100)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    py5.stroke(212, 204, 188, 135)
    py5.stroke_weight(1.1)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)


def evaluate_test_pattern_signal(u_norm: float, v_norm: float, tau: float, omega: float, sync_tear: float):
    """
    Evaluates the 1928 Baird / Reichspost 30-Line Mechanical Television Test Pattern
    at normalized gate coordinates u_norm in [-1, 1] (horizontal arc), v_norm in [-1, 1]
    (vertical radial scanline), including horizontal phonic-wheel sync-slip tearing!
    Returns quantized signal level in [0..6].
    """
    u_s = u_norm + sync_tear
    r_p = math.hypot(u_s * 1.15, v_norm)
    ang_p = math.atan2(v_norm, u_s + 1e-6)

    # Concentric zone-plate target rings + rotating radial test Maltese crossbars + border frame
    ring_wave = math.cos(5.5 * math.pi * r_p - 2.0 * omega * tau)
    spoke_wave = math.cos(4.0 * ang_p + omega * tau)
    diag_bars = math.sin(6.0 * math.pi * (u_s + 0.5 * v_norm) + omega * tau)

    # Border checkerboard calibration bars at top/bottom/sides of the Bildfenster
    if abs(u_norm) > 0.84 or abs(v_norm) > 0.86:
        chk = 1.0 if (int((u_norm + 1.0) * 8.0) + int((v_norm + 1.0) * 8.0)) % 2 == 0 else 0.12
        val = chk
    elif r_p < 0.24:
        # Bright central bullseye beacon
        val = 0.96 - 1.5 * r_p
    elif r_p < 0.68:
        val = 0.52 + 0.34 * ring_wave + 0.22 * spoke_wave
    else:
        val = 0.45 + 0.38 * diag_bars

    return max(0.0, min(1.0, val))


def draw_central_nipkow_televisor(tau: float, omega: float):
    """
    Renders the central Nipkow Mechanical Television Scanner & 30-Line Arcuate Raster:
    1. Outer Prussian-vulcanite housing & 60-tooth phonic-wheel synchronous motor stator
    2. Rotating Vulcanite & Brass Nipkow Disc (R = 742 px) with 8 spoked flywheel cutouts,
       radial sector lines, and the continuous Archimedean spiral guide track
    3. Two Opposite Arcuate 30-Line Televisor Viewing Windows (Upper-Right Transmitter
       Selenium Gate & Lower-Left Receiver Neon Glimmlampe Raster Window) so the entire
       circular composition is dynamically balanced and overflowing with 30-line raster detail!
    4. 30 Square Beveled Brass Nipkow Spiral Apertures orbiting along r_k = R_out - k*dr
       and emitting glowing flying-spot scan beams as they sweep across the raster gates
    5. Central Phonic-Wheel Synchronous Rotor Hub, Selenium Cell Bridge & Tachometer Strobe
    """
    # Disc rotation angle: 2 full revolutions per 12s animation loop
    theta_disc = 2.0 * omega * tau + RND_DISC_PHASE

    # --- 1. OUTER HOUSING & 60-TOOTH PHONIC-WHEEL STATOR RING ---
    py5.no_stroke()
    py5.fill(112, 86, 48, 255)
    py5.circle(CX, CY, (HOUSING_R + 16.0) * 2.0)

    py5.fill(16, 26, 42, 255)
    py5.circle(CX, CY, HOUSING_R * 2.0)

    # 60-tooth brass phonic-wheel stator teeth inside [DISC_R + 8 .. HOUSING_R - 8]
    n_stator = 60
    stator_quads = []
    for s_i in range(n_stator):
        a0 = (s_i / float(n_stator)) * 2.0 * math.pi
        a1 = ((s_i + 0.55) / float(n_stator)) * 2.0 * math.pi
        r_in_s = DISC_R + 10.0
        r_out_s = HOUSING_R - 12.0
        stator_quads.append([
            [CX + r_in_s * math.cos(a0), CY + r_in_s * math.sin(a0)],
            [CX + r_out_s * math.cos(a0), CY + r_out_s * math.sin(a0)],
            [CX + r_out_s * math.cos(a1), CY + r_out_s * math.sin(a1)],
            [CX + r_in_s * math.cos(a1), CY + r_in_s * math.sin(a1)],
        ])
    py5.no_stroke()
    py5.fill(188, 142, 58, 210)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(stator_quads, dtype=np.float64).reshape(-1, 2))

    # --- 2. ROTATING VULCANITE & BRASS NIPKOW DISC ---
    py5.fill(22, 34, 54, 255)
    py5.stroke(218, 168, 68, 245)
    py5.stroke_weight(3.6)
    py5.circle(CX, CY, DISC_R * 2.0)

    # Concentric brushed vulcanite & anodized aluminum turning rings on the Nipkow disc
    py5.no_fill()
    for r_c in range(260, int(DISC_R), 28):
        py5.stroke(46, 68, 98, 115)
        py5.stroke_weight(1.2)
        py5.circle(CX, CY, r_c * 2.0)

    # 30 Radial Nipkow sector division hairlines rotating with the disc
    rad_segs = []
    for k in range(N_LINES):
        ak = theta_disc + (k / float(N_LINES)) * 2.0 * math.pi
        ca, sa = math.cos(ak), math.sin(ak)
        rad_segs.append([
            CX + 185.0 * ca, CY + 185.0 * sa,
            CX + (DISC_R - 8.0) * ca, CY + (DISC_R - 8.0) * sa,
        ])
    py5.stroke(78, 108, 148, 130)
    py5.stroke_weight(1.2)
    py5.lines(np.array(rad_segs, dtype=np.float64))

    # --- 3. TWO MONUMENTAL 30-LINE ARCUATE RASTER WINDOWS (BILDFENSTER) ---
    # Window A (Upper-Right / Top-Center): Receiver Neon Glimmlampe 30-Line Raster Gate
    # Window B (Lower-Left / Bottom-Center): Transmitter Selenium Photo-Conductive Raster Gate
    # Each window spans 108 degrees of azimuth across all 30 radial scanline tracks
    # r in [R_SCAN_INNER (275 px) .. R_SCAN_OUTER (685 px)], filling the disc with luminous
    # 30-line arcuate raster signal bricks!
    n_arc_cols = 44

    # Palette for Receiver Neon Glimmlampe (Warm Vermilion-Orange -> Sodium Amber -> Incandescent Gold)
    NEON_BUCKETS = [
        (16, 22, 34),      # 0: Black blanking level
        (78, 26, 28),      # 1: Deep neon cathode glow
        (142, 42, 32),     # 2: Low-current crimson neon
        (198, 68, 36),     # 3: Mid-level Glimmlampe vermilion
        (232, 112, 38),    # 4: Bright neon-orange discharge
        (246, 168, 52),    # 5: High-luminance sodium amber
        (254, 232, 138),   # 6: Peak crater-lamp white-gold
    ]

    # Palette for Transmitter Selenium Photocell (Deep Prussian -> Selenium Teal -> Electric Cyan-Gold)
    SELENIUM_BUCKETS = [
        (14, 24, 38),      # 0: Dark shadow resistance R_max
        (22, 58, 78),      # 1: Low photoconductive current
        (28, 98, 118),     # 2: Mid-low selenium response
        (36, 144, 152),    # 3: Active selenium carrier teal
        (68, 188, 178),    # 4: High photo-current turquoise
        (164, 224, 192),   # 5: Saturated specular highlight
        (248, 214, 96),    # 6: Flying-spot aperture flash gold
    ]

    windows = [
        # (center_angle_rad, span_rad, is_neon_window, label_str)
        (-0.35 * math.pi, 0.58 * math.pi, True, "NEON GLIMMLAMPE 30-LINE RECEIVER GATE"),
        (0.65 * math.pi, 0.58 * math.pi, False, "SELENIUM PHOTOCELL TRANSMITTER GATE"),
    ]

    raster_batches = {}  # Key: (is_neon, bucket_idx) -> list of 4x2 quads
    frame_bezels = []

    for w_ang_c, w_span, is_neon, _ in windows:
        a_start = w_ang_c - 0.5 * w_span
        a_end = w_ang_c + 0.5 * w_span
        a_edges = np.linspace(a_start, a_end, n_arc_cols + 1)
        ca_e = np.cos(a_edges)
        sa_e = np.sin(a_edges)

        for line_k in range(N_LINES):
            v_norm = (line_k / float(N_LINES - 1)) * 2.0 - 1.0
            r_out_l = R_SCAN_OUTER - line_k * DR_LINE - 1.2
            r_in_l = r_out_l - DR_LINE + 2.4

            # Periodic horizontal phonic-wheel sync-tearing glitch on bands of scanlines
            glitch_env = math.sin(3.0 * omega * tau + line_k * 0.45)
            sync_tear = 0.18 * math.sin(2.0 * omega * tau - line_k * 0.8) if glitch_env > 0.52 else 0.0

            # Check if the spinning Nipkow aperture for line_k is currently sweeping near this window
            ap_ang = (theta_disc + (line_k / float(N_LINES)) * 2.0 * math.pi) % (2.0 * math.pi)

            for col_j in range(n_arc_cols):
                u_norm = (col_j / float(n_arc_cols - 1)) * 2.0 - 1.0
                sig = evaluate_test_pattern_signal(u_norm, v_norm, tau, omega, sync_tear)

                # Add exponential selenium/neon flying-spot persistence boost behind the passing aperture
                cell_ang = 0.5 * (a_edges[col_j] + a_edges[col_j + 1]) % (2.0 * math.pi)
                d_ang = (ap_ang - cell_ang) % (2.0 * math.pi)
                if d_ang < 0.45:
                    sig = min(1.0, sig + 0.48 * math.exp(-d_ang * 6.5))

                b_idx = max(0, min(6, int(sig * 6.99)))
                q_cell = (
                    (CX + r_in_l * ca_e[col_j], CY + r_in_l * sa_e[col_j]),
                    (CX + r_out_l * ca_e[col_j], CY + r_out_l * sa_e[col_j]),
                    (CX + r_out_l * ca_e[col_j + 1], CY + r_out_l * sa_e[col_j + 1]),
                    (CX + r_in_l * ca_e[col_j + 1], CY + r_in_l * sa_e[col_j + 1]),
                )
                raster_batches.setdefault((is_neon, b_idx), []).append(q_cell)

        # Brass & steel arcuate frame bezel segments around the Bildfenster gate
        for r_b in [R_SCAN_INNER - 6.0, R_SCAN_OUTER + 6.0]:
            xb = CX + r_b * ca_e
            yb = CY + r_b * sa_e
            frame_bezels.append(np.column_stack([xb[:-1], yb[:-1], xb[1:], yb[1:]]))
        for a_side in [a_start, a_end]:
            frame_bezels.append(np.array([[
                CX + (R_SCAN_INNER - 6.0) * math.cos(a_side),
                CY + (R_SCAN_INNER - 6.0) * math.sin(a_side),
                CX + (R_SCAN_OUTER + 6.0) * math.cos(a_side),
                CY + (R_SCAN_OUTER + 6.0) * math.sin(a_side),
            ]], dtype=np.float64))

    # Render all batched 30-line arcuate raster cells
    py5.no_stroke()
    for (is_neon, b_idx), q_list in raster_batches.items():
        cr, cg, cb = NEON_BUCKETS[b_idx] if is_neon else SELENIUM_BUCKETS[b_idx]
        py5.fill(cr, cg, cb, 248)
        q_arr = np.array(q_list, dtype=np.float64)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(q_arr.reshape(-1, 2))

    # Render bold brass Bildfenster gate bezels
    if frame_bezels:
        all_bez = np.vstack(frame_bezels)
        py5.stroke(14, 20, 32, 245)
        py5.stroke_weight(6.5)
        py5.lines(all_bez)
        py5.stroke(236, 184, 72, 245)
        py5.stroke_weight(3.0)
        py5.lines(all_bez)

    # --- 4. ARCHIMEDEAN SPIRAL TRACK & 30 ROTATING SQUARE NIPKOW APERTURES ---
    # Continuous Archimedean spiral locus connecting the 30 scanning holes
    u_sp = np.linspace(0.0, 1.0, 180)
    ang_sp = theta_disc + u_sp * 2.0 * math.pi
    r_sp = R_SCAN_OUTER - 0.5 * DR_LINE - u_sp * (R_SCAN_OUTER - R_SCAN_INNER - DR_LINE)
    x_sp = CX + r_sp * np.cos(ang_sp)
    y_sp = CY + r_sp * np.sin(ang_sp)
    segs_sp = np.column_stack([x_sp[:-1], y_sp[:-1], x_sp[1:], y_sp[1:]])
    py5.stroke(12, 18, 28, 225)
    py5.stroke_weight(5.2)
    py5.lines(segs_sp)
    py5.stroke(245, 194, 78, 235)
    py5.stroke_weight(2.2)
    py5.lines(segs_sp)

    # 30 Square Beveled Brass Nipkow Apertures along the spiral
    ap_outer_quads = []
    ap_inner_quads = []
    beam_wake_quads = []

    for k in range(N_LINES):
        ak = theta_disc + (k / float(N_LINES)) * 2.0 * math.pi
        rk = R_SCAN_OUTER - (k + 0.5) * DR_LINE
        ca, sa = math.cos(ak), math.sin(ak)
        tx, ty = -sa, ca  # Tangent unit vector

        ax = CX + rk * ca
        ay = CY + rk * sa

        # Outer brass collar & inner incandescent flying-spot aperture square
        s_out = 9.2
        s_in = 5.6
        for s_half, target_list in [(s_out, ap_outer_quads), (s_in, ap_inner_quads)]:
            p0 = (ax - ca * s_half - tx * s_half, ay - sa * s_half - ty * s_half)
            p1 = (ax + ca * s_half - tx * s_half, ay + sa * s_half - ty * s_half)
            p2 = (ax + ca * s_half + tx * s_half, ay + sa * s_half + ty * s_half)
            p3 = (ax - ca * s_half + tx * s_half, ay - sa * s_half + ty * s_half)
            target_list.append((p0, p1, p2, p3))

        # Trailing flying-spot selenium persistence arc behind each aperture
        a_trail = ak - 0.14
        cat, sat = math.cos(a_trail), math.sin(a_trail)
        beam_wake_quads.append((
            (CX + (rk - 5.0) * ca, CY + (rk - 5.0) * sa),
            (CX + (rk + 5.0) * ca, CY + (rk + 5.0) * sa),
            (CX + (rk + 5.0) * cat, CY + (rk + 5.0) * sat),
            (CX + (rk - 5.0) * cat, CY + (rk - 5.0) * sat),
        ))

    py5.no_stroke()
    py5.fill(250, 204, 21, 145)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(beam_wake_quads, dtype=np.float64).reshape(-1, 2))

    py5.stroke(14, 20, 32, 240)
    py5.stroke_weight(1.4)
    py5.fill(218, 162, 54, 255)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(ap_outer_quads, dtype=np.float64).reshape(-1, 2))

    py5.no_stroke()
    py5.fill(255, 248, 214, 255)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(ap_inner_quads, dtype=np.float64).reshape(-1, 2))

    # --- 5. CENTRAL SYNCHRONOUS PHONIC-WHEEL ROTOR HUB & STROBOSCOPE DISC ---
    r_hub = 225.0
    py5.fill(18, 28, 44, 255)
    py5.stroke(218, 168, 68, 245)
    py5.stroke_weight(3.2)
    py5.circle(CX, CY, r_hub * 2.0)

    # 8 Brass Flywheel Spokes & Stroboscopic Speed-Calibration Sectors inside the hub
    n_spokes = 16
    strob_quads = []
    for sp_i in range(n_spokes):
        if sp_i % 2 == 0:
            a0 = theta_disc + (sp_i / float(n_spokes)) * 2.0 * math.pi
            a1 = theta_disc + ((sp_i + 1) / float(n_spokes)) * 2.0 * math.pi
            r0_h, r1_h = 68.0, r_hub - 16.0
            strob_quads.append([
                [CX + r0_h * math.cos(a0), CY + r0_h * math.sin(a0)],
                [CX + r1_h * math.cos(a0), CY + r1_h * math.sin(a0)],
                [CX + r1_h * math.cos(a1), CY + r1_h * math.sin(a1)],
                [CX + r0_h * math.cos(a1), CY + r0_h * math.sin(a1)],
            ])
    py5.no_stroke()
    py5.fill(214, 158, 52, 225)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(strob_quads, dtype=np.float64).reshape(-1, 2))

    # Central steel drive shaft & brass keyway collar
    py5.fill(38, 48, 66, 255)
    py5.stroke(244, 198, 92, 255)
    py5.stroke_weight(2.8)
    py5.circle(CX, CY, 112.0)
    py5.fill(228, 72, 44, 255)
    py5.no_stroke()
    py5.circle(CX, CY, 34.0)


def draw_light_card_frame(x: float, y: float, w: float, h: float):
    """Draws a warm Imperial Patent Office card frame with brass corner brackets."""
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


def draw_nipkow_apparatuses(tau: float, omega: float):
    """
    Renders 8 Mechanical Television & Selenium Phototelegraphy apparatuses across 4 flank cards.
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
    # CARD 1 (TOP-LEFT): FIG. 01 DRP 30105 SPIRAL & FIG. 02 ARCUATE RASTER
    # =========================================================================
    draw_light_card_frame(lx, ty, cw, th)

    # --- FIG. 01: DRP PATENT 30105 ARCHIMEDEAN SPIRAL APERTURE LOCUS ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 01 // DRP PATENT 30105 ARCHIMEDEAN SPIRAL APERTURE LOCUS", lx + 28, ty + 24)
    py5.fill(198, 68, 36)
    py5.text_size(12)
    py5.text("r_k = R_OUTER - k * (H_GATE / N), THETA_k = 2*PI * k / N (N = 30 SCANLINES @ 12.5 FPS)", lx + 28, ty + 48)

    # Mini Nipkow spiral disc diagram at (lx + 172, ty + 215)
    f1_cx, f1_cy = lx + 172.0, ty + 215.0
    py5.fill(242, 236, 224, 245)
    py5.stroke(28, 58, 96, 225)
    py5.stroke_weight(2.2)
    py5.circle(f1_cx, f1_cy, 184.0)

    u1 = np.linspace(0.0, 1.0, 90)
    a1 = u1 * 2.0 * math.pi + 2.0 * omega * tau
    r1 = 82.0 - u1 * 48.0
    x1 = f1_cx + r1 * np.cos(a1)
    y1 = f1_cy + r1 * np.sin(a1)
    py5.stroke(198, 68, 36, 235)
    py5.stroke_weight(2.4)
    py5.lines(np.column_stack([x1[:-1], y1[:-1], x1[1:], y1[1:]]))

    for k1 in range(0, 30, 2):
        ak1 = (k1 / 30.0) * 2.0 * math.pi + 2.0 * omega * tau
        rk1 = 82.0 - (k1 / 30.0) * 48.0
        py5.fill(28, 58, 96, 255)
        py5.no_stroke()
        py5.circle(f1_cx + rk1 * math.cos(ak1), f1_cy + rk1 * math.sin(ak1), 6.5)

    tx1 = lx + 336.0
    ty1 = ty + 88.0
    f1_specs = [
        ("IMPERIAL PATENT", ": DRP No. 30105 (Paul Nipkow, Jan 1884)", (198, 68, 36)),
        ("SCANNING SPIRAL", ": Single-Turn Archimedean r(th) = R-b*th", (28, 58, 96)),
        ("VERTICAL RESOLUTION", ": N = 30 Curved Scanlines per Frame", (144, 94, 24)),
        ("ASPECT RATIO", ": 3 : 7 Vertical Baird Portrait Gate", (36, 118, 96)),
        ("ROTOR ANGULAR SPEED", ": 750 RPM (f_frame = 12.5 Hz)", (38, 30, 22)),
        ("LINE SCAN FREQUENCY", ": f_line = 30 x 12.5 = 375.0 Hz", (198, 68, 36)),
        ("APERTURE PITCH", ": Delta_theta = 12.0 DEG Arc Spacing", (28, 58, 96)),
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

    # --- FIG. 02: ARCUATE RASTER GEOMETRY & KEYSTONE CURVATURE ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 02 // ARCUATE BILDFENSTER GEOMETRY & SCANLINE CURVATURE", lx + 28, ty + 412)
    py5.fill(28, 58, 96)
    py5.text_size(12)
    py5.text("RADIAL ARC SAGITTA s_k = r_k * (1 - COS(DELTA_THETA / 2)) ACROSS THE VIEWING GATE", lx + 28, ty + 436)

    # Curved arcuate scanline fan diagram inside [lx+42..lx+300, ty+488..ty+728]
    f2_cx, f2_cy = lx + 172.0, ty + 785.0
    a2 = np.linspace(-0.72 * math.pi, -0.28 * math.pi, 50)
    for k2 in range(8):
        r2 = 115.0 + k2 * 22.0
        x2 = f2_cx + r2 * np.cos(a2)
        y2 = f2_cy + r2 * np.sin(a2)
        py5.stroke(*(198, 68, 36, 230) if k2 % 2 == 0 else (28, 58, 96, 215))
        py5.stroke_weight(2.6)
        py5.lines(np.column_stack([x2[:-1], y2[:-1], x2[1:], y2[1:]]))

    tx2 = lx + 336.0
    ty2 = ty + 485.0
    f2_specs = [
        ("SCANLINE TRAJECTORY", ": Concentric Circular Arcs of Radius r_k", (198, 68, 36)),
        ("KEYSTONE RATIO", ": W_outer / W_inner = R_out / R_in", (28, 58, 96)),
        ("ANGULAR GATE WIDTH", ": Delta_Phi = 2*pi / N = 12.0 DEG Nominal", (144, 94, 24)),
        ("SPOT VELOCITY (v_k)", ": v_k = omega_disc * r_k (Outer Faster)", (36, 118, 96)),
        ("SHADING VARIATION", ": Outer Lines 2.4x Brighter Before Comp.", (38, 30, 22)),
        ("APERTURE SHAPE", ": Square / Diamond Diaphragm Stops", (198, 68, 36)),
        ("TRANSMITTER OPTICS", ": Condenser Lens + Spotlight Flood Bank", (28, 58, 96)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f2_specs):
        yy = ty2 + i * 33.0
        py5.fill(96, 82, 64)
        py5.text_size(12)
        py5.text(k_lbl, tx2, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx2 + 178.0, yy)

    # =========================================================================
    # CARD 2 (BOTTOM-LEFT): FIG. 03 SELENIUM RESPONSE & FIG. 04 PALETTE
    # =========================================================================
    draw_light_card_frame(lx, by, cw, bh)

    # --- FIG. 03: CRYSTALLINE SELENIUM PHOTOCELL RESPONSE & THERMAL LAG ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 03 // SELENIUM PHOTOCONDUCTIVE CELL & EXPONENTIAL LAG TAIL", lx + 28, by + 24)
    py5.fill(36, 118, 96)
    py5.text_size(12)
    py5.text("ARTHUR KORN COMPENSATED SELENIUM BRIDGE: SIGMA(E) = SIGMA_0 + k * SQRT(E)", lx + 28, by + 48)

    f3_x, f3_y, f3_w, f3_h = lx + 42.0, by + 95.0, 255.0, 240.0
    py5.fill(242, 236, 224, 245)
    py5.stroke(158, 136, 104, 215)
    py5.stroke_weight(1.6)
    py5.rect(f3_x, f3_y, f3_w, f3_h, 5)

    # Square-wave light pulse vs sluggish selenium exponential rise/decay curve
    u3 = np.linspace(0.0, 1.0, 100)
    x3_p = f3_x + 14.0 + u3 * (f3_w - 28.0)
    sq_pulse = np.where((u3 > 0.2) & (u3 < 0.6), 1.0, 0.0)
    se_resp = np.where(
        u3 <= 0.2,
        0.0,
        np.where(
            u3 <= 0.6,
            1.0 - np.exp(-(u3 - 0.2) * 8.5),
            (1.0 - math.exp(-0.4 * 8.5)) * np.exp(-(u3 - 0.6) * 5.2),
        ),
    )
    y3_sq = (f3_y + f3_h - 24.0) - sq_pulse * (f3_h - 56.0)
    y3_se = (f3_y + f3_h - 24.0) - se_resp * (f3_h - 56.0)
    py5.stroke(28, 58, 96, 185)
    py5.stroke_weight(2.0)
    py5.lines(np.column_stack([x3_p[:-1], y3_sq[:-1], x3_p[1:], y3_sq[1:]]))
    py5.stroke(198, 68, 36, 245)
    py5.stroke_weight(3.0)
    py5.lines(np.column_stack([x3_p[:-1], y3_se[:-1], x3_p[1:], y3_se[1:]]))

    tx3 = lx + 336.0
    ty3 = by + 88.0
    f3_specs = [
        ("SEMICONDUCTOR", ": Trigonal Metallic Gray Selenium (Z=34)", (36, 118, 96)),
        ("DARK RESISTANCE", ": R_dark = 120 kOhm -> R_lit = 18 kOhm", (28, 58, 96)),
        ("RELAXATION TIME", ": tau_Se = 12.0 ms Carrier Trap Decay", (198, 68, 36)),
        ("KORN BRIDGE (1904)", ": Differential 2-Cell Inertia Canceler", (144, 94, 24)),
        ("PHOTOELECTRIC UPGRADE", ": Potassium Hydride Vacuum Cell (1927)", (38, 30, 22)),
        ("BASEBAND BANDWIDTH", ": f_max = 12.5 kHz AM Audio-Carrier", (198, 68, 36)),
        ("VISUAL ARTIFACT", ": Horizontal Comet-Tail Persistence Blur", (36, 118, 96)),
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

    # --- FIG. 04: NEON GLIMMLAMPE, SELENIUM & PATENT VELLUM PALETTE ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 04 // NEON GLIMMLAMPE, SELENIUM & VULCANITE PALETTE", lx + 28, by + 412)
    py5.fill(198, 68, 36)
    py5.text_size(12)
    py5.text("585-640 nm NEON CATHODE GLOW, SELENIUM CARRIER TEAL & TURNED BRASS", lx + 28, by + 436)

    swatches = [
        ((198, 68, 36), "NEON GLIMMLAMPE VERMILION // 640.2 nm COLD-CATHODE GAS DISCHARGE CRATER TUBE"),
        ((246, 168, 52), "MOORE LAMP SODIUM AMBER // 585.2 nm PEAK IONIZATION FLYING-SPOT HIGHLIGHT"),
        ((36, 144, 152), "SELENIUM PHOTOCELL TEAL // TRIGONAL SELENIUM PHOTOCONDUCTIVE BRIDGE SIGNAL"),
        ((214, 158, 52), "IMPERIAL INSTRUMENT BRASS // BEVELED NIPKOW APERTURE DIAPHRAGM & STATOR"),
        ((22, 34, 54), "EBONITE VULCANITE ROTOR // SULFUR-VULCANIZED HARD RUBBER SCANNING DISC"),
        ((245, 241, 230), "KAISERLICHES PATENTAMT VELLUM // 1884 GERMAN IMPERIAL PATENT SPECIFICATION PAPER"),
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
    # CARD 3 (TOP-RIGHT): FIG. 05 MECHANICAL OPTICS & FIG. 06 CODEX LEDGER
    # =========================================================================
    draw_light_card_frame(rx, ty, cw, th)

    # --- FIG. 05: NIPKOW DISC VS. WEILLER MIRROR DRUM (SPIEGELRAD) OPTICS ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 05 // MECHANICAL SCANNING TAXONOMY: LENS DISC & SPIEGELRAD", rx + 28, ty + 24)
    py5.fill(28, 58, 96)
    py5.text_size(12)
    py5.text("BAIRD LENS-IN-DISC ARRAY (1926) VS. WEILLER TILTED POLYGON MIRROR DRUM (1889)", rx + 28, ty + 48)

    # Left: Baird lens disc; Right: Weiller 12-facet polygonal mirror drum with reflected beam
    c5_x1, c5_y1 = rx + 112.0, ty + 215.0
    py5.fill(242, 236, 224, 245)
    py5.stroke(28, 58, 96, 225)
    py5.stroke_weight(2.0)
    py5.circle(c5_x1, c5_y1, 128.0)
    for k5 in range(8):
        a5 = k5 * (math.pi / 4.0) + omega * tau
        r5 = 48.0 - k5 * 2.5
        py5.fill(56, 189, 248, 220)
        py5.stroke(28, 58, 96, 235)
        py5.stroke_weight(1.5)
        py5.circle(c5_x1 + r5 * math.cos(a5), c5_y1 + r5 * math.sin(a5), 16.0)

    c5_x2, c5_y2 = rx + 242.0, ty + 215.0
    a_poly = np.linspace(0.0, 2.0 * math.pi, 13) + 0.5 * omega * tau
    px_m = c5_x2 + 54.0 * np.cos(a_poly)
    py_m = c5_y2 + 54.0 * np.sin(a_poly)
    py5.stroke(198, 68, 36, 235)
    py5.stroke_weight(2.4)
    py5.lines(np.column_stack([px_m[:-1], py_m[:-1], px_m[1:], py_m[1:]]))

    tx5 = rx + 336.0
    ty5 = ty + 88.0
    f5_specs = [
        ("NIPKOW PINHOLE DISC", ": Simple Stamped Sheet, f/40 Low Flux", (198, 68, 36)),
        ("BAIRD LENS DISC", ": 30 Condenser Lenses Mounted in Spiral", (28, 58, 96)),
        ("WEILLER SPIEGELRAD", ": 30 Canted Mirrors on Drum Perimeter", (36, 118, 96)),
        ("MIHALY TELEHOR", ": Oscillating Mirror Galvanometer", (144, 94, 24)),
        ("JENKINS PRISM RINGS", ": Counter-Rotating Liquid-Glass Prisms", (38, 30, 22)),
        ("FLYING-SPOT SCANNER", ": Inverted Ray Path (Dark Studio Arc)", (198, 68, 36)),
        ("OPTICAL EFFICIENCY", ": Mirror Drum 18x Brighter than Pinhole", (28, 58, 96)),
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

    # --- FIG. 06: HISTORICAL MECHANICAL TELEVISION & TELEPHOTOGRAPHY LEDGER ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 06 // HISTORICAL MECHANICAL TELEVISION & TELEPHOTOGRAPHY LEDGER", rx + 28, ty + 412)
    py5.fill(198, 68, 36)
    py5.text_size(12)
    py5.text("FROM BAIN'S FACSIMILE (1843) & NIPKOW (1884) TO BAIRD'S 30-LINE TELEVISOR", rx + 28, ty + 436)

    rows = [
        ("COPYING TELEGRAPH (1843)", "Alexander Bain", "Pendulum Stylus", "First Image Scan"),
        ("DRP PATENT 30105 (1884)", "Paul G. Nipkow", "24/30-Hole Spiral", "Elektr. Teleskop"),
        ("BILDTELEGRAPHIE (1904)", "Arthur Korn", "Selenium Tube", "Munich-Nuremberg"),
        ("SOHO TELEVISOR (1926)", "John Logie Baird", "30-Line Halftone", "First Live Human TV"),
        ("BELL LABS COLOR (1929)", "Herbert E. Ives", "3-Channel RGB Disc", "50-Line Neon/Argon"),
        ("ACTIVE 30-LINE RASTER", "750 RPM Spiral", "f_line = 375.0 Hz", "HARMONIC LIVE"),
    ]
    for r_i, (c_name, c_inv, c_sys, c_note) in enumerate(rows):
        ry_row = ty + 478.0 + r_i * 55.0
        is_hi = (r_i == 1 or r_i == 5)
        py5.fill(*(240, 228, 204, 242) if is_hi else (248, 244, 234, 215))
        py5.stroke(*(198, 68, 36, 235) if is_hi else (194, 176, 144, 175))
        py5.stroke_weight(1.9 if is_hi else 1.1)
        py5.rect(rx + 28, ry_row, cw - 56, 44, 5)

        py5.no_stroke()
        py5.fill(38, 30, 22)
        py5.text_size(12)
        py5.text(c_name, rx + 44, ry_row + 15)
        py5.fill(28, 58, 96)
        py5.text(c_inv, rx + 265, ry_row + 15)
        py5.fill(198, 68, 36)
        py5.text(c_sys, rx + 435, ry_row + 15)
        py5.fill(36, 118, 96)
        py5.text(c_note, rx + 595, ry_row + 15)

    # =========================================================================
    # CARD 4 (BOTTOM-RIGHT): FIG. 07 PHONIC WHEEL SYNC & FIG. 08 VIDEO WAVEFORM
    # =========================================================================
    draw_light_card_frame(rx, by, cw, bh)

    # --- FIG. 07: PHONIC WHEEL SYNCHRONIZATION & PHASE-TEARING GLITCH ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 07 // PHONIC WHEEL SYNCHRONIZATION & RASTER TEARING ARTIFACT", rx + 28, by + 24)
    py5.fill(198, 68, 36)
    py5.text_size(12)
    py5.text("LACOUR TOOTHED IRON PHONIC WHEEL LOCKED TO 375 Hz LINE-SYNC PULSES", rx + 28, by + 48)

    # Sheared raster test bars diagram inside [rx+42..rx+300, by+95..by+335]
    f7_x, f7_y, f7_w, f7_h = rx + 42.0, by + 95.0, 255.0, 240.0
    py5.fill(22, 34, 54, 245)
    py5.stroke(158, 136, 104, 215)
    py5.stroke_weight(1.6)
    py5.rect(f7_x, f7_y, f7_w, f7_h, 5)

    for r7 in range(12):
        y7_r = f7_y + 14.0 + r7 * 18.0
        # Periodic horizontal sync-tear displacement on middle scanlines
        tear7 = 28.0 * math.sin(2.0 * omega * tau + r7 * 0.6) if (3 <= r7 <= 8) else 0.0
        py5.fill(*(232, 112, 38, 240) if (3 <= r7 <= 8) else (56, 189, 248, 225))
        py5.no_stroke()
        py5.rect(f7_x + 48.0 + tear7, y7_r, 154.0, 12.0, 2)

    tx7 = rx + 336.0
    ty7 = by + 88.0
    f7_specs = [
        ("SYNC MECHANISM", ": Toothed Iron Wheel + 2 Electromagnets", (198, 68, 36)),
        ("SYNC PULSE FREQ", ": f_sync = 375 Hz Line-End Blanking", (28, 58, 96)),
        ("PHASE HUNTING", ": Pendular Rotor Oscillation +/- 1.8 DEG", (144, 94, 24)),
        ("HORIZONTAL TEARING", ": Sudden Phase Slip Shifts Scanline X", (36, 118, 96)),
        ("FRAMING KNOB", ": Manual Stator Rotation Aligns Border", (38, 30, 22)),
        ("IONOSPHERIC MULTIPATH", ": Ghost Echoes on Shortwave AM Link", (198, 68, 36)),
        ("SIGNAL-TO-NOISE", ": SNR = 18.4 dB Carbon-Arc Studio", (28, 58, 96)),
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

    # --- FIG. 08: COMPOSITE 30-LINE AM VIDEO BASEBAND & SYNC OSCILLOGRAM ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 08 // 30-LINE COMPOSITE VIDEO BASEBAND & SYNC OSCILLOGRAM", rx + 28, by + 412)
    py5.fill(28, 58, 96)
    py5.text_size(12)
    py5.text("375 Hz LINE-BLANKING SYNC PEDESTALS, SELENIUM VIDEO & NEON DISCHARGE CURRENT", rx + 28, by + 436)

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

    n_w = 220
    u_w = np.linspace(0.0, 1.0, n_w)
    xw_arr = wx + u_w * ww
    mid_y = wy + wh * 0.52

    # Composite video signal with periodic negative sync pulses every 0.25 of trace
    sync_notch = np.where((u_w * 4.0) % 1.0 < 0.10, -85.0, 25.0 + 55.0 * np.sin(6.0 * math.pi * u_w - 2.0 * omega * tau))
    se_lag_w = 58.0 * np.sin(4.0 * math.pi * u_w - omega * tau) * np.cos(2.0 * math.pi * u_w + omega * tau)
    neon_i_w = 42.0 * np.cos(8.0 * math.pi * u_w - 2.0 * omega * tau)

    for y_off_w, col_w in [
        (sync_notch, (198, 68, 36, 240)),
        (se_lag_w, (36, 118, 96, 235)),
        (neon_i_w, (28, 58, 96, 225)),
    ]:
        yw_c = mid_y - y_off_w
        segs_w = np.column_stack([xw_arr[:-1], yw_c[:-1], xw_arr[1:], yw_c[1:]])
        py5.stroke(*col_w)
        py5.stroke_weight(2.5)
        py5.lines(segs_w)

    py5.no_stroke()
    py5.fill(86, 68, 44)
    py5.text_size(12)
    py5.text(
        "VERMILION: COMPOSITE VIDEO + 375 Hz SYNC  //  TEAL: SELENIUM BRIDGE  //  PRUSSIAN: PHONIC LOCK",
        wx + 8,
        wy + wh + 18,
    )


def draw_archival_border_and_typography(tau: float, omega: float):
    """Draws the outer Imperial Patent Office architectural border, header, and footer."""
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
        "NIPKOW MECHANICAL TELEVISION & SELENIUM SCAN-DISC // 30-LINE ARCUATE RASTER",
        CX,
        82,
    )

    py5.fill(198, 68, 36)
    py5.text_size(15)
    py5.text(
        "DRP PATENT 30105 ELEKTRISCHES TELESKOP (1884), KORN SELENIUM TELEPHOTOGRAPHY & BAIRD TELEVISOR (1926)",
        CX,
        124,
    )

    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(86, 72, 52)
    py5.text_size(14)
    py5.text(
        "30 ARCHIMEDEAN SPIRAL APERTURES // 750 RPM (12.5 FPS) // 375.0 Hz LINE SYNC // NEON GLIMMLAMPE & SELENIUM CELL",
        96,
        HEIGHT - 74,
    )

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K ANALOG RASTER ARTIFACTS // HARMONIC PHASE TAU = {tau:0.3f} (12.0s @ 60FPS)",
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

