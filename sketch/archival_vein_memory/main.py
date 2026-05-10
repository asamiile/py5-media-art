from pathlib import Path
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
PREVIEW_FRAME = TOTAL_FRAMES // 2
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

GRID_W, GRID_H = 960, 540
NUM_PARTICLES = 65000
SPAWN_PER_FRAME = 720

rng = np.random.default_rng()

pos = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
age = np.zeros(NUM_PARTICLES, dtype=np.float32)
life = np.zeros(NUM_PARTICLES, dtype=np.float32)
phase = np.zeros(NUM_PARTICLES, dtype=np.float32)
source_id = np.zeros(NUM_PARTICLES, dtype=np.int32)

ink = np.zeros((GRID_H, GRID_W), dtype=np.float32)
oxide = np.zeros_like(ink)
base_rgb = np.zeros((GRID_H, GRID_W, 3), dtype=np.float32)
fiber_x = np.zeros((GRID_H, GRID_W), dtype=np.float32)
fiber_y = np.zeros_like(fiber_x)
crease = np.zeros_like(ink)
sources = np.zeros((11, 2), dtype=np.float32)
next_particle = 0


def build_paper() -> None:
    global base_rgb, fiber_x, fiber_y, crease, sources
    yy, xx = np.indices((GRID_H, GRID_W), dtype=np.float32)
    nx = xx / GRID_W
    ny = yy / GRID_H

    grain = (
        0.030 * np.sin(xx * 0.23 + np.sin(yy * 0.031) * 2.5)
        + 0.018 * np.sin((xx + yy) * 0.071)
        + 0.012 * rng.standard_normal((GRID_H, GRID_W))
    )
    vignette = ((nx - 0.52) ** 2 * 0.42 + (ny - 0.48) ** 2 * 0.72)
    warmth = np.clip(1.0 + grain - vignette, 0.78, 1.05)
    parchment = np.array([228.0, 212.0, 177.0], dtype=np.float32)
    under = np.array([80.0, 96.0, 78.0], dtype=np.float32)
    base_rgb = parchment[None, None, :] * warmth[..., None]
    base_rgb += under[None, None, :] * (0.05 + 0.03 * np.sin(ny * np.pi))[..., None]

    angle = (
        -0.18
        + 0.33 * np.sin(ny * np.pi * 2.1)
        + 0.18 * np.sin(nx * np.pi * 3.7 + 0.4)
    )
    fiber_x = np.cos(angle).astype(np.float32)
    fiber_y = np.sin(angle).astype(np.float32)

    crease = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    for cx, tilt, width, strength in [
        (0.23, -0.16, 0.010, 0.90),
        (0.51, 0.09, 0.014, 0.65),
        (0.78, 0.20, 0.012, 0.75),
    ]:
        line = nx - cx - tilt * (ny - 0.5)
        crease += strength * np.exp(-(line * line) / (2.0 * width * width))
    crease[:] = np.clip(crease, 0.0, 1.0)

    sources = np.array(
        [
            [GRID_W * 0.10, GRID_H * 0.28],
            [GRID_W * 0.13, GRID_H * 0.74],
            [GRID_W * 0.30, GRID_H * 0.48],
            [GRID_W * 0.44, GRID_H * 0.22],
            [GRID_W * 0.54, GRID_H * 0.66],
            [GRID_W * 0.70, GRID_H * 0.37],
            [GRID_W * 0.85, GRID_H * 0.20],
            [GRID_W * 0.90, GRID_H * 0.70],
            [GRID_W * 0.60, GRID_H * 0.87],
            [GRID_W * 0.35, GRID_H * 0.84],
            [GRID_W * 0.20, GRID_H * 0.12],
        ],
        dtype=np.float32,
    )


def respawn(indices: np.ndarray, frame: int) -> None:
    count = len(indices)
    if count == 0:
        return
    sid = rng.integers(0, len(sources), count)
    jitter = rng.normal(0.0, [8.5, 4.5], (count, 2)).astype(np.float32)
    drift = np.column_stack(
        [
            np.sin(frame * 0.013 + sid * 1.7) * 16.0,
            np.cos(frame * 0.009 + sid * 1.1) * 8.0,
        ]
    ).astype(np.float32)
    pos[indices] = sources[sid] + jitter + drift
    pos[indices, 0] = np.clip(pos[indices, 0], 2, GRID_W - 3)
    pos[indices, 1] = np.clip(pos[indices, 1], 2, GRID_H - 3)
    age[indices] = 0.0
    life[indices] = rng.uniform(115.0, 260.0, count)
    phase[indices] = rng.uniform(0.0, np.pi * 2.0, count)
    source_id[indices] = sid


def seed_initial_particles() -> None:
    age[:] = life + 1.0
    respawn(np.arange(9000), 0)
    age[:9000] = rng.uniform(0.0, life[:9000] * 0.65)


