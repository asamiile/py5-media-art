from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Burke-Shaw Attractor
# dx/dt = -s*(x + y)
# dy/dt = -y - s*x*z
# dz/dt =  s*x*y + v
# Chaotic params: s=10, v=4.272  -> twin-lobe strange attractor
N = 1000000
rng = np.random.default_rng()
x = rng.uniform(-2, 2, N).astype(np.float32)
y = rng.uniform(-2, 2, N).astype(np.float32)
z = rng.uniform(-2, 2, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)


def step_burke_shaw(s, v, dt=0.01):
    global x, y, z

    dx = -s * (x + y)
    dy = -y - s * x * z
    dz = s * x * y + v

    x_new = x + dx * dt
    y_new = y + dy * dt
    z_new = z + dz * dt

    mask = (np.abs(x_new) > 100) | (np.abs(y_new) > 100) | (np.abs(z_new) > 100) | np.isnan(x_new)
    n_reset = int(np.sum(mask))
    if n_reset > 0:
        x_new[mask] = rng.uniform(-2, 2, n_reset).astype(np.float32)
        y_new[mask] = rng.uniform(-2, 2, n_reset).astype(np.float32)
        z_new[mask] = rng.uniform(-2, 2, n_reset).astype(np.float32)

    x[:] = x_new
    y[:] = y_new
    z[:] = z_new


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    print("[Setup] Warming up...", flush=True)
    for _ in range(3000):
        step_burke_shaw(10.0, 4.272, dt=0.01)
    print("[Setup] Done.", flush=True)


def draw():
    global density_buffer

    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES

    s = 10.0
    v = 4.272 + 0.15 * np.sin(t * 1.3)

    for _ in range(5):
        step_burke_shaw(s, v, dt=0.01)

    # Slow rotation
    theta = t * 0.3
    phi = np.sin(t * 0.7) * 0.6

    x_rot1 = x * np.cos(theta) - y * np.sin(theta)
    y_rot1 = x * np.sin(theta) + y * np.cos(theta)
    x_rot2 = x_rot1
    y_rot2 = y_rot1 * np.cos(phi) - z * np.sin(phi)

    # Adaptive scale
    cx = float(np.median(x_rot2))
    cy = float(np.median(y_rot2))
    rx = max(4.0 * float(np.std(x_rot2)), 0.1)
    ry = max(4.0 * float(np.std(y_rot2)), 0.1)

    screen_x = (x_rot2 - cx) / rx * SIZE[0] + SIZE[0] / 2
    screen_y = (y_rot2 - cy) / ry * SIZE[1] + SIZE[1] / 2

    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]),
                             range=[[0, SIZE[1]], [0, SIZE[0]]])

    density_buffer = density_buffer * 0.85 + H

    py5.load_np_pixels()

    # Palette: Deep Indigo -> Electric Violet -> Neon White
    density_norm = np.clip(density_buffer / 10.0, 0, 1)

    r_col =  8 * (density_norm ** 1.5)
    g_col =  4 * (density_norm ** 1.5)
    b_col = 20 * (density_norm ** 1.5)

    # Violet midtones
    mid = (density_norm > 0.25) & (density_norm < 0.7)
    t_mid = (density_norm[mid] - 0.25) / 0.45
    r_col[mid] = np.maximum(r_col[mid],   8 + 167 * t_mid)
    g_col[mid] = np.maximum(g_col[mid],   4 +  26 * t_mid)
    b_col[mid] = np.maximum(b_col[mid],  20 + 215 * t_mid)

    # Neon White highlights
    hi = density_norm > 0.7
    t_hi = (density_norm[hi] - 0.7) / 0.3
    r_col[hi] = np.maximum(r_col[hi], 175 +  80 * t_hi)
    g_col[hi] = np.maximum(g_col[hi],  30 + 220 * t_hi)
    b_col[hi] = np.maximum(b_col[hi], 235 +  20 * t_hi)

    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = np.clip(r_col, 0, 255).astype(np.uint8)
    py5.np_pixels[:, :, 2] = np.clip(g_col, 0, 255).astype(np.uint8)
    py5.np_pixels[:, :, 3] = np.clip(b_col, 0, 255).astype(np.uint8)

    py5.update_np_pixels()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 10 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen at frame {py5.frame_count}. Aborting.", flush=True)
            import os; os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} "
              f"({py5.frame_count / TOTAL_FRAMES * 100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames...", flush=True)
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid_frame = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid_frame, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Frames removed.")

        import os; os._exit(0)


py5.run_sketch()
