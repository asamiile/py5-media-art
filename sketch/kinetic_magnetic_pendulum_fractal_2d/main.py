from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)  # Random duration up to 20s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Magnets
magnets = np.array([
    [0, -250],
    [216.5, 125],
    [-216.5, 125]
], dtype=np.float32)

colors = [
    (255, 215, 0),    # Gold
    (220, 20, 60),    # Crimson
    (65, 105, 225)    # Royal Blue
]

# Multiple pendulums
n_pendulums = 2000
positions = None
velocities = None

def setup():
    global positions, velocities
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = np.zeros((n_pendulums, 2), dtype=np.float32)
    velocities = np.zeros((n_pendulums, 2), dtype=np.float32)
    
    # Initialize in a grid or random circle
    for i in range(n_pendulums):
        r = random.uniform(0, 400)
        theta = random.uniform(0, py5.TWO_PI)
        positions[i, 0] = r * math.cos(theta)
        positions[i, 1] = r * math.sin(theta)

def draw():
    global positions, velocities
    if py5.frame_count == 1:
        py5.background(11, 16, 33) # Deep navy
        
    py5.blend_mode(py5.ADD)
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    dt = 0.05
    friction = 0.02
    gravity = 0.1
    magnet_strength = 2.0
    
    py5.no_stroke()
    
    for _ in range(3): # Multiple physics steps per frame
        # Compute forces
        for i in range(n_pendulums):
            x, y = positions[i]
            vx, vy = velocities[i]
            
            # Gravity (pulls to origin)
            fx = -gravity * x
            fy = -gravity * y
            
            # Magnets
            for j in range(3):
                mx, my = magnets[j]
                dx = mx - x
                dy = my - y
                dist_sq = dx**2 + dy**2 + 100.0 # Small softening
                
                dist = math.sqrt(dist_sq)
                force = magnet_strength / (dist_sq * dist)
                fx += dx * force
                fy += dy * force
                
            # Friction
            fx -= friction * vx
            fy -= friction * vy
            
            velocities[i, 0] += fx * dt
            velocities[i, 1] += fy * dt
            
            positions[i, 0] += velocities[i, 0] * dt
            positions[i, 1] += velocities[i, 1] * dt
            
        # Draw a trail segment
        for i in range(n_pendulums):
            x, y = positions[i]
            
            # Determine closest magnet to color
            closest = 0
            min_dist = 1e9
            for j in range(3):
                mx, my = magnets[j]
                d = (mx - x)**2 + (my - y)**2
                if d < min_dist:
                    min_dist = d
                    closest = j
                    
            c = colors[closest]
            py5.fill(c[0], c[1], c[2], 15)
            py5.circle(x, y, 2.5)

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
