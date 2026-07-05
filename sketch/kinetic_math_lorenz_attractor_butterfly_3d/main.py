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

# Lorenz attractor parameters
sigma = 10.0
rho = 28.0
beta = 8.0 / 3.0

NUM_POINTS = 50000
dt = 0.005

# Initialize points slightly spread around origin
positions = np.random.normal(0, 5.0, (NUM_POINTS, 3))
positions[:, 2] += 20.0 # Shift Z up

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(5, 5, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    global positions
    
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 5, 10, 8)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Update physics (Euler integration)
    x = positions[:, 0]
    y = positions[:, 1]
    z = positions[:, 2]
    
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    
    positions[:, 0] += dx * dt
    positions[:, 1] += dy * dt
    positions[:, 2] += dz * dt
    
    # Normalize and center coordinates for rendering
    # Lorenz attractor typically ranges x:[-20, 20], y:[-30, 30], z:[0, 50]
    render_pos = positions.copy()
    render_pos[:, 2] -= 25.0 # Center Z
    
    time_val = py5.frame_count * 0.005
    
    # 3D Rotation
    rot_y = np.array([
        [np.cos(time_val), 0, np.sin(time_val)],
        [0, 1, 0],
        [-np.sin(time_val), 0, np.cos(time_val)]
    ])
    
    rot_x = np.array([
        [1, 0, 0],
        [0, np.cos(time_val * 0.3), -np.sin(time_val * 0.3)],
        [0, np.sin(time_val * 0.3), np.cos(time_val * 0.3)]
    ])
    
    rotated = render_pos.dot(rot_y).dot(rot_x)
    
    # Projection
    scale = 30.0
    fov = 1000.0
    z_offset = rotated[:, 2] * scale + fov
    valid_z = z_offset > 1
    
    proj_x = (rotated[valid_z, 0] * scale / z_offset[valid_z]) * fov + py5.width / 2
    proj_y = (rotated[valid_z, 1] * scale / z_offset[valid_z]) * fov + py5.height / 2
    
    # Color based on Z speed/position
    speed = np.sqrt(dx**2 + dy**2 + dz**2)[valid_z]
    
    py5.stroke_weight(2.0)
    
    # Fast points
    fast_mask = speed > 60.0
    if np.any(fast_mask):
        py5.stroke(40, 80, 100, 30) # Orange
        py5.points(np.column_stack((proj_x[fast_mask], proj_y[fast_mask])))
        
    # Medium points
    med_mask = (speed <= 60.0) & (speed > 20.0)
    if np.any(med_mask):
        py5.stroke(320, 80, 100, 15) # Magenta
        py5.points(np.column_stack((proj_x[med_mask], proj_y[med_mask])))
        
    # Slow points
    slow_mask = speed <= 20.0
    if np.any(slow_mask):
        py5.stroke(220, 80, 80, 5) # Blue/Cyan
        py5.points(np.column_stack((proj_x[slow_mask], proj_y[slow_mask])))

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
