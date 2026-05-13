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
PREVIEW_FRAME = TOTAL_FRAMES // 2
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

GRID_W, GRID_H = 768, 432
rng = np.random.default_rng()

field = np.zeros((GRID_H, GRID_W), dtype=np.float32)
memory = np.zeros_like(field)
pinning = np.zeros_like(field)
base_tint = np.zeros((GRID_H, GRID_W, 3), dtype=np.float32)
yy, xx = np.indices((GRID_H, GRID_W), dtype=np.float32)
nx = xx / GRID_W
ny = yy / GRID_H


def build_domains() -> None:
    global field, memory, pinning, base_tint
    centers = rng.uniform([0.0, 0.0], [1.0, 1.0], (22, 2)).astype(np.float32)
    variants = rng.choice([-1.0, -0.35, 0.38, 1.0], len(centers)).astype(np.float32)
    score = np.full((GRID_H, GRID_W), 1e9, dtype=np.float32)
    field = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    for center, variant in zip(centers, variants):
        d2 = (nx - center[0]) ** 2 + (ny - center[1]) ** 2
        d2 += 0.018 * np.sin(nx * 19.0 + center[0] * 8.0) * np.sin(ny * 13.0 + center[1] * 7.0)
        mask = d2 < score
        field[mask] = variant
        score[mask] = d2[mask]

    field += 0.16 * np.sin(nx * 34.0 + ny * 5.0) + 0.12 * np.sin(ny * 27.0)
    for _ in range(18):
        field[:] = (
            field * 0.76
            + 0.06 * (np.roll(field, 1, 0) + np.roll(field, -1, 0))
            + 0.06 * (np.roll(field, 1, 1) + np.roll(field, -1, 1))
        )
    field[:] = np.tanh(field * 1.7)
    memory[:] = np.abs(field) * 0.18

    scratches = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    pinning = (
        0.10 * np.sin(nx * np.pi * 15.0 + 0.5 * np.sin(ny * 8.0))
        + 0.08 * np.sin((nx + ny) * np.pi * 21.0)
        + 0.035 * scratches
    ).astype(np.float32)

    graphite = np.array([12.0, 15.0, 18.0], dtype=np.float32)
    blue_gray = np.array([34.0, 43.0, 49.0], dtype=np.float32)
    base_tint = graphite[None, None, :] + blue_gray[None, None, :] * (0.42 + 0.18 * ny[..., None])


def step_field(frame: int) -> None:
    global field, memory
    t = frame / TOTAL_FRAMES
    lap = (
        np.roll(field, 1, 0)
        + np.roll(field, -1, 0)
        + np.roll(field, 1, 1)
        + np.roll(field, -1, 1)
        - 4.0 * field
    )
    slow_bias = (
        0.34 * np.sin(nx * 9.5 + t * np.pi * 2.0)
        + 0.27 * np.cos(ny * 8.0 - t * np.pi * 2.6)
        + 0.18 * np.sin((nx - ny) * 11.0 + t * np.pi * 1.4)
    )
    free_energy = field - field ** 3
    field += 0.055 * lap + 0.030 * free_energy + 0.010 * slow_bias + 0.006 * pinning
    field[:] = np.clip(field, -1.35, 1.35)
    gy, gx = np.gradient(field)
    wall = np.clip(np.sqrt(gx * gx + gy * gy) * 6.0, 0.0, 1.0)
    memory[:] = np.maximum(memory * 0.982, wall)


def render_rgb(frame: int) -> np.ndarray:
    analyzer = frame * np.pi * 2.0 / TOTAL_FRAMES
    orientation = field * 1.22 + 0.23 * np.sin(nx * 17.0 - analyzer * 0.7)
    crossed = np.sin(2.0 * orientation + analyzer) ** 2
    crossed = np.clip(crossed, 0.0, 1.0)
    variant_a = np.clip(field, 0.0, 1.0)
    variant_b = np.clip(-field, 0.0, 1.0)
    wall = np.clip(memory, 0.0, 1.0)

    teal = np.array([24.0, 168.0, 153.0], dtype=np.float32)
    violet = np.array([138.0, 82.0, 170.0], dtype=np.float32)
    amber = np.array([232.0, 174.0, 82.0], dtype=np.float32)
    pearl = np.array([210.0, 223.0, 214.0], dtype=np.float32)

    rgb = base_tint.copy()
    rgb += teal[None, None, :] * crossed[..., None] * variant_a[..., None] * 0.56
    rgb += violet[None, None, :] * crossed[..., None] * variant_b[..., None] * 0.52
    rgb += pearl[None, None, :] * (crossed ** 2)[..., None] * 0.16
    rgb += amber[None, None, :] * (wall ** 1.7)[..., None] * 0.92
    rgb -= np.array([12.0, 8.0, 3.0], dtype=np.float32)[None, None, :] * (1.0 - crossed[..., None]) * 0.35
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
    build_domains()


def draw():
    for _ in range(2):
        step_field(py5.frame_count)
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
