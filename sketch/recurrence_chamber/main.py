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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

W, H = SIZE
N = 48
DT = 0.018
SUBSTEPS = 18
ALPHA = 0.22
AMPLITUDE = 3.8

BG = (8, 10, 13)
GRAPHITE = (24, 29, 33)
GRID = (46, 56, 61)
TEAL = (44, 222, 212)
AMBER = (245, 178, 64)
SILVER = (214, 224, 222)
ROSE = (238, 95, 116)

idx = np.arange(N, dtype=np.float32)
mode_matrix = np.array(
    [np.sin(k * np.pi * idx / (N - 1)) for k in range(1, 7)],
    dtype=np.float32,
)


def acceleration(q: np.ndarray) -> np.ndarray:
    right = np.roll(q, -1) - q
    left = q - np.roll(q, 1)
    right[-1] = -q[-1]
    left[0] = q[0]
    acc = (right - left) + ALPHA * (right * right - left * left)
    acc[0] = 0.0
    acc[-1] = 0.0
    return acc


def integrate() -> None:
    global q, v
    for _ in range(SUBSTEPS):
        acc = acceleration(q)
        q_next = q + v * DT + 0.5 * acc * DT * DT
        acc_next = acceleration(q_next)
        v = v + 0.5 * (acc + acc_next) * DT
        q = q_next


def smoothstep(v: float) -> float:
    v = max(0.0, min(1.0, v))
    return v * v * (3.0 - 2.0 * v)


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)

    global q, v, smooth_modes, spark_x, spark_phase
    rng = np.random.default_rng()
    q = AMPLITUDE * np.sin(np.pi * idx / (N - 1))
    q += rng.normal(0.0, 0.03, N).astype(np.float32)
    q[0] = 0.0
    q[-1] = 0.0
    v = np.zeros(N, dtype=np.float32)
    smooth_modes = np.zeros(6, dtype=np.float32)
    smooth_modes[0] = AMPLITUDE * N * 0.42
    spark_x = rng.uniform(0.08, 0.92, 260).astype(np.float32)
    spark_phase = rng.uniform(0, math.tau, 260).astype(np.float32)


def draw_background(t: float) -> None:
    py5.background(*BG)
    py5.no_stroke()
    py5.fill(14, 18, 22, 235)
    py5.rect(W * 0.5, H * 0.54, W * 0.84, H * 0.72, 6)
    py5.fill(22, 27, 31, 190)
    py5.rect(W * 0.5, H * 0.54, W * 0.78, H * 0.62, 4)

    py5.stroke(*GRID, 58)
    py5.stroke_weight(1)
    for x in np.linspace(W * 0.13, W * 0.87, 25):
        py5.line(x, H * 0.22, x, H * 0.86)
    for y in np.linspace(H * 0.25, H * 0.83, 11):
        py5.line(W * 0.10, y, W * 0.90, y)

    for i, sx in enumerate(spark_x):
        pulse = 0.5 + 0.5 * math.sin(t * 0.7 + float(spark_phase[i]))
        py5.no_stroke()
        py5.fill(*TEAL if i % 3 else AMBER, 12 + 36 * pulse)
        py5.circle(float(sx) * W, H * (0.18 + 0.72 * ((i * 37) % 100) / 100), 1.4 + 1.8 * pulse)


def draw_mode_scope(t: float, recurrence: float) -> None:
    left = W * 0.14
    top = H * 0.12
    py5.no_stroke()
    py5.fill(*SILVER, 120)
    py5.text_size(13)
    py5.text("RECURRENCE CHAMBER / NONLINEAR MODE RETURN", W * 0.5, H * 0.065)
    for i, m in enumerate(smooth_modes):
        x = left + i * 66
        h = 12 + min(96, m * 1.45)
        rgb = [TEAL, AMBER, ROSE, SILVER, TEAL, AMBER][i]
        py5.fill(rgb[0], rgb[1], rgb[2], 45)
        py5.rect(x, top + 62, 34, 112, 3)
        py5.fill(rgb[0], rgb[1], rgb[2], 145)
        py5.rect(x, top + 118 - h * 0.5, 34, h, 3)
    py5.no_fill()
    py5.stroke(*TEAL, 60 + 120 * recurrence)
    py5.stroke_weight(2)
    py5.circle(W * 0.84, H * 0.16, 48 + 34 * recurrence)
    py5.fill(*TEAL, 105)
    py5.text_size(11)
    py5.text(f"{int(recurrence * 100):02d}", W * 0.84, H * 0.16)


def draw_resonators(t: float, recurrence: float) -> None:
    base_y = H * 0.57
    chamber_w = W * 0.72
    start_x = W * 0.14
    xs = start_x + np.linspace(0, chamber_w, N)
    normalized = q / (np.max(np.abs(q)) + 1e-5)
    high_energy = 1.0 - recurrence

    py5.no_fill()
    for band, rgb in enumerate((TEAL, AMBER, ROSE)):
        py5.stroke(rgb[0], rgb[1], rgb[2], 24 + 36 * high_energy)
        py5.stroke_weight(1.1 + band * 0.3)
        py5.begin_shape()
        for i, x in enumerate(xs):
            y = base_y - normalized[i] * (78 + band * 28) + math.sin(t * (1.1 + band * 0.3) + i * 0.35) * (4 + 6 * high_energy)
            py5.curve_vertex(float(x), float(y))
        py5.end_shape()

    for i, x in enumerate(xs):
        n = float(normalized[i])
        y = base_y - n * 155
        h = 80 + abs(n) * 160
        rgb = TEAL if n >= 0 else AMBER
        if abs(n) > 0.72:
            rgb = SILVER
        py5.no_stroke()
        py5.fill(rgb[0], rgb[1], rgb[2], 14 + 44 * abs(n))
        py5.rect(float(x), base_y, 13, h, 6)
        py5.fill(*GRAPHITE, 230)
        py5.rect(float(x), base_y, 7, h * 0.88, 4)
        py5.fill(rgb[0], rgb[1], rgb[2], 120 + 80 * abs(n))
        py5.circle(float(x), y, 4 + 8 * abs(n))
        if i % 4 == 0:
            py5.stroke(*GRID, 120)
            py5.stroke_weight(1)
            py5.line(float(x), H * 0.28, float(x), H * 0.82)

    pulse = smoothstep(max(0.0, (recurrence - 0.72) / 0.28))
    if pulse > 0:
        py5.no_fill()
        for r in range(4):
            py5.stroke(*TEAL, int((80 - r * 14) * pulse))
            py5.stroke_weight(2)
            py5.rect(W * 0.5, base_y, W * (0.22 + r * 0.13), H * (0.12 + r * 0.08), 8)


def update_modes() -> float:
    global smooth_modes
    modes = np.abs(mode_matrix @ q)
    smooth_modes = 0.90 * smooth_modes + 0.10 * modes
    recurrence = smooth_modes[0] / (np.sum(smooth_modes) + 1e-5)
    return float(np.clip(recurrence, 0.0, 1.0))


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
    integrate()
    recurrence = update_modes()
    t = py5.frame_count / FPS
    draw_background(t)
    draw_mode_scope(t, recurrence)
    draw_resonators(t, recurrence)
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
