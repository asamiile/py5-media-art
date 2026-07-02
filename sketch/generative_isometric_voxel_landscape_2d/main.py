from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()

def draw_isometric_cube(x, y, size, h, hue):
    py5.push_matrix()
    py5.translate(x, y)
    
    # Top face
    py5.fill(hue, 60, 100)
    py5.begin_shape()
    py5.vertex(0, -h)
    py5.vertex(size * np.cos(np.pi/6), -h + size * np.sin(np.pi/6))
    py5.vertex(0, -h + 2 * size * np.sin(np.pi/6))
    py5.vertex(-size * np.cos(np.pi/6), -h + size * np.sin(np.pi/6))
    py5.end_shape(py5.CLOSE)
    
    # Left face
    py5.fill(hue, 80, 70)
    py5.begin_shape()
    py5.vertex(-size * np.cos(np.pi/6), -h + size * np.sin(np.pi/6))
    py5.vertex(0, -h + 2 * size * np.sin(np.pi/6))
    py5.vertex(0, 2 * size * np.sin(np.pi/6))
    py5.vertex(-size * np.cos(np.pi/6), size * np.sin(np.pi/6))
    py5.end_shape(py5.CLOSE)
    
    # Right face
    py5.fill(hue, 90, 40)
    py5.begin_shape()
    py5.vertex(0, -h + 2 * size * np.sin(np.pi/6))
    py5.vertex(size * np.cos(np.pi/6), -h + size * np.sin(np.pi/6))
    py5.vertex(size * np.cos(np.pi/6), size * np.sin(np.pi/6))
    py5.vertex(0, 2 * size * np.sin(np.pi/6))
    py5.end_shape(py5.CLOSE)
    
    py5.pop_matrix()

def draw():
    py5.background(15, 100, 10) # Dark cosmic background
    
    t = py5.frame_count * 0.05
    
    grid_size = 40
    cube_size = 25
    x_offset = py5.width / 2
    y_offset = py5.height * 0.3
    
    # Calculate isometric projection for grid
    for row in range(grid_size):
        for col in range(grid_size):
            # Centered coordinates
            cx = (col - grid_size/2)
            cy = (row - grid_size/2)
            
            # Map 2D grid to isometric screen space
            screen_x = x_offset + (cx - cy) * cube_size * np.cos(np.pi/6)
            screen_y = y_offset + (cx + cy) * cube_size * np.sin(np.pi/6)
            
            # Distance from center for radial waves
            dist = np.sqrt(cx*cx + cy*cy)
            
            # Noise-based height with sine wave pulsing
            noise_val = py5.os_noise(cx * 0.1, cy * 0.1, t * 0.2)
            pulse = np.sin(dist * 0.5 - t * 2) * 0.5 + 0.5
            
            h = (noise_val * 150 + pulse * 100) * max(0, 1 - dist/20)
            
            # Hue mapping based on height and time
            hue = (200 + h + t * 20) % 360
            
            if h > 5:
                draw_isometric_cube(screen_x, screen_y, cube_size, h, hue)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
            
        import os
        os._exit(0)

py5.run_sketch()
