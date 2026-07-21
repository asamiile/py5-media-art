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

NUM_PARTICLES = 60000

# We map the screen to a mathematical plate from x=[-1, 1] and y=[-1, 1]
# But wait, aspect ratio is 16:9, so x=[-1.777, 1.777] and y=[-1, 1]
ASPECT = SIZE[0] / SIZE[1]

# Particles coordinates in mathematical space
px = np.random.uniform(-ASPECT, ASPECT, NUM_PARTICLES).astype(np.float32)
py = np.random.uniform(-1.0, 1.0, NUM_PARTICLES).astype(np.float32)
vx = np.zeros(NUM_PARTICLES, dtype=np.float32)
vy = np.zeros(NUM_PARTICLES, dtype=np.float32)

def chladni_gradient(x, y, n, m, a, b):
    # Calculates the gradient of the Chladni equation
    # C(x, y) = a * sin(n*pi*x)*sin(m*pi*y) + b * sin(m*pi*x)*sin(n*pi*y)
    # The gradient is the slope. Particles move AWAY from high absolute values of C(x,y).
    # Specifically, they are pushed down the gradient of C^2.
    # d(C^2)/dx = 2 * C * dC/dx
    
    n_pi = n * np.pi
    m_pi = m * np.pi
    
    sin_nx = np.sin(n_pi * x)
    cos_nx = np.cos(n_pi * x)
    sin_ny = np.sin(n_pi * y)
    cos_ny = np.cos(n_pi * y)
    
    sin_mx = np.sin(m_pi * x)
    cos_mx = np.cos(m_pi * x)
    sin_my = np.sin(m_pi * y)
    cos_my = np.cos(m_pi * y)
    
    C = a * sin_nx * sin_my + b * sin_mx * sin_ny
    
    dC_dx = a * n_pi * cos_nx * sin_my + b * m_pi * cos_mx * sin_ny
    dC_dy = a * m_pi * sin_nx * cos_my + b * n_pi * sin_mx * cos_ny
    
    # We want to push particles AWAY from vibration antinodes (high C^2)
    # So force is proportional to -grad(C^2)
    fx = -2 * C * dC_dx
    fy = -2 * C * dC_dy
    
    return fx, fy

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    # Additive blend mode to make dense sand glow
    py5.blend_mode(py5.ADD)

def draw():
    global px, py, vx, vy
    
    # Draw dark background to fade tails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Animate parameters
    t = py5.frame_count * 0.005
    # Morph frequencies slowly
    n = 3.0 + np.sin(t * 0.7) * 2.0
    m = 5.0 + np.cos(t * 0.5) * 3.0
    a = 1.0
    b = 1.0 # np.sin(t * 0.3)
    
    # Calculate force from Chladni plate vibrations
    fx, fy = chladni_gradient(px, py, n, m, a, b)
    
    # Add random Brownian motion / vibration so they don't get stuck perfectly on the line
    vibration_strength = 0.1
    fx += np.random.normal(0, vibration_strength, NUM_PARTICLES)
    fy += np.random.normal(0, vibration_strength, NUM_PARTICLES)
    
    # Update velocities (with friction/damping)
    dt = 0.01
    vx = vx * 0.85 + fx * dt
    vy = vy * 0.85 + fy * dt
    
    px += vx * dt
    py += vy * dt
    
    # Boundary reflection
    hit_left = px < -ASPECT
    hit_right = px > ASPECT
    px[hit_left] = -ASPECT
    px[hit_right] = ASPECT
    vx[hit_left] *= -1
    vx[hit_right] *= -1
    
    hit_top = py < -1.0
    hit_bottom = py > 1.0
    py[hit_top] = -1.0
    py[hit_bottom] = 1.0
    vy[hit_top] *= -1
    vy[hit_bottom] *= -1
    
    # Map to screen space
    sx = (px + ASPECT) / (2 * ASPECT) * py5.width
    sy = (py + 1.0) / 2.0 * py5.height
    
    # Draw points
    py5.stroke(45, 80, 100, 40) # golden yellow
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        py5.vertex(sx[i], sy[i])
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
        import os
        os._exit(0)

py5.run_sketch()
