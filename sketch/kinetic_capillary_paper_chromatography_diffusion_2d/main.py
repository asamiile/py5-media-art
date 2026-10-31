"""
kinetic_capillary_paper_chromatography_diffusion_2d
Autonomous Generative py5 Media Art Animation
Genre: Atmospheric / Painterly / Color Field
Theme: Paper Chromatography Pigment Fractionation & Capillary Advection Dynamics
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

# Master 4K Resolution
WIDTH, HEIGHT = 3840, 2160
TOTAL_FRAMES = 720
FPS = 60

WORK_DIR = Path(__file__).resolve().parent
WORK_NAME = WORK_DIR.name
FRAMES_DIR = WORK_DIR / "frames"
PREVIEW_PATH = WORK_DIR / f"{WORK_NAME}_p1.png"
OUTPUT_VIDEO = WORK_DIR / f"{WORK_NAME}.mp4"

# Static Cellulose Chromatography Paper (Stable across frames)
SEED = int(np.random.randint(1, 1000000))
RNG = np.random.RandomState(SEED)

# Porous cellulose fibers
N_FIBERS = 850
FX1 = RNG.uniform(60, WIDTH - 60, N_FIBERS)
FY1 = RNG.uniform(60, HEIGHT - 60, N_FIBERS)
F_LEN = RNG.uniform(35, 140, N_FIBERS)
F_ANG = RNG.uniform(0, 2 * np.pi, N_FIBERS)
FX2 = FX1 + F_LEN * np.cos(F_ANG)
FY2 = FY1 + F_LEN * np.sin(F_ANG)
FIBER_LINES = np.column_stack([FX1, FY1, FX2, FY2])

# Paper pore tooth grain
N_PORES = 750
PX = RNG.uniform(40, WIDTH - 40, N_PORES)
PY = RNG.uniform(40, HEIGHT - 40, N_PORES)
PR = RNG.uniform(1.8, 4.8, N_PORES)
PA = RNG.randint(30, 95, N_PORES)

# Chromatographic Droplet Nuclei Definitions
DROPLETS = [
    {"xc": WIDTH * 0.48, "yc": HEIGHT * 0.48, "r_max": 920.0, "type": "classic", "seed": 101},
    {"xc": WIDTH * 0.76, "yc": HEIGHT * 0.33, "r_max": 620.0, "type": "peacock", "seed": 202},
    {"xc": WIDTH * 0.24, "yc": HEIGHT * 0.67, "r_max": 640.0, "type": "madder", "seed": 303},
    {"xc": WIDTH * 0.17, "yc": HEIGHT * 0.24, "r_max": 400.0, "type": "classic", "seed": 404},
    {"xc": WIDTH * 0.83, "yc": HEIGHT * 0.77, "r_max": 440.0, "type": "peacock", "seed": 505},
]

N_PTS = 540
THETA = np.linspace(0, 2.0 * np.pi, N_PTS, endpoint=False)
M_MODES = np.array([3, 4, 5, 7, 9, 12, 16, 21])

DROPLET_DATA = []
for drop in DROPLETS:
    d_rng = np.random.RandomState(drop["seed"])
    amps = d_rng.uniform(0.03, 0.12, len(M_MODES))
    phases = d_rng.uniform(0, 2.0 * np.pi, len(M_MODES))
    freq_mult = np.array([1, -1, 1, 2, -1, 1, -2, 1])

    # Capillary fibril radial streamers
    n_fibrils = 50
    fibril_angles = (np.linspace(0, 2.0 * np.pi, n_fibrils, endpoint=False) + d_rng.uniform(-0.03, 0.03, n_fibrils))

    DROPLET_DATA.append({
        "drop": drop,
        "amps": amps,
        "phases": phases,
        "freq_mult": freq_mult,
        "fibril_angles": fibril_angles,
    })


def setup():
    py5.size(WIDTH, HEIGHT)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized 4K render session (720 frames, Seed: {SEED})")


def draw():
    frame = py5.frame_count
    # Harmonic phase tau in [0, 2pi] for exact seamless loop
    tau = 2.0 * np.pi * ((frame - 1) % TOTAL_FRAMES) / TOTAL_FRAMES

    # 1. Warm Porous Cellulose Paper Substrate
    py5.background(246, 243, 236)

    # Cellulose paper fibers
    py5.stroke(222, 214, 200, 85)
    py5.stroke_weight(1.8)
    py5.lines(FIBER_LINES)

    # Paper pore tooth grain
    py5.no_stroke()
    for px, py, pr, pa in zip(PX, PY, PR, PA):
        py5.fill(210, 200, 185, pa)
        py5.circle(px, py, pr)

    # Corner Watermark Calibration Arcs
    py5.no_fill()
    py5.stroke(205, 195, 180, 55)
    py5.stroke_weight(1.5)
    corner_m = 220
    for cx, cy in [
        (corner_m, corner_m),
        (WIDTH - corner_m, corner_m),
        (corner_m, HEIGHT - corner_m),
        (WIDTH - corner_m, HEIGHT - corner_m)
    ]:
        py5.circle(cx, cy, 260)
        py5.circle(cx, cy, 380)
        py5.line(cx - 50, cy, cx + 50, cy)
        py5.line(cx, cy - 50, cx, cy + 50)

    # 2. Multi-Plume Chromatographic Fractionation
    for dd in DROPLET_DATA:
        drop = dd["drop"]
        xc, yc = drop["xc"], drop["yc"]
        d_type = drop["type"]

        # Dynamic capillary breathing expansion
        breathe = 1.0 + 0.045 * np.sin(tau + drop["seed"] * 0.1)
        R_max = drop["r_max"] * breathe

        # Compute Saffman-Taylor fingering radius profile
        r_mod = np.ones(N_PTS)
        for m, amp, ph, fm in zip(M_MODES, dd["amps"], dd["phases"], dd["freq_mult"]):
            r_mod += amp * np.cos(m * THETA + ph + fm * tau)

        # 12-layer optical glazes for physical pigment sedimentation
        if d_type == "classic":
            # Gall ink breakdown: Celadon solvent -> Saffron gold -> Rose carmine -> Indigo -> Navy -> Carbon
            glazes = [
                (1.00, (215, 232, 224, 45), (170, 195, 185, 100), 2.4),
                (0.92, (230, 218, 175, 55), None, 0),
                (0.84, (242, 192, 45, 75), (235, 180, 35, 110), 2.0),
                (0.76, (230, 145, 55, 80), None, 0),
                (0.68, (205, 42, 75, 95), (220, 52, 90, 125), 2.2),
                (0.60, (168, 38, 92, 105), None, 0),
                (0.50, (68, 62, 128, 115), (78, 72, 148, 135), 2.4),
                (0.42, (32, 68, 122, 135), None, 0),
                (0.34, (24, 48, 92, 160), (32, 62, 118, 175), 2.6),
                (0.24, (18, 32, 65, 195), None, 0),
                (0.16, (16, 22, 38, 225), (24, 34, 58, 235), 3.0),
                (0.09, (12, 14, 18, 250), (8, 10, 12, 255), 3.6),
            ]
        elif d_type == "peacock":
            # Peacock teal breakdown: Clear solvent -> Chartreuse -> Emerald -> Cyan -> Deep Violet -> Plum
            glazes = [
                (1.00, (215, 235, 232, 45), (165, 198, 192, 100), 2.4),
                (0.92, (195, 228, 185, 55), None, 0),
                (0.84, (120, 205, 165, 75), (105, 190, 150, 110), 2.0),
                (0.76, (48, 182, 188, 80), None, 0),
                (0.68, (24, 145, 182, 95), (28, 162, 205, 125), 2.2),
                (0.60, (35, 105, 175, 105), None, 0),
                (0.50, (52, 68, 155, 115), (65, 82, 178, 135), 2.4),
                (0.42, (72, 45, 138, 135), None, 0),
                (0.34, (68, 28, 108, 160), (85, 38, 135, 175), 2.6),
                (0.24, (54, 20, 82, 195), None, 0),
                (0.16, (38, 14, 55, 225), (48, 20, 70, 235), 3.0),
                (0.09, (20, 10, 28, 250), (12, 6, 18, 255), 3.6),
            ]
        else:
            # Madder & dragon's blood: Pale rose -> Solar amber -> Vermilion -> Crimson -> Carmine core
            glazes = [
                (1.00, (238, 224, 226, 45), (210, 180, 185, 100), 2.4),
                (0.92, (245, 218, 175, 55), None, 0),
                (0.84, (248, 188, 48, 75), (242, 175, 38, 110), 2.0),
                (0.76, (240, 132, 42, 80), None, 0),
                (0.68, (225, 68, 45, 95), (235, 78, 55, 125), 2.2),
                (0.60, (208, 42, 58, 105), None, 0),
                (0.50, (185, 28, 62, 115), (200, 38, 75, 135), 2.4),
                (0.42, (155, 22, 58, 135), None, 0),
                (0.34, (122, 18, 48, 160), (142, 24, 60, 175), 2.6),
                (0.24, (88, 14, 38, 195), None, 0),
                (0.16, (55, 10, 26, 225), (70, 15, 35, 235), 3.0),
                (0.09, (28, 8, 16, 250), (18, 4, 10, 255), 3.6),
            ]

        for frac, fill_col, stroke_col, sw in glazes:
            bx = xc + R_max * frac * r_mod * np.cos(THETA)
            by = yc + R_max * frac * r_mod * np.sin(THETA) * 0.94

            py5.fill(*fill_col)
            if stroke_col:
                py5.stroke(*stroke_col)
                py5.stroke_weight(sw)
            else:
                py5.no_stroke()

            py5.begin_shape()
            for x, y in zip(bx, by):
                py5.vertex(x, y)
            py5.end_shape(py5.CLOSE)

        # Micro-Capillary Feathered Meniscus Fingers
        py5.stroke(fill_col[0], fill_col[1], fill_col[2], 65)
        py5.stroke_weight(1.8)
        for ang in dd["fibril_angles"]:
            idx = int((ang % (2.0 * np.pi)) / (2.0 * np.pi) * N_PTS)
            t_steps = np.linspace(0.25, 0.96, 24)
            fx = xc + R_max * t_steps * r_mod[idx] * np.cos(ang) + 8.0 * np.sin(t_steps * np.pi * 5.0 + tau)
            fy = yc + R_max * t_steps * r_mod[idx] * np.sin(ang) * 0.94 + 8.0 * np.cos(t_steps * np.pi * 5.0 + tau)
            py5.lines(np.column_stack([fx[:-1], fy[:-1], fx[1:], fy[1:]]))

    # Save initial preview on frame 1
    if frame == 1:
        py5.save(str(PREVIEW_PATH))
        print(f"[{WORK_NAME}] Initial preview image saved to {PREVIEW_PATH.name}")

    # Blank screen check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame}. Aborting.")
            import os
            os._exit(1)

    frame_filename = FRAMES_DIR / f"frame_{frame:04d}.png"
    py5.save(str(frame_filename))

    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[{WORK_NAME}] Rendered frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

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

    mid_frame = FRAMES_DIR / f"frame_{TOTAL_FRAMES // 2:04d}.png"
    if mid_frame.exists():
        shutil.copy(str(mid_frame), str(PREVIEW_PATH))
        print(f"[{WORK_NAME}] Updated preview snapshot from frame {TOTAL_FRAMES // 2}")

    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    print(f"[{WORK_NAME}] Temporary frames directory cleaned up.")

    import os
    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
