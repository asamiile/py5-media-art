from __future__ import annotations

from pathlib import Path
import math
import os
import shutil
import subprocess
import sys

import numpy as np

try:
    import py5  # noqa: F401
except Exception as exc:
    PY5_IMPORT_ERROR = exc
else:
    PY5_IMPORT_ERROR = None

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

BG = (7, 9, 12)
GRAPHITE = (18, 24, 27)
STEEL = (72, 86, 88)
CYAN = (74, 220, 211)
VIOLET = (138, 105, 226)
AMBER = (239, 174, 74)
SMOKE = (128, 154, 147)
WHITE = (224, 235, 228)

rng = np.random.default_rng()
PANE_COUNT = 7
ROLLER_COUNT = 34
crack_seeds = rng.uniform(0, 1, (36, 5))
sensor_noise = rng.uniform(0, 1, (110, 4))
pane_offsets = rng.uniform(0, 1, PANE_COUNT)


def rgba(rgb: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1.0 - v) + b[i] * v) for i in range(3))


def smoothstep(v: float) -> float:
    v = max(0.0, min(1.0, v))
    return v * v * (3.0 - 2.0 * v)


def draw_glow_line(draw, points, color, alpha, width):
    for scale, a in ((6, alpha * 0.10), (3, alpha * 0.22), (1, alpha)):
        draw.line(points, fill=rgba(color, a), width=max(1, int(width * scale)), joint="curve")


def stress_color(v: float) -> tuple[int, int, int]:
    if v < 0.42:
        return mix(CYAN, VIOLET, v / 0.42)
    if v < 0.78:
        return mix(VIOLET, AMBER, (v - 0.42) / 0.36)
    return mix(AMBER, WHITE, (v - 0.78) / 0.22)


def pane_position(index: int, t: float, w: int, h: int) -> tuple[float, float, float, float, float]:
    cycle = (pane_offsets[index] + t * 0.062) % 1.0
    x = -w * 0.23 + cycle * w * 1.42
    y = h * (0.34 + 0.035 * math.sin(index * 0.9))
    pw = w * (0.30 + 0.035 * math.sin(index * 1.7))
    ph = h * (0.285 + 0.018 * math.cos(index * 1.1))
    heat = smoothstep(1.0 - abs(cycle - 0.52) / 0.34)
    return x, y, pw, ph, heat


