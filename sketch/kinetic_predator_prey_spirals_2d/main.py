"""
kinetic_predator_prey_spirals_2d
A 4K kinetic visualization of Lotka-Volterra predator-prey dynamics on a spatial 
grid, producing emergent spiral waves and oscillating biological fronts.
"""
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# --- Simulation Parameters ---
GRID_W = 480
GRID_H = 270

DT = 0.015
STEPS_PER_FRAME = 4

# Model parameters
R_prey = 0.82       # prey growth rate
K = 1.0            # prey carrying capacity
ALPHA = 0.85       # predation efficiency
BETA = 0.55        # predator biomass conversion
M = 0.42           # predator mortality

DP = 0.05          # prey diffusion coefficient
DQ = 0.02          # predator diffusion coefficient

# Arrays: prey (P) and predator (Q)
P = np.random.uniform(0.3, 0.7, (GRID_H, GRID_W)).astype(np.float32)
Q = np.zeros((GRID_H, GRID_W), dtype=np.float32)


def laplacian(f):
    # Fast 5-point stencil Laplacian using numpy roll
    return (np.roll(f, 1, axis=0) + np.roll(f, -1, axis=0) +
            np.roll(f, 1, axis=1) + np.roll(f, -1, axis=1) - 4.0 * f)


def setup():
    global Q
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize predator pockets in specific regions to seed beautiful spiral waves
    cx, cy = GRID_W // 2, GRID_H // 2
    y_indices, x_indices = np.ogrid[:GRID_H, :GRID_W]
    
    # Center circle
    mask = (x_indices - cx) ** 2 + (y_indices - cy) ** 2 <= (GRID_H // 6) ** 2
    Q[mask] = np.random.uniform(0.2, 0.5, mask.sum()).astype(np.float32)
    
    # Two offset boxes to break symmetry
    Q[cy-30:cy-10, cx-80:cx-60] = 0.4
    Q[cy+10:cy+30, cx+60:cx+80] = 0.4
    
    print("[Setup] Predator-prey Lotka-Volterra grid initialized.")


def step_simulation():
    global P, Q
    for _ in range(STEPS_PER_FRAME):
        lap_p = laplacian(P)
        lap_q = laplacian(Q)
        
        # Differential equations
        dp_dt = DP * lap_p + R_prey * P * (1.0 - P / K) - ALPHA * P * Q
        dq_dt = DQ * lap_q + BETA * ALPHA * P * Q - M * Q
        
        P = np.clip(P + DT * dp_dt, 0.0, K)
        Q = np.clip(Q + DT * dq_dt, 0.0, 2.0)


def colorize(p_grid, q_grid):
    # Vectorized color mapping for bioluminescent populations
    # Background: dark obsidian void (6, 8, 20)
    r = np.zeros_like(p_grid)
    g = np.zeros_like(p_grid)
    b = np.zeros_like(p_grid)
    
    # Prey: glowing mint/emerald green (mapped to G and B channels)
    # Predator: glowing coral/magenta (mapped to R and B channels)
    # Mixed: overlaps produce glowing white/pastel highlights
    
    bg_r, bg_g, bg_b = 6, 8, 20
    
    # Scale density bounds to 0-1
    pn = np.clip(p_grid / K, 0.0, 1.0)
    qn = np.clip(q_grid / 1.5, 0.0, 1.0)
    
    # Custom vector blend mapping
    r = bg_r + (pn * 28 + qn * 230)
    g = bg_g + (pn * 210 + qn * 45)
    b = bg_b + (pn * 92 + qn * 200)
    
    # Add neon highlight where they strongly interact
    overlap = pn * qn
    r += overlap * 45
    g += overlap * 45
    b += overlap * 45
    
    return np.clip(r, 0, 255).astype(np.uint8), np.clip(g, 0, 255).astype(np.uint8), np.clip(b, 0, 255).astype(np.uint8)


def draw():
    W, H = SIZE
    frame = py5.frame_count
    t = frame / FPS
    
    step_simulation()
    
    # Colorize populations
    r_grid, g_grid, b_grid = colorize(P, Q)
    
    # Upscale 480x270 directly to 3840x2160 (exact 8x repeat factor)
    sx = W // GRID_W
    sy = H // GRID_H
    
    r_up = np.repeat(np.repeat(r_grid, sy, axis=0), sx, axis=1)[:H, :W]
    g_up = np.repeat(np.repeat(g_grid, sy, axis=0), sx, axis=1)[:H, :W]
    b_up = np.repeat(np.repeat(b_grid, sy, axis=0), sx, axis=1)[:H, :W]
    
    # Direct memory write to py5 pixels
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

    # HUD telemetry
    py5.fill(160, 30, 90, 140)
    py5.text_size(20)
    py5.text(f"t={t:.2f}s  prey_max: {P.max():.2f}  predator_max: {Q.max():.2f}  grid: {GRID_W}x{GRID_H}", 50, H - 50)

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
