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
protein_speckle = np.zeros((GRID_H, GRID_W), dtype=np.float32)
memory = np.zeros((GRID_H, GRID_W), dtype=np.float32)
phase_offsets = np.zeros((GRID_H, GRID_W), dtype=np.float32)


def build_membrane() -> None:
    global base_rgb, protein_speckle, phase_offsets
    deep = np.array([10.0, 18.0, 22.0], dtype=np.float32)
    teal_milk = np.array([45.0, 93.0, 94.0], dtype=np.float32)
    rose_shadow = np.array([70.0, 42.0, 58.0], dtype=np.float32)

    grain = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    for _ in range(5):
        grain = (
            grain
            + np.roll(grain, 1, 0)
            + np.roll(grain, -1, 0)
            + np.roll(grain, 1, 1)
            + np.roll(grain, -1, 1)
        ) / 5.0
    slow = (
        0.5
        + 0.5 * np.sin(nx * 7.0 + 1.2 * np.sin(ny * 5.0))
        * np.cos(ny * 9.0 + 0.7 * np.sin(nx * 4.0))
    )
    vignette = (nx - 0.50) ** 2 * 0.55 + (ny - 0.52) ** 2 * 0.85
    base_rgb = deep[None, None, :] + teal_milk[None, None, :] * (0.25 + 0.13 * slow[..., None])
    base_rgb += rose_shadow[None, None, :] * (0.11 + 0.09 * np.sin((nx + ny) * 6.0))[..., None]
    base_rgb -= vignette[..., None] * np.array([16.0, 20.0, 18.0], dtype=np.float32)
    base_rgb += grain[..., None] * np.array([1.6, 1.8, 1.4], dtype=np.float32)

    protein_speckle = (
        0.5 + 0.5 * np.sin(nx * 44.0 + 0.8 * np.sin(ny * 10.0))
    ) * (0.5 + 0.5 * np.sin(ny * 38.0 + 0.3 * np.sin(nx * 8.0)))
    phase_offsets = rng.normal(0.0, 0.24, (GRID_H, GRID_W)).astype(np.float32)


def render_frame(frame: int) -> np.ndarray:
    global memory
    t = frame / TOTAL_FRAMES
    theta = t * np.pi * 2.0

    wave = (
        nx * 18.0
        + ny * 31.0
        - theta * 5.4
        + 0.7 * np.sin(nx * 8.0 - theta)
        + phase_offsets
    )
    secondary = nx * 9.0 - ny * 13.0 + theta * 2.2

    beat = np.sin(wave)
    recovery = np.sin(wave - 0.82)
    bend = np.sin(wave + 0.55 * np.sin(secondary))

    # Comb-like ridges: local coordinate along short cilia strokes.
    spacing = 0.020 + 0.004 * np.sin(ny * 11.0)
    cilia_columns = np.abs(((nx + 0.012 * np.sin(ny * 24.0)) / spacing) % 1.0 - 0.5)
    cilia_rows = np.abs(((ny + 0.008 * np.cos(nx * 19.0)) / 0.036) % 1.0 - 0.5)
    shaft = np.exp(-(cilia_columns ** 2) / 0.0026) * np.exp(-(cilia_rows ** 2) / 0.060)
    shaft *= 0.36 + 0.64 * np.clip(bend * 0.5 + 0.5, 0.0, 1.0)

    crest = np.clip(beat * 0.5 + 0.5, 0.0, 1.0) ** 2.2
    return_wake = np.clip(recovery * 0.5 + 0.5, 0.0, 1.0) ** 3.0
    metachronal_band = np.exp(-((beat - 0.78) ** 2) / 0.070)

    flow = shaft * (0.30 + 0.95 * crest) + metachronal_band * 0.35
    shear = np.clip(np.abs(np.gradient(beat)[1]) * 2.8, 0.0, 1.0)
    memory = np.maximum(memory * 0.976, np.clip(flow * shear, 0.0, 1.0))

    cyan = np.array([74.0, 210.0, 196.0], dtype=np.float32)
    pearl = np.array([226.0, 235.0, 214.0], dtype=np.float32)
    coral = np.array([226.0, 118.0, 122.0], dtype=np.float32)
    indigo = np.array([18.0, 22.0, 38.0], dtype=np.float32)

    rgb = base_rgb.copy()
    rgb = rgb * (1.0 - return_wake[..., None] * 0.18) + indigo[None, None, :] * return_wake[..., None] * 0.18
    rgb += cyan[None, None, :] * flow[..., None] * 0.46
    rgb += pearl[None, None, :] * (metachronal_band ** 1.6)[..., None] * 0.52
    rgb += coral[None, None, :] * memory[..., None] * 0.22
    rgb += protein_speckle[..., None] * np.array([2.2, 3.0, 2.6], dtype=np.float32)
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
            "-crf", "31", str(output_path),
        ],
        check=True,
    )
    shutil.copyfile(output_path, SKETCH_DIR / f"{WORK_NAME}.mp4")
    shutil.copyfile(FRAMES_DIR / f"frame-{PREVIEW_FRAME:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)


def setup():
    py5.size(*SIZE, py5.P2D)
    FRAMES_DIR.mkdir(exist_ok=True)
    build_membrane()


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