def render_frame(frame_no: int, path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFilter

    w, h = PREVIEW_SIZE
    loop_t = frame_no / TOTAL_FRAMES
    t = loop_t * DURATION_SEC

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")

    for i in range(44):
        y0 = int(i / 44 * h)
        y1 = int((i + 1) / 44 * h + 1)
        depth = i / 43
        draw.rectangle((0, y0, w, y1), fill=rgba(mix(BG, (20, 34, 37), depth), 210))

    # Annealing tunnel zones.
    for i, x in enumerate(np.linspace(w * 0.11, w * 0.89, 6)):
        temp = math.sin(t * 0.55 + i * 0.7) * 0.5 + 0.5
        color = AMBER if i < 3 else CYAN
        draw.rectangle((x - w * 0.06, h * 0.12, x + w * 0.06, h * 0.74), fill=rgba(color, 9 + 20 * temp))
        draw.line((x, h * 0.12, x, h * 0.74), fill=rgba(color, 45 + 30 * temp), width=1)

    # Rollers and rails.
    rail_y = h * 0.68
    draw.rectangle((0, rail_y - h * 0.018, w, rail_y + h * 0.055), fill=rgba(GRAPHITE, 205))
    for i in range(ROLLER_COUNT):
        x = (i / (ROLLER_COUNT - 1)) * w
        spin = (t * 2.7 + i * 0.34) % math.tau
        draw.ellipse((x - 22, rail_y - 11, x + 22, rail_y + 11), fill=rgba((30, 39, 41), 245), outline=rgba(STEEL, 130), width=2)
        draw.line((x - math.cos(spin) * 18, rail_y - math.sin(spin) * 6, x + math.cos(spin) * 18, rail_y + math.sin(spin) * 6), fill=rgba(CYAN, 38), width=1)

    # Heat haze.
    for sx, sy, sp, hue in sensor_noise:
        x = (sx * w + t * (8 + sp * 24)) % w
        y = h * (0.15 + sy * 0.50)
        color = AMBER if hue > 0.54 else CYAN
        draw.rounded_rectangle((x, y, x + 18 + 30 * sp, y + 1.5), radius=2, fill=rgba(color, 10 + 35 * sp))

    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    for i in range(PANE_COUNT):
        x, y, pw, ph, heat = pane_position(i, t, w, h)
        if x + pw * 0.55 < 0 or x - pw * 0.55 > w:
            continue

        left = x - pw * 0.5
        top = y - ph * 0.5
        right = x + pw * 0.5
        bottom = y + ph * 0.5
        od.rounded_rectangle((left, top, right, bottom), radius=8, fill=rgba((23, 37, 41), 96), outline=rgba(SMOKE, 112), width=2)
        od.rectangle((left + 6, top + 6, right - 6, bottom - 6), outline=rgba(CYAN, 30 + 80 * heat), width=1)

        center_count = 9
        for band in range(center_count):
            v = band / (center_count - 1)
            color = stress_color((v * 0.76 + heat * 0.38 + i * 0.11) % 1.0)
            alpha = 35 + heat * 120 * (1.0 - abs(v - 0.52))
            points = []
            for j in range(95):
                u = j / 94
                px = left + u * pw
                wave = math.sin(u * math.tau * (1.7 + band * 0.13) + t * 1.2 + i) * ph * 0.035
                wave += math.sin(u * math.tau * 5.0 - t * 1.8 + band) * ph * 0.012
                py = top + ph * (0.16 + v * 0.68) + wave
                points.append((px, py))
            draw_glow_line(od, points, color, alpha, 1.4 + heat * 1.4)

        # Stress cracks and edge strain markers.
        for sx, sy, angle, length, local in crack_seeds:
            if int(local * PANE_COUNT) != i:
                continue
            cx = left + sx * pw
            cy = top + sy * ph
            flicker = 0.5 + 0.5 * math.sin(t * 2.2 + sx * 7.0)
            if flicker < 0.28:
                continue
            crack_len = (0.03 + length * 0.10) * pw
            ex = cx + math.cos(angle * math.tau + heat) * crack_len
            ey = cy + math.sin(angle * math.tau + heat * 0.5) * crack_len * 0.28
            od.line((cx, cy, ex, ey), fill=rgba(WHITE, (38 + 82 * heat) * flicker), width=1)

        od.rectangle((left, bottom - 5, right, bottom), fill=rgba(AMBER, 16 + heat * 55))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.35))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    # Polarizer frame and meters.
    draw.rectangle((w * 0.055, h * 0.09, w * 0.945, h * 0.78), outline=rgba(SMOKE, 62), width=2)
    draw.line((w * 0.055, h * 0.09, w * 0.945, h * 0.78), fill=rgba(VIOLET, 24), width=1)
    draw.line((w * 0.055, h * 0.78, w * 0.945, h * 0.09), fill=rgba(CYAN, 24), width=1)

    for i in range(5):
        x = w * (0.08 + i * 0.055)
        level = 0.42 + 0.48 * math.sin(t * 0.75 + i * 0.9) ** 2
        draw.rectangle((x, h * 0.86 - h * 0.10 * level, x + 10, h * 0.86), fill=rgba((CYAN if i % 2 else AMBER), 105))
        draw.rectangle((x - 3, h * 0.75, x + 13, h * 0.865), outline=rgba(STEEL, 95), width=1)

    draw.text((w * 0.045, h * 0.045), "ANNEALING STRESS FIELD", fill=rgba(WHITE, 125))
    draw.text((w * 0.045, h * 0.071), "CROSSED POLARIZER / THERMAL RELIEF", fill=rgba(CYAN, 92))
    img.convert("RGB").save(path)


def run() -> None:
    if PY5_IMPORT_ERROR is not None:
        print(f"[{WORK_NAME}] py5 unavailable; using PIL headless renderer: {PY5_IMPORT_ERROR}")
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

    for frame_no in range(TOTAL_FRAMES):
        render_frame(frame_no, FRAMES_DIR / f"frame-{frame_no + 1:04d}.png")
        if (frame_no + 1) % 60 == 0:
            pct = (frame_no + 1) / TOTAL_FRAMES * 100
            print(f"[Render Progress] Frame {frame_no + 1}/{TOTAL_FRAMES} ({pct:.1f}%)", flush=True)

    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-r",
            str(FPS),
            "-i",
            str(FRAMES_DIR / "frame-%04d.png"),
            "-vf",
            f"scale={OUTPUT_SIZE[0]}:{OUTPUT_SIZE[1]}:flags=lanczos",
            "-vcodec",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ],
        check=True,
    )
    shutil.copyfile(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)
    shutil.rmtree(FRAMES_DIR)
    print("[Render Cleanup] Temporary frames directory successfully removed.")


if __name__ == "__main__":
    run()
