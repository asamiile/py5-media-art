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
DROP_COUNT = 19
rng = np.random.default_rng()

yy, xx = np.indices((GRID_H, GRID_W), dtype=np.float32)
nx = xx / GRID_W
ny = yy / GRID_H

centers = np.zeros((DROP_COUNT, 2), dtype=np.float32)
radii = np.zeros(DROP_COUNT, dtype=np.float32)
phase = np.zeros(DROP_COUNT, dtype=np.float32)
base_rgb = np.zeros((GRID_H, GRID_W, 3), dtype=np.float32)
residue = np.zeros((GRID_H, GRID_W), dtype=np.float32)


def build_surface() -> None:
    global centers, radii, phase, base_rgb
    centers = rng.uniform([0.10, 0.16], [0.90, 0.84], (DROP_COUNT, 2)).astype(np.float32)
    # Keep a few larger anchor drops so bridges have visible endpoints.
    radii = rng.uniform(0.026, 0.060, DROP_COUNT).astype(np.float32)
    radii[:5] *= rng.uniform(1.15, 1.45, 5)
    phase = rng.uniform(0.0, np.pi * 2.0, DROP_COUNT).astype(np.float32)

    graphite = np.array([12.0, 16.0, 17.0], dtype=np.float32)
    slate = np.array([42.0, 50.0, 48.0], dtype=np.float32)
    olive = np.array([58.0, 62.0, 42.0], dtype=np.float32)
    grain = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    brushing = 0.5 + 0.5 * np.sin(nx * 90.0 + 4.0 * np.sin(ny * 12.0))
    vignette = (nx - 0.52) ** 2 * 0.50 + (ny - 0.50) ** 2 * 0.92
    base_rgb = graphite[None, None, :] + slate[None, None, :] * (0.45 - vignette[..., None])
    base_rgb += olive[None, None, :] * brushing[..., None] * 0.11
    base_rgb += grain[..., None] * np.array([3.0, 3.0, 2.0], dtype=np.float32)


def segment_distance(px, py, ax, ay, bx, by):
    vx = bx - ax
    vy = by - ay
    wx = px - ax
    wy = py - ay
    denom = vx * vx + vy * vy + 1e-6
    t = np.clip((wx * vx + wy * vy) / denom, 0.0, 1.0)
    qx = ax + t * vx
    qy = ay + t * vy
    return np.sqrt((px - qx) ** 2 + (py - qy) ** 2), t


def render_frame(frame: int) -> np.ndarray:
    global residue
    t = frame / TOTAL_FRAMES
    theta = t * np.pi * 2.0
    current = centers.copy()
    current[:, 0] += 0.018 * np.sin(theta * 0.8 + phase)
    current[:, 1] += 0.014 * np.cos(theta * 1.1 + phase * 1.3)

    liquid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    rim = np.zeros_like(liquid)
    snap = np.zeros_like(liquid)

    for i in range(DROP_COUNT):
        cx, cy = current[i]
        r = radii[i] * (0.94 + 0.08 * np.sin(theta + phase[i]))
        d = np.sqrt((nx - cx) ** 2 + (ny - cy) ** 2)
        body = np.clip(1.0 - d / r, 0.0, 1.0)
        liquid = np.maximum(liquid, body ** 0.42)
        rim += np.exp(-((d - r) ** 2) / (2.0 * (r * 0.055) ** 2)) * 0.55

    # Capillary bridges between near neighbors; the waist periodically thins and snaps.
    for i in range(DROP_COUNT):
        for j in range(i + 1, DROP_COUNT):
            ax, ay = current[i]
            bx, by = current[j]
            dist_centers = np.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
            reach = radii[i] + radii[j] + 0.145
            if dist_centers > reach:
                continue
            d, s = segment_distance(nx, ny, ax, ay, bx, by)
            bridge_phase = (np.sin(theta * 1.45 + phase[i] - phase[j]) + 1.0) * 0.5
            neck = 1.0 - 0.68 * bridge_phase * np.exp(-((s - 0.5) ** 2) / 0.045)
            width = (0.010 + 0.026 * (1.0 - dist_centers / reach)) * neck
            bridge = np.exp(-(d ** 2) / (2.0 * width ** 2))
            liquid = np.maximum(liquid, bridge * 0.72)
            rim += bridge * (0.10 + 0.35 * bridge_phase)
            if bridge_phase > 0.82:
                cut = np.exp(-((s - 0.5) ** 2) / 0.010) * np.exp(-(d ** 2) / (2.0 * (width * 1.7) ** 2))
                snap += cut * (bridge_phase - 0.82) * 5.2

    residue = np.maximum(residue * 0.982, np.clip(snap, 0.0, 1.0))

    gy, gx = np.gradient(liquid)
    slope = np.clip(np.sqrt(gx * gx + gy * gy) * 14.0, 0.0, 1.0)
    meniscus = np.clip(rim, 0.0, 1.0)

    ink = np.array([8.0, 14.0, 15.0], dtype=np.float32)
    glass = np.array([92.0, 164.0, 154.0], dtype=np.float32)
    pearl = np.array([226.0, 232.0, 210.0], dtype=np.float32)
    amber = np.array([229.0, 151.0, 72.0], dtype=np.float32)

    rgb = base_rgb.copy()
    rgb = rgb * (1.0 - liquid[..., None] * 0.50) + ink[None, None, :] * liquid[..., None] * 0.50
    rgb += glass[None, None, :] * liquid[..., None] * 0.34
    rgb += pearl[None, None, :] * slope[..., None] * 0.42
    rgb += amber[None, None, :] * residue[..., None] * 0.85
    rgb += pearl[None, None, :] * meniscus[..., None] * 0.20
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
            "-crf", "18", str(output_path),
        ],
        check=True,
    )
    shutil.copyfile(output_path, SKETCH_DIR / f"{WORK_NAME}.mp4")
    shutil.copyfile(FRAMES_DIR / f"frame-{PREVIEW_FRAME:04d}.png", SKETCH_DIR / PREVIEW_FILENAME)


def setup():
    py5.size(*SIZE, py5.P2D)
    FRAMES_DIR.mkdir(exist_ok=True)
    build_surface()


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
