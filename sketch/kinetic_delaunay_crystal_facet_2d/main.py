from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
from scipy.spatial import Delaunay
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

NUM_POINTS = 1500
pos = None
vel = None

# Palettes
# Deep Ocean (#03045E), Bright Teal (#00B4D8), Aqua (#90E0EF), Soft Pink (#FFB5A7)
# For easier interpolation, we'll map to py5 colors using lerp_color
C1, C2, C3, C4 = None, None, None, None

def setup():
    global pos, vel, C1, C2, C3, C4
    py5.size(*SIZE) # Removed P2D to prevent crash
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    C1 = py5.color(3, 4, 94)
    C2 = py5.color(0, 180, 216)
    C3 = py5.color(144, 224, 239)
    C4 = py5.color(255, 181, 167)
    
    # Initialize points slightly outside the bounds so we don't have empty edges
    margin = 100
    x = np.random.uniform(-margin, py5.width + margin, NUM_POINTS)
    y = np.random.uniform(-margin, py5.height + margin, NUM_POINTS)
    pos = np.column_stack((x, y))
    
    # Velocities
    angle = np.random.uniform(0, np.pi * 2, NUM_POINTS)
    speed = np.random.uniform(0.5, 2.0, NUM_POINTS)
    vx = np.cos(angle) * speed
    vy = np.sin(angle) * speed
    vel = np.column_stack((vx, vy))
    
    # Add static corner points to anchor the triangulation
    corners = np.array([
        [-margin, -margin],
        [py5.width + margin, -margin],
        [-margin, py5.height + margin],
        [py5.width + margin, py5.height + margin]
    ])
    pos = np.vstack((pos, corners))
    vel = np.vstack((vel, np.zeros((4, 2))))
    
    py5.no_stroke()

def get_triangle_color(cx, cy, t):
    # Determine color based on centroid position and time
    # Use noise to create shifting color zones
    scale = 0.001
    n_val = py5.os_noise(cx * scale, cy * scale, t * 2.0)
    
    if n_val < 0.33:
        f = n_val / 0.33
        return py5.lerp_color(C1, C2, f)
    elif n_val < 0.66:
        f = (n_val - 0.33) / 0.33
        return py5.lerp_color(C2, C3, f)
    else:
        f = (n_val - 0.66) / 0.34
        return py5.lerp_color(C3, C4, f)

def draw():
    global pos, vel
    
    py5.background(11, 15, 25) # #0B0F19
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Update positions
    margin = 100
    pos += vel
    
    # Bounce off walls
    mask_x_low = pos[:, 0] < -margin
    mask_x_high = pos[:, 0] > py5.width + margin
    vel[mask_x_low, 0] *= -1
    vel[mask_x_high, 0] *= -1
    pos[mask_x_low, 0] = -margin
    pos[mask_x_high, 0] = py5.width + margin
    
    mask_y_low = pos[:, 1] < -margin
    mask_y_high = pos[:, 1] > py5.height + margin
    vel[mask_y_low, 1] *= -1
    vel[mask_y_high, 1] *= -1
    pos[mask_y_low, 1] = -margin
    pos[mask_y_high, 1] = py5.height + margin
    
    # Compute Delaunay Triangulation
    tri = Delaunay(pos)
    
    # Draw triangles
    py5.begin_shape(py5.TRIANGLES)
    for simplex in tri.simplices:
        # Get vertices
        v1, v2, v3 = pos[simplex]
        
        # Calculate centroid
        cx = (v1[0] + v2[0] + v3[0]) / 3.0
        cy = (v1[1] + v2[1] + v3[1]) / 3.0
        
        # Set fill color based on centroid (flat shading)
        c = get_triangle_color(cx, cy, t)
        py5.fill(c)
        
        py5.vertex(v1[0], v1[1])
        py5.vertex(v2[0], v2[1])
        py5.vertex(v3[0], v3[1])
    py5.end_shape()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_pixels()
        # P2D renderer checks

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
