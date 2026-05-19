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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

num_particles = 150000
pos = None
ages = None

def get_curl_noise(x, y, t):
    # Base frequencies
    f1, f2, f3 = 0.002, 0.005, 0.011
    
    # Potential derivatives
    dp_dy = -f1 * np.sin(f1 * x + t) * np.sin(f1 * y) \
            -f2 * np.sin(f2 * x - t*0.5) * np.sin(f2 * y + t) \
            -f3 * 1.5 * np.cos(f3 * x) * np.sin(f3 * y - t*1.2)
            
    dp_dx =  f1 * np.cos(f1 * x + t) * np.cos(f1 * y) \
            +f2 * np.cos(f2 * x - t*0.5) * np.cos(f2 * y + t) \
            -f3 * 1.5 * np.sin(f3 * x) * np.cos(f3 * y - t*1.2)
            
    vx = dp_dy * 400
    vy = -dp_dx * 400 - 3.0 # Buoyancy
    return vx, vy

def setup():
    global pos, ages
    py5.size(SIZE[0], SIZE[1], py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(15, 15, 18) # Dark charcoal
    
    pos = np.zeros((num_particles, 2), dtype=np.float32)
    pos[:, 0] = np.random.uniform(0, py5.width, num_particles)
    pos[:, 1] = np.random.uniform(0, py5.height, num_particles)
    
    ages = np.random.uniform(0, 100, num_particles)

def draw():
    global pos, ages
    
    # Fading background for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(15, 15, 18, 20) # Trail length
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.02
    
    # Advect
    vx, vy = get_curl_noise(pos[:, 0], pos[:, 1], t)
    pos[:, 0] += vx
    pos[:, 1] += vy
    ages += 1
    
    # Respawn
    dead = (ages > 120) | (pos[:, 0] < 0) | (pos[:, 0] > py5.width) | (pos[:, 1] < -100) | (pos[:, 1] > py5.height + 100)
    num_dead = np.sum(dead)
    if num_dead > 0:
        pos[dead, 0] = np.random.uniform(0, py5.width, num_dead)
        pos[dead, 1] = py5.height + 20 # Respawn near bottom
        ages[dead] = 0
        
    py5.blend_mode(py5.ADD)
    
    # Schlieren optics effect
    py5.stroke(220, 230, 255, 30) # Faint electric blue/silver tint
    py5.stroke_weight(1.5)
    py5.points(pos)

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

py5.run_sketch()
