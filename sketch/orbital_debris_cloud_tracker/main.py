"""
orbital_debris_cloud_tracker
=============================
A procedural radar scope tracking tens of thousands of space debris fragments
orbiting in a massive 3D cloud.

Format: Animation (15s @ 60fps)
Palette: Deep Radar Green, Glowing Cyan, Amber Warnings, White Traces
"""

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
from lib.sizes import get_sizes

# ── Configuration ────────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# ── Simulation Data ──────────────────────────────────────────────────────────
N_DEBRIS = 45000
debris_pos = None
debris_color = None
debris_size = None

def setup():
    global debris_pos, debris_color, debris_size
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize debris in orbital rings using Keplerian-like distribution
    r = np.random.normal(700, 150, N_DEBRIS)
    theta = np.random.uniform(0, 2*np.pi, N_DEBRIS)
    
    # Incline orbits slightly to form a shell, plus a distinct dense equatorial ring
    is_equatorial = np.random.rand(N_DEBRIS) < 0.25
    phi = np.where(
        is_equatorial,
        np.random.normal(np.pi/2, 0.05, N_DEBRIS),
        np.random.normal(np.pi/2, 0.4, N_DEBRIS)
    )
    
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.cos(phi)
    z = r * np.sin(phi) * np.sin(theta)
    
    debris_pos = np.column_stack((x, y, z)).astype(np.float32)
    
    # Base orbital angular velocity (inversely proportional to r^1.5 approx)
    v_base = 1000.0 / (r ** 1.5)
    
    # Assign colors based on density/danger
    debris_color = np.zeros((N_DEBRIS, 3), dtype=np.float32)
    debris_size = np.zeros(N_DEBRIS, dtype=np.float32)
    
    for i in range(N_DEBRIS):
        speed = v_base[i]
        # Most are dim green, fast/close ones are cyan, some are amber warning
        if speed > 0.08 and np.random.rand() < 0.1:
            debris_color[i] = [1.0, 0.6, 0.1] # Amber
            debris_size[i] = 2.5
        elif speed > 0.06:
            debris_color[i] = [0.2, 0.8, 0.9] # Cyan
            debris_size[i] = 1.8
        else:
            debris_color[i] = [0.1, 0.4, 0.2] # Dim Green
            debris_size[i] = 1.0
            
    print(f"[{WORK_NAME}] Debris tracker initialized.")

def draw():
    fc = py5.frame_count
    W, H = SIZE
    
    py5.background(5, 8, 5) # Very dark green-black void
    
    py5.push_matrix()
    py5.translate(W/2, H/2, 0)
    
    # Slowly orbit camera
    py5.rotate_x(0.3 + np.sin(fc * 0.01) * 0.1)
    py5.rotate_y(fc * 0.005)
    
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    
    # Draw central Earth-like occlusion sphere
    py5.blend_mode(py5.BLEND)
    py5.fill(2, 4, 2, 255)
    py5.sphere(400)
    py5.blend_mode(py5.ADD)
    
    # We will use POINTS for massive particle count
    py5.begin_shape(py5.POINTS)
    
    # Advance orbits
    # Simplification: rotation around Y axis
    rot_angle = fc * 0.02
    cos_a = np.cos(rot_angle)
    sin_a = np.sin(rot_angle)
    
    # Different rings rotate at different speeds. 
    # To keep performance 60fps without numpy loop, we just draw with a trick:
    # We rotate the whole matrix, but we also manually add a subtle warp based on radius
    
    # For actual performance in Python, we draw using py5.points directly from numpy if possible
    # Wait, py5.shape can take numpy arrays? Yes, but begin_shape doesn't natively take numpy.
    # We can just iterate or use py5.points() which accepts 2D arrays!
    
    py5.end_shape()
    
    # Fast drawing with py5.points()
    # We need to compute rotated positions
    # Instead of full rotation matrix per particle, we do it in a vectorized way
    
    r_factor = np.sqrt(debris_pos[:,0]**2 + debris_pos[:,2]**2)
    speeds = 5.0 / (r_factor + 100)
    angles = np.arctan2(debris_pos[:,2], debris_pos[:,0]) + speeds * fc * 5.0
    
    new_x = r_factor * np.cos(angles)
    new_z = r_factor * np.sin(angles)
    
    current_pos = np.column_stack((new_x, debris_pos[:,1], new_z))
    
    py5.stroke_weight(2.0)
    # Py5 allows passing a 2D array of coordinates to points()
    py5.stroke(40, 200, 220, 100)
    py5.points(current_pos)
    
    # Let's draw the amber ones slightly larger
    amber_mask = debris_color[:,0] > 0.9
    if np.any(amber_mask):
        py5.stroke_weight(4.0)
        py5.stroke(255, 150, 20, 200)
        py5.points(current_pos[amber_mask])
    
    # Overlay radar HUD elements
    py5.pop_matrix()
    py5.blend_mode(py5.BLEND)
    
    # UI Layer
    py5.fill(40, 200, 100)
    py5.text_size(24)
    py5.text(f"ORBITAL DEBRIS TRACKER  //  OBJ_COUNT: {N_DEBRIS}", 50, 50)
    py5.text(f"SWEEP ANGLE: {fc * 0.05:.2f} RAD", 50, 80)
    py5.text(f"CRITICAL PROXIMITY ALERTS: {np.sum(amber_mask)}", 50, 110)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid = TOTAL_FRAMES // 2
        shutil.copyfile(
            str(FRAMES_DIR / f"frame-{mid:04d}.png"),
            str(SKETCH_DIR / PREVIEW_FILENAME)
        )
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
        import os
        os._exit(0)

if __name__ == "__main__":
    py5.run_sketch()
