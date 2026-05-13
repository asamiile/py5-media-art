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
WAVE_SPEED = 0.185
DAMPING = 0.991

rng = np.random.default_rng()

u = np.zeros((GRID_H, GRID_W), dtype=np.float32)
u_prev = np.zeros_like(u)
stress_memory = np.zeros_like(u)
fault_heat = np.zeros_like(u)
base_rgb = np.zeros((GRID_H, GRID_W, 3), dtype=np.float32)
stiffness = np.ones_like(u)
fault_mask = np.zeros_like(u)
layer_phase = np.zeros(GRID_H, dtype=np.float32)
event_schedule: list[tuple[int, float, float, float]] = []


def build_lithograph() -> None:
    global base_rgb, stiffness, fault_mask, layer_phase, event_schedule
    yy, xx = np.indices((GRID_H, GRID_W), dtype=np.float32)
    nx = xx / GRID_W
    ny = yy / GRID_H

    layer_phase = np.cumsum(rng.normal(0.0, 0.028, GRID_H)).astype(np.float32)
    waviness = (
        0.034 * np.sin(nx * np.pi * 5.1 + layer_phase[:, None] * 5.0)
        + 0.018 * np.sin(nx * np.pi * 13.0 + ny * 2.0)
    )
    strata = ny + waviness
    band = 0.5 + 0.5 * np.sin(strata * np.pi * 28.0)
    fine = 0.5 + 0.5 * np.sin(strata * np.pi * 83.0 + np.sin(nx * 17.0))
    grain = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)

    dark_slate = np.array([24.0, 31.0, 34.0], dtype=np.float32)
    warm_shale = np.array([75.0, 63.0, 48.0], dtype=np.float32)
    ash = np.array([142.0, 126.0, 92.0], dtype=np.float32)
    base_rgb = dark_slate[None, None, :] * (0.72 + 0.18 * ny[..., None])
    base_rgb += warm_shale[None, None, :] * (0.25 + 0.24 * band[..., None])
    base_rgb += ash[None, None, :] * (0.10 * fine[..., None])
    base_rgb += grain[..., None] * np.array([4.0, 3.0, 2.0], dtype=np.float32)

    stiffness = (0.78 + 0.32 * band + 0.06 * fine).astype(np.float32)

    fault_mask = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    fault_specs = [
        (0.23, -0.42, 0.006, 1.00),
        (0.47, 0.20, 0.004, 0.70),
        (0.71, -0.24, 0.005, 0.82),
        (0.86, 0.36, 0.004, 0.60),
    ]
    for cx, slope, width, strength in fault_specs:
        line = nx - cx - slope * (ny - 0.5) + 0.018 * np.sin(ny * 18.0 + cx * 7.0)
        fault_mask += strength * np.exp(-(line * line) / (2.0 * width * width))
    fault_mask[:] = np.clip(fault_mask, 0.0, 1.0)
    base_rgb -= fault_mask[..., None] * np.array([15.0, 18.0, 16.0], dtype=np.float32)

    event_schedule = []
    for frame in [1, 92, 166, 248, 330, 412, 500]:
        event_schedule.append(
            (
                frame,
                rng.uniform(GRID_W * 0.10, GRID_W * 0.90),
                rng.uniform(GRID_H * 0.18, GRID_H * 0.82),
                rng.uniform(0.75, 1.45),
            )
        )


def add_impulse(cx: float, cy: float, strength: float, sigma: float) -> None:
    pad = max(8, int(sigma * 5.0))
    x0, x1 = max(0, int(cx - pad)), min(GRID_W, int(cx + pad + 1))
    y0, y1 = max(0, int(cy - pad)), min(GRID_H, int(cy + pad + 1))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.ogrid[y0:y1, x0:x1]
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    s2 = sigma * sigma
    pulse = (1.0 - r2 / (2.0 * s2)) * np.exp(-r2 / (2.0 * s2))
    u[y0:y1, x0:x1] += (strength * pulse).astype(np.float32)


def trigger_events(frame: int) -> None:
    for event_frame, cx, cy, strength in event_schedule:
        if frame == event_frame:
            add_impulse(cx, cy, strength, rng.uniform(5.0, 9.0))

    # A low, continuous tremor from the lower-left margin.
    if frame % 37 == 0:
        t = frame / TOTAL_FRAMES
        add_impulse(
            GRID_W * (0.05 + 0.08 * np.sin(t * np.pi * 3.0)),
            GRID_H * (0.78 + 0.08 * np.cos(t * np.pi * 2.0)),
            0.45,
            7.0,
        )


def step_wave() -> None:
    global u, u_prev, stress_memory, fault_heat
    lap = np.zeros_like(u)
    lap[1:-1, 1:-1] = (
        u[:-2, 1:-1]
        + u[2:, 1:-1]
        + u[1:-1, :-2]
        + u[1:-1, 2:]
        - 4.0 * u[1:-1, 1:-1]
    )
    nonlinear_slip = np.tanh(u * 4.0) * fault_mask * 0.018
    u_next = (2.0 * u - u_prev + WAVE_SPEED * stiffness * lap - nonlinear_slip) * DAMPING
    u_next[0, :] *= 0.82
    u_next[-1, :] *= 0.82
    u_next[:, 0] *= 0.82
    u_next[:, -1] *= 0.82
    u_prev, u = u, u_next

    gy, gx = np.gradient(u)
    strain = np.sqrt(gx * gx + gy * gy)
    stress_memory = np.maximum(stress_memory * 0.985, np.clip(strain * 4.2, 0.0, 1.0))
    fault_heat = np.maximum(fault_heat * 0.970, np.clip(np.abs(u) * fault_mask * 1.35, 0.0, 1.0))


def render_rgb(frame: int) -> np.ndarray:
    crest = np.clip(np.tanh(np.maximum(u, 0.0) * 5.0), 0.0, 1.0)
    trough = np.clip(np.tanh(np.maximum(-u, 0.0) * 5.0), 0.0, 1.0)
    stress = np.clip(stress_memory, 0.0, 1.0)
    hot = np.clip(fault_heat, 0.0, 1.0)

    sulfur = np.array([218.0, 181.0, 82.0], dtype=np.float32)
    rust = np.array([174.0, 80.0, 45.0], dtype=np.float32)
    cold_shadow = np.array([7.0, 18.0, 24.0], dtype=np.float32)
    pale_edge = np.array([226.0, 214.0, 171.0], dtype=np.float32)

    pulse = 0.85 + 0.15 * np.sin(frame * np.pi * 2.0 / TOTAL_FRAMES)
    rgb = base_rgb.copy()
    rgb = rgb * (1.0 - trough[..., None] * 0.26) + cold_shadow[None, None, :] * trough[..., None] * 0.26
    rgb += pale_edge[None, None, :] * crest[..., None] * 0.20
    rgb += sulfur[None, None, :] * stress[..., None] * (0.34 * pulse)
    rgb += rust[None, None, :] * hot[..., None] * 0.70
    rgb += fault_mask[..., None] * hot[..., None] * np.array([55.0, 22.0, 7.0], dtype=np.float32)
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
    build_lithograph()
    add_impulse(GRID_W * 0.18, GRID_H * 0.70, 0.75, 8.0)


def draw():
    trigger_events(py5.frame_count)
    for _ in range(2):
        step_wave()

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
