"""
Kinetic Pier Luigi Nervi Isostatic Ribbed Vault Kinematics 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art exploring Structural Engineering, Ferroconcrete
Precast Lamella Vaults, and Isostatic Stress Trajectories inspired by Pier Luigi Nervi
(Palazzetto dello Sport, Rome 1957; Turin Exhibition Hall Salone Agnelli 1948)
executed on deep structural blueprint slate (#0a0e17).

A monumental ribbed vaulted cupola (diameter 61.0 m) seen in wide-angle upward
worm's-eye perspective features 72 interwoven isostatic ribs following exact principal
stress trajectories, 432 recessed diamond coffer pans (cassettone), a central sunlit
skylight oculus casting sweeping volumetric light cones, 18 perimeter inclined Y-pylons,
and finite-element stress telemetry in 12.0s elastic harmonic resonance.
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
WORK_NAME = "kinetic_nervi_isostatic_ribbed_vault_kinematics_2d"
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
RND_LOAD_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))
RND_SUN_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))

# Vault Dimensions (scaled for 4K)
OC_X = WIDTH / 2.0
OC_Y = HEIGHT / 2.0 - 40.0
R_OCULUS = 180.0
R_PERIMETER = 1160.0

NUM_RINGS = 13
R_STEPS = np.geomspace(R_OCULUS, R_PERIMETER, NUM_RINGS)

NUM_SPOKES = 36 # 36 left spirals, 36 right spirals
PTS_PER_SPIRAL = 70
T_VALS = np.linspace(0.0, 1.0, PTS_PER_SPIRAL)

# Precalculate static geometric grid for Diamond Coffering Pans (Cassettone)
GRID_PTS = np.zeros((2, NUM_SPOKES, NUM_RINGS, 2))
for fam_idx, family in enumerate([-1, 1]):
    for s in range(NUM_SPOKES):
        base_angle = (s / float(NUM_SPOKES)) * 2.0 * math.pi
        for r_idx, r_val in enumerate(R_STEPS):
            t_norm = (r_val - R_OCULUS) / (R_PERIMETER - R_OCULUS)
            twist = family * (t_norm ** 0.72) * 1.35
            angle = base_angle + twist
            z_dome = math.cos(t_norm * math.pi * 0.5) * 220.0
            px = OC_X + r_val * math.cos(angle)
            py_val = OC_Y + (r_val * 0.82) * math.sin(angle) - z_dome * 0.25
            GRID_PTS[fam_idx, s, r_idx] = [px, py_val]

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

    travel_theta = omega * tau + RND_LOAD_OFFSET
    sun_phi = omega * tau + RND_SUN_OFFSET

    # 1. Deep Structural Blueprint Slate Ground (#0a0e17)
    py5.background(10, 14, 23)

    # 2. Engineering Drafting Grid & Radial Graticule
    py5.stroke(20, 30, 48, 110)
    py5.stroke_weight(1.5)
    for x in range(120, WIDTH, 120):
        py5.line(x, 80, x, HEIGHT - 80)
    for y in range(120, HEIGHT, 120):
        py5.line(80, y, WIDTH - 80, y)

    # 3. Recessed Diamond Coffers (Cassettone Precast Concrete Pans)
    # 432 diamond units bounded by 2 rings and 2 intersecting spiral ribs
    for r_idx in range(NUM_RINGS - 1):
        for s in range(NUM_SPOKES):
            s_next = (s + 1) % NUM_SPOKES
            p_top = GRID_PTS[0, s, r_idx]
            p_right = GRID_PTS[1, s_next, r_idx]
            p_bot = GRID_PTS[0, s, r_idx + 1]
            p_left = GRID_PTS[1, s_next, r_idx + 1]

            cx = (p_top[0] + p_right[0] + p_bot[0] + p_left[0]) * 0.25
            cy = (p_top[1] + p_right[1] + p_bot[1] + p_left[1]) * 0.25
            ang_to_c = math.atan2(cy - OC_Y, cx - OC_X)

            # Sweeping sunbeam illumination calculation
            ang_diff = (ang_to_c - sun_phi + math.pi) % (2.0 * math.pi) - math.pi
            is_sunlit = max(0.0, math.cos(ang_diff)) ** 4 if abs(ang_diff) < 0.6 else 0.0

            r_c = int(18 + 15 * (r_idx / float(NUM_RINGS)) + 120 * is_sunlit)
            g_c = int(24 + 18 * (r_idx / float(NUM_RINGS)) + 110 * is_sunlit)
            b_c = int(36 + 22 * (r_idx / float(NUM_RINGS)) + 50 * is_sunlit)

            py5.fill(r_c, g_c, b_c, 210)
            py5.stroke(25, 38, 55, 140)
            py5.stroke_weight(1.5)
            py5.begin_shape()
            py5.vertex(p_top[0], p_top[1])
            py5.vertex(p_right[0], p_right[1])
            py5.vertex(p_bot[0], p_bot[1])
            py5.vertex(p_left[0], p_left[1])
            py5.end_shape(py5.CLOSE)

            # Specular sunlit bevel highlight
            if is_sunlit > 0.2:
                py5.stroke(254, 240, 138, int(170 * is_sunlit))
                py5.stroke_weight(2.0)
                py5.line(p_top[0], p_top[1], p_right[0], p_right[1])

    # 4. Concentric Circumferential Compression Rings
    for idx, r_val in enumerate(R_STEPS):
        ring_stress = 0.5 + 0.3 * math.sin(omega * tau + idx * 0.45)
        # Deep ferroconcrete shadow
        py5.no_fill()
        py5.stroke(6, 10, 16, 180)
        py5.stroke_weight(9.0 - idx * 0.3)
        py5.circle(OC_X, OC_Y + 4, r_val * 2)

        # Main ring rib
        py5.stroke(55, 75, 105, 180)
        py5.stroke_weight(7.0 - idx * 0.3)
        py5.circle(OC_X, OC_Y, r_val * 2)

        # Inner highlight edge
        py5.stroke(140, 175, 220, 140)
        py5.stroke_weight(2.0)
        py5.circle(OC_X, OC_Y, (r_val - 3.0) * 2)

    # 5. Intersecting Lamella Isostatic Ribs (Spiral Families)
    for fam_idx, family in enumerate([-1, 1]):
        for s in range(NUM_SPOKES):
            base_angle = (s / float(NUM_SPOKES)) * 2.0 * math.pi
            pts = []
            stresses = []
            for t_norm in T_VALS:
                r = R_OCULUS + (R_PERIMETER - R_OCULUS) * (t_norm ** 0.85)
                twist = family * (t_norm ** 0.72) * 1.35
                angle = base_angle + twist
                z_dome = math.cos(t_norm * math.pi * 0.5) * 220.0
                px = OC_X + r * math.cos(angle)
                py_val = OC_Y + (r * 0.82) * math.sin(angle) - z_dome * 0.25
                pts.append((px, py_val))

                dist_to_load = math.cos(angle - travel_theta)
                stress = 0.5 + 0.4 * dist_to_load * (t_norm ** 0.5)
                stresses.append(stress)

            # Drop shadow
            py5.stroke(6, 9, 14, 200)
            py5.stroke_weight(9.0)
            py5.no_fill()
            py5.begin_shape()
            for px, py_val in pts:
                py5.vertex(px + 4, py_val + 6)
            py5.end_shape()

            # Continuous gradient along rib (Compression Cobalt -> Neutral Slate -> Tension Amber)
            for j in range(len(pts) - 1):
                st = stresses[j]
                if st > 0.5:
                    blend = (st - 0.5) / 0.5
                    r_col = int(148 * (1 - blend) + 245 * blend)
                    g_col = int(163 * (1 - blend) + 158 * blend)
                    b_col = int(184 * (1 - blend) + 11 * blend)
                else:
                    blend = (0.5 - st) / 0.5
                    r_col = int(148 * (1 - blend) + 37 * blend)
                    g_col = int(163 * (1 - blend) + 99 * blend)
                    b_col = int(184 * (1 - blend) + 235 * blend)

                py5.stroke(r_col, g_col, b_col, 230)
                py5.stroke_weight(5.2)
                py5.line(pts[j][0], pts[j][1], pts[j+1][0], pts[j+1][1])

    # 6. Sweeping Volumetric Sunlight Shaft & Central Oculus
    py5.no_stroke()
    for beam_step in range(16):
        b_alpha = int(24 * (1.0 - beam_step / 16.0))
        py5.fill(254, 240, 138, b_alpha)
        py5.begin_shape()
        py5.vertex(OC_X, OC_Y)
        angle_1 = sun_phi - 0.50 - beam_step * 0.035
        angle_2 = sun_phi + 0.50 + beam_step * 0.035
        py5.vertex(OC_X + 1960 * math.cos(angle_1), OC_Y + 1640 * math.sin(angle_1))
        py5.vertex(OC_X + 1960 * math.cos(angle_2), OC_Y + 1640 * math.sin(angle_2))
        py5.end_shape(py5.CLOSE)

    # Oculus Compression Ring
    py5.stroke(245, 158, 11, 240)
    py5.stroke_weight(11.0)
    py5.no_fill()
    py5.circle(OC_X, OC_Y, R_OCULUS * 2)

    # Skylight Glazing Geodesic Spoke Web
    for spk in range(18):
        spk_ang = spk * (2.0 * math.pi / 18.0)
        py5.stroke(226, 232, 240, 210)
        py5.stroke_weight(3.2)
        py5.line(OC_X, OC_Y, OC_X + R_OCULUS * math.cos(spk_ang), OC_Y + R_OCULUS * math.sin(spk_ang))

    # Central Sun Core
    for cr in range(int(R_OCULUS * 0.8), 0, -6):
        py5.fill(255, 255, 250, int(220 * (1.0 - cr / (R_OCULUS * 0.8))))
        py5.no_stroke()
        py5.circle(OC_X, OC_Y, cr * 2)

    # 7. Exterior Inclined Y-Pylons / Buttress Piers (Cavalletti di sostegno)
    num_piers = 18
    for p_idx in range(num_piers):
        p_ang = p_idx * (2.0 * math.pi / num_piers)
        vx = OC_X + R_PERIMETER * math.cos(p_ang)
        vy = OC_Y + (R_PERIMETER * 0.82) * math.sin(p_ang)
        fx = OC_X + (R_PERIMETER + 320) * math.cos(p_ang)
        fy = OC_Y + ((R_PERIMETER + 320) * 0.82) * math.sin(p_ang) + 80
        
        # Pylon strut
        py5.stroke(203, 213, 225, 240)
        py5.stroke_weight(9.0)
        py5.line(vx, vy, (vx + fx) * 0.5, (vy + fy) * 0.5)
        py5.stroke_weight(7.0)
        py5.line((vx + fx) * 0.5, (vy + fy) * 0.5, fx - 32 * math.sin(p_ang), fy + 32 * math.cos(p_ang))
        py5.line((vx + fx) * 0.5, (vy + fy) * 0.5, fx + 32 * math.sin(p_ang), fy - 32 * math.cos(p_ang))
        
        # Foundation pad & tieback
        py5.stroke(245, 158, 11, 230)
        py5.stroke_weight(4.0)
        py5.circle(fx, fy, 28)

    # 8. Perimeter Radial Degree Markings
    for deg in range(0, 360, 15):
        d_rad = math.radians(deg)
        r1 = R_PERIMETER + 16
        r2 = R_PERIMETER + (36 if deg % 45 == 0 else 24)
        p1x = OC_X + r1 * math.cos(d_rad)
        p1y = OC_Y + (r1 * 0.82) * math.sin(d_rad)
        p2x = OC_X + r2 * math.cos(d_rad)
        p2y = OC_Y + (r2 * 0.82) * math.sin(d_rad)
        py5.stroke(148, 163, 184, 180)
        py5.stroke_weight(2.0 if deg % 45 != 0 else 3.5)
        py5.line(p1x, p1y, p2x, p2y)

    # 9. Four-Corner Structural Engineering Apparatuses
    # Corner 1 (Top-Left): Finite Element Principal Stress Trajectory Mohr's Circle
    c1_x, c1_y = 340, 320
    py5.fill(15, 22, 35, 215)
    py5.stroke(30, 45, 70)
    py5.stroke_weight(3.0)
    py5.rect(c1_x - 220, c1_y - 200, 440, 400)
    py5.fill(245, 158, 11)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(22)
    py5.text("ISOSTATIC STRESS TENSOR", c1_x - 196, c1_y - 176)
    py5.fill(148, 163, 184)
    py5.text_size(18)
    py5.text(f"SIGMA_1: {84.2 + 12.0 * math.sin(omega * tau):.1f} MPa", c1_x - 196, c1_y - 140)
    py5.text(f"SIGMA_2: {-32.6 + 6.0 * math.cos(omega * tau):.1f} MPa", c1_x - 196, c1_y - 108)
    py5.stroke(37, 99, 235, 200)
    py5.stroke_weight(3.0)
    py5.no_fill()
    py5.circle(c1_x, c1_y + 50, 160)
    py5.stroke(245, 158, 11)
    py5.line(c1_x - 110, c1_y + 50, c1_x + 110, c1_y + 50)
    py5.line(c1_x, c1_y - 60, c1_x, c1_y + 160)

    # Corner 2 (Top-Right): Catenary Thrust Arch Profile & Bending Moment Diagram
    c2_x, c2_y = WIDTH - 340, 320
    py5.fill(15, 22, 35, 215)
    py5.stroke(30, 45, 70)
    py5.stroke_weight(3.0)
    py5.rect(c2_x - 220, c2_y - 200, 440, 400)
    py5.fill(245, 158, 11)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(22)
    py5.text("THRUST LINE OF RESISTANCE", c2_x - 196, c2_y - 176)
    py5.stroke(148, 163, 184, 180)
    py5.stroke_weight(2.4)
    py5.no_fill()
    py5.begin_shape()
    for ax in np.linspace(-160, 160, 40):
        ay = (ax / 160.0) ** 2 * 120 - 40
        py5.vertex(c2_x + ax, c2_y + 80 + ay)
    py5.end_shape()
    py5.stroke(239, 68, 68, 220)
    py5.stroke_weight(3.6)
    py5.begin_shape()
    for ax in np.linspace(-160, 160, 40):
        my = math.sin(ax * 0.025 + omega * tau) * 36.0
        py5.vertex(c2_x + ax, c2_y + 80 + my)
    py5.end_shape()

    # Corner 3 (Bottom-Left): Live-Load Harmonic Seismograph & Modal Deflection
    c3_x, c3_y = 340, HEIGHT - 320
    py5.fill(15, 22, 35, 215)
    py5.stroke(30, 45, 70)
    py5.stroke_weight(3.0)
    py5.rect(c3_x - 220, c3_y - 200, 440, 400)
    py5.fill(245, 158, 11)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(22)
    py5.text("MODAL FREQUENCY SPECTRUM", c3_x - 196, c3_y - 176)
    py5.fill(148, 163, 184)
    py5.text_size(18)
    py5.text("F_01 = 1.48 Hz (RADIAL)", c3_x - 196, c3_y - 140)
    py5.text("F_02 = 2.74 Hz (TORSION)", c3_x - 196, c3_y - 108)
    py5.stroke(16, 185, 129, 220)
    py5.stroke_weight(3.0)
    py5.no_fill()
    py5.begin_shape()
    for wx in range(-180, 180, 8):
        wy = math.sin(wx * 0.06 - omega * tau * 2.0) * 32.0 + math.cos(wx * 0.03 + omega * tau) * 16.0
        py5.vertex(c3_x + wx, c3_y + 70 + wy)
    py5.end_shape()

    # Corner 4 (Bottom-Right): Ferrocemento Material Spec & Reinforcement Ratio
    c4_x, c4_y = WIDTH - 340, HEIGHT - 320
    py5.fill(15, 22, 35, 215)
    py5.stroke(30, 45, 70)
    py5.stroke_weight(3.0)
    py5.rect(c4_x - 220, c4_y - 200, 440, 400)
    py5.fill(245, 158, 11)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(22)
    py5.text("FERROCEMENTO SPECIFICATION", c4_x - 196, c4_y - 176)
    py5.fill(148, 163, 184)
    py5.text_size(18)
    py5.text("DENSE WIRE MESH LAYERS: 8", c4_x - 196, c4_y - 140)
    py5.text("MORTAR: 500 kg/m³ CEMENT", c4_x - 196, c4_y - 108)
    py5.text("THICKNESS: 25 mm TO 60 mm", c4_x - 196, c4_y - 76)
    py5.text("SPAN: 61.0 m (DIAMETER)", c4_x - 196, c4_y - 44)
    py5.stroke(75, 85, 105, 180)
    py5.stroke_weight(2.0)
    for gx in range(c4_x - 140, c4_x + 160, 30):
        py5.line(gx, c4_y + 20, gx, c4_y + 150)
    for gy in range(c4_y + 20, c4_y + 160, 30):
        py5.line(c4_x - 140, gy, c4_x + 140, gy)

    # 10. Monolithic Blueprint Outer Borders & Telemetry
    py5.no_fill()
    py5.stroke(50, 70, 100)
    py5.stroke_weight(4.0)
    py5.rect(60, 60, WIDTH - 120, HEIGHT - 120)
    py5.stroke(245, 158, 11, 140)
    py5.stroke_weight(2.0)
    py5.rect(72, 72, WIDTH - 144, HEIGHT - 144)

    # Header Title
    py5.fill(241, 245, 249)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(24)
    py5.text("STRUCTURAL ENGINEERING • ISOSTATIC FERROCONCRETE RIBBED VAULT", WIDTH / 2.0, 96)
    py5.text_size(38)
    py5.text("PIER LUIGI NERVI — ISOSTATIC LAMELLA CUPOLA KINEMATICS", WIDTH / 2.0, 136)
    py5.text_size(22)
    py5.fill(245, 158, 11)
    py5.text("PRINCIPAL STRESS TRAJECTORIES • OCULUS SUNLIGHT CONE • INCLINED Y-PYLON BUTTRESSES", WIDTH / 2.0, 186)

    # Bottom Telemetry
    py5.fill(148, 163, 184)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(22)
    py5.text("PALAZZETTO DELLO SPORT (1957) • SALONE AGNELLI (1948) • FERROCEMENTO PREFABRICATION", 108, HEIGHT - 92)
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text("4K GENERATIVE MEDIA ART • 12.0s ELASTIC HARMONIC CYCLE", WIDTH - 108, HEIGHT - 92)

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
