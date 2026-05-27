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

BG = (7, 11, 16)
NIGHT = (10, 24, 34)
GRID = (56, 75, 83)
CYAN = (70, 214, 214)
ICE = (169, 217, 225)
AMBER = (232, 170, 76)
MAGENTA = (188, 88, 137)
WHITE = (222, 231, 226)

rng = np.random.default_rng()
LAYER_COUNT = 18
BARB_COUNT = 34
telemetry = rng.uniform(0, 1, (160, 4))
clouds = rng.uniform(0, 1, (90, 4))
noise_phase = rng.uniform(0, math.tau, LAYER_COUNT)


def rgba(rgb: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1.0 - v) + b[i] * v) for i in range(3))


def draw_glow(draw: ImageDraw.ImageDraw, points, color, alpha, width) -> None:
    for scale, a in ((8, alpha * 0.07), (3, alpha * 0.22), (1, alpha)):
        draw.line(points, fill=rgba(color, a), width=max(1, int(width * scale)))


def profile_x(y_norm: float, t: float, w: int) -> float:
    return w * (0.48 + 0.12 * math.sin(y_norm * 9.0 + t * 0.58) + 0.045 * math.sin(y_norm * 31.0 - t * 1.25))


def render_frame(frame_no: int, frame_path: Path) -> None:
    w, h = PREVIEW_SIZE
    loop = frame_no / TOTAL_FRAMES
    t = loop * DURATION_SEC
    ascent = (loop * 1.08) % 1.0

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(56):
        y0 = int(i / 56 * h)
        y1 = int((i + 1) / 56 * h + 1)
        depth = i / 55
        draw.rectangle((0, y0, w, y1), fill=rgba(mix((5, 10, 16), NIGHT, depth), 235))

    plot = (w * 0.10, h * 0.10, w * 0.72, h * 0.88)
    skew = h * 0.06
    draw.polygon(
        [(plot[0], plot[3]), (plot[0] + skew, plot[1]), (plot[2] + skew, plot[1]), (plot[2], plot[3])],
        outline=rgba(GRID, 95),
        fill=rgba((11, 19, 24), 130),
    )
    for i in range(LAYER_COUNT):
        y = plot[3] - i / (LAYER_COUNT - 1) * (plot[3] - plot[1])
        pressure = 1000 - i * 48
        alpha = 22 + i * 2
        draw.line((plot[0] + i * skew / LAYER_COUNT, y, plot[2] + i * skew / LAYER_COUNT, y), fill=rgba(GRID, alpha), width=1)
        draw.text((plot[0] - 54, y - 6), f"{pressure}", fill=rgba(ICE, 60))

    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    # Temperature/dewpoint profiles.
    for color, offset, amp, alpha in ((CYAN, 0.0, 1.0, 115), (MAGENTA, 0.11, 0.75, 85), (AMBER, -0.09, 0.55, 70)):
        pts = []
        for j in range(160):
            yn = j / 159
            y = plot[3] - yn * (plot[3] - plot[1])
            x = profile_x(yn + offset, t, w) + amp * w * 0.035 * math.sin(yn * 17 + t * 0.9 + offset)
            x += yn * skew * 0.8
            pts.append((x, y))
        draw_glow(od, pts, color, alpha, 2)

    # Balloon trace.
    by = plot[3] - ascent * (plot[3] - plot[1])
    bx = profile_x(ascent, t, w) + ascent * skew * 0.8
    trail = []
    for j in range(90):
        a = max(0.0, ascent - j / 140)
        y = plot[3] - a * (plot[3] - plot[1])
        x = profile_x(a, t, w) + a * skew * 0.8
        trail.append((x, y))
    draw_glow(od, trail, WHITE, 60, 1.1)
    od.line((bx, by + 16, bx, by + 48), fill=rgba(WHITE, 85), width=1)
    od.ellipse((bx - 18, by - 28, bx + 18, by + 10), fill=rgba(ICE, 90), outline=rgba(WHITE, 130), width=1)
    od.rounded_rectangle((bx - 8, by + 46, bx + 8, by + 64), radius=2, fill=rgba(AMBER, 125))

    # Wind barbs.
    for i in range(BARB_COUNT):
        yn = i / (BARB_COUNT - 1)
        y = plot[3] - yn * (plot[3] - plot[1])
        x = w * 0.79
        angle = math.sin(yn * 8.5 + t * 0.62) * 0.9 - 0.35
        length = 28 + 34 * (0.5 + 0.5 * math.sin(yn * 13 + t))
        x2 = x + math.cos(angle) * length
        y2 = y + math.sin(angle) * length
        col = CYAN if i % 3 else AMBER
        od.line((x, y, x2, y2), fill=rgba(col, 72), width=2)
        for k in range(2 + i % 3):
            u = 0.45 + k * 0.18
            px = x * (1 - u) + x2 * u
            py = y * (1 - u) + y2 * u
            od.line((px, py, px - 10 * math.sin(angle), py + 10 * math.cos(angle)), fill=rgba(col, 65), width=1)

    # Cloud/moisture patches.
    for cx, cy, sp, size in clouds:
        x = (plot[0] + cx * (plot[2] - plot[0]) + math.sin(t * 0.2 + sp * 5) * 30)
        y = (plot[1] + cy * (plot[3] - plot[1]) - t * (4 + sp * 8)) % h
        if plot[1] < y < plot[3]:
            od.ellipse((x - 25 * size, y - 5 * size, x + 45 * size, y + 8 * size), fill=rgba(ICE, 7 + 18 * sp))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.28))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    # Telemetry panel.
    panel_x = w * 0.82
    for i in range(5):
        base_y = h * (0.18 + i * 0.105)
        pts = []
        for j in range(80):
            u = j / 79
            y = base_y + math.sin(u * math.tau * (2.0 + i * 0.35) + t * (1.1 + i * 0.2)) * h * 0.018
            pts.append((panel_x + u * w * 0.13, y))
        draw_glow(draw, pts, (CYAN, AMBER, MAGENTA, ICE, WHITE)[i], 55, 1)

    for x, y, sp, hue in telemetry:
        px = (x * w + t * (6 + sp * 18)) % w
        py = (y * h + math.sin(t * 0.5 + x * 9) * 4) % h
        color = CYAN if hue > 0.38 else AMBER
        draw.ellipse((px - 1.5, py - 1.5, px + 1.5, py + 1.5), fill=rgba(color, 10 + 35 * sp))

    draw.text((w * 0.045, h * 0.045), "RADIOSONDE WIND PROFILE", fill=rgba(WHITE, 130))
    draw.text((w * 0.045, h * 0.073), f"ASCENT {ascent:0.2f} / PRESSURE WIND TEMP", fill=rgba(CYAN, 100))
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
