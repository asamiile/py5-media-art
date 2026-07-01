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

NUM_PARTICLES = 250000

# State
# [x, y, z]
points = np.zeros((NUM_PARTICLES, 3))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize near the origin
    points[:, 0] = np.random.uniform(-0.1, 0.1, NUM_PARTICLES)
    points[:, 1] = np.random.uniform(-0.1, 0.1, NUM_PARTICLES)
    points[:, 2] = np.random.uniform(-0.1, 0.1, NUM_PARTICLES)

def draw():
    # Motion blur using semi-transparent black
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 5, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    # Base Lorenz parameters
    sigma = 10.0
    beta = 8.0 / 3.0
    # Modulate rho (the Rayleigh number) to cause chaotic shifts and morphs
    rho = 28.0 + 15.0 * np.sin(t * 1.5)
    
    dt = 0.005
    
    # Perform 4 Euler integration steps per frame to speed up the flow
    for _ in range(4):
        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]
        
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z
        
        points[:, 0] += dx * dt
        points[:, 1] += dy * dt
        points[:, 2] += dz * dt

    # Projection from 3D to 2D
    # Scale and center
    scale = 30.0 + 5.0 * np.cos(t)
    
    # We will rotate the attractor slowly to show its 3D structure
    rot_angle = t * 0.5
    cos_t = np.cos(rot_angle)
    sin_t = np.sin(rot_angle)
    
    # Rotate around Y axis
    x_rot = points[:, 0] * cos_t - points[:, 2] * sin_t
    z_rot = points[:, 0] * sin_t + points[:, 2] * cos_t
    
    # The attractor naturally lives around Z=rho, let's shift it so it's centered around the origin
    y_shifted = points[:, 1]
    z_shifted = z_rot - rho
    
    # Perspective projection
    fov = 1500.0
    # Add distance so it's fully in front of the camera
    z_proj = z_shifted + 100.0
    
    # prevent div zero
    z_proj = np.maximum(z_proj, 1.0)
    
    x2d = (x_rot / z_proj) * fov * scale + SIZE[0]/2
    # Invert Y so up is up
    y2d = SIZE[1]/2 - (y_shifted / z_proj) * fov * scale
    
    # Separate into two color buckets based on the sign of X before rotation
    # This colors the "left" and "right" wings of the butterfly
    mask_left = points[:, 0] < 0
    mask_right = ~mask_left
    
    py5.stroke_weight(2)
    
    # Left wing
    if np.any(mask_left):
        py5.stroke(0, 150, 255, 30) # Cyan
        pts_left = np.column_stack((x2d[mask_left], y2d[mask_left]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts_left)
        py5.end_shape()
        
    # Right wing
    if np.any(mask_right):
        py5.stroke(255, 0, 150, 30) # Magenta
        pts_right = np.column_stack((x2d[mask_right], y2d[mask_right]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts_right)
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
