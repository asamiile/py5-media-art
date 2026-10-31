"""
kinetic_horological_rose_engine_guilloche_2d
Autonomous 4K Media Art Animation (12.0s seamless loop, 720 frames @ 60fps)

Haute Horlogerie rose engine lathe micro-engraving simulation on deep obsidian substrate.
Features multi-harmonic epicyclic rosette guilloché (grain d'orge and vague d'argent),
concentric railroad and Roman chapter rings, an open-worked tourbillon escapement cage
with Glucydur balance wheel, blued steel Breguet hands, and animated machine lathe telemetry.
Strictly autonomous and anonymous; completely free of author signatures or personal marks.
"""

import os
import shutil
import subprocess
import time
import numpy as np
import py5

WORK_NAME = "kinetic_horological_rose_engine_guilloche_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "temp_frames")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_PNG = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

TOTAL_FRAMES = 720
FPS = 60
WIDTH, HEIGHT = 3840, 2160
CX, CY = WIDTH // 2, HEIGHT // 2

# Precompute mathematical constants and angular coordinates
TAU = 2 * np.pi
ANGLES_BARLEY = np.linspace(0, TAU, 450, endpoint=False)
ANGLES_WAVE = np.linspace(0, TAU, 360, endpoint=False)
COS_BARLEY = np.cos(ANGLES_BARLEY)
SIN_BARLEY = np.sin(ANGLES_BARLEY)
COS_WAVE = np.cos(ANGLES_WAVE)
SIN_WAVE = np.sin(ANGLES_WAVE)

# Rosette cam precomputation for corner apparatus
ANGLES_CAM = np.linspace(0, TAU, 240, endpoint=False)
CAM_PROFILE = 140.0 + 18.0 * np.cos(24 * ANGLES_CAM)
CAM_XS = CAM_PROFILE * np.cos(ANGLES_CAM)
CAM_YS = CAM_PROFILE * np.sin(ANGLES_CAM)

current_frame = 0
start_time = 0.0

def settings():
    py5.size(WIDTH, HEIGHT, py5.P2D)
    py5.smooth(8)

def setup():
    global start_time
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    start_time = time.time()
    print(f"[{WORK_NAME}] Starting 4K UHD 60fps rendering ({TOTAL_FRAMES} frames)...")

