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

BG = (8, 10, 12)
CONCRETE = (38, 43, 45)
TRACK = (18, 21, 23)
CYAN = (72, 208, 207)
AMBER = (232, 168, 69)
ROSE = (198, 91, 112)
GREEN = (106, 188, 126)
WHITE = (218, 226, 218)

rng = np.random.default_rng()
FLOW_LINES = 78
line_seed = rng.uniform(0, 1, (FLOW_LINES, 4))
people = rng.uniform(0, 1, (80, 4))
particles = rng.uniform(0, 1, (520, 4))
sensor_phase = rng.uniform(0, math.tau, 5)


def rgba(c: tuple[int, int, int], a: float) -> tuple[int, int, int, int]:
    return (c[0], c[1], c[2], max(0, min(255, int(a))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1 - v) + b[i] * v) for i in range(3))


def glow_line(draw: ImageDraw.ImageDraw, pts, color, alpha, width) -> None:
    for scale, aa in ((7, alpha * 0.07), (3, alpha * 0.22), (1, alpha)):
        draw.line(pts, fill=rgba(color, aa), width=max(1, int(width * scale)))


def render_frame(frame_no: int, path: Path) -> None:
    w, h = PREVIEW_SIZE
    loop = frame_no / TOTAL_FRAMES
    t = loop * DURATION_SEC
    train = (loop * 1.18) % 1.0

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(44):
        y0 = int(i / 44 * h)
        y1 = int((i + 1) / 44 * h + 1)
        draw.rectangle((0, y0, w, y1), fill=rgba(mix(BG, (22, 25, 28), i / 43), 230))

    station = (w * 0.05, h * 0.16, w * 0.79, h * 0.84)
    draw.rounded_rectangle(station, radius=8, fill=rgba((15, 18, 20), 210), outline=rgba(CONCRETE, 120), width=2)
    platform_y = h * 0.58
    track_y = h * 0.73
    draw.rectangle((station[0], platform_y, station[2], platform_y + h * 0.09), fill=rgba(CONCRETE, 190))
    draw.rectangle((station[0], track_y, station[2], station[3]), fill=rgba(TRACK, 230))
    for x in np.linspace(station[0] + 40, station[2] - 40, 16):
        draw.line((x, station[1], x, station[3]), fill=rgba(CONCRETE, 20), width=1)
    for x in np.linspace(station[0] + 30, station[2] - 30, 13):
        draw.rectangle((x, station[1] + 20, x + 12, platform_y), fill=rgba(CONCRETE, 88))

    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    train_x = station[0] - w * 0.34 + train * (station[2] - station[0] + w * 0.68)
    train_box = (train_x, h * 0.66, train_x + w * 0.42, h * 0.80)
    od.rounded_rectangle(train_box, radius=10, fill=rgba((36, 42, 45), 190), outline=rgba(CYAN, 72), width=2)
    for k in range(7):
        wx = train_box[0] + w * 0.035 + k * w * 0.052
        od.rectangle((wx, train_box[1] + 18, wx + w * 0.033, train_box[1] + 52), fill=rgba(CYAN if k % 2 else AMBER, 64))

    pressure = math.exp(-((train - 0.52) / 0.28) ** 2)
    for i, (sy, amp, speed, hue) in enumerate(line_seed):
        y0 = station[1] + sy * (platform_y - station[1] + h * 0.14)
        pts = []
        for j in range(120):
            u = j / 119
            x = station[0] + u * (station[2] - station[0])
            wave = math.sin(u * math.tau * (1.2 + amp * 3.0) + t * (0.8 + speed * 1.6) + sy * 8) * h * (0.008 + 0.018 * pressure)
            pull = -pressure * h * 0.055 * math.exp(-abs(u - train) * 5.0)
            pts.append((x, y0 + wave + pull))
        color = CYAN if hue > 0.46 else (AMBER if hue > 0.2 else GREEN)
        glow_line(od, pts, color, 26 + 48 * pressure, 1.0)

    for px, py, sp, hue in people:
        x = station[0] + px * (station[2] - station[0])
        y = platform_y - 8 - py * h * 0.035
        sway = math.sin(t * (0.8 + sp) + px * 10) * 3
        color = AMBER if hue > 0.58 else CYAN
        od.ellipse((x - 4 + sway, y - 18, x + 4 + sway, y - 10), fill=rgba(color, 70))
        od.line((x + sway, y - 10, x + sway, y + 10), fill=rgba(WHITE, 56), width=2)

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.25))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    for x, y, sp, hue in particles:
        drift = pressure * (20 + 80 * sp)
        px = (station[0] + x * (station[2] - station[0]) - drift + t * (4 + 12 * sp)) % w
        py = station[1] + y * (station[3] - station[1])
        if station[0] < px < station[2]:
            color = ROSE if hue < 0.18 else (AMBER if hue < 0.42 else CYAN)
            draw.ellipse((px - 1.2, py - 1.2, px + 1.2, py + 1.2), fill=rgba(color, 8 + 32 * sp))

    panel_x = w * 0.84
    for i, label in enumerate(("PM2.5", "CO2", "TEMP", "FAN", "FLOW")):
        base = h * (0.18 + i * 0.13)
        color = (ROSE, CYAN, AMBER, GREEN, WHITE)[i]
        draw.text((panel_x, base - 31), label, fill=rgba(color, 95))
        pts = []
        for j in range(78):
            u = j / 77
            y = base + math.sin(u * math.tau * (1.5 + i * 0.25) + t * (1.1 + i * 0.18) + sensor_phase[i]) * h * 0.018
            y += pressure * h * 0.018 * math.sin(u * math.tau * 4 + i)
            pts.append((panel_x + u * w * 0.12, y))
        glow_line(draw, pts, color, 54, 1.1)

    sweep = station[0] + (loop * 1.6 % 1.0) * (station[2] - station[0])
    glow_line(draw, ((sweep, station[1]), (sweep, station[3])), CYAN, 56, 1.1)
    draw.text((w * 0.045, h * 0.045), "SUBWAY PLATFORM AIRFLOW", fill=rgba(WHITE, 130))
    draw.text((w * 0.045, h * 0.074), f"TRAIN PRESSURE {pressure:0.2f} / VENTILATION MAP", fill=rgba(CYAN, 100))
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
