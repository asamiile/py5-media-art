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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle settings
NUM_PARTICLES = 40000
particles = None
ages = None
max_age = 150

# Dipole settings
NUM_DIPOLES = 10
dipoles = None

def setup():
    global particles, ages, dipoles
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(5, 5, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    particles = np.random.rand(NUM_PARTICLES, 2)
    particles[:, 0] *= SIZE[0]
    particles[:, 1] *= SIZE[1]
    
    ages = np.random.randint(0, max_age, NUM_PARTICLES)
    
    # Init dipoles: x, y, dx, dy, moment_x, moment_y
    dipoles = np.zeros((NUM_DIPOLES, 6))
    dipoles[:, 0] = np.random.rand(NUM_DIPOLES) * SIZE[0]
    dipoles[:, 1] = np.random.rand(NUM_DIPOLES) * SIZE[1]
    dipoles[:, 2] = (np.random.rand(NUM_DIPOLES) - 0.5) * 4
    dipoles[:, 3] = (np.random.rand(NUM_DIPOLES) - 0.5) * 4
    angles = np.random.rand(NUM_DIPOLES) * 2 * np.pi
    dipoles[:, 4] = np.cos(angles) * 1e8
    dipoles[:, 5] = np.sin(angles) * 1e8

def draw():
    global particles, ages, dipoles
    
    # Fading background for trails
    py5.no_stroke()
    py5.fill(5, 5, 10, 10)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Update dipoles
    dipoles[:, 0] += dipoles[:, 2]
    dipoles[:, 1] += dipoles[:, 3]
    
    # Bounce dipoles
    mask_x = (dipoles[:, 0] < 0) | (dipoles[:, 0] > SIZE[0])
    dipoles[mask_x, 2] *= -1
    mask_y = (dipoles[:, 1] < 0) | (dipoles[:, 1] > SIZE[1])
    dipoles[mask_y, 3] *= -1
    
    # Calculate magnetic field at particle positions
    # B = (mu0 / 4pi) * (3 * (m . r_hat) * r_hat - m) / r^3
    # We will use an optimized vectorized approximation for speed.
    bx = np.zeros(NUM_PARTICLES)
    by = np.zeros(NUM_PARTICLES)
    
    for i in range(NUM_DIPOLES):
        dx = particles[:, 0] - dipoles[i, 0]
        dy = particles[:, 1] - dipoles[i, 1]
        
        r2 = dx*dx + dy*dy
        r2[r2 < 1000] = 1000 # Avoid singularities
        
        r5 = r2 * r2 * np.sqrt(r2)
        
        m_dot_r = dipoles[i, 4] * dx + dipoles[i, 5] * dy
        
        bx += (3 * m_dot_r * dx / r2 - dipoles[i, 4]) / r5
        by += (3 * m_dot_r * dy / r2 - dipoles[i, 5]) / r5

    # Normalize B field to get velocities
    b_mag = np.sqrt(bx*bx + by*by)
    b_mag[b_mag == 0] = 1
    vx = bx / b_mag * 12
    vy = by / b_mag * 12

    # Update particles
    particles[:, 0] += vx
    particles[:, 1] += vy
    ages += 1
    
    # Respawn old or out-of-bounds particles
    out_bounds = (particles[:, 0] < 0) | (particles[:, 0] > SIZE[0]) | (particles[:, 1] < 0) | (particles[:, 1] > SIZE[1])
    dead = (ages > max_age) | out_bounds
    num_dead = np.sum(dead)
    
    if num_dead > 0:
        particles[dead, 0] = np.random.rand(num_dead) * SIZE[0]
        particles[dead, 1] = np.random.rand(num_dead) * SIZE[1]
        ages[dead] = 0

    # Draw particles natively
    # Bin by age for color mapping
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        a = ages[i]
        alpha = int(255 * np.sin((a / max_age) * np.pi))
        py5.stroke(200, 150, 50, alpha) # Gold / Bronze
        py5.vertex(particles[i, 0], particles[i, 1])
    py5.end_shape()

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
