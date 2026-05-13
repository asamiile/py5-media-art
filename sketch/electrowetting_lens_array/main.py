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

base_grain = np.zeros((GRID_H, GRID_W), dtype=np.float32)
memory = np.zeros((GRID_H, GRID_W), dtype=np.float32)


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
    global base_grain
    base_grain = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    base_grain = blur(base_grain, 3)
    base_grain = (base_grain - base_grain.min()) / (base_grain.max() - base_grain.min() + 1e-6)


def lens_centers(theta: float) -> list[tuple[float, float, float, float]]:
    centers = []
    for row in range(3):
        for col in range(5):
            cx = 0.12 + col * 0.19 + 0.018 * np.sin(theta * 0.62 + row * 1.7 + col * 0.6)
            cy = 0.22 + row * 0.27 + 0.015 * np.cos(theta * 0.74 + col * 1.2)
            phase = row * 0.9 + col * 0.55
            centers.append((cx, cy, phase, 0.045 + 0.005 * ((row + col) % 3)))
    return centers


def render_frame(frame: int) -> np.ndarray:
    global memory
    t = frame / TOTAL_FRAMES
    theta = t * np.pi * 2.0

    droplet = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    rim = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    caustic = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    electrode = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    voltage_trace = np.zeros((GRID_H, GRID_W), dtype=np.float32)

    sweep = 0.52 + 0.48 * np.sin(theta * 1.15 + nx * 5.8)
    for cx, cy, phase, base_radius in lens_centers(theta):
        pulse = 0.5 + 0.5 * np.sin(theta * 2.0 + phase)
        flattened = smoothstep(0.18, 0.92, pulse)
        rx = base_radius * (1.35 + 0.50 * flattened)
        ry = base_radius * (1.10 - 0.34 * flattened)
        dx = nx - cx
        dy = (ny - cy) * 1.78
        d = np.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)
        body = 1.0 - smoothstep(0.74, 1.0, d)
        edge = np.exp(-((d - 1.0) ** 2) / 0.0045)
        inner = np.exp(-((d - 0.44 - flattened * 0.16) ** 2) / 0.015)
        focus = np.sin((dx * 86.0 + dy * 52.0) + theta * (3.0 + flattened * 1.8) + phase)
        focus = np.exp(-((focus - 0.90) ** 2) / 0.030) * body
        droplet = np.maximum(droplet, body * (0.42 + flattened * 0.55))
        rim = np.maximum(rim, edge * (0.50 + flattened * 0.55))
        caustic = np.maximum(caustic, (focus + inner * 0.28) * (0.36 + flattened * 0.80))

        wire = np.exp(-((ny - cy) ** 2) / 0.000012) * np.exp(-((nx - cx + 0.09) ** 2) / 0.008)
        pad = np.exp(-(((nx - cx + 0.10) / 0.014) ** 2 + ((ny - cy) / 0.060) ** 2))
        electrode = np.maximum(electrode, wire * 0.45 + pad * 0.22)
        spark = np.exp(-((nx - (0.08 + 0.84 * sweep)) ** 2) / 0.000035)
        voltage_trace = np.maximum(voltage_trace, spark * wire * flattened)

    memory = np.maximum(memory * 0.970, voltage_trace * 0.80 + caustic * 0.08)

    glass_line = (
        0.5
        + 0.5 * np.sin(nx * 78.0 + 0.35 * np.sin(ny * 11.0 + theta))
    ) * 0.055
    vignette = 1.0 - np.clip((nx - 0.52) ** 2 * 1.15 + (ny - 0.50) ** 2 * 1.45, 0.0, 0.78) / 0.92

    graphite = np.array([8.0, 11.0, 13.0], dtype=np.float32)
    oil_blue = np.array([18.0, 46.0, 58.0], dtype=np.float32)
    aquamarine = np.array([70.0, 208.0, 188.0], dtype=np.float32)
    silver = np.array([205.0, 222.0, 213.0], dtype=np.float32)
    amber = np.array([232.0, 157.0, 67.0], dtype=np.float32)

    rgb = graphite[None, None, :] + oil_blue[None, None, :] * (0.35 + base_grain[..., None] * 0.18)
    rgb += glass_line[..., None] * np.array([22.0, 38.0, 38.0], dtype=np.float32)
    rgb += aquamarine[None, None, :] * droplet[..., None] * 0.40
    rgb += silver[None, None, :] * rim[..., None] * 0.74
    rgb += aquamarine[None, None, :] * caustic[..., None] * 0.96
    rgb += silver[None, None, :] * (caustic ** 2.2)[..., None] * 0.70
    rgb += amber[None, None, :] * memory[..., None] * 0.70
    rgb += silver[None, None, :] * electrode[..., None] * 0.20
    rgb += base_grain[..., None] * np.array([2.4, 2.6, 2.2], dtype=np.float32)
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
