from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import shutil
import subprocess
import sys

import py5
import numpy as np

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
LANES = 7
LANE_SPACING = H * 0.095
LANE_TOP = H * 0.23
NODE_XS = [W * p for p in (0.18, 0.34, 0.50, 0.66, 0.82)]

BG = (10, 13, 17)
GRID = (34, 44, 52)
STEEL = (82, 96, 104)
CYAN = (37, 225, 219)
AMBER = (246, 178, 67)
SILVER = (218, 226, 225)
RED = (255, 94, 90)


@dataclass
class Parcel:
    lane: int
    target_lane: int
    offset: float
    speed: float
    width: float
    height: float
    hue_pick: int
    gate_index: int
    phase: float


def ease_in_out(v: float) -> float:
    v = max(0.0, min(1.0, v))
    return v * v * (3.0 - 2.0 * v)


def lane_y(lane: int) -> float:
    return LANE_TOP + lane * LANE_SPACING


def parcel_position(parcel: Parcel, clock: float) -> tuple[float, float, float]:
    span = W + 520
    x = (parcel.offset + clock * parcel.speed) % span - 260
    y = lane_y(parcel.lane)
    gate_x = NODE_XS[parcel.gate_index]
    bend = 82
    if gate_x - bend < x < gate_x + bend:
        p = ease_in_out((x - (gate_x - bend)) / (bend * 2))
        y = lane_y(parcel.lane) * (1.0 - p) + lane_y(parcel.target_lane) * p
    elif x >= gate_x + bend:
        y = lane_y(parcel.target_lane)
    pulse = 0.5 + 0.5 * math.sin(clock * 0.09 + parcel.phase)
    return x, y, pulse


def draw_glow_line(x1: float, y1: float, x2: float, y2: float, rgb: tuple[int, int, int], alpha: float, weight: float) -> None:
    for scale, a in ((5.2, 20), (2.6, 42), (1.0, alpha)):
        py5.stroke(*rgb, a)
        py5.stroke_weight(weight * scale)
        py5.line(x1, y1, x2, y2)


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text_size(12)
    FRAMES_DIR.mkdir(exist_ok=True)

    global parcels, spark_offsets, scanner_phase
    rng = np.random.default_rng()
    parcels = []
    for i in range(54):
        lane = int(rng.integers(0, LANES))
        delta = int(rng.choice([-2, -1, 1, 2]))
        target = max(0, min(LANES - 1, lane + delta))
        parcels.append(
            Parcel(
                lane=lane,
                target_lane=target,
                offset=float(rng.uniform(0, W + 520)),
                speed=float(rng.uniform(120, 245)),
                width=float(rng.uniform(42, 76)),
                height=float(rng.uniform(24, 40)),
                hue_pick=int(rng.integers(0, 3)),
                gate_index=int(rng.integers(0, len(NODE_XS))),
                phase=float(rng.uniform(0, math.tau)),
            )
        )
    spark_offsets = rng.uniform(0, 1, (140, 3))
    scanner_phase = rng.uniform(0, math.tau, len(NODE_XS))


def draw_floor(t: float) -> None:
    py5.background(*BG)
    py5.stroke(*GRID, 54)
    py5.stroke_weight(1)
    for x in np.linspace(-160, W + 160, 23):
        py5.line(x + 30 * math.sin(t * 0.25), H * 0.13, x - 190, H * 0.94)
    for y in np.linspace(H * 0.16, H * 0.92, 13):
        py5.line(0, y, W, y + 18 * math.sin(t * 0.2 + y * 0.01))

    py5.no_stroke()
    for lane in range(LANES):
        y = lane_y(lane)
        py5.fill(18, 25, 31, 230)
        py5.rect(W / 2, y, W * 0.88, 34, 4)
        py5.fill(48, 61, 68, 160)
        for x in np.arange(W * 0.07, W * 0.94, 58):
            py5.rect(x, y, 24, 3, 2)
        draw_glow_line(W * 0.055, y - 22, W * 0.95, y - 22, CYAN if lane % 2 else STEEL, 54, 1.2)


