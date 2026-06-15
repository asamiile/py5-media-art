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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Physics variables
num_particles = 100000
positions = None
a, b, c, d = 0.0, 0.0, 0.0, 0.0

def setup():
    global positions, a, b, c, d
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 5, 15)  # Very dark purple background
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize Clifford Attractor parameters
    a = 1.4
    b = 1.56
    c = 1.4
    d = -6.56
    
    positions = np.random.uniform(-1, 1, (num_particles, 2))

def draw():
    global positions, a, b, c, d
    
    # We do not clear the background, allowing the tapestry to weave and accumulate
    
    # Slowly morph the attractor parameters to animate the woven pattern
    t = py5.frame_count * 0.005
    a = 1.4 + 0.2 * np.sin(t)
    b = 1.56 + 0.2 * np.cos(t * 0.8)
    c = 1.4 + 0.2 * np.sin(t * 1.2)
    d = -6.56 + 0.2 * np.cos(t * 0.9)
    
    # Clifford attractor step
    x_new = np.sin(a * positions[:, 1]) + c * np.cos(a * positions[:, 0])
    y_new = np.sin(b * positions[:, 0]) + d * np.cos(b * positions[:, 1])
    
    positions[:, 0] = x_new
    positions[:, 1] = y_new
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Scale coordinates to screen
    scale = min(py5.width, py5.height) * 0.15
    
    # Calculate colors based on position
    # Map from -3..3 to 0..255 for color mapping
    r = np.clip((positions[:, 0] + 3) * 40, 0, 255)
    g = np.clip((positions[:, 1] + 3) * 30, 0, 255)
    bl = np.clip((np.abs(positions[:, 0] * positions[:, 1])) * 20, 0, 255)
    
    py5.stroke_weight(0.5)
    
    # Draw points efficiently
    py5.begin_shape(py5.POINTS)
    for i in range(min(10000, num_particles)):  # Draw a subset to keep performance and transparency
        # Dynamic color shifting over time
        rc = (r[i] + py5.frame_count) % 255
        gc = g[i]
        bc = (bl[i] + py5.frame_count * 2) % 255
        py5.stroke(rc, gc, bc, 8)  # Very transparent for weaving effect
        py5.vertex(positions[i, 0] * scale, positions[i, 1] * scale)
    py5.end_shape()
    
    py5.pop_matrix()

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
