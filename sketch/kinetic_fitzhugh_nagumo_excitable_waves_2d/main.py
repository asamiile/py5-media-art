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

# Grid sizes for simulation (upscaled to 4K for performance and rendering quality)
GRID_W, GRID_H = 1280, 720

# FitzHugh-Nagumo PDE parameters
# u: activator, v: inhibitor
DU = 0.22      # Activator diffusion rate
DV = 0.01      # Inhibitor diffusion rate
DT = 0.12      # Time step size
EPSILON = 0.03 # Time scale separation
A0 = 0.8       # Parameter a
A1 = 0.7       # Parameter b

# Initialize grids
u_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
v_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Seed multiple spiral-generating wave breaks
rng = np.random.default_rng(1337)
for _ in range(6):
    cx = rng.integers(100, GRID_W - 100)
    cy = rng.integers(100, GRID_H - 100)
    r = 60
    
    # Create gradient grids around center
    yy, xx = np.ogrid[-r:r, -r:r]
    mask = xx**2 + yy**2 <= r**2
    
    # Crossing gradients: u varies horizontally, v varies vertically
    u_patch = (xx / r).astype(np.float32)
    v_patch = (yy / r).astype(np.float32)
    
    # Apply to grids
    u_grid[cy-r:cy+r, cx-r:cx+r] = np.where(mask, u_patch * 1.5, u_grid[cy-r:cy+r, cx-r:cx+r])
    v_grid[cy-r:cy+r, cx-r:cx+r] = np.where(mask, v_patch * 0.8 + 0.3, v_grid[cy-r:cy+r, cx-r:cx+r])


def get_laplacian(grid):
    # Vectorized 2D Laplacian using periodic boundaries (numpy rolls)
    return (
        np.roll(grid, 1, axis=0) +
        np.roll(grid, -1, axis=0) +
        np.roll(grid, 1, axis=1) +
        np.roll(grid, -1, axis=1) -
        4.0 * grid
    )


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    global u_grid, v_grid
    
    # Run multiple PDE steps per frame for smooth wave dynamics
    for _ in range(4):
        lu = get_laplacian(u_grid)
        lv = get_laplacian(v_grid)
        
        # FitzHugh-Nagumo equations:
        # du/dt = DU * laplacian(u) + u - u^3 - v
        # dv/dt = DV * laplacian(v) + EPSILON * (u - A0*v - A1)
        next_u = u_grid + DT * (DU * lu + u_grid - u_grid**3 - v_grid)
        next_v = v_grid + DT * (DV * lv + EPSILON * (u_grid - A0 * v_grid - A1))
        
        u_grid = np.clip(next_u, -2.0, 2.0)
        v_grid = np.clip(next_v, -2.0, 2.0)

    # Color Mapping
    # Palette colors:
    # Background/Void: Obsidian Abyss (12, 10, 16)
    # Activator front (u > 0.5): Bioluminescent Cyan (0, 240, 220)
    # Inhibitor/Refractory (v > 0.2): Deep Ultraviolet (100, 30, 220)
    # Accent/Annihilation cores: Phosphor Amber (250, 160, 20)

    # Normalize values for interpolation
    u_norm = np.clip((u_grid + 1.0) / 2.0, 0.0, 1.0)
    v_norm = np.clip((v_grid + 0.5) / 1.5, 0.0, 1.0)

    # Base background (Obsidian Abyss)
    r_arr = np.full_like(u_grid, 12.0)
    g_arr = np.full_like(u_grid, 10.0)
    b_arr = np.full_like(u_grid, 16.0)

    # Blend refractory tail (Ultraviolet) based on inhibitor v
    r_arr = r_arr * (1.0 - v_norm) + 100.0 * v_norm
    g_arr = g_arr * (1.0 - v_norm) + 30.0 * v_norm
    b_arr = b_arr * (1.0 - v_norm) + 220.0 * v_norm

    # Blend active wave front (Cyan) based on activator u
    u_front = np.clip((u_grid - 0.2) / 0.8, 0.0, 1.0)
    r_arr = r_arr * (1.0 - u_front) + 0.0 * u_front
    g_arr = g_arr * (1.0 - u_front) + 240.0 * u_front
    b_arr = b_arr * (1.0 - u_front) + 220.0 * u_front

    # Additive wave collision/annihilation core (Amber) where both u and v are high
    core_mask = np.clip(u_grid * v_grid, 0.0, 1.0)
    r_arr += core_mask * 250.0
    g_arr += core_mask * 160.0
    b_arr += core_mask * 20.0

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
