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

GRID_W, GRID_H = 960, 540
yy, xx = np.indices((GRID_H, GRID_W), dtype=np.float32)
nx = xx / (GRID_W - 1)
ny = yy / (GRID_H - 1)
rng = np.random.default_rng()

grain = np.zeros((GRID_H, GRID_W), dtype=np.float32)
orientation = np.zeros((GRID_H, GRID_W), dtype=np.float32)
solute_memory = np.zeros((GRID_H, GRID_W), dtype=np.float32)


def blur(field: np.ndarray, passes: int) -> np.ndarray:
    for _ in range(passes):
        field = (
            field
            + np.roll(field, 1, 0)
            + np.roll(field, -1, 0)
            + np.roll(field, 1, 1)
            + np.roll(field, -1, 1)
        ) / 5.0
    return field


def smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    x = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def build_base() -> None:
    global grain, orientation
    grain = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    grain = blur(grain, 8)
    grain = (grain - grain.min()) / (grain.max() - grain.min() + 1e-6)

    cells = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    cells = blur(cells, 18)
    cells = (cells - cells.min()) / (cells.max() - cells.min() + 1e-6)
    orientation = (cells - 0.5) * 2.0


def render_frame(frame: int) -> np.ndarray:
    global solute_memory
    t = frame / TOTAL_FRAMES
    theta = t * np.pi * 2.0

    cooling = -0.08 + 1.36 * t
    interface_bias = (
        nx
        + 0.075 * np.sin(ny * 9.0 + theta * 0.72)
        + 0.038 * np.sin(ny * 25.0 - theta * 1.25 + grain * 4.1)
        + 0.026 * orientation
    )
    solid = smoothstep(0.055, -0.035, interface_bias - cooling)
    secondary_front = smoothstep(
        0.040,
        -0.030,
        (1.0 - ny) + 0.12 * np.sin(nx * 7.0 - theta * 0.55) - (cooling * 0.78 - 0.22),
    )
    solid = np.maximum(solid, secondary_front * 0.62)

    distance = interface_bias - cooling
    front_band = np.exp(-(distance**2) / 0.00155)
    undercooled = np.exp(-((distance + 0.035) ** 2) / 0.007) * (1.0 - solid * 0.75)

    rotated = (
        nx * (54.0 + orientation * 12.0)
        + ny * (26.0 - orientation * 19.0)
        + 2.6 * np.sin((nx + ny) * 11.0 + theta * 0.42)
    )
    lamella = 0.5 + 0.5 * np.sin(rotated + theta * 0.20)
    phase_a = smoothstep(0.32, 0.58, lamella)
    lamella_edge = np.exp(-((lamella - 0.50) ** 2) / 0.0038)

    branch_phase = (
        np.sin(nx * 72.0 + orientation * 7.0 - theta * 0.36)
        + np.sin(ny * 88.0 + nx * 16.0 + theta * 0.18)
    ) * 0.5
    dendrite_tips = smoothstep(0.48, 0.88, branch_phase) * front_band
    grain_boundaries = np.exp(-((np.sin(orientation * 9.0 + nx * 8.0 - ny * 6.0)) ** 2) / 0.025) * solid

    solute_wave = 0.5 + 0.5 * np.sin(nx * 41.0 - ny * 37.0 + theta * 0.62 + grain * 5.0)
    rejected_solute = (
        smoothstep(0.72, 0.98, solute_wave)
        * (front_band * 0.65 + lamella_edge * solid * 0.30)
        + undercooled * 0.11
    )
    solute_memory = np.maximum(solute_memory * 0.982, rejected_solute)

    ripple = 0.5 + 0.5 * np.sin(nx * 18.0 + ny * 7.0 - theta * 1.15)
    vignette = 1.0 - np.clip((nx - 0.56) ** 2 * 0.95 + (ny - 0.48) ** 2 * 1.55, 0.0, 0.82)

    graphite = np.array([7.0, 9.0, 11.0], dtype=np.float32)
    iron_blue = np.array([16.0, 31.0, 44.0], dtype=np.float32)
    pewter = np.array([112.0, 126.0, 130.0], dtype=np.float32)
    silver = np.array([214.0, 226.0, 218.0], dtype=np.float32)
    dark_phase = np.array([46.0, 65.0, 75.0], dtype=np.float32)
    copper = np.array([226.0, 132.0, 49.0], dtype=np.float32)

    melt = graphite[None, None, :] + iron_blue[None, None, :] * (0.42 + ripple[..., None] * 0.12)
    metal_a = pewter[None, None, :] * 0.84 + silver[None, None, :] * 0.28
    metal_b = dark_phase[None, None, :] * 0.95 + silver[None, None, :] * 0.12
    alloy = metal_a * phase_a[..., None] + metal_b * (1.0 - phase_a[..., None])

    rgb = melt * (1.0 - solid[..., None]) + alloy * solid[..., None]
    rgb += silver[None, None, :] * front_band[..., None] * 0.58
    rgb += silver[None, None, :] * dendrite_tips[..., None] * 0.92
    rgb += np.array([18.0, 28.0, 31.0], dtype=np.float32)[None, None, :] * grain_boundaries[..., None]
    rgb += copper[None, None, :] * solute_memory[..., None] * 0.82
    rgb += silver[None, None, :] * lamella_edge[..., None] * solid[..., None] * 0.13
    rgb += grain[..., None] * np.array([6.0, 6.4, 5.2], dtype=np.float32)
    rgb *= vignette[..., None]
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
            "ffmpeg",
            "-y",
            "-r",
            str(FPS),
            "-start_number",
            "1",
            "-i",
            str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "34",
            str(output_path),
        ],
        check=True,
    )
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
