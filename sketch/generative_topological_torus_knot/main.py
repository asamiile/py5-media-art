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

NUM_POINTS = 20000

t_vals = np.linspace(0, 2 * np.pi, NUM_POINTS)
p = 3
q = 7

# base knot coordinates
r_base = 350 + 120 * np.cos(q * t_vals)
base_x = r_base * np.cos(p * t_vals)
base_y = r_base * np.sin(p * t_vals)
base_z = 120 * np.sin(q * t_vals)

# Tangent vector approximation for orthonormal basis (for tube generation)
dx = np.gradient(base_x)
dy = np.gradient(base_y)
dz = np.gradient(base_z)

# Normalize tangent
mag = np.sqrt(dx**2 + dy**2 + dz**2)
tx, ty, tz = dx/mag, dy/mag, dz/mag

# Normal vector (assume up is z, unless parallel)
nx = np.zeros(NUM_POINTS)
ny = np.zeros(NUM_POINTS)
nz = np.ones(NUM_POINTS)

# Cross product to get binormal
bx = ty * nz - tz * ny
by = tz * nx - tx * nz
bz = tx * ny - ty * nx

b_mag = np.sqrt(bx**2 + by**2 + bz**2)
bx, by, bz = bx/b_mag, by/b_mag, bz/b_mag

# Recalculate normal to be perfectly orthogonal
nx = by * tz - bz * ty
ny = bz * tx - bx * tz
nz = bx * ty - by * tx

# offsets for the tube
angles = np.random.uniform(0, 2 * np.pi, NUM_POINTS)
radii = np.random.uniform(0, 80, NUM_POINTS)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    # Motion blur using semi-transparent background
    py5.push_matrix()
    py5.reset_matrix()
    py5.no_lights()
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 20)  # Moderate fade
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()

    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    time = py5.frame_count * 0.015
    
    py5.rotate_x(time * 0.5)
    py5.rotate_y(time * 0.7)
    py5.rotate_z(time * 0.3)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(3)
    
    # Calculate noise-based displacement
    # To keep it fast, we add a simple global sine displacement + noise on radii
    dynamic_radii = radii + 40 * np.sin(t_vals * 15 + time * 5)
    
    # Apply orthonormal basis to get 3D tube coordinates
    ox = nx * np.cos(angles) + bx * np.sin(angles)
    oy = ny * np.cos(angles) + by * np.sin(angles)
    oz = nz * np.cos(angles) + bz * np.sin(angles)
    
    final_x = base_x + ox * dynamic_radii
    final_y = base_y + oy * dynamic_radii
    final_z = base_z + oz * dynamic_radii
    
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_POINTS):
        # Color based on position in the knot (t_vals) and depth
        h = (t_vals[i] * 60 + time * 50 + final_z[i] * 0.2) % 360
        s = 80
        b = 90
        
        py5.stroke(h, s, b, 70)
        py5.vertex(final_x[i], final_y[i], final_z[i])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
