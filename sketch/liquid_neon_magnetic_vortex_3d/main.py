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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle system state
NUM_PARTICLES = 15000
positions = None
velocities = None
colors = None


def setup():
    global positions, velocities, colors
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize particles
    np.random.seed(42)
    
    # Randomly distribute in a sphere
    phi = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
    costheta = np.random.uniform(-1, 1, NUM_PARTICLES)
    u = np.random.uniform(0, 1, NUM_PARTICLES)
    
    theta = np.arccos(costheta)
    r = 800 * np.cbrt(u)
    
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    
    positions = np.column_stack((x, y, z))
    velocities = np.zeros_like(positions)
    
    # Colors base
    colors = np.random.uniform(180, 320, NUM_PARTICLES)


def draw():
    global positions, velocities
    py5.background(5, 5, 10)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Camera rotation
    cam_angle = py5.frame_count * 0.01
    py5.rotate_y(cam_angle)
    py5.rotate_x(np.sin(cam_angle * 0.5) * 0.5)
    
    # Update physics
    t = py5.frame_count * 0.02
    
    # Dual attractors
    attractor1 = np.array([np.sin(t) * 500, np.cos(t * 1.3) * 500, np.sin(t * 0.7) * 500])
    attractor2 = np.array([-np.sin(t) * 500, -np.cos(t * 1.3) * 500, -np.sin(t * 0.7) * 500])
    
    # Vectorized forces
    diff1 = attractor1 - positions
    diff2 = attractor2 - positions
    
    dist1 = np.linalg.norm(diff1, axis=1, keepdims=True)
    dist2 = np.linalg.norm(diff2, axis=1, keepdims=True)
    
    # Avoid division by zero
    dist1[dist1 < 10] = 10
    dist2[dist2 < 10] = 10
    
    force1 = (diff1 / dist1) * (50000 / dist1**2)
    force2 = (diff2 / dist2) * (50000 / dist2**2)
    
    # Add curl noise-like rotation around Y axis
    curl = np.column_stack((-positions[:, 2], np.zeros(NUM_PARTICLES), positions[:, 0])) * 0.05
    
    acceleration = force1 + force2 + curl
    
    velocities += acceleration
    velocities *= 0.95  # friction
    positions += velocities
    
    # Calculate speed for color
    speeds = np.linalg.norm(velocities, axis=1)
    
    # Render particles
    py5.stroke_weight(4)
    py5.begin_shape(py5.POINTS)
    
    for i in range(NUM_PARTICLES):
        p = positions[i]
        speed = speeds[i]
        
        # Color mapping based on speed
        hue = (colors[i] + speed * 2) % 360
        bright = min(100, 50 + speed * 5)
        
        py5.stroke(hue, 90, bright, 80)
        py5.vertex(p[0], p[1], p[2])
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
