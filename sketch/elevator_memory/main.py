from __future__ import annotations

from dataclasses import dataclass
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
SHAFTS = 9
FLOORS = 15
TOWER_X = W * 0.16
TOWER_W = W * 0.68
TOP = H * 0.12
BOTTOM = H * 0.90
TOWER_H = BOTTOM - TOP

BG = (8, 11, 16)
GLASS = (43, 58, 70)
TEAL = (63, 224, 214)
ICE = (206, 230, 232)
AMBER = (242, 176, 80)
ROSE = (240, 108, 126)


@dataclass
class Cabin:
    shaft: int
    phase: float
    speed: float
    size: float
    accent: tuple[int, int, int]


def floor_y(floor: float) -> float:
    return BOTTOM - floor / (FLOORS - 1) * TOWER_H


def shaft_x(shaft: int) -> float:
    return TOWER_X + (shaft + 0.5) * TOWER_W / SHAFTS


def smoothstep(v: float) -> float:
    v = max(0.0, min(1.0, v))
    return v * v * (3.0 - 2.0 * v)


def tri_wave(v: float) -> float:
    f = v % 1.0
    return 1.0 - abs(f * 2.0 - 1.0)


def cabin_floor(cabin: Cabin, t: float) -> float:
    raw = tri_wave(t * cabin.speed + cabin.phase)
    eased = smoothstep(raw)
    drift = 0.42 * math.sin(t * 1.7 + cabin.phase * math.tau)
    return eased * (FLOORS - 1) + drift


def draw_glow_rect(x: float, y: float, w: float, h: float, rgb: tuple[int, int, int], alpha: float, radius: float) -> None:
    py5.no_stroke()
    for grow, a in ((28, 14), (12, 34), (0, alpha)):
        py5.fill(rgb[0], rgb[1], rgb[2], a)
        py5.rect(x, y, w + grow, h + grow * 0.55, radius)


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)

    global cabins, window_noise, call_phases
    rng = np.random.default_rng()
    accents = [TEAL, ICE, AMBER, ROSE]
    cabins = [
        Cabin(
            shaft=i,
            phase=float(rng.uniform(0, 1)),
            speed=float(rng.uniform(0.045, 0.092)),
            size=float(rng.uniform(0.82, 1.18)),
            accent=accents[int(rng.integers(0, len(accents)))],
        )
        for i in range(SHAFTS)
    ]
    window_noise = rng.uniform(0, 1, (FLOORS, SHAFTS))
    call_phases = rng.uniform(0, math.tau, (FLOORS, SHAFTS))


def draw_city(t: float) -> None:
    py5.background(*BG)
    py5.no_stroke()
    for layer, alpha in ((0, 42), (1, 66), (2, 90)):
        step = 92 - layer * 16
        base = H * (0.88 - layer * 0.03)
        for i, x in enumerate(np.arange(-120, W + 160, step)):
            height = 150 + 80 * math.sin(i * 1.7 + layer)
            wobble = math.sin(t * 0.08 + i) * (layer + 1) * 8
            py5.fill(13 + layer * 8, 19 + layer * 9, 28 + layer * 10, alpha)
            py5.rect(x + wobble, base - height * 0.5, step * 0.72, height, 2)
    for i in range(60):
        x = (i * 139 + t * 9) % (W + 120) - 60
        y = H * (0.08 + 0.78 * ((i * 37) % 100) / 100)
        py5.fill(*ICE, 10 + (i % 5) * 7)
        py5.circle(x, y, 1.2 + (i % 3))


