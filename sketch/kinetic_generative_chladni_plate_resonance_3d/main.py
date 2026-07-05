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

# Grid size for the Chladni plate
RES = 400
x = np.linspace(-1, 1, RES)
y = np.linspace(-1, 1, RES)
X, Y = np.meshgrid(x, y)
X_flat = X.flatten()
Y_flat = Y.flatten()

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 15, 20)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(10, 15, 20)
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.015
    
    # Animate the resonance frequencies
    # M and N typically integers for standing waves, but we allow continuous values for kinetic art
    N = 4.0 + np.sin(time_val * 0.5) * 2.0
    M = 6.0 + np.cos(time_val * 0.3) * 3.0
    
    # Chladni equation
    Z_flat = np.cos(N * np.pi * X_flat) * np.cos(M * np.pi * Y_flat) - np.cos(M * np.pi * X_flat) * np.cos(N * np.pi * Y_flat)
    
    # Normalize Z
    Z_flat = Z_flat / 2.0
    
    # Prepare 3D coordinates
    scale = 600.0
    z_scale = 150.0
    
    coords = np.zeros((RES * RES, 3))
    coords[:, 0] = X_flat * scale
    coords[:, 1] = Z_flat * z_scale
    coords[:, 2] = Y_flat * scale
    
    # 3D Rotation (tilt slightly down and rotate slowly)
    rot_x = np.array([
        [1, 0, 0],
        [0, np.cos(0.8), -np.sin(0.8)],
        [0, np.sin(0.8), np.cos(0.8)]
    ])
    
    rot_y = np.array([
        [np.cos(time_val * 0.4), 0, np.sin(time_val * 0.4)],
        [0, 1, 0],
        [-np.sin(time_val * 0.4), 0, np.cos(time_val * 0.4)]
    ])
    
    rotated = coords.dot(rot_y).dot(rot_x)
    
    # Perspective projection
    fov = 1200.0
    z_offset = rotated[:, 2] + 1000.0
    valid_z = z_offset > 1
    
    proj_x = (rotated[valid_z, 0] / z_offset[valid_z]) * fov + py5.width / 2
    proj_y = (rotated[valid_z, 1] / z_offset[valid_z]) * fov + py5.height / 2
    z_vals = Z_flat[valid_z]
    
    # Coloring based on height (Z value)
    # Deep violet (280) to Electric blue (220) to Gold (40)
    py5.stroke_weight(2.0)
    
    # Peaks (Gold)
    peak_mask = z_vals > 0.4
    if np.any(peak_mask):
        py5.stroke(40, 90, 100, 80)
        py5.points(np.column_stack((proj_x[peak_mask], proj_y[peak_mask])))
        
    # Mid-high (Cyan)
    mid_mask = (z_vals <= 0.4) & (z_vals > 0.0)
    if np.any(mid_mask):
        py5.stroke(200, 80, 80, 50)
        py5.points(np.column_stack((proj_x[mid_mask], proj_y[mid_mask])))
        
    # Valleys / Nodes (Violet)
    valley_mask = z_vals <= 0.0
    if np.any(valley_mask):
        py5.stroke(280, 90, 60, 30)
        py5.points(np.column_stack((proj_x[valley_mask], proj_y[valley_mask])))

    py5.blend_mode(py5.BLEND)

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
