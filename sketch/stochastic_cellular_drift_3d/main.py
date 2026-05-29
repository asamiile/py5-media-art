from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os

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

NUM_CELLS = 400
cells_pos = None
cells_color = None
cells_size = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global cells_pos, cells_color, cells_size
    cells_pos = np.random.randn(NUM_CELLS, 3) * 400
    
    # Random colors matching palette
    # Deep blue (220-240), Pale green (120-150), Warm coral (10-30)
    cells_color = np.zeros((NUM_CELLS, 3))
    for i in range(NUM_CELLS):
        r = np.random.rand()
        if r < 0.6:
            cells_color[i] = [py5.random(220, 240), 90, 80]
        elif r < 0.9:
            cells_color[i] = [py5.random(120, 150), 60, 90]
        else:
            cells_color[i] = [py5.random(10, 30), 80, 100]
            
    cells_size = np.random.rand(NUM_CELLS) * 30 + 10

def draw():
    global cells_pos
    
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Soft glowing spheres
    py5.ambient_light(50, 50, 50)
    py5.directional_light(0, 0, 100, 0, 1, -1)
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    t = py5.frame_count * 0.01
    py5.rotate_y(t)
    
    # Move cells based on noise
    for i in range(NUM_CELLS):
        nx = py5.os_noise(cells_pos[i,0]*0.005, cells_pos[i,1]*0.005, t) - 0.5
        ny = py5.os_noise(cells_pos[i,1]*0.005, cells_pos[i,2]*0.005, t) - 0.5
        nz = py5.os_noise(cells_pos[i,2]*0.005, cells_pos[i,0]*0.005, t) - 0.5
        
        cells_pos[i,0] += nx * 2
        cells_pos[i,1] += ny * 2
        cells_pos[i,2] += nz * 2
        
        py5.push_matrix()
        py5.translate(cells_pos[i,0], cells_pos[i,1], cells_pos[i,2])
        py5.no_stroke()
        py5.fill(cells_color[i,0], cells_color[i,1], cells_color[i,2], 80)
        py5.sphere(cells_size[i])
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
            
        os._exit(0)

py5.run_sketch()
