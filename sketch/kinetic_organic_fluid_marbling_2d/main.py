from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 15  # 15s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

N_PARTICLES = 30000
particles = None

def get_curl_np(x, y, t):
    eps = 0.01
    scale = 0.003
    
    n1 = np.array([py5.os_noise(px * scale, (py + eps) * scale, t) for px, py in zip(x, y)])
    n2 = np.array([py5.os_noise(px * scale, (py - eps) * scale, t) for px, py in zip(x, y)])
    a = (n1 - n2) / (2 * eps)
    
    n3 = np.array([py5.os_noise((px + eps) * scale, py * scale, t) for px, py in zip(x, y)])
    n4 = np.array([py5.os_noise((px - eps) * scale, py * scale, t) for px, py in zip(x, y)])
    b = (n3 - n4) / (2 * eps)
    
    return a, -b

def setup():
    global particles
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 15, 25) # Dark indigo base
    FRAMES_DIR.mkdir(exist_ok=True)
    
    particles = np.zeros((N_PARTICLES, 4))
    particles[:, 0] = np.random.uniform(0, SIZE[0], N_PARTICLES)
    particles[:, 1] = np.random.uniform(0, SIZE[1], N_PARTICLES)
    particles[:, 2] = np.random.uniform(0, 1, N_PARTICLES)
    particles[:, 3] = np.random.uniform(0, 1, N_PARTICLES)

def draw():
    global particles
    
    py5.no_stroke()
    py5.fill(10, 15, 25, 10)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.005
    
    vx, vy = get_curl_np(particles[:, 0], particles[:, 1], t)
    
    particles[:, 0] += vx * 5.0
    particles[:, 1] += vy * 5.0
    particles[:, 3] -= 0.01
    
    # Respawn dead or out-of-bounds particles
    dead = (particles[:, 3] < 0) | (particles[:, 0] < 0) | (particles[:, 0] > SIZE[0]) | (particles[:, 1] < 0) | (particles[:, 1] > SIZE[1])
    num_dead = np.sum(dead)
    if num_dead > 0:
        particles[dead, 0] = np.random.uniform(0, SIZE[0], num_dead)
        particles[dead, 1] = np.random.uniform(0, SIZE[1], num_dead)
        particles[dead, 3] = 1.0

    # For colors, just use a simpler method or batch them
    # To keep it fast, we will draw all points with a single color
    # Then we add variations based on hue
    
    py5.stroke_weight(2)
    py5.blend_mode(py5.ADD)
    
    py5.stroke(50, 200, 255, 100) # Turquoise
    py5.points(particles[:, 0:2])
    
    py5.blend_mode(py5.BLEND)

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
