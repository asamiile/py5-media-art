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

# Grid sizes for simulation
GRID_W, GRID_H = 1280, 720

# Keller-Segel parameters
DRHO = 0.06    # Organism diffusion rate
DC = 0.60      # Chemical diffusion rate
CHI = 4.8      # Chemotactic sensitivity
A = 0.5        # Chemical production rate
B = 0.3        # Chemical decay rate
DT = 0.08      # Time step

# Initialize grids
# rho: cell density (in range [0, 1] for volume filling)
# c: chemoattractant concentration
rng = np.random.default_rng(2026)
rho_grid = rng.uniform(0.02, 0.18, (GRID_H, GRID_W)).astype(np.float32)
c_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)


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


def get_divergence(fx, fy):
    # Central difference divergence
    div_x = (np.roll(fx, -1, axis=1) - np.roll(fx, 1, axis=1)) / 2.0
    div_y = (np.roll(fy, -1, axis=0) - np.roll(fy, 1, axis=0)) / 2.0
    return div_x + div_y


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    global rho_grid, c_grid

    # Perform multiple integration steps per frame
    for _ in range(3):
        # 1. Chemical field update:
        # dc/dt = DC * laplacian(c) + A * rho - B * c
        lc = get_laplacian(c_grid)
        next_c = c_grid + DT * (DC * lc + A * rho_grid - B * c_grid)
        c_grid = np.clip(next_c, 0.0, 50.0)

        # 2. Organism density update (Volume-filling Keller-Segel):
        # drho/dt = DRHO * laplacian(rho) - CHI * div( rho * (1 - rho) * grad(c) )
        lrho = get_laplacian(rho_grid)
        cx, cy = get_gradient(c_grid)
        
        # Flux components: J = rho * (1 - rho) * grad(c)
        flux_factor = rho_grid * (1.0 - rho_grid)
        fx = flux_factor * cx
        fy = flux_factor * cy
        
        div_j = get_divergence(fx, fy)
        next_rho = rho_grid + DT * (DRHO * lrho - CHI * div_j)
        rho_grid = np.clip(next_rho, 0.0, 0.99)

    # Color mapping
    # Background/Void: Deep Void (8, 6, 12)
    # Cell density (rho): Bioluminescent Amber (240, 150, 20)
    # Chemical field (c): Glowing Violet (130, 40, 240)
    # Highly packed nodes (rho > 0.6): Phosphor Cyan (0, 245, 235)

    # Normalize chemical field for visual mapping
    c_norm = np.clip(c_grid / 4.0, 0.0, 1.0)
    
    # Base background (Deep Void)
    r_arr = np.full_like(rho_grid, 8.0)
    g_arr = np.full_like(rho_grid, 6.0)
    b_arr = np.full_like(rho_grid, 12.0)

    # Blend chemical field (Violet)
    r_arr = r_arr * (1.0 - c_norm) + 130.0 * c_norm
    g_arr = g_arr * (1.0 - c_norm) + 40.0 * c_norm
    b_arr = b_arr * (1.0 - c_norm) + 240.0 * c_norm

    # Blend cell density (Amber)
    rho_norm = np.clip(rho_grid / 0.7, 0.0, 1.0)
    r_arr = r_arr * (1.0 - rho_norm) + 240.0 * rho_norm
    g_arr = g_arr * (1.0 - rho_norm) + 150.0 * rho_norm
    b_arr = b_arr * (1.0 - rho_norm) + 20.0 * rho_norm

    # Overprint high-density nodes (Phosphor Cyan)
    high_rho = np.clip((rho_grid - 0.45) / 0.35, 0.0, 1.0)
    r_arr = r_arr * (1.0 - high_rho) + 0.0 * high_rho
    g_arr = g_arr * (1.0 - high_rho) + 245.0 * high_rho
    b_arr = b_arr * (1.0 - high_rho) + 235.0 * high_rho

    # Convert to RGB image
    r_img = np.clip(r_arr, 0, 255).astype(np.uint8)
    g_img = np.clip(g_arr, 0, 255).astype(np.uint8)
    b_img = np.clip(b_arr, 0, 255).astype(np.uint8)
    rgb_small = np.stack([r_img, g_img, b_img], axis=-1)

    # Bilinear repeat upscaling to 4K
    sy = py5.height // GRID_H
    sx = py5.width // GRID_W
    big = np.repeat(np.repeat(rgb_small, sy, axis=0), sx, axis=1)

    # Blit directly to screen pixels
    py5.load_np_pixels()
    py5.np_pixels[..., 0] = 255
    py5.np_pixels[..., 1] = big[..., 0]
    py5.np_pixels[..., 2] = big[..., 1]
    py5.np_pixels[..., 3] = big[..., 2]
    py5.update_np_pixels()

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        # Save a preview snapshot (mid frame)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()
