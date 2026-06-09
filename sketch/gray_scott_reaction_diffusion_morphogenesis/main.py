from pathlib import Path
import shutil
import sys
import subprocess
import numpy as np
import py5
from scipy.ndimage import convolve

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 25
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Simulation grid (smaller for performance; will be upscaled to canvas)
GRID_W = 960
GRID_H = 540

# Gray-Scott parameters — "coral growth" / "moving spots" regime
# See Pearson (1993) parameter map; this produces branching coral-like growth
FEED = 0.055
KILL = 0.062
DU = 0.21   # diffusion rate of U
DV = 0.105  # diffusion rate of V (half of DU is a common ratio)
DT = 1.0    # integration time step
STEPS_PER_FRAME = 20  # integration steps per rendered frame

# 5-point Laplacian stencil (symmetric, isotropic approximation)
LAPLACIAN_KERNEL = np.array([
    [0.05, 0.20, 0.05],
    [0.20, -1.0, 0.20],
    [0.05, 0.20, 0.05],
])

U = None
V = None
pixel_buf = None


def laplacian(grid):
    return convolve(grid, LAPLACIAN_KERNEL, mode='wrap')


def gs_step(u, v):
    """Single Gray-Scott integration step."""
    lap_u = laplacian(u)
    lap_v = laplacian(v)
    uvv = u * v * v
    du = DU * lap_u - uvv + FEED * (1.0 - u)
    dv = DV * lap_v + uvv - (FEED + KILL) * v
    np.add(u, du * DT, out=u)
    np.add(v, dv * DT, out=v)
    np.clip(u, 0.0, 1.0, out=u)
    np.clip(v, 0.0, 1.0, out=v)


def concentration_to_rgb(c):
    """
    Map Gray-Scott U concentration to warm earth-tone palette.
    U typically spans ~0.25–1.0; contrast-stretch to use full palette range.
    High U (background) → deep soil near-black; low U (reaction front) → ivory/amber.
    """
    # Contrast-stretch: map observed [0.25, 1.0] range to full [0, 1] palette
    stretched = np.clip((c - 0.25) / 0.75, 0.0, 1.0)
    # Invert so reaction fronts (low U, low stretched) are bright
    t = 1.0 - stretched

    r = np.zeros_like(t)
    g = np.zeros_like(t)
    b = np.zeros_like(t)

    # 0.0–0.25: very dark to dark rust
    m = t < 0.25
    s = t[m] / 0.25
    r[m] = 10 + s * 60
    g[m] = 8 + s * 25
    b[m] = 6 + s * 12

    # 0.25–0.55: rust → deep amber
    m = (t >= 0.25) & (t < 0.55)
    s = (t[m] - 0.25) / 0.30
    r[m] = 70 + s * 110
    g[m] = 33 + s * 60
    b[m] = 18 + s * 15

    # 0.55–0.80: amber → warm ochre-gold
    m = (t >= 0.55) & (t < 0.80)
    s = (t[m] - 0.55) / 0.25
    r[m] = 180 + s * 60
    g[m] = 93 + s * 90
    b[m] = 33 + s * 30

    # 0.80–1.00: ochre-gold → bleached ivory
    m = t >= 0.80
    s = (t[m] - 0.80) / 0.20
    r[m] = 240 + s * 15
    g[m] = 183 + s * 50
    b[m] = 63 + s * 80

    return (
        np.clip(r, 0, 255).astype(np.uint8),
        np.clip(g, 0, 255).astype(np.uint8),
        np.clip(b, 0, 255).astype(np.uint8),
    )


def setup():
    global U, V, pixel_buf
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    rng = np.random.default_rng()

    # Initialize U≈1 everywhere, V with small global noise so patterns
    # emerge uniformly across the full canvas (avoids large uncovered patches)
    U = np.ones((GRID_H, GRID_W), dtype=np.float32) - rng.random((GRID_H, GRID_W), dtype=np.float32) * 0.02
    V = rng.random((GRID_H, GRID_W), dtype=np.float32) * 0.01

    # Superimpose larger seeds to kick-start multiple region nucleations
    n_seeds = 80
    for _ in range(n_seeds):
        cx = rng.integers(5, GRID_W - 5)
        cy = rng.integers(5, GRID_H - 5)
        r = rng.integers(4, 10)
        yy, xx = np.ogrid[-r:r+1, -r:r+1]
        mask = xx*xx + yy*yy <= r*r
        y0, y1 = max(0, cy - r), min(GRID_H, cy + r + 1)
        x0, x1 = max(0, cx - r), min(GRID_W, cx + r + 1)
        U[y0:y1, x0:x1][mask[:y1-y0, :x1-x0]] = 0.50
        V[y0:y1, x0:x1][mask[:y1-y0, :x1-x0]] = 0.25

    # Run warmup iterations to let patterns emerge
    print("[Setup] Running Gray-Scott warmup (800 steps)...")
    for _ in range(800):
        gs_step(U, V)
    print("[Setup] Warmup complete.")

    H, W = SIZE[1], SIZE[0]
    pixel_buf = np.zeros((H, W, 4), dtype=np.uint8)
    pixel_buf[:, :, 0] = 255


def draw():
    global U, V, pixel_buf

    H, W = SIZE[1], SIZE[0]

    # Advance simulation
    for _ in range(STEPS_PER_FRAME):
        gs_step(U, V)

    # Map U concentration to warm earth colors
    r_sm, g_sm, b_sm = concentration_to_rgb(U)

    # Upscale from GRID to full canvas using numpy repeat (nearest-neighbor, fast)
    scale_y = H // GRID_H
    scale_x = W // GRID_W
    r_full = np.repeat(np.repeat(r_sm, scale_y, axis=0), scale_x, axis=1)
    g_full = np.repeat(np.repeat(g_sm, scale_y, axis=0), scale_x, axis=1)
    b_full = np.repeat(np.repeat(b_sm, scale_y, axis=0), scale_x, axis=1)

    # Crop/pad to exact SIZE if needed
    r_full = r_full[:H, :W]
    g_full = g_full[:H, :W]
    b_full = b_full[:H, :W]

    pixel_buf[:, :, 0] = 255
    pixel_buf[:, :, 1] = r_full
    pixel_buf[:, :, 2] = g_full
    pixel_buf[:, :, 3] = b_full

    py5.load_np_pixels()
    py5.np_pixels[:] = pixel_buf
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
