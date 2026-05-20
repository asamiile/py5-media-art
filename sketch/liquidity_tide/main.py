from __future__ import annotations

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
LEVELS = 45
HISTORY = 170

BG = (6, 9, 12)
PANEL = (14, 19, 23)
GRID = (44, 54, 59)
BID = (42, 218, 198)
ASK = (238, 83, 105)
AMBER = (244, 179, 73)
SILVER = (215, 224, 221)


def setup() -> None:
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.rect_mode(py5.CENTER)
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)

    global rng, bid_depth, ask_depth, mid_price, spread, heat_bid, heat_ask, trades
    rng = np.random.default_rng()
    distance = np.arange(LEVELS, dtype=np.float32)
    bid_depth = 0.9 * np.exp(-distance / 13.0) + rng.uniform(0.0, 0.12, LEVELS)
    ask_depth = 0.85 * np.exp(-distance / 12.0) + rng.uniform(0.0, 0.12, LEVELS)
    mid_price = 0.0
    spread = 2.0
    heat_bid = np.zeros((HISTORY, LEVELS), dtype=np.float32)
    heat_ask = np.zeros((HISTORY, LEVELS), dtype=np.float32)
    trades = []


def update_book(t: float) -> None:
    global bid_depth, ask_depth, mid_price, spread, heat_bid, heat_ask, trades
    imbalance = (np.sum(bid_depth[:12]) - np.sum(ask_depth[:12])) / (np.sum(bid_depth[:12]) + np.sum(ask_depth[:12]) + 1e-5)
    mid_price = 0.992 * mid_price + 0.055 * imbalance + rng.normal(0.0, 0.012)
    spread = 1.65 + 0.55 * math.sin(t * 1.35) + 0.55 * abs(imbalance)

    base = np.exp(-np.arange(LEVELS, dtype=np.float32) / 12.5)
    bid_depth *= rng.uniform(0.965, 1.012, LEVELS)
    ask_depth *= rng.uniform(0.965, 1.012, LEVELS)
    bid_depth += base * rng.uniform(0.0, 0.05, LEVELS)
    ask_depth += base * rng.uniform(0.0, 0.05, LEVELS)

    if rng.random() < 0.62:
        side = 1 if rng.random() < 0.5 + imbalance * 0.28 else -1
        level = int(rng.integers(0, 10))
        volume = float(rng.uniform(0.16, 0.42))
        if side > 0:
            ask_depth[level] *= 1.0 - volume
        else:
            bid_depth[level] *= 1.0 - volume
        trades.append([side, level, 1.0, volume])

    if rng.random() < 0.36:
        level = int(rng.integers(4, LEVELS))
        if rng.random() < 0.5:
            bid_depth[level] += rng.uniform(0.18, 0.52) * base[level]
        else:
            ask_depth[level] += rng.uniform(0.18, 0.52) * base[level]

    bid_depth = np.clip(bid_depth, 0.02, 1.35)
    ask_depth = np.clip(ask_depth, 0.02, 1.35)
    heat_bid = np.roll(heat_bid, -1, axis=0)
    heat_ask = np.roll(heat_ask, -1, axis=0)
    heat_bid[-1] = bid_depth
    heat_ask[-1] = ask_depth

    for tr in trades:
        tr[2] -= 0.028
    trades = [tr for tr in trades if tr[2] > 0]


def draw_shell(t: float) -> None:
    py5.background(*BG)
    py5.no_stroke()
    py5.fill(*PANEL, 238)
    py5.rect(W * 0.5, H * 0.53, W * 0.84, H * 0.72, 6)
    py5.fill(20, 26, 30, 190)
    py5.rect(W * 0.5, H * 0.53, W * 0.76, H * 0.60, 4)
    py5.stroke(*GRID, 70)
    py5.stroke_weight(1)
    for y in np.linspace(H * 0.24, H * 0.82, 13):
        py5.line(W * 0.12, y, W * 0.88, y)
    for x in np.linspace(W * 0.14, W * 0.86, 15):
        py5.line(x, H * 0.22, x, H * 0.84)
    py5.no_stroke()
    py5.fill(*SILVER, 120)
    py5.text_size(13)
    py5.text("LIQUIDITY TIDE / LIVE DEPTH MEMORY", W * 0.5, H * 0.065)


