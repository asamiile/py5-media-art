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

# Parameters
GRID_SIZE = 800
NUM_POINTS = GRID_SIZE * GRID_SIZE

# Create a 2D meshgrid centered at 0
x_vals = np.linspace(-1, 1, GRID_SIZE)
y_vals = np.linspace(-1, 1, GRID_SIZE)
xv, yv = np.meshgrid(x_vals, y_vals)
xv = xv.flatten()
yv = yv.flatten()

# Base points in 3D: [x, y, z]
base_points = np.column_stack((xv, yv, np.zeros(NUM_POINTS)))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Motion blur using semi-transparent black
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 5, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    # We will simulate multiple wave sources
    # A source has (x, y, frequency, amplitude, phase_speed)
    sources = [
        (-0.5, -0.5, 15.0, 0.2, 2.0),
        (0.5, 0.5, 20.0, 0.15, 2.5),
        (-0.3, 0.6, 12.0, 0.18, 1.8),
        (0.6, -0.4, 18.0, 0.12, 2.2),
        (0.0, 0.0, 8.0, 0.25, 1.0)
    ]
    
    # Let the sources drift slowly to make it more dynamic
    drift_t = t * 0.2
    
    z = np.zeros(NUM_POINTS)
    
    for i, (sx, sy, freq, amp, speed) in enumerate(sources):
        # Drift source positions
        sx_d = sx + np.sin(drift_t + i) * 0.2
        sy_d = sy + np.cos(drift_t + i * 1.5) * 0.2
        
        # Calculate distance from source
        dist = np.sqrt((xv - sx_d)**2 + (yv - sy_d)**2)
        
        # Add wave interference
        z += np.sin(dist * freq - t * speed) * amp

    # Modulate overall amplitude
    z *= (0.5 + 0.5 * np.cos(drift_t * 0.5))

    # We now have 3D points
    x3d = xv * 100.0
    y3d = yv * 100.0
    z3d = z * 30.0
    
    # Rotate the grid to view it in pseudo-3D
    rot_x = np.pi / 3 # Tilt forward
    rot_z = t * 0.1   # Slowly spin
    
    # Rotate around Z
    cos_rz = np.cos(rot_z)
    sin_rz = np.sin(rot_z)
    x3d_rot1 = x3d * cos_rz - y3d * sin_rz
    y3d_rot1 = x3d * sin_rz + y3d * cos_rz
    
    # Rotate around X
    cos_rx = np.cos(rot_x)
    sin_rx = np.sin(rot_x)
    y3d_rot2 = y3d_rot1 * cos_rx - z3d * sin_rx
    z3d_rot2 = y3d_rot1 * sin_rx + z3d * cos_rx
    
    # Project
    fov = 800.0
    z_offset = 120.0
    z_proj = z3d_rot2 + z_offset
    
    x2d = (x3d_rot1 / z_proj) * fov + SIZE[0]/2
    y2d = SIZE[1]/2 - (y3d_rot2 / z_proj) * fov
    
    # Color mapping based on height `z`
    # We will slice `z` into 3 buckets for Red, Green, Blue
    
    py5.stroke_weight(1.5)
    
    # High points -> Hot pink / Red
    mask_high = z > 0.1
    if np.any(mask_high):
        py5.stroke(255, 50, 150, 60)
        pts = np.column_stack((x2d[mask_high], y2d[mask_high]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Mid points -> Cyan / Blue
    mask_mid = (z <= 0.1) & (z >= -0.1)
    if np.any(mask_mid):
        py5.stroke(0, 200, 255, 40)
        pts = np.column_stack((x2d[mask_mid], y2d[mask_mid]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Low points -> Purple / Dark Blue
    mask_low = z < -0.1
    if np.any(mask_low):
        py5.stroke(100, 0, 255, 60)
        pts = np.column_stack((x2d[mask_low], y2d[mask_low]))
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
