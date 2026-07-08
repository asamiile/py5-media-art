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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 150
TRAIL_LENGTH = 120

# Arrays to store current pos and history
pts = np.zeros((NUM_PARTICLES, 3))
history = np.zeros((NUM_PARTICLES, TRAIL_LENGTH, 3))
colors = np.zeros((NUM_PARTICLES, 3))

# Lorenz parameters
sigma = 10.0
rho = 28.0
beta = 8.0 / 3.0
dt = 0.005

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(5, 10, 20)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    
    # Initialize particles near slightly different starting points
    for i in range(NUM_PARTICLES):
        pts[i] = [
            random.uniform(0.1, 1.1),
            random.uniform(0.1, 1.1),
            random.uniform(0.1, 1.1)
        ]
        
        # Color gradient based on index
        t_col = i / NUM_PARTICLES
        # Interpolate between cyan and magenta
        r = py5.lerp(0, 255, t_col)
        g = py5.lerp(255, 50, t_col)
        b = 255
        colors[i] = [r, g, b]
        
        # fill history
        for j in range(TRAIL_LENGTH):
            history[i, j] = pts[i]

def draw():
    # Motion blur / fading
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 10, 20, 60)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    # Update simulation
    # To speed things up, we can do multiple steps per frame
    steps_per_frame = 3
    
    for _ in range(steps_per_frame):
        x = pts[:, 0]
        y = pts[:, 1]
        z = pts[:, 2]
        
        dx = sigma * (y - x) * dt
        dy = (x * (rho - z) - y) * dt
        dz = (x * y - beta * z) * dt
        
        pts[:, 0] += dx
        pts[:, 1] += dy
        pts[:, 2] += dz
        
    # Shift history
    history[:, 1:] = history[:, :-1]
    history[:, 0] = pts
    
    t = py5.frame_count * 0.01
    rx = t * 0.4
    ry = t * 0.7
    
    # Rotation matrices
    mx = np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx), np.cos(rx)]
    ])
    my = np.array([
        [np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)]
    ])
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2 + 100)
    
    scale_factor = 25.0
    
    py5.no_fill()
    py5.stroke_weight(2.0)
    
    for i in range(NUM_PARTICLES):
        c = colors[i]
        
        # Draw trail
        py5.begin_shape()
        for j in range(TRAIL_LENGTH):
            # Fade alpha over the trail
            alpha = py5.remap(j, 0, TRAIL_LENGTH-1, 200, 0)
            py5.stroke(c[0], c[1], c[2], alpha)
            
            p = history[i, j]
            # Center the attractor roughly around z=25
            p_centered = np.array([p[0], p[1], p[2] - 25.0])
            
            # Rotate
            rotated = my @ (mx @ p_centered)
            
            # Project
            z_proj = rotated[2]
            f = 800 / (800 - z_proj) if (800 - z_proj) != 0 else 1
            px = rotated[0] * scale_factor * f
            py_coord = rotated[1] * scale_factor * f
            
            py5.vertex(px, py_coord)
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
