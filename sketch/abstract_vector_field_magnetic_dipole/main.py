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

NUM_PARTICLES = 30000

# NumPy arrays for vectorized physics
pos = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
age = np.zeros(NUM_PARTICLES, dtype=np.int32)
max_age = np.random.randint(50, 150, size=NUM_PARTICLES)

def reset_particles(mask):
    count = np.sum(mask)
    if count == 0: return
    # Start particles near the poles or randomly
    pos[mask, 0] = np.random.uniform(0, SIZE[0], size=count)
    pos[mask, 1] = np.random.uniform(0, SIZE[1], size=count)
    vel[mask] = 0
    age[mask] = 0
    max_age[mask] = np.random.randint(50, 150, size=count)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(5)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initial spawn
    reset_particles(np.ones(NUM_PARTICLES, dtype=bool))
    
def draw():
    global pos, vel, age
    # Motion blur instead of clearing
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    # Define magnetic dipoles (poles) moving in Lissajous curves
    poles = np.array([
        [py5.width/2 + py5.cos(t * 0.7) * 400, py5.height/2 + py5.sin(t * 0.4) * 300, 1.0],   # Positive
        [py5.width/2 + py5.sin(t * 0.5) * 400, py5.height/2 + py5.cos(t * 0.6) * 300, -1.0],  # Negative
        [py5.width/2 + py5.cos(t * 1.1) * 200, py5.height/2 + py5.sin(t * 1.3) * 200, 0.5],   # Weak Positive
        [py5.width/2 + py5.sin(t * 0.9) * 200, py5.height/2 + py5.cos(t * 0.8) * 200, -0.5]   # Weak Negative
    ])
    
    # Calculate vector field force for all particles simultaneously using NumPy broadcasting
    px = pos[:, 0]
    py_c = pos[:, 1]
    
    force_x = np.zeros(NUM_PARTICLES, dtype=np.float32)
    force_y = np.zeros(NUM_PARTICLES, dtype=np.float32)
    
    for pole in poles:
        dx = pole[0] - px
        dy = pole[1] - py_c
        charge = pole[2]
        
        dist_sq = dx*dx + dy*dy
        # Prevent division by zero
        dist_sq = np.maximum(dist_sq, 100.0)
        
        # Magnetic force falls off with square of distance
        # Force vector points away from positive, towards negative
        f = charge * 5000.0 / dist_sq
        
        force_x -= f * dx / np.sqrt(dist_sq)
        force_y -= f * dy / np.sqrt(dist_sq)
        
    # Add a bit of Perlin noise for turbulence
    # We approximate noise over the field using numpy to avoid slow py5.noise in loop
    turb_x = np.sin(px * 0.01 + t) * np.cos(py_c * 0.01 - t)
    turb_y = np.cos(px * 0.01 - t) * np.sin(py_c * 0.01 + t)
    
    vel[:, 0] += force_x + turb_x * 0.5
    vel[:, 1] += force_y + turb_y * 0.5
    
    # Apply friction limit
    speed = np.sqrt(vel[:, 0]**2 + vel[:, 1]**2)
    vel[speed > 8] = (vel[speed > 8].T / speed[speed > 8] * 8).T
    
    # Update positions
    old_pos = pos.copy()
    pos += vel
    
    # Aging
    age += 1
    
    # Check bounds and lifespan
    dead = (pos[:, 0] < 0) | (pos[:, 0] > py5.width) | (pos[:, 1] < 0) | (pos[:, 1] > py5.height) | (age > max_age)
    reset_particles(dead)
    
    # Render
    py5.stroke_weight(1.5)
    
    # Color depends on speed
    hue = (220 + speed * 15) % 360
    
    for i in range(NUM_PARTICLES):
        if not dead[i]:
            a = min(100, (max_age[i] - age[i]) * 2)
            a = min(a, age[i] * 5) # Fade in and out
            
            py5.stroke(hue[i], 80, 80, a)
            py5.line(old_pos[i, 0], old_pos[i, 1], pos[i, 0], pos[i, 1])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
