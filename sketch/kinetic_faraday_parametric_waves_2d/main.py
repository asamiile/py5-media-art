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

# --- Simulation Grid Size ---
GRID_W = 640
GRID_H = 360

# Wave simulation state arrays
u_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)      # current height u^n
u_prev = np.zeros((GRID_H, GRID_W), dtype=np.float32)      # previous height u^{n-1}

# --- Wave Simulation Parameters ---
DT = 0.1
GAMMA = 0.12     # Damping / viscosity
BETA = 1.8       # Nonlinear cubic saturation coefficient
C0_SQ = 1.2      # Base wave speed squared
FORCING_AMP = 0.90  # Parametric driving amplitude
OMEGA = 3.6      # Driving frequency

rng = np.random.default_rng(2026)


def get_laplacian(grid):
    # Periodic 5-point Laplacian stencil
    return (
        np.roll(grid, 1, axis=0) +
        np.roll(grid, -1, axis=0) +
        np.roll(grid, 1, axis=1) +
        np.roll(grid, -1, axis=1) -
        4.0 * grid
    )


def get_gradient(grid):
    # Central difference gradient
    gx = (np.roll(grid, -1, axis=1) - np.roll(grid, 1, axis=1)) / 2.0
    gy = (np.roll(grid, -1, axis=0) - np.roll(grid, 1, axis=0)) / 2.0
    return gx, gy


def step_simulation(t):
    global u_grid, u_prev
    
    # 1. Parametric wave speed: c^2(t) = c0^2 + A * cos(omega * t)
    c_sq = C0_SQ + FORCING_AMP * np.cos(OMEGA * t)
    
    # 2. Compute Laplacian of current field
    lu = get_laplacian(u_grid)
    
    # 3. Add tiny stochastic fluctuations (seed noise to trigger instability)
    noise = rng.uniform(-0.0006, 0.0006, (GRID_H, GRID_W)).astype(np.float32)
    
    # 4. Explicit FDTD update scheme:
    # u_next = (2*u - u_prev * (1 - gamma*dt/2) + dt^2 * (c_sq * lu - beta * u^3)) / (1 + gamma*dt/2)
    denom = 1.0 + (GAMMA * DT) / 2.0
    u_next = (
        2.0 * u_grid -
        u_prev * (1.0 - (GAMMA * DT) / 2.0) +
        (DT**2) * (c_sq * lu - BETA * (u_grid**3))
    ) / denom + noise
    
    # Update states
    u_prev = u_grid.copy()
    u_grid = np.clip(u_next, -1.8, 1.8)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    W, H = SIZE
    frame = py5.frame_count
    t = frame / FPS
    
    # Perform 4 simulation integration substeps per frame for smooth wave propagation
    for _ in range(4):
        step_simulation(t)
        
    # --- Shading and Rendering ---
    gx, gy = get_gradient(u_grid)
    
    # Scale gradients to control reflection highlight sharpness
    scale = 14.0
    gx_scaled = gx * scale
    gy_scaled = gy * scale
    
    # Compute normal components
    nz = 1.0 / np.sqrt(gx_scaled**2 + gy_scaled**2 + 1.0)
    nx = -gx_scaled * nz
    ny = -gy_scaled * nz
    
    # Light direction (pointing from top-left, slightly tilted forward)
    lx, ly, lz = 0.5, -0.5, 0.8
    l_len = np.sqrt(lx**2 + ly**2 + lz**2)
    lx /= l_len; ly /= l_len; lz /= l_len
    
    # Dot product (n . l) for diffuse lighting shading
    n_dot_l = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)
    
    # Specular reflection component: r_z = 2 * n_z * (n . l) - l_z
    rz = 2.0 * nz * n_dot_l - lz
    specular = np.clip(rz, 0.0, 1.0) ** 16.0
    
    # Color mapping arrays
    # Background: Obsidian Abyss (8, 6, 12)
    r_arr = np.full_like(u_grid, 8.0)
    g_arr = np.full_like(u_grid, 6.0)
    b_arr = np.full_like(u_grid, 12.0)
    
    # Troughs (u < 0): blend toward Deep Amethyst (100, 30, 220)
    trough_mask = u_grid < 0.0
    trough_factor = np.clip(-u_grid[trough_mask] / 1.0, 0.0, 1.0)
    r_arr[trough_mask] = r_arr[trough_mask] * (1.0 - trough_factor) + 100.0 * trough_factor
    g_arr[trough_mask] = g_arr[trough_mask] * (1.0 - trough_factor) + 30.0 * trough_factor
    b_arr[trough_mask] = b_arr[trough_mask] * (1.0 - trough_factor) + 220.0 * trough_factor
    
    # Crests (u >= 0): blend toward Phosphor Cyan (0, 245, 220)
    crest_mask = u_grid >= 0.0
    crest_factor = np.clip(u_grid[crest_mask] / 1.0, 0.0, 1.0)
    r_arr[crest_mask] = r_arr[crest_mask] * (1.0 - crest_factor) + 0.0 * crest_factor
    g_arr[crest_mask] = g_arr[crest_mask] * (1.0 - crest_factor) + 245.0 * crest_factor
    b_arr[crest_mask] = b_arr[crest_mask] * (1.0 - crest_factor) + 220.0 * crest_factor
    
    # Add Liquid Platinum highlights (220, 225, 235) from specular reflection
    r_arr = r_arr * (1.0 - specular) + 220.0 * specular
    g_arr = g_arr * (1.0 - specular) + 225.0 * specular
    b_arr = b_arr * (1.0 - specular) + 235.0 * specular
    
    # Convert to 8-bit unsigned integers
    r_img = np.clip(r_arr, 0, 255).astype(np.uint8)
    g_img = np.clip(g_arr, 0, 255).astype(np.uint8)
    b_img = np.clip(b_arr, 0, 255).astype(np.uint8)
    rgb_small = np.stack([r_img, g_img, b_img], axis=-1)
    
    # Bilinear repeat upscaling to 4K Framebuffer
    sx = W // GRID_W
    sy = H // GRID_H
    big = np.repeat(np.repeat(rgb_small, sy, axis=0), sx, axis=1)
    
    # Write directly to py5 np_pixels array
    py5.load_np_pixels()
    py5.np_pixels[..., 0] = 255
    py5.np_pixels[..., 1] = big[..., 0]
    py5.np_pixels[..., 2] = big[..., 1]
    py5.np_pixels[..., 3] = big[..., 2]
    py5.update_np_pixels()
    
    # Vignette shadow
    py5.no_stroke()
    for i in range(16):
        alpha = int(3 + i * 4)
        m = i * 22
        py5.fill(8, 8, 16, alpha)
        py5.rect(0, 0, W, m)
        py5.rect(0, H - m, W, m)
        py5.rect(0, 0, m, H)
        py5.rect(W - m, 0, m, H)
        
    # Telemetry HUD
    py5.fill(255, 255, 255, 140)
    py5.text_size(20)
    py5.text(f"t={t:.2f}s | drive_amp: {FORCING_AMP:.2f} | grid: {GRID_W}x{GRID_H} | method: Mathieu FDTD", 50, H - 50)
    
    # Blank screen safety check
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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
