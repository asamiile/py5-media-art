"""
kinetic_ifs_fractal_flame_2d
A 4K kinetic visualization of an Iterated Function System (IFS) fractal flame
morphing its affine transformations over time, rendered via vectorized chaos 
game orbits and log-density accumulation.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import math
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
SIZE = OUTPUT_SIZE

# --- Simulation Parameters ---
GRID_W = 480
GRID_H = 270
N_PARTICLES = 120_000
STEPS_PER_FRAME = 12

# View bounds: (xmin, xmax, ymin, ymax)
BOUNDS = (-0.35, 1.35, -0.65, 0.65)

# Pre-allocate particle positions and density grid
pts = np.random.uniform(0, 1, (N_PARTICLES, 2)).astype(np.float32)
hist = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Probabilities for the 5 crystal transformations
probs = np.array([0.20, 0.20, 0.20, 0.20, 0.20], dtype=np.float32)
cum_probs = np.cumsum(probs)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    print("[Setup] Optimized IFS Fractal Flame initialized.")


def get_transforms(t):
    # Dynamic morphing of the crystal fractal transformations using time t
    s = math.sin(t * 0.2) * 0.04
    c = math.cos(t * 0.2) * 0.02
    
    # 5 transforms: a, b, c, d, e, f
    return [
        (0.382 + s, 0.00, 0.00, 0.382 + s, 0.00, 0.00),
        (0.382, 0.00, 0.00, 0.382, 0.618 + c, 0.00),
        (0.191 + s, -0.330 - c, 0.330 + c, 0.191 + s, 0.309, 0.535),
        (0.191 - s, 0.330 + c, -0.330 - c, 0.191 - s, 0.309, -0.535),
        (-0.382 + c, 0.00, 0.00, 0.382 - c, 1.00 + s, 0.00),
    ]


def step_simulation(t):
    global pts, hist
    transforms = get_transforms(t)
    n_tf = len(transforms)

    # Reset frame history to keep it dynamic and breathing (decay)
    hist *= 0.85

    for _ in range(STEPS_PER_FRAME):
        # Vectorized choice of transformation for each particle
        r_vals = np.random.random(N_PARTICLES).astype(np.float32)
        idx = np.searchsorted(cum_probs, r_vals)
        idx = np.clip(idx, 0, n_tf - 1)

        new_pts = np.empty_like(pts)
        for ti, (a, b, c_coeff, d, e, f) in enumerate(transforms):
            mask = idx == ti
            if not mask.any():
                continue
            x, y = pts[mask, 0], pts[mask, 1]
            new_pts[mask, 0] = a * x + b * y + e
            new_pts[mask, 1] = c_coeff * x + d * y + f
        pts = new_pts

    # Accumulate coordinates to density grid
    xmin, xmax, ymin, ymax = BOUNDS
    xi = (((pts[:, 0] - xmin) / (xmax - xmin)) * GRID_W).astype(np.int32)
    yi = (((pts[:, 1] - ymin) / (ymax - ymin)) * GRID_H).astype(np.int32)
    valid = (xi >= 0) & (xi < GRID_W) & (yi >= 0) & (yi < GRID_H)
    
    np.add.at(hist, (GRID_H - 1 - yi[valid], xi[valid]), 1.0)


def colorize(log_t):
    # Purple to cyan/white
    r = np.zeros_like(log_t)
    g = np.zeros_like(log_t)
    b = np.zeros_like(log_t)
    
    # Background color for 0 density
    bg_r, bg_g, bg_b = 6, 8, 20
    
    # Level 1: 0.0 -> 0.35 (dark blue to bright purple)
    m1 = log_t <= 0.35
    t1 = log_t / 0.35
    r[m1] = bg_r + t1[m1] * 144
    g[m1] = bg_g + t1[m1] * 24
    b[m1] = bg_b + t1[m1] * 220
    
    # Level 2: 0.35 -> 0.75 (purple to cyan)
    m2 = (log_t > 0.35) & (log_t <= 0.75)
    t2 = (log_t - 0.35) / 0.40
    r[m2] = 150 - t2[m2] * 150
    g[m2] = 32 + t2[m2] * 208
    b[m2] = 240 + t2[m2] * 15
    
    # Level 3: 0.75 -> 1.0 (cyan to white)
    m3 = log_t > 0.75
    t3 = (log_t - 0.75) / 0.25
    r[m3] = t3[m3] * 255
    g[m3] = 240 + t3[m3] * 15
    b[m3] = 255
    
    return r.astype(np.uint8), g.astype(np.uint8), b.astype(np.uint8)


def draw():
    global hist
    W, H = SIZE
    frame = py5.frame_count
    t = frame / FPS
    
    step_simulation(t)
    
    # --- Rendering Density Grid ---
    # Log-scaling
    max_h = hist.max()
    if max_h > 0:
        log_t = np.log1p(hist) / np.log1p(max_h)
    else:
        log_t = np.zeros_like(hist)
        
    r_grid, g_grid, b_grid = colorize(log_t)
    
    # Upscale using np.repeat
    scale_x = W / GRID_W
    scale_y = H / GRID_H
    sx = int(round(scale_x))
    sy = int(round(scale_y))
    
    r_up = np.repeat(np.repeat(r_grid, sy, axis=0), sx, axis=1)[:H, :W]
    g_up = np.repeat(np.repeat(g_grid, sy, axis=0), sx, axis=1)[:H, :W]
    b_up = np.repeat(np.repeat(b_grid, sy, axis=0), sx, axis=1)[:H, :W]
    
    # Direct blit to screen pixels
    py5.load_np_pixels()
    py5.np_pixels[:, :, 0] = 255      # alpha
    py5.np_pixels[:, :, 1] = r_up     # R
    py5.np_pixels[:, :, 2] = g_up     # G
    py5.np_pixels[:, :, 3] = b_up     # B
    py5.update_np_pixels()

    # Vignette shadow
    for i in range(16):
        alpha = int(4 + i * 5)
        m = i * 22
        py5.fill(240, 40, 3, alpha)
        py5.rect(0, 0, W, m)
        py5.rect(0, H - m, W, m)
        py5.rect(0, 0, m, H)
        py5.rect(W - m, 0, m, H)

    # HUD readout (Using solid vector text overlay)
    py5.fill(185, 40, 95, 140)
    py5.text_size(20)
    py5.text(f"t={t:.2f}s  particles: {N_PARTICLES}  steps/frame: {STEPS_PER_FRAME}  grid: {GRID_W}x{GRID_H}", 50, H - 50)

    # Blank screen check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {frame}. Aborting.")
            import os
            os._exit(1)

    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")

    if frame == TOTAL_FRAMES // 2:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
        print(f"[Preview] Saved {PREVIEW_FILENAME}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] frames removed.")
        import os
        os._exit(0)


py5.run_sketch()
