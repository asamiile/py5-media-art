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

BG = (7, 13, 12)
GLASS = (22, 39, 35)
LEAF = (42, 95, 61)
LEAF_DARK = (18, 47, 35)
CYAN = (74, 215, 197)
LIME = (149, 222, 101)
AMBER = (233, 172, 72)
MIST = (178, 217, 198)
WHITE = (222, 231, 219)

rng = np.random.default_rng()
LEAVES = 18
PORES_PER_LEAF = 120
leaf_pos = rng.uniform(0.0, 1.0, (LEAVES, 4))
pore_local = rng.normal(0.0, 0.32, (LEAVES, PORES_PER_LEAF, 2))
pore_phase = rng.uniform(0.0, math.tau, (LEAVES, PORES_PER_LEAF))
motes = rng.uniform(0.0, 1.0, (420, 4))
trace_phase = rng.uniform(0.0, math.tau, 5)


def rgba(rgb: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(alpha))))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], v: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1.0 - v) + b[i] * v) for i in range(3))


def draw_glow(draw: ImageDraw.ImageDraw, pts, color, alpha, width) -> None:
    for scale, a in ((7, alpha * 0.07), (3, alpha * 0.20), (1, alpha)):
        draw.line(pts, fill=rgba(color, a), width=max(1, int(width * scale)))


def leaf_polygon(cx: float, cy: float, rx: float, ry: float, angle: float) -> list[tuple[float, float]]:
    pts = []
    ca, sa = math.cos(angle), math.sin(angle)
    for i in range(72):
        u = i / 72 * math.tau
        taper = 0.35 + 0.65 * abs(math.sin(u))
        x = math.cos(u) * rx * taper
        y = math.sin(u) * ry
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def render_frame(frame_no: int, frame_path: Path) -> None:
    w, h = PREVIEW_SIZE
    loop = frame_no / TOTAL_FRAMES
    t = loop * DURATION_SEC
    day = 0.5 + 0.5 * math.sin(loop * math.tau - math.pi / 2)

    img = Image.new("RGB", PREVIEW_SIZE, BG)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(44):
        y0 = int(i / 44 * h)
        y1 = int((i + 1) / 44 * h + 1)
        draw.rectangle((0, y0, w, y1), fill=rgba(mix(BG, (11, 31, 24), i / 43), 230))

    bed = (w * 0.06, h * 0.13, w * 0.76, h * 0.88)
    draw.rounded_rectangle(bed, radius=10, fill=rgba(GLASS, 112), outline=rgba(MIST, 72), width=2)
    for x in np.linspace(bed[0] + 40, bed[2] - 40, 13):
        draw.line((x, bed[1], x, bed[3]), fill=rgba(MIST, 18), width=1)
    for y in np.linspace(bed[1] + 40, bed[3] - 40, 8):
        draw.line((bed[0], y, bed[2], y), fill=rgba(MIST, 15), width=1)

    overlay = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    for i, (lx, ly, scale, rot_seed) in enumerate(leaf_pos):
        cx = bed[0] + lx * (bed[2] - bed[0])
        cy = bed[1] + ly * (bed[3] - bed[1])
        rx = w * (0.045 + 0.03 * scale)
        ry = h * (0.075 + 0.03 * (1 - scale))
        angle = (rot_seed - 0.5) * 1.9 + 0.08 * math.sin(t * 0.7 + i)
        open_amount = 0.22 + 0.78 * (0.55 * day + 0.45 * (0.5 + 0.5 * math.sin(t * 1.1 + i * 0.8)))
        pts = leaf_polygon(cx, cy, rx, ry, angle)
        color = mix(LEAF_DARK, LEAF, open_amount)
        od.polygon(pts, fill=rgba(color, 152), outline=rgba(LIME, 42 + 40 * open_amount))
        ca, sa = math.cos(angle), math.sin(angle)
        od.line((cx - ca * rx * 0.88, cy - sa * rx * 0.88, cx + ca * rx * 0.88, cy + sa * rx * 0.88), fill=rgba(LIME, 50), width=1)

        for p in range(PORES_PER_LEAF):
            px, py = pore_local[i, p]
            if (px / 0.78) ** 2 + (py / 1.0) ** 2 > 1.0:
                continue
            local_x = px * rx * 0.8
            local_y = py * ry * 0.76
            x = cx + local_x * ca - local_y * sa
            y = cy + local_x * sa + local_y * ca
            pulse = 0.5 + 0.5 * math.sin(t * 2.0 + pore_phase[i, p])
            aperture = open_amount * (0.55 + 0.45 * pulse)
            r = 1.2 + 3.2 * aperture
            col = CYAN if aperture > 0.55 else LIME
            od.ellipse((x - r * 1.8, y - r * 0.7, x + r * 1.8, y + r * 0.7), fill=rgba(col, 22 + 78 * aperture))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.24))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    # Light curtain and mist.
    curtain_x = bed[0] + (loop * 1.3 % 1.0) * (bed[2] - bed[0])
    draw_glow(draw, ((curtain_x, bed[1]), (curtain_x, bed[3])), CYAN, 82, 1.6)
    for x, y, sp, hue in motes:
        px = (bed[0] + x * (bed[2] - bed[0]) + t * (4 + 16 * sp)) % w
        py = bed[1] + ((y + 0.04 * math.sin(t * 0.4 + x * 9)) % 1.0) * (bed[3] - bed[1])
        col = MIST if hue > 0.35 else AMBER
        draw.ellipse((px - 1.4, py - 1.4, px + 1.4, py + 1.4), fill=rgba(col, 10 + 34 * sp))

    panel_x = w * 0.81
    for i, (name, color) in enumerate((("CO2", CYAN), ("HUM", MIST), ("PAR", AMBER), ("VPD", LIME), ("TEMP", WHITE))):
        base_y = h * (0.18 + i * 0.12)
        pts = []
        for j in range(90):
            u = j / 89
            y = base_y + math.sin(u * math.tau * (1.5 + i * 0.28) + t * (1.1 + i * 0.18) + trace_phase[i]) * h * 0.022
            pts.append((panel_x + u * w * 0.13, y))
        draw.text((panel_x, base_y - h * 0.043), name, fill=rgba(color, 94))
        draw_glow(draw, pts, color, 58, 1.2)

    aperture_meter = day
    draw.rounded_rectangle((panel_x, h * 0.80, panel_x + w * 0.13, h * 0.825), radius=5, outline=rgba(MIST, 70), width=1)
    draw.rounded_rectangle((panel_x, h * 0.80, panel_x + w * 0.13 * aperture_meter, h * 0.825), radius=5, fill=rgba(LIME, 110))

    draw.text((w * 0.045, h * 0.045), "GREENHOUSE STOMATA CLOCK", fill=rgba(WHITE, 132))
    draw.text((w * 0.045, h * 0.074), f"APERTURE {aperture_meter:0.2f} / LIGHT CO2 HUMIDITY", fill=rgba(CYAN, 100))
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
