from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)  # Random duration up to 20s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

particles = None

def setup():
    global particles
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    num_particles = 25000
    
    # [x, y, age, max_age, mass]
    particles = np.zeros((num_particles, 5), dtype=np.float32)
    particles[:, 0] = np.random.rand(num_particles) * SIZE[0]
    particles[:, 1] = np.random.rand(num_particles) * SIZE[1]
    particles[:, 2] = np.random.rand(num_particles) * 150
    particles[:, 3] = np.random.rand(num_particles) * 100 + 100
    particles[:, 4] = np.random.rand(num_particles) * 0.5 + 0.5

def draw():
    global particles
    
    if py5.frame_count == 1:
        py5.background(4, 10, 24) # Very dark blue
        
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(4, 10, 24, 12) # Fading trail
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.003
    
    px = particles[:, 0]
    py = particles[:, 1]
    
    # Base flow rightwards
    vx = np.ones_like(px) * 2.0
    vy = np.zeros_like(py)
    
    # Obstacles
    obstacles = [
        (SIZE[0] * 0.3, SIZE[1] * 0.5, 300),
        (SIZE[0] * 0.6, SIZE[1] * 0.3, 150),
        (SIZE[0] * 0.6, SIZE[1] * 0.7, 150)
    ]
    
    for ox, oy, orad in obstacles:
        dx = px - ox
        dy = py - oy
        dist_sq = dx**2 + dy**2
        
        # Avoid division by zero
        dist_sq = np.maximum(dist_sq, 1.0)
        dist = np.sqrt(dist_sq)
        
        # Repel from cylinder
        force = np.exp(-dist_sq / (orad**2)) * 5.0
        vx += (dx / dist) * force
        vy += (dy / dist) * force
        
        # Vortex shedding (curl) behind the cylinder
        # We add a swirling force that alternates based on time and y-position relative to obstacle
        wake_zone = (dx > 0) & (dx < orad * 6) & (np.abs(dy) < orad * 2)
        
        # Alternating vortex
        vortex_phase = (dx / (orad * 2.0)) - t * 10.0
        swirl = np.sin(vortex_phase) * np.exp(-dx / (orad * 3)) * 2.0
        
        # Upper and lower wake have opposite swirls
        swirl_dir = np.sign(dy)
        
        # Apply perpendicular force in wake
        vx[wake_zone] += -dy[wake_zone] / dist[wake_zone] * swirl[wake_zone] * swirl_dir[wake_zone]
        vy[wake_zone] += dx[wake_zone] / dist[wake_zone] * swirl[wake_zone] * swirl_dir[wake_zone]

    # Add general noise turbulence
    n_s = 0.002
    for i in range(len(px)):
        n1 = py5.noise(px[i]*n_s, py[i]*n_s, t) * py5.TWO_PI * 2
        vx[i] += math.cos(n1) * 0.5
        vy[i] += math.sin(n1) * 0.5
        
    particles[:, 0] += vx * particles[:, 4]
    particles[:, 1] += vy * particles[:, 4]
    particles[:, 2] += 1
    
    # Wrap horizontally, reset if too old or out of bounds vertically
    dead = (particles[:, 2] > particles[:, 3]) | (particles[:, 1] < 0) | (particles[:, 1] > SIZE[1])
    num_dead = np.sum(dead)
    
    if num_dead > 0:
        particles[dead, 0] = np.random.rand(num_dead) * SIZE[0] * 0.1 # Respawn near left edge
        particles[dead, 1] = np.random.rand(num_dead) * SIZE[1]
        particles[dead, 2] = 0
        particles[dead, 3] = np.random.rand(num_dead) * 100 + 100
        
    wrapped = particles[:, 0] > SIZE[0]
    particles[wrapped, 0] -= SIZE[0]
    
    # Draw
    py5.stroke(0, 240, 255, 30) # Cyan
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for i in range(len(px)):
        # Mix some amethyst in based on mass
        if particles[i, 4] > 0.8:
            py5.stroke(96, 32, 160, 40)
        else:
            py5.stroke(0, 240, 255, 30)
        py5.vertex(px[i], py[i])
    py5.end_shape()
    
    # Draw obstacles faintly
    py5.no_stroke()
    py5.fill(0, 0, 0, 50)
    for ox, oy, orad in obstacles:
        py5.ellipse(ox, oy, orad*1.8, orad*1.8)

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
