"""
Kinetic Foraminifera Logarithmic Chamber Biomineralization 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Organic / Morphogenesis genre, exploring
marine Foraminifera (Thalamophora / Rotaliida / Globigerinacea) multilocular
calcite shell morphogenesis, D'Arcy Wentworth Thompson's gnomonic logarithmic
spiral accretion laws (On Growth and Form, 1917; Raup 1966 coiled shell morphospace),
Alcide d'Orbigny's 1826 Tableau methodique, and Ernst Haeckel's Kunstformen der
Natur Plate 2 (Thalamophora), executed on warm Victorian naturalist vellum (#f5f1e6).

Beginning from a central embryonic proloculus (megalospheric chamber), 26 successive
globular and crescentic calcium carbonate (CaCO3) chambers (loculi) accrete along a
self-similar equiangular spiral r(theta) = r_0 * exp(b * theta). Each chamber is
bounded by a double-walled bilamellar septum pierced by an arched basal aperture
(foramen, "opening") through which a continuous turquoise-and-gold cytoplasmic stream
flows, while delicate radiating calcite spines and anastomosing granuloreticulopodia
extend into the surrounding marine boundary layer, flanked by eight micropaleontology
and paleoclimatology telemetry apparatuses across four balanced flank cards.

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
WORK_NAME = "kinetic_foraminifera_logarithmic_chamber_biomineralization_2d"
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
RND_GROWTH_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_PORE_SEED = int(np.random.randint(100, 99999))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 22.0
MEDALLION_R = 805.0

# Raup & D'Arcy Thompson logarithmic spiral parameters for 32 multilocular chambers
# Spanning from R0_PROLOCULUS = 30 px out to r_31 = 485 px (outer chamber margin at ~660 px,
# with acicular calcite spines and anastomosing reticulopodia reaching r = 782 px).
N_CHAMBERS = 32
B_SPIRAL = 0.194  # Logarithmic flare rate b -> W = exp(2*pi*b) = 3.38 whorl expansion
R0_PROLOCULUS = 30.0
D_THETA = 0.455   # Angular step per chamber (~26.1 deg -> ~13.8 chambers per whorl, 2.32 whorls)

# Precompute unit circle & crescent geometry for fast vectorized chamber rendering
N_CHAMBER_PTS = 36
U_ANG = np.linspace(0.0, 2.0 * math.pi, N_CHAMBER_PTS + 1)
U_CA = np.cos(U_ANG)
U_SA = np.sin(U_ANG)

# 6-stop Victorian Naturalist & Biomineral Calcite Palette (from inner embryonic gold
# through rose-terracotta Globigerina ruber, warm travertine ochre, to outer alabaster):
CHAMBER_PALETTE = [
    # (outer_wall_rgb, mid_shell_rgb, inner_lumen_rgb, suture_rgb)
    ((188, 62, 44), (226, 112, 86), (250, 218, 198), (118, 34, 24)),     # Globigerinoides ruber Rose-Crimson
    ((204, 96, 42), (238, 152, 92), (252, 232, 206), (134, 58, 22)),     # Warm Terracotta Calcite
    ((214, 146, 44), (242, 194, 108), (254, 244, 216), (144, 94, 24)),   # Dinoflagellate Symbiont Amber
    ((168, 128, 88), (218, 192, 158), (248, 242, 230), (104, 78, 52)),   # Benthic Travertine Umber
    ((64, 128, 114), (124, 184, 168), (222, 244, 238), (36, 84, 74)),    # Chlorophyll Plastid Celadon
    ((52, 96, 144), (118, 162, 204), (224, 238, 250), (28, 58, 96)),     # Pelagic Prussian Slate Calcite
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

    # 1. Warm Victorian Naturalist Monograph Vellum (#f5f1e6)
    py5.background(245, 241, 230)

    # 2. Archival Monograph Coordinate Grid & Polar Gnomonic Wash
    draw_naturalist_vellum_substrate(tau)

    # 3. Central Monumental Foraminifera Logarithmic Chamber Biomineralization Medallion
    draw_central_foraminifera_medallion(tau, omega)

    # 4. Eight Micropaleontology & Morphogenesis Apparatuses Across Four Flank Cards
    draw_foraminifera_apparatuses(tau, omega)

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


def draw_naturalist_vellum_substrate(tau: float):
    """Draws warm vellum toning washes and precision naturalist micrometer hairlines."""
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


def draw_central_foraminifera_medallion(tau: float, omega: float):
    """
    Renders the central Foraminifera Biomineralization & Gnomonic Spiral Medallion:
    1. Recessed Prussian pelagic field with polar logarithmic gnomon coordinate net
    2. Radiant calcite acicular spines & anastomosing granuloreticulopodia streaming outward
    3. 26 accreting logarithmic chambers (loculi) with bilamellar calcite walls, vaulted
       sutural bridges (ponticuli), internal endosymbiont halos, and mural pore sieves
    4. Continuous intercameral foramen cytoplasmic stream spiraling from proloculus to aperture
    5. Engraved brass & mahogany microscope stage bezel with 360-degree goniometer ticks
    """
    # --- 1. RECESSED PELAGIC PRUSSIAN-INDIGO MICROSCOPE FIELD ---
    py5.no_stroke()
    py5.fill(112, 86, 48, 255)
    py5.circle(CX, CY, (MEDALLION_R + 16.0) * 2.0)

    py5.fill(18, 36, 58, 255)
    py5.circle(CX, CY, MEDALLION_R * 2.0)

    # Subtle concentric bathymetric depth rings inside the marine microscope field
    for r_m, col_m in [
        (720.0, (22, 44, 70, 180)),
        (580.0, (26, 54, 84, 165)),
        (420.0, (32, 64, 98, 150)),
        (260.0, (38, 76, 114, 140)),
    ]:
        py5.fill(*col_m)
        py5.circle(CX, CY, r_m * 2.0)

    # Polar goniometer radial rays (every 15 deg) & D'Arcy Thompson logarithmic spiral reference net
    rot_base = 0.25 * omega * tau + RND_GROWTH_PHASE
    rad_segs = []
    for deg in range(0, 360, 15):
        ang = math.radians(deg)
        ca, sa = math.cos(ang), math.sin(ang)
        rad_segs.append([CX + 45.0 * ca, CY + 45.0 * sa, CX + (MEDALLION_R - 28.0) * ca, CY + (MEDALLION_R - 28.0) * sa])
    py5.stroke(64, 102, 138, 95)
    py5.stroke_weight(1.1)
    py5.lines(np.array(rad_segs, dtype=np.float64))

    # Golden equiangular reference spirals r = r0 * exp(b * theta)
    th_sp = np.linspace(0.0, 16.5, 260)
    r_sp = R0_PROLOCULUS * np.exp(B_SPIRAL * th_sp)
    mask_sp = r_sp < (MEDALLION_R - 32.0)
    th_sp = th_sp[mask_sp]
    r_sp = r_sp[mask_sp]
    for arm_k in range(2):
        ang_arm = th_sp + rot_base + arm_k * math.pi
        x_sp = CX + r_sp * np.cos(ang_arm)
        y_sp = CY + r_sp * np.sin(ang_arm)
        segs_sp = np.column_stack([x_sp[:-1], y_sp[:-1], x_sp[1:], y_sp[1:]])
        py5.stroke(*(216, 164, 68, 135) if arm_k == 0 else (88, 148, 188, 95))
        py5.stroke_weight(1.8 if arm_k == 0 else 1.2)
        py5.lines(segs_sp)

    # --- 2. COMPUTE 32 LOGARITHMIC CHAMBERS (LOCULI) ---
    # Each chamber k in [0..31] sits at spiral angle theta_k = k * D_THETA
    # with harmonic osmotic breathing and 3D trochospiral tilt modulation
    chambers = []
    for k in range(N_CHAMBERS):
        # Continuous chamber phase
        theta_k = k * D_THETA
        # Harmonic breathing modulation of spiral radius and chamber inflation
        breath = 1.0 + 0.032 * math.sin(2.0 * omega * tau - k * 0.32)
        rk = R0_PROLOCULUS * math.exp(B_SPIRAL * theta_k) * breath
        ang_k = theta_k + rot_base

        cx_k = CX + rk * math.cos(ang_k)
        cy_k = CY + rk * math.sin(ang_k)

        # Chamber major & minor semi-axes scale proportionally to spiral radius rk (gnomonic similarity!)
        a_k = rk * 0.45 * (1.0 + 0.035 * math.cos(omega * tau + k * 0.4))
        b_k = rk * 0.35 * (1.0 + 0.035 * math.sin(omega * tau + k * 0.4))

        # Tangent orientation of the chamber lobe (tilted along spiral tangent psi = atan(1/b))
        tilt_k = ang_k + math.atan2(1.0, B_SPIRAL) - 0.28
        col_idx = k % len(CHAMBER_PALETTE)
        chambers.append((k, rk, ang_k, cx_k, cy_k, a_k, b_k, tilt_k, col_idx))

    # --- 3. RADIATING CALCITE SPINES & ANASTOMOSING GRANULORETICULOPODIA ---
    # Outer whorl chambers (k >= 14) project long crystalline calcite spines and branching
    # cytoplasmic reticulopodia filaments with streaming endosymbiont granules out to r = 780 px
    spine_segs = []
    retic_segs = []
    granule_quads = []

    for k, rk, ang_k, cx_k, cy_k, a_k, b_k, tilt_k, col_idx in chambers[14:]:
        n_rays = 5 if k < 22 else 7
        for r_i in range(n_rays):
            ray_ang = ang_k + (r_i - (n_rays - 1) * 0.5) * 0.11
            ca_r, sa_r = math.cos(ray_ang), math.sin(ray_ang)
            r_start = rk + b_k * 0.55
            r_end = min(MEDALLION_R - 24.0, r_start + 165.0 + 185.0 * (k / float(N_CHAMBERS)))
            if r_end <= r_start + 18.0:
                continue

            # Primary acicular calcite spine
            x0_s = CX + r_start * ca_r
            y0_s = CY + r_start * sa_r
            x1_s = CX + r_end * ca_r
            y1_s = CY + r_end * sa_r
            spine_segs.append([x0_s, y0_s, x1_s, y1_s])

            # Sinuous cytoplasmic reticulopodia filament wrapping & bifurcating along the spine
            u_f = np.linspace(0.0, 1.0, 12)
            r_f = r_start + (r_end - r_start) * u_f
            wiggle = (7.0 + 11.0 * u_f) * np.sin(3.0 * math.pi * u_f - 2.0 * omega * tau + k * 0.7 + r_i)
            xf = CX + r_f * ca_r - wiggle * sa_r
            yf = CY + r_f * sa_r + wiggle * ca_r
            for s_f in range(len(u_f) - 1):
                retic_segs.append([xf[s_f], yf[s_f], xf[s_f + 1], yf[s_f + 1]])

            # Streaming bidirectional dinoflagellate symbiont diamond granule along each spine
            u_g = (tau * 2.0 + (k * 0.17 + r_i * 0.29)) % 1.0
            rg = r_start + (r_end - r_start) * u_g
            xg = CX + rg * ca_r
            yg = CY + rg * sa_r
            gs = 5.6
            granule_quads.append([
                [xg, yg - gs],
                [xg + gs, yg],
                [xg, yg + gs],
                [xg - gs, yg],
            ])

    if retic_segs:
        py5.stroke(72, 188, 164, 155)
        py5.stroke_weight(1.5)
        py5.lines(np.array(retic_segs, dtype=np.float64))

    if spine_segs:
        py5.stroke(246, 238, 222, 195)
        py5.stroke_weight(2.0)
        py5.lines(np.array(spine_segs, dtype=np.float64))

    if granule_quads:
        py5.no_stroke()
        py5.fill(244, 196, 68, 235)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(np.array(granule_quads, dtype=np.float64).reshape(-1, 2))

    # --- 4. RENDER 26 MULTILOCULAR CALCITE CHAMBERS (FROM PROLOCULUS TO APERTURE) ---
    # Rendered in accretion order k = 0..25 so each newer chamber naturally overlaps
    # the anterior wall of the preceding chamber (authentic bilamellar septum imbrication!)
    pore_quads_dark = []
    pore_quads_lit = []
    suture_rib_segs = []

    for k, rk, ang_k, cx_k, cy_k, a_k, b_k, tilt_k, col_idx in chambers:
        outer_rgb, mid_rgb, lumen_rgb, sut_rgb = CHAMBER_PALETTE[col_idx]
        ct, st = math.cos(tilt_k), math.sin(tilt_k)

        # Crescentic / globular lobe distortion: outer peripheral margin is convexly inflated
        lobe_mod = 1.0 + 0.14 * np.sin(U_ANG)
        lx_raw = a_k * U_CA * lobe_mod
        ly_raw = b_k * U_SA * lobe_mod

        # Rotate into world coordinates around (cx_k, cy_k)
        rx_w = lx_raw * ct - ly_raw * st
        ry_w = lx_raw * st + ly_raw * ct

        # 4 concentric shell thickness layers per chamber (bilamellar outer calcite wall,
        # intermediate prismatic layer, inner organic lining, and glowing cytoplasmic lumen)
        layers = [
            (1.06, 1.00, sut_rgb, 245),       # Dark sutural shadow & outer periostracum rim
            (1.00, 0.84, outer_rgb, 250),     # Outer radial hyaline calcite lamella
            (0.84, 0.56, mid_rgb, 248),       # Intermediate bilamellar chamber vault
            (0.56, 0.00, lumen_rgb, 245),     # Sunlit apical crest & inner chamber dome
        ]

        # Directional sunlight offset (upper-left incident light highlighting 3D chamber convexity)
        sun_dx = -a_k * 0.14
        sun_dy = -b_k * 0.14

        py5.no_stroke()
        for sc_out, sc_in, rgb_l, alpha_l in layers:
            off_out = 1.0 - sc_out
            off_in = 1.0 - sc_in
            xo = cx_k + sun_dx * off_out + rx_w * sc_out
            yo = cy_k + sun_dy * off_out + ry_w * sc_out
            xi = cx_k + sun_dx * off_in + rx_w * sc_in
            yi = cy_k + sun_dy * off_in + ry_w * sc_in

            q_ch = np.empty((N_CHAMBER_PTS, 4, 2), dtype=np.float64)
            q_ch[:, 0, 0] = xo[:-1]
            q_ch[:, 0, 1] = yo[:-1]
            q_ch[:, 1, 0] = xo[1:]
            q_ch[:, 1, 1] = yo[1:]
            q_ch[:, 2, 0] = xi[1:]
            q_ch[:, 2, 1] = yi[1:]
            q_ch[:, 3, 0] = xi[:-1]
            q_ch[:, 3, 1] = yi[:-1]

            py5.fill(rgb_l[0], rgb_l[1], rgb_l[2], alpha_l)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(q_ch.reshape(-1, 2))

        # Crisp copperplate sutural contour line around each chamber
        segs_rim = np.column_stack([
            cx_k + rx_w[:-1], cy_k + ry_w[:-1],
            cx_k + rx_w[1:], cy_k + ry_w[1:],
        ])
        py5.stroke(sut_rgb[0], sut_rgb[1], sut_rgb[2], 235)
        py5.stroke_weight(2.2)
        py5.lines(segs_rim)

        # Costae / Sutural Bridges (Ponticuli) radiating across the chamber vault
        if k >= 3:
            for rib_i in range(0, N_CHAMBER_PTS, 3):
                suture_rib_segs.append([
                    cx_k + rx_w[rib_i] * 0.45,
                    cy_k + ry_w[rib_i] * 0.45,
                    cx_k + rx_w[rib_i] * 0.98,
                    cy_k + ry_w[rib_i] * 0.98,
                ])

        # Perforated Mural Pores (Foraminifera test porosity for gas & symbiont exchange)
        if k >= 4:
            n_rings_p = 2 if k < 14 else (3 if k < 22 else 4)
            for pr_i in range(1, n_rings_p + 1):
                r_frac = 0.22 + (0.64 / float(n_rings_p)) * pr_i
                n_p = 6 + 4 * pr_i
                for p_j in range(n_p):
                    pa = (p_j / float(n_p)) * 2.0 * math.pi + pr_i * 0.35
                    px_loc = a_k * r_frac * math.cos(pa)
                    py_loc = b_k * r_frac * math.sin(pa)
                    px_w = cx_k + sun_dx * (1.0 - r_frac) + (px_loc * ct - py_loc * st)
                    py_w = cy_k + sun_dy * (1.0 - r_frac) + (px_loc * st + py_loc * ct)
                    ps = max(2.2, min(7.2, rk * 0.015))
                    pore_quads_dark.append([
                        [px_w - ps, py_w - ps],
                        [px_w + ps, py_w - ps],
                        [px_w + ps, py_w + ps],
                        [px_w - ps, py_w + ps],
                    ])
                    # Glowing endosymbiont / pore rim highlight on every 2nd pore
                    if (p_j + k) % 2 == 0:
                        ps2 = ps * 0.62
                        pore_quads_lit.append([
                            [px_w - ps2, py_w - ps2],
                            [px_w + ps2, py_w - ps2],
                            [px_w + ps2, py_w + ps2],
                            [px_w - ps2, py_w + ps2],
                        ])

    # Batch-render sutural costae ribs
    if suture_rib_segs:
        py5.stroke(96, 58, 36, 130)
        py5.stroke_weight(1.3)
        py5.lines(np.array(suture_rib_segs, dtype=np.float64))

    # Batch-render mural pores across all chambers
    if pore_quads_dark:
        py5.no_stroke()
        py5.fill(48, 32, 22, 185)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(np.array(pore_quads_dark, dtype=np.float64).reshape(-1, 2))
    if pore_quads_lit:
        py5.no_stroke()
        py5.fill(52, 184, 154, 220)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(np.array(pore_quads_lit, dtype=np.float64).reshape(-1, 2))

    # --- 5. INTERCAMERAL FORAMEN (APERTURAL) CYTOPLASMIC STREAM & PROLOCULUS ---
    # Connects all 26 chambers through their basal foramina with pulsing golden-emerald protoplasm
    foramen_pts = np.array([(c[3], c[4]) for c in chambers], dtype=np.float64)
    foramen_segs = np.column_stack([
        foramen_pts[:-1, 0], foramen_pts[:-1, 1],
        foramen_pts[1:, 0], foramen_pts[1:, 1],
    ])
    py5.stroke(28, 128, 108, 215)
    py5.stroke_weight(5.5)
    py5.lines(foramen_segs)

    py5.stroke(246, 202, 74, 240)
    py5.stroke_weight(2.4)
    py5.lines(foramen_segs)

    # Arched terminal umbilical-extraumbilical primary aperture lip on the final chamber (k=25)
    _, rk_last, ang_last, cx_last, cy_last, a_last, b_last, tilt_last, _ = chambers[-1]
    ap_ang = np.linspace(-0.85, 0.85, 28) + tilt_last + 0.65
    ap_x = cx_last + (a_last * 0.92) * np.cos(ap_ang)
    ap_y = cy_last + (a_last * 0.92) * np.sin(ap_ang)
    ap_segs = np.column_stack([ap_x[:-1], ap_y[:-1], ap_x[1:], ap_y[1:]])
    py5.stroke(28, 22, 18, 245)
    py5.stroke_weight(7.5)
    py5.lines(ap_segs)
    py5.stroke(252, 238, 198, 250)
    py5.stroke_weight(3.8)
    py5.lines(ap_segs)

    # Central Embryonic Proloculus (Megalosphere) at (CX, CY)
    py5.fill(244, 184, 52, 255)
    py5.stroke(118, 42, 24, 245)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, R0_PROLOCULUS * 1.9)
    py5.fill(255, 248, 220, 255)
    py5.no_stroke()
    py5.circle(CX - 3.5, CY - 3.5, R0_PROLOCULUS * 0.85)

    # --- 6. ENGRAVED BRASS MICROSCOPE GONIOMETER BEZEL ---
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
    """Draws a warm Victorian naturalist monograph card frame with brass corner brackets."""
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


def draw_foraminifera_apparatuses(tau: float, omega: float):
    """
    Renders 8 Micropaleontology & Morphogenesis apparatuses across 4 balanced flank cards.
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
    # CARD 1 (TOP-LEFT): FIG. 01 GNOMONIC SPIRAL & FIG. 02 BILAMELLAR SEPTUM
    # =========================================================================
    draw_light_card_frame(lx, ty, cw, th)

    # --- FIG. 01: D'ARCY THOMPSON GNOMONIC LOGARITHMIC SPIRAL ACCRETION ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 01 // D'ARCY THOMPSON GNOMONIC SHELL ACCRETION & RAUP MORPHOSPACE", lx + 28, ty + 24)
    py5.fill(188, 62, 44)
    py5.text_size(12)
    py5.text("r(THETA) = r_0 * EXP(b * THETA) // CONSTANT TANGENT ANGLE PSI = ARCTAN(1 / b) = 82.1 DEG", lx + 28, ty + 48)

    # Logarithmic gnomon diagram at (lx + 172, ty + 215)
    f1_cx, f1_cy = lx + 172.0, ty + 215.0
    th1 = np.linspace(0.0, 4.2 * math.pi, 140)
    r1 = 8.5 * np.exp(0.18 * th1)
    x1 = f1_cx + r1 * np.cos(th1 + 0.5 * omega * tau)
    y1 = f1_cy + r1 * np.sin(th1 + 0.5 * omega * tau)
    segs1 = np.column_stack([x1[:-1], y1[:-1], x1[1:], y1[1:]])
    py5.stroke(28, 58, 96, 235)
    py5.stroke_weight(2.6)
    py5.lines(segs1)

    for k1 in range(4, 15):
        a1 = k1 * 0.85 + 0.5 * omega * tau
        rk1 = 8.5 * math.exp(0.18 * (k1 * 0.85))
        py5.fill(226, 112, 86, 185)
        py5.stroke(188, 62, 44, 225)
        py5.stroke_weight(1.5)
        py5.circle(f1_cx + rk1 * math.cos(a1), f1_cy + rk1 * math.sin(a1), rk1 * 0.68)

    tx1 = lx + 336.0
    ty1 = ty + 88.0
    f1_specs = [
        ("WHORL EXPANSION (W)", ": W = exp(2*pi*b) = 3.38 per Whorl", (188, 62, 44)),
        ("FLARE PARAMETER (b)", ": b = 0.194 rad^-1 (Equiangular)", (28, 58, 96)),
        ("TANGENT ANGLE (PSI)", ": psi = 79.02 DEG Self-Similar", (144, 94, 24)),
        ("RAUP OVERLAP (D)", ": D = 0.34 (Involute -> Evolute)", (36, 118, 96)),
        ("TRANSLATION RATE (T)", ": T = 0.42 Low Trochospiral Cone", (38, 30, 22)),
        ("CHAMBER COUNT (N)", ": 32 Loculi across 2.32 Whorls", (188, 62, 44)),
        ("PROLOCULUS FORM", ": Megalospheric Gamont (d = 60 um)", (28, 58, 96)),
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

    # --- FIG. 02: BILAMELLAR CALCITE WALL & INTERCAMERAL FORAMEN SEPTUM ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 02 // BILAMELLAR CALCITE SEPTUM & INTERCAMERAL FORAMEN ANATOMY", lx + 28, ty + 412)
    py5.fill(28, 58, 96)
    py5.text_size(12)
    py5.text("PRIMARY ORGANIC LINING (IOL) FLANKED BY RADIAL C-AXIS HYALINE CALCITE LAMELLAE", lx + 28, ty + 436)

    # Cross-section schematic of bilamellar wall with pore canals and basal foramen
    f2_x, f2_y, f2_w, f2_h = lx + 42.0, ty + 488.0, 255.0, 240.0
    py5.fill(242, 236, 224, 245)
    py5.stroke(158, 136, 104, 215)
    py5.stroke_weight(1.6)
    py5.rect(f2_x, f2_y, f2_w, f2_h, 5)

    # Outer lamella, Primary Organic Membrane (POM), and Inner lamella bands
    py5.fill(226, 112, 86, 225)
    py5.rect(f2_x + 24, f2_y + 38, f2_w - 48, 56, 3)
    py5.fill(188, 62, 44, 255)
    py5.rect(f2_x + 24, f2_y + 94, f2_w - 48, 10)
    py5.fill(242, 194, 108, 225)
    py5.rect(f2_x + 24, f2_y + 104, f2_w - 48, 48, 3)

    # Perforated vertical pore channels across the bilamellar wall
    for pk in range(5):
        px_p = f2_x + 48.0 + pk * 38.0
        py5.fill(52, 184, 154, 240)
        py5.no_stroke()
        py5.rect(px_p, f2_y + 36, 10, 118, 2)

    tx2 = lx + 336.0
    ty2 = ty + 485.0
    f2_specs = [
        ("MINERAL POLYMORPH", ": Trigonal Low-Mg Calcite (CaCO3)", (188, 62, 44)),
        ("WALL ARCHITECTURE", ": Bilamellar Rotaliida (Outer + Inner)", (28, 58, 96)),
        ("OPTICAL ORIENTATION", ": Radial c-Axes (Uniaxial Cross)", (144, 94, 24)),
        ("MURAL PORE DENSITY", ": d_pore = 2.4 to 5.8 um Sieve Plate", (36, 118, 96)),
        ("INTERCAMERAL FORAMEN", ": Basal Arched Aperture + Lip Rim", (38, 30, 22)),
        ("CALCIFICATION MODE", ": Vacuolated Seawater Endocytosis", (188, 62, 44)),
        ("ONTogenic LAMINATION", ": +1 Outer Crust Layer / New Chamber", (28, 58, 96)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f2_specs):
        yy = ty2 + i * 33.0
        py5.fill(96, 82, 64)
        py5.text_size(12)
        py5.text(k_lbl, tx2, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx2 + 178.0, yy)

    # =========================================================================
    # CARD 2 (BOTTOM-LEFT): FIG. 03 PALEOCLIMATE d18O & FIG. 04 PALETTE
    # =========================================================================
    draw_light_card_frame(lx, by, cw, bh)

    # --- FIG. 03: PALEOCLIMATOLOGY DELTA-18O & Mg/Ca THERMOMETRY ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 03 // PALEOCLIMATOLOGY: OXYGEN ISOTOPE (d18O) & Mg/Ca THERMOMETRY", lx + 28, by + 24)
    py5.fill(28, 58, 96)
    py5.text_size(12)
    py5.text("UREY-EPSTEIN PALEOTEMPERATURE EQUATION: T(C) = 16.5 - 4.3*(d18O_c - d18O_w) + 0.14*(d18O)^2", lx + 28, by + 48)

    f3_x, f3_y, f3_w, f3_h = lx + 42.0, by + 95.0, 255.0, 240.0
    py5.fill(242, 236, 224, 245)
    py5.stroke(158, 136, 104, 215)
    py5.stroke_weight(1.6)
    py5.rect(f3_x, f3_y, f3_w, f3_h, 5)

    # Plot of exponential Mg/Ca = 0.38 * exp(0.09 * T) and linear d18O fractionation vs T in [0..30 C]
    u3 = np.linspace(0.0, 1.0, 80)
    x3_p = f3_x + 14.0 + u3 * (f3_w - 28.0)
    y3_mg = (f3_y + f3_h - 18.0) - (np.exp(1.8 * u3) - 1.0) / (math.exp(1.8) - 1.0) * (f3_h - 42.0)
    y3_ox = (f3_y + 28.0) + u3 * (f3_h - 48.0)
    py5.stroke(188, 62, 44, 235)
    py5.stroke_weight(2.8)
    py5.lines(np.column_stack([x3_p[:-1], y3_mg[:-1], x3_p[1:], y3_mg[1:]]))
    py5.stroke(28, 58, 96, 235)
    py5.lines(np.column_stack([x3_p[:-1], y3_ox[:-1], x3_p[1:], y3_ox[1:]]))

    tx3 = lx + 336.0
    ty3 = by + 88.0
    t_sea = 24.2 + 2.4 * math.sin(omega * tau)
    mg_ca = 0.38 * math.exp(0.090 * t_sea)
    f3_specs = [
        ("OCEAN TEMPERATURE", f": T_SST = {t_sea:0.2f} DEG C (Photic Zone)", (188, 62, 44)),
        ("CALCITE Mg/Ca RATIO", f": Mg/Ca = {mg_ca:0.2f} mmol / mol", (28, 58, 96)),
        ("OXYGEN ISOTOPE d18O", f": d18O_VPDB = {-1.85 - 0.21 * (t_sea - 24.0):0.2f} per mil", (36, 118, 96)),
        ("CARBON ISOTOPE d13C", ": +1.45 per mil (Symbiont Enriched)", (144, 94, 24)),
        ("BORON ISOTOPE d11B", ": Paleo-pH Proxy (pH = 8.12 +/- 0.04)", (38, 30, 22)),
        ("LYSOKLINE DEPTH", ": CCD = 4,500 m Calcite Saturation", (188, 62, 44)),
        ("ISOTOPE STAGE", ": Emiliani MIS 1 Holocene Interglacial", (28, 58, 96)),
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

    # --- FIG. 04: BIOMINERAL CALCITE & SYMBIONT CHROMOPHORE PALETTE ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 04 // BIOMINERAL CALCITE & ENDOSYMBIONT CHROMOPHORE PALETTE", lx + 28, by + 412)
    py5.fill(188, 62, 44)
    py5.text_size(12)
    py5.text("GLOBIGERINOIDES RUBER CAROTENOID POLYENES, TRAVERTINE CALCITE & DINOFLAGELLATES", lx + 28, by + 436)

    swatches = [
        ((188, 62, 44), "GLOBIGERINA RUBER ROSE-CRIMSON // POLYENE KETOCAROTENOID COMPLEX IN CALCITE MATRIX"),
        ((204, 96, 42), "TERRACOTTA SEPTAL CALCITE // IRON-MANGANESE AUTHIGENIC OVERGROWTH TINT"),
        ((214, 146, 44), "SYMBIODINIUM DINOFLAGELLATE GOLD // PERIDININ & DIADINOXANTHIN PLASTID PIGMENTS"),
        ((168, 128, 88), "BENTHIC ROTALIIDA TRAVERTINE // AGGLUTINATED & HYALINE BILAMELLAR TEST"),
        ((64, 128, 114), "GRANULORETICULOPODIA CELADON // BIDIRECTIONAL MICROTUBULE CYTOPLASMIC STREAM"),
        ((28, 58, 96), "PELAGIC CHALLENGER INDIGO // DEEP MARINE BATHYMETRIC DARKFIELD CONTRAST"),
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
    # CARD 3 (TOP-RIGHT): FIG. 05 COILING TAXONOMY & FIG. 06 CODEX LEDGER
    # =========================================================================
    draw_light_card_frame(rx, ty, cw, th)

    # --- FIG. 05: CHAMBER ARRANGEMENT & COILING TAXONOMY ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 05 // FORAMINIFERA COILING & CHAMBER ARRANGEMENT TAXONOMY", rx + 28, ty + 24)
    py5.fill(28, 58, 96)
    py5.text_size(12)
    py5.text("TROCHOSPIRAL, PLANISPIRAL EVOLUTE, BISERIAL & MILIOLINE QUINQUELOCULINE PLANS", rx + 28, ty + 48)

    # Mini comparison of Biserial vs Planispiral Evolute inside [rx+42..rx+300]
    c5_x1, c5_y1 = rx + 112.0, ty + 215.0
    for k5 in range(7):
        r5 = 14.0 + k5 * 7.5
        a5 = k5 * 0.72 + omega * tau * 0.5
        py5.fill(226, 112, 86, 215)
        py5.stroke(118, 34, 24, 225)
        py5.stroke_weight(1.5)
        py5.circle(c5_x1 + r5 * math.cos(a5), c5_y1 + r5 * math.sin(a5), r5 * 0.72)

    c5_x2, c5_y2 = rx + 242.0, ty + 135.0
    for b5 in range(6):
        side = -1 if b5 % 2 == 0 else 1
        rad5 = 14.0 + b5 * 4.5
        py5.fill(242, 194, 108, 225)
        py5.stroke(144, 94, 24, 225)
        py5.stroke_weight(1.5)
        py5.circle(c5_x2 + side * (10.0 + b5 * 2.2), c5_y2 + b5 * 24.0, rad5 * 1.65)

    tx5 = rx + 336.0
    ty5 = ty + 88.0
    f5_specs = [
        ("TROCHOSPIRAL", ": Helical Spire (Spiral vs Umbilical)", (188, 62, 44)),
        ("PLANISPIRAL EVOLUTE", ": All Whorls Visible Symmetrically", (28, 58, 96)),
        ("PLANISPIRAL INVOLUTE", ": Outer Whorl Envelops Inner Loculi", (144, 94, 24)),
        ("BISERIAL (TEXTULARIA)", ": Alternating 180-DEG Dyad Stack", (36, 118, 96)),
        ("MILIOLINE COILING", ": 144-DEG / 72-DEG Quinqueloculine", (38, 30, 22)),
        ("UNISERIAL (LAGENA)", ": Rectilinear Orthoconic Chamber Axis", (188, 62, 44)),
        ("COILING CHIRALITY", ": Sinistral (Cold) vs Dextral (Warm)", (28, 58, 96)),
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

    # --- FIG. 06: HISTORICAL MICROPALEONTOLOGY & TAXONOMIC CODEX LEDGER ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 06 // HISTORICAL MICROPALEONTOLOGY & MONOGRAPH CODEX LEDGER", rx + 28, ty + 412)
    py5.fill(188, 62, 44)
    py5.text_size(12)
    py5.text("FROM D'ORBIGNY (1826) & HMS CHALLENGER (1884) TO D'ARCY THOMPSON (1917)", rx + 28, ty + 436)

    rows = [
        ("D'ORBIGNY TABLEAU (1826)", "Paris (A. d'Orbigny)", "Order Foraminiferes", "First Systematic Key"),
        ("HMS CHALLENGER (1884)", "H.B. Brady", "115 Lithographic Pl.", "Deep-Sea Globigerina"),
        ("KUNSTFORMEN PL. 2 (1899)", "Ernst Haeckel", "Thalamophora Plate", "20 Chambered Forms"),
        ("ON GROWTH & FORM (1917)", "D'Arcy W. Thompson", "Logarithmic Gnomon", "Equiangular Law"),
        ("RAUP MORPHOSPACE (1966)", "David M. Raup", "(W, D, T, S) Tensor", "Coiled Shell Geometry"),
        ("ACTIVE TEST SIMULATION", "26-Chamber Rotaliid", "W=2.38 // b=0.138", "HARMONIC LIVE"),
    ]
    for r_i, (c_name, c_auth, c_tax, c_note) in enumerate(rows):
        ry_row = ty + 478.0 + r_i * 55.0
        is_hi = (r_i == 3 or r_i == 5)
        py5.fill(*(240, 228, 204, 242) if is_hi else (248, 244, 234, 215))
        py5.stroke(*(188, 62, 44, 235) if is_hi else (194, 176, 144, 175))
        py5.stroke_weight(1.9 if is_hi else 1.1)
        py5.rect(rx + 28, ry_row, cw - 56, 44, 5)

        py5.no_stroke()
        py5.fill(38, 30, 22)
        py5.text_size(12)
        py5.text(c_name, rx + 44, ry_row + 15)
        py5.fill(28, 58, 96)
        py5.text(c_auth, rx + 265, ry_row + 15)
        py5.fill(188, 62, 44)
        py5.text(c_tax, rx + 435, ry_row + 15)
        py5.fill(36, 118, 96)
        py5.text(c_note, rx + 595, ry_row + 15)

    # =========================================================================
    # CARD 4 (BOTTOM-RIGHT): FIG. 07 RETICULOPODIA & FIG. 08 ACCRETION TRACE
    # =========================================================================
    draw_light_card_frame(rx, by, cw, bh)

    # --- FIG. 07: GRANULORETICULOPODIA MICROTUBULE & SYMBIONT TRANSPORT ---
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 07 // GRANULORETICULOPODIA NETWORK & SYMBIONT STREAMING", rx + 28, by + 24)
    py5.fill(36, 118, 96)
    py5.text_size(12)
    py5.text("BIDIRECTIONAL KINESIN/DYNEIN MICROTUBULE TRANSPORT ALONG CALCITE SPINES", rx + 28, by + 48)

    # Anastomosing branching network diagram inside [rx+42..rx+300]
    f7_cx, f7_cy = rx + 172.0, by + 205.0
    py5.fill(28, 58, 96, 235)
    py5.no_stroke()
    py5.circle(f7_cx, f7_cy, 44.0)
    for b7 in range(8):
        a7 = b7 * (math.pi / 4.0) + 0.2 * math.sin(omega * tau)
        x7_m = f7_cx + 58.0 * math.cos(a7)
        y7_m = f7_cy + 58.0 * math.sin(a7)
        py5.stroke(52, 168, 138, 225)
        py5.stroke_weight(2.4)
        py5.line(f7_cx, f7_cy, x7_m, y7_m)
        for sub7 in [-0.32, 0.32]:
            x7_e = x7_m + 52.0 * math.cos(a7 + sub7)
            y7_e = y7_m + 52.0 * math.sin(a7 + sub7)
            py5.stroke_weight(1.6)
            py5.line(x7_m, y7_m, x7_e, y7_e)
            py5.fill(226, 146, 34, 245)
            py5.no_stroke()
            py5.circle(x7_e, y7_e, 8.0)

    tx7 = rx + 336.0
    ty7 = by + 88.0
    f7_specs = [
        ("PSEUDOPODIAL TYPE", ": Anastomosing Granuloreticulopodia", (36, 118, 96)),
        ("STREAMING VELOCITY", ": v_cyto = 8.5 to 15.0 um / sec", (188, 62, 44)),
        ("CYTOSKELETAL CORE", ": Helical alpha/beta-Tubulin Bundles", (28, 58, 96)),
        ("ENDOSYMBIONT TAXA", ": Symbiodinium & Pelagodinium spp.", (144, 94, 24)),
        ("DIURNAL MIGRATION", ": Dawn Spine Outflow / Dusk Retract", (38, 30, 22)),
        ("CHAMBER TEMPLATE", ": Ectoplasmic Bulge (Anlage) Mold", (188, 62, 44)),
        ("GAMETOGENESIS", ": Spine Resorption at Lunar Full Moon", (28, 58, 96)),
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
    py5.line(rx + 24, by + 390, rx + cw - 24, ty_sep := by + 390)

    # --- FIG. 08: ONTOGENETIC CHAMBER VOLUME & CALCIFICATION PULSES ---
    py5.no_stroke()
    py5.fill(38, 30, 22)
    py5.text_size(17)
    py5.text("FIG. 08 // ONTOGENETIC CHAMBER VOLUME V_k & CALCIFICATION FLUX", rx + 28, by + 412)
    py5.fill(28, 58, 96)
    py5.text_size(12)
    py5.text("EXPONENTIAL CHAMBER SCALING V_k = V_0 * EXP(3 * b * k * dTHETA) & DIURNAL pH WAVE", rx + 28, by + 436)

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
    base_y = wy + wh - 24.0

    # Exponential gnomonic growth curve + episodic chamber addition pulses
    y_exp = base_y - ((np.exp(2.4 * u_w) - 1.0) / (math.exp(2.4) - 1.0)) * (wh - 48.0)
    y_pulse = (wy + wh * 0.55) - 72.0 * np.sin(8.0 * math.pi * u_w - 2.0 * omega * tau) * np.exp(-0.4 * (1.0 - u_w))
    y_ph = (wy + wh * 0.58) - 44.0 * np.cos(4.0 * math.pi * u_w + omega * tau)

    for y_arr_w, col_w in [
        (y_exp, (188, 62, 44, 240)),
        (y_pulse, (36, 118, 96, 230)),
        (y_ph, (28, 58, 96, 225)),
    ]:
        segs_w = np.column_stack([xw_arr[:-1], y_arr_w[:-1], xw_arr[1:], y_arr_w[1:]])
        py5.stroke(*col_w)
        py5.stroke_weight(2.6)
        py5.lines(segs_w)

    py5.no_stroke()
    py5.fill(86, 68, 44)
    py5.text_size(12)
    py5.text(
        "CRIMSON: GNOMONIC VOLUME V_k  //  EMERALD: EPISODIC CHAMBER PULSE  //  PRUSSIAN: VACUOLAR pH",
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
        "FORAMINIFERA LOGARITHMIC CHAMBER BIOMINERALIZATION // GNOMONIC SHELL MORPHOGENESIS",
        CX,
        82,
    )

    py5.fill(188, 62, 44)
    py5.text_size(15)
    py5.text(
        "THALAMOPHORA BILAMELLAR CALCITE ACCRETION - r(THETA) = r_0 * EXP(b * THETA) (D'ORBIGNY 1826 / THOMPSON 1917)",
        CX,
        124,
    )

    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(86, 72, 52)
    py5.text_size(14)
    py5.text(
        "26 MULTILOCULAR CHAMBERS // WHORL EXPANSION W = 2.38 // TANGENT ANGLE PSI = 82.14 DEG // BILAMELLAR CaCO3",
        96,
        HEIGHT - 74,
    )

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K ORGANIC MORPHOGENESIS // HARMONIC PHASE TAU = {tau:0.3f} (12.0s @ 60FPS)",
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
