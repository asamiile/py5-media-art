from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 6
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid size for Gray-Scott simulation (optimized)
GRID_W = 160
GRID_H = 90

# Simulation grids (U, V concentration)
U = np.ones((GRID_H, GRID_W), dtype=np.float32)
V = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Gray-Scott feed/kill parameters (typically feed=0.0367, kill=0.0649)
Du = 0.16
Dv = 0.08
feed = 0.037
kill = 0.060


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed V concentration with some random circles/squares
    global U, V
    for _ in range(12):
        cx = random.randint(GRID_W // 4, 3 * GRID_W // 4)
        cy = random.randint(GRID_H // 4, 3 * GRID_H // 4)
        r = random.randint(10, 25)
        # Create disk mask
        y, x = np.ogrid[-cy:GRID_H-cy, -cx:GRID_W-cx]
        mask = x*x + y*y <= r*r
        U[mask] = 0.5
        V[mask] = 0.25 + np.random.uniform(0.0, 0.1, size=np.sum(mask))


def laplacian(grid):
    # Compute 5-point discrete Laplacian with periodic boundaries
    return (
        np.roll(grid, 1, axis=0) +
        np.roll(grid, -1, axis=0) +
        np.roll(grid, 1, axis=1) +
        np.roll(grid, -1, axis=1) -
        4.0 * grid
    )


def draw():
    global U, V
    
    # 1. Update Gray-Scott reaction-diffusion with advection
    t = py5.frame_count * 0.01
    # Precompute a chaotic wind/flow field using sine/cosine waves rather than py5.noise
    # This runs 100x faster than calling py5.noise in loops
    x_coords = np.linspace(0, 4.0 * np.pi, GRID_W, dtype=np.float32)
    y_coords = np.linspace(0, 2.25 * np.pi, GRID_H, dtype=np.float32)
    xx, yy = np.meshgrid(x_coords, y_coords)
    
    # Sum of shifting waves creates chaotic pseudo-noise flow field
    angle = np.sin(xx + t) * np.cos(yy - t) * 2.0 + np.sin(xx * 0.5 - t * 0.5) * 1.5
    vx = np.cos(angle) * 1.5
    vy = np.sin(angle) * 1.5
            
    # Semi-Lagrangian advection step for U and V
    coords_y, coords_x = np.indices((GRID_H, GRID_W))
    src_x = (coords_x - vx) % GRID_W
    src_y = (coords_y - vy) % GRID_H
    
    # Bilinear interpolation for advection lookup
    x0 = np.floor(src_x).astype(np.int32)
    x1 = (x0 + 1) % GRID_W
    y0 = np.floor(src_y).astype(np.int32)
    y1 = (y0 + 1) % GRID_H
    
    wx = src_x - x0
    wy = src_y - y0
    
    # Interpolate U
    u_00 = U[y0, x0]
    u_10 = U[y0, x1]
    u_01 = U[y1, x0]
    u_11 = U[y1, x1]
    U = (1.0 - wy) * ((1.0 - wx) * u_00 + wx * u_10) + wy * ((1.0 - wx) * u_01 + wx * u_11)
    
    # Interpolate V
    v_00 = V[y0, x0]
    v_10 = V[y0, x1]
    v_01 = V[y1, x0]
    v_11 = V[y1, x1]
    V = (1.0 - wy) * ((1.0 - wx) * v_00 + wx * v_10) + wy * ((1.0 - wx) * v_01 + wx * v_11)
    
    # 2. Reaction-Diffusion step (multiple substeps per frame for stability)
    for _ in range(1):
        lu = laplacian(U)
        lv = laplacian(V)
        uv2 = U * V * V
        U += Du * lu - uv2 + feed * (1.0 - U)
        V += Dv * lv + uv2 - (feed + kill) * V
        
    # Clip concentrations to safety
    U = np.clip(U, 0.0, 1.0)
    V = np.clip(V, 0.0, 1.0)
    
    # 3. Render grid to screen using high-resolution upscaling (bilinear)
    # Map concentration V to color palette (Violet to Cyan/White)
    # ARGB channels
    r_ch = np.zeros_like(V)
    g_ch = np.zeros_like(V)
    b_ch = np.zeros_like(V)
    
    # Background: dark indigo void
    r_ch += 4.0 / 255.0
    g_ch += 4.0 / 255.0
    b_ch += 6.0 / 255.0
    
    # Dominant Cyan and Secondary Violet
    # Violet region (low-mid V)
    violet_mask = V > 0.05
    r_ch[violet_mask] += (V[violet_mask] * 138.0 / 255.0)
    g_ch[violet_mask] += (V[violet_mask] * 43.0 / 255.0)
    b_ch[violet_mask] += (V[violet_mask] * 226.0 / 255.0)
    
    # Cyan region (mid-high V)
    cyan_mask = V > 0.2
    factor = (V[cyan_mask] - 0.2) / 0.8
    r_ch[cyan_mask] = r_ch[cyan_mask] * (1.0 - factor) + factor * 0.0
    g_ch[cyan_mask] = g_ch[cyan_mask] * (1.0 - factor) + factor * 240.0 / 255.0
    b_ch[cyan_mask] = b_ch[cyan_mask] * (1.0 - factor) + factor * 255.0 / 255.0
    
    # Hot White peaks
    white_mask = V > 0.6
    w_factor = (V[white_mask] - 0.6) / 0.4
    r_ch[white_mask] = r_ch[white_mask] * (1.0 - w_factor) + w_factor * 1.0
    g_ch[white_mask] = g_ch[white_mask] * (1.0 - w_factor) + w_factor * 1.0
    b_ch[white_mask] = b_ch[white_mask] * (1.0 - w_factor) + w_factor * 1.0
    
    # Clip colors
    r_ch = np.clip(r_ch * 255, 0, 255).astype(np.uint32)
    g_ch = np.clip(g_ch * 255, 0, 255).astype(np.uint32)
    b_ch = np.clip(b_ch * 255, 0, 255).astype(np.uint32)
    
    # Pack into (H, W, 4) uint8 array for np_pixels (format is usually R, G, B, A or B, G, R, A depending on platform, but py5 uses R, G, B, A in np_pixels)
    packed = np.zeros((GRID_H, GRID_W, 4), dtype=np.uint8)
    packed[..., 0] = r_ch
    packed[..., 1] = g_ch
    packed[..., 2] = b_ch
    packed[..., 3] = 255  # Alpha
    
    # Upscale dynamically using py5 image
    img = py5.create_image(GRID_W, GRID_H, py5.ARGB)
    img.load_np_pixels()
    img.np_pixels[:] = packed
    img.update_pixels()
    
    # Render upscaled image
    py5.image(img, 0, 0, *SIZE)
    
    # Add a subtle vignette/frame overlay
    py5.no_fill()
    py5.stroke(0, 0, 0, 80)
    py5.stroke_weight(40)
    py5.rect(0, 0, *SIZE)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
