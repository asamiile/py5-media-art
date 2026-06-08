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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Lorenz system constants
SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0
DT = 0.005
N_PARTICLES = 4000
STEPS_PER_FRAME = 3

# Dark navy background
BG_R, BG_G, BG_B = 3, 3, 12

positions = None
pixel_buf = None  # (H, W, 4) ARGB uint8


def lorenz_step(pos):
    """Vectorized Lorenz Euler step; returns velocity magnitude for each particle."""
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    dx = SIGMA * (y - x)
    dy = x * (RHO - z) - y
    dz = x * y - BETA * z
    pos[:, 0] += dx * DT
    pos[:, 1] += dy * DT
    pos[:, 2] += dz * DT
    return np.sqrt(dx * dx + dy * dy + dz * dz)


def vel_to_rgb(vn):
    """
    Thermal gradient: navy (slow) → cobalt → cyan → hot-white → amber (fast).
    vn: normalized velocity in [0, 1].
    """
    r = np.zeros(len(vn), dtype=np.float32)
    g = np.zeros(len(vn), dtype=np.float32)
    b = np.zeros(len(vn), dtype=np.float32)

    # 0.0–0.3: deep navy → cobalt blue
    m = (vn >= 0.0) & (vn < 0.3)
    t = vn[m] / 0.3
    r[m] = t * 25
    g[m] = t * 40
    b[m] = 100 + t * 155

    # 0.3–0.6: cobalt blue → electric cyan
    m = (vn >= 0.3) & (vn < 0.6)
    t = (vn[m] - 0.3) / 0.3
    r[m] = 25 + t * 10
    g[m] = 40 + t * 200
    b[m] = 255

    # 0.6–0.8: cyan → hot white
    m = (vn >= 0.6) & (vn < 0.8)
    t = (vn[m] - 0.6) / 0.2
    r[m] = 35 + t * 220
    g[m] = 240 + t * 15
    b[m] = 255

    # 0.8–1.0: hot white → amber-orange
    m = vn >= 0.8
    t = (vn[m] - 0.8) / 0.2
    r[m] = 255
    g[m] = 255 - t * 130
    b[m] = 255 - t * 255

    return r, g, b


def setup():
    global positions, pixel_buf
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    rng = np.random.default_rng()
    positions = np.zeros((N_PARTICLES, 3), dtype=np.float64)
    # Start near classic (0.1, 0, 0) with tiny perturbations
    positions[:, 0] = 0.1 + rng.normal(0, 0.05, N_PARTICLES)
    positions[:, 1] = rng.normal(0, 0.05, N_PARTICLES)
    positions[:, 2] = rng.normal(0, 0.05, N_PARTICLES)

    print("[Setup] Warming up Lorenz attractor (4000 steps)...")
    for _ in range(4000):
        lorenz_step(positions)
    print("[Setup] Warmup complete — particles distributed across attractor.")

    H, W = SIZE[1], SIZE[0]
    pixel_buf = np.zeros((H, W, 4), dtype=np.uint8)
    pixel_buf[:, :, 0] = 255   # Alpha channel (ARGB)
    pixel_buf[:, :, 1] = BG_R
    pixel_buf[:, :, 2] = BG_G
    pixel_buf[:, :, 3] = BG_B


