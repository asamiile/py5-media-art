from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 30000

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    
    global p_pos, p_vel
    # Initial random distribution
    p_pos = np.random.rand(NUM_PARTICLES, 2) * [SIZE[0], SIZE[1]]
    p_vel = np.zeros((NUM_PARTICLES, 2))

def draw():
    global p_pos, p_vel
    py5.background(5, 50)  # Slight trail
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    # Chladni parameters
    n = 3.0 + py5.sin(t * 0.2) * 1.5
    m = 4.0 + py5.cos(t * 0.3) * 1.5
    
    # Vectorized gradient calculation for Chladni
    # Chladni eq: cos(n*pi*x/L) * cos(m*pi*y/L) - cos(m*pi*x/L) * cos(n*pi*y/L)
    L = py5.width / 2
    
    # Shift coordinates to center
    x = (p_pos[:, 0] - L) / L
    y = (p_pos[:, 1] - py5.height/2) / L
    
    # To find nodes (where eq = 0), we push particles towards minima of the squared equation
    # Approximate gradient descent towards nodal lines
    
    c_nx = np.cos(n * np.pi * x)
    c_my = np.cos(m * np.pi * y)
    c_mx = np.cos(m * np.pi * x)
    c_ny = np.cos(n * np.pi * y)
    
    s_nx = np.sin(n * np.pi * x)
    s_my = np.sin(m * np.pi * y)
    s_mx = np.sin(m * np.pi * x)
    s_ny = np.sin(n * np.pi * y)
    
    # Function value
    Z = c_nx * c_my - c_mx * c_ny
    
    # Partial derivatives (ignoring pi/L factor for scaling)
    dZ_dx = -n * s_nx * c_my + m * s_mx * c_ny
    dZ_dy = -m * c_nx * s_my + n * c_mx * s_ny
    
    # We want to minimize Z^2, so gradient is 2 * Z * dZ
    force_x = -Z * dZ_dx * 2.0
    force_y = -Z * dZ_dy * 2.0
    
    p_vel[:, 0] += force_x
    p_vel[:, 1] += force_y
    
    # Friction
    p_vel *= 0.8
    
    # Update positions
    p_pos += p_vel
    
    # Random jiggle to keep them from getting perfectly stuck
    p_pos += np.random.randn(NUM_PARTICLES, 2) * 2.0
    
    # Boundary reflection
    hit_left = p_pos[:, 0] < 0
    hit_right = p_pos[:, 0] > py5.width
    p_vel[hit_left | hit_right, 0] *= -1
    p_pos[:, 0] = np.clip(p_pos[:, 0], 0, py5.width)
    
    hit_top = p_pos[:, 1] < 0
    hit_bottom = p_pos[:, 1] > py5.height
    p_vel[hit_top | hit_bottom, 1] *= -1
    p_pos[:, 1] = np.clip(p_pos[:, 1], 0, py5.height)

    # Draw particles
    hue = (t * 10) % 360
    py5.stroke(hue, 80, 90, 80)
    py5.stroke_weight(2)
    
    # Fast drawing with Py5 shape points
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        py5.vertex(p_pos[i, 0], p_pos[i, 1])
    py5.end_shape()

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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
