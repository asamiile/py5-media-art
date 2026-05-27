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

BG = (9, 10, 12)
SHELF = (30, 27, 24)
BOOK = (76, 70, 58)
CYAN = (72, 210, 203)
AMBER = (231, 166, 68)
ROSE = (190, 91, 121)
GREEN = (104, 184, 117)
PAPER = (210, 197, 154)
WHITE = (222, 226, 215)

rng = np.random.default_rng()
ROWS = 9
COLS = 52
book_hues = rng.choice([0, 1, 2, 3, 4], (ROWS, COLS), p=[0.48, 0.18, 0.14, 0.12, 0.08])
book_widths = rng.uniform(0.55, 1.25, (ROWS, COLS))
book_offsets = rng.uniform(-0.18, 0.18, (ROWS, COLS))
trace_seeds = rng.uniform(0, 1, (120, 4))
dust = rng.uniform(0, 1, (360, 4))


def rgba(rgb: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1.0 - v) + b[i] * v) for i in range(3))


def color_for(kind: int) -> tuple[int, int, int]:
    return (BOOK, CYAN, AMBER, ROSE, GREEN)[kind]


def draw_glow(draw: ImageDraw.ImageDraw, pts, color, alpha, width) -> None:
    for scale, a in ((8, alpha * 0.07), (3, alpha * 0.22), (1, alpha)):
        draw.line(pts, fill=rgba(color, a), width=max(1, int(width * scale)))


def render_frame(frame_no: int, frame_path: Path) -> None:
    w, h = PREVIEW_SIZE
    loop = frame_no / TOTAL_FRAMES
    t = loop * DURATION_SEC
    scan = (loop * 1.22) % 1.0

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(44):
        y0 = int(i / 44 * h)
        y1 = int((i + 1) / 44 * h + 1)
        draw.rectangle((0, y0, w, y1), fill=rgba(mix(BG, (27, 22, 18), i / 43), 224))

    area = (w * 0.06, h * 0.12, w * 0.78, h * 0.88)
    row_h = (area[3] - area[1]) / ROWS
    col_w = (area[2] - area[0]) / COLS
    draw.rounded_rectangle(area, radius=7, fill=rgba((18, 16, 15), 190), outline=rgba(PAPER, 55), width=2)

    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    for r in range(ROWS):
        y0 = area[1] + r * row_h + 5
        y1 = y0 + row_h * 0.78
        od.rectangle((area[0], y1 + 5, area[2], y1 + 13), fill=rgba(SHELF, 210))
        for c in range(COLS):
            x = area[0] + c * col_w + 2
            bw = max(4, col_w * book_widths[r, c])
            lean = book_offsets[r, c] * 9
            pulse = 0.5 + 0.5 * math.sin(t * 1.3 + r * 0.8 + c * 0.17)
            kind = int(book_hues[r, c])
            base = color_for(kind)
            hot = abs(scan - c / COLS)
            alpha = 92 + 82 * max(0, 1 - hot * 18) + 28 * pulse
            col = mix(base, WHITE, 0.22 * pulse if kind else 0.06)
            od.polygon([(x + lean, y0), (x + bw + lean, y0), (x + bw - lean * 0.45, y1), (x - lean * 0.45, y1)], fill=rgba(col, alpha), outline=rgba(PAPER, 20))
            if c % 5 == 0:
                od.line((x + bw * 0.48, y0 + 5, x + bw * 0.48, y1 - 4), fill=rgba(PAPER, 34), width=1)
            if max(0, 1 - hot * 18) > 0:
                od.rectangle((x, y0, x + bw, y0 + 3), fill=rgba(CYAN, 80 * max(0, 1 - hot * 18)))

    # Circulation traces between shelves and panel.
    for sx, sy, sp, hue in trace_seeds:
        u = (sx + t * (0.02 + sp * 0.04)) % 1.0
        row = int(sy * ROWS)
        y = area[1] + (row + 0.5) * row_h
        x1 = area[0] + u * (area[2] - area[0])
        x2 = w * (0.83 + 0.11 * sp)
        color = CYAN if hue > 0.55 else AMBER
        pts = []
        for i in range(32):
            q = i / 31
            x = x1 * (1 - q) + x2 * q
            yy = y + math.sin(q * math.pi) * h * (0.025 + 0.05 * sp)
            pts.append((x, yy))
        draw_glow(od, pts, color, 26 + 45 * sp, 1.0)

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.22))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    scan_x = area[0] + scan * (area[2] - area[0])
    draw_glow(draw, ((scan_x, area[1]), (scan_x, area[3])), CYAN, 90, 1.4)

    for x, y, sp, hue in dust:
        px = (x * w + t * (3 + 10 * sp)) % w
        py = (y * h + math.sin(t * 0.4 + x * 8) * 3) % h
        col = PAPER if hue > 0.35 else CYAN
        draw.ellipse((px - 1.2, py - 1.2, px + 1.2, py + 1.2), fill=rgba(col, 8 + 28 * sp))

    panel_x = w * 0.83
    for i, label in enumerate(("CALL", "HOLDS", "LIGHT", "AIR", "SCAN")):
        base_y = h * (0.17 + i * 0.13)
        draw.text((panel_x, base_y - 32), label, fill=rgba(PAPER, 95))
        pts = []
        color = (CYAN, AMBER, GREEN, ROSE, WHITE)[i]
        for j in range(76):
            q = j / 75
            y = base_y + math.sin(q * math.tau * (1.4 + i * 0.3) + t * (1.2 + i * 0.2)) * h * 0.018
            pts.append((panel_x + q * w * 0.12, y))
        draw_glow(draw, pts, color, 55, 1.1)

    draw.text((w * 0.045, h * 0.045), "LIBRARY STACK LUMINANCE", fill=rgba(WHITE, 130))
    draw.text((w * 0.045, h * 0.074), f"SHELF SCAN {scan:0.2f} / CIRCULATION MEMORY", fill=rgba(CYAN, 100))
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
