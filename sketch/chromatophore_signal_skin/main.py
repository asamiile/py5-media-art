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
skin_grain = np.zeros((GRID_H, GRID_W), dtype=np.float32)
phase_jitter = np.zeros((GRID_H, GRID_W), dtype=np.float32)
signal_memory = np.zeros((GRID_H, GRID_W), dtype=np.float32)


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


def build_skin() -> None:
    global base_rgb, skin_grain, phase_jitter
    umber = np.array([38.0, 25.0, 20.0], dtype=np.float32)
    mauve = np.array([88.0, 54.0, 68.0], dtype=np.float32)
    olive = np.array([42.0, 70.0, 54.0], dtype=np.float32)
    pearl = np.array([122.0, 112.0, 94.0], dtype=np.float32)

    grain = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    grain = smooth(grain, 5)
    broad = (
        0.5
        + 0.5 * np.sin(nx * 8.0 + 1.2 * np.sin(ny * 5.0))
        * np.cos(ny * 7.0 + 0.8 * np.sin(nx * 4.0))
    )
    vascular = 0.5 + 0.5 * np.sin((nx * 17.0 - ny * 12.0) + 0.6 * np.sin(ny * 9.0))
    vignette = (nx - 0.50) ** 2 * 0.70 + (ny - 0.52) ** 2 * 0.95

    base_rgb = umber[None, None, :] + mauve[None, None, :] * (0.28 + 0.16 * broad[..., None])
    base_rgb += olive[None, None, :] * (0.10 + 0.10 * vascular[..., None])
    base_rgb += pearl[None, None, :] * (0.05 + 0.06 * (1.0 - ny))[..., None]
    base_rgb -= vignette[..., None] * np.array([20.0, 17.0, 15.0], dtype=np.float32)
    base_rgb += grain[..., None] * np.array([2.9, 2.2, 2.0], dtype=np.float32)

    skin_grain = smooth(rng.random((GRID_H, GRID_W), dtype=np.float32), 2)
    phase_jitter = smooth(rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32), 3)


def chromatophore_field(theta: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cell_w = 0.033
    cell_h = 0.046
    row = np.floor(ny / cell_h)
    offset = (row % 2.0) * cell_w * 0.5
    local_x = ((nx + offset) / cell_w) % 1.0 - 0.5
    local_y = (ny / cell_h) % 1.0 - 0.5
    local_y *= 0.78
    radius = np.sqrt(local_x * local_x + local_y * local_y)

    row_phase = row * 0.37
    wave_a = np.sin(nx * 11.0 + ny * 22.0 - theta * 2.7 + row_phase)
    wave_b = np.sin(nx * 29.0 - ny * 8.0 + theta * 3.8 + phase_jitter * 0.38)
    wave_c = np.sin(np.sqrt((nx - 0.25) ** 2 + (ny - 0.58) ** 2) * 42.0 - theta * 5.2)
    expansion = np.clip(0.44 + 0.28 * wave_a + 0.18 * wave_b + 0.22 * wave_c, 0.08, 0.96)

    spot_edge = 0.105 + expansion * 0.205
    disk = np.clip((spot_edge - radius) / 0.018, 0.0, 1.0)
    ring = np.exp(-((radius - spot_edge) ** 2) / 0.00034)
    spoke = 0.55 + 0.45 * np.sin(np.arctan2(local_y, local_x) * 14.0 + theta * 1.6 + row_phase)
    pigment = np.clip(disk * (0.66 + 0.34 * spoke) + ring * 0.58, 0.0, 1.0)
    iridescence = np.exp(-((radius - spot_edge * 0.62) ** 2) / 0.00055) * (0.4 + 0.6 * wave_b)
    return pigment, ring, np.clip(iridescence, 0.0, 1.0)


def render_frame(frame: int) -> np.ndarray:
    global signal_memory
    t = frame / TOTAL_FRAMES
    theta = t * np.pi * 2.0

    pigment, ring, iridescence = chromatophore_field(theta)
    nerve_wave = (
        np.sin(nx * 5.0 + ny * 35.0 - theta * 6.2)
        + 0.5 * np.sin(nx * 27.0 - theta * 3.0)
    )
    nerve = np.exp(-((nerve_wave - 0.82) ** 2) / 0.035)
    shear = np.clip(np.abs(np.gradient(pigment)[1]) * 5.0, 0.0, 1.0)
    signal_memory = np.maximum(signal_memory * 0.972, np.clip((nerve * 0.55 + ring * 0.42) * shear, 0.0, 1.0))

    brown = np.array([166.0, 74.0, 42.0], dtype=np.float32)
    crimson = np.array([150.0, 42.0, 67.0], dtype=np.float32)
    gold = np.array([222.0, 162.0, 74.0], dtype=np.float32)
    cyan = np.array([68.0, 172.0, 160.0], dtype=np.float32)
    pearl = np.array([224.0, 210.0, 176.0], dtype=np.float32)

    rgb = base_rgb.copy()
    rgb += skin_grain[..., None] * np.array([3.6, 2.5, 1.8], dtype=np.float32)
    rgb += brown[None, None, :] * pigment[..., None] * 0.56
    rgb += crimson[None, None, :] * (pigment ** 1.8)[..., None] * 0.24
    rgb += gold[None, None, :] * ring[..., None] * 0.34
    rgb += cyan[None, None, :] * iridescence[..., None] * 0.42
    rgb += pearl[None, None, :] * (nerve ** 1.5)[..., None] * 0.26
    rgb += cyan[None, None, :] * signal_memory[..., None] * 0.24
    rgb -= pigment[..., None] * np.array([5.0, 8.0, 10.0], dtype=np.float32)
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
    build_skin()


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
