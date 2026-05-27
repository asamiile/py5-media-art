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

BG = (9, 8, 8)
BRICK = (48, 30, 24)
CLAY = (92, 56, 39)
EMBER = (236, 103, 53)
AMBER = (236, 174, 71)
CYAN = (72, 205, 196)
VIOLET = (138, 91, 178)
WHITE = (232, 221, 190)

rng = np.random.default_rng()
TILE_ROWS = 5
TILE_COLS = 12
tile_phase = rng.uniform(0, math.tau, (TILE_ROWS, TILE_COLS))
cone_phase = rng.uniform(0, math.tau, 18)
ash = rng.uniform(0, 1, (460, 4))


def rgba(c: tuple[int, int, int], a: float) -> tuple[int, int, int, int]:
    return (c[0], c[1], c[2], max(0, min(255, int(a))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1 - v) + b[i] * v) for i in range(3))


def glow_line(draw: ImageDraw.ImageDraw, pts, color, alpha, width) -> None:
    for scale, aa in ((9, alpha * 0.06), (4, alpha * 0.20), (1, alpha)):
        draw.line(pts, fill=rgba(color, aa), width=max(1, int(width * scale)))


def render_frame(frame_no: int, path: Path) -> None:
    w, h = PREVIEW_SIZE
    loop = frame_no / TOTAL_FRAMES
    t = loop * DURATION_SEC
    heat = 0.18 + 0.82 * (0.5 - 0.5 * math.cos(math.tau * loop))

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(48):
        y0 = int(i / 48 * h)
        y1 = int((i + 1) / 48 * h + 1)
        draw.rectangle((0, y0, w, y1), fill=rgba(mix(BG, (34, 16, 14), i / 47), 230))

    chamber = (w * 0.07, h * 0.12, w * 0.78, h * 0.88)
    draw.rounded_rectangle(chamber, radius=16, fill=rgba((18, 11, 10), 218), outline=rgba(BRICK, 145), width=4)
    for r in range(11):
        y = chamber[1] + r / 10 * (chamber[3] - chamber[1])
        draw.line((chamber[0], y, chamber[2], y), fill=rgba(BRICK, 38), width=1)
    for c in range(16):
        x = chamber[0] + c / 15 * (chamber[2] - chamber[0])
        draw.line((x, chamber[1], x, chamber[3]), fill=rgba(BRICK, 22), width=1)

    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    # Thermal rings.
    center = (w * 0.42, h * 0.50)
    for k in range(18):
        radius = (0.08 + k * 0.026 + 0.015 * math.sin(t * 0.55 + k)) * w
        alpha = (22 + 72 * heat) * (1 - k / 22)
        color = mix(EMBER, AMBER, k / 18)
        box = (center[0] - radius, center[1] - radius * 0.72, center[0] + radius, center[1] + radius * 0.72)
        od.ellipse(box, outline=rgba(color, alpha), width=2)

    # Glaze witness tiles.
    tile_w = (chamber[2] - chamber[0]) * 0.048
    tile_h = (chamber[3] - chamber[1]) * 0.105
    for r in range(TILE_ROWS):
        for c in range(TILE_COLS):
            x = chamber[0] + w * 0.10 + c * tile_w * 1.55
            y = chamber[1] + h * 0.16 + r * tile_h * 1.35
            melt = heat * (0.65 + 0.35 * math.sin(t * 0.9 + tile_phase[r, c]) ** 2)
            color = mix(CLAY, AMBER if (r + c) % 4 else VIOLET, melt)
            od.rounded_rectangle((x, y, x + tile_w, y + tile_h), radius=5, fill=rgba(color, 110 + 90 * melt), outline=rgba(WHITE, 26 + 40 * melt), width=1)
            drip = tile_h * 0.5 * melt * math.sin(tile_phase[r, c]) ** 2
            od.line((x + tile_w * 0.55, y + tile_h * 0.72, x + tile_w * 0.50, y + tile_h * 0.72 + drip), fill=rgba(EMBER, 70 * melt), width=3)

    # Pyrometric cones.
    for i in range(18):
        x = chamber[0] + w * (0.58 + 0.12 * (i % 3)) + (i // 3) * 4
        y = chamber[1] + h * (0.20 + 0.095 * (i // 3))
        bend = heat * (0.25 + 0.75 * (0.5 + 0.5 * math.sin(t + cone_phase[i])))
        pts = [(x, y + 54), (x + 16 * bend, y - 28), (x + 28, y + 54)]
        od.polygon(pts, fill=rgba(mix(CLAY, WHITE, bend * 0.45), 128), outline=rgba(AMBER, 80 * bend))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.35))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    # Side telemetry.
    px = w * 0.83
    for i, label in enumerate(("CONE", "OXY", "RAMP", "SOAK", "GLOW")):
        base = h * (0.18 + i * 0.13)
        color = (AMBER, CYAN, EMBER, VIOLET, WHITE)[i]
        pts = []
        for j in range(80):
            u = j / 79
            y = base + math.sin(u * math.tau * (1.6 + i * 0.33) + t * (1.2 + i * 0.22)) * h * 0.018
            pts.append((px + u * w * 0.13, y))
        draw.text((px, base - 32), label, fill=rgba(color, 95))
        glow_line(draw, pts, color, 56, 1.2)

    sweep = chamber[0] + (loop * 1.5 % 1.0) * (chamber[2] - chamber[0])
    glow_line(draw, ((sweep, chamber[1]), (sweep, chamber[3])), CYAN, 58, 1.2)
    for x, y, sp, hue in ash:
        ax = (x * w + t * (4 + 18 * sp)) % w
        ay = (y * h - t * (2 + 8 * sp)) % h
        color = AMBER if hue > 0.45 else WHITE
        draw.ellipse((ax - 1.3, ay - 1.3, ax + 1.3, ay + 1.3), fill=rgba(color, 7 + 28 * sp * heat))

    draw.text((w * 0.045, h * 0.045), "KILN PYROMETRY RINGS", fill=rgba(WHITE, 130))
    draw.text((w * 0.045, h * 0.074), f"FIRING HEAT {heat:0.2f} / CONE BEND MAP", fill=rgba(AMBER, 104))
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