def step_particles(frame: int) -> None:
    global next_particle, ink, oxide
    spawn = np.arange(next_particle, next_particle + SPAWN_PER_FRAME) % NUM_PARTICLES
    next_particle = (next_particle + SPAWN_PER_FRAME) % NUM_PARTICLES
    respawn(spawn, frame)

    alive = age < life
    ids = np.flatnonzero(alive)
    if ids.size == 0:
        return

    p = pos[ids]
    ix = np.clip(p[:, 0].astype(np.int32), 0, GRID_W - 1)
    iy = np.clip(p[:, 1].astype(np.int32), 0, GRID_H - 1)
    fx = fiber_x[iy, ix]
    fy = fiber_y[iy, ix]
    cre = crease[iy, ix]
    px = p[:, 0] / GRID_W
    py = p[:, 1] / GRID_H
    sid = source_id[ids].astype(np.float32)

    curl = np.sin(px * 18.0 + py * 9.0 + frame * 0.026 + phase[ids])
    cross = np.cos(px * 7.0 - py * 21.0 + sid)
    ridge_pull = (cre - 0.35) * 0.62
    speed = 0.58 + 1.55 * (1.0 - age[ids] / life[ids])
    wander = rng.normal(0.0, 0.24, (ids.size, 2)).astype(np.float32)

    pos[ids, 0] += (fx * speed + (-fy) * curl * 0.46 + ridge_pull * 0.24 + wander[:, 0])
    pos[ids, 1] += (fy * speed + fx * cross * 0.34 + wander[:, 1])
    pos[ids, 0] = np.clip(pos[ids, 0], 0, GRID_W - 1)
    pos[ids, 1] = np.clip(pos[ids, 1], 0, GRID_H - 1)

    ix = pos[ids, 0].astype(np.int32)
    iy = pos[ids, 1].astype(np.int32)
    pulse = 0.55 + 0.45 * np.sin(frame * 0.018 + phase[ids])
    deposit = (0.040 + 0.16 * cre) * pulse * (1.0 - age[ids] / life[ids] * 0.60)
    np.add.at(ink, (iy, ix), deposit.astype(np.float32))
    np.add.at(oxide, (iy, ix), (deposit * (0.35 + 0.75 * cre)).astype(np.float32))

    age[ids] += 1.0
    dead = ids[(age[ids] >= life[ids]) | (pos[ids, 0] < 1) | (pos[ids, 0] > GRID_W - 2)]
    respawn(dead, frame)


def diffuse_fields() -> None:
    global ink, oxide
    ink *= 0.9965
    oxide *= 0.9975
    ink += 0.006 * (
        np.roll(ink, 1, 0) + np.roll(ink, -1, 0)
        + np.roll(ink, 1, 1) + np.roll(ink, -1, 1) - 4.0 * ink
    )
    oxide += 0.004 * (
        np.roll(oxide, 1, 0) + np.roll(oxide, -1, 0)
        + np.roll(oxide, 1, 1) + np.roll(oxide, -1, 1) - 4.0 * oxide
    )
    np.maximum(ink, 0.0, out=ink)
    np.maximum(oxide, 0.0, out=oxide)


def render_rgb(frame: int) -> np.ndarray:
    d = np.log1p(ink * 1.9)
    o = np.log1p(oxide * 1.4)
    d = np.clip(d / max(0.08, np.percentile(d, 99.4)), 0.0, 1.0)
    o = np.clip(o / max(0.08, np.percentile(o, 99.2)), 0.0, 1.0)
    d = d ** 0.72
    o = o ** 0.62

    gy, gx = np.gradient(d)
    edge = np.clip(np.sqrt(gx * gx + gy * gy) * 8.5, 0.0, 1.0)
    breathing = 0.88 + 0.12 * np.sin(frame * np.pi * 2.0 / TOTAL_FRAMES)

    sepia_ink = np.array([38.0, 37.0, 30.0], dtype=np.float32)
    verdigris = np.array([33.0, 92.0, 78.0], dtype=np.float32)
    copper = np.array([178.0, 118.0, 70.0], dtype=np.float32)
    shadow = np.array([25.0, 34.0, 32.0], dtype=np.float32)

    rgb = base_rgb.copy()
    rgb = rgb * (1.0 - d[..., None] * 0.78) + sepia_ink[None, None, :] * d[..., None] * 0.78
    rgb = rgb * (1.0 - o[..., None] * 0.42) + verdigris[None, None, :] * o[..., None] * 0.42
    rgb += copper[None, None, :] * edge[..., None] * 0.34 * breathing
    rgb -= shadow[None, None, :] * crease[..., None] * 0.13
    rgb += np.array([20.0, 28.0, 22.0], dtype=np.float32)[None, None, :] * crease[..., None] * o[..., None] * 0.40
    return np.clip(rgb, 0.0, 255.0).astype(np.uint8)


def upscale(rgb_small: np.ndarray, out_h: int, out_w: int) -> np.ndarray:
    sy = max(1, out_h // GRID_H)
    sx = max(1, out_w // GRID_W)
    big = np.repeat(np.repeat(rgb_small, sy, axis=0), sx, axis=1)
    if big.shape[0] < out_h or big.shape[1] < out_w:
        big = np.pad(
            big,
            ((0, max(0, out_h - big.shape[0])), (0, max(0, out_w - big.shape[1])), (0, 0)),
            mode="edge",
        )
    return big[:out_h, :out_w]


def encode_video() -> None:
    mp4_path = SKETCH_DIR / f"{WORK_NAME}.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", str(mp4_path),
        ],
        check=True,
    )
    shutil.copyfile(FRAMES_DIR / f"frame-{PREVIEW_FRAME:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)


def setup():
    py5.size(*SIZE, py5.P2D)
    FRAMES_DIR.mkdir(exist_ok=True)
    build_paper()
    seed_initial_particles()
    py5.background(230, 215, 180)


def draw():
    step_particles(py5.frame_count)
    diffuse_fields()
    rgb_small = render_rgb(py5.frame_count)

    py5.load_np_pixels()
    ph, pw = py5.np_pixels.shape[:2]
    big = upscale(rgb_small, ph, pw)
    py5.np_pixels[..., 0] = 255
    py5.np_pixels[..., 1] = big[..., 0]
    py5.np_pixels[..., 2] = big[..., 1]
    py5.np_pixels[..., 3] = big[..., 2]
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        encode_video()


if __name__ == "__main__":
    py5.run_sketch()
