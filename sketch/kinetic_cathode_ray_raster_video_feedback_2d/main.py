"""
kinetic_cathode_ray_raster_video_feedback_2d
Autonomous Generative py5 Media Art Animation (720 frames @ 60 FPS, 12.0s seamless loop, 4K Master)

Genre: Signal / Glitch / Digital Artifacts
Theme: Analogue Cathode Ray Tube (CRT) video synthesizer with recursive optical feedback loop,
       multi-harmonic Lissajous beam deflection, RGB chromatic aberration shears,
       horizontal sync glitch tearing, and P22 phosphor persistence glow.

Anti-Clustering & Diversity Compliance:
- Genre: Signal / Glitch / Digital Artifacts (Rotates away from Atmospheric/Painterly, Textile/Craft, Architecture)
- Background: Deep CRT cathode ray chassis black (#08080b, luminance ~3%)
- Primitives: Recursive nested raster feedback tunnels, vector oscilloscope Harmonograph curves,
  horizontal sync glitch tear slices, shadow mask scanline grilles, and vintage OSD telemetry HUD.
  Zero particles or point clouds.
- Palette: CRT black (#08080b), P22 phosphor green (#22c55e), oscilloscope cyan (#06b6d4),
  beam trace magenta (#f43f5e), amber lock (#fbbf24), and electron core white (#ffffff).
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_cathode_ray_raster_video_feedback_2d"
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

# Harmonograph Lissajous curve configuration
N_L_PTS = 1200
THETAS = np.linspace(0, 2 * np.pi, N_L_PTS, endpoint=False)

HARM_CONFIGS = [
    {"fx": 3.0, "fy": 4.0, "p_speed": 1, "scale": 1.00, "c": (34, 197, 94)},   # Phosphor green
    {"fx": 5.0, "fy": 6.0, "p_speed": 2, "scale": 0.78, "c": (6, 182, 212)},   # Oscilloscope cyan
    {"fx": 2.0, "fy": 3.0, "p_speed": -1, "scale": 0.58, "c": (244, 63, 94)},  # Beam trace magenta
    {"fx": 7.0, "fy": 5.0, "p_speed": 1, "scale": 0.38, "c": (251, 191, 36)},  # Amber lock
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

    # 1. Dark CRT cathode ray chassis ground
    py5.background(8, 8, 11)

    # 2. Dynamic Moiré Grating Interference Field (two counter-modulating line arrays)
    n_moire = 128
    py5.stroke(14, 45, 55, 38)
    py5.stroke_weight(1.5)
    for m in range(n_moire):
        frac_m = m / n_moire
        y_m = HEIGHT * frac_m
        w1 = 45.0 * np.sin(tau + frac_m * 18.0)
        py5.line(0, y_m + w1, WIDTH, y_m - w1)

    py5.stroke(55, 18, 42, 38)
    for m in range(n_moire):
        frac_m = m / n_moire
        x_m = WIDTH * frac_m
        w2 = 50.0 * np.cos(tau * 2.0 + frac_m * 14.0)
        py5.line(x_m + w2, 0, x_m - w2, HEIGHT)

    # 3. Recursive Video Feedback Tunnel (46 recursive depth planes)
    n_feedback = 46
    py5.no_fill()
    for fb in range(n_feedback, 0, -1):
        frac = fb / n_feedback
        fb_phase = tau + frac * np.pi * 3.5
        scale = np.power(frac, 1.25)
        fw = (WIDTH - 480) * scale
        fh = (HEIGHT - 360) * scale
        corner_r = 38 * scale

        # Lissajous feedback focal drift
        fb_cx = CX + 180.0 * np.sin(fb_phase * 2.0) * (1.0 - frac)
        fb_cy = CY + 110.0 * np.cos(fb_phase * 3.0) * (1.0 - frac)
        rot_angle = np.sin(fb_phase) * 0.42 * (1.0 - frac)

        py5.push_matrix()
        py5.translate(fb_cx, fb_cy)
        py5.rotate(rot_angle)

        chroma_offset = 9.0 * (1.0 - frac)

        # Red / Magenta chromatic channel
        py5.stroke(244, 63, 94, int(30 + frac * 150))
        py5.stroke_weight(2.4 + frac * 4.6)
        py5.rect(-fw * 0.5 - chroma_offset, -fh * 0.5, fw, fh, corner_r)

        # Cyan / Blue chromatic channel
        py5.stroke(6, 182, 212, int(30 + frac * 150))
        py5.stroke_weight(2.4 + frac * 4.6)
        py5.rect(-fw * 0.5 + chroma_offset, -fh * 0.5, fw, fh, corner_r)

        # Core Phosphor Green channel
        py5.stroke(34, 197, 94, int(45 + frac * 170))
        py5.stroke_weight(1.8 + frac * 2.8)
        py5.rect(-fw * 0.5, -fh * 0.5, fw, fh, corner_r)

        py5.pop_matrix()

    # 4. Multi-Harmonic Vector Oscilloscope Harmonograph Curves
    for cfg in HARM_CONFIGS:
        c = cfg["c"]
        sc = cfg["scale"]
        curve_phase = tau * cfg["p_speed"]
        lx = (740.0 * sc) * np.sin(cfg["fx"] * THETAS + curve_phase)
        ly = (470.0 * sc) * np.sin(cfg["fy"] * THETAS)

        pts = np.column_stack([CX + lx, CY + ly])

        # A. Broad phosphor persistence halo
        py5.stroke(c[0], c[1], c[2], 38)
        py5.stroke_weight(13.0 * sc)
        py5.begin_shape()
        py5.vertices(pts)
        py5.end_shape(py5.CLOSE)

        # B. Saturated mid-beam trace
        py5.stroke(c[0], c[1], c[2], 165)
        py5.stroke_weight(3.6 * sc)
        py5.begin_shape()
        py5.vertices(pts)
        py5.end_shape(py5.CLOSE)

        # C. Hyper-bright electron core beam
        py5.stroke(255, 255, 255, 225)
        py5.stroke_weight(max(1.2, 1.8 * sc))
        py5.begin_shape()
        py5.vertices(pts)
        py5.end_shape(py5.CLOSE)

    # 5. Horizontal CRT Shadow Mask Scanlines
    py5.stroke(0, 0, 0, 85)
    py5.stroke_weight(2.0)
    for y_scan in range(0, HEIGHT, 6):
        py5.line(0, y_scan, WIDTH, y_scan)

    # 6. Horizontal Sync Glitch Tear Slices (analogue tracking error)
    n_tears = 7
    for gt in range(n_tears):
        gy = int((320 + gt * 260 + 160 * np.sin(tau * 2.0 + gt * 1.7)) % HEIGHT)
        gh = int(24 + 36 * np.abs(np.sin(tau * 3.0 + gt * 2.1)))
        g_shift = int(80.0 * np.sin(tau * 4.0 + gt * 2.5))

        # Tear highlight edges
        py5.stroke(244, 63, 94, 145)
        py5.stroke_weight(1.6)
        py5.line(180, gy, WIDTH - 180, gy)
        py5.stroke(6, 182, 212, 145)
        py5.line(180 + g_shift, gy + gh, WIDTH - 180 + g_shift, gy + gh)

        # Glitch raster scanlines inside slice
        py5.stroke(251, 191, 36, 115)
        py5.stroke_weight(1.0)
        for sub_y in range(gy + 2, gy + gh, 4):
            py5.line(180 + g_shift * 0.7, sub_y, WIDTH - 180 + g_shift * 0.7, sub_y)

    # 7. Oscilloscope Calibration Graticule Crosshairs & Reticle Ticks
    py5.stroke(34, 197, 94, 80)
    py5.stroke_weight(1.2)
    for qx, qy in [(CX - 800, CY - 450), (CX + 800, CY - 450), (CX - 800, CY + 450), (CX + 800, CY + 450)]:
        py5.line(qx - 30, qy, qx + 30, qy)
        py5.line(qx, qy - 30, qx, qy + 30)

    # 8. CRT Curved Bezel and Border Glass Vignette
    py5.no_fill()
    py5.stroke(18, 22, 28, 255)
    py5.stroke_weight(84.0)
    py5.rect(42, 42, WIDTH - 84, HEIGHT - 84, 68)

    # Bezel inner edge specular reflection highlight
    py5.stroke(48, 60, 78, 145)
    py5.stroke_weight(3.5)
    py5.rect(88, 88, WIDTH - 176, HEIGHT - 176, 46)

    # 9. Frame output & progress tracking
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Capture preview image at frame 180 (quarter-cycle peak phase)
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] CRT preview captured: {PREVIEW_PATH}")

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
