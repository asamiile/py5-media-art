"""
Kinetic Kerr Black Hole Ergosphere Frame Dragging 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art exploring Relativistic Astrophysics and General Relativity:
The exact rotating Kerr black hole spacetime formulated by Roy Kerr (1963), featuring:
- Novikov-Thorne relativistic accretion disk with continuous 5-stop Doppler boosting
  (intense electric cyan / diamond white approaching limb vs. radiant gold / amber / crimson receding wing)
- Luminet-Thorne relativistic ray-tracing geometry: majestic upper arch curving over the Kerr shadow,
  lower lensed crescent curving beneath, and front equatorial crossing
- Asymmetric Bardeen / Kerr black hole shadow void with ultra-sharp hairline photon ring
- Neon emerald static limit ergosphere boundary (r_E(th) = M + sqrt(M^2 - a^2 cos^2(th)))
  and infalling Lense-Thirring spacetime frame-dragging vortex inside the ISCO cavity
- Bounded Blandford-Znajek relativistic plasma jets with braided helical magnetic field flux ropes
- Four archival relativistic astrophysics telemetry apparatuses on deep interstellar obsidian (#020409)
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
WORK_NAME = "kinetic_kerr_black_hole_ergosphere_frame_dragging_2d"
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

# Dynamic non-fixed runtime seed offsets
np.random.seed(int(time.time() * 1000) % 100000)
RND_PHASE_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))
RND_DENSITY_SEED = float(np.random.uniform(0.8, 1.2))

# 4K Physical and Spacetime Geometric Parameters
CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 70.0

M = 120.0
A_STAR = 0.940 # Near-extremal Kerr spin parameter
A = A_STAR * M
R_PLUS = M * (1.0 + math.sqrt(max(0.0, 1.0 - A_STAR**2))) # Event horizon ~ 161.0 px
R_SHADOW = 2.65 * M # Gravitational shadow radius ~ 318.0 px
R_ISCO = 2.05 * M   # Innermost Stable Circular Orbit ~ 246.0 px
R_OUT = 11.2 * M    # Outer accretion disk edge ~ 1344.0 px

# Disk inclination angle i = 74 degrees
INC = math.radians(74)
COS_I = math.cos(INC)
SIN_I = math.sin(INC)

# Jet tilt angle along polar axis
JET_TILT = math.radians(11)
COS_J = math.cos(JET_TILT)
SIN_J = math.sin(JET_TILT)

# Mesh density for smooth 4K accretion disk
NUM_RINGS = 100
PTS_PER_ARCH = 240
R_VALS = np.geomspace(R_ISCO, R_OUT, NUM_RINGS)

def settings():
    py5.size(WIDTH, HEIGHT)
    py5.smooth(8)

def setup():
    global START_TIME
    START_TIME = time.time()
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized 4K render pipeline: {TOTAL_FRAMES} frames @ {FPS} fps.")

def get_spline_color_and_alpha(x_pos, r_val, t_r, v_orb, matter_phase):
    alpha_norm = x_pos / r_val # in [-1, 1]

    # Relativistic line-of-sight velocity projection
    v_parallel = -v_orb * alpha_norm * SIN_I
    gamma = 1.0 / math.sqrt(max(0.04, 1.0 - v_orb**2))
    delta = 1.0 / (gamma * max(0.12, (1.0 - v_parallel * 0.92)))

    # Novikov-Thorne radial emissivity profile
    r_ratio = r_val / R_ISCO
    temp_factor = max(0.08, (r_ratio**(-0.75)) * max(0.0, 1.0 - math.sqrt(1.0 / r_ratio))**0.25 * 3.2 + 0.18)

    # Harmonically periodic spiral density waves (seamless 12.0s loop)
    knot = 1.0 + 0.32 * math.sin(matter_phase * 6.0 + RND_PHASE_OFFSET) + 0.18 * math.cos(matter_phase * 12.0)
    beaming = (delta ** 2.8) * knot * temp_factor * RND_DENSITY_SEED

    # Normalized Doppler velocity parameter u in [0, 1]
    # u = 0: maximum approaching (electric cyan / diamond white)
    # u = 0.5: transverse / neutral (platinum / pale gold)
    # u = 1: maximum receding (radiant amber / copper / deep crimson)
    u = 0.5 + 0.5 * alpha_norm * (v_orb / 0.72)
    u = max(0.0, min(1.0, u))

    # 5-stop continuous smooth spline gradient
    if u < 0.25:
        f = u / 0.25
        r_c = 220 * (1 - f) + 56 * f
        g_c = 245 * (1 - f) + 189 * f
        b_c = 255 * (1 - f) + 248 * f
    elif u < 0.50:
        f = (u - 0.25) / 0.25
        r_c = 56 * (1 - f) + 254 * f
        g_c = 189 * (1 - f) + 240 * f
        b_c = 248 * (1 - f) + 190 * f
    elif u < 0.75:
        f = (u - 0.50) / 0.25
        r_c = 254 * (1 - f) + 245 * f
        g_c = 240 * (1 - f) + 158 * f
        b_c = 190 * (1 - f) + 11 * f
    else:
        f = (u - 0.75) / 0.25
        r_c = 245 * (1 - f) + 185 * f
        g_c = 158 * (1 - f) + 28 * f
        b_c = 11 * (1 - f) + 28 * f

    # Apply Doppler beaming flux modulation
    boost = max(0.45, min(2.5, beaming * 1.35))
    whiteness = max(0.0, min(1.0, (beaming - 1.35) * 0.55))

    final_r = int(min(255, (r_c * boost) * (1.0 - whiteness) + 255 * whiteness))
    final_g = int(min(255, (g_c * boost) * (1.0 - whiteness) + 252 * whiteness))
    final_b = int(min(255, (b_c * boost) * (1.0 - whiteness) + 255 * whiteness))

    alpha_val = int(min(245, max(30, 175 * min(2.5, beaming) * (1.0 - t_r * 0.52))))
    return (final_r, final_g, final_b, alpha_val)

def draw():
    frame = py5.frame_count - 1
    if frame >= TOTAL_FRAMES:
        finish_and_encode()
        return

    tau = frame / float(TOTAL_FRAMES) # [0, 1)
    omega = 2.0 * math.pi

    # Deep interstellar obsidian ground (#020409)
    py5.background(2, 4, 9)

    # 1. Spacetime Metric Web & Boyer-Lindquist Geodesic Graticule
    py5.stroke(20, 32, 54, 60)
    py5.stroke_weight(1.5)
    py5.no_fill()
    for r_web in np.linspace(R_SHADOW * 1.25, 1680, 15):
        py5.circle(CX, CY, r_web * 2)
    for a_deg in range(0, 360, 15):
        rad = math.radians(a_deg)
        py5.line(CX + R_SHADOW * 1.2 * math.cos(rad), CY + R_SHADOW * 1.2 * math.sin(rad),
                 CX + 1700 * math.cos(rad), CY + 1700 * math.sin(rad))

    # 2. Blandford-Znajek Relativistic Jets along Polar Axis
    for direction in [-1, 1]:
        # Synchrotron plasma sheaths
        for glow_w, glow_a in [(110.0, 10), (64.0, 22), (28.0, 45)]:
            py5.no_fill()
            py5.begin_shape()
            for z_j in np.linspace(R_SHADOW * 0.7, 960, 45):
                w = glow_w + 60.0 * (z_j / 960.0)**0.8
                x_loc = 0.0
                y_loc = direction * z_j
                px = CX + x_loc * COS_J - y_loc * SIN_J
                py_val = CY + x_loc * SIN_J + y_loc * COS_J
                py5.stroke(147, 51, 234, int(glow_a * (1.0 - z_j / 960.0)))
                py5.stroke_weight(w)
                py5.vertex(px, py_val)
            py5.end_shape()

        # Core collimated beam
        py5.no_fill()
        py5.begin_shape()
        for z_j in np.linspace(R_SHADOW * 0.75, 980, 65):
            x_loc = 3.6 * math.sin(z_j * 0.02 + omega * tau * 3.0 * direction)
            y_loc = direction * z_j
            px = CX + x_loc * COS_J - y_loc * SIN_J
            py_val = CY + x_loc * SIN_J + y_loc * COS_J
            alpha_beam = int(215 * (1.0 - (z_j / 980.0)**1.2))
            py5.stroke(225, 245, 255, alpha_beam)
            py5.stroke_weight(6.0)
            py5.vertex(px, py_val)
        py5.end_shape()

        # Helical magnetic field flux ropes (6 braided coils)
        for h in range(6):
            base_phase = (h / 6.0) * 2.0 * math.pi + omega * tau * 2.0 * direction
            py5.no_fill()
            py5.begin_shape()
            for z_jet in np.linspace(R_SHADOW * 0.75, 960, 75):
                r_jet = 18.0 + 92.0 * ((z_jet / 960.0) ** 0.72)
                phi_jet = base_phase + z_jet * 0.021 * direction
                x_local = r_jet * math.cos(phi_jet)
                y_local = direction * z_jet
                px = CX + x_local * COS_J - y_local * SIN_J
                py_val = CY + x_local * SIN_J + y_local * COS_J

                t_z = z_jet / 960.0
                alpha_h = int(max(0, 185 * (1.0 - t_z * 0.85)))
                if h % 2 == 0:
                    py5.stroke(192, 132, 252, alpha_h)
                else:
                    py5.stroke(56, 189, 248, alpha_h)
                py5.stroke_weight(3.2)
                py5.vertex(px, py_val)
            py5.end_shape()

    # 3. Dense Novikov-Thorne Accretion Disk - Relativistic Ray Tracing
    # A. UPPER LENSED ARCH (Light from rear disk bent over the black hole)
    for r_val in R_VALS:
        t_r = (r_val - R_ISCO) / (R_OUT - R_ISCO)
        v_orb = 1.0 / (math.sqrt(r_val / M) + A_STAR * 0.5)

        # Deflection profile: strong near shadow, bounded at large r
        apex_height = R_SHADOW * (1.08 + 0.35 * (R_ISCO / r_val)) + (r_val - R_ISCO) * 0.26

        pts = []
        for i in range(PTS_PER_ARCH):
            alpha_pos = -1.0 + 2.0 * (i / float(PTS_PER_ARCH - 1))
            x_disk = alpha_pos * r_val
            arch_shape = math.sqrt(max(0.0, 1.0 - alpha_pos**2))

            y_arch = apex_height * arch_shape
            px = CX + x_disk * 0.99
            py_val = CY - y_arch
            pts.append((px, py_val, x_disk, y_arch))

        for i in range(len(pts) - 1):
            px1, py1, x1, y1 = pts[i]
            px2, py2, x2, y2 = pts[i+1]
            x_mid = 0.5 * (x1 + x2)
            y_mid = 0.5 * (y1 + y2)
            matter_phase = math.atan2(y_mid, x_mid) - omega * tau * 2.0
            col_r, col_g, col_b, alpha_val = get_spline_color_and_alpha(x_mid, r_val, t_r, v_orb, matter_phase)

            py5.stroke(col_r, col_g, col_b, alpha_val)
            py5.stroke_weight(5.0 + 2.4 * (1.0 - t_r))
            py5.line(px1, py1, px2, py2)

        # B. LOWER LENSED ARCH (Light from bottom of rear disk bent under the black hole)
        lower_apex = R_SHADOW * (0.92 + 0.20 * (R_ISCO / r_val)) + (r_val - R_ISCO) * 0.12
        pts_low = []
        for i in range(PTS_PER_ARCH):
            alpha_pos = -1.0 + 2.0 * (i / float(PTS_PER_ARCH - 1))
            x_disk = alpha_pos * r_val
            arch_shape = math.sqrt(max(0.0, 1.0 - alpha_pos**2))
            y_arch = lower_apex * arch_shape
            px = CX + x_disk * 0.99
            py_val = CY + y_arch
            pts_low.append((px, py_val, x_disk, y_arch))

        for i in range(len(pts_low) - 1):
            px1, py1, x1, y1 = pts_low[i]
            px2, py2, x2, y2 = pts_low[i+1]
            x_mid = 0.5 * (x1 + x2)
            y_mid = 0.5 * (y1 + y2)
            matter_phase = -math.atan2(y_mid, x_mid) - omega * tau * 2.0
            col_r, col_g, col_b, alpha_val = get_spline_color_and_alpha(x_mid, r_val, t_r, v_orb, matter_phase)

            py5.stroke(col_r, col_g, col_b, int(alpha_val * 0.85))
            py5.stroke_weight(4.4 + 2.0 * (1.0 - t_r))
            py5.line(px1, py1, px2, py2)

    # 4. Central Kerr Black Hole Shadow Void (Asymmetric Bardeen / Kerr Silhouette)
    shadow_dx = 0.14 * A_STAR * M
    py5.fill(1, 2, 5)
    py5.no_stroke()
    py5.begin_shape()
    for deg in range(360):
        rad = math.radians(deg)
        r_sh = R_SHADOW * (1.0 + 0.09 * A_STAR * math.cos(rad) - 0.03 * (math.sin(rad)**2))
        px = CX + shadow_dx + r_sh * math.cos(rad)
        py_val = CY + r_sh * math.sin(rad) * 0.95
        py5.vertex(px, py_val)
    py5.end_shape(py5.CLOSE)

    # 5. Kerr Ergosphere Boundary & Frame-Dragging Infalling Streamlines (Inside the ISCO cavity)
    for e_weight, e_alpha in [(8.0, 55), (4.4, 175), (2.2, 245)]:
        py5.stroke(16, 185, 129, e_alpha) # Neon emerald
        py5.stroke_weight(e_weight)
        py5.no_fill()
        py5.begin_shape()
        for deg in range(361):
            rad = math.radians(deg)
            cos_th = math.sin(rad) * COS_I
            r_e = M * (1.0 + math.sqrt(max(0.0, 1.0 - (A_STAR**2) * (cos_th**2))))
            px = CX + r_e * math.cos(rad) * 1.06
            py_val = CY + r_e * math.sin(rad) * 0.88
            py5.vertex(px, py_val)
        py5.end_shape()

    # Infalling Frame-Dragging Spirals (Lense-Thirring Spacetime Whirlpool inside cavity)
    for s in range(22):
        base_s_phi = (s / 22.0) * 2.0 * math.pi
        py5.stroke(56, 189, 248, 160)
        py5.stroke_weight(3.0)
        py5.no_fill()
        py5.begin_shape()
        for r_s in np.linspace(R_ISCO * 1.35, R_PLUS * 1.04, 60):
            drag_twist = (2.0 * A * M / (r_s**2.2 + 20.0)) * 2.8
            phi_s = base_s_phi + drag_twist + omega * tau * 2.0
            px_s = CX + r_s * math.cos(phi_s)
            py_s = CY + (r_s * 0.42) * math.sin(phi_s)
            py5.vertex(px_s, py_s)
        py5.end_shape()

    # Hairline Ultra-Luminous Photon Ring (Caustic boundary)
    for p_layer, (p_weight, p_alpha) in enumerate([(7.0, 75), (4.0, 150), (2.0, 245)]):
        pts_p = []
        for deg in range(361):
            rad = math.radians(deg)
            r_sh = R_SHADOW * (1.0 + 0.09 * A_STAR * math.cos(rad) - 0.03 * (math.sin(rad)**2))
            px = CX + shadow_dx + r_sh * math.cos(rad)
            py_val = CY + r_sh * math.sin(rad) * 0.95
            pts_p.append((px, py_val, rad))

        for i in range(len(pts_p) - 1):
            px1, py1, rad1 = pts_p[i]
            px2, py2, rad2 = pts_p[i+1]
            rad_mid = 0.5 * (rad1 + rad2)
            boost = max(0.25, 1.0 - 0.85 * math.cos(rad_mid))
            if math.cos(rad_mid) < 0:
                py5.stroke(235, 250, 255, int(p_alpha * boost))
            else:
                py5.stroke(245, 158, 11, int(p_alpha * 0.45 * boost))
            py5.stroke_weight(p_weight)
            py5.line(px1, py1, px2, py2)

    # 6. Front Equatorial Accretion Disk (Passes In Front Across Equator)
    for r_val in R_VALS:
        t_r = (r_val - R_ISCO) / (R_OUT - R_ISCO)
        v_orb = 1.0 / (math.sqrt(r_val / M) + A_STAR * 0.5)

        pts_front = []
        for i in range(PTS_PER_ARCH):
            th = math.pi - (i / float(PTS_PER_ARCH - 1)) * math.pi
            px = CX + r_val * math.cos(th)
            py_val = CY + r_val * math.sin(th) * COS_I
            x_disk = r_val * math.cos(th)
            pts_front.append((px, py_val, x_disk, th))

        for i in range(len(pts_front) - 1):
            px1, py1, x1, th1 = pts_front[i]
            px2, py2, x2, th2 = pts_front[i+1]
            x_mid = 0.5 * (x1 + x2)
            th_mid = 0.5 * (th1 + th2)
            matter_phase = th_mid - omega * tau * 2.0
            col_r, col_g, col_b, alpha_val = get_spline_color_and_alpha(x_mid, r_val, t_r, v_orb, matter_phase)

            py5.stroke(col_r, col_g, col_b, alpha_val)
            py5.stroke_weight(5.5 + 2.8 * (1.0 - t_r))
            py5.line(px1, py1, px2, py2)

    # 7. Four Corner Relativistic Telemetry Cards (Scaled for 4K)
    # Corner 1 (Top-Left): Boyer-Lindquist Metric Tensor
    c1_x, c1_y = 350, 350
    py5.fill(6, 10, 18, 240)
    py5.stroke(35, 52, 78)
    py5.stroke_weight(2.5)
    py5.rect(c1_x - 230, c1_y - 220, 460, 430)

    py5.fill(56, 189, 248)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(21)
    py5.text("BOYER-LINDQUIST KERR METRIC", c1_x - 200, c1_y - 192)
    py5.fill(148, 163, 184)
    py5.text("ds^2 = -(1-2Mr/rho^2)dt^2", c1_x - 200, c1_y - 152)
    py5.text("- (4aMr sin^2(th)/rho^2) dt dphi", c1_x - 200, c1_y - 120)
    py5.text(f"HORIZON r+ = {R_PLUS/M:.3f} M", c1_x - 200, c1_y - 84)
    py5.text("ERGOSPHERE r_E = M + sqrt(M^2 - a^2 cos^2(th))", c1_x - 200, c1_y - 48)
    py5.text("ISCO RADIUS r_isco = 2.05 M", c1_x - 200, c1_y - 12)
    py5.stroke(56, 189, 248, 180)
    py5.stroke_weight(2.4)
    py5.no_fill()
    py5.ellipse(c1_x, c1_y + 110, 160, 88)
    py5.stroke(16, 185, 129, 210)
    py5.circle(c1_x, c1_y + 110, 64)

    # Corner 2 (Top-Right): Relativistic Doppler Boosting
    c2_x, c2_y = WIDTH - 350, 350
    py5.fill(6, 10, 18, 240)
    py5.stroke(35, 52, 78)
    py5.stroke_weight(2.5)
    py5.rect(c2_x - 230, c2_y - 220, 460, 430)

    py5.fill(56, 189, 248)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(21)
    py5.text("RELATIVISTIC DOPPLER BEAMING", c2_x - 200, c2_y - 192)
    py5.fill(148, 163, 184)
    py5.text("DOPPLER FACTOR: DELTA = 1/[GAMMA(1-v/c)]", c2_x - 200, c2_y - 152)
    py5.text("INTENSITY BOOST: I_OBS = DELTA^(3+ALPHA)", c2_x - 200, c2_y - 116)
    py5.text("LORENTZ FACTOR: GAMMA_MAX = 1.48", c2_x - 200, c2_y - 80)
    py5.text("ASYMMETRY RATIO: 8.6 : 1 (L/R)", c2_x - 200, c2_y - 44)
    py5.stroke(245, 158, 11)
    py5.stroke_weight(3.0)
    py5.no_fill()
    py5.begin_shape()
    for wx in range(-90, 90):
        wy = -50.0 * math.exp(-((wx + 30)/36.0)**2) + 16.0 * math.exp(-((wx - 40)/44.0)**2)
        py5.vertex(c2_x + wx, c2_y + 115 + wy)
    py5.end_shape()

    # Corner 3 (Bottom-Left): Penrose Process Energy Extraction
    c3_x, c3_y = 350, HEIGHT - 350
    py5.fill(6, 10, 18, 240)
    py5.stroke(35, 52, 78)
    py5.stroke_weight(2.5)
    py5.rect(c3_x - 230, c3_y - 210, 460, 420)

    py5.fill(16, 185, 129)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(21)
    py5.text("PENROSE PROCESS EXTRACTION", c3_x - 200, c3_y - 184)
    py5.fill(148, 163, 184)
    py5.text("ERGOSPHERE NEGATIVE ENERGY STATES", c3_x - 200, c3_y - 144)
    py5.text("MAX EFFICIENCY: ETA_MAX = 20.7%", c3_x - 200, c3_y - 108)
    py5.text("ROTATIONAL ENERGY: E_ROT = 0.29 M", c3_x - 200, c3_y - 72)
    py5.stroke(16, 185, 129, 220)
    py5.stroke_weight(3.6)
    py5.line(c3_x - 80, c3_y + 70, c3_x, c3_y + 70)
    py5.stroke(239, 68, 68, 220)
    py5.line(c3_x, c3_y + 70, c3_x + 70, c3_y + 110)
    py5.stroke(56, 189, 248, 220)
    py5.line(c3_x, c3_y + 70, c3_x + 70, c3_y + 30)

    # Corner 4 (Bottom-Right): Kerr Spin a* & Horizon Velocity
    c4_x, c4_y = WIDTH - 350, HEIGHT - 350
    py5.fill(6, 10, 18, 240)
    py5.stroke(35, 52, 78)
    py5.stroke_weight(2.5)
    py5.rect(c4_x - 230, c4_y - 210, 460, 420)

    py5.fill(56, 189, 248)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(21)
    py5.text("KERR SPIN & FRAME DRAGGING", c4_x - 200, c4_y - 184)
    py5.fill(148, 163, 184)
    py5.text(f"SPIN PARAMETER: a* = {A_STAR:.3f}", c4_x - 200, c4_y - 144)
    py5.text("HORIZON FREQ: OMEGA_H = a / (2 M r+)", c4_x - 200, c4_y - 108)
    py5.text("BLANDFORD-ZNAJEK JET POWER", c4_x - 200, c4_y - 72)
    py5.stroke(56, 189, 248, 180)
    py5.stroke_weight(2.8)
    py5.no_fill()
    py5.circle(c4_x, c4_y + 80, 96)
    spin_needle_a = omega * tau * 2.0
    py5.stroke(245, 158, 11)
    py5.stroke_weight(4.0)
    py5.line(c4_x, c4_y + 80, c4_x + 44 * math.cos(spin_needle_a), c4_y + 80 + 44 * math.sin(spin_needle_a))

    # 8. Archival Relativistic Telemetry Borders & Title
    py5.no_fill()
    py5.stroke(30, 42, 62)
    py5.stroke_weight(4.0)
    py5.rect(60, 60, WIDTH - 120, HEIGHT - 120)
    py5.stroke(56, 189, 248, 90)
    py5.stroke_weight(2.0)
    py5.rect(72, 72, WIDTH - 144, HEIGHT - 144)

    # Header Title
    py5.fill(241, 245, 249)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(23)
    py5.text("RELATIVISTIC ASTROPHYSICS - GENERAL RELATIVITY KERR BLACK HOLE SPACETIME", WIDTH / 2.0, 96)
    py5.text_size(37)
    py5.text("KERR BLACK HOLE ERGOSPHERE - LENSE-THIRRING FRAME DRAGGING", WIDTH / 2.0, 136)
    py5.text_size(21)
    py5.fill(56, 189, 248)
    py5.text("BOYER-LINDQUIST GEOMETRY - RELATIVISTIC DOPPLER BEAMING - GRAVITATIONAL LENSING HALO", WIDTH / 2.0, 186)

    # Bottom Telemetry
    py5.fill(148, 163, 184)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(21)
    py5.text("ROY KERR (1963) - ROGER PENROSE (1969) - LENSE-THIRRING EFFECT - GENERAL RELATIVITY", 108, HEIGHT - 92)
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text("4K GENERATIVE MEDIA ART - 12.0s RELATIVISTIC HARMONIC CYCLE", WIDTH - 108, HEIGHT - 92)

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
