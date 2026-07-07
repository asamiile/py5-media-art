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

# Simulation Constants
NUM_PARTICLES = 30000
NUM_WELLS = 4
G_CONST = 1500.0
SOFTENING = 200.0

pos = np.zeros((NUM_PARTICLES, 2))
vel = np.zeros((NUM_PARTICLES, 2))
colors = np.zeros((NUM_PARTICLES, 3), dtype=np.uint8)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(5, 5, 8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles in a large ring
    angles = np.random.uniform(0, py5.TWO_PI, NUM_PARTICLES)
    radii = np.random.uniform(SIZE[1]*0.1, SIZE[1]*0.4, NUM_PARTICLES)
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    pos[:, 0] = cx + np.cos(angles) * radii
    pos[:, 1] = cy + np.sin(angles) * radii
    
    # Initial circular velocity
    vel[:, 0] = -np.sin(angles) * 3.0
    vel[:, 1] = np.cos(angles) * 3.0
    
    # Pre-calculate colors (Cosmic Gold)
    for i in range(NUM_PARTICLES):
        r = random.randint(200, 255)
        g = random.randint(150, 200)
        b = random.randint(50, 100)
        colors[i] = [r, g, b]

def draw():
    # Subtle fade for motion trail
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 8, 30)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.01
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    # Gravity wells moving in Lissajous curves
    wells_x = np.zeros(NUM_WELLS)
    wells_y = np.zeros(NUM_WELLS)
    
    for i in range(NUM_WELLS):
        # Different frequencies and phases for each well
        freq_x = 1.0 + i * 0.2
        freq_y = 1.2 + i * 0.3
        phase = i * py5.TWO_PI / NUM_WELLS
        
        radius_x = SIZE[0] * 0.3
        radius_y = SIZE[1] * 0.3
        
        wells_x[i] = cx + np.sin(t * freq_x + phase) * radius_x
        wells_y[i] = cy + np.cos(t * freq_y + phase) * radius_y
    
    # Update particles
    global pos, vel
    
    for i in range(NUM_WELLS):
        dx = wells_x[i] - pos[:, 0]
        dy = wells_y[i] - pos[:, 1]
        
        dist_sq = dx**2 + dy**2 + SOFTENING
        dist = np.sqrt(dist_sq)
        
        f = G_CONST / dist_sq
        
        vel[:, 0] += f * (dx / dist)
        vel[:, 1] += f * (dy / dist)
        
    # Optional central supermassive well
    dx = cx - pos[:, 0]
    dy = cy - pos[:, 1]
    dist_sq = dx**2 + dy**2 + SOFTENING * 10.0
    f = (G_CONST * 2.0) / dist_sq
    vel[:, 0] += f * (dx / np.sqrt(dist_sq))
    vel[:, 1] += f * (dy / np.sqrt(dist_sq))
    
    # Friction
    vel *= 0.995
    
    pos += vel
    
    # Draw particles
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.0)
    
    # Py5 doesn't easily let us draw colored point arrays in one call without Py5Shape.
    # To use colored points efficiently:
    # Divide into 5 color buckets
    
    # Since particles change position but not color, we can just draw them in chunks.
    # We will use py5.points() for performance.
    chunk_size = NUM_PARTICLES // 10
    for i in range(10):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        
        # Take the average color of the chunk (good enough since colors are similar)
        avg_r = np.mean(colors[start:end, 0])
        avg_g = np.mean(colors[start:end, 1])
        avg_b = np.mean(colors[start:end, 2])
        
        py5.stroke(avg_r, avg_g, avg_b, 100)
        py5.points(pos[start:end])

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
