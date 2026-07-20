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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Use a high number of particles with vectorized math for performance
NUM_PARTICLES = 30000

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 80, 15)
    
    global pos, vel, ages, max_ages, colors
    pos = np.random.uniform(0, max(SIZE), (NUM_PARTICLES, 2))
    pos[:, 0] = np.random.uniform(0, py5.width, NUM_PARTICLES)
    pos[:, 1] = np.random.uniform(0, py5.height, NUM_PARTICLES)
    vel = np.zeros((NUM_PARTICLES, 2))
    
    ages = np.random.randint(0, 100, NUM_PARTICLES)
    max_ages = np.random.randint(50, 200, NUM_PARTICLES)
    
    # Store initial hues to keep colors somewhat coherent
    colors = np.random.uniform(180, 300, NUM_PARTICLES) # Blues, Cyans, Purples

def get_noise_vector_field(x, y, t):
    # Scale down coordinates for noise sampling
    noise_scale = 0.002
    x_scaled = x * noise_scale
    y_scaled = y * noise_scale
    t_scaled = t * 2.0
    
    # Instead of generating 30k py5.noise calls which is slow, we use a simple vectorized math formula simulating a fluid flow
    # that evolves over time.
    angle = np.sin(x_scaled * 3.0 + t_scaled) * np.cos(y_scaled * 3.0) * py5.TWO_PI * 2.0
    angle += np.sin(y_scaled * 2.0 - t_scaled * 1.5) * py5.PI
    
    # Add a swirl based on distance to center
    cx, cy = py5.width / 2, py5.height / 2
    dx, dy = x - cx, y - cy
    dist = np.hypot(dx, dy)
    swirl_angle = np.arctan2(dy, dx) + py5.PI / 2
    swirl_strength = np.exp(-dist / 1000.0)
    
    final_angle = angle * (1 - swirl_strength) + swirl_angle * swirl_strength
    
    vx = np.cos(final_angle)
    vy = np.sin(final_angle)
    
    return vx, vy

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # Subtle fade out for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 80, 15, 8)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    global pos, vel, ages, max_ages, colors
    
    # Vectorized update
    vx, vy = get_noise_vector_field(pos[:, 0], pos[:, 1], t)
    
    vel[:, 0] = vel[:, 0] * 0.95 + vx * 0.5
    vel[:, 1] = vel[:, 1] * 0.95 + vy * 0.5
    
    # Speed limit
    speed = np.hypot(vel[:, 0], vel[:, 1])
    max_speed = 8.0
    overspeed = speed > max_speed
    vel[overspeed, 0] = (vel[overspeed, 0] / speed[overspeed]) * max_speed
    vel[overspeed, 1] = (vel[overspeed, 1] / speed[overspeed]) * max_speed
    
    pos += vel
    ages += 1
    
    # Find dead particles or those out of bounds
    out_of_bounds = (pos[:, 0] < 0) | (pos[:, 0] > py5.width) | (pos[:, 1] < 0) | (pos[:, 1] > py5.height)
    dead = (ages > max_ages) | out_of_bounds
    
    # Respawn dead particles
    num_dead = np.sum(dead)
    if num_dead > 0:
        pos[dead, 0] = np.random.uniform(0, py5.width, num_dead)
        pos[dead, 1] = np.random.uniform(0, py5.height, num_dead)
        vel[dead] = 0
        ages[dead] = 0
        max_ages[dead] = np.random.randint(50, 200, num_dead)
        colors[dead] = np.random.uniform(180, 300, num_dead)
        
    # Draw points. py5.points() expects a Nx2 numpy array, which is blazing fast!
    py5.stroke(180, 50, 100, 40)
    py5.stroke_weight(3)
    
    # To draw multi-colored points efficiently in py5 without a loop, we can group them by color bins
    # Or just use a single color for this layer, but we can do a couple layers.
    c1 = (180 + t * 90) % 360
    c2 = (250 + t * 90) % 360
    
    mask1 = colors < 240
    mask2 = ~mask1
    
    py5.stroke(c1, 80, 100, 30)
    if np.any(mask1):
        py5.points(pos[mask1])
        
    py5.stroke(c2, 80, 100, 30)
    if np.any(mask2):
        py5.points(pos[mask2])
    
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
        import os
        os._exit(0)

py5.run_sketch()