def draw_gates(t: float) -> None:
    for gi, x in enumerate(NODE_XS):
        scan = (math.sin(t * 1.8 + scanner_phase[gi]) + 1.0) * 0.5
        beam_y = lane_y(0) - 40 + scan * ((LANES - 1) * LANE_SPACING + 80)
        draw_glow_line(x, lane_y(0) - 54, x, lane_y(LANES - 1) + 54, CYAN, 78, 1.4)
        py5.stroke(*AMBER, 105)
        py5.stroke_weight(1.6)
        py5.line(x - 44, beam_y, x + 44, beam_y)
        py5.no_stroke()
        py5.fill(*AMBER, 170)
        py5.circle(x, beam_y, 5)

        for lane in range(LANES - 1):
            y = (lane_y(lane) + lane_y(lane + 1)) * 0.5
            angle = math.sin(t * 1.15 + gi * 0.7 + lane * 0.55) * 0.55
            py5.push_matrix()
            py5.translate(x, y)
            py5.rotate(angle)
            py5.fill(22, 30, 34, 245)
            py5.stroke(*SILVER, 120)
            py5.stroke_weight(1.2)
            py5.rect(0, 0, 58, 10, 3)
            py5.no_stroke()
            py5.fill(*CYAN, 150)
            py5.rect(24, 0, 8, 6, 2)
            py5.pop_matrix()


def draw_parcels(t: float) -> None:
    clock = t * FPS
    for parcel in parcels:
        x, y, pulse = parcel_position(parcel, clock)
        if not (-120 < x < W + 120):
            continue
        color = (CYAN, AMBER, SILVER)[parcel.hue_pick]
        py5.no_stroke()
        py5.fill(color[0], color[1], color[2], 18 + 34 * pulse)
        py5.rect(x, y, parcel.width + 30, parcel.height + 20, 8)
        py5.fill(31, 37, 39, 238)
        py5.stroke(*color, 125 + 70 * pulse)
        py5.stroke_weight(1.3)
        py5.rect(x, y, parcel.width, parcel.height, 5)
        py5.no_stroke()
        py5.fill(*color, 210)
        py5.rect(x - parcel.width * 0.22, y, parcel.width * 0.2, parcel.height * 0.55, 2)
        py5.fill(*SILVER, 190)
        for i in range(5):
            bx = x + parcel.width * (-0.02 + i * 0.07)
            py5.rect(bx, y, 1.6 + (i % 2) * 2.2, parcel.height * 0.52, 1)


def draw_sparks(t: float) -> None:
    py5.no_stroke()
    for sx, sy, sp in spark_offsets:
        x = (sx * W + t * (18 + sp * 62)) % W
        y = lane_y(0) - 70 + sy * ((LANES - 1) * LANE_SPACING + 140)
        blink = 0.35 + 0.65 * math.sin(t * (1.2 + sp) + sx * 9.0) ** 2
        rgb = CYAN if sp < 0.62 else AMBER
        py5.fill(rgb[0], rgb[1], rgb[2], 22 + 75 * blink)
        py5.circle(x, y, 1.6 + 2.5 * sp)


def draw_hud(t: float) -> None:
    py5.no_fill()
    py5.stroke(*SILVER, 50)
    py5.stroke_weight(1)
    py5.rect(W * 0.5, H * 0.105, W * 0.88, 64, 5)
    for i, x in enumerate(NODE_XS):
        activity = 0.5 + 0.5 * math.sin(t * 1.7 + i)
        py5.no_stroke()
        py5.fill(*CYAN, 90 + 90 * activity)
        py5.rect(x, H * 0.105, 54, 6 + activity * 26, 3)
        py5.fill(*AMBER, 90)
        py5.circle(x + 43, H * 0.105 - 20, 4 + activity * 3)
    py5.fill(*SILVER, 130)
    py5.text("SORTATION DAWN  /  LIVE ROUTING FIELD", W * 0.5, H * 0.057)


def compile_video() -> None:
    output_path = SKETCH_DIR / "output.mp4"
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
            str(output_path),
        ],
        check=True,
    )
    shutil.copy2(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)
    shutil.rmtree(FRAMES_DIR)


def draw() -> None:
    t = py5.frame_count / FPS
    draw_floor(t)
    draw_sparks(t)
    draw_gates(t)
    draw_parcels(t)
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
