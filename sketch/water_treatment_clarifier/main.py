from __future__ import annotations

import math
import os
import random
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


WORK_NAME = "water_treatment_clarifier"
SIZE = (1920, 1080)
OUTPUT_SIZE = (3840, 2160)
FPS = 60
DURATION = 10
FRAMES = FPS * DURATION
ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Floc:
    radius: float
    angle: float
    depth: float
    size: float
    drift: float
    phase: float
    density: float


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ring_point(cx: float, cy: float, rx: float, ry: float, angle: float) -> tuple[float, float]:
    return cx + math.cos(angle) * rx, cy + math.sin(angle) * ry


def make_palette(rng: random.Random) -> dict[str, tuple[int, int, int]]:
    blue_shift = rng.randint(-8, 10)
    return {
        "bg0": (8, 13, 18),
        "bg1": (18, 28 + blue_shift, 34 + blue_shift),
        "concrete": (116, 127, 122),
        "concrete_dark": (54, 62, 62),
        "water": (26, 108 + blue_shift, 128 + blue_shift),
        "water_hi": (93, 201, 203),
        "sludge": (97, 72, 48),
        "amber": (224, 156, 80),
        "green": (89, 183, 130),
        "foam": (215, 237, 223),
    }


def draw_gradient(draw: ImageDraw.ImageDraw, palette: dict[str, tuple[int, int, int]]) -> None:
    w, h = SIZE
    for y in range(h):
        u = y / (h - 1)
        c = tuple(int(lerp(palette["bg0"][i], palette["bg1"][i], u)) for i in range(3))
        draw.line([(0, y), (w, y)], fill=c)


def draw_clarifier(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    palette: dict[str, tuple[int, int, int]],
    frame: int,
) -> None:
    w, _ = SIZE
    cx, cy = 960, 555
    rx, ry = 710, 286
    phase = frame / FRAMES

    draw.ellipse((cx - rx - 38, cy - ry - 48, cx + rx + 38, cy + ry + 58), fill=(35, 45, 45), outline=palette["concrete"], width=8)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(15, 55, 66), outline=(178, 190, 183), width=5)

    water = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    wd = ImageDraw.Draw(water)
    for i in range(38):
        frac = i / 37
        y0 = cy - ry + frac * ry * 2
        mix = 0.38 * math.sin(frac * math.pi)
        band = tuple(int(lerp(palette["water"][j], palette["water_hi"][j], mix)) for j in range(3))
        wd.ellipse((cx - rx + 12, y0 - 45, cx + rx - 12, y0 + 45), outline=(*band, 30), width=20)

    for i in range(14):
        a = phase * 360 + i * 25.7
        width = 6 if i % 3 else 10
        col = (*palette["water_hi"], 34 + (i % 4) * 9)
        wd.arc((cx - rx + i * 12, cy - ry + i * 7, cx + rx - i * 12, cy + ry - i * 7), int(a), int(a + 130), fill=col, width=width)
    canvas.alpha_composite(water)

    angle = phase * math.tau
    draw.ellipse((cx - 78, cy - 48, cx + 78, cy + 48), fill=(37, 45, 44), outline=(196, 203, 194), width=5)
    draw.ellipse((cx - 32, cy - 20, cx + 32, cy + 20), fill=(14, 19, 20), outline=palette["amber"], width=3)
    for k in range(4):
        a = angle + k * math.pi / 2
        ex, ey = ring_point(cx, cy, rx * 0.82, ry * 0.82, a)
        sx, sy = ring_point(cx, cy, 88, 38, a + 0.05)
        draw.line((sx, sy, ex, ey), fill=(210, 218, 205), width=9)
        draw.line((sx, sy + 8, ex, ey + 8), fill=(64, 74, 72), width=4)
        for tooth in range(8):
            t = (tooth + 1) / 9
            px, py = lerp(sx, ex, t), lerp(sy, ey, t)
            draw.line((px, py, px - math.sin(a) * 13, py + math.cos(a) * 9), fill=(166, 176, 165), width=2)

    draw.rectangle((0, 896, w, 1080), fill=(17, 22, 22))
    draw.polygon([(248, 899), (1672, 899), (1810, 1080), (92, 1080)], fill=(34, 41, 39))
    for x in range(125, 1795, 98):
        pulse = 55 + int(40 * math.sin(phase * math.tau + x * 0.02))
        draw.line((x, 915, x - 64, 1080), fill=(74, 82, 78), width=2)
        draw.ellipse((x - 6, 910 - pulse * 0.02, x + 6, 922 - pulse * 0.02), fill=(129, 137, 126))


