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

num_particles = 10000
particles = None
cylinder_radius = 150
U0 = 10.0 

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles
    particles = np.zeros((num_particles, 4), dtype=np.float32)
    particles[:, 0] = np.random.uniform(-SIZE[0], SIZE[0]*2, num_particles)
    particles[:, 1] = np.random.uniform(0, SIZE[1], num_particles)
    particles[:, 2] = np.random.uniform(1.0, 3.0, num_particles) 
    particles[:, 3] = np.random.uniform(0, py5.TWO_PI, num_particles) 
    
    py5.background(5, 8, 15)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 8, 15, 10) 
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    cx, cy = SIZE[0]/3, SIZE[1]/2
    R = cylinder_radius
    
    t = py5.frame_count * 0.02
    noise_scale = 0.005
    
    py5.no_stroke()
    for i in range(num_particles):
        x, y = particles[i, 0], particles[i, 1]
        
        dx = x - cx
        dy = y - cy
        r2 = dx*dx + dy*dy
        r = np.sqrt(r2)
        
        if r < R:
            particles[i, 0] = np.random.uniform(-200, -50)
            particles[i, 1] = np.random.uniform(0, SIZE[1])
            continue
            
        vx = U0 * (1.0 - R**2 * (dx**2 - dy**2) / (r2**2))
        vy = U0 * (-R**2 * 2.0 * dx * dy / (r2**2))
        
        if dx > 0:
            wake_intensity = min(1.0, R / (dx + R)) * np.exp(-(dy**2)/(2 * (R*2)**2))
            vortex = np.sin(dx * 0.02 - t * 2) * np.cos(dy * 0.01)
            vx += wake_intensity * vortex * 5.0
            vy += wake_intensity * np.cos(dx * 0.02 - t * 2) * 10.0
            
            nx = py5.os_noise(x * noise_scale, y * noise_scale, t) - 0.5
            ny = py5.os_noise(x * noise_scale + 100, y * noise_scale, t) - 0.5
            vx += nx * 5.0 * wake_intensity
            vy += ny * 5.0 * wake_intensity
            
        particles[i, 0] += vx
        particles[i, 1] += vy
        
        speed = np.sqrt(vx**2 + vy**2)
        hue = (180 + speed * 10) % 360
        alpha = 20 + 30 * np.sin(particles[i, 3] + t * 5)
        if alpha > 0:
            py5.fill(hue, 90, 90, alpha)
            py5.ellipse(particles[i, 0], particles[i, 1], 2, 2)
            
        if particles[i, 0] > SIZE[0] + 100 or particles[i, 1] < -100 or particles[i, 1] > SIZE[1] + 100:
            particles[i, 0] = np.random.uniform(-200, -50)
            particles[i, 1] = np.random.uniform(0, SIZE[1])
            
    py5.blend_mode(py5.BLEND)
    py5.fill(0)
    py5.stroke(180, 80, 80, 50)
    py5.stroke_weight(2)
    py5.ellipse(cx, cy, R*2, R*2)

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
