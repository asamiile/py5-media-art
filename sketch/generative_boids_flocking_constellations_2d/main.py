from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 800
MAX_DIST = 150.0

pos = np.zeros((NUM_PARTICLES, 2))
vel = np.zeros((NUM_PARTICLES, 2))
colors = np.zeros((NUM_PARTICLES, 3))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 15, 25)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize positions and colors
    for i in range(NUM_PARTICLES):
        pos[i] = [random.uniform(0, SIZE[0]), random.uniform(0, SIZE[1])]
        
        # Ethereal blues and purples
        r = random.uniform(100, 200)
        g = random.uniform(150, 255)
        b = 255
        colors[i] = [r, g, b]

def draw():
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 15, 25, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.005
    
    # Update velocities based on a flow field (Perlin noise derivative)
    for i in range(NUM_PARTICLES):
        px, py = pos[i]
        
        # Scale coordinates for noise
        nx = px * 0.002
        ny = py * 0.002
        
        # Complex flow
        angle = py5.os_noise(nx, ny, t) * py5.TWO_PI * 4.0
        
        vx = np.cos(angle) * 3.0
        vy = np.sin(angle) * 3.0
        
        # Add a slight pull towards the center to keep them clustered
        cx = SIZE[0] / 2
        cy = SIZE[1] / 2
        vx += (cx - px) * 0.001
        vy += (cy - py) * 0.001
        
        # Smooth velocity updates
        vel[i, 0] = py5.lerp(vel[i, 0], vx, 0.1)
        vel[i, 1] = py5.lerp(vel[i, 1], vy, 0.1)
        
        # Move
        pos[i, 0] += vel[i, 0]
        pos[i, 1] += vel[i, 1]
        
        # Wrap around edges
        pos[i, 0] = pos[i, 0] % SIZE[0]
        pos[i, 1] = pos[i, 1] % SIZE[1]

    # Draw connections (Constellations)
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1.0)
    
    # Vectorized distance calculation
    # Only draw lines between close particles
    # To avoid double drawing, we only look at j > i, but a simple nested loop in numpy works
    
    # Calculate all pairwise distances squared
    dx = pos[:, 0:1] - pos[:, 0:1].T
    dy = pos[:, 1:2] - pos[:, 1:2].T
    dist2 = dx**2 + dy**2
    
    # Get indices where distance is less than MAX_DIST
    i_idx, j_idx = np.where((dist2 > 0) & (dist2 < MAX_DIST**2))
    
    # Filter to only i < j to avoid drawing twice
    mask = i_idx < j_idx
    i_idx = i_idx[mask]
    j_idx = j_idx[mask]
    
    distances = np.sqrt(dist2[i_idx, j_idx])
    
    # Drawing lines is slow if there are millions. 
    # With 800 particles and small dist, we should have a few thousand lines max.
    
    py5.begin_shape(py5.LINES)
    for k in range(len(i_idx)):
        i = i_idx[k]
        j = j_idx[k]
        d = distances[k]
        
        # Alpha based on distance
        alpha = py5.remap(d, 0, MAX_DIST, 150, 0)
        
        # Blend colors of the two connected particles
        c1 = colors[i]
        c2 = colors[j]
        
        r = (c1[0] + c2[0]) / 2
        g = (c1[1] + c2[1]) / 2
        b = (c1[2] + c2[2]) / 2
        
        py5.stroke(r, g, b, alpha)
        py5.vertex(pos[i, 0], pos[i, 1])
        py5.vertex(pos[j, 0], pos[j, 1])
    py5.end_shape()

    # Draw particles
    py5.no_stroke()
    for i in range(NUM_PARTICLES):
        py5.fill(colors[i, 0], colors[i, 1], colors[i, 2], 200)
        py5.circle(pos[i, 0], pos[i, 1], 4)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
