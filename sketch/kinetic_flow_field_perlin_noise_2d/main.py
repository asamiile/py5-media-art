from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
from scipy.ndimage import zoom

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 500000

# Coarse grid size
GRID_W = 120
GRID_H = int(GRID_W * (SIZE[1] / SIZE[0]))

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colors, z_offset
    
    # Initialize positions randomly
    pos = np.random.rand(NUM_PARTICLES, 2) * [py5.width, py5.height]
    
    # Map colors from deep magenta to electric blue
    norm_idx = np.linspace(0, 1, NUM_PARTICLES)
    r = (0.5 + 0.5 * np.cos(norm_idx * py5.PI + 0.0)) * 255
    g = (0.5 + 0.5 * np.cos(norm_idx * py5.PI + 2.0)) * 100
    b = (0.5 + 0.5 * np.cos(norm_idx * py5.PI + 4.0)) * 255
    
    colors = np.column_stack((r, g, b, np.full(NUM_PARTICLES, 15))) # Alpha 15
    z_offset = 0.0

def draw():
    global pos, z_offset
    
    # Fade background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    # 1. Generate coarse flow field using py5.noise
    # We do this in a fast double loop (only ~8,000 iterations)
    coarse_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    noise_scale = 0.05
    for y in range(GRID_H):
        for x in range(GRID_W):
            # Noise returns 0 to 1. Map to 0 to 4*PI for twisting currents
            val = py5.noise(x * noise_scale, y * noise_scale, z_offset)
            coarse_grid[y, x] = val * py5.PI * 4.0
            
    z_offset += 0.015
    
    # 2. Upscale coarse grid to full screen resolution using fast bilinear interpolation
    zoom_y = py5.height / GRID_H
    zoom_x = py5.width / GRID_W
    flow_field = zoom(coarse_grid, (zoom_y, zoom_x), order=1)
    
    # Flow field might be slightly off by 1 pixel due to rounding, so we clip indices safely
    
    # 3. Update 500,000 particles 3 times per frame for faster perceived motion
    for _ in range(3):
        x_idx = np.clip(pos[:, 0].astype(np.int32), 0, flow_field.shape[1] - 1)
        y_idx = np.clip(pos[:, 1].astype(np.int32), 0, flow_field.shape[0] - 1)
        
        # Look up angle
        angles = flow_field[y_idx, x_idx]
        
        # Calculate velocity
        speed = 3.0
        vx = np.cos(angles) * speed
        vy = np.sin(angles) * speed
        
        # Update positions
        pos[:, 0] += vx
        pos[:, 1] += vy
        
        # Wrap around edges
        pos[:, 0] = np.mod(pos[:, 0], py5.width)
        pos[:, 1] = np.mod(pos[:, 1], py5.height)
    
    # 4. Draw particles
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    # Group by color channel for fast py5.points drawing
    dom_color = np.argmax(colors[:, :3], axis=1)
    
    palette = [
        (255, 30, 200, 20), # Magenta
        (50, 100, 255, 20), # Blue
        (200, 50, 255, 20)  # Purple
    ]
    
    for i in range(3):
        mask = (dom_color == i)
        if np.any(mask):
            py5.stroke(*palette[i])
            py5.points(pos[mask])
            
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
