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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Lorenz parameters
sigma = 10.0
rho = 28.0
beta = 8.0 / 3.0

def lorenz(state):
    x, y, z = state
    return np.array([sigma * (y - x),
                     x * (rho - z) - y,
                     x * y - beta * z], dtype=np.float32)

# Precompute attractor points
num_points = 200000
dt = 0.005
state = np.array([1.0, 1.0, 1.0], dtype=np.float32)
trajectory = np.zeros((num_points, 3), dtype=np.float32)

print("Integrating Lorenz attractor...")
for i in range(num_points):
    trajectory[i] = state
    state += lorenz(state) * dt

# Center and scale the trajectory
trajectory -= np.mean(trajectory, axis=0)
trajectory *= 35.0 # Scale to fit screen

TRAIL_LENGTH = 12000
SPEED = 120 # Points advanced per frame

def get_rotation_matrix(rx, ry, rz):
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    
    return Rz @ Ry @ Rx

def setup():
    # Use default 2D renderer to avoid P3D OpenGL issues on headless Mac
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10, 5, 20)
    
    py5.push_matrix()
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    # Rotation angles
    t = py5.frame_count * 0.005
    rx = np.sin(t * 0.5) * 0.2
    ry = t
    rz = np.cos(t * 0.3) * 0.2
    
    R = get_rotation_matrix(rx, ry, rz)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2.0)
    
    start_idx = py5.frame_count * SPEED
    end_idx = start_idx + TRAIL_LENGTH
    
    if end_idx >= num_points:
        end_idx = num_points - 1
        start_idx = max(0, end_idx - TRAIL_LENGTH)
        
    pts = trajectory[start_idx:end_idx]
    
    # Project to 2D
    pts_rotated = pts @ R.T
    
    # We draw the trail in a loop
    py5.begin_shape(py5.LINES)
    
    for i in range(len(pts_rotated) - 1):
        progress = i / TRAIL_LENGTH
        
        r = int(255 * (progress ** 2))
        g = int(150 * (progress ** 4))
        b = int(200 * max(0, 1 - progress * 2))
        alpha = int(255 * progress)
        
        py5.stroke(r, g, b, alpha)
        
        p1 = pts_rotated[i]
        p2 = pts_rotated[i+1]
        
        py5.vertex(p1[0], p1[1])
        py5.vertex(p2[0], p2[1])
        
    py5.end_shape()
    py5.pop_matrix()

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
