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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

TILE_SIZE = 80
cols = 0
rows = 0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    global cols, rows
    cols = py5.width // TILE_SIZE + 2
    rows = py5.height // TILE_SIZE + 2
    
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_truchet_tile(x, y, rotation_angle, col_idx, row_idx):
    py5.push_matrix()
    py5.translate(x, y)
    py5.rotate(rotation_angle)
    
    # Base color depending on position
    color_mix = (col_idx + row_idx) * 0.05
    r = py5.lerp(0, 50, color_mix % 1.0)
    g = py5.lerp(255, 255, color_mix % 1.0)
    b = py5.lerp(255, 100, color_mix % 1.0)
    
    py5.stroke(r, g, b, 200)
    py5.stroke_weight(8)
    py5.no_fill()
    
    # Add a glowing thicker stroke beneath
    py5.stroke(0, 50, 255, 50)
    py5.stroke_weight(20)
    
    # Arc 1: Top-Left
    py5.arc(-TILE_SIZE/2, -TILE_SIZE/2, TILE_SIZE, TILE_SIZE, 0, py5.HALF_PI)
    
    # Arc 2: Bottom-Right
    py5.arc(TILE_SIZE/2, TILE_SIZE/2, TILE_SIZE, TILE_SIZE, py5.PI, py5.PI + py5.HALF_PI)
    
    # Draw core lines
    py5.stroke(r, g, b, 255)
    py5.stroke_weight(6)
    py5.arc(-TILE_SIZE/2, -TILE_SIZE/2, TILE_SIZE, TILE_SIZE, 0, py5.HALF_PI)
    py5.arc(TILE_SIZE/2, TILE_SIZE/2, TILE_SIZE, TILE_SIZE, py5.PI, py5.PI + py5.HALF_PI)
    
    py5.pop_matrix()

def draw():
    py5.background(10, 15, 25) # Very dark blue/black
    
    t = py5.frame_count * 0.02
    
    # We want smooth rotation. We'll use noise to determine a target state (0 or 1)
    # and then smoothstep it based on time to animate the 90 degree rotation.
    
    py5.translate(-TILE_SIZE/2, -TILE_SIZE/2)
    
    for i in range(cols):
        for j in range(rows):
            x = i * TILE_SIZE
            y = j * TILE_SIZE
            
            # Use noise to pick a target state that flips periodically
            noise_val = py5.os_noise(i * 0.1, j * 0.1, t * 0.5)
            
            # If noise > 0.5, target is 1 (90 degrees), else 0 (0 degrees)
            # To make it smooth, we use a sine wave on the noise
            smooth_val = (np.sin(noise_val * np.pi * 4.0 - t * 2.0) + 1.0) / 2.0
            
            # Ease the rotation using smoothstep
            eased_val = smooth_val * smooth_val * (3.0 - 2.0 * smooth_val)
            
            angle = eased_val * py5.HALF_PI
            
            draw_truchet_tile(x, y, angle, i, j)

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
