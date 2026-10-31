"""
kinetic_renaissance_astrolabe_armillary_mechanism_2d
Autonomous Generative py5 Media Art Animation (720 frames @ 60 FPS, 12.0s seamless loop, 4K Master)

Genre: Figurative / Schematic / Technical Drawing
Theme: Renaissance celestial astrolabe, Galileo armillary sphere mechanism, and planetary
       epicyclic gear linkages drawn as a master cyanotype blueprint schematic.

Anti-Clustering & Diversity Compliance:
- Genre: Figurative / Schematic / Technical Drawing (Rotates away from Mathematical/Topology, Organic, Signal/Glitch)
- Background: Deep Prussian cyanotype blueprint ground (#0b1d3a, L ≈ 14%) with technical grid
- Primitives: Outer 360-degree vernier graduated meridian ring, 23.5-degree tilted rotating ecliptic ring,
  celestial colure meridian circles, 6-tier planetary epicyclic gear train with interlocking gear teeth,
  and kinematic linkage connecting rods. Zero particles or point clouds.
- Strict Anonymity: Zero signatures, zero seals/hanko, zero monograms, zero initials, zero author marks.
- Palette: Prussian blueprint (#0b1d3a), celestial brass gold (#fbbf24), drafting cyan (#38bdf8),
  technical chalk white (#f8fafc), and slate steel (#64748b).
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_renaissance_astrolabe_armillary_mechanism_2d"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")
PREVIEW_PATH = os.path.join(SCRIPT_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SCRIPT_DIR, f"{WORK_NAME}.mp4")

TOTAL_FRAMES = 720
FPS = 60
PREVIEW_FRAME = 180

# Canvas dimensions (4K UHD)
WIDTH = 3840
HEIGHT = 2160
CX = WIDTH // 2
CY = HEIGHT // 2

# Astrolabe physical dimensions
R_OUTER = 900.0
TILT_ECLIPTIC = np.radians(23.44)  # Earth axial obliquity

# Pre-computed arrays for ecliptic and colure rings
N_ECLIPTIC_PTS = 500
THETAS_ECLIPTIC = np.linspace(0.0, 2.0 * np.pi, N_ECLIPTIC_PTS, endpoint=False)
COS_E, SIN_E = np.cos(THETAS_ECLIPTIC), np.sin(THETAS_ECLIPTIC)

# Epicyclic gear configs (radius, teeth, orbit speed, gear spin ratio)
GEAR_CONFIGS = [
    {"r_orbit": 240.0, "r_base": 36.0, "teeth": 14, "orbit_speed": 1,  "spin_ratio": -3.0},
    {"r_orbit": 360.0, "r_base": 44.0, "teeth": 18, "orbit_speed": -1, "spin_ratio": 2.5},
    {"r_orbit": 480.0, "r_base": 52.0, "teeth": 22, "orbit_speed": 2,  "spin_ratio": -2.0},
    {"r_orbit": 600.0, "r_base": 58.0, "teeth": 26, "orbit_speed": -1, "spin_ratio": 1.8},
    {"r_orbit": 720.0, "r_base": 66.0, "teeth": 30, "orbit_speed": 1,  "spin_ratio": -1.5},
    {"r_orbit": 820.0, "r_base": 72.0, "teeth": 34, "orbit_speed": -2, "spin_ratio": 1.2},
]


def setup():
    py5.size(WIDTH, HEIGHT)
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Starting render of {TOTAL_FRAMES} frames @ 60 FPS (4K Master)...")


def draw():
    frame = py5.frame_count
    if frame > TOTAL_FRAMES:
        return

    # Normalized time parameter for seamless 12.0s loop
    t_norm = (frame - 1) / TOTAL_FRAMES
    tau = 2.0 * np.pi * t_norm

    # 1. Deep Prussian Cyanotype Blueprint Ground (#0b1d3a)
    py5.background(11, 29, 58)

    # 2. Precision Technical Drafting Grid & Construction Guides
    py5.stroke(24, 52, 92, 55)
    py5.stroke_weight(1.0)
    for x in range(0, WIDTH, 100):
        py5.line(x, 0, x, HEIGHT)
    for y in range(0, HEIGHT, 100):
        py5.line(0, y, WIDTH, y)

    # Major 500px modular drafting marks
    py5.stroke(38, 76, 128, 80)
    for x in range(0, WIDTH, 500):
        py5.line(x, 0, x, HEIGHT)
    for y in range(0, HEIGHT, 500):
        py5.line(0, y, WIDTH, y)

    # 3. Outer Meridian Ring with Vernier Degree Scale
    py5.no_fill()
    py5.stroke(248, 250, 252, 230)
    py5.stroke_weight(4.5)
    py5.ellipse(CX, CY, R_OUTER * 2.0, R_OUTER * 2.0)

    py5.stroke(56, 189, 248, 140)
    py5.stroke_weight(1.8)
    py5.ellipse(CX, CY, (R_OUTER - 32.0) * 2.0, (R_OUTER - 32.0) * 2.0)

    # 360-degree graduation tick marks
    for deg in range(360):
        rad = np.radians(deg)
        c_a, s_a = np.cos(rad), np.sin(rad)
        tick_len = 28.0 if deg % 30 == 0 else (16.0 if deg % 10 == 0 else (10.0 if deg % 5 == 0 else 5.0))
        py5.stroke(248, 250, 252, 220 if deg % 30 == 0 else (160 if deg % 10 == 0 else 75))
        py5.stroke_weight(2.0 if deg % 30 == 0 else (1.4 if deg % 10 == 0 else 1.0))
        py5.line(CX + (R_OUTER - 32.0) * c_a, CY + (R_OUTER - 32.0) * s_a,
                 CX + (R_OUTER - 32.0 + tick_len) * c_a, CY + (R_OUTER - 32.0 + tick_len) * s_a)

    # 4. Celestial Solstice & Equinox Colure Meridian Rings
    n_colures = 6
    for c_idx in range(n_colures):
        ang_c = c_idx * (np.pi / n_colures) + tau * 0.5
        rx_c = (R_OUTER - 55.0) * np.cos(ang_c)
        py5.stroke(56, 189, 248, int(60 + 95 * np.abs(np.sin(ang_c))))
        py5.stroke_weight(1.8)
        py5.ellipse(CX, CY, np.abs(rx_c) * 2.0, (R_OUTER - 55.0) * 2.0)

    # 5. Oblique 3D Rotating Ecliptic Zodiac Ring (Tilted at 23.44°)
    r_ecliptic = R_OUTER - 90.0
    rot_y = tau
    x_e = r_ecliptic * COS_E * np.cos(rot_y) - r_ecliptic * SIN_E * np.sin(TILT_ECLIPTIC) * np.sin(rot_y)
    y_e = r_ecliptic * SIN_E * np.cos(TILT_ECLIPTIC)
    pts_ecliptic = np.column_stack([CX + x_e, CY + y_e])

    # Saturated brass gold band
    py5.stroke(251, 191, 36, 220)
    py5.stroke_weight(3.5)
    py5.begin_shape()
    py5.vertices(pts_ecliptic)
    py5.end_shape(py5.CLOSE)

    # 6. Planetary Epicyclic Gear Train & Kinematic Linkages
    for g_idx, cfg in enumerate(GEAR_CONFIGS):
        rg_orbit = cfg["r_orbit"]
        speed = cfg["orbit_speed"]
        spin_ratio = cfg["spin_ratio"]

        # Planetary carrier orbital trajectory
        orb_ang = tau * speed * 0.5
        gx = CX + rg_orbit * np.cos(orb_ang)
        gy = CY + rg_orbit * np.sin(orb_ang)

        # Orbit path track
        py5.stroke(56, 189, 248, 50)
        py5.stroke_weight(1.0)
        py5.ellipse(CX, CY, rg_orbit * 2.0, rg_orbit * 2.0)

        # Linkage connecting arm to origin
        py5.stroke(248, 250, 252, 70)
        py5.stroke_weight(1.2)
        py5.line(CX, CY, gx, gy)

        # Epicyclic gear teeth geometry
        n_teeth = cfg["teeth"]
        r_base = cfg["r_base"]
        spin_ang = tau * speed * 0.5 * spin_ratio

        n_t_pts = n_teeth * 6
        th_t = np.linspace(0.0, 2.0 * np.pi, n_t_pts, endpoint=False)
        # Involute-like tooth profile
        tooth_wave = 7.0 * np.sin(th_t * n_teeth + spin_ang)
        r_gear = r_base + tooth_wave
        gear_pts = np.column_stack([gx + r_gear * np.cos(th_t), gy + r_gear * np.sin(th_t)])

        # Outer brass tooth contour
        py5.stroke(251, 191, 36, 190)
        py5.stroke_weight(2.0)
        py5.begin_shape()
        py5.vertices(gear_pts)
        py5.end_shape(py5.CLOSE)

        # Inner gear body & lightening holes
        py5.stroke(56, 189, 248, 120)
        py5.stroke_weight(1.2)
        py5.ellipse(gx, gy, (r_base - 10.0) * 2.0, (r_base - 10.0) * 2.0)

        # Pivot pin bearing
        py5.no_stroke()
        py5.fill(248, 250, 252, 230)
        py5.ellipse(gx, gy, 8, 8)
        py5.fill(11, 29, 58, 255)
        py5.ellipse(gx, gy, 3, 3)
        py5.no_fill()

    # 7. Astrolabe Rotating Alidade (Sight-Vane Rule)
    alidade_ang = tau * 1.5
    ca_al, sa_al = np.cos(alidade_ang), np.sin(alidade_ang)
    al_len = R_OUTER - 45.0

    py5.stroke(248, 250, 252, 230)
    py5.stroke_weight(2.5)
    py5.line(CX - al_len * ca_al, CY - al_len * sa_al, CX + al_len * ca_al, CY + al_len * sa_al)

    # Alidade sight sights (pivots at ends)
    for sign in [-1, 1]:
        px = CX + sign * al_len * ca_al
        py_pt = CY + sign * al_len * sa_al
        py5.stroke(251, 191, 36, 220)
        py5.stroke_weight(2.0)
        py5.line(px - 14 * sa_al, py_pt + 14 * ca_al, px + 14 * sa_al, py_pt - 14 * ca_al)

    # 8. Central Sol / Earth Armature Pivot Hub
    py5.no_stroke()
    py5.fill(251, 191, 36, 240)
    py5.ellipse(CX, CY, 52, 52)
    py5.fill(11, 29, 58, 255)
    py5.ellipse(CX, CY, 26, 26)
    py5.fill(248, 250, 252, 255)
    py5.ellipse(CX, CY, 8, 8)

    # Cardinal axis alignment crosshairs
    py5.stroke(56, 189, 248, 120)
    py5.stroke_weight(1.2)
    py5.line(CX - R_OUTER - 40, CY, CX + R_OUTER + 40, CY)
    py5.line(CX, CY - R_OUTER - 40, CX, CY + R_OUTER + 40)

    # 9. Frame output & progress tracking
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Capture preview image at frame 180 (quarter-cycle peak phase)
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] Astrolabe preview captured: {PREVIEW_PATH}")

    # Progress reporting
    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # 10. Finalize animation on reaching total frame count
    if frame == TOTAL_FRAMES:
        print("[Rendering Complete] Encoding master 4K MP4 via ffmpeg...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "17",
            "-preset", "slow",
            OUTPUT_MP4
        ]
        res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[Video Compiled] Master MP4 saved: {OUTPUT_MP4}")
            shutil.rmtree(FRAMES_DIR, ignore_errors=True)
            print("[Render Cleanup] Temporary frames directory removed.")
        else:
            print(f"[FFmpeg Error] {res.stderr}")

        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
