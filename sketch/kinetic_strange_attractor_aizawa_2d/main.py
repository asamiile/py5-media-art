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

# Aizawa Attractor Parameters
a = 0.95
b = 0.7
c = 0.6
d = 3.5
e = 0.25
f = 0.1
dt = 0.015

NUM_GROUPS = 5
PTS_PER_GROUP = 10000
TOTAL_PTS = NUM_GROUPS * PTS_PER_GROUP

# Initialize particles in a small random cube
pos = np.random.randn(NUM_GROUPS, PTS_PER_GROUP, 3) * 0.1 + np.array([0.1, 0, 0])

# Colors for each group
colors = [
    (0, 255, 255, 40),    # Cyan
    (255, 0, 255, 40),    # Magenta
    (255, 200, 0, 40),    # Gold
    (100, 150, 255, 40),  # Soft Blue
    (255, 255, 255, 40),  # White
]

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(15, 5, 25)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Warm up the simulation so the attractor is fully formed by frame 0
    global pos
    for _ in range(150):
        update_physics()

def update_physics():
    global pos
    x = pos[:, :, 0]
    y = pos[:, :, 1]
    z = pos[:, :, 2]
    
    # Aizawa equations
    dx = (z - b) * x - d * y
    dy = d * x + (z - b) * y
    dz = c + a * z - (z**3) / 3.0 - (x**2 + y**2) * (1 + e * z) + f * z * (x**3)
    
    # Euler integration
    pos[:, :, 0] += dx * dt
    pos[:, :, 1] += dy * dt
    pos[:, :, 2] += dz * dt

def draw():
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(15, 5, 25, 25)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Update simulation
    # Run a few steps per frame to increase visual speed
    for _ in range(3):
        update_physics()
        
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.0)
    
    t = py5.frame_count * 0.005
    
    # Global rotation angles
    theta_y = t * 1.5
    theta_x = t * 0.8
    
    cos_ty = np.cos(theta_y)
    sin_ty = np.sin(theta_y)
    
    cos_tx = np.cos(theta_x)
    sin_tx = np.sin(theta_x)
    
    # Pre-calculate projection scale to fit nicely in 4K resolution
    # The Aizawa attractor bounds are roughly [-2, 2] in all axes
    scale = min(SIZE) * 0.25
    cx = SIZE[0] / 2
    cy = SIZE[1] / 2
    
    # Draw each group
    for i in range(NUM_GROUPS):
        group_pos = pos[i]
        
        # Extract coordinates
        x = group_pos[:, 0]
        y = group_pos[:, 1]
        z = group_pos[:, 2]
        
        # Rotate around Y axis
        rx1 = x * cos_ty - z * sin_ty
        ry1 = y
        rz1 = x * sin_ty + z * cos_ty
        
        # Rotate around X axis
        rx2 = rx1
        ry2 = ry1 * cos_tx - rz1 * sin_tx
        rz2 = ry1 * sin_tx + rz1 * cos_tx
        
        # Project to 2D
        px = rx2 * scale + cx
        # Invert Y to match screen coords
        py = -ry2 * scale + cy
        
        # Stack for py5.points()
        pts_2d = np.column_stack((px, py))
        
        # Color with subtle pulse
        r, g, b, a_base = colors[i]
        pulse = (np.sin(t * 5 + i) + 1) * 0.5
        alpha = a_base + pulse * 40
        
        py5.stroke(r, g, b, alpha)
        py5.points(pts_2d)

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