def draw_heatmap() -> None:
    x0 = W * 0.18
    y0 = H * 0.24
    heat_w = W * 0.64
    heat_h = H * 0.50
    cell_w = heat_w / HISTORY
    cell_h = heat_h / (LEVELS * 2)
    center_y = y0 + heat_h * 0.5 + mid_price * 24

    py5.no_stroke()
    for h in range(0, HISTORY, 2):
        x = x0 + h * cell_w
        age = h / HISTORY
        for level in range(LEVELS):
            alpha_bid = int(90 * heat_bid[h, level] * (0.35 + age * 0.9))
            alpha_ask = int(90 * heat_ask[h, level] * (0.35 + age * 0.9))
            y_bid = center_y + (level + spread) * cell_h
            y_ask = center_y - (level + spread) * cell_h
            py5.fill(BID[0], BID[1], BID[2], alpha_bid)
            py5.rect(x, y_bid, cell_w * 1.8, cell_h * 1.3)
            py5.fill(ASK[0], ASK[1], ASK[2], alpha_ask)
            py5.rect(x, y_ask, cell_w * 1.8, cell_h * 1.3)

    py5.stroke(*SILVER, 120)
    py5.stroke_weight(1.5)
    py5.line(x0, center_y, x0 + heat_w, center_y)
    py5.no_fill()
    py5.stroke(*AMBER, 90)
    py5.rect(x0 + heat_w * 0.5, center_y, heat_w, spread * cell_h * 2.5, 4)


def draw_current_book(t: float) -> None:
    base_x = W * 0.5
    center_y = H * 0.53 + mid_price * 24
    max_w = W * 0.24
    step_y = 8.2
    py5.no_stroke()
    for level in range(30):
        y_bid = center_y + (level + spread) * step_y
        y_ask = center_y - (level + spread) * step_y
        wb = max_w * bid_depth[level]
        wa = max_w * ask_depth[level]
        py5.fill(BID[0], BID[1], BID[2], 30 + 105 * bid_depth[level])
        py5.rect(base_x - wb * 0.5 - 8, y_bid, wb, 4.2, 2)
        py5.fill(ASK[0], ASK[1], ASK[2], 30 + 105 * ask_depth[level])
        py5.rect(base_x + wa * 0.5 + 8, y_ask, wa, 4.2, 2)

    for side, level, life, volume in trades:
        rgb = ASK if side > 0 else BID
        y = center_y + (-side) * (level + spread) * step_y
        radius = 14 + 45 * volume * life
        py5.no_fill()
        py5.stroke(rgb[0], rgb[1], rgb[2], int(170 * life))
        py5.stroke_weight(2)
        py5.circle(base_x, y, radius)


def draw_imbalance_meter(t: float) -> None:
    bid_sum = float(np.sum(bid_depth[:14]))
    ask_sum = float(np.sum(ask_depth[:14]))
    imbalance = (bid_sum - ask_sum) / (bid_sum + ask_sum + 1e-5)
    x = W * 0.80
    y = H * 0.15
    py5.no_fill()
    py5.stroke(*GRID, 130)
    py5.stroke_weight(1.3)
    py5.circle(x, y, 82)
    angle = -math.pi / 2 + imbalance * math.pi * 0.78
    px = x + math.cos(angle) * 34
    py = y + math.sin(angle) * 34
    py5.stroke(*BID if imbalance > 0 else ASK, 190)
    py5.stroke_weight(2.5)
    py5.line(x, y, px, py)
    py5.no_stroke()
    py5.fill(*SILVER, 125)
    py5.text_size(11)
    py5.text(f"{imbalance:+.2f}", x, y + 52)


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
    update_book(t)
    draw_shell(t)
    draw_heatmap()
    draw_current_book(t)
    draw_imbalance_meter(t)
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
