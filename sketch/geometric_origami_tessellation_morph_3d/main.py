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

# Grid size
COLS = 60
ROWS = 60
SCL = 30 # Size of each cell

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(10, 80, 5)
    
    py5.lights()
    py5.directional_light(0, 0, 100, 0, 1, -1)
    py5.directional_light(220, 80, 100, -1, -1, -1)
    
    t = py5.frame_count * 0.015
    
    py5.translate(py5.width / 2, py5.height / 2 + 300, -500)
    
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.2)
    
    # Center the grid
    py5.translate(-COLS * SCL / 2, -ROWS * SCL / 2, 0)
    
    # Calculate noise values
    # We use numpy to quickly calculate all Z values
    x_coords = np.linspace(0, COLS * 0.1, COLS)
    y_coords = np.linspace(0, ROWS * 0.1, ROWS)
    
    # Create meshgrid
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Complex folding function
    Z = np.sin(X * 2 + t * 3) * np.cos(Y * 2 - t * 2) * 50
    # Add noise-like high frequency detail
    Z += np.sin(X * 10 + Y * 5 + t * 5) * 15
    # Add slow wave
    Z += np.sin(np.sqrt((X - COLS*0.05)**2 + (Y - ROWS*0.05)**2) * 3 - t * 4) * 100
    
    py5.stroke_weight(1)
    
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            # Vertex 1 (top)
            z1 = Z[y, x]
            hue1 = (200 + z1 + t * 50) % 360
            py5.fill(hue1, 80, 90)
            py5.stroke((hue1 + 180) % 360, 50, 100, 50)
            py5.vertex(x * SCL, y * SCL, z1)
            
            # Vertex 2 (bottom)
            z2 = Z[y+1, x]
            hue2 = (200 + z2 + t * 50) % 360
            py5.fill(hue2, 80, 90)
            py5.stroke((hue2 + 180) % 360, 50, 100, 50)
            py5.vertex(x * SCL, (y+1) * SCL, z2)
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
