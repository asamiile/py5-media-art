from __future__ import annotations

from pathlib import Path
import math
import os
import shutil
import subprocess
import sys

import numpy as np
try:
    import py5
except Exception as exc:  # py5 can fail in headless Java/AWT sessions.
    py5 = None
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
W, H = SIZE

BG = (5, 10, 18)
DEEP = (8, 25, 39)
CYAN = (72, 214, 205)
GREEN = (82, 177, 138)
AMBER = (234, 177, 79)
CORAL = (232, 103, 93)
SILVER = (205, 220, 216)

CREATURE_COUNT = 2600
TRACE_COUNT = 220
RING_COUNT = 7

rng = np.random.default_rng()
creatures = {
    "x": rng.uniform(0.04, 0.96, CREATURE_COUNT),
    "base_y": rng.beta(4.6, 1.55, CREATURE_COUNT),
    "size": rng.uniform(1.0, 4.0, CREATURE_COUNT),
    "speed": rng.uniform(0.15, 0.75, CREATURE_COUNT),
    "phase": rng.uniform(0.0, math.tau, CREATURE_COUNT),
    "species": rng.choice([0, 1, 2], CREATURE_COUNT, p=[0.74, 0.19, 0.07]),
}
traces = rng.uniform(0.0, 1.0, (TRACE_COUNT, 5))
sonar_offsets = rng.uniform(0.0, 1.0, RING_COUNT)


def ease(v: float) -> float:
    v = max(0.0, min(1.0, v))
    return v * v * (3.0 - 2.0 * v)


def migration_lift(loop_t: float) -> float:
    # A seamless dusk-to-night-to-dawn lift curve.
    return 0.5 - 0.5 * math.cos(math.tau * loop_t)


def draw_glow_line(x1: float, y1: float, x2: float, y2: float, rgb: tuple[int, int, int], alpha: float, weight: float) -> None:
    for scale, a in ((7.5, alpha * 0.10), (3.2, alpha * 0.26), (1.0, alpha)):
        py5.stroke(*rgb, a)
        py5.stroke_weight(weight * scale)
        py5.line(x1, y1, x2, y2)


def draw_background(t: float, lift: float) -> None:
    py5.background(*BG)
    py5.no_stroke()

    for i in range(36):
        y = i / 36 * H
        depth = y / H
        alpha = 16 + 46 * depth
        py5.fill(DEEP[0], DEEP[1] + int(16 * depth), DEEP[2] + int(24 * depth), alpha)
        py5.rect(W / 2, y + H / 72, W, H / 34)

    py5.stroke(32, 55, 68, 80)
    py5.stroke_weight(1.0)
    for i in range(10):
        y = H * (0.14 + i * 0.078)
        wobble = 28 * math.sin(t * 0.34 + i * 0.7)
        py5.line(0, y + wobble, W, y - wobble * 0.35)

    horizon = H * (0.82 - 0.36 * lift)
    py5.no_fill()
    for i in range(18):
        y = horizon + (i - 9) * H * 0.018
        a = 18 + 38 * math.exp(-abs(i - 9) / 4.5)
        py5.stroke(CYAN[0], CYAN[1], CYAN[2], a)
        py5.stroke_weight(1.0 + i % 3)
        py5.begin_shape()
        for j in range(90):
            x = j / 89 * W
            wave = math.sin(j * 0.31 + t * 1.2 + i * 0.7) * H * 0.006
            wave += math.sin(j * 0.09 - t * 1.7 + i) * H * 0.004
            py5.vertex(x, y + wave)
        py5.end_shape()


