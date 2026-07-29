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

# Lorenz Mod 2 Attractor
# dx/dt = -a*x + y^2 - z^2 + a*f
# dy/dt = x*(y - b*z) + g
# dz/dt = -z + x*(b*y + z)
# Chaotic params: a=0.9, b=5, f=9.9, g=1
N = 1000000
rng = np.random.default_rng()
x = rng.uniform(-5, 5, N).astype(np.float32)
y = rng.uniform(-5, 5, N).astype(np.float32)
z = rng.uniform(-5, 5, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)


def step_lorenz_mod2(f_val, dt=0.01):
    global x, y, z

    a = 0.9
    b = 5.0
    g = 1.0

    dx = -a * x + y**2 - z**2 + a * f_val
    dy = x * (y - b * z) + g
    dz = -z + x * (b * y + z)

    x_new = x + dx * dt
    y_new = y + dy * dt
    z_new = z + dz * dt

    mask = (np.abs(x_new) > 200) | (np.abs(y_new) > 200) | (np.abs(z_new) > 200) | np.isnan(x_new)
    n_reset = int(np.sum(mask))
    if n_reset > 0:
        x_new[mask] = rng.uniform(-5, 5, n_reset).astype(np.float32)
        y_new[mask] = rng.uniform(-5, 5, n_reset).astype(np.float32)
        z_new[mask] = rng.uniform(-5, 5, n_reset).astype(np.float32)

    x[:] = x_new
    y[:] = y_new
    z[:] = z_new


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    # Warm-up: drive particles onto the attractor
    print("[Setup] Warming up...", flush=True)
    for _ in range(3000):
        step_lorenz_mod2(9.9, dt=0.01)
    print("[Setup] Done.", flush=True)


def draw():
    global density_buffer

    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES

    # Modulate f parameter
    f_val = 9.9 + 0.8 * np.sin(t)

    for _ in range(3):
        step_lorenz_mod2(f_val, dt=0.01)

    # Gentle rotation
    theta = t * 0.4
    phi = np.sin(t * 1.5) * 0.4

    x_rot1 = x * np.cos(theta) - y * np.sin(theta)
    y_rot1 = x * np.sin(theta) + y * np.cos(theta)
    z_rot1 = z

    x_rot2 = x_rot1
    y_rot2 = y_rot1 * np.cos(phi) - z_rot1 * np.sin(phi)

    # Adaptive scale
    x_c = float(np.median(x_rot2))
    y_c = float(np.median(y_rot2))
    x_r = max(4.0 * float(np.std(x_rot2)), 1.0)
    y_r = max(4.0 * float(np.std(y_rot2)), 1.0)

    screen_x = (x_rot2 - x_c) / x_r * SIZE[0] + SIZE[0] / 2
    screen_y = (y_rot2 - y_c) / y_r * SIZE[1] + SIZE[1] / 2

    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]),
                             range=[[0, SIZE[1]], [0, SIZE[0]]])

    density_buffer = density_buffer * 0.85 + H

    py5.load_np_pixels()

    # Palette: Midnight Navy → Electric Indigo → Pale Ice
    density_norm = np.clip(density_buffer / 12.0, 0, 1)

    r_col = 10 * (density_norm ** 1.5)
    g_col =  5 * (density_norm ** 1.5)
    b_col = 50 * (density_norm ** 1.5)

    # Electric Indigo midtones
    mid = (density_norm > 0.3) & (density_norm < 0.7)
    t_mid = (density_norm[mid] - 0.3) / 0.4
    r_col[mid] = np.maximum(r_col[mid],  10 + 100 * t_mid)
    g_col[mid] = np.maximum(g_col[mid],   5 +  30 * t_mid)
    b_col[mid] = np.maximum(b_col[mid],  50 + 185 * t_mid)

    # Pale Ice highlights
    hi = density_norm > 0.7
    t_hi = (density_norm[hi] - 0.7) / 0.3
    r_col[hi] = np.maximum(r_col[hi], 110 + 145 * t_hi)
    g_col[hi] = np.maximum(g_col[hi],  35 + 195 * t_hi)
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

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...", flush=True)
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
