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

# Generate random spherical coordinates
NUM_POINTS = 500000
r = np.abs(np.random.normal(0, 15, NUM_POINTS))
theta = np.random.uniform(0, 2*np.pi, NUM_POINTS)
phi = np.random.uniform(0, np.pi, NUM_POINTS)

# Manual Y_3^1 approximation for visualization
# Y_3^1 proportional to sin(phi) * (5*cos^2(phi) - 1) * exp(i * theta)
def Y_3_1(theta, phi):
    magnitude = np.sin(phi) * (5 * np.cos(phi)**2 - 1)
    phase = theta
    return magnitude, phase

def R(r_val):
    return (r_val**3) * np.exp(-r_val / 4.0)

magnitude, phase = Y_3_1(theta, phi)
density = np.abs(magnitude)**2 * R(r)**2

threshold = np.percentile(density, 80)
mask = density > threshold
r_f = r[mask]
theta_f = theta[mask]
phi_f = phi[mask]
phase_f = phase[mask]

# Convert to Cartesian
x = r_f * np.sin(phi_f) * np.cos(theta_f) * 20
y = r_f * np.sin(phi_f) * np.sin(theta_f) * 20
z = r_f * np.cos(phi_f) * 20

coords = np.column_stack((x, y, z))

# Color by phase sign of the Y harmonic magnitude
colors_hue = np.where(magnitude[mask] > 0, 180, 300) # Cyan and Magenta

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.01
    
    rot_y = np.array([
        [np.cos(time_val), 0, np.sin(time_val)],
        [0, 1, 0],
        [-np.sin(time_val), 0, np.cos(time_val)]
    ])
    
    rot_x = np.array([
        [1, 0, 0],
        [0, np.cos(time_val * 0.5), -np.sin(time_val * 0.5)],
        [0, np.sin(time_val * 0.5), np.cos(time_val * 0.5)]
    ])
    
    rotated_coords = coords.dot(rot_x).dot(rot_y)
    
    fov = 800
    z_offset = rotated_coords[:, 2] + 400
    valid_z = z_offset > 1
    
    proj_x = (rotated_coords[valid_z, 0] / z_offset[valid_z]) * fov + py5.width / 2
    proj_y = (rotated_coords[valid_z, 1] / z_offset[valid_z]) * fov + py5.height / 2
    hues = colors_hue[valid_z]
    
    py5.stroke_weight(2.5)
    
    py5.stroke(180, 80, 100, 10)
    cyan_mask = hues == 180
    if np.any(cyan_mask):
        py5.points(np.column_stack((proj_x[cyan_mask], proj_y[cyan_mask])))
    
    py5.stroke(300, 80, 100, 10)
    mag_mask = hues == 300
    if np.any(mag_mask):
        py5.points(np.column_stack((proj_x[mag_mask], proj_y[mag_mask])))
    
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
