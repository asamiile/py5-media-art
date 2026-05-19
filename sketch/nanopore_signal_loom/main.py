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
CHANNELS = 12
TRACE_LEN = 150

BG = (7, 9, 13)
PANEL = (15, 21, 27)
GRID = (45, 57, 63)
CYAN = (45, 224, 212)
GREEN = (110, 222, 124)
AMBER = (244, 179, 72)
VIOLET = (150, 122, 238)
SILVER = (216, 226, 224)
ROSE = (238, 86, 116)
BASE_COLORS = [CYAN, GREEN, AMBER, VIOLET]


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)

    global rng, traces, pore_phase, events, molecules, quality
    rng = np.random.default_rng()
    traces = rng.uniform(0.44, 0.58, (CHANNELS, TRACE_LEN)).astype(np.float32)
    pore_phase = rng.uniform(0, math.tau, CHANNELS).astype(np.float32)
    quality = rng.uniform(0.65, 0.96, CHANNELS).astype(np.float32)
    events = []
    molecules = rng.uniform(0, 1, (170, 4)).astype(np.float32)


def update_signals(t: float) -> None:
    global traces, events, molecules, quality
    traces = np.roll(traces, -1, axis=1)
    for ch in range(CHANNELS):
        baseline = 0.50 + 0.035 * math.sin(t * 0.85 + float(pore_phase[ch]))
        blockage = 0.0
        if rng.random() < 0.15:
            base = int(rng.integers(0, 4))
            blockage = [0.16, -0.11, 0.08, -0.18][base] * rng.uniform(0.65, 1.0)
            events.append([ch, base, 1.0, blockage])
            quality[ch] = min(1.0, quality[ch] + rng.uniform(0.002, 0.012))
        quality[ch] += (0.78 - quality[ch]) * 0.002
        traces[ch, -1] = np.clip(baseline + blockage + rng.normal(0.0, 0.016), 0.1, 0.9)

    for ev in events:
        ev[2] -= 0.025
    events = [ev for ev in events if ev[2] > 0]

    molecules[:, 1] += 0.0018 + molecules[:, 3] * 0.0025
    molecules[:, 0] += np.sin(t * 0.7 + molecules[:, 2] * 8.0) * 0.0009
    molecules[molecules[:, 1] > 0.88, 1] = 0.10
    molecules[:, 0] %= 1.0


def draw_shell(t: float) -> None:
    py5.background(*BG)
    py5.no_stroke()
    py5.fill(*PANEL, 240)
    py5.rect(W * 0.5, H * 0.53, W * 0.84, H * 0.72, 6)
    py5.fill(20, 27, 32, 190)
    py5.rect(W * 0.5, H * 0.53, W * 0.76, H * 0.60, 4)
    py5.stroke(*GRID, 62)
    py5.stroke_weight(1)
    for y in np.linspace(H * 0.24, H * 0.82, 12):
        py5.line(W * 0.12, y, W * 0.88, y)
    for x in np.linspace(W * 0.14, W * 0.86, 16):
        py5.line(x, H * 0.22, x, H * 0.84)
    py5.no_stroke()
    py5.fill(*SILVER, 120)
    py5.text_size(13)
    py5.text("NANOPORE SIGNAL LOOM / LIVE BASECALL CURRENT", W * 0.5, H * 0.065)


def draw_molecules(t: float) -> None:
    py5.no_stroke()
    for x, y, ph, size in molecules:
        alpha = 16 + 42 * (0.5 + 0.5 * math.sin(t + float(ph) * 9.0))
        rgb = BASE_COLORS[int(float(ph) * 4) % 4]
        py5.fill(rgb[0], rgb[1], rgb[2], alpha)
        py5.circle(float(x) * W, float(y) * H, 1.6 + float(size) * 5.0)


def draw_channels(t: float) -> None:
    left = W * 0.18
    right = W * 0.82
    top = H * 0.25
    spacing = H * 0.045
    trace_w = right - left
    for ch in range(CHANNELS):
        y = top + ch * spacing
        q = float(quality[ch])
        py5.no_fill()
        py5.stroke(*GRID, 120)
        py5.stroke_weight(1)
        py5.rect((left + right) * 0.5, y, trace_w, spacing * 0.64, 3)
        py5.stroke(CYAN[0], CYAN[1], CYAN[2], 35 + 90 * q)
        py5.stroke_weight(1.5)
        py5.begin_shape()
        for i, val in enumerate(traces[ch]):
            x = left + i / (TRACE_LEN - 1) * trace_w
            py = y + (float(val) - 0.5) * spacing * 2.2
            py5.curve_vertex(x, py)
        py5.end_shape()
        pulse = 0.5 + 0.5 * math.sin(t * 1.6 + float(pore_phase[ch]))
        py5.no_stroke()
        py5.fill(*CYAN, 45 + 100 * pulse)
        py5.circle(left - 32, y, 10 + 10 * pulse)
        py5.fill(*SILVER, 105)
        py5.text_size(9)
        py5.text(f"{ch:02d}", left - 62, y)


def draw_events(t: float) -> None:
    left = W * 0.18
    top = H * 0.25
    spacing = H * 0.045
    for ch, base, life, blockage in events:
        y = top + int(ch) * spacing
        x = W * (0.56 + 0.25 * (1.0 - life))
        rgb = BASE_COLORS[int(base)]
        py5.no_fill()
        py5.stroke(rgb[0], rgb[1], rgb[2], int(190 * life))
        py5.stroke_weight(2)
        py5.circle(x, y, 16 + 42 * life)
        py5.no_stroke()
        py5.fill(rgb[0], rgb[1], rgb[2], int(130 * life))
        py5.text_size(12)
        py5.text("ACGT"[int(base)], x, y)


def draw_quality_panel(t: float) -> None:
    x = W * 0.82
    y0 = H * 0.20
    mean_q = float(np.mean(quality))
    py5.no_fill()
    py5.stroke(*SILVER, 65)
    py5.rect(x, y0, 118, 54, 5)
    py5.no_stroke()
    py5.fill(*GREEN, 55 + 115 * mean_q)
    py5.rect(x - 46 + 46 * mean_q, y0, 92 * mean_q, 9, 3)
    py5.fill(*SILVER, 115)
    py5.text_size(10)
    py5.text(f"Q {mean_q:.2f}", x, y0 + 27)


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
    update_signals(t)
    draw_shell(t)
    draw_molecules(t)
    draw_channels(t)
    draw_events(t)
    draw_quality_panel(t)
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
