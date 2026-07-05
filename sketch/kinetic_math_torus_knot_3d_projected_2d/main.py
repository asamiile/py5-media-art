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

# Torus Knot parameters
# p and q determine the knot shape
p = 3
q = 7
NUM_POINTS = 8000

# Generate base curve
t = np.linspace(0, 2 * np.pi * p, NUM_POINTS)
# Torus knot equations
r = 200 + 80 * np.cos(q * t / p)
base_x = r * np.cos(t)
base_y = r * np.sin(t)
base_z = 80 * np.sin(q * t / p)

base_points = np.column_stack((base_x, base_y, base_z))

# We want to make it a thick "tube". We can just draw circles at these points,
# or better, add some noise or smaller orbital points to make it voluminous.
# Let's create a bundle of strands.
num_strands = 10
strand_points = []
strand_colors = []

for s in range(num_strands):
    angle_offset = s * (2 * np.pi / num_strands)
    # offset each strand slightly from the center
    ox = 30 * np.cos(t * 15 + angle_offset)
    oy = 30 * np.sin(t * 15 + angle_offset)
    oz = 30 * np.cos(t * 7 + angle_offset) # some 3D twist
    
    pts = base_points.copy()
    pts[:, 0] += ox
    pts[:, 1] += oy
    pts[:, 2] += oz
    strand_points.append(pts)
    
    # Assign a color per strand, or gradient along t
    strand_colors.append(np.linspace(0, 1, NUM_POINTS) + s * 0.1)

all_points = np.vstack(strand_points)
all_colors = np.concatenate(strand_colors) % 1.0

def get_rotation_matrix_3d(rx, ry, rz):
    # X rotation
    cx, sx = np.cos(rx), np.sin(rx)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    # Y rotation
    cy, sy = np.cos(ry), np.sin(ry)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    # Z rotation
    cz, sz = np.cos(rz), np.sin(rz)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 15)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(10, 10, 15)
    
    time_val = py5.frame_count * 0.01
    
    # Dynamic rotation
    rot_x = time_val * 0.5
    rot_y = time_val * 0.7
    rot_z = time_val * 0.3
    
    R = get_rotation_matrix_3d(rot_x, rot_y, rot_z)
    
    # Rotate points
    # all_points is (N, 3). R is (3, 3)
    rotated = all_points @ R.T
    
    # Simple perspective projection
    # Camera at z = -800, looking at +z
    # z is depth
    z_dist = 800.0
    z_vals = rotated[:, 2]
    
    # z_vals range roughly from -300 to 300
    # Add distance
    depth = z_vals + z_dist
    
    # Prevent div by zero
    depth[depth < 1] = 1
    
    # Projection factor (FOV)
    fov = 1200.0
    factor = fov / depth
    
    proj_x = rotated[:, 0] * factor + py5.width / 2
    proj_y = rotated[:, 1] * factor + py5.height / 2
    
    # We want to draw them back-to-front (Painter's algorithm)
    # Sort by z depth (descending depth means further away, so smaller z_vals first? No, camera is at -800. 
    # Larger z is further away. So we sort descending z to draw furthest first.)
    sort_idx = np.argsort(z_vals)[::-1]
    
    sx = proj_x[sort_idx]
    sy = proj_y[sort_idx]
    sz = z_vals[sort_idx]
    sc = all_colors[sort_idx]
    sf = factor[sort_idx]
    
    # Draw points/circles
    # Since we use painter's algorithm, we can't easily vectorize distinct colored shapes in pure py5 without loop
    # or py5.points() (which uses 1 color). We can use create_shape, but rebuilding is slow.
    # A loop of 80000 points doing ellipse() is perfectly fine for rendering (might take ~50ms).
    
    N = len(sx)
    for i in range(N):
        # Base size scaled by perspective
        r_size = 6.0 * sf[i]
        
        # Holographic color
        # sc goes 0 to 1. We map it to shifting hues
        hue = (sc[i] * 360 + sz[i] * 0.5 - time_val * 100) % 360
        
        # Brightness depends on depth (fog effect)
        # depth range ~ 500 to 1100
        depth_val = depth[sort_idx[i]]
        brightness = np.clip(100 - (depth_val - 500) * 0.1, 0, 100)
        
        py5.fill(hue, 70, brightness, 90)
        py5.ellipse(sx[i], sy[i], r_size, r_size)

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
