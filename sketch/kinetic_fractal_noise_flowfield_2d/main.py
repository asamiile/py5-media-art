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

# Particle parameters
NUM_PARTICLES = 25000
particles = np.random.uniform(0, SIZE[0], (NUM_PARTICLES, 2))
particles[:, 1] = np.random.uniform(0, SIZE[1], NUM_PARTICLES)
velocities = np.zeros((NUM_PARTICLES, 2))

def get_curl_noise(x, y, t):
    # Simulate curl noise by finite difference of perlin noise
    eps = 0.01
    scale = 0.002
    
    n1 = py5.noise(x * scale, (y + eps) * scale, t)
    n2 = py5.noise(x * scale, (y - eps) * scale, t)
    a = (n1 - n2) / (2 * eps)
    
    n3 = py5.noise((x + eps) * scale, y * scale, t)
    n4 = py5.noise((x - eps) * scale, y * scale, t)
    b = (n3 - n4) / (2 * eps)
    
    return np.array([a, -b])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(5, 5, 10)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    # Fade background slightly for trails
    py5.no_stroke()
    py5.fill(240, 50, 5, 2)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.005
    
    py5.stroke_weight(3)
    
    for i in range(NUM_PARTICLES):
        p = particles[i]
        
        # Get curl noise for direction
        force = get_curl_noise(p[0], p[1], t) * 10
        
        velocities[i] = velocities[i] * 0.95 + force * 0.05
        new_p = p + velocities[i]
        
        # Color based on angle
        angle = np.arctan2(velocities[i][1], velocities[i][0])
        hue_val = np.interp(angle, [-np.pi, np.pi], [280, 360]) # Pink to blue/purple
        if hue_val > 360: hue_val -= 360
        
        speed = np.linalg.norm(velocities[i])
        
        py5.stroke(hue_val, 90, 100, min(100, 80 + speed * 15))
        py5.line(p[0], p[1], new_p[0], new_p[1])
        
        # Screen wrap
        if new_p[0] < 0: new_p[0] += SIZE[0]
        if new_p[0] > SIZE[0]: new_p[0] -= SIZE[0]
        if new_p[1] < 0: new_p[1] += SIZE[1]
        if new_p[1] > SIZE[1]: new_p[1] -= SIZE[1]
        
        # Reset position sometimes to prevent clumping
        if random.random() < 0.01:
            new_p = np.array([random.uniform(0, SIZE[0]), random.uniform(0, SIZE[1])])
            velocities[i] = [0, 0]
            
        particles[i] = new_p

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
