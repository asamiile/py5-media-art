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
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

SIM_W = SIZE[0]
SIM_H = SIZE[1]

NUM_PARTICLES = 500000
pos = np.random.rand(NUM_PARTICLES, 2).astype(np.float32)
pos[:, 0] *= SIM_W
pos[:, 1] *= SIM_H

# Pre-calculate base color variations
colors_r = np.random.uniform(50, 255, NUM_PARTICLES).astype(np.uint16)
colors_g = np.random.uniform(100, 255, NUM_PARTICLES).astype(np.uint16)
colors_b = np.random.uniform(200, 255, NUM_PARTICLES).astype(np.uint16)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global pos
    
    t = py5.frame_count * 0.01
    
    # Analytical vector flow field using combined sine/cosine waves
    # This simulates a smooth, continuous noise-like field without the cost of Perlin noise
    nx = pos[:, 0] * 0.005
    ny = pos[:, 1] * 0.005
    
    vx = np.sin(ny * 2.0 + t) + np.cos(nx * 1.5 - t * 0.8) + np.sin((nx + ny) * 0.5 + t * 1.2)
    vy = np.cos(nx * 2.0 - t) + np.sin(ny * 1.5 + t * 0.9) + np.cos((nx - ny) * 0.5 - t * 1.1)
    
    # Normalize and scale
    v_mag = np.sqrt(vx**2 + vy**2) + 1e-6
    vx = (vx / v_mag) * 3.0
    vy = (vy / v_mag) * 3.0
    
    pos[:, 0] += vx
    pos[:, 1] += vy
    
    # Wrap around edges
    pos[:, 0] = pos[:, 0] % SIM_W
    pos[:, 1] = pos[:, 1] % SIM_H
    
    # Fade background slightly for long trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 10) # 10/255 transparency leaves very long trails
    py5.rect(0, 0, py5.width, py5.height)
    
    # Draw particles additively to np_pixels
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    px = pos[:, 0].astype(int)
    py_ = pos[:, 1].astype(int)
    
    valid = (px >= 0) & (px < SIM_W) & (py_ >= 0) & (py_ < SIM_H)
    p_x = px[valid]
    p_y = py_[valid]
    
    curr_r = pixels[p_y, p_x, 1]
    curr_g = pixels[p_y, p_x, 2]
    curr_b = pixels[p_y, p_x, 3]
    
    # Very faint additive draw to allow lines to build up smoothly
    pixels[p_y, p_x, 0] = 255
    pixels[p_y, p_x, 1] = np.clip(curr_r.astype(np.float32) + colors_r[valid] * 0.05, 0, 255).astype(np.uint8)
    pixels[p_y, p_x, 2] = np.clip(curr_g.astype(np.float32) + colors_g[valid] * 0.05, 0, 255).astype(np.uint8)
    pixels[p_y, p_x, 3] = np.clip(curr_b.astype(np.float32) + colors_b[valid] * 0.05, 0, 255).astype(np.uint8)
    
    py5.update_np_pixels()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
