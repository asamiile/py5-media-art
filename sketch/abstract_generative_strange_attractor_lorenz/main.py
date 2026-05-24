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

NUM_PARTICLES = 15000
DT = 0.005

# Lorenz system constants
SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0

# Initialize particles in a tiny cluster to show chaotic divergence
# Start near a known unstable fixed point
start_points = np.random.normal(loc=[0.1, 0.1, 0.1], scale=0.01, size=(NUM_PARTICLES, 3)).astype(np.float32)

pos = start_points.copy()
# Store previous positions to draw lines
prev_pos = pos.copy()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    # Don't clear background entirely in draw to create a huge motion trail effect
    py5.background(5, 5, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global pos, prev_pos
    
    # Motion blur / fading
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 4)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    # Camera / Viewport
    py5.translate(py5.width / 2, py5.height / 2 + 100, -300)
    
    # The Lorenz attractor has a dominant Z-axis, usually plotted X vs Z or similar.
    # We will slowly orbit it.
    py5.rotate_y(t * 0.5)
    py5.rotate_x(py5.sin(t * 0.2) * 0.3)
    py5.rotate_z(py5.cos(t * 0.3) * 0.2)
    
    # Scale up the attractor (the coordinates are usually within -20 to 20 or so)
    SCALE = 18.0
    py5.scale(SCALE)
    # Center the attractor (Z is usually positive, averaging around 25)
    py5.translate(0, 0, -25)
    
    # Update physics using NumPy
    prev_pos[:] = pos[:]
    
    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]
    
    # Lorenz Differential Equations
    dx = SIGMA * (y - x)
    dy = x * (RHO - z) - y
    dz = x * y - BETA * z
    
    pos[:, 0] += dx * DT
    pos[:, 1] += dy * DT
    pos[:, 2] += dz * DT
    
    py5.stroke_weight(0.1 / SCALE) # Very thin lines
    
    # Render particles as lines
    # We iterate, but we can do it somewhat efficiently.
    # We color based on the velocity (divergence speed) or just the age/position.
    velocities = np.sqrt(dx**2 + dy**2 + dz**2)
    
    for i in range(NUM_PARTICLES):
        hue = (pos[i, 2] * 4 + t * 50) % 360
        vel = velocities[i]
        brightness = np.clip(vel * 2, 30, 100)
        
        py5.stroke(hue, 90, brightness, 30)
        
        # Draw a line from prev to current
        py5.line(prev_pos[i, 0], prev_pos[i, 1], prev_pos[i, 2],
                 pos[i, 0], pos[i, 1], pos[i, 2])

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
