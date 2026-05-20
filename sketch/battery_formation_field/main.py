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
ROWS = 8
COLS = 18

BG = (7, 9, 12)
RACK = (17, 22, 26)
GRID = (47, 57, 60)
CYAN = (45, 224, 211)
GREEN = (111, 222, 121)
AMBER = (244, 178, 70)
RED = (238, 83, 98)
SILVER = (214, 224, 221)


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)

    global rng, charge, heat, phase, balance, traces
    rng = np.random.default_rng()
    charge = rng.uniform(0.12, 0.35, (ROWS, COLS)).astype(np.float32)
    heat = rng.uniform(0.02, 0.12, (ROWS, COLS)).astype(np.float32)
    phase = rng.uniform(0, math.tau, (ROWS, COLS)).astype(np.float32)
    balance = rng.uniform(0, 1, (ROWS, COLS)).astype(np.float32)
    traces = np.zeros((COLS, 90), dtype=np.float32)


def update_cells(t: float) -> None:
    global charge, heat, traces
    wave = np.zeros_like(charge)
    for r in range(ROWS):
        for c in range(COLS):
            target = 0.55 + 0.38 * math.sin(t * 0.45 + c * 0.34 + r * 0.52 + phase[r, c]) ** 2
            shunt = 0.025 if charge[r, c] > 0.84 and balance[r, c] > 0.45 else 0.0
            charge[r, c] += (target - charge[r, c]) * 0.018 - shunt
            local_heat = max(0.0, charge[r, c] - 0.72) * 0.48 + shunt * 5.0
            heat[r, c] = heat[r, c] * 0.965 + local_heat * 0.035
            wave[r, c] = charge[r, c]
    charge = np.clip(charge, 0.04, 0.98)
    heat = np.clip(heat, 0.0, 1.0)
    traces = np.roll(traces, -1, axis=1)
    traces[:, -1] = np.mean(wave, axis=0)


def draw_background(t: float) -> None:
    py5.background(*BG)
    py5.no_stroke()
    py5.fill(*RACK, 238)
    py5.rect(W * 0.5, H * 0.55, W * 0.82, H * 0.70, 6)
    py5.fill(22, 28, 31, 170)
    py5.rect(W * 0.5, H * 0.55, W * 0.75, H * 0.58, 4)
    py5.stroke(*GRID, 65)
    py5.stroke_weight(1)
    for x in np.linspace(W * 0.13, W * 0.87, 20):
        py5.line(x, H * 0.23, x, H * 0.84)
    for y in np.linspace(H * 0.28, H * 0.80, 10):
        py5.line(W * 0.11, y, W * 0.89, y)
    py5.no_stroke()
    py5.fill(*SILVER, 120)
    py5.text_size(13)
    py5.text("BATTERY FORMATION FIELD / CELL BALANCING RACK", W * 0.5, H * 0.065)


def cell_color(q: float, h: float) -> tuple[int, int, int]:
    if h > 0.28:
        return RED
    if q > 0.74:
        return GREEN
    if q > 0.48:
        return CYAN
    return AMBER


def draw_cells(t: float) -> None:
    left = W * 0.17
    top = H * 0.28
    rack_w = W * 0.66
    rack_h = H * 0.43
    sx = rack_w / (COLS - 1)
    sy = rack_h / (ROWS - 1)
    for r in range(ROWS):
        for c in range(COLS):
            x = left + c * sx
            y = top + r * sy
            q = float(charge[r, c])
            h = float(heat[r, c])
            rgb = cell_color(q, h)
            py5.no_stroke()
            py5.fill(rgb[0], rgb[1], rgb[2], 16 + 60 * q + 80 * h)
            py5.rect(x, y, 34, 62, 10)
            py5.fill(18, 24, 27, 230)
            py5.stroke(*SILVER, 62)
            py5.stroke_weight(1)
            py5.rect(x, y, 22, 52, 8)
            fill_h = 42 * q
            py5.no_stroke()
            py5.fill(rgb[0], rgb[1], rgb[2], 90 + 115 * q)
            py5.rect(x, y + 21 - fill_h * 0.5, 13, fill_h, 5)
            if q > 0.84 and balance[r, c] > 0.45:
                py5.stroke(*AMBER, 155)
                py5.stroke_weight(1.4)
                py5.line(x - 17, y - 34, x + 17, y - 34)
            if h > 0.30:
                py5.no_fill()
                py5.stroke(*RED, 120 + 80 * math.sin(t * 6 + c))
                py5.circle(x, y, 56 + 20 * h)


def draw_traces(t: float) -> None:
    x0 = W * 0.18
    y0 = H * 0.79
    width = W * 0.64
    py5.no_fill()
    for c in range(0, COLS, 2):
        rgb = CYAN if c % 4 else AMBER
        py5.stroke(rgb[0], rgb[1], rgb[2], 50)
        py5.stroke_weight(1.2)
        py5.begin_shape()
        for i, val in enumerate(traces[c]):
            x = x0 + i / (traces.shape[1] - 1) * width
            y = y0 - float(val) * 70 - c * 0.9
            py5.curve_vertex(x, y)
        py5.end_shape()
    py5.stroke(*GRID, 95)
    py5.line(x0, y0, x0 + width, y0)


def draw_meters(t: float) -> None:
    mean_charge = float(np.mean(charge))
    max_heat = float(np.max(heat))
    for i, (label, val, rgb) in enumerate((("SOC", mean_charge, CYAN), ("TEMP", max_heat, RED), ("BAL", 0.5 + 0.5 * math.sin(t * 1.2), AMBER))):
        x = W * (0.84)
        y = H * (0.24 + i * 0.09)
        py5.no_fill()
        py5.stroke(*GRID, 120)
        py5.rect(x, y, 98, 42, 5)
        py5.no_stroke()
        py5.fill(rgb[0], rgb[1], rgb[2], 125)
        py5.rect(x - 42 + val * 42, y, max(4, 82 * val), 8, 3)
        py5.fill(*SILVER, 118)
        py5.text_size(10)
        py5.text(label, x, y + 28)


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
    update_cells(t)
    draw_background(t)
    draw_cells(t)
    draw_traces(t)
    draw_meters(t)
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
