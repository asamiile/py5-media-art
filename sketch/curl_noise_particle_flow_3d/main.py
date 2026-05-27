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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 3000
positions = None
velocities = None
lifespans = None

def get_curl(x, y, z):
    eps = 0.01
    
    n1 = py5.os_noise(x, y + eps, z)
    n2 = py5.os_noise(x, y - eps, z)
    a = (n1 - n2) / (2 * eps)
    
    n1 = py5.os_noise(x, y, z + eps)
    n2 = py5.os_noise(x, y, z - eps)
    b = (n1 - n2) / (2 * eps)
    
    cx = a - b
    
    n1 = py5.os_noise(x, y, z + eps)
    n2 = py5.os_noise(x, y, z - eps)
    a = (n1 - n2) / (2 * eps)
    
    n1 = py5.os_noise(x + eps, y, z)
    n2 = py5.os_noise(x - eps, y, z)
    b = (n1 - n2) / (2 * eps)
    
    cy = a - b
    
    n1 = py5.os_noise(x + eps, y, z)
    n2 = py5.os_noise(x - eps, y, z)
    a = (n1 - n2) / (2 * eps)
    
    n1 = py5.os_noise(x, y + eps, z)
    n2 = py5.os_noise(x, y - eps, z)
    b = (n1 - n2) / (2 * eps)
    
    cz = a - b
    
    return np.array([cx, cy, cz])

def reset_particle(i):
    global positions, lifespans, velocities
    positions[i] = (np.random.rand(3) - 0.5) * 1500
    lifespans[i] = np.random.randint(50, 200)
    velocities[i] = np.zeros(3)

def setup():
    global positions, velocities, lifespans
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = (np.random.rand(NUM_PARTICLES, 3) - 0.5) * 1500
    velocities = np.zeros((NUM_PARTICLES, 3))
    lifespans = np.random.randint(50, 200, size=NUM_PARTICLES)

def draw():
    global positions, velocities, lifespans
    
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 20)
    py5.no_stroke()
    
    # Draw background
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.push_matrix()
    py5.camera()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()
    py5.hint(py5.ENABLE_DEPTH_TEST)

    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.005
    
    py5.translate(py5.width/2, py5.height/2)
    py5.rotate_x(py5.frame_count * 0.002)
    py5.rotate_y(py5.frame_count * 0.003)
    
    py5.stroke_weight(3)
    
    noise_scale = 0.002
    
    for i in range(NUM_PARTICLES):
        p = positions[i]
        
        # Calculate curl noise
        curl = get_curl(p[0]*noise_scale, p[1]*noise_scale, p[2]*noise_scale + time)
        
        velocities[i] += curl * 0.5
        velocities[i] *= 0.95 # friction
        
        new_p = p + velocities[i] * 5.0
        
        # Color based on velocity
        speed = np.linalg.norm(velocities[i])
        hue = (220 + speed * 30) % 360 # Blue to Purple/Gold
        if hue > 300: 
            hue = 45 # Gold accent
            
        alpha_val = min(100, lifespans[i] * 2)
        py5.stroke(hue, 90, 100, alpha_val)
        
        py5.line(p[0], p[1], p[2], new_p[0], new_p[1], new_p[2])
        
        positions[i] = new_p
        lifespans[i] -= 1
        
        if lifespans[i] <= 0 or np.linalg.norm(positions[i]) > 1000:
            reset_particle(i)

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
