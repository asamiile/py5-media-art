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
rng = np.random.default_rng()

yy, xx = np.indices((GRID_H, GRID_W), dtype=np.float32)
nx = xx / (GRID_W - 1)
ny = yy / (GRID_H - 1)
cx = nx - 0.5
cy = ny - 0.5

grain = np.zeros((GRID_H, GRID_W), dtype=np.float32)
slow_noise = np.zeros((GRID_H, GRID_W), dtype=np.float32)
salt_memory = np.zeros((GRID_H, GRID_W), dtype=np.float32)
seed_field = np.zeros((GRID_H, GRID_W), dtype=np.float32)


def blur(field: np.ndarray, passes: int = 1) -> np.ndarray:
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


def build_static_fields() -> None:
    global grain, slow_noise, seed_field
    grain = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    grain = blur(grain, 2)

    slow_noise = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    slow_noise = blur(slow_noise, 16)
    slow_noise = (slow_noise - slow_noise.min()) / (slow_noise.max() - slow_noise.min() + 1e-6)

    seeds = [
        (0.22, 0.30, 0.16),
        (0.39, 0.72, 0.13),
        (0.70, 0.38, 0.18),
        (0.82, 0.78, 0.11),
    ]
    seed_field = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    for sx, sy, radius in seeds:
        d = np.sqrt((nx - sx) ** 2 + ((ny - sy) * 1.35) ** 2)
        seed_field = np.maximum(seed_field, np.clip(1.0 - d / radius, 0.0, 1.0))
    seed_field = blur(seed_field, 4)


def channel_field(theta: float) -> np.ndarray:
    warp_x = nx + 0.030 * np.sin(ny * 17.0 + theta * 0.7) + slow_noise * 0.045
    warp_y = ny + 0.025 * np.sin(nx * 13.0 - theta * 0.5) - slow_noise * 0.030
    diagonal = warp_x * 5.7 + warp_y * 7.2
    radial = np.sqrt((cx * 1.25) ** 2 + (cy * 1.55) ** 2)
    vein_wave = (
        np.sin(diagonal * 7.0 + theta * 1.8)
        + 0.68 * np.sin((warp_x * 16.0 - warp_y * 9.0) - theta * 2.1)
        + 0.42 * np.sin(radial * 48.0 - theta * 1.4 + slow_noise * 4.0)
    )
    veins = np.exp(-((vein_wave + 0.20) ** 2) / 0.020)
    hairline = np.exp(-((vein_wave - 0.72) ** 2) / 0.006) * 0.42
    return np.clip(veins + hairline, 0.0, 1.0)


def render_frame(frame: int) -> np.ndarray:
    global salt_memory
    t = frame / TOTAL_FRAMES
    theta = t * np.pi * 2.0

    edge_distance = np.minimum.reduce([nx, 1.0 - nx, ny, 1.0 - ny])
    edge_freeze = 1.0 - smoothstep(0.02 + t * 0.42, 0.18 + t * 0.43, edge_distance)
    seed_freeze = smoothstep(0.12, 0.96, seed_field + t * 1.10 - 0.18)
    crystal_phase = (
        np.sin(nx * 80.0 + slow_noise * 7.0)
        * np.sin(ny * 54.0 - theta * 0.35)
        + 0.45 * np.sin((nx + ny) * 90.0 + theta * 0.55)
    )
    dendrite = smoothstep(0.18, 0.78, crystal_phase + slow_noise * 0.85)
    ice = np.clip(np.maximum(edge_freeze, seed_freeze) * (0.70 + 0.30 * dendrite), 0.0, 1.0)

    channels = channel_field(theta)
    brine = np.clip(channels * (0.30 + 0.95 * ice) * (0.35 + t * 0.95), 0.0, 1.0)
    salt_flash = np.exp(-((channels - 0.84) ** 2) / 0.006) * ice
    salt_memory = np.maximum(salt_memory * 0.982, salt_flash * (0.20 + t * 0.65))

    boundary = np.abs(np.gradient(ice, axis=0)) + np.abs(np.gradient(ice, axis=1))
    boundary = np.clip(boundary * 9.0, 0.0, 1.0)
    frost_spark = np.clip((grain * 0.45 + slow_noise - 0.14) * ice, 0.0, 1.0)

    deep_brine = np.array([5.0, 14.0, 25.0], dtype=np.float32)
    blue_black = np.array([9.0, 19.0, 31.0], dtype=np.float32)
    ice_blue = np.array([95.0, 184.0, 205.0], dtype=np.float32)
    porcelain = np.array([224.0, 236.0, 224.0], dtype=np.float32)
    salt_amber = np.array([218.0, 132.0, 58.0], dtype=np.float32)

    vignette = 0.55 + 0.45 * (1.0 - np.clip((cx * cx * 1.15 + cy * cy * 1.45), 0.0, 0.75) / 0.75)
    rgb = deep_brine[None, None, :] + blue_black[None, None, :] * (0.35 + slow_noise[..., None] * 0.45)
    rgb += ice_blue[None, None, :] * ice[..., None] * 0.58
    rgb += porcelain[None, None, :] * (ice ** 2.1)[..., None] * 0.38
    rgb += porcelain[None, None, :] * boundary[..., None] * 0.52
    rgb -= np.array([8.0, 31.0, 45.0], dtype=np.float32)[None, None, :] * brine[..., None] * 0.95
    rgb += salt_amber[None, None, :] * (salt_memory ** 1.7)[..., None] * 0.72
    rgb += porcelain[None, None, :] * (frost_spark ** 3.0)[..., None] * 0.45
    rgb += grain[..., None] * np.array([1.8, 2.1, 2.4], dtype=np.float32)
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
    build_static_fields()


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
