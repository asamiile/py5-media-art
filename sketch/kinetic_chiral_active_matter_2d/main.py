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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Active matter simulation parameters
N = 3500
L = 100.0 # Box size
R = 4.0 # Interaction radius
v0 = 1.2 # Self-propulsion speed
dt = 0.5
noise_std = 0.12

# Torque: half clockwise, half counter-clockwise
omega0 = 0.35
omega = np.ones(N) * omega0
omega[N//2:] = -omega0

# State variables
pos = None
theta = None
density = None
neighbors = None

def setup():
    global pos, theta
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    np.random.seed(random.randint(0, 10000))
    pos = np.random.uniform(0, L, size=(N, 2))
    theta = np.random.uniform(-np.pi, np.pi, size=N)

def step_simulation():
    global pos, theta, density, neighbors
    
    # 1. Update positions
    v = v0 * np.stack([np.cos(theta), np.sin(theta)], axis=-1)
    pos += v * dt
    pos %= L
    
    # 2. Distance matrix calculation with periodic wrapping
    dx = pos[:, None, 0] - pos[None, :, 0]
    dy = pos[:, None, 1] - pos[None, :, 1]
    
    dx = dx - L * np.round(dx / L)
    dy = dy - L * np.round(dy / L)
    
    dist2 = dx**2 + dy**2
    neighbors = dist2 < R**2
    
    # 3. Align orientation with neighbors
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)
    
    sum_sin = np.sum(neighbors * sin_theta[None, :], axis=1)
    sum_cos = np.sum(neighbors * cos_theta[None, :], axis=1)
    
    mean_theta = np.arctan2(sum_sin, sum_cos)
    
    # 4. Update angles with alignment + torque + noise
    theta = mean_theta + omega * dt + np.random.normal(0, noise_std, size=N)
    
    # Calculate density for color mapping
    density = np.sum(neighbors, axis=1)

def draw():
    step_simulation()
    
    # Decay trails using a translucent black rectangle
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Additive blending for glowing particles
    py5.blend_mode(py5.ADD)
    
    scale_x = py5.width / L
    scale_y = py5.height / L
    
    scaled_pos = pos * [scale_x, scale_y]
    
    # Classify particles
    cw_mask = (omega > 0) & (density <= 12)
    ccw_mask = (omega < 0) & (density <= 12)
    dense_mask = density > 12
    
    # 1. Draw clockwise particles (Amber)
    if np.any(cw_mask):
        py5.stroke(255, 179, 0, 120)
        py5.stroke_weight(2.0)
        py5.points(scaled_pos[cw_mask])
        
    # 2. Draw counter-clockwise particles (Neon Teal)
    if np.any(ccw_mask):
        py5.stroke(0, 229, 255, 120)
        py5.stroke_weight(2.0)
        py5.points(scaled_pos[ccw_mask])
        
    # 3. Draw dense clusters / mills (Electric Pink)
    if np.any(dense_mask):
        py5.stroke(255, 0, 127, 200)
        py5.stroke_weight(3.5)
        py5.points(scaled_pos[dense_mask])

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if blank screen
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels[:, :, :3].std() < 0.5:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 0.5). Aborting.")
            import os
            os._exit(1)

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # End sketch and build video
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
