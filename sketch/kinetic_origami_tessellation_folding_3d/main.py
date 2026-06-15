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

grid_size = 40
spacing = 30
# Create a grid of points
points = np.zeros((grid_size, grid_size, 3))
for x in range(grid_size):
    for y in range(grid_size):
        points[x, y] = [(x - grid_size/2) * spacing, (y - grid_size/2) * spacing, 0]

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth()
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, 0)
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.rotate_x(py5.TWO_PI * 0.15 + py5.sin(t * py5.TWO_PI) * 0.2)
    py5.rotate_y(t * py5.TWO_PI * 0.5)
    
    # Calculate Z displacement (folding)
    displaced_points = np.copy(points)
    for x in range(grid_size):
        for y in range(grid_size):
            # Complex folding pattern using noise and sine waves
            px = displaced_points[x,y,0]
            py = displaced_points[x,y,1]
            
            fold_x = py5.sin(px * 0.02 + t * py5.TWO_PI)
            fold_y = py5.cos(py * 0.02 + t * py5.TWO_PI)
            noise_val = py5.os_noise(px * 0.005, py * 0.005, t * 2.0)
            
            # Combine to create sharp creases (absolute value of sine)
            crease = abs(py5.sin(px * 0.01 + py * 0.01 + t * py5.TWO_PI))
            
            # Max fold height oscillates
            fold_height = 200 * py5.sin(t * py5.TWO_PI * 2.0)
            
            z = fold_height * (crease + noise_val * fold_x * fold_y)
            displaced_points[x, y, 2] = z

    py5.stroke_weight(1)
    
    py5.begin_shape(py5.TRIANGLES)
    for x in range(grid_size - 1):
        for y in range(grid_size - 1):
            p1 = displaced_points[x, y]
            p2 = displaced_points[x+1, y]
            p3 = displaced_points[x, y+1]
            p4 = displaced_points[x+1, y+1]
            
            # Triangle 1: p1, p2, p3
            # Color based on height and position
            avg_z1 = (p1[2] + p2[2] + p3[2]) / 3.0
            hue1 = (180 + avg_z1 * 0.5 + t * 360) % 360
            
            py5.fill(hue1, 80, 100, 40)
            py5.stroke(hue1, 90, 100, 80)
            py5.vertex(p1[0], p1[1], p1[2])
            py5.vertex(p2[0], p2[1], p2[2])
            py5.vertex(p3[0], p3[1], p3[2])
            
            # Triangle 2: p2, p4, p3
            avg_z2 = (p2[2] + p4[2] + p3[2]) / 3.0
            hue2 = (25 + avg_z2 * 0.5 + t * 360) % 360 # Electric orange base
            
            py5.fill(hue2, 80, 100, 40)
            py5.stroke(hue2, 90, 100, 80)
            py5.vertex(p2[0], p2[1], p2[2])
            py5.vertex(p4[0], p4[1], p4[2])
            py5.vertex(p3[0], p3[1], p3[2])
            
    py5.end_shape()

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
