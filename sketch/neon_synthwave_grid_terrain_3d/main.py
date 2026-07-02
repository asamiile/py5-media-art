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

COLS, ROWS = 60, 40
CELL_SIZE = 80
W = COLS * CELL_SIZE
H = ROWS * CELL_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5, 0, 15) # Very Dark Purple
    
    # Draw the glowing Synthwave Sun in the background (no depth test)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2 - 300, -1000)
    py5.no_stroke()
    
    # Sun glow
    py5.blend_mode(py5.ADD)
    for i in range(10):
        py5.fill(255, 80, 0, 10 - i)
        py5.circle(0, 0, 1000 + i * 20)
        
    # Solid sun with scanlines
    py5.blend_mode(py5.BLEND)
    py5.fill(255, 120, 0)
    py5.circle(0, 0, 900)
    
    # Cut out scanlines
    py5.fill(5, 0, 15)
    t = py5.frame_count * 0.5
    for y in range(-450, 450, 40):
        # Scanlines get thicker at the bottom
        thickness = py5.remap(y, -450, 450, 2, 25)
        # Move scanlines up slowly
        y_pos = y + (t % 40)
        if y_pos < 450:
            py5.rect(-500, y_pos, 1000, thickness)
    py5.pop_matrix()
    
    # Draw the terrain
    py5.hint(py5.ENABLE_DEPTH_TEST)
    py5.blend_mode(py5.BLEND)
    
    py5.translate(py5.width / 2, py5.height / 2 + 300, 200)
    py5.rotate_x(py5.PI / 2.5) # Tilt the grid down
    py5.translate(-W / 2, -H / 2 + 500, 0) # Center the grid, pull it closer
    
    flying_speed = py5.frame_count * 0.05
    
    py5.no_fill()
    py5.stroke_weight(3)
    
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            # Calculate heights using noise
            # Create a flat valley in the center, mountains on the sides
            center_dist_x = abs(x - COLS/2) / (COLS/2)
            valley_mask = np.clip((center_dist_x - 0.2) * 2, 0, 1)
            
            # Row 1
            nx = x * 0.1
            ny = (y - flying_speed) * 0.1
            z1 = py5.os_noise(nx, ny) * 800 * valley_mask
            
            # Row 2
            ny2 = (y + 1 - flying_speed) * 0.1
            z2 = py5.os_noise(nx, ny2) * 800 * valley_mask
            
            # Color gradient based on depth (y)
            depth_ratio = y / ROWS
            r = py5.remap(depth_ratio, 0, 1, 0, 255) # Cyan to Magenta
            b = py5.remap(depth_ratio, 0, 1, 255, 100)
            py5.stroke(r, 0, b)
            
            py5.vertex(x * CELL_SIZE, y * CELL_SIZE, z1)
            py5.vertex(x * CELL_SIZE, (y + 1) * CELL_SIZE, z2)
            
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
