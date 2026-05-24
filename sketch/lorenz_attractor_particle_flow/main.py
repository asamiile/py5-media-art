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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 200000
STEPS_PER_FRAME = 3
DT = 0.005

# Lorenz parameters
SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0

# Initialize particles in a small cluster near the origin
pos = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
pos[:, 0] = np.random.uniform(-5, 5, NUM_PARTICLES)
pos[:, 1] = np.random.uniform(-5, 5, NUM_PARTICLES)
pos[:, 2] = np.random.uniform(20, 30, NUM_PARTICLES)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global pos
    
    # Semi-transparent background for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Additive blending for glowing particles
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # RK4 or Euler integration. We'll use fast Euler for performance,
    # as chaotic divergence is actually desired visually here.
    for _ in range(STEPS_PER_FRAME):
        dx = SIGMA * (pos[:, 1] - pos[:, 0])
        dy = pos[:, 0] * (RHO - pos[:, 2]) - pos[:, 1]
        dz = pos[:, 0] * pos[:, 1] - BETA * pos[:, 2]
        
        pos[:, 0] += dx * DT
        pos[:, 1] += dy * DT
        pos[:, 2] += dz * DT

    # Camera rotation
    rot_y = t * np.pi * 2.0
    
    cos_y, sin_y = np.cos(rot_y), np.sin(rot_y)
    
    # Center the attractor (Z mean is around ~24)
    # The attractor spans roughly X:[-20,20], Y:[-25,25], Z:[0,50]
    cx = pos[:, 0]
    cy = pos[:, 1]
    cz = pos[:, 2] - 24.0
    
    # Rotate around Y axis
    x1 = cx * cos_y - cz * sin_y
    y1 = cy
    z1 = cx * sin_y + cz * cos_y
    
    # Scale up for screen
    scale = 20.0
    px = x1 * scale + SIZE[0] / 2
    py_ = y1 * scale + SIZE[1] / 2
    
    valid = (px >= 0) & (px < SIZE[0]) & (py_ >= 0) & (py_ < SIZE[1])
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    p_x = px[valid].astype(int)
    p_y = py_[valid].astype(int)
    
    # Color based on Z position (depth)
    # Map Z:[0,50] to a color gradient: Deep Purple -> Hot Pink -> Bright Orange
    p_z = pos[:, 2][valid]
    norm_z = np.clip((p_z) / 40.0, 0, 1)
    
    # Purple (100, 0, 200) -> Pink (255, 50, 150) -> Orange (255, 150, 0)
    c_r = (norm_z * 155 + 100).astype(np.uint16)
    c_g = (norm_z**2 * 150).astype(np.uint16)
    c_b = ((1.0 - norm_z) * 200).astype(np.uint16)
    
    curr_r = pixels[p_y, p_x, 1]
    curr_g = pixels[p_y, p_x, 2]
    curr_b = pixels[p_y, p_x, 3]
    
    # Additive blend intensity
    intensity = 0.05
    
    pixels[p_y, p_x, 0] = 255
    pixels[p_y, p_x, 1] = np.clip(curr_r.astype(np.float32) + c_r * intensity, 0, 255).astype(np.uint8)
    pixels[p_y, p_x, 2] = np.clip(curr_g.astype(np.float32) + c_g * intensity, 0, 255).astype(np.uint8)
    pixels[p_y, p_x, 3] = np.clip(curr_b.astype(np.float32) + c_b * intensity, 0, 255).astype(np.uint8)
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
