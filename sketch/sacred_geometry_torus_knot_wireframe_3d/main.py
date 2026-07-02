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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Torus knot parameters
P = 3
Q = 7
NUM_POINTS = 800
TUBE_RES = 12
TUBE_RADIUS = 30.0
SCALE = 200.0

def get_torus_knot_point(t):
    # Parametric equations for torus knot
    r = np.cos(Q * t) + 2.0
    x = r * np.cos(P * t) * SCALE
    y = r * np.sin(P * t) * SCALE
    z = -np.sin(Q * t) * SCALE
    return np.array([x, y, z])

def get_frenet_frame(t):
    # Numerical differentiation to get tangent, normal, binormal
    dt = 0.01
    p0 = get_torus_knot_point(t - dt)
    p1 = get_torus_knot_point(t + dt)
    p2 = get_torus_knot_point(t + 2*dt)
    
    # Tangent
    t_vec = p1 - p0
    t_vec = t_vec / np.linalg.norm(t_vec)
    
    # Second derivative approx
    p_prime = p1 - p0
    p_prime2 = p2 - p1
    n_vec = p_prime2 - p_prime
    
    # Prevent divide by zero if curve is straight (unlikely for torus knot)
    norm_n = np.linalg.norm(n_vec)
    if norm_n > 0.0001:
        n_vec = n_vec / norm_n
    else:
        # Fallback if curvature is zero
        n_vec = np.array([0, 1, 0])
        
    # Binormal
    b_vec = np.cross(t_vec, n_vec)
    b_vec = b_vec / np.linalg.norm(b_vec)
    
    # Re-orthogonalize normal just in case
    n_vec = np.cross(b_vec, t_vec)
    n_vec = n_vec / np.linalg.norm(n_vec)
    
    return p1, t_vec, n_vec, b_vec

# Precalculate the path and frames
t_vals = np.linspace(0, 2 * np.pi, NUM_POINTS, endpoint=False)
frames = [get_frenet_frame(t) for t in t_vals]

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(10, 80, 5)
    
    py5.lights()
    py5.directional_light(0, 0, 100, 0, 1, -1)
    py5.directional_light(200, 80, 100, -1, -1, 0)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.5)
    py5.rotate_z(t * 0.1)
    
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    # Draw the tube
    for i in range(NUM_POINTS):
        idx1 = i
        idx2 = (i + 1) % NUM_POINTS
        
        p1, t1, n1, b1 = frames[idx1]
        p2, t2, n2, b2 = frames[idx2]
        
        # Modulate radius over time and position
        pulse = np.sin(i * 0.05 + t * 4) * 15
        current_radius = TUBE_RADIUS + pulse
        
        hue = (180 + i * 0.5 + t * 30) % 360
        py5.stroke(hue, 80, 90, 80)
        
        py5.begin_shape(py5.QUAD_STRIP)
        for j in range(TUBE_RES + 1):
            angle = (j / TUBE_RES) * 2 * np.pi
            
            # Circle profile point 1
            cx1 = np.cos(angle) * current_radius
            cy1 = np.sin(angle) * current_radius
            # Map to 3D frame 1
            v1 = p1 + n1 * cx1 + b1 * cy1
            
            # Circle profile point 2
            cx2 = np.cos(angle) * current_radius
            cy2 = np.sin(angle) * current_radius
            # Map to 3D frame 2
            v2 = p2 + n2 * cx2 + b2 * cy2
            
            py5.vertex(v1[0], v1[1], v1[2])
            py5.vertex(v2[0], v2[1], v2[2])
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
