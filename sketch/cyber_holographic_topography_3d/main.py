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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

COLS, ROWS = 60, 80
SCL = 30 # Scale of each grid cell
W, H = COLS * SCL, ROWS * SCL

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5, 5, 10) # Pitch black / deep void
    
    py5.translate(py5.width / 2, py5.height / 2 + 300, -400)
    py5.rotate_x(py5.PI / 3) # Tilt for map view
    
    # Slight dynamic camera pan
    py5.rotate_z(np.sin(py5.frame_count * 0.005) * 0.2)
    
    py5.translate(-W / 2, -H / 2, 0)
    
    # Forward movement offset
    flying = py5.frame_count * 0.05
    
    # Generate terrain heights
    terrain = np.zeros((ROWS, COLS))
    for y in range(ROWS):
        for x in range(COLS):
            # Noise for terrain height (os_noise returns -1 to 1)
            val = py5.os_noise(x * 0.06, (y * 0.06) - flying)
            mapped_val = (val + 1.0) * 0.5
            # Power to make valleys flat and peaks sharp
            terrain[y][x] = (mapped_val ** 1.5) * 600 - 150
            
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)
    
    py5.stroke_weight(1.5)
    
    # Draw the mesh
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            for dy in [0, 1]:
                yy = y + dy
                z = terrain[yy][x]
                
                # Height-based coloring
                if z > 200:
                    py5.stroke(255, 50, 50, 200) # Warning Red
                    py5.fill(255, 50, 50, 20)
                else:
                    py5.stroke(0, 255, 255, 150) # Holographic Cyan
                    py5.fill(0, 50, 255, 10) # Deep Neon Blue
                    
                py5.vertex(x * SCL, yy * SCL, z)
        py5.end_shape()
        
    # Draw data particles floating above
    py5.stroke_weight(3)
    py5.begin_shape(py5.POINTS)
    for _ in range(50):
        px = py5.random(COLS - 1)
        py5.stroke(0, 255, 200, 255) # Cyan/Green data points
        # Keep particles fixed in space relative to moving terrain
        py_absolute = py5.random(ROWS * SCL)
        
        # Calculate local grid coords
        gx = int(px)
        gy = int((py_absolute + flying * SCL) % ROWS)
        if gy >= ROWS: gy = ROWS - 1
        
        pz = terrain[gy][gx] + py5.random(50, 150)
        
        py5.vertex(px * SCL, py_absolute, pz)
    py5.end_shape()

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
