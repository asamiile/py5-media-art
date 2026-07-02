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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
NUM_PARTICLES = 300000

# State
points = np.zeros((NUM_PARTICLES, 2))
colors = np.zeros((NUM_PARTICLES, 3), dtype=np.uint8)

# Flow field parameters
NUM_HARMONICS = 10
amplitudes = np.random.uniform(0.1, 1.0, NUM_HARMONICS)
kx = np.random.uniform(0.5, 4.0, NUM_HARMONICS)
ky = np.random.uniform(0.5, 4.0, NUM_HARMONICS)
phase_x = np.random.uniform(0, np.pi*2, NUM_HARMONICS)
phase_y = np.random.uniform(0, np.pi*2, NUM_HARMONICS)

# Time evolution speeds
speed_t = np.random.uniform(0.01, 0.05, NUM_HARMONICS)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize randomly
    points[:, 0] = np.random.uniform(0, SIZE[0], NUM_PARTICLES)
    points[:, 1] = np.random.uniform(0, SIZE[1], NUM_PARTICLES)
    
    # Random colors from a palette
    c_idx = np.random.randint(0, 3, NUM_PARTICLES)
    
    # Cyan, Gold, Purple
    colors[c_idx == 0] = [0, 255, 200]
    colors[c_idx == 1] = [255, 200, 0]
    colors[c_idx == 2] = [150, 0, 255]

def draw():
    # Motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 5, 10, 15) # Very dark blue with high transparency
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count
    dt = 2.0
    
    # Normalized coordinates [-1, 1] for math
    nx = (points[:, 0] / SIZE[0]) * 2.0 - 1.0
    ny = (points[:, 1] / SIZE[1]) * 2.0 - 1.0
    
    vx = np.zeros(NUM_PARTICLES)
    vy = np.zeros(NUM_PARTICLES)
    
    # Calculate analytical curl of scalar potential Psi
    # Psi = sum( A * sin(kx*x + phase_x) * sin(ky*y + phase_y) )
    # vx = dPsi/dy = sum( A * ky * sin(kx*x) * cos(ky*y) )
    # vy = -dPsi/dx = sum( -A * kx * cos(kx*x) * sin(ky*y) )
    
    for i in range(NUM_HARMONICS):
        px = kx[i] * nx + phase_x[i] + t * speed_t[i]
        py_ = ky[i] * ny + phase_y[i] + t * speed_t[i] * 1.3
        
        A = amplitudes[i]
        
        vx += A * ky[i] * np.sin(px) * np.cos(py_)
        vy += -A * kx[i] * np.cos(px) * np.sin(py_)

    # Update positions
    # Scale back to screen space speed
    points[:, 0] += vx * dt * (SIZE[0]/SIZE[1]) * 2.0
    points[:, 1] += vy * dt * 2.0
    
    # Wrap around edges seamlessly
    points[:, 0] = np.mod(points[:, 0], SIZE[0])
    points[:, 1] = np.mod(points[:, 1], SIZE[1])

    py5.stroke_weight(2.0)
    
    # Draw by color groups
    for i in range(3):
        mask = (colors[:, 0] == ([0, 255, 150][i]))
        if np.any(mask):
            c = colors[mask][0]
            py5.stroke(int(c[0]), int(c[1]), int(c[2]), 40)
            pts = points[mask]
            py5.begin_shape(py5.POINTS)
            py5.vertices(pts)
            py5.end_shape()

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
