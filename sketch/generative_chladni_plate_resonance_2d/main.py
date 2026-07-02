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

num_particles = 30000
positions = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global positions
    
    positions = np.zeros((num_particles, 2), dtype=np.float32)
    positions[:, 0] = np.random.uniform(0, SIZE[0], num_particles)
    positions[:, 1] = np.random.uniform(0, SIZE[1], num_particles)
    
    py5.background(20)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def chladni(x, y, n, m, L):
    nx = x / L
    ny = y / L
    v1 = np.cos(n * np.pi * nx) * np.cos(m * np.pi * ny)
    v2 = np.cos(m * np.pi * nx) * np.cos(n * np.pi * ny)
    return abs(v1 - v2)

def draw():
    global positions
    
    py5.blend_mode(py5.BLEND)
    py5.fill(20, 15) 
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    
    L = min(SIZE[0], SIZE[1])
    
    n = 3.0 + 2.0 * np.sin(t * 0.5)
    m = 5.0 + 3.0 * np.cos(t * 0.3)
    
    eps = 2.0 
    step_size = 20.0
    
    for i in range(num_particles):
        x = positions[i, 0]
        y = positions[i, 1]
        
        c_center = chladni(x, y, n, m, L)
        c_dx = chladni(x + eps, y, n, m, L)
        c_dy = chladni(x, y + eps, n, m, L)
        
        grad_x = (c_dx - c_center) / eps
        grad_y = (c_dy - c_center) / eps
        
        positions[i, 0] -= grad_x * step_size
        positions[i, 1] -= grad_y * step_size
        
        positions[i, 0] += np.random.uniform(-1, 1) * c_center * 5.0
        positions[i, 1] += np.random.uniform(-1, 1) * c_center * 5.0
        
        if positions[i, 0] < 0 or positions[i, 0] > SIZE[0] or positions[i, 1] < 0 or positions[i, 1] > SIZE[1]:
            positions[i, 0] = np.random.uniform(0, SIZE[0])
            positions[i, 1] = np.random.uniform(0, SIZE[1])
            
    py5.no_stroke()
    py5.fill((t * 20) % 360, 40, 90, 40)
    for i in range(num_particles):
        py5.ellipse(positions[i, 0], positions[i, 1], 1.5, 1.5)

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
