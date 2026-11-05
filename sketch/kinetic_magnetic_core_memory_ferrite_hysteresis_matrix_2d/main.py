"""
Kinetic Magnetic Core Memory & Ferrite Hysteresis Matrix 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Signal / Glitch / Digital Artifacts genre,
exploring 1950s-1960s Coincident-Current Magnetic Core Memory (Jay Forrester, MIT
Whirlwind I 1951; An Wang; MIT Instrumentation Lab Apollo Guidance Computer Block II,
1966), executed on deep ferrite backplane obsidian (#060912).

Each binary bit is stored as the remanent magnetic flux polarity (+B_r clockwise vs.
-B_r counterclockwise) inside a 3D-canted sintered manganese-magnesium spinel ferrite
toroid. A 4-wire coordinate matrix (X-Select horizontal copper enamel wire, Y-Select
vertical magnet wire, 45-degree serpentine noise-canceling Sense wire, and Z-Inhibit
wire) weaves over and under 177 canted toroidal cores inside a gold-plated circular
backplane aperture. Only the core at the intersection of active half-select currents
(I_X = +I_m/2, I_Y = +I_m/2 -> I_total = I_m > I_c) overcomes the square ferromagnetic
B-H hysteresis coercivity threshold H_c, flipping its magnetic domain and inducing a
Faraday EMF voltage pulse V_sense = -d(Phi)/dt on the serpentine sense line during the
Destructive Readout (DRO) and Restore cycle.

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
WORK_NAME = "kinetic_magnetic_core_memory_ferrite_hysteresis_matrix_2d"
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
RND_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_WORD_SEED = int(np.random.randint(0, 65535))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 22.0
APERTURE_R = 805.0

# Core matrix grid inside circular aperture: 15 x 15 grid (-7..+7)
GRID_N = 15
GRID_HALF = GRID_N // 2
PITCH = 88.0
MAX_CORE_R = 655.0

# Precompute active core positions inside the circular memory plane
CORES = []
CORE_MAP = {}
for gy in range(-GRID_HALF, GRID_HALF + 1):
    for gx in range(-GRID_HALF, GRID_HALF + 1):
        px = CX + gx * PITCH
        py = CY + gy * PITCH
        dist = math.hypot(gx * PITCH, gy * PITCH)
        if dist <= MAX_CORE_R:
            # Alternating +/- 45 deg cant angle of hand-woven ferrite toroids
            cant_sign = 1 if ((gx + gy) % 2 == 0) else -1
            idx = len(CORES)
            CORES.append((idx, gx, gy, px, py, cant_sign, dist))
            CORE_MAP[(gx, gy)] = idx

# Precompute continuous serpentine diagonal sense wire path through the cores
SERPENTINE_SENSE_PTS = []
for d_diag in range(-2 * GRID_HALF, 2 * GRID_HALF + 1):
    diag_cores = []
    for gx in range(-GRID_HALF, GRID_HALF + 1):
        gy = gx - d_diag
        if (gx, gy) in CORE_MAP:
            c_idx = CORE_MAP[(gx, gy)]
            _, _, _, c_px, c_py, _, _ = CORES[c_idx]
            diag_cores.append((c_px, c_py))
    if diag_cores:
        if d_diag % 2 != 0:
            diag_cores.reverse()
        SERPENTINE_SENSE_PTS.extend(diag_cores)

SERPENTINE_SENSE_ARR = np.array(SERPENTINE_SENSE_PTS, dtype=np.float64)
SERPENTINE_SENSE_SEGS = np.column_stack([
    SERPENTINE_SENSE_ARR[:-1, 0],
    SERPENTINE_SENSE_ARR[:-1, 1],
    SERPENTINE_SENSE_ARR[1:, 0],
    SERPENTINE_SENSE_ARR[1:, 1],
])

# Precompute 3D-canted elliptical toroid quad meshes for cant_sign = +1 and -1
N_TOR_SEG = 28
TOR_ANG = np.linspace(0.0, 2.0 * math.pi, N_TOR_SEG + 1)
TOR_CA = np.cos(TOR_ANG)
TOR_SA = np.sin(TOR_ANG)


def build_unit_canted_torus(cant_sign: int, a_out: float, b_out: float, a_in: float, b_in: float):
    """
    Precomputes the 2D projected vertices of a 3D canted toroidal ring (top beveled
    face + 3D side-wall thickness skirt) tilted along theta_c = cant_sign * pi / 4.
    """
    theta_c = cant_sign * (0.25 * math.pi)
    cc, sc = math.cos(theta_c), math.sin(theta_c)

    # Local ellipse points (u, v) rotated by theta_c
    xo_raw, yo_raw = a_out * TOR_CA, b_out * TOR_SA
    xi_raw, yi_raw = a_in * TOR_CA, b_in * TOR_SA

    xo = xo_raw * cc - yo_raw * sc
    yo = xo_raw * sc + yo_raw * cc
    xi = xi_raw * cc - yi_raw * sc
    yi = xi_raw * sc + yi_raw * cc

    # 3D axial thickness offset vector (perpendicular to cant axis)
    dx_3d = 6.0 * (-sc * cant_sign)
    dy_3d = 6.0 * (cc * cant_sign) + 4.5

    # Outer skirt quads (extruded by dx_3d, dy_3d)
    skirt_quads = np.empty((N_TOR_SEG, 4, 2), dtype=np.float64)
    skirt_quads[:, 0, 0] = xo[:-1]
    skirt_quads[:, 0, 1] = yo[:-1]
    skirt_quads[:, 1, 0] = xo[1:]
    skirt_quads[:, 1, 1] = yo[1:]
    skirt_quads[:, 2, 0] = xo[1:] + dx_3d
    skirt_quads[:, 2, 1] = yo[1:] + dy_3d
    skirt_quads[:, 3, 0] = xo[:-1] + dx_3d
    skirt_quads[:, 3, 1] = yo[:-1] + dy_3d

    # Inner bore wall quads (extruded by dx_3d * 0.75, dy_3d * 0.75)
    bore_quads = np.empty((N_TOR_SEG, 4, 2), dtype=np.float64)
    bore_quads[:, 0, 0] = xi[:-1]
    bore_quads[:, 0, 1] = yi[:-1]
    bore_quads[:, 1, 0] = xi[1:]
    bore_quads[:, 1, 1] = yi[1:]
    bore_quads[:, 2, 0] = xi[1:] + dx_3d * 0.72
    bore_quads[:, 2, 1] = yi[1:] + dy_3d * 0.72
    bore_quads[:, 3, 0] = xi[:-1] + dx_3d * 0.72
    bore_quads[:, 3, 1] = yi[:-1] + dy_3d * 0.72

    # Top ceramic face quads (split into lit upper-left half and shaded lower-right half)
    face_quads = np.empty((N_TOR_SEG, 4, 2), dtype=np.float64)
    face_quads[:, 0, 0] = xi[:-1]
    face_quads[:, 0, 1] = yi[:-1]
    face_quads[:, 1, 0] = xo[:-1]
    face_quads[:, 1, 1] = yo[:-1]
    face_quads[:, 2, 0] = xo[1:]
    face_quads[:, 2, 1] = yo[1:]
    face_quads[:, 3, 0] = xi[1:]
    face_quads[:, 3, 1] = yi[1:]

    # Mid-wall flux track ring quads
    af0, bf0 = 0.5 * (a_in + a_out) - 2.6, 0.5 * (b_in + b_out) - 2.0
    af1, bf1 = 0.5 * (a_in + a_out) + 2.6, 0.5 * (b_in + b_out) + 2.0
    xf0 = (af0 * TOR_CA) * cc - (bf0 * TOR_SA) * sc
    yf0 = (af0 * TOR_CA) * sc + (bf0 * TOR_SA) * cc
    xf1 = (af1 * TOR_CA) * cc - (bf1 * TOR_SA) * sc
    yf1 = (af1 * TOR_CA) * sc + (bf1 * TOR_SA) * cc

    flux_quads = np.empty((N_TOR_SEG, 4, 2), dtype=np.float64)
    flux_quads[:, 0, 0] = xf0[:-1]
    flux_quads[:, 0, 1] = yf0[:-1]
    flux_quads[:, 1, 0] = xf1[:-1]
    flux_quads[:, 1, 1] = yf1[:-1]
    flux_quads[:, 2, 0] = xf1[1:]
    flux_quads[:, 2, 1] = yf1[1:]
    flux_quads[:, 3, 0] = xf0[1:]
    flux_quads[:, 3, 1] = yf0[1:]

    return skirt_quads, bore_quads, face_quads, flux_quads


TORUS_GEOM = {
    1: build_unit_canted_torus(1, 35.5, 25.5, 15.5, 11.0),
    -1: build_unit_canted_torus(-1, 35.5, 25.5, 15.5, 11.0),
}

# Precompute deterministic sequence of 24 coincident-current (gx, gy) read-write addresses
ADDRESS_SEQ = [
    (0, 0), (3, -2), (-4, 2), (2, 4), (-3, -3), (5, -1),
    (-2, 5), (4, 3), (-5, -2), (1, -5), (-4, 4), (3, 1),
    (-1, -3), (5, 2), (-3, 4), (2, -4), (-5, 1), (4, -3),
    (0, 5), (-4, -1), (3, 4), (-2, -5), (4, 0), (-3, 2),
]

AGC_OPCODES = [
    ("01 // TC (TRANSFER CONTROL)", "OCT 04521 // BANK 02"),
    ("02 // CCS (COUNT, COMPARE, SKIP)", "OCT 12304 // ERASABLE E3"),
    ("03 // INDEX (NEXT INSTRUCTION)", "OCT 50017 // FIXED F14"),
    ("04 // CA (CLEAR AND ADD)", "OCT 31402 // ACCUMULATOR A"),
    ("05 // CS (CLEAR AND SUBTRACT)", "OCT 44110 // L-REGISTER"),
    ("06 // AD (ADD TO ACCUMULATOR)", "OCT 62075 // DSKY VERB 16"),
    ("07 // XCH (EXCHANGE A AND K)", "OCT 55712 // P63 LANDING"),
    ("08 // TS (TRANSFER TO STORAGE)", "OCT 54201 // KALMAN STATE"),
]


def compute_core_bit_state(gx: int, gy: int, tau: float):
    """
    Computes the continuous magnetization state M in [-1, +1] of core (gx, gy) at phase tau.
    M = +1 corresponds to +B_r (Logic '1', clockwise amber-gold flux),
    M = -1 corresponds to -B_r (Logic '0', counterclockwise cyan-cobalt flux).
    """
    omega = 2.0 * math.pi
    wave = (
        math.sin(0.55 * gx - 0.45 * gy + omega * tau + RND_PHASE)
        + 0.65 * math.cos(0.40 * (gx * gx + gy * gy) ** 0.5 - 2.0 * omega * tau)
        + 0.35 * math.sin(0.75 * (gx + gy) - omega * tau)
    )
    return math.tanh(2.4 * wave)


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

    n_steps = len(ADDRESS_SEQ)
    step_f = tau * n_steps
    step_idx = int(step_f) % n_steps
    sub_tau = step_f - int(step_f)
    sel_gx, sel_gy = ADDRESS_SEQ[step_idx]
    sel2_gx, sel2_gy = ADDRESS_SEQ[(step_idx + 7) % n_steps]

    # 1. Deep Ferrite Backplane Obsidian Substrate (#060912)
    py5.background(6, 9, 18)

    # 2. Backplane Electromagnetic Glow & Coordinate Grid
    draw_backplane_substrate(tau)

    # 3. Central Circular Woven Ferrite Core Memory Plane & Coincident-Current Wavefronts
    draw_central_core_memory_plane(tau, omega, sel_gx, sel_gy, sel2_gx, sel2_gy, sub_tau)

    # 4. Eight Ferromagnetic Physics & Early Computing Apparatuses Across Four Flank Cards
    draw_ferrite_apparatuses(tau, omega, sel_gx, sel_gy, sub_tau, step_idx)

    # 5. Archival Museum Border & Scholarly Typography (Zero Personal Signatures/Seals)
    draw_archival_border_and_typography(tau, sel_gx, sel_gy)

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


def draw_backplane_substrate(tau: float):
    """Draws the dark obsidian PCB substrate, subtle radial EM glow, and coordinate grid."""
    py5.no_stroke()
    for r_g, col_g in [
        (1150, (12, 22, 44, 28)),
        (880, (18, 34, 64, 34)),
        (680, (24, 42, 76, 38)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    py5.stroke(22, 36, 62, 115)
    py5.stroke_weight(1.2)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)


def draw_central_core_memory_plane(
    tau: float,
    omega: float,
    sel_gx: int,
    sel_gy: int,
    sel2_gx: int,
    sel2_gy: int,
    sub_tau: float,
):
    """
    Renders the circular ferrite core memory plane with 177 3D-canted toroidal cores,
    single serpentine diagonal sense wire, Z-inhibit return bus, X/Y half-select
    copper magnet wires, and coincident-current Barkhausen domain switching.
    """
    # Outer circular phenolic PCB frame & recessed dark cavity
    py5.no_stroke()
    py5.fill(7, 11, 22, 252)
    py5.circle(CX, CY, (APERTURE_R + 18.0) * 2.0)

    # Subtle internal PCB fiberglass weave grid inside the aperture
    r_clip = APERTURE_R - 48.0
    py5.stroke(16, 28, 48, 140)
    py5.stroke_weight(1.0)
    for g_k in range(-16, 17):
        off_k = g_k * 44.0
        if abs(off_k) < r_clip:
            sp_k = math.sqrt(r_clip * r_clip - off_k * off_k)
            py5.line(CX - sp_k, CY + off_k, CX + sp_k, CY + off_k)
            py5.line(CX + off_k, CY - sp_k, CX + off_k, CY + sp_k)

    # Gold-plated perimeter bus bezel
    py5.no_fill()
    py5.stroke(196, 148, 54, 240)
    py5.stroke_weight(4.8)
    py5.circle(CX, CY, APERTURE_R * 2.0)
    py5.stroke(88, 142, 210, 165)
    py5.stroke_weight(2.0)
    py5.circle(CX, CY, (APERTURE_R - 44.0) * 2.0)

    # 60 Gold-plated PCB edge-connector solder fingers around perimeter ring
    n_tabs = 60
    tab_quads = np.empty((n_tabs, 4, 2), dtype=np.float64)
    r_t0 = APERTURE_R - 38.0
    r_t1 = APERTURE_R - 7.0
    for k in range(n_tabs):
        ang = k * (2.0 * math.pi / n_tabs)
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa * 5.8, ca * 5.8
        x0, y0 = CX + r_t0 * ca, CY + r_t0 * sa
        x1, y1 = CX + r_t1 * ca, CY + r_t1 * sa
        tab_quads[k, 0] = (x0 - nx, y0 - ny)
        tab_quads[k, 1] = (x1 - nx, y1 - ny)
        tab_quads[k, 2] = (x1 + nx, y1 + ny)
        tab_quads[k, 3] = (x0 + nx, y0 + ny)

    py5.fill(224, 178, 68, 235)
    py5.stroke(48, 34, 14, 225)
    py5.stroke_weight(1.2)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(tab_quads.reshape(-1, 2))

    # --- Layer 1: Z-Inhibit Return Bus & Continuous Serpentine 45-Deg Sense Wire ---
    inhibit_segs = []
    for gy in range(-GRID_HALF, GRID_HALF + 1):
        yy = gy * PITCH - 13.0
        if abs(yy) < r_clip:
            half_span = math.sqrt(max(0.0, r_clip * r_clip - yy * yy))
            inhibit_segs.append([CX - half_span, CY + yy, CX + half_span, CY + yy])
    inhibit_arr = np.array(inhibit_segs, dtype=np.float64)
    py5.stroke(156, 98, 236, 150)
    py5.stroke_weight(2.6)
    py5.lines(inhibit_arr)

    # Single continuous serpentine diagonal Sense Wire (emerald magnet wire)
    sense_pulse = math.exp(-18.0 * (sub_tau - 0.32) ** 2) + math.exp(-18.0 * (sub_tau - 0.74) ** 2)
    py5.stroke(16, 185, 129, 110)
    py5.stroke_weight(5.5)
    py5.lines(SERPENTINE_SENSE_SEGS)
    py5.stroke(110, 231, 183, int(185 + 65 * min(1.0, sense_pulse)))
    py5.stroke_weight(2.5)
    py5.lines(SERPENTINE_SENSE_SEGS)

    # --- Layer 2: Horizontal X-Select & Vertical Y-Select Magnet Wires (Under-Pass) ---
    for g_idx in range(-GRID_HALF, GRID_HALF + 1):
        coord_off = g_idx * PITCH
        half_span = math.sqrt(max(0.0, r_clip * r_clip - coord_off * coord_off))

        # Horizontal row (X-Select copper enamel wire)
        y_line = CY + coord_off
        is_sel_y = (g_idx == sel_gy)
        is_sel2_y = (g_idx == sel2_gy)
        if is_sel_y:
            py5.stroke(245, 158, 11, 115)
            py5.stroke_weight(14.0)
            py5.line(CX - half_span, y_line, CX + half_span, y_line)
            py5.stroke(254, 240, 138, 255)
            py5.stroke_weight(4.8)
            py5.line(CX - half_span, y_line, CX + half_span, y_line)
        elif is_sel2_y:
            py5.stroke(245, 158, 11, 225)
            py5.stroke_weight(3.8)
            py5.line(CX - half_span, y_line, CX + half_span, y_line)
        else:
            py5.stroke(146, 78, 28, 215)
            py5.stroke_weight(4.6)
            py5.line(CX - half_span, y_line, CX + half_span, y_line)
            py5.stroke(234, 148, 68, 195)
            py5.stroke_weight(1.9)
            py5.line(CX - half_span, y_line, CX + half_span, y_line)

        # Vertical column (Y-Select polyurethane magnet wire)
        x_line = CX + coord_off
        is_sel_x = (g_idx == sel_gx)
        is_sel2_x = (g_idx == sel2_gx)
        if is_sel_x:
            py5.stroke(56, 189, 248, 115)
            py5.stroke_weight(14.0)
            py5.line(x_line, CY - half_span, x_line, CY + half_span)
            py5.stroke(186, 230, 253, 255)
            py5.stroke_weight(4.8)
            py5.line(x_line, CY - half_span, x_line, CY + half_span)
        elif is_sel2_x:
            py5.stroke(56, 189, 248, 225)
            py5.stroke_weight(3.8)
            py5.line(x_line, CY - half_span, x_line, CY + half_span)
        else:
            py5.stroke(28, 84, 158, 215)
            py5.stroke_weight(4.6)
            py5.line(x_line, CY - half_span, x_line, CY + half_span)
            py5.stroke(88, 178, 248, 195)
            py5.stroke_weight(1.9)
            py5.line(x_line, CY - half_span, x_line, CY + half_span)

    # --- Layer 3: Vectorized 3D-Canted Sintered Ferrite Toroidal Cores ---
    all_skirts = []
    all_bores = []
    face_std = []
    face_half = []
    face_coinc = []
    flux_amber = []
    flux_cyan = []
    flux_coinc = []

    over_x_dark = []
    over_x_spec = []
    over_y_dark = []
    over_y_spec = []
    over_sense_segs = []

    for (idx, gx, gy, px, py, cant_sign, dist) in CORES:
        m_val = compute_core_bit_state(gx, gy, tau)
        is_coincident = (gx == sel_gx and gy == sel_gy) or (gx == sel2_gx and gy == sel2_gy)
        is_half_select = (gx == sel_gx or gy == sel_gy or gx == sel2_gx or gy == sel2_gy) and not is_coincident

        skirt_q, bore_q, face_q, flux_q = TORUS_GEOM[cant_sign]
        offset = np.array([px, py], dtype=np.float64)

        all_skirts.append(skirt_q + offset)
        all_bores.append(bore_q + offset)

        if is_coincident:
            face_coinc.append(face_q + offset)
            flux_coinc.append(flux_q + offset)
        elif is_half_select:
            face_half.append(face_q + offset)
            if m_val >= 0.0:
                flux_amber.append(flux_q + offset)
            else:
                flux_cyan.append(flux_q + offset)
        else:
            face_std.append(face_q + offset)
            if m_val >= 0.0:
                flux_amber.append(flux_q + offset)
            else:
                flux_cyan.append(flux_q + offset)

        # Over-passing wire bridges emerging from the central elliptical bore and wrapping over one rim
        if cant_sign > 0:
            over_x_dark.append([px - 31.0, py, px + 8.0, py])
            over_x_spec.append([px - 31.0, py, px + 8.0, py])
            over_y_dark.append([px, py - 8.0, px, py + 31.0])
            over_y_spec.append([px, py - 8.0, px, py + 31.0])
            over_sense_segs.append([px - 19.0, py - 19.0, px + 19.0, py + 19.0])
        else:
            over_x_dark.append([px - 8.0, py, px + 31.0, py])
            over_x_spec.append([px - 8.0, py, px + 31.0, py])
            over_y_dark.append([px, py - 31.0, px, py + 8.0])
            over_y_spec.append([px, py - 31.0, px, py + 8.0])
            over_sense_segs.append([px - 19.0, py + 19.0, px + 19.0, py - 19.0])

    # 3A: Render 3D outer side-wall skirts and inner bore walls
    py5.stroke(10, 14, 24, 210)
    py5.stroke_weight(0.9)
    py5.fill(16, 22, 36, 248)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.vstack(all_skirts).reshape(-1, 2))

    py5.fill(12, 16, 28, 250)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.vstack(all_bores).reshape(-1, 2))

    # 3B: Render top sintered ceramic faces of the 177 canted ferrite toroids
    py5.stroke(64, 82, 112, 185)
    py5.stroke_weight(1.0)
    if face_std:
        py5.fill(32, 42, 62, 248)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(np.vstack(face_std).reshape(-1, 2))

    if face_half:
        py5.stroke(122, 158, 206, 210)
        py5.fill(46, 62, 92, 252)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(np.vstack(face_half).reshape(-1, 2))

    if face_coinc:
        py5.stroke(244, 114, 182, 245)
        py5.fill(88, 32, 76, 255)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(np.vstack(face_coinc).reshape(-1, 2))

    # 3C: Render the remanent magnetic flux loops (+B_r Amber vs. -B_r Cyan vs. Coincident Flip)
    py5.no_stroke()
    if flux_amber:
        py5.fill(245, 168, 24, 242)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(np.vstack(flux_amber).reshape(-1, 2))

    if flux_cyan:
        py5.fill(46, 186, 248, 242)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(np.vstack(flux_cyan).reshape(-1, 2))

    if flux_coinc:
        py5.fill(254, 240, 138, 255)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(np.vstack(flux_coinc).reshape(-1, 2))

    # 3D: Render over-passing wire bridges across the canted toroid rims
    ox_arr = np.array(over_x_dark, dtype=np.float64)
    oy_arr = np.array(over_y_dark, dtype=np.float64)
    os_arr = np.array(over_sense_segs, dtype=np.float64)

    py5.stroke(146, 78, 28, 245)
    py5.stroke_weight(5.2)
    py5.lines(ox_arr)
    py5.stroke(251, 182, 72, 245)
    py5.stroke_weight(2.2)
    py5.lines(ox_arr)

    py5.stroke(28, 84, 158, 245)
    py5.stroke_weight(5.2)
    py5.lines(oy_arr)
    py5.stroke(112, 198, 254, 245)
    py5.stroke_weight(2.2)
    py5.lines(oy_arr)

    py5.stroke(16, 185, 129, 235)
    py5.stroke_weight(4.4)
    py5.lines(os_arr)
    py5.stroke(167, 243, 208, 245)
    py5.stroke_weight(1.8)
    py5.lines(os_arr)

    # --- Layer 4: Coincident-Current Domain Flip Shockwave & Reticle Brackets ---
    for c_gx, c_gy, col_ring in [
        (sel_gx, sel_gy, (244, 114, 182)),
        (sel2_gx, sel2_gy, (251, 191, 36)),
    ]:
        if (c_gx, c_gy) in CORE_MAP:
            c_px = CX + c_gx * PITCH
            c_py = CY + c_gy * PITCH
            r_wave = 32.0 + 72.0 * sub_tau
            a_wave = int(245 * (1.0 - sub_tau))
            py5.no_fill()
            py5.stroke(col_ring[0], col_ring[1], col_ring[2], a_wave)
            py5.stroke_weight(3.6)
            py5.circle(c_px, c_py, r_wave * 2.0)

            b_r = 39.0
            py5.stroke(254, 240, 138, 245)
            py5.stroke_weight(2.5)
            py5.line(c_px - b_r, c_py - b_r, c_px - b_r + 13, c_py - b_r)
            py5.line(c_px - b_r, c_py - b_r, c_px - b_r, c_py - b_r + 13)
            py5.line(c_px + b_r, c_py - b_r, c_px + b_r - 13, c_py - b_r)
            py5.line(c_px + b_r, c_py - b_r, c_px + b_r, c_py - b_r + 13)
            py5.line(c_px - b_r, c_py + b_r, c_px - b_r + 13, c_py + b_r)
            py5.line(c_px - b_r, c_py + b_r, c_px - b_r, c_py + b_r - 13)
            py5.line(c_px + b_r, c_py + b_r, c_px + b_r - 13, c_py + b_r)
            py5.line(c_px + b_r, c_py + b_r, c_px + b_r, c_py + b_r - 13)


def draw_dark_card_frame(x: float, y: float, w: float, h: float):
    """Draws an obsidian & gold-copper instrumentation panel card."""
    py5.no_stroke()
    py5.fill(2, 4, 10, 165)
    py5.rect(x + 6, y + 8, w, h, 8)

    py5.fill(10, 16, 30, 238)
    py5.stroke(56, 98, 156, 205)
    py5.stroke_weight(2.0)
    py5.rect(x, y, w, h, 8)

    py5.no_fill()
    py5.stroke(188, 142, 52, 115)
    py5.stroke_weight(1.1)
    py5.rect(x + 8, y + 8, w - 16, h - 16, 5)


def draw_ferrite_apparatuses(
    tau: float,
    omega: float,
    sel_gx: int,
    sel_gy: int,
    sub_tau: float,
    step_idx: int,
):
    """
    Renders 8 scholarly ferromagnetic physics & early computing apparatuses
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
    # CARD 1 (TOP-LEFT): FIG. 01 4-WIRE TOROID MAGNIFICATION & FIG. 02 B-H LOOP
    # =========================================================================
    draw_dark_card_frame(lx, ty, cw, th)
    py5.text_align(py5.LEFT, py5.TOP)

    # --- FIG. 01: SINGLE TOROIDAL FERRITE CORE 4-WIRE INTERSECTION ---
    py5.fill(236, 244, 255)
    py5.text_size(17)
    py5.text("FIG. 01 // 4-WIRE FERRITE TOROID COINCIDENT-CURRENT INTERSECTION", lx + 28, ty + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("X-DRIVE (+I_m/2), Y-DRIVE (+I_m/2), 45-DEG SENSE & Z-INHIBIT THREADING", lx + 28, ty + 48)

    f1_cx = lx + 175.0
    f1_cy = ty + 215.0

    # Under-wires entering the magnified ferrite toroid
    py5.stroke(245, 158, 11, 240)
    py5.stroke_weight(5.5)
    py5.line(f1_cx - 115.0, f1_cy, f1_cx + 115.0, f1_cy)

    py5.stroke(56, 189, 248, 240)
    py5.stroke_weight(5.5)
    py5.line(f1_cx, f1_cy - 115.0, f1_cx, f1_cy + 115.0)

    py5.stroke(168, 85, 247, 220)
    py5.stroke_weight(3.8)
    py5.line(f1_cx - 110.0, f1_cy - 22.0, f1_cx + 110.0, f1_cy - 22.0)

    py5.stroke(52, 211, 153, 240)
    py5.stroke_weight(4.2)
    py5.line(f1_cx - 92.0, f1_cy - 92.0, f1_cx + 92.0, f1_cy + 92.0)

    # Magnified 3D Ferrite Toroid ring (outer R = 82, inner R = 42)
    n_seg = 72
    ang = np.linspace(0.0, 2.0 * math.pi, n_seg + 1)
    ca, sa = np.cos(ang), np.sin(ang)
    tor_quads = np.empty((n_seg, 4, 2), dtype=np.float64)
    tor_quads[:, 0, 0] = f1_cx + 42.0 * ca[:-1]
    tor_quads[:, 0, 1] = f1_cy + 42.0 * sa[:-1]
    tor_quads[:, 1, 0] = f1_cx + 82.0 * ca[:-1]
    tor_quads[:, 1, 1] = f1_cy + 82.0 * sa[:-1]
    tor_quads[:, 2, 0] = f1_cx + 82.0 * ca[1:]
    tor_quads[:, 2, 1] = f1_cy + 82.0 * sa[1:]
    tor_quads[:, 3, 0] = f1_cx + 42.0 * ca[1:]
    tor_quads[:, 3, 1] = f1_cy + 42.0 * sa[1:]

    py5.fill(28, 36, 54, 245)
    py5.no_stroke()
    with py5.begin_shape(py5.QUADS):
        py5.vertices(tor_quads.reshape(-1, 2))

    py5.no_fill()
    py5.stroke(148, 178, 218, 235)
    py5.stroke_weight(2.4)
    py5.circle(f1_cx, f1_cy, 164.0)
    py5.circle(f1_cx, f1_cy, 84.0)

    # Circulating magnetic flux quanta along the toroidal core wall
    py5.stroke(251, 191, 36, 220)
    py5.stroke_weight(2.2)
    py5.circle(f1_cx, f1_cy, 124.0)
    py5.no_stroke()
    py5.fill(254, 240, 138, 250)
    for k_f in range(8):
        af = k_f * (math.pi / 4.0) + 2.0 * omega * tau
        py5.circle(f1_cx + 62.0 * math.cos(af), f1_cy + 62.0 * math.sin(af), 7.5)

    # Over-passing half of the 4 wires through the central aperture
    py5.stroke(245, 158, 11, 255)
    py5.stroke_weight(5.5)
    py5.line(f1_cx - 25.0, f1_cy, f1_cx + 95.0, f1_cy)
    py5.stroke(56, 189, 248, 255)
    py5.stroke_weight(5.5)
    py5.line(f1_cx, f1_cy - 95.0, f1_cx, f1_cy + 25.0)

    tx1 = lx + 340.0
    ty1 = ty + 88.0
    f1_specs = [
        ("FERRITE COMPOSITION", ": Mn-Mg Spinel Ceramic (0.8 mm OD)", (226, 236, 248)),
        ("X-SELECT DRIVE LINE", ": +I_m / 2 = 320 mA Half-Select", (251, 191, 36)),
        ("Y-SELECT DRIVE LINE", ": +I_m / 2 = 320 mA Half-Select", (56, 189, 248)),
        ("COINCIDENT SUM (I_X+I_Y)", ": 640 mA > I_c (480 mA Coercive)", (244, 114, 182)),
        ("SENSE WIRE (DIAGONAL)", ": V_sense = -d(Phi)/dt (~45 mV)", (52, 211, 153)),
        ("Z-INHIBIT LINE", ": -320 mA Opposition (Write '0')", (192, 132, 252)),
        ("SWITCHING TIME (t_s)", ": 1.15 Microseconds (Domain Flip)", (226, 236, 248)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f1_specs):
        yy = ty1 + i * 33.0
        py5.fill(148, 168, 196)
        py5.text_size(12)
        py5.text(k_lbl, tx1, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx1 + 178.0, yy)

    py5.stroke(42, 68, 108, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, ty + 390, lx + cw - 24, ty + 390)

    # --- FIG. 02: SQUARE FERROMAGNETIC B-H HYSTERESIS LOOP ---
    py5.no_stroke()
    py5.fill(236, 244, 255)
    py5.text_size(17)
    py5.text("FIG. 02 // SQUARE FERROMAGNETIC B-H HYSTERESIS LOOP", lx + 28, ty + 412)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("BISTABLE REMANENCE (+/- B_r) & COERCIVE THRESHOLD DISCRIMINATION (+/- H_c)", lx + 28, ty + 436)

    f2_cx = lx + 175.0
    f2_cy = ty + 625.0
    py5.stroke(72, 98, 136, 190)
    py5.stroke_weight(1.6)
    py5.line(f2_cx - 115.0, f2_cy, f2_cx + 115.0, f2_cy)
    py5.line(f2_cx, f2_cy - 110.0, f2_cx, f2_cy + 110.0)

    h_vals = np.linspace(-100.0, 100.0, 120)
    b_up = 78.0 * np.tanh((h_vals + 48.0) / 14.0)
    b_dn = 78.0 * np.tanh((h_vals - 48.0) / 14.0)
    segs_up = np.column_stack([
        f2_cx + h_vals[:-1], f2_cy - b_up[:-1],
        f2_cx + h_vals[1:], f2_cy - b_up[1:],
    ])
    segs_dn = np.column_stack([
        f2_cx + h_vals[:-1], f2_cy - b_dn[:-1],
        f2_cx + h_vals[1:], f2_cy - b_dn[1:],
    ])
    py5.stroke(251, 191, 36, 235)
    py5.stroke_weight(2.8)
    py5.lines(segs_up)
    py5.stroke(56, 189, 248, 235)
    py5.stroke_weight(2.8)
    py5.lines(segs_dn)

    h_cur = 85.0 * math.sin(omega * tau)
    dh_cur = math.cos(omega * tau)
    b_cur = 78.0 * np.tanh((h_cur - (48.0 if dh_cur > 0 else -48.0)) / 14.0)
    py5.fill(244, 114, 182, 255)
    py5.no_stroke()
    py5.circle(f2_cx + h_cur, f2_cy - b_cur, 12.0)

    tx2 = lx + 340.0
    ty2 = ty + 485.0
    f2_specs = [
        ("UPPER REMANENCE (+B_r)", ": +2,200 Gauss -> LOGIC BIT '1'", (251, 191, 36)),
        ("LOWER REMANENCE (-B_r)", ": -2,200 Gauss -> LOGIC BIT '0'", (56, 189, 248)),
        ("COERCIVE FIELD (H_c)", ": 1.45 Oersteds (Switching Knee)", (244, 114, 182)),
        ("SQUARENESS RATIO", ": B_r / B_max = 0.94 (High Squareness)", (52, 211, 153)),
        ("HALF-SELECT FIELD", ": H_m / 2 = 0.95 Oe < H_c (Stable)", (226, 236, 248)),
        ("FULL-SELECT FIELD", ": H_m = 1.90 Oe > H_c (Domain Flip)", (244, 114, 182)),
        ("CURIE TEMPERATURE", ": T_C = 585 K (Thermal Limit)", (192, 132, 252)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f2_specs):
        yy = ty2 + i * 33.0
        py5.fill(148, 168, 196)
        py5.text_size(12)
        py5.text(k_lbl, tx2, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx2 + 178.0, yy)

    # =========================================================================
    # CARD 2 (BOTTOM-LEFT): FIG. 03 DIAGONAL SENSE WEAVE & FIG. 04 PALETTE
    # =========================================================================
    draw_dark_card_frame(lx, by, cw, bh)

    # --- FIG. 03: DIAGONAL CHECKERBOARD SENSE-WIRE NOISE CANCELLATION ---
    py5.fill(236, 244, 255)
    py5.text_size(17)
    py5.text("FIG. 03 // CHECKERBOARD SENSE-WIRE DELTA-NOISE CANCELLATION", lx + 28, by + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("BOW-TIE DIAGONAL THREADING CANCELING HALF-SELECT DISTURBANCE SPIKES", lx + 28, by + 48)

    f3_cx = lx + 175.0
    f3_cy = by + 215.0
    pts_s3 = []
    for r3 in range(-1, 3):
        for c3 in range(-1, 3):
            kx = f3_cx + (c3 - 0.5) * 52.0
            ky = f3_cy + (r3 - 0.5) * 52.0
            pol = 1 if ((r3 + c3) % 2 == 0) else -1
            py5.no_fill()
            py5.stroke(*(251, 191, 36, 225) if pol > 0 else (56, 189, 248, 225))
            py5.stroke_weight(3.2)
            py5.circle(kx, ky, 26.0)
            pts_s3.append((kx, ky))

    py5.stroke(52, 211, 153, 235)
    py5.stroke_weight(2.4)
    for k_i in range(len(pts_s3) - 1):
        py5.line(pts_s3[k_i][0], pts_s3[k_i][1], pts_s3[k_i + 1][0], pts_s3[k_i + 1][1])

    tx3 = lx + 340.0
    ty3 = by + 88.0
    f3_specs = [
        ("ACTIVE ADDRESS (X, Y)", f": X = {sel_gx:+02d}, Y = {sel_gy:+02d} (Coincident)", (244, 114, 182)),
        ("HALF-SELECTED CORES", ": 28 Disturbed Cores Along Row/Col", (251, 191, 36)),
        ("CHECKERBOARD POLARITY", ": +d(Phi)/dt + (-d(Phi)/dt) = 0.0 mV", (52, 211, 153)),
        ("COMMON-MODE REJECTION", ": > 42 dB Differential Sense Amp", (56, 189, 248)),
        ("SIGNAL-TO-NOISE RATIO", ": 18.5 : 1 Strobe Window Peak", (226, 236, 248)),
        ("STROBE SAMPLE WINDOW", ": t = 0.55 us (Peak dPhi/dt)", (192, 132, 252)),
        ("INVENTOR PATENT", ": Jay W. Forrester (MIT, 1951)", (226, 236, 248)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f3_specs):
        yy = ty3 + i * 33.0
        py5.fill(148, 168, 196)
        py5.text_size(12)
        py5.text(k_lbl, tx3, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx3 + 178.0, yy)

    py5.stroke(42, 68, 108, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, by + 390, lx + cw - 24, by + 390)

    # --- FIG. 04: SINTERED FERRITE & MAGNET WIRE ENAMEL PALETTE ---
    py5.no_stroke()
    py5.fill(236, 244, 255)
    py5.text_size(17)
    py5.text("FIG. 04 // MAGNETIC CORE & ENAMEL WIRE STRATIGRAPHY PALETTE", lx + 28, by + 412)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("REMANENT FLUX POLARITIES, FORMVAR COPPER GLAZES & BARKHAUSEN EMISSION", lx + 28, by + 436)

    swatches = [
        ((251, 191, 36), "CLOCKWISE REMANENCE (+B_r) // LOGIC '1' TOROIDAL FLUX & X-SELECT BUS"),
        ((56, 189, 248), "COUNTERCLOCKWISE REMANENCE (-B_r) // LOGIC '0' FLUX & Y-SELECT BUS"),
        ((244, 114, 182), "COINCIDENT-CURRENT DOMAIN FLIP (I_X + I_Y > I_c) // BARKHAUSEN PULSE"),
        ((52, 211, 153), "45-DEG DIAGONAL SENSE WIRE // FARADAY INDUCED EMF V = -d(PHI)/dt"),
        ((168, 85, 247), "Z-INHIBIT BUS WIRE // OPPOSING -I_m/2 PULSE DURING '0' REWRITE"),
        ((218, 172, 64), "GOLD-PLATED BACKPLANE TERMINAL FINGERS // PERIMETER DRIVER BUS"),
    ]
    for i, (rgb_s, desc_s) in enumerate(swatches):
        sy = by + 482.0 + i * 54.0
        py5.fill(*rgb_s)
        py5.stroke(148, 178, 218, 210)
        py5.stroke_weight(1.5)
        py5.rect(lx + 32, sy, 52, 34, 4)
        py5.no_stroke()
        py5.fill(226, 236, 248)
        py5.text_size(13)
        py5.text(desc_s, lx + 104, sy + 9)

    # =========================================================================
    # CARD 3 (TOP-RIGHT): FIG. 05 AGC 16-BIT WORD REGISTER & FIG. 06 LEDGER
    # =========================================================================
    draw_dark_card_frame(rx, ty, cw, th)

    # --- FIG. 05: APOLLO GUIDANCE COMPUTER (AGC BLOCK II) 16-BIT WORD REGISTER ---
    py5.fill(236, 244, 255)
    py5.text_size(17)
    py5.text("FIG. 05 // APOLLO GUIDANCE COMPUTER (AGC BLOCK II) 16-BIT WORD", rx + 28, ty + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("15-BIT ONES'-COMPLEMENT INSTRUCTION WORD + 1 ODD PARITY BIT SENSE READOUT", rx + 28, ty + 48)

    word_val = ((step_idx + 1) * 2654435761 ^ RND_WORD_SEED) & 0xFFFF
    for b_i in range(16):
        bit_on = ((word_val >> (15 - b_i)) & 1) == 1
        row_b = b_i // 8
        col_b = b_i % 8
        bx_c = rx + 36.0 + col_b * 86.0
        by_c = ty + 88.0 + row_b * 76.0
        py5.fill(*(48, 36, 14, 240) if bit_on else (14, 28, 48, 240))
        py5.stroke(*(251, 191, 36, 245) if bit_on else (56, 189, 248, 215))
        py5.stroke_weight(2.0)
        py5.rect(bx_c, by_c, 74.0, 60.0, 6)

        py5.no_fill()
        py5.circle(bx_c + 24.0, by_c + 30.0, 24.0)
        py5.no_stroke()
        py5.fill(*(254, 240, 138) if bit_on else (125, 211, 252))
        py5.text_size(15)
        py5.text("1" if bit_on else "0", bx_c + 48.0, by_c + 22.0)

    op_lbl, bank_lbl = AGC_OPCODES[step_idx % len(AGC_OPCODES)]
    py5.fill(148, 168, 196)
    py5.text_size(13)
    py5.text(f"DECODED AGC OPCODE : {op_lbl}", rx + 36, ty + 258)
    py5.fill(52, 211, 153)
    py5.text(f"MEMORY BANK & OCTAL: {bank_lbl}  //  WORD = 0x{word_val:04X}", rx + 36, ty + 286)
    py5.fill(251, 191, 36)
    py5.text("CYCLE PHASE        : DESTRUCTIVE READOUT (t < 0.5) -> INHIBIT REWRITE (t >= 0.5)", rx + 36, ty + 314)
    py5.fill(244, 114, 182)
    py5.text("PARITY CHECK       : ODD PARITY VERIFIED (SENSE AMPLIFIER STROBE OK)", rx + 36, ty + 342)

    py5.stroke(42, 68, 108, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, ty + 390, rx + cw - 24, ty + 390)

    # --- FIG. 06: HISTORICAL FERRITE CORE MEMORY ARCHITECTURE LEDGER ---
    py5.no_stroke()
    py5.fill(236, 244, 255)
    py5.text_size(17)
    py5.text("FIG. 06 // HISTORICAL MAGNETIC CORE MEMORY ARCHITECTURE LEDGER", rx + 28, ty + 412)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("EVOLUTION OF COINCIDENT-CURRENT & CORE ROPE MEMORY SYSTEMS (1953-1969)", rx + 28, ty + 436)

    rows = [
        ("MIT WHIRLWIND I (1953)", "32x32x16 Planes", "2.0 mm OD", "8.0 us Cycle"),
        ("IBM 704 / 737 (1955)", "4,096 x 36-Bit", "1.8 mm OD", "12.0 us Cycle"),
        ("DEC PDP-8 (1965)", "4,096 x 12-Bit", "0.8 mm OD", "1.5 us Cycle"),
        ("AGC BLOCK II ERASABLE", "2,048 x 16-Bit", "0.75 mm OD", "11.7 us Cycle"),
        ("AGC BLOCK II CORE ROPE", "36,864 x 16-Bit", "Permalloy", "Read-Only ROM"),
        ("CDC 6600 SUPER (1964)", "131,072 x 60-Bit", "0.5 mm OD", "1.0 us Cycle"),
    ]
    for r_i, (c_sys, c_cap, c_od, c_cyc) in enumerate(rows):
        ry_row = ty + 478.0 + r_i * 55.0
        is_hi = (r_i == 3)
        py5.fill(*(24, 42, 74, 240) if is_hi else (14, 22, 40, 215))
        py5.stroke(*(251, 191, 36, 240) if is_hi else (46, 72, 114, 175))
        py5.stroke_weight(1.9 if is_hi else 1.1)
        py5.rect(rx + 28, ry_row, cw - 56, 44, 5)

        py5.no_stroke()
        py5.fill(236, 244, 255)
        py5.text_size(12)
        py5.text(c_sys, rx + 44, ry_row + 15)
        py5.fill(56, 189, 248)
        py5.text(c_cap, rx + 285, ry_row + 15)
        py5.fill(251, 191, 36)
        py5.text(c_od, rx + 465, ry_row + 15)
        py5.fill(52, 211, 153)
        py5.text(c_cyc, rx + 595, ry_row + 15)

    # =========================================================================
    # CARD 4 (BOTTOM-RIGHT): FIG. 07 CORE ROPE ROM & FIG. 08 DRO WAVEFORM
    # =========================================================================
    draw_dark_card_frame(rx, by, cw, bh)

    # --- FIG. 07: CORE ROPE READ-ONLY MEMORY ("LOL MEMORY") WEAVE TOPOLOGY ---
    py5.fill(236, 244, 255)
    py5.text_size(17)
    py5.text("FIG. 07 // APOLLO CORE ROPE ROM TRANSFORMER WEAVE TOPOLOGY", rx + 28, by + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("HIGH-DENSITY READ-ONLY MEMORY: SENSE WIRE THREADS CORE ('1') OR BYPASSES ('0')", rx + 28, by + 48)

    for c_k in range(3):
        rc_x = rx + 82.0 + c_k * 88.0
        rc_y = by + 215.0
        py5.fill(24, 34, 54, 245)
        py5.stroke(251, 191, 36, 235)
        py5.stroke_weight(3.2)
        py5.circle(rc_x, rc_y, 56.0)
        py5.fill(8, 12, 22, 255)
        py5.circle(rc_x, rc_y, 26.0)

    u_r = np.linspace(0.0, 1.0, 140)
    xr_arr = rx + 42.0 + u_r * 255.0
    for s_idx, (amp_r, freq_r, col_r) in enumerate([
        (36.0, 3.0 * math.pi, (52, 211, 153, 235)),
        (-34.0, 2.0 * math.pi, (56, 189, 248, 235)),
        (24.0, 4.0 * math.pi, (244, 114, 182, 235)),
    ]):
        yr_arr = by + 215.0 + amp_r * np.sin(freq_r * u_r + omega * tau * 0.5)
        segs_r = np.column_stack([xr_arr[:-1], yr_arr[:-1], xr_arr[1:], yr_arr[1:]])
        py5.stroke(*col_r)
        py5.stroke_weight(2.4)
        py5.lines(segs_r)

    tx7 = rx + 340.0
    ty7 = by + 88.0
    f7_specs = [
        ("MEMORY TOPOLOGY", ": Linear Transformer Core Rope ROM", (226, 236, 248)),
        ("STORAGE DENSITY", ": 64 Bits per Single Permalloy Core", (251, 191, 36)),
        ("THREADED CORE", ": Induces Pulse -> Binary '1'", (52, 211, 153)),
        ("BYPASSED CORE", ": Zero Induced EMF -> Binary '0'", (56, 189, 248)),
        ("RADIATION IMMUNITY", ": 100% Immune to Single-Event Upsets", (244, 114, 182)),
        ("FLIGHT SOFTWARE", ": LUMINARY (LM) & COLOSSUS (CSM)", (192, 132, 252)),
        ("SOFTWARE DIRECTOR", ": MIT Instrumentation Laboratory", (226, 236, 248)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f7_specs):
        yy = ty7 + i * 33.0
        py5.fill(148, 168, 196)
        py5.text_size(12)
        py5.text(k_lbl, tx7, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx7 + 178.0, yy)

    py5.stroke(42, 68, 108, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, by + 390, rx + cw - 24, by + 390)

    # --- FIG. 08: DESTRUCTIVE READOUT (DRO) & REWRITE TIMING WAVEFORM ---
    py5.no_stroke()
    py5.fill(236, 244, 255)
    py5.text_size(17)
    py5.text("FIG. 08 // DESTRUCTIVE READOUT (DRO) & REWRITE TIMING OSCILLOSCOPE", rx + 28, by + 412)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("COINCIDENT HALF-SELECT PULSES I_X, I_Y, Z-INHIBIT & FARADAY SENSE SPIKE V_sense(t)", rx + 28, by + 436)

    wx = rx + 36.0
    wy = by + 482.0
    ww = cw - 72.0
    wh = 285.0
    py5.fill(6, 10, 20, 245)
    py5.stroke(56, 98, 156, 200)
    py5.stroke_weight(1.6)
    py5.rect(wx, wy, ww, wh, 6)

    py5.stroke(24, 42, 72, 165)
    py5.stroke_weight(1.1)
    for g_i in range(1, 4):
        gy_w = wy + (wh / 4.0) * g_i
        py5.line(wx, gy_w, wx + ww, gy_w)
    for g_j in range(1, 6):
        gx_w = wx + (ww / 6.0) * g_j
        py5.line(gx_w, wy, gx_w, wy + wh)

    n_w = 200
    t_w = np.linspace(0.0, 1.0, n_w)
    xw_arr = wx + t_w * ww

    read_env = np.exp(-((t_w - 0.28) / 0.09) ** 4)
    write_env = -np.exp(-((t_w - 0.72) / 0.09) ** 4)
    sense_spike = 1.15 * np.exp(-((t_w - 0.26) / 0.035) ** 2) - 0.45 * np.exp(-((t_w - 0.70) / 0.045) ** 2)

    yw_x = (wy + 58.0) - 34.0 * (read_env + write_env)
    yw_y = (wy + 135.0) - 34.0 * (read_env + write_env)
    yw_s = (wy + 222.0) - 48.0 * sense_spike

    for y_arr, col_w in [
        (yw_x, (251, 191, 36, 240)),
        (yw_y, (56, 189, 248, 240)),
        (yw_s, (52, 211, 153, 250)),
    ]:
        segs_w = np.column_stack([xw_arr[:-1], y_arr[:-1], xw_arr[1:], y_arr[1:]])
        py5.stroke(*col_w)
        py5.stroke_weight(2.6)
        py5.lines(segs_w)

    cur_wx = wx + sub_tau * ww
    py5.stroke(244, 114, 182, 235)
    py5.stroke_weight(2.2)
    py5.line(cur_wx, wy, cur_wx, wy + wh)

    py5.no_stroke()
    py5.fill(148, 168, 196)
    py5.text_size(12)
    py5.text(
        "AMBER: I_X DRIVE  //  CYAN: I_Y DRIVE  //  EMERALD: V_SENSE = -d(PHI)/dt  //  ROSE: STROBE GATE",
        wx + 8,
        wy + wh + 18,
    )


def draw_archival_border_and_typography(tau: float, sel_gx: int, sel_gy: int):
    """Draws the outer museum architectural border, title header, and telemetry footer."""
    py5.no_fill()
    py5.stroke(56, 108, 176, 215)
    py5.stroke_weight(3.0)
    py5.rect(52, 48, WIDTH - 104, HEIGHT - 96, 10)

    py5.stroke(188, 142, 52, 140)
    py5.stroke_weight(1.4)
    py5.rect(64, 60, WIDTH - 128, HEIGHT - 120, 6)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(240, 246, 255)
    py5.text_size(30)
    py5.text(
        "COINCIDENT-CURRENT MAGNETIC CORE MEMORY // FERRITE HYSTERESIS MATRIX",
        CX,
        82,
    )

    py5.fill(56, 189, 248)
    py5.text_size(15)
    py5.text(
        "4-WIRE WOVEN TOROIDAL FERRITE PLANE (X-DRIVE, Y-DRIVE, 45-DEG SENSE, Z-INHIBIT) - SQUARE B-H REMANENCE",
        CX,
        124,
    )

    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(148, 168, 196)
    py5.text_size(14)
    py5.text(
        f"ADDRESSED COORDINATE (X={sel_gx:+02d}, Y={sel_gy:+02d}) // COERCIVE THRESHOLD I_X + I_Y > I_c // FARADAY EMF V = -d(PHI)/dt",
        96,
        HEIGHT - 74,
    )

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K FERROMAGNETIC TELEMETRY // MEMORY CYCLE PHASE TAU = {tau:0.3f} (12.0s @ 60FPS)",
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
