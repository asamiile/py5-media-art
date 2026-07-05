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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid properties
COLS = 120
ROWS = 68
grid_x = None
grid_y = None


def setup():
    global grid_x, grid_y
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Pre-calculate grid coordinates
    grid_x, grid_y = np.meshgrid(
        np.linspace(0, SIZE[0], COLS),
        np.linspace(0, SIZE[1], ROWS)
    )


def draw():
    py5.background(10)  # Pitch black void
    
    t = py5.frame_count * 0.015
    
    # Calculate noise fields
    # Optical flow base
    noise_x = py5.os_noise(grid_x * 0.002, grid_y * 0.002, t * 0.5) * 2 - 1
    noise_y = py5.os_noise(grid_x * 0.002 + 100, grid_y * 0.002 + 100, t * 0.5) * 2 - 1
    
    # Glitch field (high frequency)
    glitch_thresh = py5.os_noise(grid_x * 0.01 + 50, grid_y * 0.01 + 50, t * 2.0)
    
    py5.rect_mode(py5.CENTER)
    py5.no_stroke()
    
    # Renders points
    for i in range(ROWS):
        for j in range(COLS):
            base_x = grid_x[i, j]
            base_y = grid_y[i, j]
            
            nx = noise_x[i, j]
            ny = noise_y[i, j]
            
            gl = glitch_thresh[i, j]
            
            x = base_x + nx * 50
            y = base_y + ny * 50
            
            w = 8
            h = 8
            
            # Apply glitch tearing
            is_glitch = gl > 0.8
            if is_glitch:
                x += random.uniform(-100, 100)
                y += random.uniform(-10, 10)
                w = random.uniform(2, 40)
                h = random.uniform(2, 10)
                
                color_choice = random.choice([(255, 0, 255), (0, 255, 255)])
                py5.fill(*color_choice)
            else:
                # Normal grid elements
                brightness = 150 + nx * 105
                py5.fill(brightness, brightness, brightness)
                
            py5.push_matrix()
            py5.translate(x, y)
            py5.rotate(nx * py5.PI)
            
            if is_glitch and random.random() > 0.5:
                py5.ellipse(0, 0, w, h)
            else:
                py5.rect(0, 0, w, h)
                
            py5.pop_matrix()


    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
