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

NUM_PARTICLES = 15000
pts_x = np.random.uniform(0, SIZE[0], NUM_PARTICLES).astype(np.float32)
pts_y = np.random.uniform(0, SIZE[1], NUM_PARTICLES).astype(np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def get_vector_field(x, y, t):
    # A pseudo-random vector field constructed from overlapping trigonometric waves.
    # Fully vectorized via NumPy for real-time performance with massive particle counts.
    scale1 = 0.003
    scale2 = 0.007
    
    u = np.sin(y * scale1 + t) * 2.5 + np.cos(x * scale2 - t * 0.7) + np.sin((x+y) * 0.001)
    v = np.cos(x * scale1 - t) * 2.5 + np.sin(y * scale2 + t * 0.5) + np.cos((x-y) * 0.001)
    
    # Large gentle vortex in the center that reverses over time
    cx, cy = SIZE[0]/2, SIZE[1]/2
    dx = x - cx
    dy = y - cy
    dist = np.hypot(dx, dy) + 1.0
    
    vortex_strength = 2.0 * np.sin(t * 0.4)
    u += (-dy / dist) * vortex_strength
    v += (dx / dist) * vortex_strength
    
    # Normalize the vectors for uniform flow speed
    mag = np.hypot(u, v) + 0.001
    return (u / mag) * 3.0, (v / mag) * 3.0

def draw():
    global pts_x, pts_y
    
    # Motion blur via faint background clear
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    t = py5.frame_count * 0.015
    
    # Calculate new positions
    vx, vy = get_vector_field(pts_x, pts_y, t)
    
    new_x = pts_x + vx * 2.0
    new_y = pts_y + vy * 2.0
    
    # Draw lines from old to new position for smooth trails
    # Using numpy array logic, we draw them one by one. To be fast, we can use py5.lines()
    # py5 has py5.lines() which takes a massive array of coords!
    # format for py5.lines is usually a 2D numpy array of shape (N, 4) for (x1, y1, x2, y2)
    # Let's map colors globally
    
    r = 20 + 200 * np.abs(np.sin(t))
    g = 100 + 150 * np.abs(np.cos(t * 0.7))
    b_col = 200 + 55 * np.abs(np.sin(t * 1.3))
    
    py5.stroke(r, g, b_col, 80)
    
    coords = np.column_stack((pts_x, pts_y, new_x, new_y))
    py5.lines(coords)
    
    # Wrap particles around the screen boundaries
    pts_x = new_x % SIZE[0]
    pts_y = new_y % SIZE[1]
    
    # Add a small amount of random drift to keep particles from clumping permanently
    pts_x += np.random.uniform(-0.5, 0.5, NUM_PARTICLES)
    pts_y += np.random.uniform(-0.5, 0.5, NUM_PARTICLES)

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