def draw_sonar(t: float) -> None:
    origin_x = W * 0.12
    origin_y = H * 0.88
    max_r = W * 0.95
    py5.no_fill()
    for i, off in enumerate(sonar_offsets):
        radius = ((t * 0.115 + off) % 1.0) * max_r
        alpha = 95 * (1.0 - radius / max_r) ** 1.8
        if alpha < 2:
            continue
        py5.stroke(CYAN[0], CYAN[1], CYAN[2], alpha)
        py5.stroke_weight(1.3 + 1.2 * (1.0 - radius / max_r))
        py5.arc(origin_x, origin_y, radius * 2, radius * 2, -math.pi * 0.93, -math.pi * 0.07)

    sweep = -math.pi * (0.91 - 0.82 * ((t * 0.14) % 1.0))
    x2 = origin_x + math.cos(sweep) * max_r
    y2 = origin_y + math.sin(sweep) * max_r
    draw_glow_line(origin_x, origin_y, x2, y2, CYAN, 80, 1.4)


def draw_creatures(t: float, lift: float) -> None:
    x = creatures["x"]
    base_y = creatures["base_y"]
    phase = creatures["phase"]
    speed = creatures["speed"]
    species = creatures["species"]
    sizes = creatures["size"]

    shoal = 0.028 * np.sin(t * 1.7 + phase) + 0.018 * np.sin(t * 4.1 + x * 22.0)
    column = np.sin(x * 31.0 + t * 1.25) * 0.045 + np.sin(x * 11.0 - t * 0.9) * 0.035
    y_norm = base_y - lift * (0.42 + 0.12 * speed) + shoal + column
    y_norm = np.clip(y_norm, 0.10, 0.96)
    x_norm = (x + 0.018 * np.sin(t * (0.55 + speed) + phase * 1.7)) % 1.0

    px = x_norm * W
    py = y_norm * H
    density_glow = np.clip(1.0 - np.abs(y_norm - (0.82 - 0.36 * lift)) * 5.0, 0.0, 1.0)

    py5.no_stroke()
    for idx in range(CREATURE_COUNT):
        pulse = 0.55 + 0.45 * math.sin(t * (2.4 + speed[idx]) + phase[idx])
        if species[idx] == 0:
            rgb = CYAN
            alpha = 32 + 82 * density_glow[idx] + 38 * pulse
        elif species[idx] == 1:
            rgb = GREEN
            alpha = 26 + 64 * density_glow[idx] + 30 * pulse
        else:
            rgb = AMBER if pulse > 0.48 else CORAL
            alpha = 42 + 110 * pulse
        radius = sizes[idx] * (1.0 + 1.8 * density_glow[idx] + 0.5 * pulse)
        py5.fill(rgb[0], rgb[1], rgb[2], alpha * 0.18)
        py5.circle(px[idx], py[idx], radius * 5.2)
        py5.fill(rgb[0], rgb[1], rgb[2], alpha)
        py5.circle(px[idx], py[idx], radius)


def draw_diagnostic_traces(t: float, lift: float) -> None:
    panel_x = W * 0.79
    panel_w = W * 0.16
    top = H * 0.14
    py5.no_fill()
    for i in range(5):
        rgb = (CYAN, GREEN, AMBER, SILVER, CORAL)[i]
        py5.stroke(*rgb, 58)
        py5.stroke_weight(1.2)
        y_mid = top + i * H * 0.07
        py5.begin_shape()
        for j in range(95):
            u = j / 94
            y = y_mid + math.sin(u * math.tau * (1.5 + i * 0.3) + t * (1.2 + i * 0.15)) * H * 0.018
            y += math.sin(u * math.tau * 6 + t * 2.4 + i) * H * 0.004
            py5.vertex(panel_x + u * panel_w, y)
        py5.end_shape()

    py5.no_stroke()
    for tx, ty, sp, hue, sz in traces:
        drift = (tx + t * (0.012 + sp * 0.025)) % 1.0
        x = W * (0.05 + drift * 0.88)
        y = H * (0.12 + ty * 0.72 - lift * 0.10)
        rgb = CYAN if hue < 0.58 else (AMBER if hue < 0.83 else CORAL)
        blink = 0.5 + 0.5 * math.sin(t * (1.4 + sp * 3.0) + tx * 15.0)
        py5.fill(rgb[0], rgb[1], rgb[2], 14 + 56 * blink)
        py5.rect(x, y, 18 + sz * 36, 1.5 + sz * 4, 2)


