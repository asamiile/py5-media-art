from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
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

N_PARTICLES = 100000

# Initialize in a disc
r = np.random.uniform(0, 800, N_PARTICLES).astype(np.float32)
theta = np.random.uniform(0, math.pi * 2, N_PARTICLES).astype(np.float32)

px = (np.cos(theta) * r + SIZE[0]/2).astype(np.float32)
py = (np.sin(theta) * r + SIZE[1]/2).astype(np.float32)

vx = np.zeros(N_PARTICLES, dtype=np.float32)
vy = np.zeros(N_PARTICLES, dtype=np.float32)

# Colors based on initial radius
colors_r = (np.clip(255 - r * 0.3, 0, 255)).astype(np.uint8)
colors_g = (np.clip(100 + np.sin(r * 0.01) * 100, 0, 255)).astype(np.uint8)
colors_b = (np.clip(200 + np.cos(r * 0.02) * 55, 0, 255)).astype(np.uint8)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(5, 0, 10)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global px, py, vx, vy
    
    # Trails fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 0, 10, 30)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    cx, cy = SIZE[0]/2, SIZE[1]/2
    
    # Physics update
    dx = cx - px
    dy = cy - py
    dist_sq = dx**2 + dy**2 + 1000.0  # soft core to prevent singularity
    
    # Gravity well force
    force = 200000.0 / dist_sq
    
    # Core repulsion to prevent singularity collapse
    repulsion = 500000.0 / (dist_sq * 0.05 + 1.0)
    
    # Total radial force
    net_force = force - repulsion
    
    # Radial vector
    dist = np.sqrt(dist_sq)
    gx = (dx / dist) * net_force
    gy = (dy / dist) * net_force
    
    # Vortex force (perpendicular to radial)
    # Adds spin
    vortex_strength = 2.5
    tx = -gy * vortex_strength
    ty = gx * vortex_strength
    
    # Noise turbulence
    t = py5.frame_count * 0.01
    turb_x = py5.os_noise(px * 0.002, py * 0.002, t) * 2 - 1
    turb_y = py5.os_noise(px * 0.002 + 100, py * 0.002 + 100, t) * 2 - 1
    
    vx += gx + tx + turb_x * 2.0
    vy += gy + ty + turb_y * 2.0
    
    # Drag
    vx *= 0.96
    vy *= 0.96
    
    px += vx
    py += vy
    
    # Fast rendering
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    py5.begin_shape(py5.POINTS)
    for i in range(N_PARTICLES):
        py5.stroke(colors_r[i], colors_g[i], colors_b[i], 180)
        py5.vertex(px[i], py[i])
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
