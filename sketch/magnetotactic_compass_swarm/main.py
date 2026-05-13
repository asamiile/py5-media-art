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
N_BACTERIA = 14000
ROD_SAMPLES = np.linspace(-1.0, 1.0, 9, dtype=np.float32)
rng = np.random.default_rng()

yy, xx = np.indices((GRID_H, GRID_W), dtype=np.float32)
nx = xx / (GRID_W - 1)
ny = yy / (GRID_H - 1)

pos = rng.random((N_BACTERIA, 2), dtype=np.float32)
theta = rng.uniform(-np.pi, np.pi, N_BACTERIA).astype(np.float32)
speed = rng.uniform(0.0012, 0.0028, N_BACTERIA).astype(np.float32)
magnetite = rng.uniform(0.25, 1.0, N_BACTERIA).astype(np.float32)
trail = np.zeros((GRID_H, GRID_W), dtype=np.float32)
field_memory = np.zeros((GRID_H, GRID_W), dtype=np.float32)
base_noise = np.zeros((GRID_H, GRID_W), dtype=np.float32)


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


def build_base() -> None:
    global base_noise
    base_noise = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    base_noise = blur(base_noise, 5)
    base_noise = (base_noise - base_noise.min()) / (base_noise.max() - base_noise.min() + 1e-6)


def wrap_angle(angle: np.ndarray) -> np.ndarray:
    return (angle + np.pi) % (np.pi * 2.0) - np.pi


def update_agents(frame: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    global pos, theta
    t = frame / TOTAL_FRAMES
    field_angle = -0.65 + t * np.pi * 2.35
    field_vec = np.array([np.cos(field_angle), np.sin(field_angle)], dtype=np.float32)

    oxygen = 0.45 + 0.38 * np.sin((pos[:, 0] * 3.8 + pos[:, 1] * 1.4 + t * 1.6) * np.pi)
    oxygen += 0.22 * np.sin((pos[:, 1] * 5.2 - t * 2.3) * np.pi)
    oxygen_turn = np.sin(oxygen * 5.0 + magnetite * 2.0) * 0.010

    desired = np.arctan2(field_vec[1], field_vec[0])
    alignment = wrap_angle(desired - theta)
    wobble = rng.normal(0.0, 0.018, N_BACTERIA).astype(np.float32)
    theta += alignment * (0.018 + magnetite * 0.030) + oxygen_turn + wobble

    heading = np.column_stack((np.cos(theta), np.sin(theta))).astype(np.float32)
    drift = np.column_stack(
        (
            0.00045 * np.sin(pos[:, 1] * 18.0 + t * 7.0),
            0.00035 * np.cos(pos[:, 0] * 16.0 - t * 5.0),
        )
    ).astype(np.float32)
    pos += heading * speed[:, None] + field_vec[None, :] * (0.00025 * magnetite[:, None]) + drift
    pos %= 1.0
    return heading, field_vec, oxygen


def deposit_rods(heading: np.ndarray, oxygen: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    density = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    cores = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    signal = np.zeros((GRID_H, GRID_W), dtype=np.float32)

    px = pos[:, 0] * (GRID_W - 1)
    py = pos[:, 1] * (GRID_H - 1)
    rod_len = (3.0 + magnetite * 5.2).astype(np.float32)
    for sample in ROD_SAMPLES:
        sx = np.clip((px + heading[:, 0] * rod_len * sample).astype(np.int32), 0, GRID_W - 1)
        sy = np.clip((py + heading[:, 1] * rod_len * sample).astype(np.int32), 0, GRID_H - 1)
        weight = (1.0 - abs(sample) * 0.55) * (0.65 + oxygen * 0.35)
        np.add.at(density, (sy, sx), weight)

    core_x = np.clip(px.astype(np.int32), 0, GRID_W - 1)
    core_y = np.clip(py.astype(np.int32), 0, GRID_H - 1)
    np.add.at(cores, (core_y, core_x), magnetite * 1.6)

    tip_x = np.clip((px + heading[:, 0] * rod_len * 1.45).astype(np.int32), 0, GRID_W - 1)
    tip_y = np.clip((py + heading[:, 1] * rod_len * 1.45).astype(np.int32), 0, GRID_H - 1)
    np.add.at(signal, (tip_y, tip_x), oxygen * magnetite)
    return density, cores, signal


def render_frame(frame: int) -> np.ndarray:
    global trail, field_memory
    heading, field_vec, oxygen = update_agents(frame)
    density, cores, signal = deposit_rods(heading, oxygen)

    trail = np.maximum(trail * 0.955, blur(density, 1) * 0.30)
    field_lines = np.sin((nx * field_vec[0] + ny * field_vec[1]) * 74.0 + frame * 0.035)
    field_lines = np.exp(-((field_lines - 0.70) ** 2) / 0.030) * 0.34
    field_memory = np.maximum(field_memory * 0.970, field_lines)

    density = np.clip(blur(density, 1) * 0.56, 0.0, 1.0)
    cores = np.clip(blur(cores, 1) * 0.32, 0.0, 1.0)
    signal = np.clip(blur(signal, 2) * 0.62, 0.0, 1.0)
    trail_view = np.clip(trail, 0.0, 1.0)

    olive = np.array([13.0, 24.0, 20.0], dtype=np.float32)
    umber = np.array([46.0, 39.0, 24.0], dtype=np.float32)
    teal = np.array([82.0, 232.0, 194.0], dtype=np.float32)
    pearl = np.array([230.0, 236.0, 210.0], dtype=np.float32)
    amber = np.array([246.0, 154.0, 62.0], dtype=np.float32)
    ink = np.array([5.0, 8.0, 10.0], dtype=np.float32)

    vignette = 1.0 - np.clip(((nx - 0.5) ** 2 * 1.1 + (ny - 0.5) ** 2 * 1.5), 0.0, 0.65) / 0.95
    rgb = olive[None, None, :] + umber[None, None, :] * (0.18 + base_noise[..., None] * 0.22)
    rgb += teal[None, None, :] * density[..., None] * 1.05
    rgb += pearl[None, None, :] * (density ** 2.0)[..., None] * 0.86
    rgb += teal[None, None, :] * trail_view[..., None] * 0.50
    rgb += amber[None, None, :] * signal[..., None] * 1.12
    rgb += pearl[None, None, :] * field_memory[..., None] * 0.25
    rgb -= ink[None, None, :] * cores[..., None] * 1.10
    rgb += base_noise[..., None] * np.array([2.2, 2.6, 2.1], dtype=np.float32)
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
            "ffmpeg", "-y", "-r", str(FPS),
            "-start_number", "1",
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
