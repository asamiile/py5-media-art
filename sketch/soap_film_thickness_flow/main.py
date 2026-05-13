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

yy, xx = np.indices((GRID_H, GRID_W), dtype=np.float32)
nx = xx / GRID_W
ny = yy / GRID_H

base_rgb = np.zeros((GRID_H, GRID_W, 3), dtype=np.float32)
grain = np.zeros((GRID_H, GRID_W), dtype=np.float32)
phase_noise = np.zeros((GRID_H, GRID_W), dtype=np.float32)
dry_memory = np.zeros((GRID_H, GRID_W), dtype=np.float32)


def smooth(field: np.ndarray, passes: int) -> np.ndarray:
    for _ in range(passes):
        field = (
            field
            + np.roll(field, 1, 0)
            + np.roll(field, -1, 0)
            + np.roll(field, 1, 1)
            + np.roll(field, -1, 1)
        ) / 5.0
    return field


def build_base() -> None:
    global base_rgb, grain, phase_noise
    graphite = np.array([8.0, 10.0, 13.0], dtype=np.float32)
    blue = np.array([20.0, 35.0, 48.0], dtype=np.float32)
    violet = np.array([34.0, 23.0, 42.0], dtype=np.float32)

    grain = smooth(rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32), 3)
    broad = 0.5 + 0.5 * np.sin(nx * 6.0 + np.sin(ny * 8.0))
    vignette = (nx - 0.50) ** 2 * 0.85 + (ny - 0.48) ** 2 * 1.05
    base_rgb = graphite[None, None, :] + blue[None, None, :] * (0.20 + 0.15 * broad[..., None])
    base_rgb += violet[None, None, :] * (0.18 + 0.10 * np.sin((nx + ny) * 5.0))[..., None]
    base_rgb -= vignette[..., None] * np.array([9.0, 12.0, 14.0], dtype=np.float32)
    base_rgb += grain[..., None] * np.array([1.3, 1.1, 1.6], dtype=np.float32)

    phase_noise = smooth(rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32), 8)


def bubble_edges(theta: float) -> np.ndarray:
    centers = [
        (0.22 + 0.03 * np.sin(theta * 0.7), 0.34 + 0.02 * np.cos(theta * 1.1), 0.24),
        (0.58 + 0.04 * np.cos(theta * 0.6), 0.58 + 0.03 * np.sin(theta * 0.9), 0.34),
        (0.83 + 0.02 * np.sin(theta * 1.2), 0.28 + 0.03 * np.cos(theta * 0.8), 0.20),
    ]
    edge = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    for cx, cy, radius in centers:
        dx = nx - cx
        dy = (ny - cy) * 1.45
        d = np.sqrt(dx * dx + dy * dy)
        edge += np.exp(-((d - radius) ** 2) / 0.00011)
        edge += np.exp(-((d - radius * 0.54) ** 2) / 0.00018) * 0.30
    return np.clip(edge, 0.0, 1.0)


def render_frame(frame: int) -> np.ndarray:
    global dry_memory
    t = frame / TOTAL_FRAMES
    theta = t * np.pi * 2.0

    drain = ny * 3.8 + 0.25 * np.sin(nx * 8.0 + theta)
    shear = (
        0.40 * np.sin(nx * 22.0 - ny * 5.0 + theta * 2.5)
        + 0.30 * np.sin(nx * 7.0 + ny * 19.0 - theta * 1.8)
        + 0.20 * np.sin((nx + ny) * 31.0 + phase_noise * 2.0 + theta * 1.1)
    )
    swirl_a = np.sqrt((nx - 0.36) ** 2 + ((ny - 0.50) * 1.7) ** 2) * 18.0 - theta * 3.4
    swirl_b = np.sqrt((nx - 0.70) ** 2 + ((ny - 0.40) * 1.5) ** 2) * 23.0 + theta * 2.6
    thickness = drain + shear + 0.25 * np.sin(swirl_a) + 0.18 * np.sin(swirl_b)

    edge = bubble_edges(theta)
    black_spots = np.exp(-((np.sin(thickness * 2.1 + theta) + 0.94) ** 2) / 0.010)
    black_spots *= np.clip(ny * 1.4 - 0.08, 0.0, 1.0)
    dry_memory = np.maximum(dry_memory * 0.985, black_spots * 0.62)

    r = 0.5 + 0.5 * np.cos(thickness * 8.8 + 0.2)
    g = 0.5 + 0.5 * np.cos(thickness * 8.8 - 2.0)
    b = 0.5 + 0.5 * np.cos(thickness * 8.8 + 2.2)
    spectrum = np.stack([r, g, b], axis=2).astype(np.float32)
    spectrum = spectrum ** 1.6

    film_strength = np.clip(0.34 + 0.52 * (1.0 - ny) + 0.30 * np.sin(thickness * 1.7), 0.0, 1.0)
    pearl = np.array([230.0, 228.0, 206.0], dtype=np.float32)
    cyan = np.array([60.0, 205.0, 218.0], dtype=np.float32)
    magenta = np.array([226.0, 82.0, 174.0], dtype=np.float32)
    amber = np.array([226.0, 151.0, 56.0], dtype=np.float32)

    rgb = base_rgb.copy()
    rgb += spectrum * film_strength[..., None] * np.array([92.0, 108.0, 120.0], dtype=np.float32)
    rgb += cyan[None, None, :] * np.clip(np.sin(thickness * 5.0 - theta) * 0.5 + 0.5, 0.0, 1.0)[..., None] * 0.18
    rgb += magenta[None, None, :] * np.clip(np.sin(thickness * 4.1 + theta * 0.7) * 0.5 + 0.5, 0.0, 1.0)[..., None] * 0.14
    rgb += amber[None, None, :] * edge[..., None] * 0.35
    rgb += pearl[None, None, :] * (edge ** 1.6)[..., None] * 0.60
    rgb *= 1.0 - dry_memory[..., None] * 0.72
    rgb += grain[..., None] * np.array([1.4, 1.3, 1.8], dtype=np.float32)
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
    output_path = SKETCH_DIR / "output.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "34", str(output_path),
        ],
        check=True,
    )
    shutil.copyfile(output_path, SKETCH_DIR / f"{WORK_NAME}.mp4")
    shutil.copyfile(FRAMES_DIR / f"frame-{PREVIEW_FRAME:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)


def setup():
    py5.size(*SIZE, py5.P2D)
    FRAMES_DIR.mkdir(exist_ok=True)
    build_base()


def draw():
    rgb_small = render_frame(py5.frame_count)
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
