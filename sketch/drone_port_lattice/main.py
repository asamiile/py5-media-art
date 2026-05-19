from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import shutil
import subprocess
import sys

import numpy as np
import py5

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
BG = (7, 10, 15)
ROOF = (18, 24, 29)
GRID = (42, 54, 60)
TEAL = (52, 223, 210)
AMBER = (244, 176, 67)
WHITE = (224, 235, 232)
RED = (248, 76, 84)


@dataclass
class Pad:
    x: float
    y: float
    radius: float
    phase: float
    tier: int


@dataclass
class Drone:
    route: list[int]
    phase: float
    speed: float
    scale: float
    accent: tuple[int, int, int]


def smoothstep(v: float) -> float:
    v = max(0.0, min(1.0, v))
    return v * v * (3.0 - 2.0 * v)


def lerp(a: float, b: float, p: float) -> float:
    return a + (b - a) * p


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)

    global pads, drones, stars
    rng = np.random.default_rng()
    pads = []
    rows = [0.28, 0.42, 0.58, 0.73]
    cols = [0.18, 0.34, 0.50, 0.66, 0.82]
    for row_i, ry in enumerate(rows):
        for col_i, cx in enumerate(cols):
            if (row_i + col_i) % 5 == 1:
                continue
            pads.append(
                Pad(
                    x=W * cx + rng.uniform(-22, 22),
                    y=H * ry + rng.uniform(-16, 16),
                    radius=float(rng.uniform(34, 52)),
                    phase=float(rng.uniform(0, math.tau)),
                    tier=int((row_i + col_i) % 3),
                )
            )

    drones = []
    accents = [TEAL, AMBER, WHITE, RED]
    for i in range(18):
        route = list(rng.choice(len(pads), size=5, replace=False))
        drones.append(
            Drone(
                route=route,
                phase=float(rng.uniform(0, 1)),
                speed=float(rng.uniform(0.025, 0.052)),
                scale=float(rng.uniform(0.75, 1.25)),
                accent=accents[int(rng.integers(0, len(accents)))],
            )
        )
    stars = rng.uniform(0, 1, (120, 3))


def drone_position(drone: Drone, t: float) -> tuple[float, float, float, float]:
    route_t = (t * drone.speed + drone.phase) % 1.0
    scaled = route_t * len(drone.route)
    idx = int(scaled) % len(drone.route)
    p = smoothstep(scaled - idx)
    a = pads[drone.route[idx]]
    b = pads[drone.route[(idx + 1) % len(drone.route)]]
    x = lerp(a.x, b.x, p)
    y = lerp(a.y, b.y, p)
    arc = math.sin(p * math.pi) * (72 + 24 * drone.scale)
    y -= arc
    angle = math.atan2(b.y - a.y, b.x - a.x)
    return x, y, angle, arc


def draw_sky(t: float) -> None:
    py5.background(*BG)
    py5.no_stroke()
    for sx, sy, sp in stars:
        blink = 0.4 + 0.6 * math.sin(t * (0.5 + sp) + sx * 12) ** 2
        py5.fill(*WHITE, 12 + 40 * blink)
        py5.circle(sx * W, sy * H * 0.52, 1.0 + sp * 2.4)
    for i in range(9):
        py5.fill(12 + i * 2, 17 + i * 2, 24 + i * 2, 50)
        x = W * (0.04 + i * 0.12)
        h = H * (0.15 + 0.11 * ((i * 3) % 5) / 4)
        py5.rect(x, H * 0.91 - h * 0.5, W * 0.08, h, 2)


def draw_rooftop(t: float) -> None:
    py5.no_stroke()
    py5.fill(*ROOF, 235)
    py5.quad(W * 0.08, H * 0.23, W * 0.92, H * 0.20, W * 0.97, H * 0.86, W * 0.03, H * 0.88)
    py5.stroke(*GRID, 70)
    py5.stroke_weight(1)
    for i in range(15):
        x = W * (0.07 + i * 0.062)
        py5.line(x, H * 0.24, x - W * 0.04, H * 0.87)
    for i in range(10):
        y = H * (0.28 + i * 0.058)
        py5.line(W * 0.06, y, W * 0.94, y - 20)


