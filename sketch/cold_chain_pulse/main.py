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
ROWS = 7
COLS = 15
TRACE = 140

BG = (6, 9, 13)
PANEL = (15, 21, 27)
GRID = (46, 59, 66)
ICE = (156, 227, 236)
CYAN = (42, 220, 216)
BLUE = (63, 135, 238)
AMBER = (245, 181, 72)
SILVER = (218, 228, 226)


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)

    global rng, temp, humidity, phase, trace, mist
    rng = np.random.default_rng()
    temp = rng.uniform(0.25, 0.55, (ROWS, COLS)).astype(np.float32)
    humidity = rng.uniform(0.2, 0.65, (ROWS, COLS)).astype(np.float32)
    phase = rng.uniform(0, math.tau, (ROWS, COLS)).astype(np.float32)
    trace = np.zeros((TRACE, COLS), dtype=np.float32)
    mist = rng.uniform(0, 1, (260, 4)).astype(np.float32)


def update_state(t: float) -> None:
    global temp, humidity, trace, mist
    for r in range(ROWS):
        for c in range(COLS):
            compressor = 0.5 + 0.5 * math.sin(t * 1.05 + c * 0.55 + r * 0.25)
            door_load = 0.18 * math.sin(t * 0.37 + phase[r, c]) ** 2
            target = 0.18 + door_load + 0.22 * (1.0 - compressor)
            temp[r, c] += (target - temp[r, c]) * 0.035 + rng.normal(0.0, 0.002)
            humidity[r, c] += (0.35 + door_load - humidity[r, c]) * 0.018 + rng.normal(0.0, 0.003)
    temp = np.clip(temp, 0.05, 0.95)
    humidity = np.clip(humidity, 0.02, 1.0)
    trace = np.roll(trace, -1, axis=0)
    trace[-1] = np.mean(temp, axis=0)
    mist[:, 1] -= 0.0015 + mist[:, 3] * 0.002
    mist[:, 0] += np.sin(t * 0.7 + mist[:, 2] * 8.0) * 0.0008
    mist[mist[:, 1] < 0.05, 1] = 0.92
    mist[:, 0] %= 1.0


def draw_shell(t: float) -> None:
    py5.background(*BG)
    py5.no_stroke()
    py5.fill(*PANEL, 240)
    py5.rect(W * 0.5, H * 0.53, W * 0.84, H * 0.72, 6)
    py5.fill(19, 28, 34, 195)
    py5.rect(W * 0.5, H * 0.50, W * 0.74, H * 0.53, 4)
    py5.stroke(*GRID, 60)
    py5.stroke_weight(1)
    for x in np.linspace(W * 0.13, W * 0.87, 18):
        py5.line(x, H * 0.23, x, H * 0.82)
    for y in np.linspace(H * 0.25, H * 0.80, 10):
        py5.line(W * 0.11, y, W * 0.89, y)
    py5.no_stroke()
    py5.fill(*SILVER, 118)
    py5.text_size(13)
    py5.text("COLD CHAIN PULSE / REFRIGERATED SENSOR WALL", W * 0.5, H * 0.065)


def draw_bays(t: float) -> None:
    left = W * 0.18
    top = H * 0.25
    wall_w = W * 0.64
    wall_h = H * 0.42
    sx = wall_w / COLS
    sy = wall_h / ROWS
    for r in range(ROWS):
        for c in range(COLS):
            x = left + (c + 0.5) * sx
            y = top + (r + 0.5) * sy
            cold = 1.0 - float(temp[r, c])
            hum = float(humidity[r, c])
            py5.no_stroke()
            py5.fill(BLUE[0], BLUE[1], BLUE[2], 18 + 70 * cold)
            py5.rect(x, y, sx * 0.78, sy * 0.70, 4)
            py5.fill(CYAN[0], CYAN[1], CYAN[2], 24 + 80 * cold)
            py5.rect(x, y + sy * 0.25 - sy * 0.48 * cold, sx * 0.54, sy * 0.10 + sy * 0.52 * cold, 3)
            py5.stroke(*SILVER, 55)
            py5.stroke_weight(1)
            py5.no_fill()
            py5.rect(x, y, sx * 0.80, sy * 0.72, 4)
            if hum > 0.58:
                py5.no_fill()
                py5.stroke(*ICE, 45 + 80 * hum)
                py5.circle(x, y, sy * (0.36 + hum * 0.26))
            if temp[r, c] > 0.48:
                py5.no_stroke()
                py5.fill(*AMBER, 80)
                py5.rect(x, y - sy * 0.30, sx * 0.32, 4, 2)


def draw_mist(t: float) -> None:
    py5.no_stroke()
    for x, y, ph, size in mist:
        alpha = 12 + 52 * (0.5 + 0.5 * math.sin(t + float(ph) * 8.0))
        py5.fill(*ICE, alpha)
        py5.circle(float(x) * W, float(y) * H, 1.5 + float(size) * 5.0)


def draw_traces(t: float) -> None:
    x0 = W * 0.19
    y0 = H * 0.77
    width = W * 0.62
    py5.no_fill()
    for c in range(0, COLS, 2):
        py5.stroke(*(CYAN if c % 4 else ICE), 60)
        py5.stroke_weight(1.2)
        py5.begin_shape()
        for i, val in enumerate(trace[:, c]):
            x = x0 + i / (TRACE - 1) * width
            y = y0 - float(1.0 - val) * 72 - c * 1.1
            py5.curve_vertex(x, y)
        py5.end_shape()
    py5.stroke(*GRID, 90)
    py5.line(x0, y0, x0 + width, y0)


def draw_compressors(t: float) -> None:
    for i in range(5):
        x = W * (0.18 + i * 0.16)
        y = H * 0.16
        pulse = 0.5 + 0.5 * math.sin(t * 1.4 + i * 0.7)
        py5.no_fill()
        py5.stroke(*CYAN, 70 + 100 * pulse)
        py5.stroke_weight(1.6)
        py5.circle(x, y, 36 + 22 * pulse)
        py5.no_stroke()
        py5.fill(*SILVER, 100)
        py5.rect(x, y, 48, 5, 2)


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
    update_state(t)
    draw_shell(t)
    draw_mist(t)
    draw_bays(t)
    draw_traces(t)
    draw_compressors(t)
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
