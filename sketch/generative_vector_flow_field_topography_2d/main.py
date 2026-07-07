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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 25000

pos = None
vel = None
colors = None

def setup():
    global pos, vel, colors
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(2, 5, 12)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    pos = np.random.rand(NUM_PARTICLES, 2) * [SIZE[0], SIZE[1]]
    vel = np.zeros((NUM_PARTICLES, 2))
    
    # Pre-calculate colors (Deep sea bioluminescence)
    colors = np.zeros((NUM_PARTICLES, 3), dtype=np.uint8)
    for i in range(NUM_PARTICLES):
        r = random.randint(10, 50)
        g = random.randint(150, 255)
        b = random.randint(150, 255)
        colors[i] = [r, g, b]

def draw():
    global pos, vel, colors
    
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(2, 5, 12, 12)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    W, H = SIZE[0], SIZE[1]
    t = py5.frame_count * 0.005
    
    # Calculate angles from 3D noise (x, y, t)
    # Scale coordinates to get smooth noise field
    nx = pos[:, 0] * 0.0015
    ny = pos[:, 1] * 0.0015
    
    angles = np.zeros(NUM_PARTICLES)
    
    for i in range(NUM_PARTICLES):
        angles[i] = py5.os_noise(nx[i], ny[i], t) * py5.TWO_PI * 4.0
        
    speed = 4.0
    vel[:, 0] = np.cos(angles) * speed
    vel[:, 1] = np.sin(angles) * speed
    
    pos += vel
    
    # Out of bounds check
    out_of_bounds = (pos[:, 0] < 0) | (pos[:, 0] > W) | (pos[:, 1] < 0) | (pos[:, 1] > H)
    num_out = np.sum(out_of_bounds)
    if num_out > 0:
        pos[out_of_bounds, 0] = np.random.uniform(0, W, num_out)
        pos[out_of_bounds, 1] = np.random.uniform(0, H, num_out)
        
    # Draw particles
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1.5)
    
    # Draw in chunks for color
    chunk_size = NUM_PARTICLES // 10
    for i in range(10):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        
        avg_r = np.mean(colors[start:end, 0])
        avg_g = np.mean(colors[start:end, 1])
        avg_b = np.mean(colors[start:end, 2])
        
        py5.stroke(avg_r, avg_g, avg_b, 60)
        py5.points(pos[start:end])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
