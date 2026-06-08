import numpy as np
from pathlib import Path
import shutil
import subprocess
import sys
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

# Particle system state
NUM_GROUPS = 5
PARTICLES_PER_GROUP = 30000
pos_list = []
vel_list = []
colors = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize groups
    base_hues = [30, 200, 300, 180, 50] # Orange, Indigo, Magenta, Cyan, Gold
    
    for i in range(NUM_GROUPS):
        # Initialize in a wide disk
        r = np.random.rand(PARTICLES_PER_GROUP, 1) * 1500 + 100
        theta = np.random.rand(PARTICLES_PER_GROUP, 1) * np.pi * 2
        y = (np.random.rand(PARTICLES_PER_GROUP, 1) - 0.5) * 400
        
        p = np.zeros((PARTICLES_PER_GROUP, 3), dtype=np.float32)
        p[:, 0:1] = r * np.cos(theta)
        p[:, 1:2] = y
        p[:, 2:3] = r * np.sin(theta)
        
        pos_list.append(p)
        
        # Initial velocity tangential
        v = np.zeros((PARTICLES_PER_GROUP, 3), dtype=np.float32)
        v[:, 0:1] = -p[:, 2:3] * 0.01
        v[:, 2:3] = p[:, 0:1] * 0.01
        vel_list.append(v)
        
        colors.append(py5.color(base_hues[i], 80, 100, 50))

def draw():
    py5.background(5, 5, 10)
    
    # Camera
    cam_radius = 1200 + py5.sin(py5.frame_count * 0.01) * 300
    cam_x = py5.cos(py5.frame_count * 0.005) * cam_radius
    cam_z = py5.sin(py5.frame_count * 0.005) * cam_radius
    cam_y = py5.sin(py5.frame_count * 0.01) * 500 - 200
    
    py5.camera(cam_x, cam_y, cam_z, 0, 0, 0, 0, 1, 0)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(3)
    
    # Anomaly pulsation
    pulse = py5.sin(py5.frame_count * 0.05) * 0.5 + 1.0
    
    for i in range(NUM_GROUPS):
        pos = pos_list[i]
        vel = vel_list[i]
        
        # Physics using NumPy
        # Distance to center
        dist_sq = pos[:, 0:1]**2 + pos[:, 1:2]**2 + pos[:, 2:3]**2
        dist = np.maximum(np.sqrt(dist_sq), 50.0)
        dir_to_center = -pos / dist
        
        # Tangent vector for vortex swirling
        tangent = np.zeros_like(pos)
        tangent[:, 0:1] = -dir_to_center[:, 2:3]
        tangent[:, 1:2] = 0
        tangent[:, 2:3] = dir_to_center[:, 0:1]
        
        # Gravity towards center
        gravity = dir_to_center * (3000.0 * pulse / dist)
        
        # Vortex spin
        vortex = tangent * (2000.0 / dist)
        
        # Updraft / downdraft along Y
        updraft = np.zeros_like(pos)
        updraft[:, 1:2] = np.sin(dist * 0.01 - py5.frame_count * 0.05) * 5.0
        
        # Repulsion at core
        repulsion = -dir_to_center * (200000.0 / (dist_sq + 1000.0))
        
        vel += gravity + vortex + updraft + repulsion
        vel *= 0.96 # Friction/drag
        
        # Speed limit to prevent explosion
        speed_sq = vel[:, 0:1]**2 + vel[:, 1:2]**2 + vel[:, 2:3]**2
        speed_limit = 40.0
        overspeed = speed_sq > speed_limit**2
        if np.any(overspeed):
            speed = np.sqrt(speed_sq)
            vel = np.where(overspeed, vel / speed * speed_limit, vel)
            
        pos += vel
        
        # Draw particles
        py5.stroke(colors[i])
        py5.points(pos)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