def render_frame() -> None:
    loop_t = (py5.frame_count - 1) / TOTAL_FRAMES
    t = loop_t * DURATION_SEC
    lift = migration_lift(loop_t)

    draw_background(t, lift)
    draw_sonar(t)
    draw_diagnostic_traces(t, lift)
    draw_creatures(t, lift)

    py5.fill(220, 235, 230, 115)
    py5.text_size(18)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("DIEL SCATTERING LAYER", W * 0.045, H * 0.045)
    py5.fill(CYAN[0], CYAN[1], CYAN[2], 90)
    py5.text_size(12)
    py5.text(f"SONAR RETURN {lift:0.2f}", W * 0.045, H * 0.073)


def compile_video() -> None:
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


def setup() -> None:
    if py5 is None:
        return
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.frame_rate(FPS)
    py5.smooth()
    py5.rect_mode(py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)
    print(f"[{WORK_NAME}] Rendering {TOTAL_FRAMES} frames at {SIZE[0]}x{SIZE[1]}.")


def draw() -> None:
    if py5 is None:
        return
    render_frame()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        pct = py5.frame_count / TOTAL_FRAMES * 100
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({pct:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        compile_video()
        os._exit(0)


def _mix(c1: tuple[int, int, int], c2: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(c1[i] * (1.0 - v) + c2[i] * v) for i in range(3))


def _rgba(rgb: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def _draw_headless_frame(frame_no: int, frame_path: Path) -> None:
    from PIL import Image, ImageDraw

    w, h = PREVIEW_SIZE
    sx = w / W
    sy = h / H
    loop_t = frame_no / TOTAL_FRAMES
    t = loop_t * DURATION_SEC
    lift = migration_lift(loop_t)

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")

    for i in range(42):
        y0 = int(i / 42 * h)
        y1 = int((i + 1) / 42 * h + 2)
        depth = i / 41
        color = _mix(BG, (10, 42, 62), depth)
        draw.rectangle((0, y0, w, y1), fill=_rgba(color, 82 + 80 * depth))

    horizon = h * (0.82 - 0.36 * lift)
    for i in range(18):
        y = horizon + (i - 9) * h * 0.018
        a = 18 + 50 * math.exp(-abs(i - 9) / 4.4)
        points = []
        for j in range(96):
            x = j / 95 * w
            wave = math.sin(j * 0.31 + t * 1.2 + i * 0.7) * h * 0.006
            wave += math.sin(j * 0.09 - t * 1.7 + i) * h * 0.004
            points.append((x, y + wave))
        draw.line(points, fill=_rgba(CYAN, a), width=max(1, int(1.4 + i % 3)))

    origin_x = w * 0.12
    origin_y = h * 0.88
    max_r = w * 0.95
    for off in sonar_offsets:
        radius = ((t * 0.115 + off) % 1.0) * max_r
        alpha = 85 * (1.0 - radius / max_r) ** 1.8
        if alpha < 2:
            continue
        box = (origin_x - radius, origin_y - radius, origin_x + radius, origin_y + radius)
        draw.arc(box, start=193, end=347, fill=_rgba(CYAN, alpha), width=max(1, int(2.0 * (1.0 - radius / max_r) + 1)))

    sweep = -math.pi * (0.91 - 0.82 * ((t * 0.14) % 1.0))
    x2 = origin_x + math.cos(sweep) * max_r
    y2 = origin_y + math.sin(sweep) * max_r
    for width, alpha in ((12, 8), (5, 28), (2, 76)):
        draw.line((origin_x, origin_y, x2, y2), fill=_rgba(CYAN, alpha), width=width)

    for i in range(5):
        rgb = (CYAN, GREEN, AMBER, SILVER, CORAL)[i]
        y_mid = h * (0.14 + i * 0.07)
        points = []
        for j in range(96):
            u = j / 95
            y = y_mid + math.sin(u * math.tau * (1.5 + i * 0.3) + t * (1.2 + i * 0.15)) * h * 0.018
            y += math.sin(u * math.tau * 6 + t * 2.4 + i) * h * 0.004
            points.append((w * 0.79 + u * w * 0.16, y))
        draw.line(points, fill=_rgba(rgb, 60), width=2)

    x = creatures["x"]
    base_y = creatures["base_y"]
    phase = creatures["phase"]
    speed = creatures["speed"]
    species = creatures["species"]
    sizes = creatures["size"]
    shoal = 0.028 * np.sin(t * 1.7 + phase) + 0.018 * np.sin(t * 4.1 + x * 22.0)
    column = np.sin(x * 31.0 + t * 1.25) * 0.045 + np.sin(x * 11.0 - t * 0.9) * 0.035
    y_norm = np.clip(base_y - lift * (0.42 + 0.12 * speed) + shoal + column, 0.10, 0.96)
    x_norm = (x + 0.018 * np.sin(t * (0.55 + speed) + phase * 1.7)) % 1.0
    px = x_norm * w
    py = y_norm * h
    density_glow = np.clip(1.0 - np.abs(y_norm - (0.82 - 0.36 * lift)) * 5.0, 0.0, 1.0)

    for idx in range(CREATURE_COUNT):
        pulse = 0.55 + 0.45 * math.sin(t * (2.4 + speed[idx]) + phase[idx])
        if species[idx] == 0:
            rgb = CYAN
            alpha = 34 + 92 * density_glow[idx] + 36 * pulse
        elif species[idx] == 1:
            rgb = GREEN
            alpha = 30 + 70 * density_glow[idx] + 28 * pulse
        else:
            rgb = AMBER if pulse > 0.48 else CORAL
            alpha = 46 + 118 * pulse
        radius = max(0.9, sizes[idx] * sx * (1.0 + 1.7 * density_glow[idx] + 0.45 * pulse))
        cx = px[idx]
        cy = py[idx]
        draw.ellipse((cx - radius * 2.8, cy - radius * 2.8, cx + radius * 2.8, cy + radius * 2.8), fill=_rgba(rgb, alpha * 0.11))
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=_rgba(rgb, alpha))

    for tx, ty, sp, hue, sz in traces:
        drift = (tx + t * (0.012 + sp * 0.025)) % 1.0
        xx = w * (0.05 + drift * 0.88)
        yy = h * (0.12 + ty * 0.72 - lift * 0.10)
        rgb = CYAN if hue < 0.58 else (AMBER if hue < 0.83 else CORAL)
        blink = 0.5 + 0.5 * math.sin(t * (1.4 + sp * 3.0) + tx * 15.0)
        draw.rounded_rectangle((xx, yy, xx + 8 + sz * 18, yy + 1.4 + sz * 3), radius=2, fill=_rgba(rgb, 18 + 62 * blink))

    draw.text((w * 0.045, h * 0.045), "DIEL SCATTERING LAYER", fill=_rgba(SILVER, 118))
    draw.text((w * 0.045, h * 0.073), f"SONAR RETURN {lift:0.2f}", fill=_rgba(CYAN, 95))
    img.save(frame_path)


def run_headless() -> None:
    print(f"[{WORK_NAME}] py5 unavailable; using PIL headless renderer: {PY5_IMPORT_ERROR}")
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)

    for frame_no in range(TOTAL_FRAMES):
        _draw_headless_frame(frame_no, FRAMES_DIR / f"frame-{frame_no + 1:04d}.png")
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


if py5 is None:
    run_headless()
else:
    py5.run_sketch()