def draw_routes(t: float) -> None:
    for drone in drones:
        for a_idx, b_idx in zip(drone.route, drone.route[1:] + [drone.route[0]]):
            a = pads[a_idx]
            b = pads[b_idx]
            py5.no_fill()
            py5.stroke(drone.accent[0], drone.accent[1], drone.accent[2], 12)
            py5.stroke_weight(1)
            mx = (a.x + b.x) * 0.5
            my = (a.y + b.y) * 0.5 - 80
            py5.bezier(a.x, a.y, mx, my, mx, my, b.x, b.y)


def draw_pads(t: float) -> None:
    py5.text_size(13)
    for i, pad in enumerate(pads):
        pulse = 0.5 + 0.5 * math.sin(t * 1.7 + pad.phase)
        rgb = (TEAL, AMBER, WHITE)[pad.tier]
        py5.no_fill()
        for grow, alpha in ((24, 18), (10, 45), (0, 130)):
            py5.stroke(rgb[0], rgb[1], rgb[2], alpha + 32 * pulse)
            py5.stroke_weight(1.5)
            py5.circle(pad.x, pad.y, pad.radius * 2 + grow)
        py5.stroke(*GRID, 150)
        py5.line(pad.x - pad.radius * 0.55, pad.y, pad.x + pad.radius * 0.55, pad.y)
        py5.line(pad.x, pad.y - pad.radius * 0.55, pad.x, pad.y + pad.radius * 0.55)
        py5.no_stroke()
        py5.fill(*rgb, 84 + 70 * pulse)
        py5.text(f"{i:02d}", pad.x, pad.y)


def draw_drone(drone: Drone, t: float) -> None:
    x, y, angle, arc = drone_position(drone, t)
    s = 22 * drone.scale
    py5.push_matrix()
    py5.translate(x, y)
    py5.rotate(angle)
    py5.no_stroke()
    py5.fill(drone.accent[0], drone.accent[1], drone.accent[2], 28)
    py5.circle(0, 0, s * 3.4)
    py5.fill(20, 28, 32, 235)
    py5.stroke(*WHITE, 145)
    py5.stroke_weight(1.1)
    py5.triangle(s * 1.05, 0, -s * 0.72, -s * 0.55, -s * 0.72, s * 0.55)
    py5.no_stroke()
    py5.fill(drone.accent[0], drone.accent[1], drone.accent[2], 210)
    py5.circle(s * 1.0, 0, 5)
    py5.fill(*RED, 190)
    py5.circle(-s * 0.74, -s * 0.48, 4)
    py5.fill(*TEAL, 190)
    py5.circle(-s * 0.74, s * 0.48, 4)
    py5.pop_matrix()

    py5.stroke(drone.accent[0], drone.accent[1], drone.accent[2], 28 + min(60, arc))
    py5.stroke_weight(1)
    py5.line(x, y + 10, x, y + 10 + arc * 0.65)


def draw_hud(t: float) -> None:
    py5.no_stroke()
    py5.fill(*TEAL, 110)
    py5.text_size(14)
    py5.text("DRONE PORT LATTICE / ROOFTOP AUTONOMY MAP", W * 0.5, H * 0.075)
    for i in range(8):
        x = W * (0.31 + i * 0.055)
        h = 8 + 24 * (0.5 + 0.5 * math.sin(t * 1.4 + i))
        py5.fill(*AMBER if i % 3 == 0 else TEAL, 100)
        py5.rect(x, H * 0.105, 34, h, 2)


def compile_video() -> None:
    subprocess.run(
        [
            "ffmpeg",
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
            "20",
            str(SKETCH_DIR / "output.mp4"),
        ],
        check=True,
    )
    shutil.copy2(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)
    shutil.rmtree(FRAMES_DIR)


def draw() -> None:
    t = py5.frame_count / FPS
    draw_sky(t)
    draw_rooftop(t)
    draw_routes(t)
    draw_pads(t)
    for drone in drones:
        draw_drone(drone, t)
    draw_hud(t)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        pct = py5.frame_count / TOTAL_FRAMES * 100
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({pct:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into output.mp4...")
        compile_video()
        print("[Render Cleanup] Temporary frames directory successfully removed.")


py5.run_sketch()
