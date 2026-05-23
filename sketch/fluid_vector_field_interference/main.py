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

NUM_PARTICLES = 25000
# positions: x, y, z
pos = np.random.uniform(-800, 800, (NUM_PARTICLES, 3)).astype(np.float32)
vel = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
colors = np.random.uniform(0, 360, NUM_PARTICLES).astype(np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    # Motion blur effect using semi-transparent background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_x(t * 0.5)
    py5.rotate_y(t * 0.3)
    
    global pos, vel, colors
    
    # Calculate 3D vector field based on two interfering vortices
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    
    # Vortex 1
    dist1 = np.sqrt(x**2 + z**2) + 0.001
    vx1 = -z / dist1 * 200 / (dist1 * 0.1 + 1)
    vz1 = x / dist1 * 200 / (dist1 * 0.1 + 1)
    vy1 = np.sin(dist1 * 0.05 - t * 5) * 5
    
    # Vortex 2 (offset)
    ox, oy, oz = x - 300, y - 200, z + 300
    dist2 = np.sqrt(ox**2 + oy**2) + 0.001
    vx2 = -oy / dist2 * 300 / (dist2 * 0.1 + 1)
    vy2 = ox / dist2 * 300 / (dist2 * 0.1 + 1)
    vz2 = np.cos(dist2 * 0.05 - t * 4) * 5
    
    # Noise force (simplified by using sinusoidal interference)
    nx = np.sin(y * 0.01 + t) * 2
    ny = np.sin(z * 0.01 + t) * 2
    nz = np.sin(x * 0.01 + t) * 2
    
    # Apply forces
    vel[:, 0] += (vx1 + vx2 + nx) * 0.1
    vel[:, 1] += (vy1 + vy2 + ny) * 0.1
    vel[:, 2] += (vz1 + vz2 + nz) * 0.1
    
    # Damping / Friction
    vel *= 0.95
    
    # Update positions
    pos += vel
    
    # Wrap particles that fly too far
    out_of_bounds = (np.abs(pos[:, 0]) > 1000) | (np.abs(pos[:, 1]) > 1000) | (np.abs(pos[:, 2]) > 1000)
    pos[out_of_bounds] = np.random.uniform(-800, 800, (np.sum(out_of_bounds), 3))
    vel[out_of_bounds] = 0
    
    # Map colors
    speed = np.sqrt(vel[:, 0]**2 + vel[:, 1]**2 + vel[:, 2]**2)
    colors = (colors + speed * 0.5) % 360
    
    # Draw particles
    py5.stroke_weight(2.5)
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        py5.stroke(colors[i], 80, 100, 60)
        py5.vertex(pos[i, 0], pos[i, 1], pos[i, 2])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

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
