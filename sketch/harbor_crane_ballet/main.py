from __future__ import annotations

from pathlib import Path
import math
import shutil
import subprocess
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

W, H = SIZE
BG = (6, 9, 13)
WATER = (9, 19, 26)
STEEL = (74, 88, 94)
CYAN = (43, 222, 214)
AMBER = (245, 178, 66)
RED = (233, 82, 99)
SILVER = (217, 226, 224)


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)

    global rng, stacks, ship_boxes, crane_phase, glints
    rng = np.random.default_rng()
    stacks = rng.uniform(0.2, 1.0, (8, 18)).astype(np.float32)
    ship_boxes = rng.choice([0, 1, 2], (5, 14), p=[0.2, 0.45, 0.35]).astype(np.int32)
    crane_phase = rng.uniform(0, math.tau, 4).astype(np.float32)
    glints = rng.uniform(0, 1, (180, 3)).astype(np.float32)


def draw_background(t: float) -> None:
    py5.background(*BG)
    py5.no_stroke()
    py5.fill(*WATER, 230)
    py5.rect(W * 0.5, H * 0.78, W, H * 0.44)
    for x, y, s in glints:
        drift = math.sin(t * 0.6 + float(s) * 9.0) * 16
        py5.fill(*CYAN if s < 0.55 else AMBER, 10 + 36 * float(s))
        py5.rect(float(x) * W + drift, H * (0.60 + float(y) * 0.35), 18 + 26 * float(s), 1.4, 1)
    py5.fill(*SILVER, 120)
    py5.text_size(13)
    py5.text("HARBOR CRANE BALLET / NIGHT BERTH SCHEDULE", W * 0.5, H * 0.065)


def draw_ship(t: float) -> None:
    hull_y = H * 0.63
    py5.no_stroke()
    py5.fill(17, 25, 31, 245)
    py5.quad(W * 0.12, hull_y, W * 0.71, hull_y, W * 0.66, H * 0.76, W * 0.18, H * 0.76)
    colors = [CYAN, AMBER, RED]
    for r in range(ship_boxes.shape[0]):
        for c in range(ship_boxes.shape[1]):
            kind = int(ship_boxes[r, c])
            if kind == 0:
                continue
            x = W * 0.18 + c * 58
            y = H * 0.59 - r * 27
            rgb = colors[kind]
            py5.fill(rgb[0], rgb[1], rgb[2], 75)
            py5.rect(x, y, 50, 20, 2)
            py5.stroke(*SILVER, 35)
            py5.no_fill()
            py5.rect(x, y, 50, 20, 2)
            py5.no_stroke()


def draw_yard(t: float) -> None:
    base_x = W * 0.58
    base_y = H * 0.50
    colors = [CYAN, AMBER, RED, SILVER]
    py5.stroke(*STEEL, 70)
    py5.stroke_weight(1)
    for i in range(9):
        py5.line(base_x - 60, base_y + i * 28, W * 0.92, base_y + i * 28)
    py5.no_stroke()
    for r in range(stacks.shape[0]):
        for c in range(stacks.shape[1]):
            h = int(1 + stacks[r, c] * 4)
            x = base_x + c * 31
            y = base_y + r * 28
            for k in range(h):
                rgb = colors[(r + c + k) % len(colors)]
                py5.fill(rgb[0], rgb[1], rgb[2], 48 + k * 18)
                py5.rect(x, y - k * 8, 26, 7, 1)


def draw_cranes(t: float) -> None:
    rail_y = H * 0.47
    py5.stroke(*STEEL, 145)
    py5.stroke_weight(4)
    py5.line(W * 0.08, rail_y, W * 0.92, rail_y)
    for i in range(4):
        base = W * (0.18 + i * 0.18)
        travel = math.sin(t * (0.42 + i * 0.05) + float(crane_phase[i]))
        x = base + travel * 55
        trolley = x + math.sin(t * (0.95 + i * 0.1) + i) * 90
        lift = H * (0.34 + 0.12 * (0.5 + 0.5 * math.sin(t * 1.2 + i)))
        py5.no_fill()
        py5.stroke(*CYAN, 22)
        py5.stroke_weight(9)
        py5.line(x - 72, H * 0.25, x + 130, H * 0.25)
        py5.stroke(*AMBER, 16)
        py5.arc(x + 30, H * 0.44, 210, 150, math.pi * 1.08, math.pi * 1.92)
        py5.stroke(*SILVER, 110)
        py5.stroke_weight(3)
        py5.line(x - 48, rail_y, x - 18, H * 0.21)
        py5.line(x + 48, rail_y, x + 18, H * 0.21)
        py5.line(x - 72, H * 0.25, x + 130, H * 0.25)
        py5.stroke(*CYAN, 85)
        py5.stroke_weight(1.5)
        py5.line(trolley, H * 0.25, trolley, lift)
        py5.no_stroke()
        py5.fill(*AMBER, 32)
        py5.rect(trolley, lift, 82, 42, 4)
        py5.fill(*AMBER, 150)
        py5.rect(trolley, lift, 46, 16, 2)
        py5.fill(*CYAN, 110)
        py5.circle(trolley, H * 0.25, 8)


def draw_reflections(t: float) -> None:
    py5.no_stroke()
    for i in range(36):
        x = W * (0.12 + i * 0.022)
        wob = math.sin(t * 1.1 + i * 0.6) * 18
        py5.fill(*CYAN if i % 3 else AMBER, 18)
        py5.rect(x + wob, H * (0.79 + (i % 7) * 0.018), 42, 2, 1)


def draw_schedule_haze(t: float) -> None:
    py5.no_fill()
    for i in range(7):
        x = W * (0.16 + i * 0.11)
        y = H * (0.50 + 0.02 * math.sin(t + i))
        py5.stroke(*(CYAN if i % 2 else AMBER), 22)
        py5.stroke_weight(1.4)
        py5.arc(x, y, 160 + i * 18, 64 + i * 8, math.pi, math.tau)
    py5.no_stroke()
    py5.fill(*CYAN, 18)
    py5.rect(W * 0.55, H * 0.55, W * 0.58, H * 0.20, 5)


def compile_video() -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-r",
            str(FPS),
            "-i",
            str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "20",
            str(SKETCH_DIR / "output.mp4"),
        ],
        check=True,
    )
    shutil.copy2(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)
    shutil.rmtree(FRAMES_DIR)


def draw() -> None:
    t = py5.frame_count / FPS
    draw_background(t)
    draw_ship(t)
    draw_yard(t)
    draw_schedule_haze(t)
    draw_cranes(t)
    draw_reflections(t)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        pct = py5.frame_count / TOTAL_FRAMES * 100
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({pct:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into output.mp4...")
        compile_video()
        print("[Render Cleanup] Temporary frames directory successfully removed.")


py5.run_sketch()
