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

NUM_PARTICLES = 1000000

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos_x, pos_y, colors
    
    # Initialize particles uniformly across the screen
    pos_x = np.random.uniform(0, py5.width, NUM_PARTICLES)
    pos_y = np.random.uniform(0, py5.height, NUM_PARTICLES)
    
    # Assign a color to each particle based on its initial location
    # Map them to a vibrant palette
    norm_x = pos_x / py5.width
    norm_y = pos_y / py5.height
    
    r = (np.sin(norm_x * py5.PI * 2) * 0.5 + 0.5) * 255
    g = (np.sin((norm_x + norm_y) * py5.PI * 2 + 2.0) * 0.5 + 0.5) * 255
    b = (np.cos(norm_y * py5.PI * 2) * 0.5 + 0.5) * 255
    
    colors = np.column_stack((r, g, b, np.full(NUM_PARTICLES, 15))) # low alpha for trails

def velocity(x, y, t):
    # Scale coordinates down so the noise features are large
    sx = x * 0.003
    sy = y * 0.003
    
    # Analytical partial derivatives of a nested sine/cosine potential field
    # P(x, y) = sin(x + t)*cos(y - t/2) + 0.5*sin(2x - 1.2t)*cos(2y + 0.8t) + 0.25*sin(4x + 0.9t)*cos(4y - 1.1t)
    # v_x = dP/dy
    # v_y = -dP/dx
    
    dP_dy = (
        -np.sin(sx*1.0 + t) * np.sin(sy*1.0 - t*0.5) * 1.0 +
        -np.sin(sx*2.0 - t*1.2) * np.sin(sy*2.0 + t*0.8) * 1.0 +
        -np.sin(sx*4.0 + t*0.9) * np.sin(sy*4.0 - t*1.1) * 1.0
    )
    dP_dx = (
        np.cos(sx*1.0 + t) * np.cos(sy*1.0 - t*0.5) * 1.0 +
        np.cos(sx*2.0 - t*1.2) * np.cos(sy*2.0 + t*0.8) * 1.0 +
        np.cos(sx*4.0 + t*0.9) * np.cos(sy*4.0 - t*1.1) * 1.0
    )
    
    # Return velocity vector
    return dP_dy, -dP_dx

def draw():
    global pos_x, pos_y
    
    t = py5.frame_count / TOTAL_FRAMES * py5.PI * 2
    
    # Darken background slightly to leave trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Additive blend mode for glowing trails
    py5.blend_mode(py5.ADD)
    
    # Perform a few Euler steps per frame to make it fast
    STEPS = 5
    dt = 2.0
    
    for _ in range(STEPS):
        vx, vy = velocity(pos_x, pos_y, t)
        pos_x += vx * dt
        pos_y += vy * dt
        
        # Toroidal wrap around screen bounds
        pos_x = np.mod(pos_x, py5.width)
        pos_y = np.mod(pos_y, py5.height)
        
    # Draw points
    # Since we can't easily pass a custom color array to py5.points(),
    # we will split the particles into 5 color buckets to draw them efficiently
    py5.stroke_weight(1)
    
    # Very fast bucketing based on the pre-computed color array
    # We use the dominant color channel
    dom_color = np.argmax(colors[:, :3], axis=1)
    
    palette = [
        (255, 50, 50, 20),
        (50, 255, 50, 20),
        (50, 50, 255, 20)
    ]
    
    points = np.column_stack((pos_x, pos_y))
    
    for i in range(3):
        mask = (dom_color == i)
        if np.any(mask):
            py5.stroke(*palette[i])
            py5.points(points[mask])
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
