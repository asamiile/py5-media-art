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

BG = (8, 10, 13)
PANEL = (18, 23, 27)
RAIL = (91, 106, 104)
CYAN = (64, 214, 204)
GREEN = (96, 198, 126)
AMBER = (232, 165, 66)
RED = (219, 82, 74)
WHITE = (218, 226, 216)

rng = np.random.default_rng()
NODES = np.array(
    [
        [0.08, 0.32], [0.22, 0.32], [0.36, 0.32], [0.50, 0.32], [0.64, 0.32], [0.82, 0.32],
        [0.22, 0.52], [0.36, 0.52], [0.50, 0.52], [0.64, 0.52], [0.82, 0.52],
        [0.08, 0.70], [0.24, 0.70], [0.42, 0.70], [0.60, 0.70], [0.82, 0.70],
    ],
    dtype=float,
)
EDGES = [
    (0, 1), (1, 2), (2, 3), (3, 4), (4, 5),
    (1, 6), (2, 7), (3, 8), (4, 9), (5, 10),
    (6, 7), (7, 8), (8, 9), (9, 10),
    (11, 12), (12, 13), (13, 14), (14, 15),
    (6, 12), (7, 13), (8, 14), (9, 15),
]
edge_phase = rng.uniform(0, math.tau, len(EDGES))
relay_phase = rng.uniform(0, math.tau, 72)
relay_state = rng.random(72)
sparks = rng.uniform(0, 1, (260, 4))


def rgba(rgb: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1.0 - v) + b[i] * v) for i in range(3))


def draw_glow(draw: ImageDraw.ImageDraw, points, color, alpha, width) -> None:
    for scale, a in ((7, alpha * 0.08), (3, alpha * 0.24), (1, alpha)):
        draw.line(points, fill=rgba(color, a), width=max(1, int(width * scale)))


def render_frame(frame_no: int, frame_path: Path) -> None:
    w, h = PREVIEW_SIZE
    loop = frame_no / TOTAL_FRAMES
    t = loop * DURATION_SEC

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(42):
        y0 = int(i / 42 * h)
        y1 = int((i + 1) / 42 * h + 1)
        draw.rectangle((0, y0, w, y1), fill=rgba(mix(BG, (14, 27, 32), i / 41), 225))

    panel = (w * 0.045, h * 0.13, w * 0.955, h * 0.84)
    draw.rounded_rectangle(panel, radius=8, fill=rgba(PANEL, 220), outline=rgba(RAIL, 96), width=2)
    for x in np.linspace(panel[0] + 40, panel[2] - 40, 18):
        draw.line((x, panel[1], x, panel[3]), fill=rgba(RAIL, 16), width=1)
    for y in np.linspace(panel[1] + 40, panel[3] - 40, 10):
        draw.line((panel[0], y, panel[2], y), fill=rgba(RAIL, 14), width=1)

    sx0, sy0, sx1, sy1 = panel
    pts = [(sx0 + p[0] * (sx1 - sx0), sy0 + p[1] * (sy1 - sy0)) for p in NODES]
    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    for idx, (a, b) in enumerate(EDGES):
        pulse = (math.sin(t * 1.1 + edge_phase[idx]) + 1.0) * 0.5
        lock = (math.sin(t * 0.43 + idx * 0.7) + 1.0) * 0.5
        color = GREEN if lock > 0.62 else (AMBER if pulse > 0.72 else CYAN)
        p1, p2 = pts[a], pts[b]
        draw_glow(od, (p1, p2), color, 48 + 80 * pulse, 2.0)
        if pulse > 0.84:
            u = (t * 0.38 + idx * 0.13) % 1.0
            x = p1[0] * (1 - u) + p2[0] * u
            y = p1[1] * (1 - u) + p2[1] * u
            od.ellipse((x - 8, y - 8, x + 8, y + 8), fill=rgba(WHITE, 130))

    for idx, (x, y) in enumerate(pts):
        state = (math.sin(t * 1.5 + idx * 0.63) + 1.0) * 0.5
        color = RED if state > 0.86 else (GREEN if state > 0.52 else CYAN)
        od.ellipse((x - 15, y - 15, x + 15, y + 15), fill=rgba(color, 36 + 70 * state), outline=rgba(WHITE, 88), width=1)
        od.ellipse((x - 4, y - 4, x + 4, y + 4), fill=rgba(color, 190))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.25))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    # Relay memory blocks.
    start_x, start_y = w * 0.075, h * 0.865
    for i in range(72):
        col, row = i % 24, i // 24
        x = start_x + col * w * 0.033
        y = start_y + row * h * 0.037
        hot = (math.sin(t * (1.1 + relay_state[i]) + relay_phase[i]) + 1.0) * 0.5
        color = AMBER if hot > 0.76 else (CYAN if hot > 0.42 else RAIL)
        draw.rounded_rectangle((x, y, x + w * 0.022, y + h * 0.018), radius=3, fill=rgba(color, 35 + 125 * hot), outline=rgba(WHITE, 28), width=1)

    sweep_x = w * (0.08 + (loop * 1.5 % 1.0) * 0.84)
    draw_glow(draw, ((sweep_x, h * 0.15), (sweep_x, h * 0.81)), CYAN, 70, 1.6)

    for x, y, sp, hue in sparks:
        px = (x * w + t * (4 + 14 * sp)) % w
        py = (y * h + math.sin(t * 0.8 + x * 7) * 3) % h
        color = AMBER if hue > 0.66 else CYAN
        draw.ellipse((px - 1.5, py - 1.5, px + 1.5, py + 1.5), fill=rgba(color, 8 + 35 * sp))

    draw.text((w * 0.045, h * 0.045), "RAIL INTERLOCKING MEMORY", fill=rgba(WHITE, 128))
    draw.text((w * 0.045, h * 0.074), f"ROUTE LOCK CYCLE {loop:0.2f} / RELAY OCCUPANCY", fill=rgba(CYAN, 98))
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
