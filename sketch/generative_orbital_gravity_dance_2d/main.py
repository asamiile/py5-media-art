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

num_planets = 1200
positions = None
velocities = None
stars = None
num_stars = 3

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global positions, velocities, stars
    
    positions = np.zeros((num_planets, 2), dtype=np.float32)
    velocities = np.zeros((num_planets, 2), dtype=np.float32)
    
    cx, cy = SIZE[0]/2, SIZE[1]/2
    
    for i in range(num_planets):
        angle = np.random.uniform(0, py5.TWO_PI)
        r = np.random.uniform(200, 800)
        positions[i, 0] = cx + r * np.cos(angle)
        positions[i, 1] = cy + r * np.sin(angle)
        
        v = np.sqrt(5000 / r) * 0.8
        velocities[i, 0] = -v * np.sin(angle)
        velocities[i, 1] = v * np.cos(angle)
        
    stars = np.zeros((num_stars, 3), dtype=np.float32) 
    
    py5.background(2)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    global positions, velocities, stars
    py5.blend_mode(py5.BLEND)
    py5.fill(2, 5) 
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    cx, cy = SIZE[0]/2, SIZE[1]/2
    t = py5.frame_count * 0.01
    
    stars[0, 0] = cx + 200 * np.cos(t)
    stars[0, 1] = cy + 200 * np.sin(t)
    stars[0, 2] = 2000.0
    
    stars[1, 0] = cx + 300 * np.cos(t * 0.7 + py5.PI)
    stars[1, 1] = cy + 300 * np.sin(t * 0.7 + py5.PI)
    stars[1, 2] = 1500.0
    
    stars[2, 0] = cx + 100 * np.cos(t * 1.3 + py5.HALF_PI)
    stars[2, 1] = cy + 100 * np.sin(t * 1.3 + py5.HALF_PI)
    stars[2, 2] = 1000.0
    
    for i in range(num_stars):
        py5.fill(40 + i*30, 80, 100, 50)
        s = stars[i, 2] / 50.0
        py5.ellipse(stars[i, 0], stars[i, 1], s, s)
        
    dt = 0.5
    gravity_const = 5.0
    
    for _ in range(3): 
        fx = np.zeros(num_planets, dtype=np.float32)
        fy = np.zeros(num_planets, dtype=np.float32)
        
        for i in range(num_stars):
            dx = stars[i, 0] - positions[:, 0]
            dy = stars[i, 1] - positions[:, 1]
            dist_sq = dx**2 + dy**2 + 1000.0 
            
            force = gravity_const * stars[i, 2] / dist_sq
            fx += force * dx / np.sqrt(dist_sq)
            fy += force * dy / np.sqrt(dist_sq)
            
        velocities[:, 0] += fx * dt
        velocities[:, 1] += fy * dt
        
        positions[:, 0] += velocities[:, 0] * dt
        positions[:, 1] += velocities[:, 1] * dt
        
    py5.no_stroke()
    for i in range(num_planets):
        speed = np.sqrt(velocities[i, 0]**2 + velocities[i, 1]**2)
        hue = (speed * 15 + 200) % 360
        py5.fill(hue, 90, 100, 40)
        py5.ellipse(positions[i, 0], positions[i, 1], 2, 2)

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
