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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 100000

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel
    pos = np.random.rand(NUM_PARTICLES, 2) * [py5.width, py5.height]
    vel = np.zeros((NUM_PARTICLES, 2))

def draw():
    # Motion blur / fading trails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    global pos, vel
    
    # Calculate pseudo-noise vector field using intersecting sine waves
    nx = pos[:, 0] * 0.002
    ny = pos[:, 1] * 0.002
    
    # Field equation
    angle = np.sin(nx + t * py5.TWO_PI) * 4.0 + np.cos(ny - t * py5.TWO_PI * 1.5) * 4.0
    
    # Calculate acceleration and add to velocity
    vel[:, 0] += np.cos(angle) * 0.5
    vel[:, 1] += np.sin(angle) * 0.5
    
    # Friction/Damping
    vel *= 0.95
    
    # Update position
    pos += vel
    
    # Wrap around edges
    pos[:, 0] %= py5.width
    pos[:, 1] %= py5.height
    
    # Group by velocity for coloring
    vel_mag = np.linalg.norm(vel, axis=1)
    
    group_slow = vel_mag < 2.0
    group_fast = vel_mag >= 2.0
    
    py5.stroke_weight(2)
    
    # Deep Blue / Purple for slow particles
    py5.stroke(50, 50, 255, 100)
    py5.begin_shape(py5.POINTS)
    py5.vertices(pos[group_slow])
    py5.end_shape()
    
    # Neon Cyan for fast particles
    py5.stroke(0, 255, 255, 150)
    py5.begin_shape(py5.POINTS)
    py5.vertices(pos[group_fast])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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
