from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os

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

GRID_W = 15
GRID_H = 15
GRID_D = 15
SPACING = 30
NUM_PARTICLES = GRID_W * GRID_H * GRID_D

targets = np.zeros((NUM_PARTICLES, 3))
pos = np.zeros((NUM_PARTICLES, 3))
vel = np.zeros((NUM_PARTICLES, 3))

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global targets, pos, vel
    idx = 0
    for x in range(GRID_W):
        for y in range(GRID_H):
            for z in range(GRID_D):
                # Target grid
                targets[idx] = [
                    (x - GRID_W/2) * SPACING,
                    (y - GRID_H/2) * SPACING,
                    (z - GRID_D/2) * SPACING
                ]
                # Start scattered
                pos[idx] = targets[idx] + np.random.randn(3) * 500
                idx += 1

def draw():
    global pos, vel
    
    py5.background(0) # Stark black
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    py5.ambient_light(50, 50, 50)
    py5.directional_light(0, 0, 100, 1, 1, -1)
    py5.directional_light(300, 100, 100, -1, -1, -1) # Magenta light
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    t = py5.frame_count * 0.02
    
    py5.rotate_y(t * 0.5)
    py5.rotate_x(t * 0.3)
    
    # Noise wave parameters
    wave = np.sin(t)
    
    # Update particles
    for i in range(NUM_PARTICLES):
        p = pos[i]
        tgt = targets[i]
        
        # Base attraction
        force = (tgt - p) * 0.05
        
        # Fluid disruption when wave > 0
        if wave > 0:
            nx = py5.os_noise(p[0]*0.01, p[1]*0.01, t) - 0.5
            ny = py5.os_noise(p[1]*0.01, p[2]*0.01, t) - 0.5
            nz = py5.os_noise(p[2]*0.01, p[0]*0.01, t) - 0.5
            force += np.array([nx, ny, nz]) * wave * 50
            
        vel[i] = vel[i] * 0.8 + force
        pos[i] += vel[i]
        
        py5.push_matrix()
        py5.translate(pos[i][0], pos[i][1], pos[i][2])
        
        # Color transition based on velocity
        speed = np.linalg.norm(vel[i])
        
        if speed > 5:
            py5.fill(300, 100, 100) # Bright magenta when chaotic
        else:
            py5.fill(0, 0, 100) # White when stable
            
        py5.no_stroke()
        
        # Size shifts slightly
        s = 10 + speed * 0.5
        py5.box(s)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
            
        os._exit(0)

py5.run_sketch()
