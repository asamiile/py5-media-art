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

NUM_PARTICLES = 300000

# State
points = np.zeros((NUM_PARTICLES, 3))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize randomly within the attractor's general bounding box
    points[:, 0] = np.random.uniform(-1, 1, NUM_PARTICLES)
    points[:, 1] = np.random.uniform(-1, 1, NUM_PARTICLES)
    points[:, 2] = np.random.uniform(-1, 1, NUM_PARTICLES)

def draw():
    # Motion blur using semi-transparent black
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 5, 10, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    # Base Aizawa attractor parameters
    a = 0.95
    b = 0.7
    c = 0.6
    d = 3.5
    e = 0.25
    f = 0.1
    
    # Mutate parameters slightly over time for a breathing effect
    a_mod = a + np.sin(t * 0.8) * 0.05
    c_mod = c + np.cos(t * 1.2) * 0.05
    
    dt = 0.01
    
    # Perform 3 Euler integration steps per frame
    for _ in range(3):
        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]
        
        # Aizawa equations
        dx = (z - b) * x - d * y
        dy = d * x + (z - b) * y
        dz = c_mod + a_mod * z - (z**3) / 3.0 - (x**2 + y**2) * (1.0 + e * z) + f * z * (x**3)
        
        points[:, 0] += dx * dt
        points[:, 1] += dy * dt
        points[:, 2] += dz * dt

    # Scale and center
    scale = 350.0 + 30.0 * np.sin(t * 0.5)
    
    # Rotate the attractor to show its 3D spherical structure
    rot_y = t * 0.3
    rot_x = t * 0.1 + np.pi/6 # slight tilt
    
    cos_ry = np.cos(rot_y)
    sin_ry = np.sin(rot_y)
    
    x_rot1 = points[:, 0] * cos_ry - points[:, 2] * sin_ry
    z_rot1 = points[:, 0] * sin_ry + points[:, 2] * cos_ry
    
    cos_rx = np.cos(rot_x)
    sin_rx = np.sin(rot_x)
    
    y_rot2 = points[:, 1] * cos_rx - z_rot1 * sin_rx
    z_rot2 = points[:, 1] * sin_rx + z_rot1 * cos_rx
    
    # Perspective projection
    fov = 1200.0
    z_offset = 6.0
    z_proj = z_rot2 + z_offset
    
    # Prevent division by zero
    z_proj = np.maximum(z_proj, 0.1)
    
    x2d = (x_rot1 / z_proj) * fov * scale + SIZE[0]/2
    y2d = SIZE[1]/2 - (y_rot2 / z_proj) * fov * scale
    
    # Determine color based on original Z value (before rotation)
    # This gives the top and bottom of the sphere different colors
    z_orig = points[:, 2]
    
    mask_top = z_orig > 0.5
    mask_mid = (z_orig <= 0.5) & (z_orig > -0.5)
    mask_bot = z_orig <= -0.5
    
    py5.stroke_weight(2)
    
    # Top points -> Bright Gold/Orange
    if np.any(mask_top):
        py5.stroke(255, 180, 50, 40)
        pts = np.column_stack((x2d[mask_top], y2d[mask_top]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Mid points -> Cyan
    if np.any(mask_mid):
        py5.stroke(50, 200, 255, 40)
        pts = np.column_stack((x2d[mask_mid], y2d[mask_mid]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Bot points -> Deep Blue/Purple
    if np.any(mask_bot):
        py5.stroke(100, 50, 255, 40)
        pts = np.column_stack((x2d[mask_bot], y2d[mask_bot]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

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
