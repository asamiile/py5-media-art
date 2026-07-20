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

# Thomas' cyclically symmetric attractor parameters
b = 0.208186
NUM_PARTICLES = 10000

# Initialize particles in a small cluster near the origin
positions = (np.random.rand(NUM_PARTICLES, 3) - 0.5) * 4.0

def thomas_derivative(p):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    dx = np.sin(y) - b * x
    dy = np.sin(z) - b * y
    dz = np.sin(x) - b * z
    return np.column_stack((dx, dy, dz))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 20)
    py5.color_mode(py5.RGB, 255)
    py5.no_stroke()

def draw():
    global positions
    # Trails effect via semi-transparent background clearing
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 5, 20, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    dt = 0.1
    # Runge-Kutta 4 integration
    k1 = thomas_derivative(positions)
    k2 = thomas_derivative(positions + k1 * dt * 0.5)
    k3 = thomas_derivative(positions + k2 * dt * 0.5)
    k4 = thomas_derivative(positions + k3 * dt)
    positions += (k1 + 2*k2 + 2*k3 + k4) * (dt / 6.0)
    
    # Camera / projection setup
    t = py5.frame_count * 0.005
    cos_t = np.cos(t)
    sin_t = np.sin(t)
    
    # Rotate around Y axis
    rot_y = np.array([
        [cos_t, 0, sin_t],
        [0, 1, 0],
        [-sin_t, 0, cos_t]
    ])
    
    # Rotate around X axis
    cos_x = np.cos(t * 0.7)
    sin_x = np.sin(t * 0.7)
    rot_x = np.array([
        [1, 0, 0],
        [0, cos_x, -sin_x],
        [0, sin_x, cos_x]
    ])
    
    rot_matrix = rot_y @ rot_x
    rotated_positions = positions @ rot_matrix.T
    
    # Simple isometric / orthographic projection to 2D
    scale = 300
    px = rotated_positions[:, 0] * scale + SIZE[0] / 2
    py = rotated_positions[:, 1] * scale + SIZE[1] / 2
    pz = rotated_positions[:, 2] # Use Z for color/depth
    
    # Draw points
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        # Color based on Z depth and position
        z_norm = (pz[i] + 4.0) / 8.0 # roughly 0 to 1
        z_norm = max(0, min(1, z_norm))
        
        # Interpolate between electric blue and hot pink
        r = int(py5.remap(z_norm, 0, 1, 0, 255))
        g = int(py5.remap(z_norm, 0, 1, 200, 50))
        b_col = 255
        
        py5.stroke(r, g, b_col, 150)
        py5.vertex(px[i], py[i])
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