def draw_tower(t: float) -> None:
    py5.no_stroke()
    py5.fill(13, 20, 27, 235)
    py5.rect(TOWER_X + TOWER_W * 0.5, TOP + TOWER_H * 0.5, TOWER_W + 90, TOWER_H + 60, 7)
    py5.fill(21, 32, 42, 150)
    py5.rect(TOWER_X + TOWER_W * 0.5, TOP + TOWER_H * 0.5, TOWER_W + 34, TOWER_H + 22, 5)

    py5.stroke(*GLASS, 105)
    py5.stroke_weight(1)
    for floor in range(FLOORS):
        y = floor_y(floor)
        py5.line(TOWER_X - 26, y, TOWER_X + TOWER_W + 26, y)
    for shaft in range(SHAFTS + 1):
        x = TOWER_X + shaft * TOWER_W / SHAFTS
        py5.line(x, TOP - 14, x, BOTTOM + 14)

    for floor in range(FLOORS):
        y = floor_y(floor)
        for shaft in range(SHAFTS):
            x = shaft_x(shaft)
            pulse = 0.5 + 0.5 * math.sin(t * 1.6 + call_phases[floor, shaft])
            lit = window_noise[floor, shaft] > 0.64 or pulse > 0.88
            if lit:
                rgb = TEAL if (floor + shaft) % 3 else AMBER
                py5.fill(rgb[0], rgb[1], rgb[2], 22 + 45 * pulse)
                py5.rect(x, y, TOWER_W / SHAFTS * 0.58, 7, 2)


def draw_memory_traces(t: float) -> None:
    for cabin in cabins:
        x = shaft_x(cabin.shaft)
        py5.stroke(cabin.accent[0], cabin.accent[1], cabin.accent[2], 34)
        py5.stroke_weight(1.3)
        last_y = None
        for k in range(48):
            age = k / 48
            yf = cabin_floor(cabin, t - age * 5.8)
            y = floor_y(yf)
            if last_y is not None:
                py5.stroke(cabin.accent[0], cabin.accent[1], cabin.accent[2], 62 * (1 - age))
                py5.line(x, last_y, x, y)
            if k % 7 == 0:
                py5.no_stroke()
                py5.fill(cabin.accent[0], cabin.accent[1], cabin.accent[2], 34 * (1 - age))
                py5.rect(x, y, TOWER_W / SHAFTS * (0.48 - age * 0.18), 5, 2)
            last_y = y

        current_floor = int(round(cabin_floor(cabin, t)))
        for floor in range(max(0, current_floor - 2), min(FLOORS, current_floor + 3)):
            y = floor_y(floor)
            py5.no_stroke()
            py5.fill(cabin.accent[0], cabin.accent[1], cabin.accent[2], 12)
            py5.rect(x, y, TOWER_W / SHAFTS * 0.82, 16, 2)


def draw_cabins(t: float) -> None:
    for cabin in cabins:
        x = shaft_x(cabin.shaft)
        y = floor_y(cabin_floor(cabin, t))
        w = TOWER_W / SHAFTS * 0.56 * cabin.size
        h = 42 * cabin.size
        draw_glow_rect(x, y, w, h, cabin.accent, 88, 5)
        py5.fill(24, 34, 40, 230)
        py5.stroke(*ICE, 125)
        py5.stroke_weight(1)
        py5.rect(x, y, w, h, 5)
        py5.no_stroke()
        py5.fill(cabin.accent[0], cabin.accent[1], cabin.accent[2], 160)
        py5.rect(x - w * 0.26, y, w * 0.08, h * 0.62, 2)
        py5.fill(*ICE, 150)
        py5.rect(x + w * 0.09, y - h * 0.12, w * 0.31, 3, 1)
        py5.rect(x + w * 0.09, y + h * 0.08, w * 0.26, 3, 1)


def draw_reflections(t: float) -> None:
    py5.stroke_weight(1.2)
    for i in range(16):
        x = TOWER_X - 50 + i * (TOWER_W + 100) / 15
        drift = math.sin(t * 0.35 + i * 0.9) * 38
        py5.stroke(*ICE, 18)
        py5.line(x + drift, TOP - 20, x + drift - 180, BOTTOM + 30)
    py5.no_stroke()
    py5.fill(*TEAL, 90)
    py5.text_size(14)
    py5.text("ELEVATOR MEMORY / VERTICAL TRAFFIC RECORDER", W * 0.5, H * 0.055)


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
    draw_city(t)
    draw_tower(t)
    draw_memory_traces(t)
    draw_cabins(t)
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