def draw():
    global positions, pixel_buf

    t = py5.frame_count / FPS
    H, W = SIZE[1], SIZE[0]

    # --- Trail fade: decay toward background minimum ---
    r_ch = pixel_buf[:, :, 1].astype(np.int32)
    g_ch = pixel_buf[:, :, 2].astype(np.int32)
    b_ch = pixel_buf[:, :, 3].astype(np.int32)

    r_ch = np.maximum(r_ch * 97 // 100, BG_R)
    g_ch = np.maximum(g_ch * 97 // 100, BG_G)
    b_ch = np.maximum(b_ch * 97 // 100, BG_B)

    pixel_buf[:, :, 1] = r_ch.astype(np.uint8)
    pixel_buf[:, :, 2] = g_ch.astype(np.uint8)
    pixel_buf[:, :, 3] = b_ch.astype(np.uint8)

    # --- Advance Lorenz particles ---
    vel_mag = np.zeros(N_PARTICLES)
    for _ in range(STEPS_PER_FRAME):
        vel_mag = lorenz_step(positions)

    # --- 3D rotation → 2D projection ---
    # Slow Y rotation + gentle X tilt wobble
    angle_y = t * 0.22 + 0.3
    angle_x = 0.42 + np.sin(t * 0.09) * 0.14

    cy, sy = np.cos(angle_y), np.sin(angle_y)
    cx, sx = np.cos(angle_x), np.sin(angle_x)

    # Lorenz attractor centers around z≈25; center it
    px = positions[:, 0]
    py_p = positions[:, 1]
    pz = positions[:, 2] - 25.0

    # Rotate Y, then X
    rx = px * cy + pz * sy
    rz = -px * sy + pz * cy
    ry = py_p * cx - rz * sx

    scale = H / 62.0
    screen_x = (rx * scale + W / 2).astype(np.int32)
    screen_y = (-ry * scale + H / 2).astype(np.int32)

    # --- Velocity coloring ---
    vn = np.clip(vel_mag / 68.0, 0.0, 1.0)
    r_vals, g_vals, b_vals = vel_to_rgb(vn)

    # Brighter for faster particles; minimum glow even for slow
    brightness = (55 + vn * 130).astype(np.float32)

    r_add = np.clip((r_vals * brightness / 210.0).astype(np.int32), 0, 255)
    g_add = np.clip((g_vals * brightness / 210.0).astype(np.int32), 0, 255)
    b_add = np.clip((b_vals * brightness / 210.0).astype(np.int32), 0, 255)

    # --- Draw particles into pixel buffer (additive) ---
    valid = (screen_x >= 0) & (screen_x < W) & (screen_y >= 0) & (screen_y < H)
    sy_v = screen_y[valid]
    sx_v = screen_x[valid]

    r_buf = pixel_buf[:, :, 1].astype(np.int32)
    g_buf = pixel_buf[:, :, 2].astype(np.int32)
    b_buf = pixel_buf[:, :, 3].astype(np.int32)

    np.add.at(r_buf, (sy_v, sx_v), r_add[valid])
    np.add.at(g_buf, (sy_v, sx_v), g_add[valid])
    np.add.at(b_buf, (sy_v, sx_v), b_add[valid])

    # Also paint a 1-pixel cross around each particle for anti-aliased feel
    for ddx, ddy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        sx_n = np.clip(sx_v + ddx, 0, W - 1)
        sy_n = np.clip(sy_v + ddy, 0, H - 1)
        np.add.at(r_buf, (sy_n, sx_n), r_add[valid] // 3)
        np.add.at(g_buf, (sy_n, sx_n), g_add[valid] // 3)
        np.add.at(b_buf, (sy_n, sx_n), b_add[valid] // 3)

    pixel_buf[:, :, 1] = np.clip(r_buf, 0, 255).astype(np.uint8)
    pixel_buf[:, :, 2] = np.clip(g_buf, 0, 255).astype(np.uint8)
    pixel_buf[:, :, 3] = np.clip(b_buf, 0, 255).astype(np.uint8)
    pixel_buf[:, :, 0] = 255

    # --- Push to py5 display ---
    py5.load_np_pixels()
    py5.np_pixels[:] = pixel_buf
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # --- Blank-screen guard ---
    if py5.frame_count == 30 or py5.frame_count % 120 == 0:
        if pixel_buf[:, :, 1:].std() < 2.0:
            print(f"[Error] Blank screen on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} "
              f"({py5.frame_count / TOTAL_FRAMES * 100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Encoding {TOTAL_FRAMES} frames → {WORK_NAME}.mp4 ...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid_frame = TOTAL_FRAMES // 2
        shutil.copyfile(
            FRAMES_DIR / f"frame-{mid_frame:04d}.png",
            SKETCH_DIR / PREVIEW_FILENAME,
        )

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Frames directory removed.")

        import os
        os._exit(0)


py5.run_sketch()
