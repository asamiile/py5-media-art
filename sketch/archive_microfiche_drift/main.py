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

BG = (8, 10, 8)
FILM = (24, 33, 25)
GRID = (67, 89, 68)
PHOSPHOR = (119, 224, 129)
AMBER = (224, 170, 74)
CREAM = (218, 211, 166)
RED = (194, 82, 72)

rng = np.random.default_rng()
CARD_COUNT = 11
TEXT_ROWS = 58
CARD_OFFSETS = rng.uniform(0.0, 1.0, CARD_COUNT)
ROW_PHASES = rng.uniform(0.0, math.tau, (CARD_COUNT, TEXT_ROWS))
ROW_LENGTHS = rng.uniform(0.15, 0.92, (CARD_COUNT, TEXT_ROWS))
SCRATCHES = rng.uniform(0.0, 1.0, (70, 5))
DUST = rng.uniform(0.0, 1.0, (430, 4))


def rgba(rgb: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1.0 - v) + b[i] * v) for i in range(3))


def draw_glow(draw: ImageDraw.ImageDraw, points, color, alpha, width) -> None:
    for scale, a in ((7, alpha * 0.09), (3, alpha * 0.22), (1, alpha)):
        draw.line(points, fill=rgba(color, a), width=max(1, int(width * scale)))


def render_frame(frame_no: int, frame_path: Path) -> None:
    w, h = PREVIEW_SIZE
    loop_t = frame_no / TOTAL_FRAMES
    t = loop_t * DURATION_SEC
    scan = (loop_t * 1.08) % 1.0

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")

    for i in range(42):
        y0 = int(i / 42 * h)
        y1 = int((i + 1) / 42 * h + 1)
        draw.rectangle((0, y0, w, y1), fill=rgba(mix(BG, (13, 30, 24), i / 41), 230))

    # Scanner bed and registration rails.
    draw.rectangle((w * 0.04, h * 0.12, w * 0.96, h * 0.86), outline=rgba(GRID, 98), width=2)
    for x in np.linspace(w * 0.08, w * 0.92, 15):
        draw.line((x, h * 0.12, x, h * 0.86), fill=rgba(GRID, 24), width=1)
    for y in np.linspace(h * 0.18, h * 0.80, 8):
        draw.line((w * 0.04, y, w * 0.96, y), fill=rgba(GRID, 20), width=1)

    scan_x = w * (0.05 + scan * 0.90)
    for width, alpha in ((30, 9), (12, 32), (3, 132)):
        draw.line((scan_x, h * 0.10, scan_x, h * 0.88), fill=rgba(PHOSPHOR, alpha), width=width)

    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    for card in range(CARD_COUNT):
        cycle = (CARD_OFFSETS[card] + t * 0.045) % 1.0
        cx = w * (cycle * 1.25 - 0.12)
        cy = h * (0.30 + 0.33 * ((card % 3) / 2.0)) + math.sin(t * 0.65 + card) * h * 0.015
        cw = w * (0.28 + 0.025 * math.sin(card * 1.3))
        ch = h * 0.225
        if cx + cw < 0 or cx - cw > w:
            continue

        skew = math.sin(t * 0.38 + card * 0.6) * 18
        left = cx - cw * 0.5
        top = cy - ch * 0.5
        right = cx + cw * 0.5
        bottom = cy + ch * 0.5
        poly = [(left + skew, top), (right + skew * 0.4, top), (right - skew, bottom), (left - skew * 0.4, bottom)]
        od.polygon(poly, fill=rgba(FILM, 168), outline=rgba(CREAM, 72))
        od.rectangle((left + 12, top + 14, right - 12, bottom - 14), outline=rgba(PHOSPHOR, 34), width=1)

        # Dense rows of microtext as unreadable archive signal.
        for row in range(TEXT_ROWS):
            v = row / (TEXT_ROWS - 1)
            row_y = top + ch * (0.12 + v * 0.76)
            row_len = cw * ROW_LENGTHS[card, row] * (0.75 + 0.25 * math.sin(t * 0.9 + ROW_PHASES[card, row]))
            start = left + cw * (0.08 + 0.08 * math.sin(ROW_PHASES[card, row]))
            shimmer = 0.45 + 0.55 * math.sin(t * 2.2 + ROW_PHASES[card, row])
            color = PHOSPHOR if row % 7 else AMBER
            alpha = 18 + 68 * shimmer
            od.line((start + skew * (0.5 - v), row_y, start + row_len + skew * (0.5 - v), row_y), fill=rgba(color, alpha), width=1)
            if row % 9 == 0:
                od.rectangle((start - 6, row_y - 2, start - 1, row_y + 2), fill=rgba(CREAM, 36))

        # Frame notches and index dots.
        for notch in range(6):
            nx = left + cw * (0.12 + notch * 0.15)
            od.rectangle((nx, top + 4, nx + cw * 0.035, top + 10), fill=rgba(CREAM, 44))
            od.rectangle((nx, bottom - 10, nx + cw * 0.035, bottom - 4), fill=rgba(CREAM, 36))
        od.ellipse((left + 12, top + 12, left + 22, top + 22), outline=rgba(RED, 88), width=1)

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.28))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    for sx, sy, length, angle, alpha in SCRATCHES:
        x = (sx * w - t * (12 + length * 34)) % w
        y = sy * h
        l = 18 + length * 120
        x2 = x + math.cos(angle * math.tau) * l
        y2 = y + math.sin(angle * math.tau) * l * 0.18
        draw.line((x, y, x2, y2), fill=rgba(CREAM, 6 + 24 * alpha), width=1)

    for dx, dy, drift, size in DUST:
        x = (dx * w + t * (4 + drift * 11)) % w
        y = (dy * h + math.sin(t + dx * 12) * 4) % h
        color = PHOSPHOR if drift > 0.65 else CREAM
        draw.ellipse((x - size * 1.35, y - size * 1.35, x + size * 1.35, y + size * 1.35), fill=rgba(color, 8 + 25 * drift))

    # Waveform readout at bottom.
    base = h * 0.91
    for band, color in enumerate((PHOSPHOR, AMBER, CREAM)):
        pts = []
        for i in range(170):
            u = i / 169
            y = base + band * 18 + math.sin(u * math.tau * (4 + band) + t * (1.7 + band * 0.4)) * (7 + band * 2)
            y += math.sin(u * math.tau * 23 - t * 3.5) * 2
            pts.append((w * 0.08 + u * w * 0.84, y))
        draw_glow(draw, pts, color, 45, 1)

    draw.text((w * 0.045, h * 0.047), "ARCHIVE MICROFICHE DRIFT", fill=rgba(CREAM, 132))
    draw.text((w * 0.045, h * 0.075), f"SCAN GATE {scan:0.2f} / REGISTRATION FLOAT", fill=rgba(PHOSPHOR, 100))
    img.convert("RGB").save(frame_path)


def run() -> None:
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
