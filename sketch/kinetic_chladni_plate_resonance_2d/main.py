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

# Physics settings
NUM_PARTICLES = 100000
VIBRATION_INTENSITY = 0.06
PARTICLE_SPEED = 0.12
EPSILON = 0.001

# Normalize coordinates from screen to -1..1
# It's faster to do math in -1..1 then project
px = np.random.uniform(-1, 1, NUM_PARTICLES)
py = np.random.uniform(-1, 1, NUM_PARTICLES)
vx = np.zeros(NUM_PARTICLES)
vy = np.zeros(NUM_PARTICLES)

def chladni(x, y, n, m):
    # Z = a * sin(n*pi*x) * sin(m*pi*y) + b * sin(m*pi*x) * sin(n*pi*y)
    # Using a=1, b=1 for simplicity
    pi = np.pi
    return np.sin(n * pi * x) * np.sin(m * pi * y) + np.sin(m * pi * x) * np.sin(n * pi * y)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global px, py, vx, vy
    
    # Motion blur / Trail effect
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 80, 8, 30) # Very dark crimson trail
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # We want to smoothly interpolate between different resonant modes.
    # We'll define a few keyframes for (n, m) pairs.
    modes = [(2, 3), (3, 5), (4, 4), (5, 7), (2, 3)]
    num_segments = len(modes) - 1
    
    segment = int(t * num_segments)
    if segment >= num_segments:
        segment = num_segments - 1
        
    local_t = (t * num_segments) - segment
    
    # Ease in-out interpolation for smooth transitions
    ease_t = local_t * local_t * (3 - 2 * local_t) 
    
    n_curr, m_curr = modes[segment]
    n_next, m_next = modes[segment + 1]
    
    n = n_curr + (n_next - n_curr) * ease_t
    m = m_curr + (m_next - m_curr) * ease_t

    # Calculate gradients of the Chladni function to move particles
    # We want particles to move towards Z=0 (nodal lines), so we move down the gradient of abs(Z)
    z = chladni(px, py, n, m)
    
    # Numerical derivative
    zx = chladni(px + EPSILON, py, n, m)
    zy = chladni(px, py + EPSILON, n, m)
    
    dzdx = (zx - z) / EPSILON
    dzdy = (zy - z) / EPSILON
    
    # For Z near zero, abs(Z) gradient is dz * sign(z)
    grad_x = dzdx * np.sign(z)
    grad_y = dzdy * np.sign(z)
    
    # Apply forces
    vx -= grad_x * PARTICLE_SPEED
    vy -= grad_y * PARTICLE_SPEED
    
    # Add random vibration noise proportional to the absolute amplitude Z
    # Particles vibrate violently at antinodes, but settle down at nodes
    vibration_x = np.random.uniform(-1, 1, NUM_PARTICLES) * np.abs(z) * VIBRATION_INTENSITY
    vibration_y = np.random.uniform(-1, 1, NUM_PARTICLES) * np.abs(z) * VIBRATION_INTENSITY
    
    vx += vibration_x
    vy += vibration_y
    
    # Friction
    vx *= 0.8
    vy *= 0.8
    
    px += vx
    py += vy
    
    # Bouncing off walls
    mask_x = np.abs(px) > 1.0
    px[mask_x] = np.sign(px[mask_x]) * 1.0
    vx[mask_x] *= -0.5
    
    mask_y = np.abs(py) > 1.0
    py[mask_y] = np.sign(py[mask_y]) * 1.0
    vy[mask_y] *= -0.5

    # Map to screen coordinates
    # We'll map -1.2 to 1.2 so they fill the screen edge to edge nicely
    screen_x = (px + 1.2) / 2.4 * py5.width
    screen_y = (py + 1.2) / 2.4 * py5.height
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    # Draw points using raw rendering for speed
    py5.stroke(45, 70, 90, 40) # Gold / Bronze
    py5.points(np.column_stack((screen_x, screen_y)))

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%) | Mode: ({n:.2f}, {m:.2f})")

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
