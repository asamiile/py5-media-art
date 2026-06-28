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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Tile parameters
TILE_SIZE = 60
COLS = SIZE[0] // TILE_SIZE + 2
ROWS = SIZE[1] // TILE_SIZE + 2

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(240, 240, 235) # off-white
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global tile_types
    # 0 or 1 for the base configuration of the Truchet tile
    tile_types = np.random.randint(0, 2, size=(ROWS, COLS))
    
def draw():
    py5.background(240, 240, 235)
    
    progress = py5.frame_count / TOTAL_FRAMES
    time_val = progress * py5.PI * 2.0
    
    py5.stroke(30, 30, 35)
    py5.stroke_weight(6.0)
    py5.no_fill()
    py5.stroke_cap(py5.SQUARE)
    
    # Draw all tiles
    for r in range(ROWS):
        for c in range(COLS):
            x = c * TILE_SIZE
            y = r * TILE_SIZE
            
            # The rotation is driven by a slow, seamless noise loop
            nx = c * 0.05 + np.cos(time_val) * 0.5
            ny = r * 0.05 + np.sin(time_val) * 0.5
            n = py5.noise(nx, ny)
            
            # Quantize noise into 4 possible 90-degree rotations
            rotation_idx = int(n * 4)
            rotation_angle = rotation_idx * py5.PI / 2.0
            
            # Add a slight smooth interpolation between states for a kinetic flip
            # We can use the fractional part of n*4 with an ease function
            frac = (n * 4) % 1.0
            if frac > 0.8:
                # smooth flip animation during the top 20% of the bracket
                ease = py5.remap(frac, 0.8, 1.0, 0, 1)
                ease = ease * ease * (3 - 2 * ease) # Smoothstep
                rotation_angle += ease * py5.PI / 2.0
            
            py5.push_matrix()
            py5.translate(x + TILE_SIZE/2, y + TILE_SIZE/2)
            py5.rotate(rotation_angle)
            
            # Draw arcs for the Truchet tile
            half = TILE_SIZE / 2
            
            if tile_types[r, c] == 0:
                py5.arc(-half, -half, TILE_SIZE, TILE_SIZE, 0, py5.PI / 2)
                py5.arc(half, half, TILE_SIZE, TILE_SIZE, py5.PI, py5.PI * 1.5)
            else:
                py5.arc(half, -half, TILE_SIZE, TILE_SIZE, py5.PI / 2, py5.PI)
                py5.arc(-half, half, TILE_SIZE, TILE_SIZE, py5.PI * 1.5, py5.PI * 2)
            
            # Sometimes draw an accent
            if n > 0.85:
                py5.fill(255, 80, 50)
                py5.no_stroke()
                py5.circle(0, 0, TILE_SIZE * 0.25)
                py5.no_fill()
                py5.stroke(30, 30, 35)
                py5.stroke_weight(6.0)
                
            py5.pop_matrix()

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
