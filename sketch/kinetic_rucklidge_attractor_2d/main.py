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

# Rucklidge Attractor
# dx/dt = -k*x + lam*y - y*z
# dy/dt = x
# dz/dt = -z + y^2
# Chaotic params: k=2, lam=6.7  -> asymmetric butterfly strange attractor
N = 1000000
rng = np.random.default_rng()
x = rng.uniform(-5, 5, N).astype(np.float32)
y = rng.uniform(-5, 5, N).astype(np.float32)
z = rng.uniform(0, 30, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)


def step_rucklidge(lam, dt=0.02):
    global x, y, z

    k = 2.0

    dx = -k * x + lam * y - y * z
    dy = x
    dz = -z + y**2

    x_new = x + dx * dt
    y_new = y + dy * dt
    z_new = z + dz * dt

    mask = (np.abs(x_new) > 200) | (np.abs(y_new) > 200) | (np.abs(z_new) > 200) | np.isnan(x_new)
    n_reset = int(np.sum(mask))
    if n_reset > 0:
        x_new[mask] = rng.uniform(-5, 5, n_reset).astype(np.float32)
        y_new[mask] = rng.uniform(-5, 5, n_reset).astype(np.float32)
        z_new[mask] = rng.uniform(0, 30, n_reset).astype(np.float32)

    x[:] = x_new
    y[:] = y_new
    z[:] = z_new


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    print("[Setup] Warming up...", flush=True)
    for _ in range(3000):
        step_rucklidge(6.7, dt=0.02)
    print("[Setup] Done.", flush=True)


def draw():
    global density_buffer

    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES

    lam = 6.7 + 0.3 * np.sin(t)

    for _ in range(4):
        step_rucklidge(lam, dt=0.02)

    # Gentle rotation
    theta = t * 0.4
    phi = np.sin(t * 1.5) * 0.5

    x_rot1 = x * np.cos(theta) - y * np.sin(theta)
    y_rot1 = x * np.sin(theta) + y * np.cos(theta)

    x_rot2 = x_rot1
    y_rot2 = y_rot1 * np.cos(phi) - z * np.sin(phi)

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

    # Palette: Obsidian -> Emerald Glow -> Arctic White
    density_norm = np.clip(density_buffer / 8.0, 0, 1)

    r_col =  5 * (density_norm ** 1.5)
    g_col = 12 * (density_norm ** 1.5)
    b_col = 10 * (density_norm ** 1.5)

    mid = (density_norm > 0.25) & (density_norm < 0.7)
    t_mid = (density_norm[mid] - 0.25) / 0.45
    r_col[mid] = np.maximum(r_col[mid],   5 +  45 * t_mid)
    g_col[mid] = np.maximum(g_col[mid],  12 + 203 * t_mid)
    b_col[mid] = np.maximum(b_col[mid],  10 +  55 * t_mid)

    hi = density_norm > 0.7
    t_hi = (density_norm[hi] - 0.7) / 0.3
    r_col[hi] = np.maximum(r_col[hi],  50 + 205 * t_hi)
    g_col[hi] = np.maximum(g_col[hi], 215 +  40 * t_hi)
    b_col[hi] = np.maximum(b_col[hi],  65 + 190 * t_hi)

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
