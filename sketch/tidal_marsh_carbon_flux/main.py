from __future__ import annotations

from pathlib import Path
import math
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

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

BG = (7, 12, 13)
PEAT = (35, 27, 20)
MUD = (67, 52, 36)
WATER = (42, 111, 116)
CYAN = (74, 215, 201)
GREEN = (105, 185, 92)
AMBER = (230, 166, 70)
SILVER = (205, 218, 205)

rng = np.random.default_rng()
STEMS = 180
ROOTS = 130
BUBBLES = 360
stems = rng.uniform(0, 1, (STEMS, 5))
roots = rng.uniform(0, 1, (ROOTS, 5))
bubbles = rng.uniform(0, 1, (BUBBLES, 4))
trace_phase = rng.uniform(0, math.tau, 5)


def rgba(c: tuple[int, int, int], a: float) -> tuple[int, int, int, int]:
    return (c[0], c[1], c[2], max(0, min(255, int(a))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1.0 - v) + b[i] * v) for i in range(3))


def glow(draw: ImageDraw.ImageDraw, pts, color, alpha, width) -> None:
    for scale, aa in ((7, alpha * 0.07), (3, alpha * 0.22), (1, alpha)):
        draw.line(pts, fill=rgba(color, aa), width=max(1, int(width * scale)))


def render_frame(frame_no: int, path: Path) -> None:
    w, h = PREVIEW_SIZE
    loop = frame_no / TOTAL_FRAMES
    t = loop * DURATION_SEC
    tide = 0.5 + 0.5 * math.sin(loop * math.tau - 0.5)
    waterline = h * (0.47 - 0.15 * tide)
    marsh_top = h * 0.52

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(48):
        y0 = int(i / 48 * h)
        y1 = int((i + 1) / 48 * h + 1)
        draw.rectangle((0, y0, w, y1), fill=rgba(mix(BG, (15, 31, 27), i / 47), 230))

    field = (w * 0.06, h * 0.12, w * 0.77, h * 0.89)
    draw.rounded_rectangle(field, radius=10, fill=rgba((10, 20, 19), 184), outline=rgba(SILVER, 54), width=2)
    for y in np.linspace(field[1], field[3], 11):
        draw.line((field[0], y, field[2], y), fill=rgba(SILVER, 14), width=1)

    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    # Sediment strata.
    for i in range(7):
        y0 = marsh_top + i * (field[3] - marsh_top) / 7
        y1 = marsh_top + (i + 1) * (field[3] - marsh_top) / 7 + 2
        col = mix(MUD, PEAT, i / 6)
        od.rectangle((field[0], y0, field[2], y1), fill=rgba(col, 198))
        pts = []
        for j in range(100):
            u = j / 99
            x = field[0] + u * (field[2] - field[0])
            y = y0 + 8 * math.sin(u * math.tau * (2 + i * 0.3) + t * 0.25 + i)
            pts.append((x, y))
        od.line(pts, fill=rgba(AMBER if i < 2 else CYAN, 30), width=1)

    # Tide water.
    od.rectangle((field[0], waterline, field[2], marsh_top), fill=rgba(WATER, 66 + 60 * tide))
    for k in range(12):
        y = waterline + k * (marsh_top - waterline) / 12
        pts = []
        for j in range(90):
            u = j / 89
            x = field[0] + u * (field[2] - field[0])
            pts.append((x, y + math.sin(u * math.tau * 4 + t * 1.1 + k) * 3))
        glow(od, pts, CYAN, 24 + 34 * tide, 1)

    # Stems.
    for x0, height, sway, phase, hue in stems:
        x = field[0] + x0 * (field[2] - field[0])
        base = marsh_top + 5
        top = base - h * (0.08 + height * 0.28)
        bend = math.sin(t * (0.7 + sway) + phase * math.tau) * (7 + 18 * tide)
        pts = []
        for j in range(18):
            q = j / 17
            pts.append((x + bend * q * q, base * (1 - q) + top * q))
        color = GREEN if hue > 0.25 else AMBER
        od.line(pts, fill=rgba(color, 65 + 70 * height), width=2)

    # Root flux lines.
    for x0, y0, length, phase, hue in roots:
        x = field[0] + x0 * (field[2] - field[0])
        y = marsh_top + y0 * (field[3] - marsh_top)
        pts = []
        for j in range(38):
            q = j / 37
            xx = x + math.sin(q * math.tau * 1.2 + phase * math.tau) * w * 0.025 * q
            yy = y + q * length * h * 0.22
            pts.append((xx, yy))
        color = CYAN if hue > 0.45 else AMBER
        glow(od, pts, color, 22 + 42 * tide, 0.8)

    for x0, y0, sp, hue in bubbles:
        x = field[0] + x0 * (field[2] - field[0]) + math.sin(t + y0 * 8) * 6
        y = (field[3] - ((y0 + t * (0.015 + sp * 0.03)) % 1.0) * (field[3] - waterline))
        if waterline < y < field[3]:
            color = CYAN if hue > 0.35 else AMBER
            od.ellipse((x - 1.7, y - 1.7, x + 1.7, y + 1.7), fill=rgba(color, 12 + 42 * sp))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.22))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    panel_x = w * 0.82
    for i, label in enumerate(("TIDE", "CO2", "CH4", "REDOX", "SAL")):
        base = h * (0.18 + i * 0.13)
        color = (CYAN, GREEN, AMBER, SILVER, WATER)[i]
        draw.text((panel_x, base - 31), label, fill=rgba(color, 95))
        pts = []
        for j in range(78):
            u = j / 77
            y = base + math.sin(u * math.tau * (1.4 + i * 0.25) + t * (1.0 + i * 0.16) + trace_phase[i]) * h * 0.018
            pts.append((panel_x + u * w * 0.12, y))
        glow(draw, pts, color, 54, 1.1)

    scan_x = field[0] + (loop * 1.4 % 1.0) * (field[2] - field[0])
    glow(draw, ((scan_x, field[1]), (scan_x, field[3])), CYAN, 60, 1.1)
    draw.text((w * 0.045, h * 0.045), "TIDAL MARSH CARBON FLUX", fill=rgba(SILVER, 132))
    draw.text((w * 0.045, h * 0.074), f"TIDE {tide:0.2f} / ROOT RESPIRATION", fill=rgba(CYAN, 104))
    img.convert("RGB").save(path)


def run() -> None:
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    for frame_no in range(TOTAL_FRAMES):
        render_frame(frame_no, FRAMES_DIR / f"frame-{frame_no + 1:04d}.png")
        if (frame_no + 1) % 60 == 0:
            print(f"[Render Progress] Frame {frame_no + 1}/{TOTAL_FRAMES} ({(frame_no + 1) / TOTAL_FRAMES * 100:.1f}%)", flush=True)

    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
    subprocess.run([ffmpeg, "-y", "-r", str(FPS), "-i", str(FRAMES_DIR / "frame-%04d.png"), "-vf", f"scale={OUTPUT_SIZE[0]}:{OUTPUT_SIZE[1]}:flags=lanczos", "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(SKETCH_DIR / f"{WORK_NAME}.mp4")], check=True)
    shutil.copyfile(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)
    shutil.rmtree(FRAMES_DIR)
    print("[Render Cleanup] Temporary frames directory successfully removed.")


if __name__ == "__main__":
    run()
