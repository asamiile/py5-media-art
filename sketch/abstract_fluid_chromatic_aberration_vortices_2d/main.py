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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_particles = 6000
particles = None
noise_scale = 0.002

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles
    particles = np.zeros((num_particles, 4), dtype=np.float32)
    particles[:, 0] = np.random.uniform(0, SIZE[0], num_particles)
    particles[:, 1] = np.random.uniform(0, SIZE[1], num_particles)
    particles[:, 2] = np.random.uniform(0.5, 2.0, num_particles) # Speed multiplier
    particles[:, 3] = np.random.uniform(1.0, 5.0, num_particles) # Size
    
    py5.background(10, 10, 15) # Deep dark blue/grey

def get_curl(x, y, t):
    eps = 1.0
    n1 = py5.os_noise(x * noise_scale, (y + eps) * noise_scale, t)
    n2 = py5.os_noise(x * noise_scale, (y - eps) * noise_scale, t)
    n3 = py5.os_noise((x + eps) * noise_scale, y * noise_scale, t)
    n4 = py5.os_noise((x - eps) * noise_scale, y * noise_scale, t)
    
    cx = (n1 - n2) / (2 * eps)
    cy = -(n3 - n4) / (2 * eps)
    return cx, cy

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 10, 15, 12) # Slight fade for long trails
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.003
    
    c_x = np.zeros(num_particles)
    c_y = np.zeros(num_particles)
    for i in range(num_particles):
        cx, cy = get_curl(particles[i, 0], particles[i, 1], t)
        c_x[i] = cx
        c_y[i] = cy
        
    particles[:, 0] += c_x * particles[:, 2] * 400
    particles[:, 1] += c_y * particles[:, 2] * 400
    
    for i in range(num_particles):
        x, y = particles[i, 0], particles[i, 1]
        s = particles[i, 3]
        
        vx = c_x[i] * 400
        vy = c_y[i] * 400
        speed = np.sqrt(vx**2 + vy**2)
        offset = speed * 1.5
        
        py5.no_stroke()
        # Red
        py5.fill(255, 40, 40, 50)
        py5.ellipse(x - offset, y, s, s)
        
        # Green
        py5.fill(40, 255, 40, 50)
        py5.ellipse(x, y + offset, s, s)
        
        # Blue
        py5.fill(40, 40, 255, 50)
        py5.ellipse(x + offset, y - offset, s, s)
        
        if x < 0: particles[i, 0] += SIZE[0]
        if x > SIZE[0]: particles[i, 0] -= SIZE[0]
        if y < 0: particles[i, 1] += SIZE[1]
        if y > SIZE[1]: particles[i, 1] -= SIZE[1]

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
