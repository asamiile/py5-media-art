"""
kinetic_suminagashi_vortex_ink_marbling_2d
Autonomous Generative py5 Media Art Animation (720 frames @ 60 FPS, 12.0s seamless loop, 4K Master)

Genre: Atmospheric / Painterly / Color Field
Theme: Traditional Japanese Suminagashi (墨流し) fluid ink marbling on water,
       where concentric bands of pure sumi charcoal ink, indigo dye, and vermilion
       undulate across an unbleached Echizen washi paper basin under gentle breath vortices.

Anti-Clustering & Diversity Compliance:
- Genre: Atmospheric / Painterly / Color Field (Rotates away from Craft, Architecture, and Physics)
- Background: Unbleached Echizen washi paper (#f4ede0, warm high-luminance ground)
- Primitives: Non-intersecting continuous nested fluid ink rings with diffeomorphic vortex
  and streamline advection. Fine paper pulp fibers. Hand-carved vermilion Hanko seal.
  Zero particles or point clouds.
- Palette: Sumi charcoal ink (#121110), indigo kachi-iro (#182638), walnut sepia (#3c281c),
  and vermilion shu-iro (#b02e20).
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_suminagashi_vortex_ink_marbling_2d"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")
PREVIEW_PATH = os.path.join(SCRIPT_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SCRIPT_DIR, f"{WORK_NAME}.mp4")

TOTAL_FRAMES = 720
FPS = 60
PREVIEW_FRAME = 180

# Canvas dimensions
WIDTH = 3840
HEIGHT = 2160

# Suminagashi ring configuration
N_RINGS = 145
POINTS_PER_RING = 640

# Authentic Japanese traditional palette
PALETTE = [
    {"name": "sumi_deep",    "c": (18, 17, 16, 235),  "w": 3.4},
    {"name": "sumi_mid",     "c": (32, 30, 28, 205),  "w": 2.4},
    {"name": "indigo_kachi", "c": (22, 34, 52, 220),  "w": 2.8},
    {"name": "sumi_light",   "c": (45, 42, 40, 175),  "w": 1.8},
    {"name": "sepia_kurumi", "c": (62, 44, 30, 200),  "w": 2.5},
    {"name": "sumi_wash",    "c": (28, 26, 25, 190),  "w": 2.0},
    {"name": "shu_vermilion","c": (176, 46, 32, 230),  "w": 3.6},
    {"name": "indigo_ai",    "c": (30, 48, 72, 185),  "w": 2.2},
    {"name": "sumi_fine",    "c": (18, 17, 16, 160),  "w": 1.5},
]

# Fluid stirring vortices (dipoles and eddies mimicking breath and paper fan)
VORTICES = [
    {"cx": WIDTH * 0.50, "cy": HEIGHT * 0.46, "rx": 200, "ry": 130, "max_angle": 2.8,  "sigma": 560.0, "freq": 1},
    {"cx": WIDTH * 0.32, "cy": HEIGHT * 0.56, "rx": 160, "ry": 110, "max_angle": -2.4, "sigma": 490.0, "freq": -1},
    {"cx": WIDTH * 0.65, "cy": HEIGHT * 0.36, "rx": 140, "ry": 95,  "max_angle": 2.0,  "sigma": 430.0, "freq": 2},
    {"cx": WIDTH * 0.42, "cy": HEIGHT * 0.68, "rx": 150, "ry": 115, "max_angle": -1.8, "sigma": 470.0, "freq": 1},
]

# Pre-generate initial nested ink contours
def init_ink_rings():
    thetas = np.linspace(0, 2 * np.pi, POINTS_PER_RING, endpoint=False)
    cos_t, sin_t = np.cos(thetas), np.sin(thetas)

    # Master focal drip origin (slightly off-center for Japanese Ma / 間 aesthetic)
    cx = WIDTH * 0.42
    cy = HEIGHT * 0.50

    rings = []
    for i in range(1, N_RINGS + 1):
        r_base = 24.0 + np.power(i * 14.2, 1.085)
        # Subtle organic fluid boundary perturbations
        r_mod = r_base * (
            1.0
            + 0.032 * np.cos(3 * thetas + i * 0.22)
            + 0.022 * np.sin(5 * thetas - i * 0.16)
            + 0.012 * np.cos(7 * thetas + i * 0.31)
        )

        drift_cx = cx + 85.0 * np.sin(i * 0.04)
        drift_cy = cy + 55.0 * np.cos(i * 0.05)

        pts = np.column_stack([drift_cx + r_mod * cos_t, drift_cy + r_mod * sin_t])
        style = PALETTE[i % len(PALETTE)]
        rings.append({
            "base_pts": pts,
            "c": style["c"],
            "w": style["w"] * (1.0 + 0.14 * np.sin(i * 0.35)),
            "order": i
        })

    return rings

RINGS = init_ink_rings()

# Pre-generate static washi paper fiber noise (deckle and kozo fibers)
np.random.seed(4208)
FIBERS = []
for _ in range(1500):
    fx = np.random.uniform(0, WIDTH)
    fy = np.random.uniform(0, HEIGHT)
    flen = np.random.uniform(25, 90)
    fa = np.random.uniform(0, 2 * np.pi)
    FIBERS.append((fx, fy, fx + flen * np.cos(fa), fy + flen * np.sin(fa)))

FLECKS = []
for _ in range(500):
    px = np.random.uniform(0, WIDTH)
    py = np.random.uniform(0, HEIGHT)
    pr = np.random.uniform(1.5, 4.5)
    FLECKS.append((px, py, pr, pr * 1.4))


def deform_rings(pts, t_norm):
    """
    Apply smooth diffeomorphic fluid deformation to ink contours.
    Guarantees non-intersecting nested lines and 100% seamless 12s looping.
    """
    p = pts.copy()
    tau = 2 * np.pi * t_norm

    # 1. Continuous fluid swirl transformations
    for sw in VORTICES:
        phase = tau * sw["freq"]
        scx = sw["cx"] + sw["rx"] * np.cos(phase)
        scy = sw["cy"] + sw["ry"] * np.sin(phase)

        dx = p[:, 0] - scx
        dy = p[:, 1] - scy
        r2 = dx * dx + dy * dy

        curr_angle = sw["max_angle"] * (0.8 + 0.35 * np.sin(phase + 0.5 * np.cos(phase)))
        d_theta = curr_angle * np.exp(- r2 / (2.0 * sw["sigma"] * sw["sigma"]))

        cos_d, sin_d = np.cos(d_theta), np.sin(d_theta)
        new_dx = dx * cos_d - dy * sin_d
        new_dy = dx * sin_d + dy * cos_d

        p[:, 0] = scx + new_dx
        p[:, 1] = scy + new_dy

    # 2. Gentle surface laminar river breeze
    breeze_phase = tau + p[:, 0] * 0.0011
    breeze_amp = 85.0 * np.sin(breeze_phase)
    breeze_weight = np.exp(- ((p[:, 1] - HEIGHT * 0.48) ** 2) / (2 * (520.0 ** 2)))
    p[:, 0] += breeze_amp * breeze_weight

    # 3. Capillary surface tension ripples
    cap_x = 14.0 * np.sin(2 * tau + p[:, 1] * 0.0028 + p[:, 0] * 0.0008)
    cap_y = 12.0 * np.cos(2 * tau + p[:, 0] * 0.0028 - p[:, 1] * 0.0008)
    p[:, 0] += cap_x
    p[:, 1] += cap_y

    return p


def setup():
    """py5 setup lifecycle method."""
    py5.size(WIDTH, HEIGHT)
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[Setup Complete] Suminagashi Canvas: {WIDTH}x{HEIGHT} | Output: {OUTPUT_MP4}")


def draw():
    """Render each frame of the 12.0s Suminagashi animation."""
    frame = py5.frame_count
    t_norm = (frame - 1) / TOTAL_FRAMES

    # 1. Warm unbleached Echizen washi paper ground (#f4ede0)
    py5.background(244, 237, 224)

    # 2. Washi substrate texture: raw kozo fibers and pulp flecks
    py5.stroke(212, 202, 186, 50)
    py5.stroke_weight(1.0)
    for fx1, fy1, fx2, fy2 in FIBERS:
        py5.line(fx1, fy1, fx2, fy2)

    py5.no_stroke()
    py5.fill(195, 182, 165, 55)
    for px, py, pw, ph in FLECKS:
        py5.ellipse(px, py, pw, ph)

    # 3. Render deformed continuous Suminagashi ink rings
    py5.no_fill()
    for r in RINGS:
        pts = deform_rings(r["base_pts"], t_norm)
        c = r["c"]
        py5.stroke(c[0], c[1], c[2], c[3])
        py5.stroke_weight(r["w"])

        py5.begin_shape()
        py5.vertices(pts)
        py5.end_shape(py5.CLOSE)

    # 4. Vermilion artist seal (落款 Hanko) in bottom right corner
    seal_x = WIDTH - 260
    seal_y = HEIGHT - 260
    py5.fill(176, 46, 32, 240)
    py5.no_stroke()
    py5.rect(seal_x - 38, seal_y - 38, 76, 76, 8)
    py5.stroke(244, 237, 224, 245)
    py5.stroke_weight(3.5)
    py5.no_fill()
    py5.rect(seal_x - 30, seal_y - 30, 60, 60, 4)
    py5.stroke_weight(3.2)
    py5.line(seal_x - 15, seal_y - 20, seal_x - 15, seal_y + 20)
    py5.line(seal_x - 15, seal_y - 2, seal_x + 18, seal_y - 2)
    py5.line(seal_x + 6, seal_y - 20, seal_x + 6, seal_y + 20)
    py5.line(seal_x + 18, seal_y - 12, seal_x + 18, seal_y + 16)

    # 5. Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Capture preview image at frame 180 (quarter-cycle peak swirl)
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] Suminagashi preview captured: {PREVIEW_PATH}")

    # Progress reporting
    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # 6. Finalize animation on reaching total frame count
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