def draw():
    global current_frame
    
    t_val = current_frame / TOTAL_FRAMES
    
    # Virtual rotating light vector (completes 1 full revolution in 12s)
    light_ang = TAU * t_val - np.pi / 4.0
    lx, ly = np.cos(light_ang), np.sin(light_ang)
    
    # Deep horological obsidian background
    py5.background(6, 8, 12)
    
    # 0. Lathe Machine Datum Graticule
    py5.no_fill()
    py5.stroke(20, 28, 40, 110)
    py5.stroke_weight(1.5)
    py5.line(CX, 60, CX, HEIGHT - 60)
    py5.line(60, CY, WIDTH - 60, CY)
    for r_grid in [1200, 1500, 1800]:
        py5.ellipse(CX, CY, r_grid * 2, r_grid * 2)

    # -------------------------------------------------------------
    # Corner Lathe Apparatuses
    # -------------------------------------------------------------
    # Top-Left: Rotating Rose Engine Rosette Cam (2 revs/loop)
    tl_x, tl_y = 380, 320
    py5.push_matrix()
    py5.translate(tl_x, tl_y)
    py5.rotate(TAU * t_val * 2.0)
    py5.stroke(185, 145, 45, 190)
    py5.stroke_weight(2.0)
    py5.no_fill()
    py5.begin_shape()
    for gx, gy in zip(CAM_XS, CAM_YS):
        py5.vertex(gx, gy)
    py5.end_shape(py5.CLOSE)
    py5.ellipse(0, 0, 70, 70)
    py5.fill(210, 160, 50)
    py5.ellipse(0, 0, 24, 24)
    py5.pop_matrix()
    py5.fill(120, 150, 185)
    py5.text_size(18)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text("ROSETTE CAM N=24", tl_x, tl_y + 190)
    py5.text("LATHE HEADSTOCK RATIO 2:1", tl_x, tl_y + 215)

    # Top-Right: Interlocking Epicyclic Gear Train (4:3 ratio)
    tr_x, tr_y = WIDTH - 380, 320
    # Gear 1 (24 Teeth, +3 revs)
    py5.push_matrix()
    py5.translate(tr_x - 55, tr_y)
    py5.rotate(TAU * t_val * 3.0)
    py5.stroke(215, 165, 55, 200)
    py5.stroke_weight(2.0)
    py5.no_fill()
    py5.ellipse(0, 0, 180, 180)
    for g in range(24):
        ga = g * (TAU / 24.0)
        gx, gy = 90.0 * np.cos(ga), 90.0 * np.sin(ga)
        py5.line(gx, gy, gx * 1.12, gy * 1.12)
    py5.fill(160, 120, 40)
    py5.ellipse(0, 0, 30, 30)
    py5.pop_matrix()
    # Gear 2 (18 Teeth, -4 revs)
    py5.push_matrix()
    py5.translate(tr_x + 75, tr_y)
    py5.rotate(-TAU * t_val * 4.0 + 0.15)
    py5.stroke(175, 135, 45, 200)
    py5.stroke_weight(2.0)
    py5.no_fill()
    py5.ellipse(0, 0, 135, 135)
    for g in range(18):
        ga = g * (TAU / 18.0)
        gx, gy = 67.5 * np.cos(ga), 67.5 * np.sin(ga)
        py5.line(gx, gy, gx * 1.15, gy * 1.15)
    py5.fill(130, 100, 35)
    py5.ellipse(0, 0, 24, 24)
    py5.pop_matrix()
    py5.fill(120, 150, 185)
    py5.text("EPICYCLIC GEAR TRAIN", tr_x, tr_y + 190)
    py5.text("MODULE 1.25 • 24T / 18T", tr_x, tr_y + 215)

    # Bottom-Left: Micrometer Cutter Carriage Scale
    bl_x, bl_y = 380, HEIGHT - 300
    py5.stroke(35, 50, 70, 180)
    py5.stroke_weight(2.0)
    py5.line(bl_x - 140, bl_y, bl_x + 140, bl_y)
    for v in range(-14, 15):
        vx = bl_x + v * 10
        h_tick = 18 if v % 5 == 0 else 9
        py5.line(vx, bl_y - h_tick, vx, bl_y)
        if v % 5 == 0:
            py5.fill(110, 140, 175)
            py5.text_size(14)
            py5.text(f"{abs(v)*2}", vx, bl_y - 30)
    slider_x = bl_x + 40.0 * np.sin(TAU * t_val)
    py5.stroke(245, 180, 50)
    py5.stroke_weight(2.5)
    py5.line(slider_x, bl_y - 25, slider_x, bl_y + 20)
    py5.fill(245, 180, 50)
    py5.text(f"FEED: {35.4 + 4.2*np.sin(TAU*t_val):.1f} μm", bl_x, bl_y + 45)
    py5.fill(120, 150, 185)
    py5.text_size(18)
    py5.text("CUTTER CARRIAGE MICROMETER", bl_x, bl_y + 75)

    # Bottom-Right: Optical Specular Angle Dial
    br_x, br_y = WIDTH - 380, HEIGHT - 300
    py5.no_fill()
    py5.stroke(35, 50, 70, 180)
    py5.stroke_weight(2.0)
    py5.ellipse(br_x, br_y, 160, 160)
    for d in range(12):
        da = d * (TAU / 12.0)
        py5.line(br_x + 70.0 * np.cos(da), br_y + 70.0 * np.sin(da),
                 br_x + 80.0 * np.cos(da), br_y + 80.0 * np.sin(da))
    py5.stroke(240, 245, 255)
    py5.stroke_weight(2.5)
    py5.line(br_x, br_y, br_x + 65.0 * lx, br_y + 65.0 * ly)
    py5.fill(240, 245, 255)
    py5.ellipse(br_x + 65.0 * lx, br_y + 65.0 * ly, 6, 6)
    py5.fill(120, 150, 185)
    py5.text_size(18)
    py5.text(f"INCIDENT LIGHT: {int((np.degrees(light_ang)) % 360)}°", br_x, br_y + 110)
    py5.text("VIRTUAL LUSTER SWEEP", br_x, br_y + 135)

    # -------------------------------------------------------------
    # 1. Coin-Edge Fluted Watch Case Flank (Cannelures)
    # -------------------------------------------------------------
    R_case = 1020
    n_flutes = 240
    for f in range(n_flutes):
        fa = f * (TAU / n_flutes)
        fx, fy = np.cos(fa), np.sin(fa)
        f_dot = max(0.0, fx * lx + fy * ly)
        b_flute = 35.0 + 95.0 * f_dot
        py5.stroke(int(b_flute * 0.85), int(b_flute * 0.95), int(b_flute * 1.05))
        py5.stroke_weight(3.0)
        py5.line(CX + (R_case - 16) * fx, CY + (R_case - 16) * fy,
                 CX + (R_case + 12) * fx, CY + (R_case + 12) * fy)

    # -------------------------------------------------------------
    # 2. Polished Bezel Step Rings
    # -------------------------------------------------------------
    py5.no_fill()
    py5.stroke(185, 200, 220)
    py5.stroke_weight(5.0)
    py5.ellipse(CX, CY, 992 * 2, 992 * 2)
    py5.stroke(110, 125, 145)
    py5.stroke_weight(2.5)
    py5.ellipse(CX, CY, 976 * 2, 976 * 2)
    py5.ellipse(CX, CY, 960 * 2, 960 * 2)

    # -------------------------------------------------------------
    # 3. Outer Railroad Minute Track (Chemin de fer)
    # -------------------------------------------------------------
    R_rail_out = 932
    R_rail_in = 884
    py5.stroke(150, 170, 195)
    py5.stroke_weight(2.5)
    py5.ellipse(CX, CY, R_rail_out * 2, R_rail_out * 2)
    py5.ellipse(CX, CY, R_rail_in * 2, R_rail_in * 2)
    
    for i in range(60):
        angle = i * (TAU / 60.0)
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        if i % 5 == 0:
            py5.stroke(245, 185, 55)
            py5.stroke_weight(5.0)
            py5.line(CX + (R_rail_in - 4) * cos_a, CY + (R_rail_in - 4) * sin_a,
                     CX + (R_rail_out + 4) * cos_a, CY + (R_rail_out + 4) * sin_a)
            # Polished pearl cabochon
            py5.fill(240, 245, 255)
            py5.no_stroke()
            py5.ellipse(CX + (R_rail_in - 24) * cos_a, CY + (R_rail_in - 24) * sin_a, 11, 11)
        else:
            py5.stroke(140, 160, 185)
            py5.stroke_weight(1.8)
            py5.line(CX + R_rail_in * cos_a, CY + R_rail_in * sin_a,
                     CX + R_rail_out * cos_a, CY + R_rail_out * sin_a)

    # -------------------------------------------------------------
    # 4. Chapter Ring (Tour d'heures) with azurage circular satin brushing
    # -------------------------------------------------------------
    py5.no_fill()
    py5.stroke(45, 60, 80, 90)
    py5.stroke_weight(1.2)
    for r in np.linspace(750, 860, 50):
        py5.ellipse(CX, CY, r * 2, r * 2)

    # Roman Numerals in Breguet styling
    roman_numerals = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    for idx, rom in enumerate(roman_numerals):
        angle = -np.pi / 2.0 + idx * (TAU / 12.0)
        r_text = 806
        tx = CX + r_text * np.cos(angle)
        ty = CY + r_text * np.sin(angle)
        py5.fill(225, 238, 255)
        py5.text_align(py5.CENTER, py5.CENTER)
        py5.text_size(34)
        py5.text(rom, tx, ty)

    # Inner Chapter Ring Border
    py5.no_fill()
    py5.stroke(185, 200, 220)
    py5.stroke_weight(3.5)
    py5.ellipse(CX, CY, 736 * 2, 736 * 2)
    py5.stroke(90, 110, 130)
    py5.stroke_weight(1.8)
    py5.ellipse(CX, CY, 724 * 2, 724 * 2)

    # -------------------------------------------------------------
    # 5. Outer Guilloché Zone: Grain d'Orge (Barleycorn)
    # -------------------------------------------------------------
    N_lobes = 28
    K_rings = 48
    n_pts_b = len(ANGLES_BARLEY)
    
    for k in range(K_rings):
        r_base = 420.0 + (k / (K_rings - 1)) * (716.0 - 420.0)
        phase = k * np.pi + TAU * t_val
        amp = 7.2 + 1.2 * np.sin(TAU * t_val + k * 0.12)
        wave_mod = 2.8 * np.sin(4.0 * ANGLES_BARLEY - TAU * t_val) * np.cos(k * np.pi / 7.0)
        r_profile = r_base + amp * np.cos(N_lobes * ANGLES_BARLEY + phase) + wave_mod
        
        xs = CX + r_profile * COS_BARLEY
        ys = CY + r_profile * SIN_BARLEY
        b_base = 135.0 + 35.0 * np.sin(k * 0.2 + TAU * t_val)
        
        for i in range(n_pts_b):
            i_next = (i + 1) % n_pts_b
            dx = xs[i_next] - xs[i]
            dy = ys[i_next] - ys[i]
            seg_len = np.hypot(dx, dy)
            if seg_len < 1e-6:
                continue
            nx, ny = -dy / seg_len, dx / seg_len
            spec = max(0.0, nx * lx + ny * ly) ** 2.2
            
            r_c = min(255, int(b_base * 0.85 + spec * 110.0))
            g_c = min(255, int(b_base * 0.95 + spec * 115.0))
            b_c = min(255, int(b_base * 1.05 + spec * 135.0))
            
            py5.stroke(r_c, g_c, b_c, 215)
            py5.stroke_weight(1.5)
            py5.line(xs[i], ys[i], xs[i_next], ys[i_next])

    # -------------------------------------------------------------
    # 6. Intermediate Beaded Border Ring
    # -------------------------------------------------------------
    py5.no_fill()
    py5.stroke(190, 205, 225)
    py5.stroke_weight(3.5)
    py5.ellipse(CX, CY, 408 * 2, 408 * 2)
    py5.stroke(85, 105, 125)
    py5.stroke_weight(1.8)
    py5.ellipse(CX, CY, 396 * 2, 396 * 2)

    # -------------------------------------------------------------
    # 7. Inner Guilloché Zone: Vague d'Argent (Harmonic Wave Fluting)
    # -------------------------------------------------------------
    K_inner = 28
    n_pts_w = len(ANGLES_WAVE)
    for k in range(K_inner):
        r_base_in = 220.0 + (k / (K_inner - 1)) * (388.0 - 220.0)
        phase_in = -k * 0.4 + 2.0 * TAU * t_val
        amp_in = 5.6 * np.cos(k * 0.15)
        r_prof_in = r_base_in + amp_in * np.sin(16.0 * ANGLES_WAVE + phase_in)
        
        xs_in = CX + r_prof_in * COS_WAVE
        ys_in = CY + r_prof_in * SIN_WAVE
        b_in = 125.0 + 40.0 * np.cos(k * 0.25 - TAU * t_val)
        
        for i in range(n_pts_w):
            i_next = (i + 1) % n_pts_w
            dx = xs_in[i_next] - xs_in[i]
            dy = ys_in[i_next] - ys_in[i]
            seg_len = np.hypot(dx, dy)
            if seg_len < 1e-6:
                continue
            nx, ny = -dy / seg_len, dx / seg_len
            spec = max(0.0, nx * lx + ny * ly) ** 2.2
            
            r_c = min(255, int(b_in * 0.82 + spec * 120.0))
            g_c = min(255, int(b_in * 0.92 + spec * 125.0))
            b_c = min(255, int(b_in * 1.05 + spec * 145.0))
            
            py5.stroke(r_c, g_c, b_c, 220)
            py5.stroke_weight(1.5)
            py5.line(xs_in[i], ys_in[i], xs_in[i_next], ys_in[i_next])

    # -------------------------------------------------------------
    # 8. Tourbillon Center Aperture & Escapement Carriage
    # -------------------------------------------------------------
    R_tourb = 208
    py5.fill(10, 13, 19)
    py5.stroke(210, 225, 245)
    py5.stroke_weight(4.0)
    py5.ellipse(CX, CY, R_tourb * 2, R_tourb * 2)
    
    # Internal Côtes de Genève (Geneva Stripes) inside circular aperture
    py5.stroke_weight(1.8)
    for dy in range(-R_tourb + 5, R_tourb - 5, 10):
        dx = np.sqrt(max(0.0, R_tourb**2 - dy**2)) - 3.0
        c_val = 20 + 10 * ((dy // 10) % 2)
        py5.stroke(c_val + 3, c_val + 7, c_val + 13)
        py5.line(CX - dx, CY + dy, CX + dx, CY + dy)
        
    # Screws securing aperture rim
    for s in range(6):
        sa = s * (TAU / 6.0)
        sx = CX + (R_tourb + 14) * np.cos(sa)
        sy = CY + (R_tourb + 14) * np.sin(sa)
        py5.fill(29, 78, 216)
        py5.stroke(150, 190, 245)
        py5.stroke_weight(1.5)
        py5.ellipse(sx, sy, 12, 12)
        py5.stroke(220, 235, 255)
        py5.line(sx - 4, sy, sx + 4, sy)

    # Tourbillon Carriage (Rotating 1 full revolution per 12s loop)
    py5.push_matrix()
    py5.translate(CX, CY)
    py5.rotate(TAU * t_val)
    
    # Glucydur Gold Balance Wheel
    py5.stroke(230, 180, 50)
    py5.stroke_weight(4.0)
    py5.no_fill()
    py5.ellipse(0, 0, 300, 300)
    for p in range(16):
        pa = p * (TAU / 16.0)
        px, py_val = 150.0 * np.cos(pa), 150.0 * np.sin(pa)
        py5.fill(250, 200, 70)
        py5.no_stroke()
        py5.ellipse(px, py_val, 9, 9)
        
    # Coiled Hairspring (Breguet Overcoil, 12 beats per cycle)
    py5.no_fill()
    py5.stroke(140, 175, 220, 180)
    py5.stroke_weight(2.0)
    py5.begin_shape()
    for theta_h in np.linspace(0, 7.5 * np.pi, 280):
        r_h = 16.0 + theta_h * 4.6
        hx = r_h * np.cos(theta_h + np.sin(12.0 * TAU * t_val) * 0.22)
        hy = r_h * np.sin(theta_h + np.sin(12.0 * TAU * t_val) * 0.22)
        py5.vertex(hx, hy)
    py5.end_shape()

    # 3-Arm Mirror-Polished Titanium Bridge
    for arm in range(3):
        a_angle = arm * (TAU / 3.0)
        ax = 140.0 * np.cos(a_angle)
        ay = 140.0 * np.sin(a_angle)
        py5.stroke(220, 230, 245)
        py5.stroke_weight(9.0)
        py5.line(0, 0, ax, ay)
        py5.stroke(120, 135, 155)
        py5.stroke_weight(3.5)
        py5.line(0, 0, ax, ay)
        py5.fill(75, 85, 100)
        py5.stroke(190, 205, 225)
        py5.stroke_weight(2.0)
        py5.ellipse(ax, ay, 14, 14)
        
    # Center Synthetic Pigeon-Blood Ruby Jewel in 18K Gold Chaton
    py5.fill(235, 185, 55)
    py5.stroke(190, 145, 40)
    py5.stroke_weight(2.0)
    py5.ellipse(0, 0, 44, 44)
    py5.fill(225, 25, 70)
    py5.stroke(255, 110, 140)
    py5.ellipse(0, 0, 26, 26)
    py5.fill(255, 255, 255, 220)
    py5.no_stroke()
    py5.ellipse(-4, -4, 7, 7)
    
    py5.pop_matrix()

    # -------------------------------------------------------------
    # 9. Blued Steel Breguet Hands (Aiguilles Pomme Évidée)
    # -------------------------------------------------------------
    h_angle = -np.pi / 2.0 + TAU * t_val
    m_angle = -np.pi / 2.0 + 2.0 * TAU * t_val
    
    def draw_breguet_hand(length, angle, width, pomme_r):
        py5.push_matrix()
        py5.translate(CX, CY)
        py5.rotate(angle)
        # Drop shadow
        py5.stroke(0, 0, 0, 110)
        py5.stroke_weight(width + 4.0)
        py5.line(10, 10, length + 10, 10)
        # Main stem
        py5.stroke(25, 75, 215)
        py5.stroke_weight(width)
        py5.line(0, 0, length, 0)
        # Hollow pomme ring
        pomme_x = length * 0.73
        py5.stroke(35, 95, 235)
        py5.stroke_weight(width * 1.25)
        py5.no_fill()
        py5.ellipse(pomme_x, 0, pomme_r * 2, pomme_r * 2)
        # Needle point
        py5.stroke(60, 135, 245)
        py5.stroke_weight(width * 0.75)
        py5.line(pomme_x + pomme_r, 0, length, 0)
        # Counterbalance
        py5.stroke(25, 75, 215)
        py5.stroke_weight(width * 1.4)
        py5.line(0, 0, -length * 0.22, 0)
        py5.pop_matrix()

    draw_breguet_hand(560, h_angle, 5.2, 30)
    draw_breguet_hand(810, m_angle, 4.2, 40)

    # Center Cannon Pinion Cap (Polished Steel Dome)
    py5.fill(235, 245, 255)
    py5.stroke(70, 85, 105)
    py5.stroke_weight(2.0)
    py5.ellipse(CX, CY, 32, 32)
    py5.fill(255, 255, 255)
    py5.no_stroke()
    py5.ellipse(CX - 4, CY - 4, 8, 8)

    # -------------------------------------------------------------
    # 10. Technical Horological Cartouche at 6 o'clock
    # -------------------------------------------------------------
    cart_y = CY + 580
    py5.fill(10, 14, 22, 230)
    py5.stroke(140, 160, 185)
    py5.stroke_weight(1.5)
    py5.rect_mode(py5.CENTER)
    py5.rect(CX, cart_y, 480, 42, 6)
    py5.fill(215, 230, 250)
    py5.text_size(17)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text("TOURBILLON 60S • EPICYCLIC GUILLOCHÉ • 21,600 VPH", CX, cart_y)

    # Save current frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{current_frame:04d}.png")
    py5.save_frame(frame_path)
    
    # Save preview image at frame 180 (quarter cycle where light and hands are beautifully balanced)
    if current_frame == 180 or (current_frame == 1 and not os.path.exists(PREVIEW_PNG)):
        py5.save_frame(PREVIEW_PNG)
        print(f"[{WORK_NAME}] Saved preview image: {PREVIEW_PNG}")

    current_frame += 1
    
    if current_frame % 60 == 0 or current_frame == TOTAL_FRAMES:
        elapsed = time.time() - start_time
        fps_calc = current_frame / max(0.1, elapsed)
        eta = (TOTAL_FRAMES - current_frame) / max(0.01, fps_calc)
        print(f"[{WORK_NAME}] Frame {current_frame:03d}/{TOTAL_FRAMES} ({current_frame/TOTAL_FRAMES*100:.1f}%) | Speed: {fps_calc:.2f} fps | ETA: {eta:.1f}s")
    
    if current_frame >= TOTAL_FRAMES:
        finish_and_encode()

def finish_and_encode():
    global start_time
    total_elapsed = time.time() - start_time
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {total_elapsed:.1f}s (~{TOTAL_FRAMES/total_elapsed:.2f} fps).")
    print(f"[{WORK_NAME}] Compiling 4K 60fps MP4 with FFmpeg...")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        OUTPUT_MP4
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=py5.sys.stderr)
        mp4_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
        print(f"[{WORK_NAME}] Successfully generated output.mp4 ({mp4_size_mb:.2f} MB)")
    except Exception as e:
        print(f"[{WORK_NAME}] Error encoding video: {e}")
    finally:
        if os.path.exists(FRAMES_DIR):
            shutil.rmtree(FRAMES_DIR)
            print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")
            
    print(f"[{WORK_NAME}] Complete!")
    os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()
