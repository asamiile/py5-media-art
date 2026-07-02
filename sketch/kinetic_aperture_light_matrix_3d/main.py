from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid settings
COLS = 30
ROWS = 20
CELL_SIZE = SIZE[0] / COLS

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_aperture(x, y, z, size, opening_ratio):
    # opening_ratio is between 0 (closed) and 1 (fully open)
    # Draw a mechanical iris
    py5.push_matrix()
    py5.translate(x, y, z)
    
    inner_r = size * 0.45 * opening_ratio
    outer_r = size * 0.48
    
    num_blades = 8
    
    py5.no_stroke()
    py5.fill(30, 30, 35) # Dark metal
    
    # Draw blades
    for i in range(num_blades):
        py5.push_matrix()
        py5.rotate_z((py5.TWO_PI / num_blades) * i + (1 - opening_ratio) * 0.5)
        
        # Blade polygon
        py5.begin_shape()
        py5.vertex(inner_r, 0)
        py5.vertex(outer_r, outer_r * 0.5)
        py5.vertex(outer_r * 0.8, outer_r * 0.8)
        py5.vertex(0, inner_r * 1.5)
        py5.end_shape(py5.CLOSE)
        
        # Blade edge
        py5.stroke(100, 100, 110)
        py5.stroke_weight(2)
        py5.begin_shape(py5.LINES)
        py5.vertex(inner_r, 0)
        py5.vertex(outer_r, outer_r * 0.5)
        py5.end_shape()
        py5.no_stroke()
        
        py5.pop_matrix()
        
    # If open, draw light coming through
    if opening_ratio > 0.05:
        py5.blend_mode(py5.ADD)
        py5.no_stroke()
        # Light core
        py5.fill(200, 240, 255, 150 * opening_ratio)
        py5.ellipse(0, 0, inner_r * 1.8, inner_r * 1.8)
        
        # Glow
        py5.fill(0, 100, 255, 50 * opening_ratio)
        py5.ellipse(0, 0, inner_r * 3, inner_r * 3)
        py5.blend_mode(py5.BLEND)
        
    py5.pop_matrix()

def draw():
    py5.background(10, 10, 15)
    
    # Lighting
    py5.ambient_light(50, 50, 60)
    py5.directional_light(200, 200, 200, 0.5, 1, -1)
    
    py5.push_matrix()
    
    # Center the grid
    offset_x = (SIZE[0] - (COLS * CELL_SIZE)) / 2 + CELL_SIZE / 2
    offset_y = (SIZE[1] - (ROWS * CELL_SIZE)) / 2 + CELL_SIZE / 2
    
    # Slight perspective shift
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    py5.rotate_x(py5.sin(py5.frame_count * 0.01) * 0.15)
    py5.rotate_y(py5.cos(py5.frame_count * 0.015) * 0.1)
    py5.translate(-SIZE[0]/2, -SIZE[1]/2, 0)
    
    for r in range(ROWS):
        for c in range(COLS):
            x = offset_x + c * CELL_SIZE
            y = offset_y + r * CELL_SIZE
            
            # Use 3D noise for fluid wave effect
            noise_val = py5.os_noise(c * 0.15, r * 0.15, py5.frame_count * 0.02)
            
            # Map noise (-1 to 1) to opening ratio (0 to 1) with some bias
            opening = py5.constrain((noise_val + 0.3) * 1.2, 0, 1)
            
            # Apply a geometric wave multiplier
            wave = py5.sin(c * 0.3 + py5.frame_count * 0.05) * py5.cos(r * 0.2 - py5.frame_count * 0.03)
            opening = py5.constrain(opening + wave * 0.3, 0, 1)
            
            # Z displacement based on opening
            z = -opening * 50
            
            draw_aperture(x, y, z, CELL_SIZE, opening)
            
    py5.pop_matrix()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 10 == 0:
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
