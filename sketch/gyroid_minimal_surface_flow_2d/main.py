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
SIZE = OUTPUT_SIZE  # 3840 × 2160

W, H = SIZE

# Evaluation grid (upscaled 4× to canvas)
GRID_W, GRID_H = 960, 540

# How many full TPMS periods to tile across the canvas
TILES_X = 5   # 5 periods horizontally
TILES_Y = 2   # 2.5 periods vertically (keeps ~2:1 aspect)

pixel_buf = None


# ---------------------------------------------------------------------------
# Triply periodic minimal surface formulas
# All map (x, y, z) -> scalar field; isosurface at f=0 is the minimal surface
# ---------------------------------------------------------------------------

def gyroid(x, y, z):
    return np.sin(x) * np.cos(y) + np.sin(y) * np.cos(z) + np.sin(z) * np.cos(x)


def schwarz_d(x, y, z):
    return (np.cos(x) * np.cos(y) * np.cos(z)
            - np.sin(x) * np.sin(y) * np.sin(z))


def schwarz_p(x, y, z):
    return np.cos(x) + np.cos(y) + np.cos(z)


def neovius(x, y, z):
    return (3 * (np.cos(x) + np.cos(y) + np.cos(z))
            + 4 * np.cos(x) * np.cos(y) * np.cos(z))


SURFACES = [gyroid, schwarz_d, schwarz_p, neovius]
N_SURFACES = len(SURFACES)


# ---------------------------------------------------------------------------
# Colour mapping
# ---------------------------------------------------------------------------

def field_to_rgb(f, t):
    """
    Map TPMS scalar field to a dark, glowing image.

    f   : (GRID_H, GRID_W) float32 array
    t   : global time in [0, 1]
    Returns: r, g, b each uint8 (GRID_H, GRID_W)
    """
    # Primary glow: bright ridge at the isosurface (f ≈ 0)
    glow_main = np.exp(-np.abs(f) * 3.5)

    # Secondary glow: fainter ridges at ±1.8 (secondary contours)
    glow_sec_pos = np.exp(-np.abs(f - 1.8) * 5.0) * 0.35
    glow_sec_neg = np.exp(-np.abs(f + 1.8) * 5.0) * 0.35
    glow_sec = glow_sec_pos + glow_sec_neg

    # Slowly cycling glow hue (primary)
    h = t * 2.0 * np.pi
    pr = 30  + 170 * (0.5 + 0.5 * np.sin(h))           # 30–200
    pg = 185 + 70  * (0.5 + 0.5 * np.sin(h + 2.094))   # 185–255  (120° offset)
    pb = 230 + 25  * (0.5 + 0.5 * np.sin(h + 4.189))   # 230–255  (240° offset)

    # Warm accent for secondary contours (complementary hue)
    sr = 220 + 35  * (0.5 + 0.5 * np.sin(h + 3.14))
    sg = 80  + 50  * (0.5 + 0.5 * np.sin(h + 5.24))
    sb = 20  + 30  * (0.5 + 0.5 * np.sin(h + 1.05))

    # Very dark background tinted by sign of f
    sign_bias = np.where(f >= 0, 1.0, 0.0)
    bg_r = 4 + 4 * sign_bias    # 4 or 8
    bg_g = 4 + 2 * sign_bias    # 4 or 6
    bg_b = 8 + 4 * sign_bias    # 8 or 12

    r = np.clip(bg_r + pr * glow_main + sr * glow_sec, 0, 255).astype(np.uint8)
    g = np.clip(bg_g + pg * glow_main + sg * glow_sec, 0, 255).astype(np.uint8)
    b = np.clip(bg_b + pb * glow_main + sb * glow_sec, 0, 255).astype(np.uint8)

    return r, g, b


# ---------------------------------------------------------------------------
# Coordinate grids (built once)
# ---------------------------------------------------------------------------

_x_lin = np.linspace(0.0, 2.0 * np.pi * TILES_X, GRID_W, dtype=np.float32)
_y_lin = np.linspace(0.0, 2.0 * np.pi * TILES_Y, GRID_H, dtype=np.float32)
X_GRID, Y_GRID = np.meshgrid(_x_lin, _y_lin)


def setup():
    global pixel_buf
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    pixel_buf = np.zeros((H, W, 4), dtype=np.uint8)
    pixel_buf[:, :, 0] = 255  # alpha


def draw():
    global pixel_buf

    frame = py5.frame_count
    t = frame / TOTAL_FRAMES  # [0, 1]

    # Z sweeps 0 → 2π over the full animation
    z_phase = t * 2.0 * np.pi

    # Smooth blend between consecutive TPMS types
    # 4 surfaces → each gets 5 s at 20 s total (surface changes every ~5 s)
    blend_pos = t * N_SURFACES
    idx_a = int(blend_pos) % N_SURFACES
    idx_b = (idx_a + 1) % N_SURFACES
    alpha = blend_pos - int(blend_pos)   # 0 → 1 within this segment

    z_grid = np.full_like(X_GRID, z_phase)

    f_a = SURFACES[idx_a](X_GRID, Y_GRID, z_grid).astype(np.float32)
    f_b = SURFACES[idx_b](X_GRID, Y_GRID, z_grid).astype(np.float32)
    f = (1.0 - alpha) * f_a + alpha * f_b

    r_sm, g_sm, b_sm = field_to_rgb(f, t)

    # 4× nearest-neighbour upscale
    scale_y = H // GRID_H  # 4
    scale_x = W // GRID_W  # 4
    r_full = np.repeat(np.repeat(r_sm, scale_y, axis=0), scale_x, axis=1)[:H, :W]
    g_full = np.repeat(np.repeat(g_sm, scale_y, axis=0), scale_x, axis=1)[:H, :W]
    b_full = np.repeat(np.repeat(b_sm, scale_y, axis=0), scale_x, axis=1)[:H, :W]

    pixel_buf[:, :, 0] = 255
    pixel_buf[:, :, 1] = r_full
    pixel_buf[:, :, 2] = g_full
    pixel_buf[:, :, 3] = b_full

    py5.load_np_pixels()
    py5.np_pixels[:] = pixel_buf
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if frame == 30 or frame % 120 == 0:
        if pixel_buf[:, :, 1:].std() < 1.0:
            print(f"[Error] Blank screen on frame {frame}. Aborting.")
            import os
            os._exit(1)

    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} "
              f"({frame / TOTAL_FRAMES * 100:.1f}%)")

    if frame >= TOTAL_FRAMES:
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
