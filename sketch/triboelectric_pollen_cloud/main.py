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
dust_noise = np.zeros((GRID_H, GRID_W), dtype=np.float32)
charge_memory = np.zeros((GRID_H, GRID_W), dtype=np.float32)
seed_phase = np.zeros((GRID_H, GRID_W), dtype=np.float32)


def blur5(field: np.ndarray, passes: int = 1) -> np.ndarray:
    for _ in range(passes):
        field = (
            field
            + np.roll(field, 1, 0)
            + np.roll(field, -1, 0)
            + np.roll(field, 1, 1)
            + np.roll(field, -1, 1)
        ) / 5.0
    return field


def build_background() -> None:
    global base_rgb, dust_noise, seed_phase
    dusk = np.array([14.0, 16.0, 24.0], dtype=np.float32)
    violet = np.array([54.0, 42.0, 79.0], dtype=np.float32)
    green = np.array([44.0, 72.0, 55.0], dtype=np.float32)
    amber = np.array([92.0, 74.0, 38.0], dtype=np.float32)

    grain = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    grain = blur5(grain, 6)
    slow = 0.5 + 0.5 * np.sin(nx * 5.3 + 0.9 * np.sin(ny * 7.0))
    vertical = np.clip(1.0 - ny * 0.85, 0.0, 1.0)
    vignette = (nx - 0.52) ** 2 * 0.72 + (ny - 0.48) ** 2 * 1.12

    base_rgb = dusk[None, None, :] + violet[None, None, :] * (0.20 + 0.22 * slow[..., None])
    base_rgb += green[None, None, :] * (0.15 + 0.18 * vertical[..., None])
    base_rgb += amber[None, None, :] * (0.04 + 0.05 * np.sin((nx - ny) * 8.0))[..., None]
    base_rgb -= vignette[..., None] * np.array([17.0, 16.0, 20.0], dtype=np.float32)
    base_rgb += grain[..., None] * np.array([2.4, 2.2, 2.9], dtype=np.float32)

    dust_noise = blur5(rng.random((GRID_H, GRID_W), dtype=np.float32), 2)
    seed_phase = rng.random((GRID_H, GRID_W), dtype=np.float32) * np.pi * 2.0


def moving_charges(theta: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cx = np.array([0.18, 0.32, 0.47, 0.61, 0.76, 0.88], dtype=np.float32)
    cy = np.array([0.36, 0.64, 0.28, 0.58, 0.42, 0.70], dtype=np.float32)
    signs = np.array([1.0, -1.0, 1.0, -1.0, -1.0, 1.0], dtype=np.float32)
    cx = cx + 0.040 * np.sin(theta * np.array([0.9, 1.1, 0.7, 1.3, 0.8, 1.0]) + np.arange(6))
    cy = cy + 0.035 * np.cos(theta * np.array([1.2, 0.8, 1.4, 0.9, 1.1, 0.7]) + np.arange(6) * 1.7)
    strength = signs * (0.9 + 0.28 * np.sin(theta * 2.0 + np.arange(6) * 0.9))
    return cx, cy, strength


def pollen_centers(theta: float) -> tuple[np.ndarray, np.ndarray]:
    idx = np.arange(18, dtype=np.float32)
    drift = theta * 0.035
    px = (0.08 + idx * 0.067 + 0.035 * np.sin(theta * 0.7 + idx * 1.13)) % 1.06 - 0.03
    py = 0.52 + 0.28 * np.sin(idx * 2.31 + theta * 0.55) + 0.045 * np.sin(theta * 1.8 + idx)
    py = np.clip(py, 0.10, 0.92)
    px += drift
    return px, py


def render_frame(frame: int) -> np.ndarray:
    global charge_memory
    t = frame / TOTAL_FRAMES
    theta = t * np.pi * 2.0

    cx, cy, strength = moving_charges(theta)
    phi = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    ex = np.zeros_like(phi)
    ey = np.zeros_like(phi)
    for x0, y0, q in zip(cx, cy, strength):
        dx = nx - x0
        dy = ny - y0
        r2 = dx * dx + dy * dy + 0.0015
        inv = 1.0 / np.sqrt(r2)
        phi += q * inv
        ex += q * dx * inv / r2
        ey += q * dy * inv / r2

    field_mag = np.sqrt(ex * ex + ey * ey)
    field_norm = np.clip(field_mag * 0.0038, 0.0, 1.0)
    angle = np.arctan2(ey, ex)
    line_phase = (
        phi * 0.55
        + 11.0 * np.sin(angle * 2.0 + theta)
        + 0.75 * np.sin(nx * 15.0 - ny * 9.0 + theta * 1.7)
        + seed_phase * 0.12
    )
    field_lines = np.exp(-((np.sin(line_phase) - 0.90) ** 2) / 0.018) * field_norm

    px, py = pollen_centers(theta)
    pollen = np.zeros_like(phi)
    pollen_core = np.zeros_like(phi)
    for i, (x0, y0) in enumerate(zip(px, py)):
        dx = nx - x0
        dy = (ny - y0) * 1.78
        d = np.sqrt(dx * dx + dy * dy)
        radius = 0.024 + 0.006 * np.sin(theta * 1.6 + i)
        shell = np.exp(-((d - radius) ** 2) / 0.000012)
        spines = 0.55 + 0.45 * np.sin(np.arctan2(dy, dx) * 18.0 + theta * (1.2 + i * 0.03))
        pollen += shell * (0.35 + spines * 0.95)
        pollen_core += np.exp(-(d * d) / 0.00038) * 0.18

    rubbed_band = np.exp(-((ny - (0.58 + 0.05 * np.sin(nx * 9.0 + theta))) ** 2) / 0.0015)
    corona = np.clip(field_lines * 0.9 + pollen * field_norm * 0.85 + rubbed_band * field_norm * 0.28, 0.0, 1.0)
    charge_memory = np.maximum(charge_memory * 0.978, corona * 0.72)

    violet = np.array([112.0, 104.0, 205.0], dtype=np.float32)
    ion_blue = np.array([70.0, 186.0, 230.0], dtype=np.float32)
    pollen_gold = np.array([225.0, 180.0, 84.0], dtype=np.float32)
    chalk = np.array([238.0, 226.0, 179.0], dtype=np.float32)
    ember = np.array([210.0, 92.0, 72.0], dtype=np.float32)

    rgb = base_rgb.copy()
    rgb += dust_noise[..., None] * np.array([4.0, 3.2, 2.2], dtype=np.float32)
    rgb += violet[None, None, :] * field_lines[..., None] * 0.30
    rgb += ion_blue[None, None, :] * (field_lines ** 1.7)[..., None] * 0.78
    rgb += pollen_gold[None, None, :] * pollen[..., None] * 0.72
    rgb += chalk[None, None, :] * (pollen_core + pollen ** 2.0)[..., None] * 0.42
    rgb += ember[None, None, :] * charge_memory[..., None] * 0.20
    rgb -= np.clip(field_norm[..., None] - 0.45, 0.0, 1.0) * np.array([10.0, 5.0, 0.0], dtype=np.float32)
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
    build_background()


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