def draw_particles(
    draw: ImageDraw.ImageDraw,
    flocs: list[Floc],
    palette: dict[str, tuple[int, int, int]],
    frame: int,
) -> None:
    cx, cy = 960, 555
    phase = frame / FRAMES
    for floc in flocs:
        orbit = phase * math.tau * floc.drift + floc.phase
        a = floc.angle + orbit
        depth = (floc.depth + phase * floc.density) % 1.0
        rx = lerp(170, 650, floc.radius)
        ry = lerp(68, 256, floc.radius)
        x, y = ring_point(cx, cy, rx, ry, a)
        y = lerp(y - 120, y + 265, depth)
        x += 10 * math.sin(phase * math.tau * 3 + floc.phase)
        if y < 844:
            r = floc.size * lerp(0.65, 1.28, depth)
            col = palette["amber"] if depth > 0.55 else palette["foam"]
            alpha = int(lerp(85, 185, depth))
            draw.ellipse((x - r, y - r * 0.72, x + r, y + r * 0.72), fill=(*col, alpha))


def draw_turbidity_panel(
    draw: ImageDraw.ImageDraw,
    palette: dict[str, tuple[int, int, int]],
    frame: int,
) -> None:
    phase = frame / FRAMES
    x0, y0 = 1320, 90
    draw.rounded_rectangle((x0, y0, x0 + 430, y0 + 210), radius=8, fill=(13, 19, 20), outline=(91, 106, 101), width=2)
    draw.text((x0 + 24, y0 + 20), "TURBIDITY  /  SETTLING", fill=(202, 214, 199))
    for row, label in enumerate(("INLET", "RAKE", "EFFLUENT")):
        y = y0 + 66 + row * 43
        draw.text((x0 + 24, y - 10), label, fill=(128, 141, 132))
        draw.line((x0 + 126, y, x0 + 390, y), fill=(42, 53, 51), width=2)
        pts = []
        for i in range(92):
            u = i / 91
            amp = 24 - row * 5
            val = math.sin(u * math.tau * (2.0 + row * 0.6) + phase * math.tau * (1.6 + row)) * amp
            val += math.sin(u * math.tau * 7 + row + phase * math.tau) * 5
            pts.append((x0 + 126 + u * 264, y - val))
        color = palette["amber"] if row == 0 else palette["water_hi"] if row == 1 else palette["green"]
        draw.line(pts, fill=color, width=3)
    sweep = x0 + 126 + (phase % 1) * 264
    draw.line((sweep, y0 + 52, sweep, y0 + 184), fill=(231, 237, 218), width=1)


def render_frame(frame: int, flocs: list[Floc], palette: dict[str, tuple[int, int, int]]) -> Image.Image:
    base = Image.new("RGB", SIZE)
    bg = ImageDraw.Draw(base)
    draw_gradient(bg, palette)
    canvas = base.convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")

    draw_clarifier(canvas, draw, palette, frame)
    draw_particles(draw, flocs, palette, frame)
    draw_turbidity_panel(draw, palette, frame)

    phase = frame / FRAMES
    for i in range(8):
        y = 190 + i * 74
        glow = int(40 + 35 * math.sin(phase * math.tau * 2 + i))
        draw.line((135, y, 500, y + 22 * math.sin(phase * math.tau + i)), fill=(74, 202, 199, glow), width=2)
        draw.ellipse((118, y - 5, 128, y + 5), fill=(*palette["water_hi"], 120))
    draw.text((118, 92), "CLARIFIER FLOW FIELD", fill=(217, 224, 207))
    draw.text((118, 124), "coagulation / settling / sludge return", fill=(126, 142, 134))

    return canvas.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.1, percent=105, threshold=3))


def encode_video(frames_dir: Path, output: Path) -> None:
    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames_dir / "frame_%04d.png"),
        "-vf",
        f"scale={OUTPUT_SIZE[0]}:{OUTPUT_SIZE[1]}:flags=lanczos",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-movflags",
        "+faststart",
        str(output),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    rng = random.Random(os.urandom(16))
    palette = make_palette(rng)
    flocs = [
        Floc(
            radius=rng.uniform(0.06, 1.0),
            angle=rng.uniform(0, math.tau),
            depth=rng.random(),
            size=rng.uniform(1.4, 5.8),
            drift=rng.uniform(-0.035, 0.06),
            phase=rng.uniform(0, math.tau),
            density=rng.uniform(0.025, 0.075),
        )
        for _ in range(950)
    ]

    render_frame(0, flocs, palette).save(ROOT / f"{WORK_NAME}_p1.png")
    with tempfile.TemporaryDirectory(prefix=f"{WORK_NAME}_") as tmp:
        frames_dir = Path(tmp)
        for frame in range(FRAMES):
            render_frame(frame, flocs, palette).save(frames_dir / f"frame_{frame:04d}.png")
            if frame % 60 == 0:
                print(f"rendered {frame}/{FRAMES}")
        encode_video(frames_dir, ROOT / f"{WORK_NAME}.mp4")
    print(f"saved {ROOT / f'{WORK_NAME}.mp4'}")


if __name__ == "__main__":
    main()
