"""
kinetic_subpolar_auroral_geomagnetic_ribbons_2d
Autonomous Generative py5 Media Art Animation
Genre: Atmospheric / Painterly / Color Field
Theme: Polar Aurora Borealis & Birkeland Geomagnetic Current Curtains over Subarctic Fjord
12.0s Seamless Loop (720 frames @ 60 FPS, 4K Master)
Strictly Anonymous: Zero signatures, seals, monograms, initials, or personal marks.
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Display & Master Resolution
WIDTH, HEIGHT = 3840, 2160
TOTAL_FRAMES = 720
FPS = 60

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(WORK_DIR, "frames")
PREVIEW_PATH = os.path.join(WORK_DIR, "kinetic_subpolar_auroral_geomagnetic_ribbons_2d_p1.png")
OUTPUT_VIDEO = os.path.join(WORK_DIR, "kinetic_subpolar_auroral_geomagnetic_ribbons_2d.mp4")

# Geomagnetic Field Line Inclination (Magnetic Dip Angle ~ 78 degrees)
DIP_ANGLE = np.radians(78.0)
DX_PER_DY = 1.0 / np.tan(DIP_ANGLE)

# Fixed Starfield Distribution
STAR_RNG = np.random.RandomState(42)
N_STARS = 320
STAR_X = STAR_RNG.uniform(0, WIDTH, N_STARS)
STAR_Y = STAR_RNG.uniform(0, HEIGHT * 0.65, N_STARS)
STAR_SZ = STAR_RNG.uniform(1.2, 3.5, N_STARS)
STAR_BRIGHT = STAR_RNG.uniform(80, 250, N_STARS)

# Multi-Tier Auroral Drapery Curtains
CURTAINS = [
    {"base_y": HEIGHT * 0.34, "n_rays": 540, "h_min": 420, "h_max": 880, "freq": 1, "phase_off": 0.0},
    {"base_y": HEIGHT * 0.42, "n_rays": 580, "h_min": 480, "h_max": 960, "freq": -1, "phase_off": 1.7},
    {"base_y": HEIGHT * 0.49, "n_rays": 620, "h_min": 380, "h_max": 820, "freq": 2, "phase_off": 3.4},
    {"base_y": HEIGHT * 0.55, "n_rays": 640, "h_min": 320, "h_max": 760, "freq": -2, "phase_off": 5.1},
]

N_SEGS = 12
S_FRACS = np.linspace(0, 1, N_SEGS)

# Mountain Polygonal Profiles
M_PTS = 420
MX = np.linspace(-50, WIDTH + 50, M_PTS)

MY_DIST = HEIGHT * 0.66 - (
    170.0 * np.sin(MX * 0.0011 + 0.7)
    + 85.0 * np.cos(MX * 0.0026 - 0.4)
    + 40.0 * np.sin(MX * 0.0058 + 1.2)
)
POLY_DIST = [(0, HEIGHT), (0, MY_DIST[0])]
for px, py in zip(MX, MY_DIST):
    POLY_DIST.append((px, py))
POLY_DIST.append((WIDTH, MY_DIST[-1]))
POLY_DIST.append((WIDTH, HEIGHT))
POLY_DIST = np.array(POLY_DIST)

MY_MID = HEIGHT * 0.71 - (
    220.0 * np.sin(MX * 0.0015 + 1.4)
    + 110.0 * np.cos(MX * 0.0032 - 0.9)
    + 60.0 * np.abs(np.sin(MX * 0.0075 + 0.3))
)
POLY_MID = [(0, HEIGHT), (0, MY_MID[0])]
for px, py in zip(MX, MY_MID):
    POLY_MID.append((px, py))
POLY_MID.append((WIDTH, MY_MID[-1]))
POLY_MID.append((WIDTH, HEIGHT))
POLY_MID = np.array(POLY_MID)

MY_FG = HEIGHT * 0.76 - (
    260.0 * np.sin(MX * 0.0017 + 0.2)
    + 130.0 * np.cos(MX * 0.0036 - 1.1)
    + 55.0 * np.sin(MX * 0.0084 + 0.8)
    + 30.0 * np.abs(np.sin(MX * 0.016))
)
POLY_FG = [(0, HEIGHT), (0, MY_FG[0])]
for px, py in zip(MX, MY_FG):
    POLY_FG.append((px, py))
POLY_FG.append((WIDTH, MY_FG[-1]))
POLY_FG.append((WIDTH, HEIGHT))
POLY_FG = np.array(POLY_FG)
FROST_CREST = np.column_stack([MX, MY_FG])

WATER_LEVEL = HEIGHT * 0.825


def setup():
    py5.size(WIDTH, HEIGHT)
    os.makedirs(FRAMES_DIR, exist_ok=True)


def draw():
    frame = py5.frame_count
    if frame > TOTAL_FRAMES:
        finish_render()
        return

    t_norm = (frame - 1) / TOTAL_FRAMES
    tau = 2.0 * np.pi * t_norm

    # 1. High-Latitude Cosmic Polar Night Background & Sky Wash
    py5.background(2, 4, 10)
    py5.no_stroke()
    for y in range(0, int(HEIGHT * 0.76), 12):
        frac = y / (HEIGHT * 0.76)
        r = int(2 + 6 * (frac ** 1.5))
        g = int(4 + 24 * (frac ** 1.5))
        b = int(10 + 32 * (frac ** 1.5))
        py5.fill(r, g, b, 255)
        py5.rect(0, y, WIDTH, 12)

    # 2. Celestial Distant Polar Stars
    py5.no_stroke()
    for sx, sy, ssz, sb in zip(STAR_X, STAR_Y, STAR_SZ, STAR_BRIGHT):
        py5.fill(210, 235, 255, int(sb * 0.35))
        py5.ellipse(sx, sy, ssz * 3.8, ssz * 3.8)
        py5.fill(255, 255, 255, int(sb))
        py5.ellipse(sx, sy, ssz, ssz)

    # 3. Multi-Tier Volumetric Auroral Drapery Curtains
    for c in CURTAINS:
        n_rays = c["n_rays"]
        xs = np.linspace(-150, WIDTH + 150, n_rays)
        phase = tau * c["freq"] + c["phase_off"]
        w1 = 180.0 * np.sin(xs * 0.0013 + phase)
        w2 = 75.0 * np.cos(xs * 0.0029 - phase * 1.5)
        w3 = 35.0 * np.sin(xs * 0.0062 + phase * 2.0)
        base_curve = c["base_y"] + w1 + w2 + w3

        slope = np.gradient(base_curve, xs)
        fold_density = 1.0 / (1.0 + np.abs(slope) * 2.5)
        ray_h = c["h_min"] + (c["h_max"] - c["h_min"]) * (
            0.5 + 0.5 * np.sin(xs * 0.0021 + phase * 0.8)
        ) * (0.65 + 0.7 * fold_density)

        # Diffuse ray wash (subsampled for soft background glow)
        sub = 3
        d_x0 = xs[::sub]
        d_y0 = base_curve[::sub]
        d_h = ray_h[::sub]
        d_x1 = d_x0 + d_h * DX_PER_DY
        d_y1 = d_y0 - d_h
        lines_diff = np.column_stack([d_x0, d_y0, d_x1, d_y1])
        py5.stroke(24, 190, 85, 22)
        py5.stroke_weight(18.0)
        py5.lines(lines_diff)

        # Segmented ray streamers along magnetic dip angle
        for s in range(N_SEGS - 1):
            f0 = S_FRACS[s]
            f1 = S_FRACS[s + 1]
            frac_alt = s / (N_SEGS - 1)

            x0 = xs + (f0 * ray_h) * DX_PER_DY
            y0 = base_curve - f0 * ray_h
            x1 = xs + (f1 * ray_h) * DX_PER_DY
            y1 = base_curve - f1 * ray_h
            lines_seg = np.column_stack([x0, y0, x1, y1])

            if frac_alt < 0.22:
                r = int(34 + 175 * (1.0 - frac_alt * 4.5))
                g = int(225 + 30 * (1.0 - frac_alt * 4.5))
                b = int(95 + 110 * (1.0 - frac_alt * 4.5))
                a = 48
                w = 5.2
            elif frac_alt < 0.62:
                f = (frac_alt - 0.22) / 0.40
                r = int(6 * (1 - f) + 85 * f)
                g = int(190 * (1 - f) + 110 * f)
                b = int(220 * (1 - f) + 245 * f)
                a = 38
                w = 4.0
            else:
                f = (frac_alt - 0.62) / 0.38
                r = int(85 * (1 - f) + 235 * f)
                g = int(110 * (1 - f) + 38 * f)
                b = int(245 * (1 - f) + 85 * f)
                a = 28
                w = 3.0

            py5.stroke(r, g, b, a)
            py5.stroke_weight(w)
            py5.lines(lines_seg)

        # Bottom curtain edge: radiant neon fold filament
        pts = np.column_stack([xs, base_curve])
        py5.no_fill()
        py5.stroke(34, 220, 95, 75)
        py5.stroke_weight(14.0)
        py5.begin_shape()
        py5.vertices(pts)
        py5.end_shape()

        py5.stroke(215, 255, 230, 200)
        py5.stroke_weight(2.6)
        py5.begin_shape()
        py5.vertices(pts)
        py5.end_shape()

    # 4. Distant Mountain Silhouette
    py5.fill(4, 9, 20, 215)
    py5.no_stroke()
    py5.begin_shape()
    py5.vertices(POLY_DIST)
    py5.end_shape(py5.CLOSE)

    # 5. Mid-Range Horn Peaks
    py5.fill(3, 6, 14, 240)
    py5.no_stroke()
    py5.begin_shape()
    py5.vertices(POLY_MID)
    py5.end_shape(py5.CLOSE)

    # 6. Foreground Basalt Fjord Mountain Ridges
    py5.fill(2, 3, 7, 255)
    py5.no_stroke()
    py5.begin_shape()
    py5.vertices(POLY_FG)
    py5.end_shape(py5.CLOSE)

    # Snow ridge frost highlights catching auroral emerald light
    py5.no_fill()
    py5.stroke(110, 231, 183, 130)
    py5.stroke_weight(2.4)
    py5.begin_shape()
    py5.vertices(FROST_CREST)
    py5.end_shape()

    # 7. Fjord Glacial Mirror Water & Sinuous Aurora Reflections
    py5.fill(2, 4, 9, 245)
    py5.no_stroke()
    py5.rect(0, WATER_LEVEL, WIDTH, HEIGHT - WATER_LEVEL)

    for wy in range(int(WATER_LEVEL), HEIGHT, 5):
        frac_w = (wy - WATER_LEVEL) / (HEIGHT - WATER_LEVEL)
        wave_dx = 38.0 * np.sin(tau * 3.0 + wy * 0.038)
        alpha_refl = int(45 * (1.0 - frac_w * 0.82))

        py5.stroke(34, 197, 94, alpha_refl)
        py5.stroke_weight(2.6)
        py5.line(wave_dx, wy, WIDTH + wave_dx, wy)

        if wy % 10 == 0:
            py5.stroke(6, 182, 212, int(alpha_refl * 0.85))
            py5.stroke_weight(2.0)
            py5.line(-wave_dx * 0.6, wy + 2, WIDTH - wave_dx * 0.6, wy + 2)

        if wy % 15 == 0:
            py5.stroke(192, 132, 252, int(alpha_refl * 0.5))
            py5.stroke_weight(1.8)
            py5.line(wave_dx * 0.4, wy + 3, WIDTH + wave_dx * 0.4, wy + 3)

    # Save preview image on frame 1
    if frame == 1:
        py5.save(PREVIEW_PATH)

    # Save frame for video
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save(frame_path)

    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        print(f"Rendered frame {frame}/{TOTAL_FRAMES} ({(frame/TOTAL_FRAMES)*100:.1f}%)")


def finish_render():
    py5.no_loop()
    print("All frames rendered. Compiling video with ffmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        OUTPUT_VIDEO
    ]
    subprocess.run(cmd, check=True)
    print(f"Master MP4 video compiled: {OUTPUT_VIDEO}")

    # Clean up frames directory
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    print("Temporary frames directory cleaned up.")
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()
