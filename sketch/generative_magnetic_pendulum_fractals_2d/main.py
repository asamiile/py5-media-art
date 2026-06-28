from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_pendulums = 8000
positions = None
velocities = None
magnets = None
num_magnets = 5

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global positions, velocities, magnets
    
    positions = np.zeros((num_pendulums, 2), dtype=np.float32)
    grid_size = int(np.sqrt(num_pendulums))
    idx = 0
    cx, cy = SIZE[0]/2, SIZE[1]/2
    for i in range(grid_size):
        for j in range(grid_size):
            if idx < num_pendulums:
                positions[idx, 0] = cx + (i - grid_size/2) * 20
                positions[idx, 1] = cy + (j - grid_size/2) * 20
                idx += 1
                
    velocities = np.zeros((num_pendulums, 2), dtype=np.float32)
    
    magnets = np.zeros((num_magnets, 3), dtype=np.float32) 
    for i in range(num_magnets):
        angle = i * py5.TWO_PI / num_magnets
        r = 600
        magnets[i, 0] = cx + r * np.cos(angle)
        magnets[i, 1] = cy + r * np.sin(angle)
        magnets[i, 2] = 1.0 
        
    py5.background(5)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    global positions, velocities, magnets
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 5, 10, 8) 
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    cx, cy = SIZE[0]/2, SIZE[1]/2
    t = py5.frame_count * 0.005
    for i in range(num_magnets):
        angle = i * py5.TWO_PI / num_magnets + t
        r = 600 + 200 * np.sin(t * 2 + i)
        magnets[i, 0] = cx + r * np.cos(angle)
        magnets[i, 1] = cy + r * np.sin(angle)
        
        py5.fill((i * 360/num_magnets + t*50) % 360, 80, 80, 20)
        py5.ellipse(magnets[i, 0], magnets[i, 1], 50, 50)
        
    dt = 0.5
    friction = 0.02
    gravity = 0.05
    magnetic_force = 1000.0
    
    for _ in range(2): 
        dx = cx - positions[:, 0]
        dy = cy - positions[:, 1]
        
        fx = gravity * dx
        fy = gravity * dy
        
        for i in range(num_magnets):
            mx, my = magnets[i, 0], magnets[i, 1]
            mdx = mx - positions[:, 0]
            mdy = my - positions[:, 1]
            mdist_sq = mdx**2 + mdy**2 + 1000.0 
            
            force = magnetic_force / mdist_sq
            fx += force * mdx
            fy += force * mdy
            
        velocities[:, 0] += fx * dt
        velocities[:, 1] += fy * dt
        velocities *= (1.0 - friction * dt)
        positions[:, 0] += velocities[:, 0] * dt
        positions[:, 1] += velocities[:, 1] * dt
        
    py5.no_stroke()
    for i in range(num_pendulums):
        x, y = positions[i, 0], positions[i, 1]
        speed = np.sqrt(velocities[i, 0]**2 + velocities[i, 1]**2)
        hue = (speed * 20 + py5.frame_count * 0.5) % 360
        py5.fill(hue, 90, 90, 30)
        py5.ellipse(x, y, 3, 3)

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
