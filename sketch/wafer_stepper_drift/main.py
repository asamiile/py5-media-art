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
COLS = 17
ROWS = 11

BG = (6, 8, 12)
WAFER = (20, 25, 30)
GRID = (50, 60, 65)
CYAN = (46, 223, 213)
VIOLET = (146, 118, 240)
AMBER = (244, 180, 70)
SILVER = (216, 225, 223)


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)

    global rng, dose, overlay, die_mask, particles
    rng = np.random.default_rng()
    dose = np.zeros((ROWS, COLS), dtype=np.float32)
    overlay = rng.normal(0.0, 1.0, (ROWS, COLS, 2)).astype(np.float32)
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    cx = (COLS - 1) / 2
    cy = (ROWS - 1) / 2
    die_mask = (((xx - cx) / (COLS * 0.50)) ** 2 + ((yy - cy) / (ROWS * 0.52)) ** 2) < 1.0
    particles = rng.uniform(0, 1, (180, 3)).astype(np.float32)


def draw_background(t: float) -> None:
    py5.background(*BG)
    py5.no_stroke()
    for x, y, s in particles:
        pulse = 0.4 + 0.6 * math.sin(t * (0.8 + s) + x * 9.0) ** 2
        py5.fill(*CYAN if s < 0.5 else AMBER, 10 + 38 * pulse)
        py5.circle(float(x) * W, float(y) * H, 1.0 + 2.4 * float(s))
    py5.fill(*SILVER, 110)
    py5.text_size(13)
    py5.text("WAFER STEPPER DRIFT / OVERLAY CONTROL FIELD", W * 0.5, H * 0.065)


def update_dose(t: float) -> float:
    global dose, overlay
    scan = (t * 0.22) % 1.0
    exposure_col = scan * (COLS + 4) - 2
    for r in range(ROWS):
        for c in range(COLS):
            if not die_mask[r, c]:
                dose[r, c] *= 0.992
                continue
            distance = abs(c - exposure_col)
            slit = max(0.0, 1.0 - distance / 1.25)
            dose[r, c] = min(1.0, dose[r, c] * 0.996 + slit * 0.075)
    overlay *= 0.988
    overlay += rng.normal(0.0, 0.018, overlay.shape).astype(np.float32)
    return exposure_col


def wafer_geometry() -> tuple[float, float, float, float, float]:
    cx = W * 0.5
    cy = H * 0.55
    radius = H * 0.39
    cell_w = radius * 1.50 / COLS
    cell_h = radius * 1.16 / ROWS
    return cx, cy, radius, cell_w, cell_h


def draw_wafer(t: float, exposure_col: float) -> None:
    cx, cy, radius, cell_w, cell_h = wafer_geometry()
    py5.no_stroke()
    py5.fill(*WAFER, 238)
    py5.circle(cx, cy, radius * 2.0)
    py5.fill(13, 18, 23, 210)
    py5.circle(cx, cy, radius * 1.85)
    py5.no_fill()
    for ring in range(4):
        py5.stroke(*GRID, 72 - ring * 10)
        py5.stroke_weight(1)
        py5.circle(cx, cy, radius * (1.75 - ring * 0.28))

    x0 = cx - (COLS - 1) * cell_w / 2
    y0 = cy - (ROWS - 1) * cell_h / 2
    for r in range(ROWS):
        for c in range(COLS):
            if not die_mask[r, c]:
                continue
            x = x0 + c * cell_w
            y = y0 + r * cell_h
            d = float(dose[r, c])
            py5.no_stroke()
            py5.fill(CYAN[0], CYAN[1], CYAN[2], 22 + 105 * d)
            py5.rect(x, y, cell_w * 0.76, cell_h * 0.70, 3)
            py5.fill(VIOLET[0], VIOLET[1], VIOLET[2], 10 + 58 * d)
            py5.rect(x, y, cell_w * 0.46, cell_h * 0.37, 2)
            py5.stroke(*SILVER, 42)
            py5.stroke_weight(1)
            py5.no_fill()
            py5.rect(x, y, cell_w * 0.78, cell_h * 0.72, 3)

            if (r + c) % 5 == 0:
                ox, oy = overlay[r, c] * 7.0
                py5.stroke(*AMBER, 55 + 75 * d)
                py5.line(x, y, x + float(ox), y + float(oy))
                py5.no_stroke()
                py5.fill(*AMBER, 92)
                py5.circle(x + float(ox), y + float(oy), 3.5)

    scan_x = x0 + exposure_col * cell_w
    py5.no_stroke()
    py5.fill(*CYAN, 26)
    py5.rect(scan_x, cy, cell_w * 2.1, radius * 1.75, 4)
    py5.stroke(*CYAN, 150)
    py5.stroke_weight(2)
    py5.line(scan_x, cy - radius * 0.86, scan_x, cy + radius * 0.86)
    py5.no_fill()
    py5.stroke(*AMBER, 85)
    py5.stroke_weight(1.5)
    py5.arc(cx, cy, radius * 1.96, radius * 1.96, -0.8 + t * 0.8, 0.8 + t * 0.8)


def draw_controls(t: float) -> None:
    cx, cy, radius, _, _ = wafer_geometry()
    left = cx - radius * 1.25
    right = cx + radius * 1.25
    py5.no_stroke()
    for i in range(8):
        v = 0.5 + 0.5 * math.sin(t * (1.1 + i * 0.09) + i * 0.7)
        rgb = [CYAN, VIOLET, AMBER, SILVER][i % 4]
        py5.fill(rgb[0], rgb[1], rgb[2], 42)
        py5.rect(left, H * (0.24 + i * 0.055), 76, 28, 3)
        py5.fill(rgb[0], rgb[1], rgb[2], 135)
        py5.rect(left - 24 + v * 48, H * (0.24 + i * 0.055), 10, 18, 2)
    py5.no_fill()
    py5.stroke(*SILVER, 70)
    py5.rect(right, H * 0.21, 112, 70, 5)
    py5.stroke(*CYAN, 145)
    py5.circle(right, H * 0.21, 38 + 18 * math.sin(t * 1.7) ** 2)
    py5.fill(*SILVER, 115)
    py5.text_size(11)
    py5.text("ALIGN", right, H * 0.28)


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
    exposure_col = update_dose(t)
    draw_background(t)
    draw_wafer(t, exposure_col)
    draw_controls(t)
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
