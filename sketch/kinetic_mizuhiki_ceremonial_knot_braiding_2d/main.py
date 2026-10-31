"""
kinetic_mizuhiki_ceremonial_knot_braiding_2d
Autonomous Generative py5 Media Art Animation
Genre: Textile / Calligraphy / Procedural Craft
Theme: Sacred Mizuhiki Silk-Wound Paper Cord Braiding & Topological Ume-Awaji Knot Dynamics
12.0s Seamless Loop (720 frames @ 60 FPS, 4K Master)
Strictly Anonymous: Zero signatures, seals (落款), monograms, initials, or personal marks.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
import py5

# Master 4K Canvas Resolution
WIDTH, HEIGHT = 3840, 2160
TOTAL_FRAMES = 720
FPS = 60

WORK_DIR = Path(__file__).resolve().parent
WORK_NAME = WORK_DIR.name
FRAMES_DIR = WORK_DIR / "frames"
PREVIEW_PATH = WORK_DIR / f"{WORK_NAME}_p1.png"
OUTPUT_VIDEO = WORK_DIR / f"{WORK_NAME}.mp4"

# Center and Geometry Scaling
XC = WIDTH / 2.0
YC = HEIGHT * 0.44

# 5-strand ribbon offsets (in 4K pixels)
STRAND_OFFSETS = np.array([-16.0, -8.0, 0.0, 8.0, 16.0])

# Color Palettes (Base & Specular Highlight)
# 1. Ceremonial Lacquer Vermilion & Burnished Gold (Beni-Kin)
COLORS_VERMILION = [
    ((190, 28, 28), (240, 58, 58)),     # Deep Lacquer Vermilion
    ((195, 145, 30), (255, 232, 110)),  # Burnished Gold Leaf
    ((245, 245, 248), (255, 255, 255)), # Silk Pearl White
    ((195, 145, 30), (255, 232, 110)),  # Burnished Gold Leaf
    ((190, 28, 28), (240, 58, 58)),     # Deep Lacquer Vermilion
]

# 2. Royal Indigo & Burnished Gold (Ai-Kin)
COLORS_INDIGO = [
    ((20, 36, 60), (52, 80, 122)),      # Royal Fermented Indigo
    ((195, 145, 30), (255, 232, 110)),  # Burnished Gold Leaf
    ((245, 245, 248), (255, 255, 255)), # Silk Pearl White
    ((195, 145, 30), (255, 232, 110)),  # Burnished Gold Leaf
    ((20, 36, 60), (52, 80, 122)),      # Royal Fermented Indigo
]

# 3. Pure Gilded Silk (Kin-Shiro)
COLORS_GOLD = [
    ((195, 145, 30), (255, 232, 110)),  # Gold
    ((245, 245, 248), (255, 255, 255)), # Pearl White
    ((195, 145, 30), (255, 232, 110)),  # Gold
    ((245, 245, 248), (255, 255, 255)), # Pearl White
    ((195, 145, 30), (255, 232, 110)),  # Gold
]

# Static Washi Canvas Fibers & Sunago Gold Dust (varied each run, stable across animation)
SEED = int(np.random.randint(1, 1000000))
RNG = np.random.RandomState(SEED)

N_FIBERS = 680
FX1 = RNG.uniform(60, WIDTH - 60, N_FIBERS)
FY1 = RNG.uniform(60, HEIGHT - 60, N_FIBERS)
F_LEN = RNG.uniform(30, 120, N_FIBERS)
F_ANG = RNG.uniform(0, 2 * np.pi, N_FIBERS)
FX2 = FX1 + F_LEN * np.cos(F_ANG)
FY2 = FY1 + F_LEN * np.sin(F_ANG)
FIBER_LINES = np.column_stack([FX1, FY1, FX2, FY2])

N_SUNAGO = 340
SX = RNG.uniform(60, WIDTH - 60, N_SUNAGO)
SY = RNG.uniform(60, HEIGHT - 60, N_SUNAGO)
SR = RNG.uniform(2.5, 7.0, N_SUNAGO)
SA = RNG.randint(80, 195, N_SUNAGO)


def generate_closed_curve(x, y, z, strand_offsets, strand_colors):
    """Compute normal vectors and midpoint depths for closed space curves."""
    x_next = np.roll(x, -1)
    y_next = np.roll(y, -1)
    z_next = np.roll(z, -1)

    dx = x_next - x
    dy = y_next - y
    dist = np.hypot(dx, dy)
    dist = np.maximum(dist, 1e-4)

    nx = -dy / dist
    ny = dx / dist
    z_mid = 0.5 * (z + z_next)

    return {
        "x": x, "y": y, "x_next": x_next, "y_next": y_next,
        "nx": nx, "ny": ny, "z_mid": z_mid,
        "offsets": strand_offsets, "colors": strand_colors
    }


def generate_open_curve(x, y, z, strand_offsets, strand_colors):
    """Compute normal vectors and midpoint depths for open ribbon streamers."""
    dx = np.gradient(x)
    dy = np.gradient(y)
    dist = np.hypot(dx, dy)
    dist = np.maximum(dist, 1e-4)

    nx = -dy / dist
    ny = dx / dist

    return {
        "x": x[:-1], "y": y[:-1], "x_next": x[1:], "y_next": y[1:],
        "nx": nx[:-1], "ny": ny[:-1], "z_mid": 0.5 * (z[:-1] + z[1:]),
        "offsets": strand_offsets, "colors": strand_colors
    }


def setup():
    py5.size(WIDTH, HEIGHT)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized 4K render session (720 frames, Seed: {SEED})")


def draw():
    frame = py5.frame_count
    # Harmonic phase tau in [0, 2pi] for exact seamless loop
    tau = 2.0 * np.pi * ((frame - 1) % TOTAL_FRAMES) / TOTAL_FRAMES

    # 1. Warm Unbleached Kozo Washi Background
    py5.background(247, 243, 234)

    # Washi Mulberry Paper Fibers
    py5.stroke(222, 214, 200, 75)
    py5.stroke_weight(1.8)
    py5.lines(FIBER_LINES)

    # Sunago Gold Leaf Flakes
    py5.no_stroke()
    for px, py, pr, pa in zip(SX, SY, SR, SA):
        py5.fill(212, 175, 55, pa)
        py5.circle(px, py, pr)

    # Corner Watermark Drafting Calibration Arcs
    py5.no_fill()
    py5.stroke(205, 190, 170, 65)
    py5.stroke_weight(1.5)
    corner_margin = 220
    for cx, cy in [
        (corner_margin, corner_margin),
        (WIDTH - corner_margin, corner_margin),
        (corner_margin, HEIGHT - corner_margin),
        (WIDTH - corner_margin, HEIGHT - corner_margin)
    ]:
        py5.circle(cx, cy, 260)
        py5.circle(cx, cy, 380)
        py5.line(cx - 50, cy, cx + 50, cy)
        py5.line(cx, cy - 50, cx, cy + 50)

    # 2. Kinetic Space Knot Geometries (Harmonic Functions of tau)
    # KNOT 1: Sacred 5-Petal Ume (Plum Blossom) Knot (Vermilion + Gold)
    N1 = 1200
    s1 = np.linspace(0, 2.0 * np.pi, N1, endpoint=False)
    # Rhythmic breathing & subtle rotational oscillation
    r1_breathe = 560.0 + 45.0 * np.sin(tau)
    r1_petal = 250.0 + 25.0 * np.cos(tau)
    r1 = r1_breathe + r1_petal * np.cos(5.0 * s1)
    theta1 = 2.0 * s1 + 0.08 * np.sin(tau)
    x1 = XC + r1 * np.cos(theta1)
    y1 = YC + r1 * np.sin(theta1) * 0.94
    z1 = 380.0 * np.sin(5.0 * s1)
    c1 = generate_closed_curve(x1, y1, z1, STRAND_OFFSETS, COLORS_VERMILION)

    # KNOT 2: Interwoven Inner 5-Petal Gilded Blossom (Gold + Pearl)
    N2 = 1000
    s2 = np.linspace(0, 2.0 * np.pi, N2, endpoint=False)
    r2_breathe = 370.0 - 35.0 * np.sin(tau)
    r2_petal = 150.0 - 20.0 * np.cos(tau)
    r2 = r2_breathe + r2_petal * np.cos(5.0 * s2 + np.pi / 5.0)
    theta2 = 2.0 * s2 + np.pi / 5.0 - 0.08 * np.sin(tau)
    x2 = XC + r2 * np.cos(theta2)
    y2 = YC + r2 * np.sin(theta2) * 0.94
    z2 = -380.0 * np.sin(5.0 * s2)
    c2 = generate_closed_curve(x2, y2, z2, STRAND_OFFSETS, COLORS_GOLD)

    # KNOT 3: Encircling Awaji Carrick Bow Wings (Royal Indigo + Gold)
    N3 = 1100
    s3 = np.linspace(0, 2.0 * np.pi, N3, endpoint=False)
    w3_x1 = 820.0 + 60.0 * np.cos(tau)
    w3_x2 = 320.0 + 35.0 * np.sin(tau)
    x3 = XC + w3_x1 * np.cos(s3) + w3_x2 * np.cos(3.0 * s3)
    y3 = YC + (620.0 + 45.0 * np.sin(tau)) * np.sin(2.0 * s3) * 0.86
    z3 = (320.0 + 40.0 * np.cos(tau)) * np.sin(3.0 * s3)
    c3 = generate_closed_curve(x3, y3, z3, STRAND_OFFSETS, COLORS_INDIGO)

    # STREAMER 1: Left Flowing Silk Tail (Nagare)
    N4 = 600
    t4 = np.linspace(0, 1.0, N4)
    p0_l = np.array([XC - 160.0, YC + 350.0])
    p1_l = np.array([XC - 540.0, YC + 720.0])
    p2_l = np.array([XC - 840.0, YC + 1040.0])
    p3_l = np.array([XC - 1280.0, HEIGHT - 80.0])
    pts_s1 = (
        (1.0 - t4)[:, None] ** 3 * p0_l
        + 3.0 * (1.0 - t4)[:, None] ** 2 * t4[:, None] * p1_l
        + 3.0 * (1.0 - t4)[:, None] * t4[:, None] ** 2 * p2_l
        + t4[:, None] ** 3 * p3_l
    )
    wave_x4 = 55.0 * np.sin(np.pi * t4 * 1.8 + tau) + 20.0 * np.cos(2.0 * np.pi * t4 * 2.5 - tau)
    wave_y4 = 30.0 * np.sin(2.0 * np.pi * t4 * 1.5 + tau)
    x4 = pts_s1[:, 0] + wave_x4
    y4 = pts_s1[:, 1] + wave_y4
    z4 = -240.0 + 160.0 * t4 + 60.0 * np.sin(np.pi * t4 * 2.0 + tau)
    c4 = generate_open_curve(x4, y4, z4, STRAND_OFFSETS, COLORS_VERMILION)

    # STREAMER 2: Right Flowing Silk Tail (Nagare)
    p0_r = np.array([XC + 160.0, YC + 350.0])
    p1_r = np.array([XC + 540.0, YC + 720.0])
    p2_r = np.array([XC + 840.0, YC + 1040.0])
    p3_r = np.array([XC + 1280.0, HEIGHT - 80.0])
    pts_s2 = (
        (1.0 - t4)[:, None] ** 3 * p0_r
        + 3.0 * (1.0 - t4)[:, None] ** 2 * t4[:, None] * p1_r
        + 3.0 * (1.0 - t4)[:, None] * t4[:, None] ** 2 * p2_r
        + t4[:, None] ** 3 * p3_r
    )
    wave_x5 = -55.0 * np.sin(np.pi * t4 * 1.8 + tau) - 20.0 * np.cos(2.0 * np.pi * t4 * 2.5 - tau)
    wave_y5 = 30.0 * np.sin(2.0 * np.pi * t4 * 1.5 + tau)
    x5 = pts_s2[:, 0] + wave_x5
    y5 = pts_s2[:, 1] + wave_y5
    z5 = -240.0 + 160.0 * t4 - 60.0 * np.sin(np.pi * t4 * 2.0 + tau)
    c5 = generate_open_curve(x5, y5, z5, STRAND_OFFSETS, COLORS_INDIGO)

    curves = [c1, c2, c3, c4, c5]

    # PASS 1: Broad Tactile Drop Shadows onto Washi Ground
    for c in curves:
        z_norm = (c["z_mid"] - c["z_mid"].min()) / (c["z_mid"].max() - c["z_mid"].min() + 1e-4)
        sh_dx = 26.0 + 18.0 * z_norm
        sh_dy = 34.0 + 22.0 * z_norm
        sh_lines = np.column_stack([
            c["x"] + sh_dx, c["y"] + sh_dy,
            c["x_next"] + sh_dx, c["y_next"] + sh_dy
        ])
        py5.stroke(48, 34, 22, 45)
        py5.stroke_weight(42.0)
        py5.lines(sh_lines)

    # PASS 2: Depth-Layered Continuous Rendering (Painter's Algorithm)
    all_z = np.concatenate([c["z_mid"] for c in curves])
    z_min, z_max = all_z.min(), all_z.max()

    N_LAYERS = 64
    layer_edges = np.linspace(z_min - 1e-3, z_max + 1e-3, N_LAYERS + 1)

    for l_idx in range(N_LAYERS):
        z_low = layer_edges[l_idx]
        z_high = layer_edges[l_idx + 1]

        # Depth ambient cueing (lower depth slightly darker, higher depth radiant)
        z_frac = l_idx / N_LAYERS
        ao_mult = 0.80 + 0.24 * z_frac

        for c in curves:
            mask = (c["z_mid"] >= z_low) & (c["z_mid"] < z_high)
            if not np.any(mask):
                continue

            sub_x = c["x"][mask]
            sub_y = c["y"][mask]
            sub_x_next = c["x_next"][mask]
            sub_y_next = c["y_next"][mask]
            sub_nx = c["nx"][mask]
            sub_ny = c["ny"][mask]

            # Draw the 5 parallel cylindrical silk strands
            for k in range(5):
                off = c["offsets"][k]
                base_col, hi_col = c["colors"][k]

                r_base = int(np.clip(base_col[0] * ao_mult, 0, 255))
                g_base = int(np.clip(base_col[1] * ao_mult, 0, 255))
                b_base = int(np.clip(base_col[2] * ao_mult, 0, 255))

                r_hi = int(np.clip(hi_col[0] * ao_mult, 0, 255))
                g_hi = int(np.clip(hi_col[1] * ao_mult, 0, 255))
                b_hi = int(np.clip(hi_col[2] * ao_mult, 0, 255))

                p0x = sub_x + off * sub_nx
                p0y = sub_y + off * sub_ny
                p1x = sub_x_next + off * sub_nx
                p1y = sub_y_next + off * sub_ny

                strand_lines = np.column_stack([p0x, p0y, p1x, p1y])

                # Base cylindrical silk cord stroke
                py5.stroke(r_base, g_base, b_base, 255)
                py5.stroke_weight(8.2)
                py5.lines(strand_lines)

                # Center specular silk thread sheen
                py5.stroke(r_hi, g_hi, b_hi, 235)
                py5.stroke_weight(3.0)
                py5.lines(strand_lines)

    # Save preview image on middle frame (knot at peak blooming resonance)
    if frame == 1:
        py5.save(str(PREVIEW_PATH))
        print(f"[{WORK_NAME}] Initial preview image saved to {PREVIEW_PATH.name}")

    # Fail-safe: ensure canvas is not blank
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame}. Aborting.")
            import os
            os._exit(1)

    # Save sequential frame for FFmpeg compilation
    frame_filename = FRAMES_DIR / f"frame_{frame:04d}.png"
    py5.save(str(frame_filename))

    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[{WORK_NAME}] Rendered frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # Final frame completion: compile video and clean up
    if frame >= TOTAL_FRAMES:
        finish_render()


def finish_render():
    py5.no_loop()
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered. Compiling 4K video with FFmpeg...")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        str(OUTPUT_VIDEO)
    ]
    subprocess.run(cmd, check=True)
    print(f"[{WORK_NAME}] Master MP4 video compiled successfully: {OUTPUT_VIDEO.name}")

    # Save the middle frame as the definitive representative preview
    mid_frame = FRAMES_DIR / f"frame_{TOTAL_FRAMES // 2:04d}.png"
    if mid_frame.exists():
        shutil.copy(str(mid_frame), str(PREVIEW_PATH))
        print(f"[{WORK_NAME}] Updated preview snapshot from frame {TOTAL_FRAMES // 2}")

    # Clean up temporary frames directory
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    print(f"[{WORK_NAME}] Temporary frames directory cleaned up.")

    import os
    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
