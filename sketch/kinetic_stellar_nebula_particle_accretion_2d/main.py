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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 100000

angles = np.random.uniform(0, py5.TWO_PI, NUM_PARTICLES)
radii = np.random.normal(SIZE[0]*0.4, SIZE[0]*0.15, NUM_PARTICLES)
x = SIZE[0]/2 + np.cos(angles) * radii
y = SIZE[1]/2 + np.sin(angles) * radii

particles = np.column_stack((x, y)).astype(np.float32)
velocities = np.zeros_like(particles)

orbital_speed = 5.0
velocities[:, 0] = -np.sin(angles) * orbital_speed
velocities[:, 1] = np.cos(angles) * orbital_speed

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(2, 0, 5)
    
def draw():
    global particles, velocities
    
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(2, 0, 5, 20) 
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.01
    
    cx, cy = SIZE[0]/2, SIZE[1]/2
    
    dx = cx - particles[:, 0]
    dy = cy - particles[:, 1]
    
    dist_sq = dx**2 + dy**2
    dist = np.sqrt(dist_sq)
    
    dist_sq = np.clip(dist_sq, 1000, None)
    
    force = 10000.0 / dist_sq
    
    velocities[:, 0] += dx * force
    velocities[:, 1] += dy * force
    
    noise_x = py5.os_noise(particles[:, 0] * 0.005, particles[:, 1] * 0.005, t) - 0.5
    noise_y = py5.os_noise(particles[:, 0] * 0.005 + 100, particles[:, 1] * 0.005 + 100, t) - 0.5
    
    velocities[:, 0] += noise_x * 0.5
    velocities[:, 1] += noise_y * 0.5
    
    velocities *= 0.99
    
    particles += velocities
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1)
    
    heat = np.clip(1.0 - (dist / (SIZE[0]*0.5)), 0, 1)
    
    hot = heat > 0.8
    if np.any(hot):
        py5.stroke(255, 255, 255, 40) 
        py5.points(particles[hot])
        
    warm = (heat <= 0.8) & (heat > 0.4)
    if np.any(warm):
        py5.stroke(255, 150, 50, 20) 
        py5.points(particles[warm])
        
    cold = heat <= 0.4
    if np.any(cold):
        py5.stroke(100, 20, 50, 10) 
        py5.points(particles[cold])

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
